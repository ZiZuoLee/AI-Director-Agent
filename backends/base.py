"""Common backend interface for image generation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List

from generation_types import GeneratedImage, GenerationConfig, PromptSpec


class GenerationBackend(ABC):
    """Stable interface implemented by every generation backend."""

    backend_name: str

    def __init__(self, config: GenerationConfig):
        self.config = config

    @abstractmethod
    def generate(self, prompt_specs: Iterable[PromptSpec]) -> List[GeneratedImage]:
        """Generate images for a batch of prompts."""
