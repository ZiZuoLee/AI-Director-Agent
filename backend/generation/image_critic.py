"""Heuristic critic for ranking storyboard image candidates."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping

from .director_memory import CharacterMemory, DirectorMemory, SceneMemory
from .generation_types import GeneratedImage, ShotContext
from .vision_analyzer import VisionAnalysis


@dataclass
class CriticScore:
    total: float
    dimensions: Dict[str, float]
    rationale: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _contains_any(text: str, values: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(value.lower() in lowered for value in values if value)


def score_candidate(
    shot: ShotContext,
    candidate: Mapping[str, Any],
    memory: DirectorMemory,
    vision: VisionAnalysis | None = None,
) -> CriticScore:
    metadata = candidate.get("metadata", {})
    prompt = str(candidate.get("prompt", ""))
    score_map: Dict[str, float] = {}
    rationale: List[str] = []

    binding = memory.shot_bindings[shot.shot_id]
    character_memories: List[CharacterMemory] = [memory.characters[item] for item in binding.character_ids]
    scene_memories: List[SceneMemory] = [memory.scenes[item] for item in binding.scene_ids]

    has_reference = bool(metadata.get("reference_image_path"))
    api_mode = metadata.get("api_mode")
    if has_reference and api_mode == "edit_image":
        score_map["continuity_strategy"] = 1.0
        rationale.append("Used edit_image with a reference frame for continuity.")
    elif len(character_memories) == 1 and len(character_memories[0].source_shots) > 1:
        score_map["continuity_strategy"] = 0.4
        rationale.append("Repeated character exists but candidate did not use an edit reference.")
    else:
        score_map["continuity_strategy"] = 0.6
        rationale.append("Standalone generation is acceptable for a new character/scene.")

    character_terms = [memory_item.display_name for memory_item in character_memories]
    character_terms.extend(term for memory_item in character_memories for term in memory_item.features[:4])
    score_map["character_anchor"] = 1.0 if _contains_any(prompt, character_terms) else 0.2
    if score_map["character_anchor"] >= 1.0:
        rationale.append("Prompt preserves explicit character anchors from memory.")
    else:
        rationale.append("Prompt is weak on character anchors from memory.")

    scene_terms = [memory_item.display_name for memory_item in scene_memories]
    scene_terms.extend(term for memory_item in scene_memories for term in memory_item.features[:4])
    score_map["scene_anchor"] = 1.0 if _contains_any(prompt, scene_terms) else 0.3
    if score_map["scene_anchor"] >= 1.0:
        rationale.append("Prompt preserves explicit scene anchors from memory.")
    else:
        rationale.append("Prompt is weak on scene anchors from memory.")

    shot_terms = [shot.shot_type, shot.camera_movement]
    score_map["shot_language"] = 1.0 if _contains_any(prompt, shot_terms) else 0.4
    if score_map["shot_language"] >= 1.0:
        rationale.append("Prompt explicitly encodes shot type or camera movement.")
    else:
        rationale.append("Prompt needs stronger shot-language cues.")

    model_feedback = str(metadata.get("model_text") or "")
    score_map["model_feedback"] = 0.7 if model_feedback else 0.5
    if model_feedback:
        rationale.append("Model returned text feedback alongside the generated image.")

    if metadata.get("strategy") == "edit_reference":
        score_map["strategy_confidence"] = 1.0
    elif metadata.get("strategy") == "continuity_anchor":
        score_map["strategy_confidence"] = 0.8
    else:
        score_map["strategy_confidence"] = 0.6

    if vision is not None:
        score_map["vision_character_consistency"] = vision.character_consistency
        score_map["vision_scene_consistency"] = vision.scene_consistency
        score_map["vision_shot_match"] = vision.shot_match
        score_map["vision_emotion_match"] = vision.emotion_match
        score_map["vision_visual_quality"] = vision.visual_quality
        rationale.extend(vision.rationale)

    total = sum(score_map.values()) / len(score_map)
    return CriticScore(total=total, dimensions=score_map, rationale=rationale)
