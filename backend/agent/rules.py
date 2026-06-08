"""Agent Layer - Rule Engine

Defines cinematic rules and mappings used by the shot planner.
"""
from __future__ import annotations

from typing import Dict, List

SHOT_RULES = [
    {
        "match": ["pursuit", "movement"],
        "shot_type": "追踪镜头",
        "reason": "动作与运动暗示需要动态追踪镜头。",
    },
    {
        "match": ["conflict"],
        "shot_type": "远景",
        "reason": "冲突场景需要更广阔的环境来展示张力。",
    },
    {
        "match": ["dialogue"],
        "shot_type": "双人镜",
        "reason": "角色对话适合双人镜头表现交流。",
    },
    {
        "match": ["intimacy", "affection", "joy"],
        "shot_type": "特写",
        "reason": "情感细节适合通过特写表现面部表情。",
    },
    {
        "match": ["fear", "sadness", "anger"],
        "shot_type": "特写",
        "reason": "强烈情绪需要亲密构图来放大情感。",
    },
    {
        "match": ["transition"],
        "shot_type": "场景镜头",
        "reason": "场景变化需要明确的环境过渡镜头。",
    },
]

DEFAULT_SHOT = {
    "shot_type": "中景",
    "reason": "中等镜头提供一般情节的清晰视觉表达。",
}


def determine_shot_rule(actions: List[str], emotions: List[str]) -> Dict[str, str]:
    combined = set(actions + emotions)
    for rule in SHOT_RULES:
        if any(item in combined for item in rule["match"]):
            return {"shot_type": rule["shot_type"], "reason": rule["reason"]}
    return DEFAULT_SHOT


def determine_camera_movement(actions: List[str], shot_type: str | None = None) -> str:
    if shot_type == "追踪镜头":
        return "推轨"
    if shot_type == "特写":
        return "缓慢推进"
    if shot_type in {"远景", "场景镜头"}:
        return "静止"
    if "movement" in actions or "pursuit" in actions or "conflict" in actions:
        return "推轨"
    if "dialogue" in actions:
        return "缓慢推进"
    return "静止"


SHOT_PROGRESSIONS: Dict[str, List[Dict[str, str]]] = {
    "pursuit": [
        {"shot_type": "追踪镜头", "reason": "追逐开始，用动态追踪镜头建立紧张节奏。"},
        {"shot_type": "特写", "reason": "情绪高潮，用特写放大主角的恐惧与喘息。"},
        {"shot_type": "中景", "reason": "冲突转折，用中景交代主角与追击者的对峙关系。"},
    ],
    "conflict": [
        {"shot_type": "远景", "reason": "先以远景建立冲突环境与空间张力。"},
        {"shot_type": "中景", "reason": "再以中景聚焦角色对峙与肢体关系。"},
        {"shot_type": "特写", "reason": "最后用特写强化情绪爆发点。"},
    ],
    "fear": [
        {"shot_type": "追踪镜头", "reason": "恐惧场景先用运动镜头制造不安。"},
        {"shot_type": "特写", "reason": "恐惧细节通过面部特写放大。"},
        {"shot_type": "中景", "reason": "回到中景交代角色与环境关系。"},
    ],
    "dialogue": [
        {"shot_type": "中景", "reason": "对话场景以中景建立两人空间关系。"},
        {"shot_type": "双人镜", "reason": "用双人镜头突出交流互动。"},
        {"shot_type": "特写", "reason": "用特写捕捉说话者的情绪细节。"},
    ],
    "default": [
        {"shot_type": "远景", "reason": "以远景建立场景与氛围。"},
        {"shot_type": "中景", "reason": "以中景推进叙事动作。"},
        {"shot_type": "特写", "reason": "以特写强化情绪或关键细节。"},
    ],
}


def determine_shot_progression(actions: List[str], emotions: List[str], shot_count: int) -> List[Dict[str, str]]:
    """Return a per-shot rule list so each storyboard frame has distinct intent."""

    combined = set(actions + emotions)
    if "pursuit" in combined or ("movement" in combined and "fear" in combined):
        template = SHOT_PROGRESSIONS["pursuit"]
    elif "conflict" in combined:
        template = SHOT_PROGRESSIONS["conflict"]
    elif "fear" in combined or "sadness" in combined or "anger" in combined:
        template = SHOT_PROGRESSIONS["fear"]
    elif "dialogue" in combined:
        template = SHOT_PROGRESSIONS["dialogue"]
    else:
        template = SHOT_PROGRESSIONS["default"]

    result: List[Dict[str, str]] = []
    for index in range(shot_count):
        result.append(template[index % len(template)])
    return result


def build_cinematic_prompt(
    shot: Dict[str, str],
    location: str,
    characters: List[str],
    *,
    story_text: str = "",
    shot_number: int = 1,
    shot_count: int = 1,
    story_beat: str = "",
) -> str:
    subject = characters[0] if characters else "主角"
    beat = story_beat or story_text
    return (
        f"第{shot_number}/{shot_count}镜，{shot['shot_type']}，地点在{location}，涉及角色：{subject}。"
        f"本镜叙事：{beat}。{shot['reason']} "
        "请生成适合中文电影分镜绘图模型使用的画面描述，保持电影质感灯光、高对比、写实细节。"
    )
