"""Agent Layer - Shot Planner

Generates a shot plan and interprets parsed story structure into storyboard shots.
"""
from __future__ import annotations

from typing import Dict, List

from parser import parse_scene
from rules import (
    build_cinematic_prompt,
    determine_camera_movement,
    determine_shot_progression,
)
from llm import process_prompt_with_llm


class ShotPlanner:
    def __init__(self, desired_shots: int = 3):
        self.desired_shots = max(1, desired_shots)

    def plan(self, story_text: str) -> Dict[str, object]:
        parsed = parse_scene(story_text)
        shots = self._build_shots(story_text, parsed)
        return {
            "input_text": story_text,
            "parsed": parsed,
            "shots": shots,
        }

    def _story_beats(self, parsed: Dict[str, object]) -> List[str]:
        sentences = list(parsed.get("sentences", []))
        if not sentences:
            return [str(parsed.get("raw_text", ""))] * self.desired_shots

        beats: List[str] = []
        for index in range(self.desired_shots):
            beats.append(sentences[min(index, len(sentences) - 1)])
        return beats

    def _build_shots(self, story_text: str, parsed: Dict[str, object]) -> List[Dict[str, object]]:
        shots: List[Dict[str, object]] = []
        actions = parsed["actions"]
        emotions = parsed["emotions"]
        locations = parsed["locations"]
        characters = parsed["characters"]

        primary_location = locations[0] if locations else "室内"
        shot_rules = determine_shot_progression(actions, emotions, self.desired_shots)
        story_beats = self._story_beats(parsed)

        character_anchor = ""

        for idx in range(self.desired_shots):
            shot_rule = shot_rules[idx]
            shot_number = idx + 1
            shot_type = shot_rule["shot_type"]
            camera_movement = determine_camera_movement(actions, shot_type)
            story_beat = story_beats[idx]
            description = (
                f"镜头{shot_number}：{shot_type}，场景在{primary_location}。"
                f"本镜重点：{story_beat}。摄像机采用{camera_movement}。"
            )
            raw_prompt = build_cinematic_prompt(
                shot_rule,
                primary_location,
                characters,
                story_text=story_text,
                shot_number=shot_number,
                shot_count=self.desired_shots,
                story_beat=story_beat,
            )
            processed = process_prompt_with_llm(
                raw_prompt,
                story_text=story_text,
                shot_number=shot_number,
                shot_count=self.desired_shots,
                story_beat=story_beat,
                character_anchor=character_anchor,
            )
            final_prompt = processed.get("prompt", raw_prompt)
            if shot_number == 1:
                character_anchor = str(final_prompt)[:220]

            shots.append(
                {
                    "id": shot_number,
                    "type": processed.get("shot_type", shot_type),
                    "description": processed.get("description", description),
                    "camera_movement": processed.get("camera_movement", camera_movement),
                    "raw_prompt": raw_prompt,
                    "prompt": final_prompt,
                    "llm_json": processed,
                    "reason": processed.get("reason", shot_rule["reason"]),
                    "story_beat": story_beat,
                }
            )
        return shots


def plan_shots(text: str, count: int = 3) -> Dict[str, object]:
    planner = ShotPlanner(desired_shots=count)
    return planner.plan(text)
