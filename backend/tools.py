"""Tools the Campus Customs agent can call. Plain functions over the database (no AI calls here);
agent.py registers them with the agent."""
import json
import re

import sqlite3

from db import get_db
from models import PriceInfo, ProductInfo, ProductMatch, ProductNotFound, SizeStock, StockInfo

MAX_RESULTS = 8
_STOPWORDS = {
    "a", "an", "and", "the", "of", "on", "with", "in", "for", "to", "me", "my", "i", "do", "you",
    "have", "any", "some", "show", "find", "want", "looking", "something", "please", "yale",
}


def _words(text: str) -> set[str]:
    """Whole words, lowercased, with a simple plural -> singular ("hoodies" -> "hoodie").
    "t-shirt" / "tee" / "tshirt" all become "tshirt", and "quarter-zip" / "1/4 zip" become
    "quarterzip", so the different spellings match each other."""
    text = re.sub(r"\bt[\s-]?shirts?\b|\btees?\b", "tshirt", text.lower())
    text = re.sub(r"\b(?:quarter|1\s*/?\s*4)[\s-]*zips?\b", "quarterzip", text)
    words = set()
    for w in re.findall(r"[a-z0-9]+", text):
        if w in _STOPWORDS:
            continue
        words.add(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w)
    return words


def search_catalogue(
    query: str = "",
    max_results: int = MAX_RESULTS,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[ProductMatch]:
    """Rank catalogue products by how many query words appear in their name, type, colors,
    tags, and description (name and tag matches count more), optionally within a price range.
    An empty query with a price range lists the products in that range, cheapest first."""
    words = _words(query)
    sql, params = "SELECT * FROM catalogue WHERE 1=1", []
    if min_price is not None:
        sql, params = sql + " AND price >= ?", params + [min_price]
    if max_price is not None:
        sql, params = sql + " AND price <= ?", params + [max_price]
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()

    scored = []
    for row in rows:
        colors, tags = json.loads(row["colors"]), json.loads(row["search_tags"])
        strong = _words(" ".join([row["name"], row["garment_type"], *tags]))
        weak = _words(" ".join([row["description"], *colors]))
        score = sum(3 * (w in strong) + (w in weak) for w in words)
        if score or not words:
            scored.append((score, row, colors))

    scored.sort(key=lambda s: (-s[0], s[1]["price"], s[1]["name"]))
    return [
        ProductMatch(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=row["garment_type"],
            price=row["price"],
            colors=colors,
            description=row["description"],
        )
        for _, row, colors in scored[: max(1, min(max_results, MAX_RESULTS))]
    ]


# ---------- Lookups for one product: info, price, stock ----------

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
_SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "sm": "S", "small": "S",
    "m": "M", "med": "M", "medium": "M",
    "l": "L", "lg": "L", "large": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL",
    "extra extra large": "XXL", "double xl": "XXL",
}


def normalize_size(size: str) -> str | None:
    """'medium' -> 'M', '2XL' -> 'XXL'. None if it isn't a size we recognize."""
    key = re.sub(r"\s+", " ", size.strip().lower())
    return _SIZE_ALIASES.get(key) or (key.upper() if key.upper() in SIZE_ORDER else None)


def find_product(query: str) -> sqlite3.Row | ProductNotFound:
    """Match a product id or (partial) product name to exactly one catalogue row.

    Tries: exact product_id, exact name, then the name containing the most query words.
    If two or more products tie, returns ProductNotFound with them as suggestions so the
    agent can ask which one the shopper means instead of guessing."""
    text = query.strip()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ? OR lower(name) = lower(?)", (text.lower(), text)
        ).fetchone()
        if row:
            return row
        rows = conn.execute("SELECT * FROM catalogue").fetchall()

    words = _words(text)
    if not words:
        return ProductNotFound(query=query, message="Please give a product name to look up.")

    scored = []
    for r in rows:
        name_words = _words(r["name"] + " " + r["product_id"].replace("-", " "))
        hits = len(words & name_words)
        if hits:
            # More query words matched is better; fewer unmatched name words breaks ties.
            scored.append((hits, -len(name_words - words), r))
    scored.sort(key=lambda s: (-s[0], -s[1], s[2]["name"]))

    if not scored or scored[0][0] < max(1, (len(words) + 1) // 2):
        close = [s[2]["name"] for s in scored[:3]]
        return ProductNotFound(
            query=query, message="No product with that name is in the Campus Customs catalogue.", suggestions=close
        )
    best = [s for s in scored if s[:2] == scored[0][:2]]
    if len(best) > 1:
        return ProductNotFound(
            query=query,
            message="Several products match that name. Ask the shopper which one they mean.",
            suggestions=[s[2]["name"] for s in best[:6]],
        )
    return scored[0][2]


def get_product_info(product: str) -> ProductInfo | ProductNotFound:
    row = find_product(product)
    if isinstance(row, ProductNotFound):
        return row
    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
    )


def get_price(product: str) -> PriceInfo | ProductNotFound:
    row = find_product(product)
    if isinstance(row, ProductNotFound):
        return row
    return PriceInfo(product_id=row["product_id"], name=row["name"], price=row["price"])


def check_stock(product: str, size: str | None = None) -> StockInfo | ProductNotFound:
    """Live inventory from the inventory table (read fresh on every call)."""
    row = find_product(product)
    if isinstance(row, ProductNotFound):
        return row
    with get_db() as conn:
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (row["product_id"],)
        ).fetchall()

    sizes = sorted(
        (SizeStock(size=s["size"], quantity=s["quantity"], in_stock=s["quantity"] > 0) for s in stock),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99,
    )
    info = StockInfo(
        product_id=row["product_id"],
        name=row["name"],
        sizes=sizes,
        available_sizes=[s.size for s in sizes if s.in_stock],
        sold_out_sizes=[s.size for s in sizes if not s.in_stock],
        total_in_stock=sum(s.quantity for s in sizes),
    )

    if size:
        wanted = normalize_size(size)
        match = next((s for s in sizes if s.size == wanted), None)
        info.requested_size = wanted or size
        if match is None:
            offered = ", ".join(s.size for s in sizes) or "none"
            info.requested_size_note = f"{size!r} is not a size this product comes in. Sizes offered: {offered}."
        elif match.quantity == 0:
            info.requested_size_quantity = 0
            others = ", ".join(info.available_sizes) or "no other sizes either"
            info.requested_size_note = f"Size {match.size} is SOLD OUT (0 left). In stock: {others}."
        else:
            info.requested_size_quantity = match.quantity
            info.requested_size_note = f"Size {match.size} is in stock: {match.quantity} left."
    return info
