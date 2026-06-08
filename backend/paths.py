"""Repository root paths used by the backend runtime."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = ROOT / "images"
FRONTEND_DIST = ROOT / "frontend" / "dist"
ENV_FILE = ROOT / ".env"
ZENMUX_ENV_FILE = ROOT / "zenmux.env"
