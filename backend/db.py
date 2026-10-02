"""Shared paths and SQLite connection helper."""
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "campus_customs.db"


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit if the block succeeds, and always close it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


PRODUCTS_DIR = DATA_DIR / "products"
# Background-removed cut-outs made by scripts/remove_backgrounds.py (optional).
CUTOUTS_DIR = DATA_DIR / "products_nobg"


def image_url(image_file_path: str) -> str:
    """Point at the transparent cut-out when it exists. It gets its own .webp address, so
    browsers that cached the original .jpg can't keep showing the old black/white background."""
    original = Path(image_file_path).name
    cutout = Path(original).stem + ".webp"
    return "/images/" + (cutout if (CUTOUTS_DIR / cutout).is_file() else original)


CHAT_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    role          TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
    content       TEXT    NOT NULL,
    product_ids   TEXT,             -- JSON list of product_ids shown as cards (assistant only)
    results_title TEXT,             -- heading for those cards
    page_path     TEXT,             -- page the shopper was on, e.g. /products/morse-1-4-zip
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history (user_id, id);
"""


def init_db() -> None:
    """Create tables this app adds to the seed database (safe to run every startup)."""
    with get_db() as conn:
        conn.executescript(CHAT_HISTORY_SCHEMA)
