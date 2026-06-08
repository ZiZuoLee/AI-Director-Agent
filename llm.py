"""LLM integration layer for Chinese prompt design that returns JSON structure.

This module loads API configuration from the environment or a local `.env` file.
It sends Chinese prompt design instructions to a Chat Completions-compatible API and parses a JSON
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

DEFAULT_LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_LLM_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_LLM_TIMEOUT = 90
DOTENV_PATH = ".env"

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


def _extract_json_string(text: str) -> str:
    cleaned = _strip_code_fence(text)
    match = re.search(r"(\{.*\})", cleaned, re.S)
    if not match:
        raise ValueError("无法从 LLM 响应中提取 JSON。")
    return match.group(1)


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


def _parse_json(content: str) -> Dict[str, object]:
    candidates = [
        content,
        _sanitize_json_control_chars(content),
        content.replace("'", '"'),
        _sanitize_json_control_chars(content.replace("'", '"')),
    ]
    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            last_error = exc

    try:
        return _fallback_parse_fields(content)
    except ValueError as exc:
        if last_error is not None:
            raise last_error from exc
        raise


def process_prompt_with_llm(prompt: str) -> Dict[str, object]:
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
            "content": (
                "你是电影分镜设计师。请根据以下中文镜头提示输出一个JSON对象，"
                "该对象包含字段 shot_type, camera_movement, prompt, description, reason。"
                "仅返回单行合法JSON，字符串内不要换行，不要Markdown或额外解释。"
                "\n\n提示内容：\n" + prompt
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
    json_text = _extract_json_string(content)
    parsed = _parse_json(json_text)

    parsed["raw_llm_content"] = content
    parsed["reasoning_details"] = message.get("reasoning_details", {})
    return parsed
