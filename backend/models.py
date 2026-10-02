"""Pydantic / PydanticAI structured types shared by the chat API, the agent, and its tools."""
from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 1000


class ChatRequest(BaseModel):
    """What the chat box sends to POST /api/chat."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class ProductCard(BaseModel):
    """A product the chat can show as a clickable card (same fields the Products page uses)."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str] = []
    image_url: str


class ChatReply(BaseModel):
    """What POST /api/chat sends back to the chat box."""

    reply: str = Field(description="Dan's message to the shopper, in plain friendly text.")
    products: list[ProductCard] = Field(default_factory=list, description="Products to show as cards.")


class ProductMatch(BaseModel):
    """One catalogue search result, as the agent sees it (no image paths or internals)."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    description: str


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
