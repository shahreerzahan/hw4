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
