"""Agent Layer - Script Parser

This module provides a lightweight parser for story text input and extracts
structured information to support shot planning.
"""
from __future__ import annotations

import re
from typing import Dict, List

EMOTION_KEYWORDS = {
    "快乐": "joy",
    "高兴": "joy",
    "悲伤": "sadness",
    "伤心": "sadness",
    "愤怒": "anger",
    "生气": "anger",
    "害怕": "fear",
    "恐惧": "fear",
    "恐慌": "fear",
    "哭": "sadness",
    "笑": "joy",
    "爱": "affection",
    "恨": "anger",
    "激动": "intensity",
}

ACTION_KEYWORDS = {
    "跑": "movement",
    "追": "pursuit",
    "追逐": "pursuit",
    "战斗": "conflict",
    "打斗": "conflict",
    "开枪": "conflict",
    "走": "movement",
    "看": "observation",
    "观察": "observation",
    "说": "dialogue",
    "对话": "dialogue",
    "喊": "intensity",
    "哭": "sadness",
    "笑": "joy",
    "耳语": "intimacy",
    "进入": "transition",
    "离开": "transition",
    "转身": "transition",
    "摔": "action",
    "跳": "action",
    "冲": "movement",
}

LOCATION_KEYWORDS = [
    "街道",
    "小巷",
    "森林",
    "城市",
    "房间",
    "办公室",
    "仓库",
    "舞台",
    "夜晚",
    "白天",
    "海滩",
    "公园",
    "屋内",
    "屋外",
]

CHARACTER_WORDS = [
    "他",
    "她",
    "他们",
    "主人公",
    "反派",
    "英雄",
    "孩子",
    "女孩",
    "男孩",
    "女人",
    "男人",
]


def split_sentences(text: str) -> List[str]:
    text = text.replace("\n", " ")
    sentences = re.split(r"(?<=[.!?。！？])\s*", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def contains_keyword(text: str, word: str) -> bool:
    if re.search(r"[\u4e00-\u9fff]", word):
        return word in text
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def extract_keywords(text: str, keywords: Dict[str, str]) -> List[str]:
    found: List[str] = []
    lower = text.lower()
    for word, tag in keywords.items():
        if contains_keyword(lower, word.lower()):
            found.append(tag)
    return sorted(set(found))


def extract_locations(text: str) -> List[str]:
    lower = text.lower()
    return [loc for loc in LOCATION_KEYWORDS if loc in lower]


def extract_characters(text: str) -> List[str]:
    lower = text.lower()
    return [word for word in CHARACTER_WORDS if word in lower]


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
