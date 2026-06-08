"""Prompt generation for the storyboard image pipeline."""
from __future__ import annotations

import re
from typing import Any, Iterable, List, Mapping, Sequence

from .generation_types import GenerationConfig, GenerationError, PromptSpec, ShotContext


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "shot"


def _dedupe_fragments(fragments: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for fragment in fragments:
        normalized = fragment.strip(" ,")
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(normalized)
    return result


def _extract_subject_hint(description: str) -> str:
    subject_markers = ("主体为", "主角为", "角色为")
    for marker in subject_markers:
        if marker in description:
            _, remainder = description.split(marker, 1)
            return remainder.split("，", 1)[0].split(",", 1)[0].strip()
    return ""


def build_prompt_spec(
    shot: Mapping[str, Any] | ShotContext,
    config: GenerationConfig | Mapping[str, Any] | None = None,
) -> PromptSpec:
    """Convert one planner shot into a backend-neutral generation spec."""

    generation_config = (
        config
        if isinstance(config, GenerationConfig)
        else GenerationConfig.from_mapping(config)
    )
    shot_context = shot if isinstance(shot, ShotContext) else ShotContext.from_mapping(shot)
    subject_hint = _extract_subject_hint(shot_context.description)

    # Keep the final prompt Chinese-first for models like Doubao Seedream.
    # Avoid appending English metadata that dilutes the LLM-crafted visual description.
    fragments = _dedupe_fragments(
        [
            shot_context.prompt,
            f"景别：{shot_context.shot_type}",
            f"运镜：{shot_context.camera_movement}",
            generation_config.prompt_suffix,
        ]
    )
    positive_prompt = "，".join(fragments)

    output_basename = (
        f"shot_{shot_context.shot_id:02d}_{_slugify(shot_context.shot_type)}."
        f"{generation_config.image_format}"
    )
    seed = generation_config.seed + (shot_context.shot_id - 1) * generation_config.seed_stride

    return PromptSpec(
        shot_id=shot_context.shot_id,
        positive_prompt=positive_prompt,
        negative_prompt=generation_config.negative_prompt,
        width=generation_config.width,
        height=generation_config.height,
        steps=generation_config.steps,
        guidance_scale=generation_config.guidance_scale,
        seed=seed,
        output_name=output_basename,
        style_preset=generation_config.style_preset,
        metadata={
            "description": shot_context.description,
            "shot_type": shot_context.shot_type,
            "camera_movement": shot_context.camera_movement,
            "reason": shot_context.reason,
            "source_prompt": shot_context.prompt,
            "raw_prompt": shot_context.raw_prompt,
            "subject_hint": subject_hint,
            **shot_context.metadata,
        },
    )


def build_prompt_specs(
    shots: Sequence[Mapping[str, Any] | ShotContext],
    config: GenerationConfig | Mapping[str, Any] | None = None,
) -> List[PromptSpec]:
    if not shots:
        raise GenerationError("At least one shot is required to build prompt specs.")
    return [build_prompt_spec(shot, config=config) for shot in shots]
