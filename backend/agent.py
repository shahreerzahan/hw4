"""Campus Customs chat agent: model wiring, system prompt, and tool registration.

main.py calls `chat(message)` for every message typed in the website's chat box.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from portkey_ai import PORTKEY_GATEWAY_URL
from pydantic_ai import Agent
from pydantic_ai.exceptions import ContentFilterError, ModelHTTPError, UsageLimitExceeded
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import tools
from models import ChatReply, ProductMatch

BACKEND = Path(__file__).resolve().parent
load_dotenv(BACKEND.parent / ".env")

# ---- Model: GPT through the Portkey gateway (same setup as Homework 3) ----
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.6-luna")
_key = os.environ["PORTKEY_API_KEY"]
_client = AsyncOpenAI(base_url=PORTKEY_GATEWAY_URL, api_key=_key, default_headers={"x-portkey-api-key": _key})
MODEL = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=_client))

# ---- System prompt: read from prompts/prompt.md (edit that file to change Dan's behavior) ----
PROMPT_PATH = BACKEND / "prompts" / "prompt.md"

# A normal reply is 1–2 model requests (maybe one search, then the answer). These caps stop a
# confused agent from looping and running up cost.
LIMITS = UsageLimits(request_limit=5, tool_calls_limit=4)

agent = Agent(
    MODEL,
    output_type=str,
    instructions=PROMPT_PATH.read_text(),
)


@agent.tool_plain
def search_catalogue(
    query: str = "",
    max_results: int = 6,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[ProductMatch]:
    """Search the Campus Customs catalogue.

    Args:
        query: Keywords such as type, color, sport, college, or who it's for ("navy hoodie",
            "morse", "dad"). Leave empty to browse only by price.
        max_results: How many products to return (1-8).
        min_price: Lowest price in dollars, if the shopper gave one.
        max_price: Highest price in dollars, e.g. 40 for "under $40".

    Returns matching products with their exact names, prices, colors, and descriptions.
    """
    return tools.search_catalogue(query, max_results, min_price, max_price)


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


async def chat(message: str) -> ChatReply:
    """Run the agent on one shopper message and return Dan's reply.

    The model provider's safety filter and our usage caps become friendly replies; any other
    model error (e.g. the API is down) is raised for main.py to turn into an HTTP error."""
    try:
        result = await agent.run(message, usage_limits=LIMITS)
    except ContentFilterError:
        return ChatReply(reply=BLOCKED_REPLY)
    except ModelHTTPError as e:
        if _is_content_filter(e):
            return ChatReply(reply=BLOCKED_REPLY)
        raise
    except UsageLimitExceeded:
        return ChatReply(reply=TOO_COMPLEX_REPLY)
    return ChatReply(reply=result.output.strip())
