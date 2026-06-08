"""Multimodal image analyzer for candidate scoring and memory updates."""
from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

from backend.agent.llm import parse_llm_json_object
from .director_memory import DirectorMemory
from .generation_types import GenerationConfig, GenerationError, ShotContext


@dataclass
class VisionAnalysis:
    score: float
    character_consistency: float
    scene_consistency: float
    shot_match: float
    emotion_match: float
    visual_quality: float
    character_features: Dict[str, List[str]]
    scene_features: Dict[str, List[str]]
    summary: str
    rationale: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VisionAnalyzer:
    def __init__(self, config: GenerationConfig):
        self.config = config
        self._client: OpenAI | None = None

    def _load_env_file(self) -> None:
        env_path = self.config.vision_env_path
        if not env_path.exists():
            return
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

    def _api_key(self) -> str:
        self._load_env_file()
        api_key = self.config.vision_api_key or os.getenv("VISION_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("ZENMUX_API_KEY")
        if not api_key:
            raise GenerationError("VISION_API_KEY, LLM_API_KEY, or ZENMUX_API_KEY must be configured for vision analysis.")
        return api_key

    def _client_instance(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                base_url="https://zenmux.ai/api/v1",
                api_key=self._api_key(),
            )
        return self._client

    def _encode_image(self, image_path: str) -> str:
        path = Path(image_path)
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('utf-8')}"

    def _prompt(self, shot: ShotContext, memory: DirectorMemory) -> str:
        binding = memory.shot_bindings[shot.shot_id]
        character_context = {
            item: memory.characters[item].to_dict() for item in binding.character_ids
        }
        scene_context = {
            item: memory.scenes[item].to_dict() for item in binding.scene_ids
        }
        return (
            "你是电影分镜视觉总监。请分析这张分镜图是否符合目标镜头，并仅返回 JSON。"
            "JSON 必须包含字段: score, character_consistency, scene_consistency, shot_match, emotion_match, visual_quality, "
            "character_features, scene_features, summary, rationale。"
            "所有 score 字段取 0 到 1 的数字。character_features 和 scene_features 必须是对象，键为 memory id，值为字符串数组。"
            f"\n\n目标镜头描述: {shot.description}"
            f"\n镜头提示词: {shot.prompt}"
            f"\n角色记忆: {json.dumps(character_context, ensure_ascii=False)}"
            f"\n场景记忆: {json.dumps(scene_context, ensure_ascii=False)}"
        )

    def analyze(self, shot: ShotContext, image_path: str, memory: DirectorMemory) -> VisionAnalysis:
        completion = self._client_instance().chat.completions.create(
            model=self.config.vision_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._prompt(shot, memory)},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self._encode_image(image_path),
                            },
                        },
                    ],
                }
            ],
        )
        content = completion.choices[0].message.content or ""
        parsed = parse_llm_json_object(content)
        return VisionAnalysis(
            score=float(parsed.get("score", 0.0)),
            character_consistency=float(parsed.get("character_consistency", 0.0)),
            scene_consistency=float(parsed.get("scene_consistency", 0.0)),
            shot_match=float(parsed.get("shot_match", 0.0)),
            emotion_match=float(parsed.get("emotion_match", 0.0)),
            visual_quality=float(parsed.get("visual_quality", 0.0)),
            character_features={
                key: [str(item) for item in value]
                for key, value in (parsed.get("character_features") or {}).items()
            },
            scene_features={
                key: [str(item) for item in value]
                for key, value in (parsed.get("scene_features") or {}).items()
            },
            summary=str(parsed.get("summary", "")),
            rationale=[str(item) for item in parsed.get("rationale", [])],
        )
