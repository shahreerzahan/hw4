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
