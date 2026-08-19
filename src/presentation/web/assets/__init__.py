"""
Static assets for the web application.
Includes CSS, images, and fonts.
"""
from pathlib import Path

ASSETS_DIR = Path(__file__).parent
CSS_DIR = ASSETS_DIR / "css"
IMAGES_DIR = ASSETS_DIR / "images"
FONTS_DIR = ASSETS_DIR / "fonts"

__all__ = [
    "ASSETS_DIR",
    "CSS_DIR",
    "IMAGES_DIR",
    "FONTS_DIR",
]