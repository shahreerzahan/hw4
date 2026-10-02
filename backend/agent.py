"""Campus Customs chat agent: model wiring, system prompt, deps, tool registration, and audit trail.

main.py calls `chat(message, deps, history)` for every message typed in the website's chat box.
The agent answers with an AgentReply (text + product_ids); chat() turns the ids into product cards.
Every step of every run is appended to output/audit_trail.json.
"""
import json
import os
import re
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from portkey_ai import PORTKEY_GATEWAY_URL
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ContentFilterError, ModelHTTPError, UsageLimitExceeded
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.messages import (
    ModelMessage, ModelRequest, ModelResponse, RetryPromptPart, TextPart, ThinkingPart, ToolCallPart, ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.usage import UsageLimits

from pydantic_core import to_jsonable_python

import tools
from models import (
    MAX_CARDS, AgentReply, AuditEntry, Category, ChatReply, CustomerInfo, HistoryMessage, PageInfo, PriceInfo, ProductInfo, ProductNotFound,
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
    category: Category | None = None,
    in_stock_only: bool = False,
    in_stock_size: str | None = None,
) -> SearchResults:
    """Search the Campus Customs catalogue.

    Args:
        query: Keywords such as color, sport, college, school, or who it's for ("navy", "morse",
            "dad", "golf"). Leave empty to browse with filters only.
        max_results: How many products to return (1-12).
        min_price: Lowest price in dollars, if the shopper gave one.
        max_price: Highest price in dollars, e.g. 40 for "under $40".
        category: Limit to one category: Hoodies, Crewnecks, T-Shirts, Quarter-Zips, Jackets,
            or Long Sleeves. Use this when the shopper asks for a type of item.
        in_stock_only: Only products with at least one size in stock right now (live).
        in_stock_size: Only products that have this size in stock right now, e.g. "M".

    Returns total_matches (how many matched in all) plus the best matches with exact names,
    prices, colors, and a short description.
    """
    return tools.search_catalogue(query, max_results, min_price, max_price, category, in_stock_only, in_stock_size)


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


# ---- Audit trail: output/audit_trail.json (append-only) ----

AUDIT_PATH = BACKEND.parent / "output" / "audit_trail.json"
SUMMARY_CHARS = 200
REQUEST_CHARS = 120
ARG_CHARS = 80
_audit_lock = threading.Lock()


def _redact(text: str) -> str:
    """Mask emails and long digit runs (card/phone numbers) before anything is written to disk."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    return re.sub(r"\b(?:\d[ -]?){8,}\d\b", "[number]", text)


def _short(value, limit: int = SUMMARY_CHARS) -> str:
    # Tool results are Pydantic models: log them as readable JSON, not Python reprs.
    text = value if isinstance(value, str) else json.dumps(to_jsonable_python(value), ensure_ascii=False)
    text = _redact(" ".join(text.split()))
    return text if len(text) <= limit else text[:limit] + "…"


def _short_args(args: dict) -> dict:
    return {k: (_short(v, ARG_CHARS) if isinstance(v, str) else v) for k, v in args.items()}


def audit_steps(messages: list[ModelMessage], run_id: str, shopper: str, page: str, request: str,
                final: bool) -> list[AuditEntry]:
    """Turn this run's new PydanticAI messages into audit entries: one per tool call (or one per
    model response with no tool call). Unless final, stop at the first step whose tool results
    haven't come back yet, so entries that were already written never change."""
    results: dict[str, str] = {}
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart):
                    results[part.tool_call_id] = _short(part.content)
                elif isinstance(part, RetryPromptPart) and part.tool_call_id:
                    results[part.tool_call_id] = "retry requested: " + _short(part.content)

    entries: list[AuditEntry] = []
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    for iteration, msg in enumerate(responses, start=1):
        calls = [p for p in msg.parts if isinstance(p, ToolCallPart)]
        if not final and any(c.tool_call_id not in results for c in calls):
            break
        text = " ".join(p.content for p in msg.parts if isinstance(p, (TextPart, ThinkingPart)) and p.content)
        step = dict(
            timestamp=msg.timestamp.astimezone(timezone.utc).isoformat(),
            run_id=run_id, iteration=iteration, model=msg.model_name or MODEL_NAME,
            shopper=shopper, page=page, tokens_used=msg.usage.total_tokens or None,
        )
        if not calls:
            entries.append(AuditEntry(**step, result_summary=_short(text or "(empty response)"), stop_reason="final_output"))
        for call in calls:
            args = call.args_as_dict()
            if call.tool_name.startswith("final_result"):
                # The structured answer: log the reply text as the result and the rest as args.
                entries.append(AuditEntry(
                    **step, tool_name=call.tool_name,
                    tool_args={k: v for k, v in args.items() if k != "reply"},
                    result_summary=_short(args.get("reply", "")),
                    stop_reason="final_output",
                ))
            else:
                entries.append(AuditEntry(
                    **step, tool_name=call.tool_name, tool_args=_short_args(args),
                    result_summary=results.get(call.tool_call_id, "no result (run ended)"),
                    stop_reason="tool_call",
                ))
            step["tokens_used"] = None  # count a step's tokens once, not once per tool call
    if entries:
        entries[0].request = _short(request, REQUEST_CHARS)
    return entries


def append_audit(entries: list[AuditEntry]) -> None:
    """Read the existing list, add the new entries, write it back. Old entries are never removed.
    If the file is unreadable it is moved aside (never overwritten) and a new list is started."""
    if not entries:
        return
    with _audit_lock:
        trail = []
        if AUDIT_PATH.exists():
            try:
                trail = json.loads(AUDIT_PATH.read_text() or "[]")
            except json.JSONDecodeError:
                AUDIT_PATH.rename(AUDIT_PATH.with_suffix(f".corrupt-{datetime.now():%Y%m%d%H%M%S}.json"))
        trail += [e.model_dump(exclude_none=False) for e in entries]
        AUDIT_PATH.parent.mkdir(exist_ok=True)
        tmp = AUDIT_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(trail, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(AUDIT_PATH)  # atomic: a crash mid-write can't leave a half-written file


def _ending(run_id: str, shopper: str, page: str, request: str, iteration: int, reason: str, summary: str) -> AuditEntry:
    return AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(), run_id=run_id, iteration=iteration, model=MODEL_NAME,
        shopper=shopper, page=page, request=_short(request, REQUEST_CHARS) if iteration == 1 else None,
        result_summary=_short(summary), stop_reason=reason,
    )


async def chat(message: str, deps: ChatDeps, history: list[HistoryMessage]) -> ChatResult:
    """Run the agent on one shopper message (with earlier messages as memory) and return Dan's reply.

    Each step is appended to the audit trail as soon as it finishes. The model provider's safety
    filter and our usage caps become friendly replies; any other model error (e.g. the API is
    down) is logged and raised for main.py to turn into an HTTP error."""
    shopper = f"user:{deps.customer.user_id}" if deps.customer else "guest"
    page = deps.page.path
    run_id = uuid.uuid4().hex
    written = 0

    def log_progress(run, final: bool) -> int:
        entries = audit_steps(run.new_messages(), run_id, shopper, page, message, final)
        append_audit(entries[written:])
        return len(entries)

    try:
        async with agent.iter(
            with_page_note(message, deps.page),
            deps=deps,
            message_history=to_model_messages(history),
            usage_limits=LIMITS,
        ) as run:
            try:
                async for _ in run:
                    written = log_progress(run, final=False)
            except Exception:
                written = log_progress(run, final=True)
                raise
            written = log_progress(run, final=True)
            out = run.result.output
    except (ContentFilterError, ModelHTTPError) as e:
        if isinstance(e, ModelHTTPError) and not _is_content_filter(e):
            append_audit([_ending(run_id, shopper, page, message, written + 1, "error", f"{type(e).__name__}: {e}")])
            raise
        append_audit([_ending(run_id, shopper, page, message, written + 1, "content_filter",
                              "Blocked by the model provider's content filter; sent the friendly on-topic reply.")])
        return ChatResult(ChatReply(reply=BLOCKED_REPLY), remember=False)
    except UsageLimitExceeded as e:
        append_audit([_ending(run_id, shopper, page, message, written + 1, "usage_limit", f"Stopped by loop limits: {e}")])
        return ChatResult(ChatReply(reply=TOO_COMPLEX_REPLY), remember=False)
    except Exception as e:
        append_audit([_ending(run_id, shopper, page, message, written + 1, "error", f"{type(e).__name__}: {e}")])
        raise

    # Cards are rebuilt from the catalogue, so names, prices, and images on the page are always
    # real even if the model mistyped something. Unknown ids are dropped, and at most MAX_CARDS
    # are kept even if the model listed more.
    cards = tools.product_cards(out.product_ids, limit=MAX_CARDS)
    see_all = out.see_all_category if out.see_all_category in tools.CATEGORIES else None
    reply = ChatReply(
        reply=out.reply.strip(),
        results_title=(out.results_title or "Dan's picks") if cards else None,
        products=cards,
        see_all_category=see_all,
        see_all_count=tools.category_counts()[see_all] if see_all else None,
    )
    return ChatResult(reply, remember=True)
