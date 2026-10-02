"""Saved chat history for logged-in shoppers (the chat_history table)."""
import json

import tools
from db import get_db
from models import ChatHistoryItem, HistoryMessage

AGENT_CONTEXT_MESSAGES = 20   # how many recent messages the agent gets as memory
UI_HISTORY_MESSAGES = 100     # how many the chat box shows when the shopper comes back


def save_turn(user_id: int, message: str, reply: str, product_ids: list[str],
              results_title: str | None, page_path: str | None) -> None:
    """Store the shopper's message and Dan's reply as two rows."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, content, page_path) VALUES (?, 'user', ?, ?)",
            (user_id, message, page_path),
        )
        conn.execute(
            "INSERT INTO chat_history (user_id, role, content, product_ids, results_title, page_path) "
            "VALUES (?, 'assistant', ?, ?, ?, ?)",
            (user_id, reply, json.dumps(product_ids) if product_ids else None, results_title, page_path),
        )


def _recent_rows(user_id: int, limit: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
    return list(reversed(rows))


def recent_for_agent(user_id: int) -> list[HistoryMessage]:
    """The shopper's latest messages, oldest first, as memory for the agent."""
    return [
        HistoryMessage(
            role=r["role"], content=r["content"],
            product_ids=json.loads(r["product_ids"] or "[]"), page_path=r["page_path"],
        )
        for r in _recent_rows(user_id, AGENT_CONTEXT_MESSAGES)
    ]


def history_for_ui(user_id: int) -> list[ChatHistoryItem]:
    """Saved messages for the chat box. Product cards are rebuilt from the catalogue, so prices
    and photos are current rather than whatever they were when the message was saved."""
    return [
        ChatHistoryItem(
            role=r["role"],
            content=r["content"],
            results_title=r["results_title"],
            products=tools.product_cards(json.loads(r["product_ids"] or "[]")),
            created_at=r["created_at"],
        )
        for r in _recent_rows(user_id, UI_HISTORY_MESSAGES)
    ]


def clear(user_id: int) -> int:
    with get_db() as conn:
        return conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,)).rowcount
