"""Campus Customs chat agent: model wiring, system prompt, deps, and tool registration.

main.py calls `chat(message, deps, history)` for every message typed in the website's chat box.
The agent answers with an AgentReply (text + product_ids); chat() turns the ids into product cards.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from portkey_ai import PORTKEY_GATEWAY_URL
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ContentFilterError, ModelHTTPError, UsageLimitExceeded
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.usage import UsageLimits

import tools
from models import (
    AgentReply, ChatReply, CustomerInfo, HistoryMessage, PageInfo, PriceInfo, ProductInfo, ProductNotFound,
    SearchResults, StockInfo,
)

BACKEND = Path(__file__).resolve().parent
load_dotenv(BACKEND.parent / ".env")

# ---- Model: GPT through the Portkey gateway (same setup as Homework 3) ----
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.6-luna")
_key = os.environ["PORTKEY_API_KEY"]
_client = AsyncOpenAI(base_url=PORTKEY_GATEWAY_URL, api_key=_key, default_headers={"x-portkey-api-key": _key})
MODEL = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=_client))

# ---- System prompt: read from prompts/prompt.md (edit that file to change Dan's behavior) ----
PROMPT_PATH = BACKEND / "prompts" / "prompt.md"

# A normal reply is 1–3 model requests (e.g. search, then a price/stock lookup, then the answer).
# These caps stop a confused agent from looping and running up cost.
LIMITS = UsageLimits(request_limit=6, tool_calls_limit=6)



@dataclass
class ChatDeps:
    """Per-request context for the agent. Built by main.py from the login cookie and the page
    URL; the shopper can't edit it through the chat."""

    customer: CustomerInfo | None  # None for guests
    page: PageInfo


# Structured output: a short chat reply plus the product_ids to show as cards on the page.
agent = Agent(
    MODEL,
    deps_type=ChatDeps,
    output_type=AgentReply,
    instructions=PROMPT_PATH.read_text(),
)


@agent.instructions
def shopper_context(ctx: RunContext[ChatDeps]) -> str:
    """Added to the system prompt on every request: who is chatting and which page they're on."""
    c, page = ctx.deps.customer, ctx.deps.page
    who = (
        f"The shopper is logged in as {c.first_name} {c.last_name} ({c.email})."
        if c else "The shopper is a guest (not logged in). You don't know their name or email."
    )
    if page.page_type == "product":
        where = (
            f"They are on the product page for \"{page.product_name}\" (product_id: {page.product_id}). "
            "If they say \"this\", \"it\", or \"this one\" without naming a product, they mean THIS product, "
            "even if earlier messages talked about other products."
        )
    else:
        where = f"They are on the {page.page_type} page ({page.path})."
    return f"## Current shopper context\n\n- {who}\n- {where}"


@agent.tool_plain
def search_catalogue(
    query: str = "",
    max_results: int = 8,
    min_price: float | None = None,
    max_price: float | None = None,
) -> SearchResults:
    """Search the Campus Customs catalogue.

    Args:
        query: Keywords such as type, color, sport, college, or who it's for ("navy hoodie",
            "morse", "dad"). Leave empty to browse only by price.
        max_results: How many products to return (1-30). Use 30 when the shopper wants to
            browse a whole type ("what hoodies do you have?"), about 8 for a recommendation.
        min_price: Lowest price in dollars, if the shopper gave one.
        max_price: Highest price in dollars, e.g. 40 for "under $40".

    Returns total_matches plus the best matching products with their exact names, prices,
    colors, and descriptions.
    """
    return tools.search_catalogue(query, max_results, min_price, max_price)


@agent.tool_plain
def get_product_info(product: str) -> ProductInfo | ProductNotFound:
    """Look up one product's full description, garment type, and colors.

    Args:
        product: The product's exact name (e.g. "Morse 1 4 Zip") or product_id from a search.
    """
    return tools.get_product_info(product)


@agent.tool_plain
def get_price(product: str) -> PriceInfo | ProductNotFound:
    """Look up one product's current price from the database. Use this for every price question.

    Args:
        product: The product's exact name or product_id.
    """
    return tools.get_price(product)


@agent.tool_plain
def check_stock(product: str, size: str | None = None) -> StockInfo | ProductNotFound:
    """Look up live stock for one product: the quantity in every size, which sizes are sold out,
    and the total. Use this for every stock, size, or availability question.

    Args:
        product: The product's exact name or product_id.
        size: The size the shopper asked about, if any (XS, S, M, L, XL, XXL; "medium" and
            "2XL" also work). Leave empty to get every size.
    """
    return tools.check_stock(product, size)


BLOCKED_REPLY = (
    "Woof, I can't help with that one. I'm here to help you find great Campus Customs gear! "
    "Want me to show you some hoodies or crewnecks?"
)
TOO_COMPLEX_REPLY = (
    "Ruff, that one tied my leash in knots! Could you ask in a simpler way, "
    "like \"navy hoodies\" or \"a gift for my dad\"?"
)


def _is_content_filter(error: ModelHTTPError) -> bool:
    body = error.body if isinstance(error.body, dict) else {}
    return body.get("code") == "content_filter"


def with_page_note(message: str, page: PageInfo) -> str:
    """Prefix a shopper message with the product page it was sent from (added by the server, so
    "this" can be resolved per message, even in old history)."""
    if page.page_type == "product":
        return f"[Sent from the product page: {page.product_name} (product_id: {page.product_id})]\n{message}"
    return message


def to_model_messages(history: list[HistoryMessage]) -> list[ModelMessage]:
    """Earlier chat messages as PydanticAI message history (oldest first), so Dan remembers the
    conversation. Shopper turns note the product page they were sent from; assistant turns note
    which product cards were shown, so follow-ups like "the second one" can be resolved."""
    messages: list[ModelMessage] = []
    for h in history:
        if h.role == "user":
            text = with_page_note(h.content, tools.describe_page(h.page_path))
            messages.append(ModelRequest(parts=[UserPromptPart(content=text)]))
        else:
            text = h.content
            if h.product_ids:
                text += "\n[Product cards shown: " + ", ".join(h.product_ids) + "]"
            messages.append(ModelResponse(parts=[TextPart(content=text)]))
    return messages


@dataclass
class ChatResult:
    reply: ChatReply
    remember: bool  # False if the turn was blocked, so it isn't saved or replayed as memory


async def chat(message: str, deps: ChatDeps, history: list[HistoryMessage]) -> ChatResult:
    """Run the agent on one shopper message (with earlier messages as memory) and return Dan's reply.

    The model provider's safety filter and our usage caps become friendly replies; any other
    model error (e.g. the API is down) is raised for main.py to turn into an HTTP error."""
    try:
        result = await agent.run(
            with_page_note(message, deps.page),
            deps=deps,
            message_history=to_model_messages(history),
            usage_limits=LIMITS,
        )
    except ContentFilterError:
        return ChatResult(ChatReply(reply=BLOCKED_REPLY), remember=False)
    except ModelHTTPError as e:
        if _is_content_filter(e):
            return ChatResult(ChatReply(reply=BLOCKED_REPLY), remember=False)
        raise
    except UsageLimitExceeded:
        return ChatResult(ChatReply(reply=TOO_COMPLEX_REPLY), remember=False)

    out = result.output
    # Cards are rebuilt from the database, so names, prices, and images on the page are always
    # real even if the model mistyped something. Unknown ids are simply dropped.
    cards = tools.product_cards(out.product_ids)
    reply = ChatReply(
        reply=out.reply.strip(),
        results_title=(out.results_title or "Dan's picks") if cards else None,
        products=cards,
    )
    return ChatResult(reply, remember=True)
