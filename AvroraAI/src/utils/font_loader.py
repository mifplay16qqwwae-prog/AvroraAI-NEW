import os
from pathlib import Path
from typing import Optional
from PIL import ImageFont


CANDIDATE_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/GoogleSans-Regular.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/seguisb.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def get_cyrillic_font(size: int, custom_font_dir: Optional[Path] = None) -> ImageFont.FreeTypeFont:
    """Loads a TTF font with Cyrillic support."""
    if custom_font_dir and custom_font_dir.exists():
        for ext in ("*.ttf", "*.otf"):
            found = list(custom_font_dir.glob(ext))
            if found:
                return ImageFont.truetype(str(found[0]), size=size)

    for path_str in CANDIDATE_FONTS:
        if os.path.exists(path_str):
            try:
                return ImageFont.truetype(path_str, size=size)
            except Exception:
                continue

    return ImageFont.load_default()
