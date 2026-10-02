"""Pydantic / PydanticAI structured types shared by the chat API, the agent, and its tools."""
from typing import Literal

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 1000
MAX_CARDS = 6  # most product cards one chat reply may put on the page

# Shopper-facing categories, derived from each product's garment_type (see tools.category_for).
Category = Literal["Hoodies", "Crewnecks", "T-Shirts", "Quarter-Zips", "Jackets", "Long Sleeves"]


MAX_GUEST_HISTORY = 10


class HistoryMessage(BaseModel):
    """One earlier chat message. Guests' chat boxes send their recent messages back with each
    request (they aren't saved on the server); logged-in shoppers' history comes from the DB."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    product_ids: list[str] = Field(default_factory=list, max_length=30)
    page_path: str | None = Field(default=None, max_length=200, description="Page the message was sent from.")


class ChatRequest(BaseModel):
    """What the chat box sends to POST /api/chat."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    page_path: str | None = Field(default=None, max_length=200, description="e.g. /products/morse-1-4-zip")
    history: list[HistoryMessage] = Field(default_factory=list, max_length=MAX_GUEST_HISTORY)


class ProductCard(BaseModel):
    """A product shown as a clickable card on the page. Built by the backend from the database
    (never from the model's text), with the same fields the Products page cards use."""

    product_id: str
    name: str
    garment_type: str
    category: Category
    price: float
    colors: list[str] = []
    description: str
    image_url: str
    badge: Literal["New", "Low stock"] | None = None


class ChatReply(BaseModel):
    """What POST /api/chat sends back to the chat box."""

    reply: str = Field(description="Dan's message to the shopper, in plain friendly text.")
    results_title: str | None = Field(default=None, description="Heading for the product cards, e.g. 'Hoodies'.")
    products: list[ProductCard] = Field(default_factory=list, description=f"Up to {MAX_CARDS} products to show as cards.")
    see_all_category: Category | None = Field(default=None, description="Category for a 'See all' link to the Products page.")
    see_all_count: int | None = Field(default=None, description="How many products that category has.")


class AgentReply(BaseModel):
    """The agent's structured final answer. main.py turns product_ids into ProductCards."""

    reply: str = Field(description="Your short, friendly chat message to the shopper (plain text).")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            f"product_id of up to {MAX_CARDS} products to show as cards on the page, best match first. "
            "Only ids returned by your tools. Empty if no products are relevant."
        ),
    )
    see_all_category: Category | None = Field(
        default=None,
        description="When the shopper is browsing a whole category with more matches than the cards, that "
        "category, so the page can link to the full list on the Products page. Otherwise null.",
    )
    results_title: str | None = Field(
        default=None,
        description="Short heading for the cards, e.g. 'Hoodies' or 'Navy crewnecks under $60'. Null if no cards.",
    )


class ProductMatch(BaseModel):
    """One catalogue search result, as the agent sees it (no image paths or internals).
    The description is shortened to save tokens; get_product_info has the full text."""

    product_id: str
    name: str
    category: Category
    price: float
    colors: list[str]
    short_description: str


class SearchResults(BaseModel):
    """search_catalogue: the best matches plus how many matched in total."""

    total_matches: int = Field(description="How many catalogue products matched in total.")
    showing: int = Field(description="How many are in `products` (may be fewer than total_matches).")
    products: list[ProductMatch]


# ---------- Lookup tool results (what the agent sees) ----------

class ProductNotFound(BaseModel):
    """Returned by a lookup tool when no single product matches what the shopper asked about."""

    found: bool = False
    query: str
    message: str
    suggestions: list[str] = Field(default_factory=list, description="Closest product names, if any.")


class ProductInfo(BaseModel):
    """get_product_info: what the product is and looks like (no price or stock)."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]


class PriceInfo(BaseModel):
    """get_price: the current price, straight from the catalogue."""

    product_id: str
    name: str
    price: float
    currency: str = "USD"


class SizeStock(BaseModel):
    size: str
    quantity: int
    in_stock: bool


class SimilarInStock(BaseModel):
    """A similar product that has the shopper's size in stock (suggested when theirs is sold out)."""

    product_id: str
    name: str
    price: float
    size: str
    quantity: int


class StockInfo(BaseModel):
    """check_stock: live inventory for one product, optionally focused on one size."""

    product_id: str
    name: str
    sizes: list[SizeStock] = Field(description="Every size in XS-XXL order, with its quantity.")
    available_sizes: list[str]
    sold_out_sizes: list[str]
    total_in_stock: int
    requested_size: str | None = Field(default=None, description="The size the shopper asked about, normalized (e.g. 'M').")
    requested_size_quantity: int | None = None
    requested_size_note: str | None = Field(default=None, description="Plain-language answer for the requested size.")
    nearest_in_stock_sizes: list[str] = Field(
        default_factory=list, description="If the requested size is sold out: in-stock sizes closest to it, nearest first."
    )
    similar_in_stock: list[SimilarInStock] = Field(
        default_factory=list,
        description="If the requested size (or the whole product) is sold out: similar products in the same "
        "category that have that size in stock.",
    )


# ---------- Customer memory: deps and saved history ----------

class CustomerInfo(BaseModel):
    """Who is chatting (logged-in shoppers only). Passed to the agent through deps."""

    user_id: int
    first_name: str
    last_name: str
    email: str


class PageInfo(BaseModel):
    """The page the shopper is looking at, resolved by the backend from the URL path."""

    path: str
    page_type: Literal["home", "products", "product", "about", "login", "create-account", "other"]
    product_id: str | None = None
    product_name: str | None = None


class ChatHistoryItem(BaseModel):
    """One saved message, as GET /api/chat/history returns it to the chat box."""

    role: Literal["user", "assistant"]
    content: str
    results_title: str | None = None
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


# ---------- Audit trail (output/audit_trail.json) ----------

class AuditEntry(BaseModel):
    """One step of an agent run: a tool call, the final answer, or how the run ended."""

    timestamp: str = Field(description="UTC time of the step, ISO 8601.")
    run_id: str = Field(description="Groups the steps of one chat message.")
    iteration: int = Field(description="Which model response in the run this step came from (1, 2, …).")
    model: str
    shopper: str = Field(description="'guest' or 'user:<id>'. Never a name, email, or password.")
    page: str = Field(description="Page the message was sent from, e.g. /products/morse-1-4-zip.")
    request: str | None = Field(default=None, description="The shopper's message, shortened and redacted (first step only).")
    tool_name: str | None = Field(default=None, description="Tool called, or 'final_result' for the structured answer.")
    tool_args: dict | None = Field(default=None, description="Arguments the agent passed, shortened.")
    result_summary: str = Field(description="Short version of the tool result or answer.")
    stop_reason: Literal["tool_call", "final_output", "content_filter", "usage_limit", "error"]
    tokens_used: int | None = Field(default=None, description="Tokens for this model response (counted once per step).")
