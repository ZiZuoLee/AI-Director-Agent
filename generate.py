"""Public entry point for the generation layer."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from backends import ZenMuxImageBackend
from director_agent import DirectorAgent
from generation_types import GeneratedImage, GenerationConfig, GenerationError, PromptSpec, ShotContext
from prompt_gen import build_prompt_specs

SUPPORTED_BACKENDS = {
    "zenmux_api": ZenMuxImageBackend,
}


def _normalize_config(config: GenerationConfig | Mapping[str, Any] | None) -> GenerationConfig:
    if isinstance(config, GenerationConfig):
        return config
    return GenerationConfig.from_mapping(config)


def _build_backend(config: GenerationConfig):
    backend_class = SUPPORTED_BACKENDS.get(config.backend)
    if backend_class is None:
        valid = ", ".join(sorted(SUPPORTED_BACKENDS))
        raise GenerationError(f"Unsupported backend '{config.backend}'. Expected one of: {valid}.")
    return backend_class(config)


def build_generation_plan(
    shots: Sequence[Mapping[str, Any] | ShotContext],
    config: GenerationConfig | Mapping[str, Any] | None = None,
) -> List[PromptSpec]:
    """Create prompt specs without executing the backend."""

    generation_config = _normalize_config(config)
    return build_prompt_specs(shots, config=generation_config)


def generate_images(
    shots: Sequence[Mapping[str, Any] | ShotContext],
    config: GenerationConfig | Mapping[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Generate images for planner shots and return JSON-serializable metadata."""

    generation_config = _normalize_config(config)
    prompt_specs = build_prompt_specs(shots, config=generation_config)
    backend = _build_backend(generation_config)
    generated_images: List[GeneratedImage] = backend.generate(prompt_specs)
    return [image.to_dict() for image in generated_images]


def generate_from_plan(
    prompt_specs: Sequence[PromptSpec],
    config: GenerationConfig | Mapping[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Execute an already-built prompt plan."""

    generation_config = _normalize_config(config)
    backend = _build_backend(generation_config)
    generated_images = backend.generate(prompt_specs)
    return [image.to_dict() for image in generated_images]


def generate_images_agentic(
    shots: Sequence[Mapping[str, Any] | ShotContext],
    config: GenerationConfig | Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Run the full director-agent loop with memory, ranking, retries, and reflections."""

    generation_config = _normalize_config(config)
    agent = DirectorAgent(generation_config)
    return agent.run(shots)
