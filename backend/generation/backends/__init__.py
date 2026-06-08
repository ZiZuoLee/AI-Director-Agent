"""Generation backends for local inference and remote serving."""

from .base import GenerationBackend
from .zenmux_api import ZenMuxImageBackend

__all__ = [
    "GenerationBackend",
    "ZenMuxImageBackend",
]
