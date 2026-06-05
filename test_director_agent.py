"""Full director-agent smoke test using memory, candidate search, ranking, and retries."""
from __future__ import annotations

import json
from pathlib import Path

from director_agent import DirectorAgent


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
    "model_id": "bytedance/doubao-seedream-5.0-lite",
    "edit_model_id": "bytedance/doubao-seedream-5.0-lite",
    "zenmux_env_path": "zenmux.env",
    "output_dir": "images",
    "width": 1024,
    "height": 576,
    "zenmux_image_size": "1K",
    "zenmux_aspect_ratio": "16:9",
    "zenmux_output_mime_type": "image/png",
    "zenmux_seed": 20260605,
    "zenmux_enhance_prompt": False,
    "candidate_count": 2,
    "max_attempts": 2,
    "score_threshold": 0.78,
    "vision_enabled": True,
    "vision_model": "z-ai/glm-4.6v-flash-free",
    "vision_shortlist_size": 1,
}


def main() -> None:
    agent = DirectorAgent(CONFIG)
    result = agent.run(SAMPLE_SHOTS)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    Path("images").mkdir(parents=True, exist_ok=True)
    main()
