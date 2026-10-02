"""Pydantic / PydanticAI structured types shared by the chat API, the agent, and its tools."""
from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 1000


class ChatRequest(BaseModel):
    """What the chat box sends to POST /api/chat."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class ProductCard(BaseModel):
    """A product shown as a clickable card on the page. Built by the backend from the database
    (never from the model's text), with the same fields the Products page cards use."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str] = []
    description: str
    image_url: str


class ChatReply(BaseModel):
    """What POST /api/chat sends back to the chat box."""

    reply: str = Field(description="Dan's message to the shopper, in plain friendly text.")
    results_title: str | None = Field(default=None, description="Heading for the product cards, e.g. 'Hoodies'.")
    products: list[ProductCard] = Field(default_factory=list, description="Products to show as cards.")


class AgentReply(BaseModel):
    """The agent's structured final answer. main.py turns product_ids into ProductCards."""

    reply: str = Field(description="Your short, friendly chat message to the shopper (plain text).")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id of every product to show as a card on the page, best match first. "
            "Only ids returned by your tools this turn. Empty if no products are relevant."
        ),
    )
    results_title: str | None = Field(
        default=None,
        description="Short heading for the cards, e.g. 'Hoodies' or 'Navy crewnecks under $60'. Null if no cards.",
    )


class ProductMatch(BaseModel):
    """One catalogue search result, as the agent sees it (no image paths or internals)."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    description: str


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
