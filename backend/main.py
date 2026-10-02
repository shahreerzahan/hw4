"""Campus Customs API: serves products, product images, accounts, and the chat agent."""
import json
import logging
import sqlite3
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic_ai.exceptions import AgentRunError, ModelAPIError

import agent
import auth
import chat_history
import tools
from db import CUTOUTS_DIR, PRODUCTS_DIR, get_db, image_url, init_db
from models import ChatHistoryItem, ChatReply, ChatRequest, CustomerInfo

log = logging.getLogger("campus_customs")

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

init_db()  # creates the chat_history table if it doesn't exist yet

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


def product_from_row(row: sqlite3.Row, badges: dict[str, str] | None = None) -> dict:
    """Turn a catalogue row into JSON-friendly data for the front end."""
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": tools.category_for(row["garment_type"]),
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
        "badge": (badges or {}).get(row["product_id"]),
    }



@app.get("/images/{filename}")
def product_image(filename: str) -> FileResponse:
    """Serve a cut-out (.webp) or an original photo (.jpg) by file name."""
    name = Path(filename).name  # blocks paths like ../../.env
    folder = CUTOUTS_DIR if name.endswith(".webp") else PRODUCTS_DIR
    path = folder / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    badges = tools.product_badges()
    return [product_from_row(r, badges) for r in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    product = product_from_row(row, tools.product_badges())
    sizes = [{"size": s["size"], "quantity": s["quantity"]} for s in stock]
    sizes.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)
    product["sizes"] = sizes
    return product


def current_customer(cc_session: str | None) -> CustomerInfo | None:
    """The logged-in shopper from the session cookie, or None for guests."""
    user_id = auth.current_user_id(cc_session)
    if user_id is None:
        return None
    u = auth.public_user(auth.get_user(user_id))
    return CustomerInfo(user_id=u["id"], first_name=u["first_name"], last_name=u["last_name"], email=u["email"])


@app.post("/api/chat")
async def chat(body: ChatRequest, cc_session: str | None = Cookie(default=None)) -> ChatReply:
    """The website's chat box posts each message here; Dan (the PydanticAI agent) replies.

    Logged in: memory comes from the chat_history table and the turn is saved there.
    Guest: memory is the recent messages the chat box sends back; nothing is saved."""
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please type a message.")

    customer = current_customer(cc_session)
    deps = agent.ChatDeps(customer=customer, page=tools.describe_page(body.page_path))
    history = chat_history.recent_for_agent(customer.user_id) if customer else body.history

    try:
        result = await agent.chat(message, deps, history)
    except (ModelAPIError, AgentRunError) as e:
        log.warning("Chat agent failed: %s: %s", type(e).__name__, e)
        raise HTTPException(
            status_code=503,
            detail="Dan is taking a quick nap and can't chat right now. Please try again in a moment.",
        )

    if customer and result.remember:
        chat_history.save_turn(
            customer.user_id, message, result.reply.reply,
            [p.product_id for p in result.reply.products], result.reply.results_title, deps.page.path,
        )
    return result.reply


@app.get("/api/chat/history")
def get_chat_history(cc_session: str | None = Cookie(default=None)) -> list[ChatHistoryItem]:
    """A logged-in shopper's saved chat, oldest first. Guests get an empty list."""
    customer = current_customer(cc_session)
    return chat_history.history_for_ui(customer.user_id) if customer else []


@app.delete("/api/chat/history")
def delete_chat_history(cc_session: str | None = Cookie(default=None)) -> dict:
    customer = current_customer(cc_session)
    if customer is None:
        raise HTTPException(status_code=401, detail="Log in to manage your chat history.")
    return {"deleted": chat_history.clear(customer.user_id)}
