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
from PIL import Image
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
EDGE_IN_PX = 3     # how far inside the outline edge pixels get soft transparency
EDGE_OUT_PX = 2    # how far outside the outline we look for faint fabric
MIN_CONTRAST = 40  # below this fabric/background brightness gap, keep the hard edge
GAP_MIN_ELONGATION = 3.5  # enclosed white sliver this stretched...
GAP_MAX_DISTANCE = 0.125  # ...and this close to the outside background = arm gap, not a logo
PADDING = 0.06     # empty margin around the trimmed garment, as a fraction of its size


def border_connected(mask: np.ndarray) -> np.ndarray:
    """Parts of `mask` that are connected to the image border."""
    labels, _ = ndimage.label(mask)
    border_labels = np.unique(
        np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    )
    return np.isin(labels, border_labels[border_labels > 0])


def background_mask(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hard masks: (background, black background, white background)."""
    lo, hi = rgb.min(axis=2), rgb.max(axis=2)
    strict_black, strict_white = hi <= STRICT_BLACK_MAX, lo >= STRICT_WHITE_MIN

    # Seeds touching the border. Black and white are grown separately into their own looser
    # thresholds, so a white background never lets the "black" rule bite into navy fabric.
    black_bg = border_connected(strict_black)
    # White background either touches the border, or is a big white photo area sitting inside
    # black padding bars. Small white areas next to black (like a white logo letter at the
    # edge of a navy hoodie) are fabric, not background.
    white_parts, n = ndimage.label(strict_white)
    white_bg = border_connected(strict_white)
    if n:
        touching_black = np.unique(white_parts[ndimage.binary_dilation(black_bg, iterations=2) & strict_white])
        sizes = ndimage.sum(strict_white, white_parts, index=np.arange(1, n + 1))
        big = [lab for lab in touching_black if lab > 0 and sizes[lab - 1] >= 0.05 * strict_white.size]
        white_bg |= np.isin(white_parts, big)
    black_bg |= (hi <= LOOSE_BLACK_MAX) & ndimage.binary_dilation(black_bg, iterations=FRINGE_PX)
    white_bg |= (lo >= LOOSE_WHITE_MIN) & ndimage.binary_dilation(white_bg, iterations=FRINGE_PX)

    # Large enclosed pure-black gaps (e.g. between an arm and the body on a black-background
    # photo) are background too.
    enclosed, n = ndimage.label(strict_black & ~(black_bg | white_bg))
    if n and black_bg.any():
        sizes = ndimage.sum(np.ones_like(enclosed), enclosed, index=np.arange(1, n + 1))
        black_bg |= np.isin(enclosed, np.arange(1, n + 1)[sizes >= 0.004 * strict_black.size])

    # Enclosed WHITE areas are usually printed logos, so only remove the ones shaped like the
    # gap between an arm and the body: a long thin sliver lying close to the garment's outline.
    # (Measured on this catalogue: arm gaps are >= 4x longer than wide and within ~11% of the
    # image size from the outside background; logos are compact or sit in the middle.)
    background = black_bg | white_bg
    enclosed, n = ndimage.label(strict_white & ~background)
    if n:
        dist_to_bg = ndimage.distance_transform_edt(~background)
        side = max(strict_white.shape)
        for label, box in enumerate(ndimage.find_objects(enclosed), start=1):
            region = enclosed[box] == label
            if region.sum() < 0.001 * strict_white.size:
                continue
            h, w = region.shape
            elongation = max(h, w) / max(1, min(h, w))
            closeness = dist_to_bg[box][region].min() / side
            if elongation >= GAP_MIN_ELONGATION and closeness <= GAP_MAX_DISTANCE:
                white_bg[box] |= region

    return black_bg | white_bg, black_bg, white_bg


def remove_background(img: Image.Image) -> Image.Image:
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    background, black_bg, white_bg = background_mask(rgb.astype(np.int16))

    # Drop specks and thin lines (e.g. the soft seam where a white photo meets black padding
    # bars), then keep only reasonably large garment pieces.
    fg = ndimage.binary_opening(~background, iterations=2)
    pieces, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(fg, pieces, index=np.arange(1, n + 1))
        fg = np.isin(pieces, np.arange(1, n + 1)[sizes >= 0.01 * sizes.max()])

    # --- Edge matting ---
    # Near the outline, a pixel is a blend of fabric and background. Estimate how much of it is
    # fabric (alpha) by comparing its brightness to the nearest solid fabric pixel and to the
    # background (black = 0, white = 255), then paint it with the solid fabric's color so no
    # black or white halo is left behind.
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    dist_in = ndimage.distance_transform_edt(fg)    # fabric pixel -> nearest background
    dist_out = ndimage.distance_transform_edt(~fg)  # background pixel -> nearest fabric
    band = (fg & (dist_in <= EDGE_IN_PX)) | (~fg & (dist_out <= EDGE_OUT_PX))
    interior = fg & (dist_in > EDGE_IN_PX)
    if not interior.any():
        interior = fg

    # Index of the nearest solid fabric pixel, for every pixel.
    _, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)
    fabric_lum = lum[iy, ix]
    fabric_rgb = rgb[iy, ix]

    # Which background each edge pixel is blending with.
    d_black = ndimage.distance_transform_edt(~black_bg) if black_bg.any() else np.full(lum.shape, np.inf)
    d_white = ndimage.distance_transform_edt(~white_bg) if white_bg.any() else np.full(lum.shape, np.inf)
    bg_lum = np.where(d_black <= d_white, 0.0, 255.0).astype(np.float32)

    contrast = fabric_lum - bg_lum
    with np.errstate(divide="ignore", invalid="ignore"):
        soft = np.clip((lum - bg_lum) / contrast, 0.0, 1.0)
    # If fabric and background are nearly the same brightness (white shirt on white),
    # the estimate is unreliable, so fall back to the hard mask there.
    soft = np.where(np.abs(contrast) < MIN_CONTRAST, fg.astype(np.float32), soft)

    alpha = np.where(band, soft, fg.astype(np.float32))
    alpha = ndimage.gaussian_filter(alpha, 0.6)
    alpha[~band & ~fg] = 0.0

    color = np.where(band[..., None], fabric_rgb, rgb)
    out = np.dstack([color, alpha * 255.0]).clip(0, 255).astype(np.uint8)
    return trim_to_square(Image.fromarray(out, "RGBA"))


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
