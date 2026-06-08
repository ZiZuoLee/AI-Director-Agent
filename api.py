"""Root entry point for `uvicorn api:app` (kept for backward-compatible startup)."""
from backend.api import app

__all__ = ["app"]
