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

### `chat_history`: saved chats for logged-in shoppers (added by this app)

Created at backend startup by `db.init_db()` (`CREATE TABLE IF NOT EXISTS`), so a fresh copy of the course database gets it automatically. The seed `chat_messages` table is left untouched.

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key | Keeps messages in order. |
| `user_id` | INTEGER, FK → `users` | Whose chat this is; history is only ever loaded for the logged-in user. |
| `role` | TEXT (`user` / `assistant`) | Who said it; needed to rebuild the conversation for the agent and the chat bubbles. |
| `content` | TEXT | The message text. |
| `product_ids` | TEXT (JSON list) | Products Dan showed as cards with that reply, so the cards can be re-shown later and follow-ups ("the second one") make sense. |
| `results_title` | TEXT | Heading for those cards. |
| `page_path` | TEXT | Page the message was sent from, so "this" in old messages still points to the right product. |
| `created_at` | TEXT, default now | When it was said. |

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

## Agent tools: product info, price, and stock

Every tool is a plain Python function in `backend/tools.py` that reads `data/campus_customs.db` **live on every call** (no caching), registered in `backend/agent.py` with `@agent.tool_plain`. Return types are Pydantic models in `backend/models.py`, so the model gets clean, labeled JSON instead of raw rows. `prompts/prompt.md` ("Price, stock, and product details") tells Dan to call `get_price` and `check_stock` for every price or stock question and to quote the numbers exactly.

| Tool | Reads | Returns |
|---|---|---|
| `search_catalogue(query, max_results, min_price, max_price)` | `catalogue` | `list[ProductMatch]` |
| `get_product_info(product)` | `catalogue` | `ProductInfo` or `ProductNotFound` |
| `get_price(product)` | `catalogue.price` | `PriceInfo` or `ProductNotFound` |
| `check_stock(product, size=None)` | `inventory` (+ `catalogue` for the name) | `StockInfo` or `ProductNotFound` |

### Finding the product (`find_product`, shared by the three lookups)

The shopper rarely types an exact name, so `product` accepts a `product_id`, an exact name, or a partial name. Matching tries the exact `product_id`, then the exact name (case-insensitive), then the name sharing the most words with the query. Spellings are normalized first: "t-shirt"/"tee" and "quarter zip"/"1/4 zip" match the catalogue's "T Shirt" and "1 4 Zip".

If several products tie (e.g. "dad" matches the Dad Crewneck, Hoodie, and T Shirt), it returns `ProductNotFound` with those names as `suggestions` instead of guessing, and Dan asks which one. The same happens when nothing matches.

### Fields chosen, and why

**`ProductMatch`** (search results): `product_id`, `name`, `garment_type`, `price`, `colors`, `description`
- Enough for Dan to recommend and compare products in one step. `product_id` lets him pass the exact product to the next lookup.
- Left out: `image_file_path` (the model can't use it, and paths stay internal) and `search_tags` (used only for ranking, and noisy to show).

**`ProductInfo`** (`get_product_info`): `product_id`, `name`, `garment_type`, `description`, `colors`
- The full description and colors answer "tell me about…" and "what color is…".
- Price and stock are left out on purpose, so they only ever come from the dedicated tools that the prompt requires for those questions.

**`PriceInfo`** (`get_price`): `product_id`, `name`, `price`, `currency="USD"`
- Kept minimal so the answer is unambiguous. `name` confirms which product was matched (so Dan doesn't quote a price for the wrong item), and `currency` keeps Dan from guessing the units.

**`StockInfo`** (`check_stock`): the per-size data plus pre-computed summaries.
- `sizes`: a list of `SizeStock(size, quantity, in_stock)` in XS→XXL order, so Dan can give exact quantities per size.
- `available_sizes` / `sold_out_sizes`: computed in Python so the model doesn't have to filter numbers, which lowers the chance of a mistake like calling a 0 "in stock".
- `total_in_stock`: answers "do you have any?" and spots "sold out in every size".
- `requested_size`: the shopper's size normalized ("medium" → `M`, "2XL" → `XXL`).
- `requested_size_quantity` and `requested_size_note`: a plain-language answer such as "Size L is SOLD OUT (0 left). In stock: XS, S, M, XL, XXL." This makes the sold-out case impossible to miss, and it also covers sizes the product doesn't come in (e.g. "4XL").

**`ProductNotFound`**: `found=false`, `query`, `message`, `suggestions`
- An explicit "not found / ambiguous" result instead of an error, so Dan can ask a follow-up instead of inventing an answer.

### Tested (answers checked against the database)

| Shopper asked | Tool(s) called | Dan said | DB |
|---|---|---|---|
| Price of the Baseball Left Chest Crewneck | `get_price` | $58.00 | 58.0 ✓ |
| Baseball Left Chest Crewneck in XL? | `check_stock(size=XL)` | Sold out in XL; S, M, L, XXL available | XL=0 ✓ |
| How many medium Baseball Crewnecks? | `check_stock(size=M)` | 5 left | M=5 ✓ |
| Morse quarter zip in large? | `check_stock(size=L)` | Sold out in L; XS, S, M, XL, XXL available | L=0 ✓ |
| Yale Dad Hoodie, all sizes | `check_stock` | XS 5, S 5, M 12, L 20, XL 12, XXL 15 (69 total) | ✓ |
| Yale Mom Hoodie in XS? | `search_catalogue` → `check_stock(size=XS)` | 25 left | XS=25 ✓ |
| Basic Hoodie Big Yale in 4XL? | `check_stock(size=4XL)` | Not offered in 4XL; comes in XS–XXL | ✓ |
| "The jacket" in medium? | `search_catalogue` | Asked which jacket, listing options | (ambiguous) ✓ |

In the website's chat box (on the Morse 1/4 Zip page): "How much is the Morse 1 4 Zip?" got "$72.00", and "in large? What about medium?" got "Large is sold out… Medium is available, with 8 left". Both match the size tiles on the same page.

## Chat search that updates the page (product cards)

When a shopper asks something like "what hoodies do you have?", Dan searches the catalogue and the matching products appear as clickable cards (photo, name, price, short description) at the top of whatever page the shopper is on. The cards use the same `ProductCard` component as the Products page, so clicking one opens the normal single-product page from Problem 3.

### How the results get from the agent to the page

```
Shopper types in ChatWidget
  → POST /api/chat {"message": "what hoodies do you have?"}
  → agent.chat() → agent.run(...)
       1. Dan calls search_catalogue("hoodie", max_results=30)
          → SearchResults {total_matches: 27, showing: 27, products: [ProductMatch…]}
       2. Dan's final answer is a structured AgentReply (not free text):
          {reply: "We've got 27 hoodies! I've put them on the page…",
           product_ids: ["ua-gameday-double-knit-hood", …], results_title: "Hoodies"}
  → tools.product_cards(product_ids): looks each id up in the catalogue table
       → ProductCard {product_id, name, garment_type, price, colors, description, image_url}
  → ChatReply {reply, results_title, products: [ProductCard…]}  (JSON response)
  → ChatWidget: shows the reply bubble with a "See all 27 on the page ↑" chip and calls
    showResults(title, query, products, current page)
  → ChatResultsPanel (rendered above every page in App.tsx) shows the cards
  → Clicking a card → /products/{product_id} → the normal ProductPage
```

### Key design choices

- **Structured output instead of parsing text.** The agent's `output_type` is `AgentReply` (`backend/models.py`), so PydanticAI makes the model return valid JSON with `reply`, `product_ids`, and `results_title`. The front end never has to guess product names from a sentence.
- **The model picks the ids; the backend builds the cards.** `product_cards()` rebuilds every card from the `catalogue` table, so names, prices, images, and descriptions on the page are always real data. Unknown or mistyped ids are dropped, and duplicates are removed.
- **Search can return a whole category.** `search_catalogue` returns up to 30 products, which covers every product of one type (e.g. all 27 hoodies), plus `total_matches`, so Dan knows when there are more than he was shown. "hood" / "hooded" / "hoodies" are normalized so all five hoodie `garment_type`s match.
- **Short chat text, details on the cards.** The prompt tells Dan not to list every product in the reply when cards are shown, just say how many and point to them.
- **Shared page state.** `ChatResultsProvider` (React context) holds the latest results, so the chat widget and the page panel can be in different parts of the app. Each new answer with cards replaces the previous set and scrolls into view. "Clear results" removes them.
- **Clicking a card doesn't bury the product page.** After moving to another page, the results fold into a slim "Dan's results: Hoodies · 27 items · Show" bar, and each new page opens scrolled to the top.

### What `prompt.md` tells Dan (section "Showing products on the page")

| Shopper asks | `product_ids` | `results_title` |
|---|---|---|
| A whole type ("what hoodies do you have?") | All relevant matches (search with `max_results=30`) | e.g. "Hoodies" |
| A recommendation or gift | The 3–6 products recommended, in order | e.g. "Gifts for Mom under $70" |
| One product's price, stock, or details | Just that product | The product name |
| Greeting, off-topic, account help | Empty | null |

Dan may only use ids returned by his tools in that turn.

### Tested

- **API:** "what hoodies do you have?" → 27 cards titled "Hoodies", every one a hoodie type. "How much is the Morse 1 4 Zip?" → 1 card. "hi dan!" → 0 cards. "gift ideas for my mom under $70?" → 2 cards (Yale Mom Crewneck $58, Yale Mom Hoodie $68).
- **In the website's chat box (headless Chrome, Home page):** asking "what hoodies do you have?" showed the panel "Dan found 27 items · Hoodies" with 27 cards. All 27 images loaded, and the reply bubble had a "See all 27 on the page" chip. Clicking the first card opened `/products/ua-gameday-double-knit-hood` at the top of the page, with the results folded into the bar. "Show" brought all 27 back.

## Customer memory: chat history, customer info, and page context

### How chat history is saved

| | Logged-in shopper | Guest |
|---|---|---|
| Who is it? | Session cookie → `users` row | No cookie |
| Saved? | Yes, in the `chat_history` table (see Database) | **No.** Nothing is written to the database |
| Memory for Dan | Last 20 messages, loaded from `chat_history` on every request | Last 10 messages, sent back by the chat box with each request (lost when the page is closed) |
| Back next visit? | Yes: `GET /api/chat/history` reloads the conversation into the chat box | No |

- **Saving:** after each reply, `POST /api/chat` stores two rows in `chat_history` (`chat_history.save_turn`): the shopper's message, and Dan's reply with the card `product_ids`, `results_title`, and the `page_path`. Messages blocked by the provider's content filter aren't saved, so a blocked message can't keep breaking every later reply in the conversation.
- **Loading for the agent:** `chat_history.recent_for_agent(user_id)` becomes PydanticAI `message_history` (`agent.to_model_messages`), as user/assistant messages, oldest first. Assistant turns carry a note of which cards were shown, and user turns carry a note of the product page they came from.
- **Loading for the chat box:** when a shopper logs in, `ChatWidget` calls `GET /api/chat/history` and shows the old messages. Card buttons ("See all 2 on the page") still work: the cards are rebuilt from the catalogue, so prices and photos are current.
- **Switching accounts:** `App.tsx` remounts the chat widget with `key={user id or "guest"}`, so logging out instantly clears the chat on screen, and one account never sees another's messages. Logging out also clears any of Dan's cards on the page.
- **Privacy controls:** the chat header shows "Chatting as {name} · history saved" or "Guest · log in to save your chat". Logged-in shoppers can press **Clear** (`DELETE /api/chat/history`).

### What customer info the agent sees (agent deps)

`agent.py` defines the deps passed into every run:

```python
@dataclass
class ChatDeps:
    customer: CustomerInfo | None   # None for guests
    page: PageInfo
```

- `CustomerInfo` (`models.py`) has `user_id`, `first_name`, `last_name`, and `email`. `main.py` builds it from the session cookie (`current_customer()` → `users` table), never from anything typed in the chat, so a shopper can't pretend to be someone else.
- An `@agent.instructions` function (`shopper_context`) turns the deps into a short **Current shopper context** section added to the system prompt on each request, e.g. "The shopper is logged in as Test User (test@campuscustoms.yale.edu)", or "The shopper is a guest… You don't know their name or email."
- The model never sees `user_id`, the password hash, or any other user. `prompt.md` says to use the first name naturally, mention the email only if asked which account they're on, and never guess anything about other customers.

### How the page info is passed

1. With every message, the chat box sends `page_path` (the current URL, e.g. `/products/morse-logo-t-shirt`).
2. `tools.describe_page()` turns it into `PageInfo` (`page_type`, `product_id`, `product_name`). For `/products/<id>` it **looks the id up in the catalogue**, so only real products get through; unknown ids become `page_type="other"`.
3. `PageInfo` goes into `ChatDeps.page`. The shopper-context instructions say which page they're on, and that "this" or "it" means this product even if earlier messages talked about other products.
4. The server also prefixes the message itself with `[Sent from the product page: Morse Logo T Shirt (product_id: morse-logo-t-shirt)]`. The same note is rebuilt for old messages from their saved `page_path`. This was needed: in testing, with only the system-prompt context, Dan answered "this" about a hoodie from earlier in the conversation instead of the shirt on screen. With the per-message note, he picks the right product.
5. **Colors:** each product is one colorway (`colors` lists every color in the design, and stock is by size only). So for "this in pink / another color", the prompt has Dan say which colorway it is, be clear it isn't sold in other colors, and search for similar items in the color the shopper wants.

### Tested (in the website, headless Chrome, as the test user)

1. **Log in** → nav shows "Hi, Test". Chat header: "Chatting as Test · history saved". Greeting: "Woof, hi Test!".
2. **Chat:** "I need a gift for my grandpa" → 2 cards (Grandpa Crewneck and Hoodie). "How much is the hoodie one?" → "The Yale Grandpa Hoodie is $68.00" (resolved from memory).
3. **Log out** → chat resets to the guest greeting ("Guest · log in to save your chat"). `GET /api/chat/history` returns `[]`.
4. **Log back in** → all 4 messages are restored in the chat box, with their card buttons. Asked "remind me which hoodie you suggested earlier?", Dan answered correctly from the saved history.
5. **Product page** `/products/morse-logo-t-shirt`, "Do you have this in another color?" → "The Morse Logo T Shirt is sold as a heather gray design; the other listed colors (white, black, and red) are part of the printed crest…". It answered about the right product even after the earlier hoodie conversation. On the Yale Dad T Shirt page, "do you have this in pink?" → not sold in pink, and Dan suggested the dusty coral Big Yale Tri Blend T Shirt as a card.
6. **Guest:** "Show me crewnecks for Davenport" then "How much is it?" → "$58.00" (memory within the visit). The database had **0** rows for the guest; only the test user's 6 rows (3 turns) were saved.
