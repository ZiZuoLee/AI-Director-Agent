"""Cross-shot memory for characters and scenes."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .generation_types import ShotContext

CHARACTER_PATTERN = re.compile(
    r"(同一名|一名)?(?P<phrase>(?:二十多岁|年轻|瘦削|黑发|男子|女子|男人|女人|主角|追击者|反派|英雄|孩子|女孩|男孩|他|她)[^，。,.]*)"
)
SCENE_PATTERN = re.compile(
    r"(?P<phrase>(?:潮湿|黑暗|昏暗|狭窄|城市|夜晚|霓虹|模糊|空旷|压迫感|危险|雨夜|潮湿黑暗)[^，。,.]*(?:小巷|街道|森林|城市|房间|办公室|仓库|舞台|海滩|公园|屋内|屋外))"
)


def _normalize_phrase(text: str) -> str:
    return re.sub(r"\s+", "", text.strip(" ，。,."))


def _unique_preserve(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        key = _normalize_phrase(item)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


@dataclass
class CharacterMemory:
    character_id: str
    display_name: str
    description: str
    features: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    source_shots: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SceneMemory:
    scene_id: str
    display_name: str
    description: str
    features: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    source_shots: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ShotMemoryBinding:
    shot_id: int
    character_ids: List[str]
    scene_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DirectorMemory:
    characters: Dict[str, CharacterMemory]
    scenes: Dict[str, SceneMemory]
    shot_bindings: Dict[int, ShotMemoryBinding]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "characters": {key: value.to_dict() for key, value in self.characters.items()},
            "scenes": {key: value.to_dict() for key, value in self.scenes.items()},
            "shot_bindings": {str(key): value.to_dict() for key, value in self.shot_bindings.items()},
        }

    def apply_visual_features(
        self,
        shot_id: int,
        *,
        character_features: Mapping[str, List[str]],
        scene_features: Mapping[str, List[str]],
    ) -> None:
        binding = self.shot_bindings[shot_id]
        for memory_id in binding.character_ids:
            memory = self.characters[memory_id]
            memory.features = _unique_preserve([*memory.features, *character_features.get(memory_id, [])])
            memory.description = _build_character_description([memory.description, "，".join(character_features.get(memory_id, []))])
        for memory_id in binding.scene_ids:
            memory = self.scenes[memory_id]
            memory.features = _unique_preserve([*memory.features, *scene_features.get(memory_id, [])])
            memory.description = _build_scene_description([memory.description, "，".join(scene_features.get(memory_id, []))])


def _extract_feature_tokens(text: str) -> List[str]:
    tokens = re.split(r"[，。,.、\s]+", text)
    return [token for token in tokens if token and len(token) >= 2]


def _match_existing(memory_map: Mapping[str, Any], phrase: str) -> Optional[str]:
    normalized = _normalize_phrase(phrase)
    for memory_id, item in memory_map.items():
        haystack = [_normalize_phrase(item.display_name), _normalize_phrase(item.description)]
        haystack.extend(_normalize_phrase(alias) for alias in item.aliases)
        if normalized in haystack or any(normalized and normalized in entry for entry in haystack):
            return memory_id
    return None


def _build_character_description(phrases: List[str]) -> str:
    return "；".join(_unique_preserve(phrases))


def _build_scene_description(phrases: List[str]) -> str:
    return "；".join(_unique_preserve(phrases))


def build_director_memory(shots: Iterable[Mapping[str, Any] | ShotContext]) -> DirectorMemory:
    character_counter = 0
    scene_counter = 0
    characters: Dict[str, CharacterMemory] = {}
    scenes: Dict[str, SceneMemory] = {}
    bindings: Dict[int, ShotMemoryBinding] = {}

    for shot_like in shots:
        shot = shot_like if isinstance(shot_like, ShotContext) else ShotContext.from_mapping(shot_like)
        text = " ".join(
            part for part in [shot.description, shot.prompt, shot.raw_prompt or "", shot.reason or ""] if part
        )
        shot_character_ids: List[str] = []
        shot_scene_ids: List[str] = []

        character_phrases = [match.group("phrase").strip() for match in CHARACTER_PATTERN.finditer(text)]
        if not character_phrases and shot.metadata.get("subject_hint"):
            character_phrases = [str(shot.metadata["subject_hint"])]

        for phrase in _unique_preserve(character_phrases):
            existing_id = _match_existing(characters, phrase)
            if existing_id is None:
                character_counter += 1
                memory_id = f"person{character_counter}"
                description = phrase
                characters[memory_id] = CharacterMemory(
                    character_id=memory_id,
                    display_name=phrase,
                    description=description,
                    features=_extract_feature_tokens(phrase),
                    aliases=[phrase],
                    source_shots=[shot.shot_id],
                )
            else:
                memory_id = existing_id
                memory = characters[memory_id]
                memory.aliases = _unique_preserve([*memory.aliases, phrase])
                memory.features = _unique_preserve([*memory.features, *_extract_feature_tokens(phrase)])
                memory.source_shots = sorted(set([*memory.source_shots, shot.shot_id]))
                memory.description = _build_character_description([memory.description, phrase])
            shot_character_ids.append(memory_id)

        if not shot_character_ids:
            character_counter += 1
            memory_id = f"person{character_counter}"
            fallback_phrase = shot.description
            characters[memory_id] = CharacterMemory(
                character_id=memory_id,
                display_name=memory_id,
                description=fallback_phrase,
                features=_extract_feature_tokens(fallback_phrase),
                aliases=[memory_id],
                source_shots=[shot.shot_id],
            )
            shot_character_ids.append(memory_id)

        scene_phrases = [match.group("phrase").strip() for match in SCENE_PATTERN.finditer(text)]
        for phrase in _unique_preserve(scene_phrases):
            existing_id = _match_existing(scenes, phrase)
            if existing_id is None:
                scene_counter += 1
                memory_id = f"scene{scene_counter}"
                scenes[memory_id] = SceneMemory(
                    scene_id=memory_id,
                    display_name=phrase,
                    description=phrase,
                    features=_extract_feature_tokens(phrase),
                    aliases=[phrase],
                    source_shots=[shot.shot_id],
                )
            else:
                memory_id = existing_id
                memory = scenes[memory_id]
                memory.aliases = _unique_preserve([*memory.aliases, phrase])
                memory.features = _unique_preserve([*memory.features, *_extract_feature_tokens(phrase)])
                memory.source_shots = sorted(set([*memory.source_shots, shot.shot_id]))
                memory.description = _build_scene_description([memory.description, phrase])
            shot_scene_ids.append(memory_id)

        if not shot_scene_ids:
            scene_counter += 1
            memory_id = f"scene{scene_counter}"
            fallback_phrase = shot.description
            scenes[memory_id] = SceneMemory(
                scene_id=memory_id,
                display_name=memory_id,
                description=fallback_phrase,
                features=_extract_feature_tokens(fallback_phrase),
                aliases=[memory_id],
                source_shots=[shot.shot_id],
            )
            shot_scene_ids.append(memory_id)

        bindings[shot.shot_id] = ShotMemoryBinding(
            shot_id=shot.shot_id,
            character_ids=_unique_preserve(shot_character_ids),
            scene_ids=_unique_preserve(shot_scene_ids),
        )

    return DirectorMemory(characters=characters, scenes=scenes, shot_bindings=bindings)
