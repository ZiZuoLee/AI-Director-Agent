"""LLM integration layer for Chinese prompt design that returns JSON structure.

This module loads OPENROUTER_API_KEY from the environment or a local `.env` file.
It sends Chinese prompt design instructions to OpenRouter and parses a JSON
response suitable for Task B consumption.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = "deepseek/deepseek-v4-flash:free"
DOTENV_PATH = ".env"


def load_dotenv(dotenv_path: str = DOTENV_PATH) -> None:
    if not os.path.exists(dotenv_path):
        return

    with open(dotenv_path, encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _extract_json_string(text: str) -> str:
    match = re.search(r"(\{.*\})", text, re.S)
    if not match:
        raise ValueError("无法从 LLM 响应中提取 JSON。")
    return match.group(1)


def _parse_json(content: str) -> Dict[str, object]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        normalized = content.replace("'", '"')
        return json.loads(normalized)


def process_prompt_with_llm(prompt: str) -> Dict[str, object]:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY 未配置。请在 .env 或环境变量中设置。"
        )
    if requests is None:
        raise RuntimeError("缺少 requests 包，无法调用 OpenRouter API。")

    messages = [
        {
            "role": "user",
            "content": (
                "你是电影分镜设计师。请根据以下中文镜头提示输出一个JSON对象，"
                "该对象包含字段 shot_type, camera_movement, prompt, description, reason。"
                "仅返回JSON，不要Markdown或额外解释。"
                "\n\n提示内容：\n" + prompt
            ),
        }
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "reasoning": {"enabled": True},
    }

    response = requests.post(
        url=LLM_API_URL,
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False),
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    message = data["choices"][0]["message"]
    content = message.get("content", "")
    json_text = _extract_json_string(content)
    parsed = _parse_json(json_text)

    parsed["raw_llm_content"] = content
    parsed["reasoning_details"] = message.get("reasoning_details", {})
    return parsed
