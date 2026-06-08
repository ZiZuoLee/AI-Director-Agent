"""Shared types and validation helpers for the generation layer."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from backend.paths import ENV_FILE, IMAGES_DIR, ZENMUX_ENV_FILE


class GenerationError(RuntimeError):
    """Raised when image generation cannot be completed safely."""


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GenerationError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _optional_string(value: object, field_name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise GenerationError(f"{field_name} must be a string when provided.")
    normalized = value.strip()
    return normalized or None


def _normalize_int(value: object, default: int, field_name: str, minimum: int = 0) -> int:
    if value is None:
        normalized = default
    elif isinstance(value, bool) or not isinstance(value, int):
        raise GenerationError(f"{field_name} must be an integer.")
    else:
        normalized = value
    if normalized < minimum:
        raise GenerationError(f"{field_name} must be >= {minimum}.")
    return normalized


def _normalize_float(value: object, default: float, field_name: str, minimum: float = 0.0) -> float:
    if value is None:
        normalized = default
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GenerationError(f"{field_name} must be a number.")
    else:
        normalized = float(value)
    if normalized < minimum:
        raise GenerationError(f"{field_name} must be >= {minimum}.")
    return normalized


@dataclass(frozen=True)
class ShotContext:
    """Normalized shot input consumed by the generation layer."""

    shot_id: int
    shot_type: str
    prompt: str
    description: str
    camera_movement: str
    raw_prompt: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, shot: Mapping[str, Any]) -> "ShotContext":
        if not isinstance(shot, Mapping):
            raise GenerationError("Each shot must be a mapping-like object.")

        shot_id = _normalize_int(shot.get("id"), default=0, field_name="shot.id", minimum=1)
        metadata = {
            key: value
            for key, value in shot.items()
            if key
            not in {
                "id",
                "type",
                "prompt",
                "description",
                "camera_movement",
                "raw_prompt",
                "reason",
            }
        }
        return cls(
            shot_id=shot_id,
            shot_type=_require_non_empty_string(shot.get("type"), "shot.type"),
            prompt=_require_non_empty_string(shot.get("prompt"), "shot.prompt"),
            description=_require_non_empty_string(shot.get("description"), "shot.description"),
            camera_movement=_require_non_empty_string(
                shot.get("camera_movement"), "shot.camera_movement"
            ),
            raw_prompt=_optional_string(shot.get("raw_prompt"), "shot.raw_prompt"),
            reason=_optional_string(shot.get("reason"), "shot.reason"),
            metadata=metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromptSpec:
    """Backend-independent prompt specification for one image."""

    shot_id: int
    positive_prompt: str
    negative_prompt: str
    width: int
    height: int
    steps: int
    guidance_scale: float
    seed: int
    output_name: str
    style_preset: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def output_path(self, output_dir: Path) -> Path:
        return output_dir / self.output_name

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationConfig:
    """Runtime configuration shared by all backends."""

    backend: str = "zenmux_api"
    model_id: str = "bytedance/doubao-seedream-5.0-lite"
    output_dir: Path = IMAGES_DIR
    image_format: str = "png"
    width: int = 1024
    height: int = 1024
    steps: int = 1
    guidance_scale: float = 0.0
    negative_prompt: str = ""
    prompt_suffix: str = (
        "电影分镜风格，角色外貌保持一致，电影感灯光，戏剧化构图，高对比，写实细节，16:9横构图"
    )
    style_preset: str = "cinematic_storyboard"
    seed: int = 20260605
    seed_stride: int = 97
    request_timeout: float = 120.0
    zenmux_base_url: str = "https://zenmux.ai/api/vertex-ai"
    zenmux_api_key: Optional[str] = None
    zenmux_env_path: Path = ZENMUX_ENV_FILE
    zenmux_image_size: str = "1K"
    zenmux_aspect_ratio: Optional[str] = None
    zenmux_output_mime_type: str = "image/png"
    zenmux_output_compression_quality: Optional[int] = None
    zenmux_seed: Optional[int] = None
    zenmux_enhance_prompt: bool = False
    zenmux_person_generation: Optional[str] = None
    zenmux_user: Optional[str] = None
    vision_enabled: bool = True
    vision_api_url: str = "https://zenmux.ai/api/v1/chat/completions"
    vision_model: str = "z-ai/glm-4.6v-flash-free"
    vision_api_key: Optional[str] = None
    vision_env_path: Path = ENV_FILE
    vision_shortlist_size: int = 1
    candidate_count: int = 3
    max_attempts: int = 2
    score_threshold: float = 0.7
    edit_model_id: Optional[str] = None

    @classmethod
    def from_mapping(cls, overrides: Optional[Mapping[str, Any]] = None) -> "GenerationConfig":
        data = dict(overrides or {})
        image_format = str(data.get("image_format", cls.image_format)).strip().lower() or "png"
        if image_format not in {"png", "jpg", "jpeg", "webp"}:
            raise GenerationError("image_format must be one of: png, jpg, jpeg, webp.")

        output_dir_value = data.get("output_dir", cls.output_dir)
        output_dir = output_dir_value if isinstance(output_dir_value, Path) else Path(str(output_dir_value))

        zenmux_api_key = _optional_string(data.get("zenmux_api_key"), "zenmux_api_key")
        zenmux_image_size = str(
            data.get("zenmux_image_size", cls.zenmux_image_size)
        ).strip().upper() or cls.zenmux_image_size
        if zenmux_image_size not in {"1K", "2K", "4K"}:
            raise GenerationError("zenmux_image_size must be one of: 1K, 2K, 4K.")

        zenmux_aspect_ratio = _optional_string(
            data.get("zenmux_aspect_ratio", cls.zenmux_aspect_ratio),
            "zenmux_aspect_ratio",
        )
        if zenmux_aspect_ratio is not None and zenmux_aspect_ratio not in {
            "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
        }:
            raise GenerationError(
                "zenmux_aspect_ratio must be one of: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9."
            )

        zenmux_output_mime_type = _require_non_empty_string(
            data.get("zenmux_output_mime_type", cls.zenmux_output_mime_type),
            "zenmux_output_mime_type",
        )
        if zenmux_output_mime_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise GenerationError("zenmux_output_mime_type must be one of: image/png, image/jpeg, image/webp.")

        output_compression_quality = data.get(
            "zenmux_output_compression_quality",
            cls.zenmux_output_compression_quality,
        )
        if output_compression_quality is None:
            zenmux_output_compression_quality = None
        else:
            zenmux_output_compression_quality = _normalize_int(
                output_compression_quality,
                75,
                "zenmux_output_compression_quality",
                minimum=0,
            )
            if zenmux_output_compression_quality > 100:
                raise GenerationError("zenmux_output_compression_quality must be <= 100.")

        zenmux_seed = data.get("zenmux_seed", cls.zenmux_seed)
        if zenmux_seed is not None:
            zenmux_seed = _normalize_int(zenmux_seed, cls.seed, "zenmux_seed", minimum=0)

        zenmux_person_generation = _optional_string(
            data.get("zenmux_person_generation", cls.zenmux_person_generation),
            "zenmux_person_generation",
        )
        if zenmux_person_generation is not None and zenmux_person_generation not in {"allow_adult", "allow_all", "dont_allow"}:
            raise GenerationError(
                "zenmux_person_generation must be one of: allow_adult, allow_all, dont_allow."
            )

        env_path_value = data.get("zenmux_env_path", cls.zenmux_env_path)
        zenmux_env_path = env_path_value if isinstance(env_path_value, Path) else Path(str(env_path_value))
        vision_env_path_value = data.get("vision_env_path", cls.vision_env_path)
        vision_env_path = (
            vision_env_path_value
            if isinstance(vision_env_path_value, Path)
            else Path(str(vision_env_path_value))
        )

        return cls(
            backend=str(data.get("backend", cls.backend)).strip() or cls.backend,
            model_id=_require_non_empty_string(data.get("model_id", cls.model_id), "model_id"),
            output_dir=output_dir,
            image_format=image_format,
            width=_normalize_int(data.get("width"), cls.width, "width", minimum=64),
            height=_normalize_int(data.get("height"), cls.height, "height", minimum=64),
            steps=_normalize_int(data.get("steps"), cls.steps, "steps", minimum=1),
            guidance_scale=_normalize_float(
                data.get("guidance_scale"), cls.guidance_scale, "guidance_scale", minimum=0.0
            ),
            negative_prompt=str(data.get("negative_prompt", cls.negative_prompt)),
            prompt_suffix=_require_non_empty_string(
                data.get("prompt_suffix", cls.prompt_suffix), "prompt_suffix"
            ),
            style_preset=_require_non_empty_string(
                data.get("style_preset", cls.style_preset), "style_preset"
            ),
            seed=_normalize_int(data.get("seed"), cls.seed, "seed", minimum=0),
            seed_stride=_normalize_int(data.get("seed_stride"), cls.seed_stride, "seed_stride", minimum=1),
            request_timeout=_normalize_float(
                data.get("request_timeout"), cls.request_timeout, "request_timeout", minimum=1.0
            ),
            zenmux_base_url=_require_non_empty_string(
                data.get("zenmux_base_url", cls.zenmux_base_url),
                "zenmux_base_url",
            ),
            zenmux_api_key=zenmux_api_key,
            zenmux_env_path=zenmux_env_path,
            zenmux_image_size=zenmux_image_size,
            zenmux_aspect_ratio=zenmux_aspect_ratio,
            zenmux_output_mime_type=zenmux_output_mime_type,
            zenmux_output_compression_quality=zenmux_output_compression_quality,
            zenmux_seed=zenmux_seed,
            zenmux_enhance_prompt=bool(data.get("zenmux_enhance_prompt", cls.zenmux_enhance_prompt)),
            zenmux_person_generation=zenmux_person_generation,
            zenmux_user=_optional_string(data.get("zenmux_user"), "zenmux_user"),
            vision_enabled=bool(data.get("vision_enabled", cls.vision_enabled)),
            vision_api_url=_require_non_empty_string(
                data.get("vision_api_url", cls.vision_api_url),
                "vision_api_url",
            ),
            vision_model=_require_non_empty_string(
                data.get("vision_model", cls.vision_model),
                "vision_model",
            ),
            vision_api_key=_optional_string(data.get("vision_api_key"), "vision_api_key"),
            vision_env_path=vision_env_path,
            vision_shortlist_size=_normalize_int(
                data.get("vision_shortlist_size"),
                cls.vision_shortlist_size,
                "vision_shortlist_size",
                minimum=1,
            ),
            candidate_count=_normalize_int(
                data.get("candidate_count"),
                cls.candidate_count,
                "candidate_count",
                minimum=1,
            ),
            max_attempts=_normalize_int(
                data.get("max_attempts"),
                cls.max_attempts,
                "max_attempts",
                minimum=1,
            ),
            score_threshold=_normalize_float(
                data.get("score_threshold"),
                cls.score_threshold,
                "score_threshold",
                minimum=0.0,
            ),
            edit_model_id=_optional_string(data.get("edit_model_id", cls.edit_model_id), "edit_model_id"),
        )


@dataclass(frozen=True)
class GeneratedImage:
    """Serialized result returned to the rest of the system."""

    shot_id: int
    prompt: str
    negative_prompt: str
    image_path: str
    seed: int
    steps: int
    guidance_scale: float
    backend: str
    model_id: str
    width: int
    height: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
