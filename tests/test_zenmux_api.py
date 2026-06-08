"""Direct ZenMux image-generation smoke test using shot JSON input."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.generation.generate import generate_from_plan
from backend.generation.generation_types import PromptSpec
from backend.paths import IMAGES_DIR, ZENMUX_ENV_FILE


SAMPLE_SHOTS = [
    {
        "id": 1,
        "type": "追踪镜头",
        "description": "镜头1：追踪镜头，主体为一名二十多岁的瘦削黑发年轻男子，穿深色连帽外套，场景在潮湿黑暗的小巷。着重电影叙事，摄像机采用推轨。",
        "camera_movement": "推轨",
        "prompt": "电影分镜风格，一名二十多岁的瘦削黑发年轻男子，穿深色连帽外套，在潮湿黑暗的城市小巷中惊恐奔跑，夜晚，追踪镜头，霓虹反光地面，紧张追逐氛围，电影感灯光，高对比，写实细节，保持角色外貌一致",
        "raw_prompt": "一名二十多岁的瘦削黑发年轻男子，穿深色连帽外套，在黑暗小巷中奔跑。",
        "reason": "动作与运动暗示需要动态追踪镜头。",
    },
    {
        "id": 2,
        "type": "特写",
        "description": "镜头2：特写，主体为同一名二十多岁的瘦削黑发年轻男子，穿深色连帽外套，场景在黑暗小巷。主角神情惊恐，着重表现面部细节，摄像机采用缓慢推进。",
        "camera_movement": "缓慢推进",
        "prompt": "电影分镜风格，同一名二十多岁的瘦削黑发年轻男子，穿深色连帽外套，惊恐表情特写，额头微汗，呼吸急促，眼神紧张，背景是模糊黑暗小巷夜景，缓慢推进镜头，电影感灯光，高对比，写实细节，保持角色外貌一致",
        "raw_prompt": "同一名二十多岁的瘦削黑发年轻男子，惊恐表情特写。",
        "reason": "强烈情绪需要亲密构图来放大情感。",
    },
    {
        "id": 3,
        "type": "中景",
        "description": "镜头3：中景，主体为同一名二十多岁的瘦削黑发年轻男子与追击者，场景在黑暗小巷。主角突然转身面对追击者，气氛紧张，摄像机采用静止。",
        "camera_movement": "静止",
        "prompt": "电影分镜风格，同一名二十多岁的瘦削黑发年轻男子，穿深色连帽外套，在黑暗小巷中突然停下并转身，与模糊危险的追击者对峙，中景，静止镜头，压迫感构图，紧张氛围，电影感灯光，高对比，写实细节，保持角色外貌一致",
        "raw_prompt": "同一名二十多岁的瘦削黑发年轻男子，在黑暗小巷中与追击者对峙。",
        "reason": "对峙时刻适合中景来同时交代角色关系与空间张力。",
    },
]

CONFIG = {
    "backend": "zenmux_api",
    "model_id": "google/gemini-2.5-flash-image",
    "zenmux_env_path": str(ZENMUX_ENV_FILE),
    "output_dir": str(IMAGES_DIR),
    "width": 1024,
    "height": 576,
    "zenmux_image_size": "1K",
    "zenmux_aspect_ratio": "16:9",
    "zenmux_output_mime_type": "image/png",
    "zenmux_seed": 20260605,
}


def build_direct_prompt_specs() -> list[PromptSpec]:
    specs: list[PromptSpec] = []
    for shot in SAMPLE_SHOTS:
        specs.append(
            PromptSpec(
                shot_id=shot["id"],
                positive_prompt=shot["prompt"],
                negative_prompt="",
                width=CONFIG["width"],
                height=CONFIG["height"],
                steps=1,
                guidance_scale=0.0,
                seed=CONFIG["zenmux_seed"],
                output_name=f"shot_{shot['id']:02d}_zenmux.png",
                style_preset="zenmux_direct_prompt",
                metadata={
                    "description": shot["description"],
                    "shot_type": shot["type"],
                    "camera_movement": shot["camera_movement"],
                    "reason": shot["reason"],
                },
            )
        )
    return specs


def main() -> None:
    prompt_specs = build_direct_prompt_specs()
    print("ZenMux prompt specs:")
    for spec in prompt_specs:
        print(json.dumps(spec.to_dict(), ensure_ascii=False, indent=2))

    results = generate_from_plan(prompt_specs, config=CONFIG)
    print("\nGenerated images:")
    for item in results:
        print(json.dumps(item, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    main()
