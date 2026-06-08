"""System layer pipeline orchestration for the storyboard agent."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional

from backend.agent.planner import plan_shots
from backend.generation.generate import generate_images, generate_images_agentic
from backend.paths import IMAGES_DIR, ZENMUX_ENV_FILE
from backend.system.image_merge import merge_storyboard

GenerationMode = Literal["simple", "agentic"]
ProgressCallback = Callable[[Dict[str, Any]], None]


def _default_generation_config(task_id: str, overrides: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "backend": "zenmux_api",
        "model_id": "bytedance/doubao-seedream-5.0-lite",
        "edit_model_id": "bytedance/doubao-seedream-5.0-lite",
        "zenmux_env_path": str(ZENMUX_ENV_FILE),
        "output_dir": str(IMAGES_DIR / task_id),
        "width": 1024,
        "height": 576,
        "zenmux_image_size": "1K",
        "zenmux_aspect_ratio": "16:9",
        "zenmux_output_mime_type": "image/png",
        "zenmux_seed": 20260605,
        "zenmux_enhance_prompt": False,
        "request_timeout": 180,
        "candidate_count": 2,
        "max_attempts": 2,
        "score_threshold": 0.78,
        "vision_enabled": True,
        "vision_model": "z-ai/glm-4.6v-flash-free",
        "vision_shortlist_size": 1,
    }
    if overrides:
        config.update(overrides)
    return config


def _image_url(image_path: str) -> str:
    path = Path(image_path)
    if path.parent.name and path.parent.parent.name == "images":
        return f"/api/images/{path.parent.name}/{path.name}"
    return f"/api/images/legacy/{path.name}"


def _attach_image_urls(images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for image in images:
        item = dict(image)
        item["image_url"] = _image_url(item["image_path"])
        enriched.append(item)
    return enriched


def _attach_agent_image_urls(agent_result: Dict[str, Any]) -> Dict[str, Any]:
    shots: List[Dict[str, Any]] = []
    for shot in agent_result.get("shots", []):
        item = dict(shot)
        selected = dict(item.get("selected_image", {}))
        if selected.get("image_path"):
            selected["image_url"] = _image_url(selected["image_path"])
        item["selected_image"] = selected

        candidates: List[Dict[str, Any]] = []
        for candidate in item.get("candidates", []):
            candidate_item = dict(candidate)
            if candidate_item.get("image_path"):
                candidate_item["image_url"] = _image_url(candidate_item["image_path"])
            candidates.append(candidate_item)
        item["candidates"] = candidates
        shots.append(item)

    return {
        "memory": agent_result.get("memory", {}),
        "shots": shots,
    }


def run_plan(text: str, shot_count: int = 3) -> Dict[str, Any]:
    """Run only the agent-layer shot planning step."""

    return plan_shots(text, count=shot_count)


def run_pipeline(
    text: str,
    *,
    task_id: str,
    shot_count: int = 3,
    mode: GenerationMode = "simple",
    config_overrides: Mapping[str, Any] | None = None,
    on_progress: Optional[ProgressCallback] = None,
) -> Dict[str, Any]:
    """Execute the full text-to-storyboard pipeline with optional progress callbacks."""

    def emit(payload: Dict[str, Any]) -> None:
        if on_progress is not None:
            on_progress(payload)

    emit({"stage": "planning", "message": "正在解析剧本并规划分镜...", "percent": 5})
    plan = run_plan(text, shot_count=shot_count)
    shots = plan["shots"]
    total_shots = max(len(shots), 1)

    emit(
        {
            "stage": "planned",
            "message": f"已完成 {total_shots} 个镜头规划",
            "percent": 20,
            "plan": plan,
        }
    )

    generation_config = _default_generation_config(task_id, config_overrides)
    output_dir = Path(generation_config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    images: List[Dict[str, Any]] = []
    agent_result: Optional[Dict[str, Any]] = None

    if mode == "simple":
        emit({"stage": "generating", "message": "正在生成图像...", "percent": 25})
        for index, shot in enumerate(shots):
            if index > 0:
                time.sleep(2)
            shot_images = generate_images([shot], config=generation_config)
            images.extend(shot_images)
            percent = 20 + int(((index + 1) / total_shots) * 60)
            enriched = _attach_image_urls(shot_images)
            emit(
                {
                    "stage": "shot_done",
                    "message": f"镜头 {shot['id']} 生成完成",
                    "percent": percent,
                    "shot_id": shot["id"],
                    "images": enriched,
                }
            )
    else:
        emit({"stage": "generating", "message": "导演模式：正在生成并评估候选图像...", "percent": 30})
        raw_agent_result = generate_images_agentic(shots, config=generation_config)
        agent_result = _attach_agent_image_urls(raw_agent_result)
        emit(
            {
                "stage": "agent_done",
                "message": "导演模式生成完成",
                "percent": 80,
                "agent_result": agent_result,
            }
        )
        for shot_result in agent_result["shots"]:
            selected = shot_result.get("selected_image")
            if selected:
                images.append(selected)

    images = _attach_image_urls(images)

    storyboard_path: Optional[str] = None
    storyboard_url: Optional[str] = None
    image_paths = [item["image_path"] for item in images if item.get("image_path")]
    if image_paths:
        emit({"stage": "merging", "message": "正在拼接分镜板...", "percent": 90})
        merged = merge_storyboard(
            image_paths,
            output_path=output_dir / "storyboard.png",
            labels=[f"镜头 {shot['id']}" for shot in shots[: len(image_paths)]],
        )
        storyboard_path = str(merged)
        storyboard_url = _image_url(storyboard_path)

    result = {
        "input_text": text,
        "mode": mode,
        "plan": plan,
        "images": images,
        "agent_result": agent_result,
        "storyboard_path": storyboard_path,
        "storyboard_url": storyboard_url,
    }
    emit({"stage": "done", "message": "全部分镜生成完成", "percent": 100, "result": result})
    return result
