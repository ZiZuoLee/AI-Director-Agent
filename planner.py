"""Agent Layer - Shot Planner

Generates a shot plan and interprets parsed story structure into storyboard shots.
"""
from __future__ import annotations

from typing import Dict, List

from parser import parse_scene
from rules import build_cinematic_prompt, determine_camera_movement, determine_shot_rule
from llm import process_prompt_with_llm


class ShotPlanner:
    def __init__(self, desired_shots: int = 3):
        self.desired_shots = max(1, desired_shots)

    def plan(self, story_text: str) -> Dict[str, object]:
        parsed = parse_scene(story_text)
        shots = self._build_shots(parsed)
        return {
            "input_text": story_text,
            "parsed": parsed,
            "shots": shots,
        }

    def _build_shots(self, parsed: Dict[str, object]) -> List[Dict[str, object]]:
        shots: List[Dict[str, object]] = []
        actions = parsed["actions"]
        emotions = parsed["emotions"]
        locations = parsed["locations"]
        characters = parsed["characters"]

        base_rule = determine_shot_rule(actions, emotions)
        primary_location = locations[0] if locations else "interior"

        for idx in range(self.desired_shots):
            shot_type = base_rule["shot_type"]
            shot_number = idx + 1
            camera_movement = determine_camera_movement(actions)
            description = (
                f"镜头{shot_number}：{shot_type}，主体为{characters[0]}，场景在{primary_location}。"
                f"着重电影叙事，摄像机采用{camera_movement}。"
            )
            raw_prompt = build_cinematic_prompt(base_rule, primary_location, characters)
            processed = process_prompt_with_llm(raw_prompt)
            final_prompt = processed.get("content", raw_prompt)

            shots.append(
                {
                    "id": shot_number,
                    "type": shot_type,
                    "description": description,
                    "camera_movement": camera_movement,
                    "raw_prompt": raw_prompt,
                    "final_prompt": final_prompt,
                    "llm_reasoning": processed.get("reasoning_details", {}),
                    "reason": base_rule["reason"],
                }
            )
        return shots


def plan_shots(text: str, count: int = 3) -> Dict[str, object]:
    planner = ShotPlanner(desired_shots=count)
    return planner.plan(text)
