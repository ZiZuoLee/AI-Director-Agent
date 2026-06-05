"""Director agent loop for memory-aware storyboard generation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from backends.zenmux_api import ZenMuxImageBackend
from director_memory import DirectorMemory, build_director_memory
from generation_types import GenerationConfig, PromptSpec, ShotContext
from image_critic import CriticScore, score_candidate
from vision_analyzer import VisionAnalyzer


@dataclass
class DirectorReflection:
    shot_id: int
    attempt: int
    strategy: str
    issue: str
    action: str
    score: float
    rationale: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DirectorShotResult:
    shot_id: int
    selected_image: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    reflections: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DirectorAgent:
    """Memory-aware generation loop that turns the image tool into an agent."""

    def __init__(self, config: GenerationConfig | Mapping[str, Any] | None = None):
        self.config = config if isinstance(config, GenerationConfig) else GenerationConfig.from_mapping(config)
        self.backend = ZenMuxImageBackend(self.config)
        self.vision = VisionAnalyzer(self.config) if self.config.vision_enabled else None

    def _normalize_shots(self, shots: Iterable[Mapping[str, Any] | ShotContext]) -> List[ShotContext]:
        return [shot if isinstance(shot, ShotContext) else ShotContext.from_mapping(shot) for shot in shots]

    def _character_memory_block(self, memory: DirectorMemory, shot: ShotContext) -> str:
        binding = memory.shot_bindings[shot.shot_id]
        descriptions = [memory.characters[item].description for item in binding.character_ids]
        return "；".join(descriptions)

    def _scene_memory_block(self, memory: DirectorMemory, shot: ShotContext) -> str:
        binding = memory.shot_bindings[shot.shot_id]
        descriptions = [memory.scenes[item].description for item in binding.scene_ids]
        return "；".join(descriptions)

    def _build_candidate_prompt(self, shot: ShotContext, memory: DirectorMemory, strategy: str, attempt: int) -> str:
        character_block = self._character_memory_block(memory, shot)
        scene_block = self._scene_memory_block(memory, shot)
        base_parts = [
            "电影分镜风格",
            character_block,
            scene_block,
            shot.prompt,
            f"镜头类型：{shot.shot_type}",
            f"运镜：{shot.camera_movement}",
        ]
        if shot.reason:
            base_parts.append(f"导演意图：{shot.reason}")
        if strategy == "continuity_anchor":
            base_parts.append("保持角色外貌一致，保持服装一致，保持场景连续性")
        elif strategy == "edit_reference":
            base_parts.append("基于上一张参考画面延续同一角色外貌、服装、场景光线和电影风格")
        elif strategy == "scene_anchor":
            base_parts.append("优先保持场景空间结构、灯光气氛和背景元素一致")
        if attempt > 1:
            base_parts.append("进一步强化角色辨识度和镜头语言，避免画面漂移")
        return "，".join(part.strip("， ") for part in base_parts if part)

    def _build_prompt_spec(self, shot: ShotContext, prompt: str, strategy: str, seed: int, attempt: int) -> PromptSpec:
        output_name = f"shot_{shot.shot_id:02d}_{strategy}_attempt_{attempt}_seed_{seed}.{self.config.image_format}"
        return PromptSpec(
            shot_id=shot.shot_id,
            positive_prompt=prompt,
            negative_prompt=self.config.negative_prompt,
            width=self.config.width,
            height=self.config.height,
            steps=self.config.steps,
            guidance_scale=self.config.guidance_scale,
            seed=seed,
            output_name=output_name,
            style_preset=self.config.style_preset,
            metadata={
                "description": shot.description,
                "shot_type": shot.shot_type,
                "camera_movement": shot.camera_movement,
                "reason": shot.reason,
                "strategy": strategy,
                "attempt": attempt,
            },
        )

    def _choose_strategy(
        self,
        shot: ShotContext,
        memory: DirectorMemory,
        previous_best: Optional[Dict[str, Any]],
        attempt: int,
    ) -> str:
        binding = memory.shot_bindings[shot.shot_id]
        repeated_character = any(len(memory.characters[item].source_shots) > 1 for item in binding.character_ids)
        repeated_scene = any(len(memory.scenes[item].source_shots) > 1 for item in binding.scene_ids)
        if previous_best and repeated_character and attempt > 1:
            return "edit_reference"
        if repeated_character:
            return "continuity_anchor"
        if repeated_scene:
            return "scene_anchor"
        return "base"

    def _candidate_seed(self, base_seed: int, offset: int) -> int:
        return base_seed + offset * 17

    def _generate_candidate(
        self,
        shot: ShotContext,
        spec: PromptSpec,
        strategy: str,
        reference_image_path: Optional[str],
    ) -> Dict[str, Any]:
        if strategy == "edit_reference" and reference_image_path:
            result = self.backend.edit_one(
                spec,
                reference_image_path=reference_image_path,
                seed_override=spec.seed,
            )
        else:
            result = self.backend.generate_one(spec, seed_override=spec.seed)
        return result.to_dict()

    def _analyze_candidate(
        self,
        shot: ShotContext,
        candidate: Dict[str, Any],
        memory: DirectorMemory,
    ):
        if self.vision is None:
            return None
        return self.vision.analyze(shot, candidate["image_path"], memory)

    def _run_shot_loop(
        self,
        shot: ShotContext,
        memory: DirectorMemory,
        previous_best: Optional[Dict[str, Any]],
    ) -> DirectorShotResult:
        best_candidate: Optional[Dict[str, Any]] = None
        best_score: Optional[CriticScore] = None
        all_candidates: List[Dict[str, Any]] = []
        reflections: List[DirectorReflection] = []

        for attempt in range(1, self.config.max_attempts + 1):
            strategy = self._choose_strategy(shot, memory, previous_best, attempt)
            reference_path = previous_best["image_path"] if previous_best and strategy == "edit_reference" else None

            for index in range(self.config.candidate_count):
                seed = self._candidate_seed(
                    self.config.zenmux_seed if self.config.zenmux_seed is not None else self.config.seed,
                    index,
                )
                prompt = self._build_candidate_prompt(shot, memory, strategy, attempt)
                if index == 1:
                    prompt += "，强化角色服装与发型识别特征"
                elif index == 2:
                    prompt += "，强化景别构图与环境气氛"
                spec = self._build_prompt_spec(shot, prompt, strategy, seed, attempt)
                candidate = self._generate_candidate(shot, spec, strategy, reference_path)
                critic_score = score_candidate(shot, candidate, memory, vision=None)
                candidate["critic_score"] = critic_score.to_dict()
                all_candidates.append(candidate)

                if best_score is None or critic_score.total > best_score.total:
                    best_candidate = candidate
                    best_score = critic_score

            shortlisted = sorted(
                all_candidates[-self.config.candidate_count:],
                key=lambda item: item["critic_score"]["total"],
                reverse=True,
            )[: self.config.vision_shortlist_size]

            for candidate in shortlisted:
                vision_analysis = self._analyze_candidate(shot, candidate, memory)
                if vision_analysis is not None:
                    candidate["vision_analysis"] = vision_analysis.to_dict()
                critic_score = score_candidate(shot, candidate, memory, vision=vision_analysis)
                candidate["critic_score"] = critic_score.to_dict()
                if best_score is None or critic_score.total > best_score.total:
                    best_candidate = candidate
                    best_score = critic_score

            assert best_score is not None and best_candidate is not None
            if best_score.total >= self.config.score_threshold:
                reflections.append(
                    DirectorReflection(
                        shot_id=shot.shot_id,
                        attempt=attempt,
                        strategy=strategy,
                        issue="candidate_search",
                        action="accept_best_candidate",
                        score=best_score.total,
                        rationale=best_score.rationale,
                    )
                )
                break

            reflections.append(
                DirectorReflection(
                    shot_id=shot.shot_id,
                    attempt=attempt,
                    strategy=strategy,
                    issue="score_below_threshold",
                    action="retry_with_stronger_continuity_strategy",
                    score=best_score.total,
                    rationale=best_score.rationale,
                )
            )

        assert best_candidate is not None
        if self.vision is not None and "vision_analysis" in best_candidate:
            vision_data = best_candidate["vision_analysis"]
            memory.apply_visual_features(
                shot.shot_id,
                character_features=vision_data.get("character_features", {}),
                scene_features=vision_data.get("scene_features", {}),
            )
        return DirectorShotResult(
            shot_id=shot.shot_id,
            selected_image=best_candidate,
            candidates=all_candidates,
            reflections=[item.to_dict() for item in reflections],
        )

    def run(self, shots: Iterable[Mapping[str, Any] | ShotContext]) -> Dict[str, Any]:
        normalized_shots = self._normalize_shots(shots)
        memory = build_director_memory(normalized_shots)

        results: List[DirectorShotResult] = []
        previous_best: Optional[Dict[str, Any]] = None
        for shot in normalized_shots:
            shot_result = self._run_shot_loop(shot, memory, previous_best)
            results.append(shot_result)
            previous_best = shot_result.selected_image

        return {
            "memory": memory.to_dict(),
            "shots": [item.to_dict() for item in results],
        }
