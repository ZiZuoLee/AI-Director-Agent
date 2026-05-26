"""Agent Layer - Script Parser

This module provides a lightweight parser for story text input and extracts
structured information to support shot planning.
"""
from __future__ import annotations

import re
from typing import Dict, List

EMOTION_KEYWORDS = {
    "happy": "joy",
    "sad": "sadness",
    "sadness": "sadness",
    "angry": "anger",
    "angry": "anger",
    "scared": "fear",
    "terrified": "fear",
    "fear": "fear",
    "furious": "anger",
    "cry": "sadness",
    "crying": "sadness",
    "laugh": "joy",
    "laughs": "joy",
    "love": "affection",
    "hate": "anger",
    "intense": "intensity",
}

ACTION_KEYWORDS = {
    "run": "movement",
    "runs": "movement",
    "chase": "pursuit",
    "chased": "pursuit",
    "fight": "conflict",
    "shoot": "conflict",
    "walk": "movement",
    "look": "observation",
    "looks": "observation",
    "talk": "dialogue",
    "talks": "dialogue",
    "scream": "intensity",
    "screams": "intensity",
    "whisper": "intimacy",
    "enters": "transition",
    "leave": "transition",
    "leaves": "transition",
    "fall": "action",
    "falls": "action",
    "jump": "action",
    "turn": "transition",
    "turns": "transition",
    "pursue": "pursuit",
    "pursues": "pursuit",
}

LOCATION_KEYWORDS = [
    "street",
    "room",
    "forest",
    "city",
    "house",
    "office",
    "warehouse",
    "stage",
    "landscape",
    "night",
    "day",
]

CHARACTER_WORDS = [
    "he",
    "she",
    "they",
    "hero",
    "villain",
    "king",
    "queen",
    "soldier",
    "child",
    "woman",
    "man",
]


def split_sentences(text: str) -> List[str]:
    text = text.replace("\n", " ")
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def extract_keywords(text: str, keywords: Dict[str, str]) -> List[str]:
    found: List[str] = []
    lower = text.lower()
    for word, tag in keywords.items():
        if re.search(rf"\b{re.escape(word)}\b", lower):
            found.append(tag)
    return sorted(set(found))


def extract_locations(text: str) -> List[str]:
    lower = text.lower()
    return [loc for loc in LOCATION_KEYWORDS if re.search(rf"\b{re.escape(loc)}\b", lower)]


def extract_characters(text: str) -> List[str]:
    lower = text.lower()
    return [word for word in CHARACTER_WORDS if re.search(rf"\b{re.escape(word)}\b", lower)]


def parse_script(text: str) -> Dict[str, object]:
    """Parse user story text into a structured semantic dictionary."""
    sentences = split_sentences(text)
    full_text = " ".join(sentences)
    actions = extract_keywords(full_text, ACTION_KEYWORDS)
    emotions = extract_keywords(full_text, EMOTION_KEYWORDS)
    locations = extract_locations(full_text)
    characters = extract_characters(full_text)

    if not locations:
        locations = ["interior"]
    if not characters:
        characters = ["protagonist"]

    themes = []
    if "pursuit" in actions or "conflict" in actions:
        themes.append("tension")
    if "joy" in emotions or "affection" in emotions:
        themes.append("warmth")
    if "sadness" in emotions or "fear" in emotions:
        themes.append("dramatic")

    return {
        "raw_text": text,
        "sentences": sentences,
        "actions": actions,
        "emotions": emotions,
        "locations": locations,
        "characters": characters,
        "themes": sorted(set(themes)),
    }


def parse_scene(text: str) -> Dict[str, object]:
    """Alias for parse_script, emphasizing shot planning input."""
    return parse_script(text)
