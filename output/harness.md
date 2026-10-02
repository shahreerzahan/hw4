# Campus Customs – Harness

## Database

File: `data/campus_customs.db` (SQLite). Four tables: `catalogue` (102 products), `inventory` (612 rows = 102 products × 6 sizes), `users` (3 seed users), `chat_messages` (22 seed messages).

### `catalogue` – one row per product

| Field | Type | Why it matters |
|---|---|---|
| `product_id` | TEXT, primary key | URL-friendly slug (e.g. `baseball-left-chest-crewneck`) used for product detail page routes and for joining to `inventory`. |
| `name` | TEXT | Display title on product cards and the detail page; what the chatbot calls the item. |
| `garment_type` | TEXT | Category (hoodie, crewneck, T-shirt…) for filtering and for the chatbot to answer "show me hoodies". Values aren't standardized (e.g. `t-shirt` vs `short-sleeve T-shirt`), so matching should be loose. |
| `description` | TEXT | Product copy on the detail page; gives the chatbot detail to describe and compare items. |
| `colors` | TEXT (JSON array) | List of colors like `["navy", "white"]`; must be parsed with JSON. Lets shoppers and the chatbot search by color. |
| `search_tags` | TEXT (JSON array) | Keywords (sport, school, residential college, style); the main hook for chatbot product search. |
| `image_file_path` | TEXT | Relative to `data/` (e.g. `products/x.jpg`); the backend serves these images for cards and the detail page. All 102 files exist. |
| `price` | REAL | Price in dollars; shown on cards and used for "under $50"-type questions. |

### `inventory` – stock per product and size

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key | Internal row ID; not shown to shoppers. |
| `product_id` | TEXT, FK → `catalogue` | Links a stock row to its product. |
| `size` | TEXT | One of XS, S, M, L, XL, XXL; drives the size picker and "do you have this in L?" answers. `(product_id, size)` is unique. |
| `quantity` | INTEGER | Units in stock (0–25); 145 rows are 0, so the site and chatbot must show "sold out" for those sizes. |

### `users` – shopper accounts

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key | Identifies the logged-in shopper; `chat_messages.user_id` points here. |
| `name` | TEXT, required | Full name (older field). Fill it in as "first last" when creating an account, because it is NOT NULL. |
| `email` | TEXT, unique | Login username; uniqueness blocks duplicate accounts. |
| `password_hash` | TEXT | Salted password hash, never plaintext. Format: `pbkdf2_sha256$<salt>$<hex digest>`. |
| `created_at` | TEXT, default now | When the account was created; useful for auditing. |
| `first_name` | TEXT | Used to greet the shopper and personalize the chatbot. |
| `last_name` | TEXT | Collected at sign-up; completes the customer profile. |

**Password hashing:** PBKDF2-HMAC-SHA256, **120,000 iterations**, salt = the salt string from the hash encoded as UTF-8 bytes, digest = 32 bytes in hex. Check a login with `hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()` and compare to the stored digest using `hmac.compare_digest`. Confirmed with the seed test user `test@campuscustoms.yale.edu`.

### `chat_messages` – chatbot conversation history

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key | Keeps messages in order. |
| `user_id` | INTEGER, FK → `users` | Gives each shopper their own chat history. |
| `role` | TEXT | `user` or `assistant`; needed to replay the conversation to the agent and render the chat bubbles. |
| `content` | TEXT | The message text (assistant replies use Markdown). |
| `products_json` | TEXT (JSON, nullable) | Products the assistant recommended in that reply (full catalogue fields), so product cards can be redrawn when history reloads. |
| `created_at` | TEXT, default now | Timestamp for ordering and showing history. |

## Authentication

Code: `backend/auth.py` (routes under `/api/auth`), `frontend/src/pages/Login.tsx`, `frontend/src/pages/CreateAccount.tsx`, `frontend/src/components/AuthProvider.tsx`.

### Create account and log in flow

1. **Create account** asks for first name, last name, email, password, and confirm password. The browser checks that the names aren't empty, the password is at least 8 characters, and the two passwords match. The backend checks all of this again, because the browser can't be trusted.
2. `POST /api/auth/register` lowercases the email, rejects it if an account already exists (checked case-insensitively), hashes the password, and inserts a row into `users`. The new user is logged in right away.
3. **Log in** asks for email and password. `POST /api/auth/login` looks up the email and checks the password against the stored hash. A wrong email and a wrong password both return the same message, "Incorrect email or password.", so nobody can test which emails have accounts. A wrong email also runs a full dummy hash check, so it takes as long as a wrong password.
4. On success the backend sets a **session cookie** (`cc_session`). `GET /api/auth/me` tells the front end who is logged in (the nav shows "Hi, {first name}" and a Log out button), and `POST /api/auth/logout` clears the cookie.

### What we save for each user (`users` table)

| Field | What we store |
|---|---|
| `first_name`, `last_name` | As typed (trimmed). |
| `name` | `"first last"`, because this older column is required. |
| `email` | Lowercased, unique; this is the login name. |
| `password_hash` | A salted PBKDF2 hash. **The password itself is never stored or logged.** |
| `created_at` | Filled in automatically by the database. |

The API only ever sends `id`, `first_name`, `last_name`, and `email` back to the browser. The hash never leaves the server.

### How passwords are protected

- **Hashing, not encryption:** we store a one-way PBKDF2-HMAC-SHA256 hash, so the password can't be turned back into text, even by us.
- **A unique random salt per user** (`secrets.token_hex(16)`), so two people with the same password get different hashes and precomputed "rainbow tables" don't work.
- **Slow on purpose:** new accounts use **600,000 iterations** (the current OWASP recommendation for PBKDF2-SHA256), so each guess costs an attacker real time.
- **Compatible with the seed data:** the seed users' hashes look like `pbkdf2_sha256$<salt>$<hex>` and use 120,000 iterations. New hashes record their iteration count, `pbkdf2_sha256$600000$<salt>$<hex>`, so `verify_password` handles both formats. The test user `test@campuscustoms.yale.edu` / `password` logs in unchanged.
- **Constant-time comparison** (`hmac.compare_digest`), so response timing doesn't leak how much of a hash matched.

### How the login session is protected

- The `cc_session` cookie holds `user_id.expiry`, signed with HMAC-SHA256 using `SESSION_SECRET` from `.env`. Changing the user id or the expiry breaks the signature, so the cookie can't be forged.
- It is **HttpOnly**, so page JavaScript (or an injected script) can't read it, and **SameSite=Lax**, which blocks most cross-site request forgery. It expires after 7 days.
- If `SESSION_SECRET` isn't set, the server picks a random one at startup. Logins still work but end when the server restarts.

### Tested

- The test user logs in, a wrong password is rejected, and an unknown email gets the same error.
- A new account is created and saved with a `pbkdf2_sha256$600000$…` hash (no plaintext). It can log out and log back in, and stays logged in after a page reload.
- Duplicate emails (even in different capitalization), short passwords, invalid emails, blank names, and mismatched confirm passwords are all rejected with friendly messages.
- A forged cookie is ignored, and logging out ends the session.
