"""Tools the Campus Customs agent can call. Plain functions over the database (no AI calls here);
agent.py registers them with the agent.

Speed: the catalogue (names, prices, descriptions) is loaded once into memory and reused for
CATALOGUE_TTL_SECONDS, with its search words pre-computed. Stock is different: inventory is read
live from the database on every call, so quantities are never stale.
"""
import json
import re
import threading
import time
from dataclasses import dataclass
from typing import get_args

from db import get_db, image_url
from models import (
    MAX_CARDS, Category, PageInfo, PriceInfo, ProductCard, ProductInfo, ProductMatch, ProductNotFound,
    SearchResults, SimilarInStock, SizeStock, StockInfo,
)

MAX_RESULTS = 12  # search results the agent sees (it picks up to MAX_CARDS of them for cards)
LOW_STOCK_TOTAL = 30  # "Low stock" badge: 30 or fewer units left across all sizes (live)
# "New" badge: the database has no date-added field, so new arrivals are a list the shop sets.
NEW_ARRIVALS = {
    "2025-yale-vs-harvard-t-shirt",
    "hype-and-vice-yale-university-offside-crewneck",
    "hype-and-vice-yale-university-premium-crewneck",
    "yale-maplehouse-diana-mockneck",
    "brooks-brothers-bomber-jacket-yale",
}
SHORT_DESCRIPTION_CHARS = 110
CATALOGUE_TTL_SECONDS = 300
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
CATEGORIES: tuple[str, ...] = get_args(Category)

_STOPWORDS = {
    "a", "an", "and", "the", "of", "on", "with", "in", "for", "to", "me", "my", "i", "do", "you",
    "have", "any", "some", "show", "find", "want", "looking", "something", "please", "yale",
}


def _words(text: str) -> set[str]:
    """Whole words, lowercased, with a simple plural -> singular ("hoodies" -> "hoodie").
    "t-shirt" / "tee" / "tshirt" all become "tshirt", and "quarter-zip" / "1/4 zip" become
    "quarterzip", and "hood" / "hooded" / "hoodies" become "hoodie", so the different spellings
    match each other."""
    text = re.sub(r"\bt[\s-]?shirts?\b|\btees?\b", "tshirt", text.lower())
    text = re.sub(r"\bhood(?:s|ed|ies|ie)?\b", "hoodie", text)
    text = re.sub(r"\b(?:quarter|1\s*/?\s*4)[\s-]*zips?\b", "quarterzip", text)
    words = set()
    for w in re.findall(r"[a-z0-9]+", text):
        if w in _STOPWORDS:
            continue
        words.add(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w)
    return words


def category_for(garment_type: str) -> str:
    """Map the catalogue's free-text garment_type ("pullover hoodie", "hooded sweatshirt", …)
    to one shopper-facing category. Order matters: a "full-zip hooded sweatshirt" is a hoodie."""
    g = garment_type.lower()
    if "hood" in g:
        return "Hoodies"
    if "quarter-zip" in g or "1/4" in g:
        return "Quarter-Zips"
    if "jacket" in g:
        return "Jackets"
    if "t-shirt" in g or "tee" in g:
        return "T-Shirts"
    if "long-sleeve" in g:
        return "Long Sleeves"
    return "Crewnecks"  # crewneck, raglan crewneck, mockneck sweatshirts


# ---------- In-memory catalogue (refreshed every CATALOGUE_TTL_SECONDS) ----------

@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    garment_type: str
    category: str
    description: str
    colors: tuple[str, ...]
    price: float
    image_file_path: str
    strong_words: frozenset[str]  # name, type, tags: count more in search
    weak_words: frozenset[str]    # description, colors
    name_words: frozenset[str]    # name + id: used to match a product someone names

    def short_description(self) -> str:
        d = self.description
        return d if len(d) <= SHORT_DESCRIPTION_CHARS else d[:SHORT_DESCRIPTION_CHARS].rsplit(" ", 1)[0] + "…"


_cache: dict = {"loaded_at": 0.0, "products": [], "by_id": {}}
_cache_lock = threading.Lock()


def _load_catalogue() -> list[Product]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    products = []
    for r in rows:
        colors, tags = json.loads(r["colors"]), json.loads(r["search_tags"])
        products.append(Product(
            product_id=r["product_id"],
            name=r["name"],
            garment_type=r["garment_type"],
            category=category_for(r["garment_type"]),
            description=r["description"],
            colors=tuple(colors),
            price=r["price"],
            image_file_path=r["image_file_path"],
            strong_words=frozenset(_words(" ".join([r["name"], r["garment_type"], *tags]))),
            weak_words=frozenset(_words(" ".join([r["description"], *colors]))),
            name_words=frozenset(_words(r["name"] + " " + r["product_id"].replace("-", " "))),
        ))
    return products


def catalogue() -> list[Product]:
    """All products, from memory. Reloaded from the database at most every CATALOGUE_TTL_SECONDS."""
    with _cache_lock:
        if time.monotonic() - _cache["loaded_at"] > CATALOGUE_TTL_SECONDS or not _cache["products"]:
            products = _load_catalogue()
            _cache.update(products=products, by_id={p.product_id: p for p in products}, loaded_at=time.monotonic())
        return _cache["products"]


def get_cached_product(product_id: str) -> Product | None:
    catalogue()
    return _cache["by_id"].get(product_id)


def clear_catalogue_cache() -> None:
    """Call after changing products or prices in the database to see the change immediately."""
    with _cache_lock:
        _cache["loaded_at"] = 0.0


def category_counts() -> dict[str, int]:
    counts = {c: 0 for c in CATEGORIES}
    for p in catalogue():
        counts[p.category] += 1
    return counts


def _stock_by_product(size: str | None) -> dict[str, int]:
    """Live: units in stock per product (in one size, or across all sizes)."""
    with get_db() as conn:
        if size:
            rows = conn.execute("SELECT product_id, quantity AS q FROM inventory WHERE size = ?", (size,)).fetchall()
        else:
            rows = conn.execute("SELECT product_id, SUM(quantity) AS q FROM inventory GROUP BY product_id").fetchall()
    return {r["product_id"]: r["q"] for r in rows}


def product_badges() -> dict[str, str]:
    """Badge per product for the cards: "Low stock" (live from inventory) wins over "New"."""
    totals = _stock_by_product(None)
    badges = {pid: "New" for pid in NEW_ARRIVALS}
    badges.update({pid: "Low stock" for pid, total in totals.items() if 0 < total <= LOW_STOCK_TOTAL})
    return badges


# ---------- Search ----------

def search_catalogue(
    query: str = "",
    max_results: int = 8,
    min_price: float | None = None,
    max_price: float | None = None,
    category: str | None = None,
    in_stock_only: bool = False,
    in_stock_size: str | None = None,
) -> SearchResults:
    """Rank products by how many query words appear in their name, type, tags (count 3x),
    description, and colors (1x), with optional price, category, and live stock filters.
    An empty query lists everything that passes the filters, cheapest first."""
    words = _words(query)
    size = normalize_size(in_stock_size) if in_stock_size else None
    stock = _stock_by_product(size) if (in_stock_only or size) else None

    scored = []
    for p in catalogue():
        if min_price is not None and p.price < min_price:
            continue
        if max_price is not None and p.price > max_price:
            continue
        if category and p.category != category:
            continue
        if stock is not None and stock.get(p.product_id, 0) <= 0:
            continue
        score = sum(3 * (w in p.strong_words) + (w in p.weak_words) for w in words)
        if score or not words:
            scored.append((score, p))

    scored.sort(key=lambda s: (-s[0], s[1].price, s[1].name))
    products = [
        ProductMatch(
            product_id=p.product_id,
            name=p.name,
            category=p.category,
            price=p.price,
            colors=list(p.colors),
            short_description=p.short_description(),
        )
        for _, p in scored[: max(1, min(max_results, MAX_RESULTS))]
    ]
    return SearchResults(total_matches=len(scored), showing=len(products), products=products)


def product_cards(product_ids: list[str], limit: int = MAX_CARDS) -> list[ProductCard]:
    """Build page cards for the products the agent picked, from the catalogue. Unknown ids are
    dropped, duplicates removed, the agent's order kept, and at most `limit` cards returned."""
    cards = []
    badges = product_badges() if product_ids else {}
    for pid in dict.fromkeys(pid.strip() for pid in product_ids if pid.strip()):
        p = get_cached_product(pid)
        if p:
            cards.append(ProductCard(
                product_id=p.product_id,
                name=p.name,
                garment_type=p.garment_type,
                category=p.category,
                price=p.price,
                colors=list(p.colors),
                description=p.description,
                image_url=image_url(p.image_file_path),
                badge=badges.get(p.product_id),
            ))
        if len(cards) >= limit:
            break
    return cards


# ---------- Lookups for one product: info, price, stock ----------

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


def find_product(query: str) -> Product | ProductNotFound:
    """Match a product id or (partial) product name to exactly one product.

    Tries: exact product_id, exact name, then the name containing the most query words.
    If two or more products tie, returns ProductNotFound with them as suggestions so the
    agent can ask which one the shopper means instead of guessing."""
    text = query.strip()
    products = catalogue()
    exact = get_cached_product(text.lower()) or next((p for p in products if p.name.lower() == text.lower()), None)
    if exact:
        return exact

    words = _words(text)
    if not words:
        return ProductNotFound(query=query, message="Please give a product name to look up.")

    scored = []
    for p in products:
        hits = len(words & p.name_words)
        if hits:
            # More query words matched is better; fewer unmatched name words breaks ties.
            scored.append((hits, -len(p.name_words - words), p))
    scored.sort(key=lambda s: (-s[0], -s[1], s[2].name))

    if not scored or scored[0][0] < max(1, (len(words) + 1) // 2):
        close = [s[2].name for s in scored[:3]]
        return ProductNotFound(
            query=query, message="No product with that name is in the Campus Customs catalogue.", suggestions=close
        )
    best = [s for s in scored if s[:2] == scored[0][:2]]
    if len(best) > 1:
        return ProductNotFound(
            query=query,
            message="Several products match that name. Ask the shopper which one they mean.",
            suggestions=[s[2].name for s in best[:6]],
        )
    return scored[0][2]


def get_product_info(product: str) -> ProductInfo | ProductNotFound:
    p = find_product(product)
    if isinstance(p, ProductNotFound):
        return p
    return ProductInfo(
        product_id=p.product_id, name=p.name, garment_type=p.garment_type,
        description=p.description, colors=list(p.colors),
    )


def get_price(product: str) -> PriceInfo | ProductNotFound:
    p = find_product(product)
    if isinstance(p, ProductNotFound):
        return p
    return PriceInfo(product_id=p.product_id, name=p.name, price=p.price)


def _nearest_sizes(wanted: str, available: list[str]) -> list[str]:
    """In-stock sizes ordered by how close they are to the wanted one (M -> L, S, XL, …)."""
    if wanted not in SIZE_ORDER:
        return available
    i = SIZE_ORDER.index(wanted)
    return sorted(available, key=lambda s: (abs(SIZE_ORDER.index(s) - i), SIZE_ORDER.index(s)))


def similar_in_stock(product: Product, size: str | None, limit: int = 3) -> list[SimilarInStock]:
    """Products in the same category with the size in stock (live), most similar first
    (shared name/tag words with the sold-out product)."""
    with get_db() as conn:
        if size:
            rows = conn.execute("SELECT product_id, size, quantity FROM inventory WHERE size = ? AND quantity > 0", (size,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT product_id, '' AS size, SUM(quantity) AS quantity FROM inventory GROUP BY product_id HAVING SUM(quantity) > 0"
            ).fetchall()
    in_stock = {r["product_id"]: r for r in rows}
    candidates = []
    for p in catalogue():
        if p.product_id == product.product_id or p.category != product.category or p.product_id not in in_stock:
            continue
        overlap = len(product.strong_words & p.strong_words)
        candidates.append((overlap, -abs(p.price - product.price), p))
    candidates.sort(key=lambda c: (-c[0], -c[1], c[2].name))
    return [
        SimilarInStock(
            product_id=p.product_id, name=p.name, price=p.price,
            size=size or "any", quantity=in_stock[p.product_id]["quantity"],
        )
        for _, _, p in candidates[:limit]
    ]


def check_stock(product: str, size: str | None = None) -> StockInfo | ProductNotFound:
    """Live inventory from the inventory table (read fresh on every call). If the requested size
    (or the whole product) is sold out, also suggests the nearest in-stock sizes and similar
    products that have that size."""
    p = find_product(product)
    if isinstance(p, ProductNotFound):
        return p
    with get_db() as conn:
        stock = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (p.product_id,)).fetchall()

    sizes = sorted(
        (SizeStock(size=s["size"], quantity=s["quantity"], in_stock=s["quantity"] > 0) for s in stock),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99,
    )
    info = StockInfo(
        product_id=p.product_id,
        name=p.name,
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
            info.nearest_in_stock_sizes = _nearest_sizes(match.size, info.available_sizes)
            info.similar_in_stock = similar_in_stock(p, match.size)
            nearest = ", ".join(info.nearest_in_stock_sizes) or "no other sizes"
            info.requested_size_note = (
                f"Size {match.size} is SOLD OUT (0 left). Nearest sizes in stock: {nearest}. "
                f"Similar items with {match.size} in stock: {len(info.similar_in_stock)} listed below."
            )
        else:
            info.requested_size_quantity = match.quantity
            info.requested_size_note = f"Size {match.size} is in stock: {match.quantity} left."

    if info.total_in_stock == 0 and not info.similar_in_stock:
        wanted = normalize_size(size) if size else None
        info.similar_in_stock = similar_in_stock(p, wanted)
    return info


# ---------- Which page is the shopper on? ----------

_PAGE_TYPES = {"/": "home", "/products": "products", "/about": "about", "/login": "login",
               "/create-account": "create-account"}


def describe_page(path: str | None) -> PageInfo:
    """Turn the browser's URL path into PageInfo. For /products/<id>, the product is looked up
    in the catalogue, so the agent only ever sees a real product (never one typed by the client)."""
    path = (path or "/").split("?")[0].split("#")[0].rstrip("/") or "/"
    if path in _PAGE_TYPES:
        return PageInfo(path=path, page_type=_PAGE_TYPES[path])
    m = re.fullmatch(r"/products/([a-z0-9-]+)", path)
    if m and (p := get_cached_product(m.group(1))):
        return PageInfo(path=path, page_type="product", product_id=p.product_id, product_name=p.name)
    return PageInfo(path=path, page_type="other")
