# Usability improvements (Problem 9)

Two front-end and two agent/backend improvements. All four were tested in the running site (headless Chrome against the Vite + FastAPI dev servers), and the numbers below come from those runs and the database.

---

## Front end 1: Search bar and category filter on the Products page

**What I added** (`frontend/src/pages/Products.tsx`)
- A search box that matches product names, descriptions, colors, garment types, and search tags. It understands spelling variants: "tee" / "t-shirt", "hoodies" / "hooded", "quarter zip" / "1/4 zip".
- Category buttons: **All · Hoodies · Crewnecks · T-Shirts · Quarter-Zips · Jackets · Long Sleeves**. Each shows how many items it has for the current search, and empty categories are greyed out.
- A live count ("25 items in Hoodies matching 'navy'"), a **Clear filters** link, and a friendly empty state ("No matches yet… ask Dan").
- The search and category are kept in the URL (`/products?category=Hoodies&q=navy`), so filtered views can be bookmarked and shared, and Dan can link straight to them.
- Each product's category comes from the backend (`tools.category_for`), which maps the catalogue's 22 different `garment_type` spellings to 6 categories. The page and the chatbot use the same groups.

**Why it helps**
- **Shoppers:** with 102 products on one page, finding "a navy hoodie" meant scrolling through everything. Now it takes two clicks (Hoodies + "navy" → 25 items), and a search like "golf" goes straight to the 2 golf items.
- **Business:** shoppers who find what they want quickly are less likely to give up and leave. Shareable links ("our Davenport gear") also work for emails and social posts.

**Tested:** all 102 items shown by default. "golf" → 2. Hoodies → 27 (`?category=Hoodies`). Hoodies + "navy" → 25. "zzzz" → empty state.

---

## Front end 2: Quick question buttons in the chat

**What I added** (`frontend/src/components/ChatWidget.tsx`)
- A row of one-tap questions above the chat input. They send immediately, no typing needed.
- **Context-aware:** on most pages: *What hoodies do you have? · What's in stock? · Gift ideas under $60 · Show me crewnecks · Anything for my residential college?* On a product page they're about that product: *Is this in stock in M? · What sizes are left? · Tell me more about this · Show me similar items*. These work because Dan already knows which page the shopper is on (Problem 8).

**Why it helps**
- **Shoppers:** many people don't know what to ask a chatbot, or don't want to type on a phone. The buttons show what Dan can do and get an answer in one tap.
- **Business:** more shoppers use the assistant, and the product-page questions (stock, sizes, similar items) are exactly the ones asked right before buying.

**Tested:** clicking "What hoodies do you have?" sent the question and showed 6 hoodie cards. On `/products/morse-1-4-zip` the buttons switched to the product questions.

---

## Agent/backend 1: Sold-out sizes suggest other sizes and similar in-stock items

**What I added**
- `check_stock` (`backend/tools.py`) now returns two extra fields when the requested size is sold out (or the whole product is):
  - `nearest_in_stock_sizes`: in-stock sizes ordered by closeness to the one asked for (L → M, XL, S, …).
  - `similar_in_stock`: up to 3 products in the same category that have that size in stock right now (read live from `inventory`), ranked by how similar they are (shared name and tag words, then closest price).
- `search_catalogue` gained live stock filters, `in_stock_only` and `in_stock_size`, plus a `category` filter, so Dan can answer "what's in stock?" or "anything in a medium?" accurately.
- `prompt.md`: Dan must never stop at "sorry, it's sold out". He says it's sold out in that size, offers the nearest sizes with quantities, and shows the similar in-stock items as cards titled "In stock in your size".

**Why it helps**
- **Shoppers:** a dead end becomes a next step. You find out right away what you *can* buy in your size.
- **Business:** a sold-out size is a likely lost sale. Pointing to a similar item that's in stock keeps that sale in the shop.

**Tested** (Morse 1/4 Zip page, "Is this in stock in large?"): Dan said "Large is sold out… M is available with 8 left and XL with 25 left; I also found three similar quarter-zips available in L". Cards shown: Morse 1/4 Zip, Berkeley 1/4 Zip, Trumbull 1/4 Zip, and Branford 1/4 Zip. Database: Morse L=0, M=8, XL=25; Berkeley L=5, Trumbull L=15, Branford L=15 ✓.

---

## Agent/backend 2: Max 6 product cards, plus a cached catalogue (faster and cheaper)

**What I added**
- **Card limit:** a reply shows at most **6 cards** (`MAX_CARDS` in `models.py`). This is enforced in `tools.product_cards`, so it holds even if the model lists more. When the shopper browses a whole category, Dan sets `see_all_category`, and the page adds a **"See all 27 Hoodies →"** button that opens the filtered Products page from Front end 1.
- **Smaller tool results:** search returns at most 12 products (was 30), with a short description (about 110 characters) instead of the full text. `get_product_info` still gives the full description when it's needed.
- **Cached catalogue:** product names, prices, descriptions, and pre-computed search words are loaded into memory once and reused for 5 minutes (`tools.catalogue()`, `clear_catalogue_cache()` to refresh now). Stock is **not** cached. `inventory` is still read live on every stock check, so quantities are never stale.

**Why it helps**
- **Shoppers:** faster answers, and 6 well-chosen picks are easier to compare than a wall of 27 cards. The "See all" button is still there for anyone who wants everything.
- **Business:** fewer tokens per chat means a lower model bill, and the database does far less work per message.

**Measured** ("what hoodies do you have?", same model):

| | Before | After |
|---|---|---|
| Cards on the page | 27 | 6 + "See all 27" link |
| Output tokens | 376 | 147 (−61%) |
| Input tokens | 7,196 | 6,365 (−12%) |
| Reply time | 6.9 s | 5.4 s |
| `search_catalogue("hoodie")` | 4.35 ms | 0.05 ms (~90× faster) |
| `find_product("morse quarter zip")` | 0.92 ms | 0.02 ms (~45× faster) |

Most input tokens are now the system prompt itself. Trimming `prompt.md` would be the next saving.
