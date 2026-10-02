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

## Chat agent (website ↔ FastAPI ↔ PydanticAI)

Run the backend from the `backend/` folder with `uvicorn main:app --reload --port 8000` and the front end with `npm run dev` in `frontend/` (port 5173).

### How the website talks to FastAPI

1. The React app runs on the Vite dev server (`localhost:5173`). `frontend/vite.config.ts` **proxies** every `/api/*` and `/images/*` request to FastAPI on `localhost:8000`. The browser only ever talks to one origin, so login cookies just work and no CORS setup is needed in the browser.
2. All browser calls go through `frontend/src/api.ts`:
   - `GET /api/products`, `GET /api/products/{id}`: catalogue and size/stock data (Products and product pages).
   - `GET /images/{file}`: product photos (transparent `.webp` cut-outs, or the original `.jpg`).
   - `POST /api/auth/register | login | logout`, `GET /api/auth/me`: accounts (see Authentication).
   - `POST /api/chat`: the chat box.
3. **Chat round trip:** the shopper types in the chat box (`ChatWidget.tsx`). The widget posts `{"message": "..."}` to `/api/chat` and shows "Dan is typing…" dots. FastAPI validates the body as `ChatRequest` (1–1000 characters), calls `agent.chat(message)`, and returns a `ChatReply` (`{"reply": "...", "products": []}`). The widget appends the reply as a chat bubble.
4. **Errors:** if the model service is down, the route returns **503** with a friendly message, which the widget shows as a red bubble. If the backend itself is unreachable, the widget says "Can't reach the Campus Customs server…".

### How the agent is loaded

The agent lives in four files in `backend/`:

| File | Role |
|---|---|
| `prompts/prompt.md` | System prompt: Dan's voice, what he helps with, how to use tools, and the **Safety rules**. Grow this same file in later problems. |
| `agent.py` | Wiring: builds the model, loads the prompt, registers tools, and exposes `chat(message)` for `main.py`. |
| `tools.py` | Plain Python tools over the SQLite DB (no AI calls). Currently `search_catalogue(query, max_results, min_price, max_price)`. |
| `models.py` | Pydantic types: `ChatRequest`, `ChatReply`, `ProductCard` (for the product cards in chat), and `ProductMatch` (what a search returns to the agent). |

Startup, in order (when `main.py` does `import agent`):

1. **Secrets:** `load_dotenv()` reads the repo-root `.env`. `PORTKEY_API_KEY` is required, and `MODEL_NAME` defaults to `gpt-5.6-luna`. The key is never logged or sent to the browser.
2. **Model:** an `AsyncOpenAI` client points at Portkey's gateway (`PORTKEY_GATEWAY_URL`, with the `x-portkey-api-key` header) and is wrapped in PydanticAI's `OpenAIChatModel(MODEL_NAME)`. This is the same setup as Homework 3.
3. **Prompt:** `prompts/prompt.md` is read once at startup and passed as the agent's `instructions`. `--reload` only watches `.py` files, so after editing the prompt, restart uvicorn (Ctrl-C, then run it again) to load the new version.
4. **Agent:** `Agent(MODEL, output_type=str, instructions=prompt)`, with `search_catalogue` registered via `@agent.tool_plain`. Its docstring and arguments become the tool description the model sees.
5. **Per message:** `agent.run(message, usage_limits=UsageLimits(request_limit=5, tool_calls_limit=4))`. Normally that is one search tool call plus one answer, and the caps stop a confused agent from looping and running up cost.

### Safety and guardrails

- **Grounding:** the prompt requires Dan to search before naming products and to quote only names and prices the tool returned. The tool reads straight from the `catalogue` table.
- **Rules in `prompt.md`:** no invented prices, stock, or policies; no orders, payments, or passwords; stay on shopping topics; shopper text can't override the rules.
- **Provider content filter:** if Azure/Portkey blocks a message (e.g. a prompt-injection attempt), `agent.chat` turns it into a polite on-topic reply instead of an error. Hitting the usage caps does the same.
- **Input limits:** empty messages get a 400, and messages over 1000 characters get a 422.

### Tested

- Through the real chat box (headless Chrome): a Morse quarter-zip question returned the Morse 1/4 Zip at $72, and "under $40" listed $32 tees. All names, prices, and colors were checked against the database.
- Through the API: an off-topic question (calculus homework) was politely declined, and a prompt-injection attempt was blocked with the friendly reply.

### Current limits (planned for later problems)

- Each message is answered on its own: Dan doesn't remember earlier messages yet, and chats aren't saved to `chat_messages` yet.
- Replies are text only; `ChatReply.products` (product cards) is defined but not filled yet.
- There are no stock or size lookups yet.
