"""Campus Customs API: serves products, product images, and accounts from the SQLite database."""
import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import auth
from db import DATA_DIR, get_db

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
        "image_url": "/images/" + Path(row["image_file_path"]).name,
    }


@app.get("/images/{filename}")
def product_image(filename: str) -> FileResponse:
    """Serve the transparent cut-out if there is one, otherwise the original photo."""
    name = Path(filename).name  # blocks paths like ../../.env
    cutout = CUTOUTS_DIR / (Path(name).stem + ".webp")
    original = PRODUCTS_DIR / name
    for path in (cutout, original):
        if path.is_file():
            return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})
    raise HTTPException(status_code=404, detail="Image not found")


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
