"""Remove the solid black / white backgrounds from product photos.

Reads data/products/*.jpg (left untouched) and writes transparent, trimmed, square WebP images to
data/products_nobg/. The backend serves those cut-outs when they exist.

How it works: the product photos sit on pure black and/or white backgrounds (some have black
bars padded around a white photo). Pixels that are near-black or near-white AND connected to
the image border are treated as background; everything else is the garment. Dark garments
such as navy survive because they are not pure black.

Usage (needs pillow, numpy, scipy):
    python backend/scripts/remove_backgrounds.py            # all products
    python backend/scripts/remove_backgrounds.py name.jpg   # just some files
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "products"
DST = ROOT / "data" / "products_nobg"

# Backgrounds are exactly 0 or 255, while navy shadows and white fabric sit a little off those
# values. So the background is grown from strict seeds, and the looser thresholds are only
# allowed in a thin band next to it (to clean up JPEG fringe without eating into the garment).
STRICT_BLACK_MAX = 8
STRICT_WHITE_MIN = 250
LOOSE_BLACK_MAX = 30
LOOSE_WHITE_MIN = 236
FRINGE_PX = 3
PADDING = 0.06   # empty margin around the trimmed garment, as a fraction of its size


def border_connected(mask: np.ndarray) -> np.ndarray:
    """Parts of `mask` that are connected to the image border."""
    labels, _ = ndimage.label(mask)
    border_labels = np.unique(
        np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    )
    return np.isin(labels, border_labels[border_labels > 0])


def remove_background(img: Image.Image) -> Image.Image:
    rgb = np.asarray(img.convert("RGB")).astype(np.int16)
    lo, hi = rgb.min(axis=2), rgb.max(axis=2)

    strict = (hi <= STRICT_BLACK_MAX) | (lo >= STRICT_WHITE_MIN)
    loose = (hi <= LOOSE_BLACK_MAX) | (lo >= LOOSE_WHITE_MIN)
    candidate = strict

    # Keep only regions that touch the border (so white logos inside a shirt stay).
    background = border_connected(strict)
    background |= loose & ndimage.binary_dilation(background, iterations=FRINGE_PX)

    # Large enclosed gaps (e.g. between an arm and the body) are background too.
    enclosed, n = ndimage.label(candidate & ~background)
    if n:
        sizes = ndimage.sum(np.ones_like(enclosed), enclosed, index=np.arange(1, n + 1))
        min_hole = 0.004 * candidate.size
        big = np.arange(1, n + 1)[sizes >= min_hole]
        background |= np.isin(enclosed, big)

    # Drop specks: keep only reasonably large garment pieces.
    fg = ~background
    fg = ndimage.binary_opening(fg, iterations=1)
    pieces, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(fg, pieces, index=np.arange(1, n + 1))
        keep = np.arange(1, n + 1)[sizes >= 0.01 * sizes.max()]
        fg = np.isin(pieces, keep)

    # Soft anti-aliased edge: shrink by one pixel, then feather.
    alpha = Image.fromarray((ndimage.binary_erosion(fg, iterations=1) * 255).astype(np.uint8))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))

    out = img.convert("RGBA")
    out.putalpha(alpha)
    return trim_to_square(out)


def trim_to_square(img: Image.Image) -> Image.Image:
    """Crop to the garment and center it on a transparent square canvas."""
    bbox = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    side = int(max(w, h) * (1 + 2 * PADDING))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def main(names: list[str]) -> None:
    DST.mkdir(exist_ok=True)
    files = [SRC / n for n in names] if names else sorted(SRC.glob("*.jpg"))
    for path in files:
        out = remove_background(Image.open(path))
        out.save(DST / (path.stem + ".webp"), quality=88, method=6)
        print(f"ok  {path.name}")
    print(f"Done: {len(files)} images -> {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
