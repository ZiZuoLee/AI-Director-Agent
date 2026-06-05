"""ZenMux image generation backend using generate/edit image APIs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

from generation_types import GeneratedImage, GenerationConfig, GenerationError, PromptSpec

from .base import GenerationBackend

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None
    types = None


class ZenMuxImageBackend(GenerationBackend):
    """Generate and edit images via ZenMux's google-genai-compatible API."""

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

    def _seed_for_spec(self, spec: PromptSpec, seed_override: Optional[int] = None) -> int:
        if seed_override is not None:
            return seed_override
        if self.config.zenmux_seed is not None:
            return self.config.zenmux_seed
        return spec.seed

    def _generate_config(self, spec: PromptSpec, *, seed_override: Optional[int] = None):
        if types is None:
            raise GenerationError("The ZenMux backend requires google-genai to be installed.")

        kwargs = {
            "number_of_images": 1,
            "aspect_ratio": self._infer_aspect_ratio(spec),
            "image_size": self.config.zenmux_image_size,
            "output_mime_type": self.config.zenmux_output_mime_type,
            "seed": self._seed_for_spec(spec, seed_override=seed_override),
            "enhance_prompt": self.config.zenmux_enhance_prompt,
        }
        if spec.negative_prompt.strip():
            kwargs["negative_prompt"] = spec.negative_prompt
        if self.config.guidance_scale > 0:
            kwargs["guidance_scale"] = self.config.guidance_scale
        if self.config.zenmux_output_compression_quality is not None:
            kwargs["output_compression_quality"] = self.config.zenmux_output_compression_quality
        if self.config.zenmux_person_generation is not None:
            kwargs["person_generation"] = self.config.zenmux_person_generation

        return types.GenerateImagesConfig(**kwargs)

    def _edit_config(self, spec: PromptSpec, *, seed_override: Optional[int] = None):
        if types is None:
            raise GenerationError("The ZenMux backend requires google-genai to be installed.")

        kwargs = {
            "number_of_images": 1,
            "output_mime_type": self.config.zenmux_output_mime_type,
            "seed": self._seed_for_spec(spec, seed_override=seed_override),
            "enhance_prompt": self.config.zenmux_enhance_prompt,
        }
        if self.config.zenmux_output_compression_quality is not None:
            kwargs["output_compression_quality"] = self.config.zenmux_output_compression_quality
        if self.config.zenmux_person_generation is not None:
            kwargs["person_generation"] = self.config.zenmux_person_generation
        return types.EditImageConfig(**kwargs)

    def _save_image_and_collect_metadata(self, generated_image, output_path: Path) -> dict:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        generated_image.image.save(output_path)
        return {
            "rai_reason": getattr(generated_image, "rai_reason", None),
            "safety_attributes": repr(getattr(generated_image, "safety_attributes", None)),
        }

    def _build_result(
        self,
        spec: PromptSpec,
        *,
        output_path: Path,
        metadata: dict,
        seed_value: int,
    ) -> GeneratedImage:
        return GeneratedImage(
            shot_id=spec.shot_id,
            prompt=spec.positive_prompt,
            negative_prompt=spec.negative_prompt,
            image_path=str(output_path),
            seed=seed_value,
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
                "zenmux_seed": seed_value,
                **metadata,
                **spec.metadata,
            },
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

    def generate_one(self, spec: PromptSpec, *, seed_override: Optional[int] = None) -> GeneratedImage:
        client = self._client()
        response = client.models.generate_images(
            model=self.config.model_id,
            prompt=self._request_prompt(spec),
            config=self._generate_config(spec, seed_override=seed_override),
        )
        generated_images = getattr(response, "generated_images", None)
        if not generated_images:
            raise GenerationError(f"ZenMux did not return generated images for shot {spec.shot_id}.")

        output_path = spec.output_path(self.config.output_dir)
        image_metadata = self._save_image_and_collect_metadata(generated_images[0], output_path)
        image_metadata["api_mode"] = "generate_images"
        image_metadata["usage"] = repr(getattr(response, "usage_metadata", None))
        return self._build_result(
            spec,
            output_path=output_path,
            metadata=image_metadata,
            seed_value=self._seed_for_spec(spec, seed_override=seed_override),
        )

    def edit_one(
        self,
        spec: PromptSpec,
        *,
        reference_image_path: str,
        seed_override: Optional[int] = None,
    ) -> GeneratedImage:
        if types is None:
            raise GenerationError("The ZenMux backend requires google-genai to be installed.")
        client = self._client()
        reference_image = types.Image.from_file(location=reference_image_path)
        response = client.models.edit_image(
            model=self.config.edit_model_id or self.config.model_id,
            prompt=self._request_prompt(spec),
            reference_images=[
                types.RawReferenceImage(
                    reference_id=1,
                    reference_image=reference_image,
                )
            ],
            config=self._edit_config(spec, seed_override=seed_override),
        )
        generated_images = getattr(response, "generated_images", None)
        if not generated_images:
            raise GenerationError(f"ZenMux did not return edited images for shot {spec.shot_id}.")

        output_path = spec.output_path(self.config.output_dir)
        image_metadata = self._save_image_and_collect_metadata(generated_images[0], output_path)
        image_metadata["api_mode"] = "edit_image"
        image_metadata["reference_image_path"] = reference_image_path
        image_metadata["usage"] = repr(getattr(response, "usage_metadata", None))
        return self._build_result(
            spec,
            output_path=output_path,
            metadata=image_metadata,
            seed_value=self._seed_for_spec(spec, seed_override=seed_override),
        )

    def generate(self, prompt_specs: Iterable[PromptSpec]) -> List[GeneratedImage]:
        specs = list(prompt_specs)
        if not specs:
            return []

        return [self.generate_one(spec) for spec in specs]
