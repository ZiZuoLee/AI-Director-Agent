"""LLM integration layer for Chinese prompt design that returns JSON structure.

This module loads API configuration from the environment or a local `.env` file.
It sends Chinese prompt design instructions to a Chat Completions-compatible API and parses a JSON
response suitable for Task B consumption.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Optional

from backend.paths import ENV_FILE

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

DEFAULT_LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_LLM_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_LLM_TIMEOUT = 90
DOTENV_PATH = str(ENV_FILE)

_http_session: "requests.Session | None" = None


def _get_http_session() -> "requests.Session":
    """Reuse a session that ignores broken system proxy settings."""

    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        _http_session.trust_env = False
    return _http_session


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


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_first_json_object(text: str) -> Dict[str, object]:
    """Parse the first JSON object from LLM output, ignoring trailing commentary."""

    cleaned = _strip_code_fence(text)
    decoder = json.JSONDecoder()
    candidates = [
        cleaned,
        _sanitize_json_control_chars(cleaned),
        cleaned.replace("'", '"'),
        _sanitize_json_control_chars(cleaned.replace("'", '"')),
    ]

    last_error: json.JSONDecodeError | ValueError | None = None
    for candidate in candidates:
        for index, char in enumerate(candidate):
            if char != "{":
                continue
            try:
                parsed, _end = decoder.raw_decode(candidate, idx=index)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError as exc:
                last_error = exc

    try:
        return _fallback_parse_fields(cleaned)
    except ValueError as exc:
        if last_error is not None:
            raise last_error from exc
        raise ValueError("无法从 LLM 响应中提取 JSON。") from exc


def _sanitize_json_control_chars(content: str) -> str:
    """Escape raw newlines/tabs/control chars that appear inside JSON strings."""

    result: list[str] = []
    in_string = False
    escaped = False

    for char in content:
        if escaped:
            result.append(char)
            escaped = False
            continue
        if char == "\\":
            result.append(char)
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            result.append(char)
            continue
        if in_string:
            if char == "\n":
                result.append("\\n")
                continue
            if char == "\r":
                result.append("\\r")
                continue
            if char == "\t":
                result.append("\\t")
                continue
            if ord(char) < 32:
                result.append(f"\\u{ord(char):04x}")
                continue
        result.append(char)

    return "".join(result)


def _unescape_json_string(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\r", "\r")
        .replace("\\t", "\t")
        .replace('\\"', '"')
        .replace("\\\\", "\\")
    )


def _fallback_parse_fields(content: str) -> Dict[str, object]:
    fields: Dict[str, object] = {}
    for key in ("shot_type", "camera_movement", "prompt", "description", "reason"):
        match = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"', content, re.S)
        if match:
            fields[key] = _unescape_json_string(match.group(1))
    if not fields.get("prompt"):
        raise ValueError("无法从 LLM 响应中解析必要字段。")
    return fields


def parse_llm_json_object(content: str) -> Dict[str, object]:
    """Public helper for parsing the first JSON object from model text."""

    return _extract_first_json_object(content)


def _build_llm_instruction(
    prompt: str,
    *,
    story_text: str = "",
    shot_number: int = 1,
    shot_count: int = 1,
    story_beat: str = "",
    character_anchor: str = "",
) -> str:
    anchor_section = (
        f"\n已确立的角色外貌（后续镜头必须完全一致）：{character_anchor}\n"
        if character_anchor
        else ""
    )
    return (
        "你是电影分镜设计师，面向中文绘图模型（如豆包 Seedream）设计镜头。\n"
        "请输出一个 JSON 对象，字段名保持英文：shot_type, camera_movement, prompt, description, reason。\n"
        "但所有字段的值必须使用中文。\n\n"
        "硬性要求：\n"
        "1. prompt 字段必须是 50-120 字的中文绘图提示词，可直接送入中文图像模型；\n"
        "2. prompt 中必须写出具体角色外貌（年龄、性别、发型、服装），禁止只写“他/她/主角”；\n"
        "3. prompt 中必须包含场景、时间、光线、镜头景别、构图与情绪；\n"
        "4. 多镜头时，角色外貌描述在所有镜头中保持一致，但每镜动作与构图必须不同；\n"
        "5. 禁止在 prompt 中混入英文单词；\n"
        "6. 仅返回一个 JSON 对象，不要 Markdown，不要输出 JSON 之外的任何说明文字。\n\n"
        f"故事全文：{story_text or '（未提供）'}\n"
        f"当前镜头：第 {shot_number}/{shot_count} 镜\n"
        f"本镜叙事重点：{story_beat or '（沿用故事全文）'}\n"
        f"{anchor_section}"
        f"规则引擎提示：{prompt}"
    )


def process_prompt_with_llm(
    prompt: str,
    *,
    story_text: str = "",
    shot_number: int = 1,
    shot_count: int = 1,
    story_beat: str = "",
    character_anchor: str = "",
) -> Dict[str, object]:
    load_dotenv()
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY 或 OPENROUTER_API_KEY 未配置。请在 .env 或环境变量中设置。"
        )
    if requests is None:
        raise RuntimeError("缺少 requests 包，无法调用 LLM API。")

    llm_api_url = os.getenv("LLM_API_URL", DEFAULT_LLM_API_URL)
    llm_model = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)

    messages = [
        {
            "role": "user",
            "content": _build_llm_instruction(
                prompt,
                story_text=story_text,
                shot_number=shot_number,
                shot_count=shot_count,
                story_beat=story_beat,
                character_anchor=character_anchor,
            ),
        }
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, object] = {
        "model": llm_model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    if "zenmux.ai" in llm_api_url:
        payload["reasoning"] = {"enabled": True}

    timeout = int(os.getenv("LLM_TIMEOUT", DEFAULT_LLM_TIMEOUT))
    response = _get_http_session().post(
        url=llm_api_url,
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False),
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    message = data["choices"][0]["message"]
    content = message.get("content", "")
    parsed = _extract_first_json_object(content)

    parsed["raw_llm_content"] = content
    parsed["reasoning_details"] = message.get("reasoning_details", {})
    return parsed
