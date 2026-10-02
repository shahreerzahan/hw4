"""Tools the Campus Customs agent can call. Plain functions over the database (no AI calls here);
agent.py registers them with the agent."""
import json
import re

from db import get_db
from models import ProductMatch

MAX_RESULTS = 8
_STOPWORDS = {
    "a", "an", "and", "the", "of", "on", "with", "in", "for", "to", "me", "my", "i", "do", "you",
    "have", "any", "some", "show", "find", "want", "looking", "something", "please", "yale",
}


def _words(text: str) -> set[str]:
    """Whole words, lowercased, with a simple plural -> singular ("hoodies" -> "hoodie").
    "t-shirt" / "tee" / "tshirt" all become "tshirt" so they match each other."""
    text = re.sub(r"\bt[\s-]?shirts?\b|\btees?\b", "tshirt", text.lower())
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
