"""ZenMux image generation backend using the Vertex AI image-generation API."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

from generation_types import GeneratedImage, GenerationConfig, GenerationError, PromptSpec

from .base import GenerationBackend

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None
    types = None


class ZenMuxImageBackend(GenerationBackend):
    """Generate images by calling ZenMux's Vertex AI-compatible image API."""

    backend_name = "zenmux_api"

    def _load_env_file(self) -> None:
        env_path = self.config.zenmux_env_path
        if env_path is None or not env_path.exists():
            return
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

    def _api_key(self) -> str:
        self._load_env_file()
        api_key = self.config.zenmux_api_key or os.getenv("ZENMUX_API_KEY")
        if not api_key:
            raise GenerationError(
                "ZENMUX_API_KEY is not configured. Set it in the environment or zenmux.env."
            )
        return api_key

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key()}",
            "Content-Type": "application/json",
        }

    def _infer_aspect_ratio(self, spec: PromptSpec) -> str:
        if self.config.zenmux_aspect_ratio:
            return self.config.zenmux_aspect_ratio
        width = spec.width
        height = spec.height
        if width == height:
            return "1:1"
        if width * 9 == height * 16:
            return "16:9"
        if width * 16 == height * 9:
            return "9:16"
        if width > height:
            return "16:9"
        return "9:16"

    def _request_prompt(self, spec: PromptSpec) -> str:
        prompt_text = spec.positive_prompt
        if spec.negative_prompt.strip():
            prompt_text += "\n\nAvoid: " + spec.negative_prompt.strip()
        return prompt_text

    def _generate_config(self, spec: PromptSpec):
        if types is None:
            raise GenerationError("The ZenMux backend requires google-genai to be installed.")

        image_config = {
            "aspect_ratio": self._infer_aspect_ratio(spec),
            "image_size": self.config.zenmux_image_size,
            "output_mime_type": self.config.zenmux_output_mime_type,
        }
        if self.config.zenmux_output_compression_quality is not None:
            image_config["output_compression_quality"] = (
                self.config.zenmux_output_compression_quality
            )

        return types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            seed=self.config.zenmux_seed if self.config.zenmux_seed is not None else spec.seed,
            image_config=types.ImageConfig(**image_config),
        )

    def _client(self):
        if genai is None or types is None:
            raise GenerationError("The ZenMux backend requires google-genai to be installed.")
        return genai.Client(
            api_key=self._api_key(),
            vertexai=True,
            http_options=types.HttpOptions(
                api_version="v1",
                base_url=self.config.zenmux_base_url.rstrip("/"),
            ),
        )

    def generate(self, prompt_specs: Iterable[PromptSpec]) -> List[GeneratedImage]:
        specs = list(prompt_specs)
        if not specs:
            return []

        results: List[GeneratedImage] = []
        client = self._client()

        for spec in specs:
            response = client.models.generate_content(
                model=self.config.model_id,
                contents=[self._request_prompt(spec)],
                config=self._generate_config(spec),
            )

            parts = getattr(response, "parts", None)
            if not parts:
                raise GenerationError(
                    f"ZenMux did not return any content parts for shot {spec.shot_id}."
                )

            output_path = spec.output_path(self.config.output_dir)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            model_text_parts = []
            image_saved = False

            for part in parts:
                if getattr(part, "text", None):
                    model_text_parts.append(part.text)
                if getattr(part, "inline_data", None) is not None:
                    image = part.as_image()
                    image.save(output_path)
                    image_saved = True

            if not image_saved:
                raise GenerationError(
                    f"ZenMux did not return image bytes for shot {spec.shot_id}."
                )

            results.append(
                GeneratedImage(
                    shot_id=spec.shot_id,
                    prompt=spec.positive_prompt,
                    negative_prompt=spec.negative_prompt,
                    image_path=str(output_path),
                    seed=self.config.zenmux_seed if self.config.zenmux_seed is not None else spec.seed,
                    steps=spec.steps,
                    guidance_scale=spec.guidance_scale,
                    backend=self.backend_name,
                    model_id=self.config.model_id,
                    width=spec.width,
                    height=spec.height,
                    metadata={
                        "style_preset": spec.style_preset,
                        "zenmux_request_model": self.config.model_id,
                        "zenmux_image_size": self.config.zenmux_image_size,
                        "zenmux_aspect_ratio": self._infer_aspect_ratio(spec),
                        "zenmux_output_mime_type": self.config.zenmux_output_mime_type,
                        "zenmux_seed": self.config.zenmux_seed if self.config.zenmux_seed is not None else spec.seed,
                        "model_text": "\n".join(model_text_parts).strip() or None,
                        "usage": repr(getattr(response, "usage_metadata", None)),
                        **spec.metadata,
                    },
                )
            )

        return results
