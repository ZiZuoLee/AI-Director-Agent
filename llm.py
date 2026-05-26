"""LLM integration layer with mocked Chinese prompt processing.

This module provides a lightweight interface for Task C style prompt refinement.
If an OpenRouter API key is configured via OPENROUTER_API_KEY, it will attempt
an actual LLM call. Otherwise, it returns a mocked processed result.
"""
from __future__ import annotations

import json
import os
from typing import Dict

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = "deepseek/deepseek-v4-flash:free"


def process_prompt_with_llm(prompt: str) -> Dict[str, object]:
    """Process a Chinese cinematic prompt through LLM reasoning or a mock fallback."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    messages = [
        {
            "role": "user",
            "content": (
                "请将以下中文分镜提示进一步优化为更适合影视生成的描述，"
                "同时保持导演视角和电影语言：\n\n" + prompt
            ),
        }
    ]

    if api_key and requests:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "reasoning": {"enabled": True},
        }
        try:
            response = requests.post(
                url=LLM_API_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            return {
                "content": message.get("content", prompt),
                "reasoning_details": message.get("reasoning_details", {}),
            }
        except Exception:
            pass

    # Mock fallback when no API key or request fails.
    return {
        "content": (
            f"{prompt} 这个提示已由本地模拟模型处理，增强了电影化表达和中文细节。"
        ),
        "reasoning_details": {
            "mocked": True,
            "note": "使用本地模拟LLM处理，因为未检测到OPENROUTER_API_KEY或请求失败。",
        },
    }
