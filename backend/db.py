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
