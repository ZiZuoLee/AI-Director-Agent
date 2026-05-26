"""Agent Layer - Rule Engine

Defines cinematic rules and mappings used by the shot planner.
"""
from __future__ import annotations

from typing import Dict, List

SHOT_RULES = [
    {
        "match": ["pursuit", "movement"],
        "shot_type": "tracking shot",
        "reason": "Action and motion suggest a dynamic tracking sequence.",
    },
    {
        "match": ["conflict"],
        "shot_type": "wide shot",
        "reason": "Conflict scenes benefit from broader context and environment.",
    },
    {
        "match": ["dialogue"],
        "shot_type": "two-shot",
        "reason": "Conversation between characters is best shown with a two-shot.",
    },
    {
        "match": ["intimacy", "affection", "joy"],
        "shot_type": "close-up",
        "reason": "Emotional detail requires a close-up to capture expression.",
    },
    {
        "match": ["fear", "sadness", "anger"],
        "shot_type": "close-up",
        "reason": "Strong emotion is emphasized through intimate framing.",
    },
    {
        "match": ["transition"],
        "shot_type": "establishing shot",
        "reason": "Location or movement transitions need a clear establishing shot.",
    },
]

DEFAULT_SHOT = {
    "shot_type": "medium shot",
    "reason": "A balanced framing provides visual clarity for general story beats.",
}


def determine_shot_rule(actions: List[str], emotions: List[str]) -> Dict[str, str]:
    combined = set(actions + emotions)
    for rule in SHOT_RULES:
        if any(item in combined for item in rule["match"]):
            return {"shot_type": rule["shot_type"], "reason": rule["reason"]}
    return DEFAULT_SHOT


def determine_camera_movement(actions: List[str]) -> str:
    if "movement" in actions or "pursuit" in actions or "conflict" in actions:
        return "dolly"
    if "dialogue" in actions:
        return "slow push-in"
    return "static"


def build_cinematic_prompt(shot: Dict[str, str], location: str, characters: List[str]) -> str:
    subject = characters[0] if characters else "a figure"
    return (
        f"{shot['shot_type']} of {subject} in a {location} with {shot['reason'].lower()} "
        "cinematic lighting, film grain, high contrast, realistic detail"
    )
