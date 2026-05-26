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


def determine_camera_movement(actions: List[str]) -> str:
    if "movement" in actions or "pursuit" in actions or "conflict" in actions:
        return "推轨"
    if "dialogue" in actions:
        return "缓慢推进"
    return "静止"


def build_cinematic_prompt(shot: Dict[str, str], location: str, characters: List[str]) -> str:
    subject = characters[0] if characters else "主角"
    return (
        f"{shot['shot_type']}，主体为{subject}，地点在{location}。{shot['reason']} "
        "保持电影质感灯光、胶片颗粒、高对比、写实细节。"
    )
