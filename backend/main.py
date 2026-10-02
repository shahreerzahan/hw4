"""Campus Customs API: serves products, product images, accounts, and the chat agent."""
import json
import logging
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic_ai.exceptions import AgentRunError, ModelAPIError

import agent
import auth
from db import DATA_DIR, get_db
from models import ChatReply, ChatRequest

log = logging.getLogger("campus_customs")

PRODUCTS_DIR = DATA_DIR / "products"
# Background-removed cut-outs made by scripts/remove_backgrounds.py (optional).
CUTOUTS_DIR = DATA_DIR / "products_nobg"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


def product_from_row(row: sqlite3.Row) -> dict:
    """Turn a catalogue row into JSON-friendly data for the front end."""
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
    }


def image_url(image_file_path: str) -> str:
    """Point at the transparent cut-out when it exists. It gets its own .webp address, so
    browsers that cached the original .jpg can't keep showing the old black/white background."""
    original = Path(image_file_path).name
    cutout = Path(original).stem + ".webp"
    return "/images/" + (cutout if (CUTOUTS_DIR / cutout).is_file() else original)


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
    return [product_from_row(r) for r in rows]


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

    product = product_from_row(row)
    sizes = [{"size": s["size"], "quantity": s["quantity"]} for s in stock]
    sizes.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)
    product["sizes"] = sizes
    return product


@app.post("/api/chat")
async def chat(body: ChatRequest) -> ChatReply:
    """The website's chat box posts each message here; Dan (the PydanticAI agent) replies."""
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please type a message.")
    try:
        return await agent.chat(message)
    except (ModelAPIError, AgentRunError) as e:
        log.warning("Chat agent failed: %s: %s", type(e).__name__, e)
        raise HTTPException(
            status_code=503,
            detail="Dan is taking a quick nap and can't chat right now. Please try again in a moment.",
        )
