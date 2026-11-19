"""DeepSeek（OpenAI 兼容）最小客户端 —— 全组共用，P3 维护。

只用标准库 urllib，不引入第三方依赖。
环境变量：
  DEEPSEEK_API_KEY   必填
  DEEPSEEK_BASE_URL  可选，默认 https://api.deepseek.com
  DEEPSEEK_MODEL     可选，默认 deepseek-chat

其他块不许各自写 API 调用，统一 import 这里。
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
import urllib.error
import urllib.request
from typing import Any

DEFAULT_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


class LLMError(RuntimeError):
    pass


class LLMAuthError(LLMError):
    """API key 无效/过期/无余额（401/403）。"""


def _endpoint() -> str:
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    return base + "/chat/completions"


def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
    json_mode: bool = False,
    timeout: int = 120,
    retries: int = 2,
) -> str:
    """返回模型回复的文本；失败抛 LLMError（带状态码/响应摘要）。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise LLMError("环境变量 DEEPSEEK_API_KEY 未设置")
    payload: dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_err = ""
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            _endpoint(),
            data=body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            _log_usage(payload.get("model"), data)
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:500]
            last_err = "HTTP " + str(e.code) + " " + body
            if e.code in (401, 403):
                raise LLMAuthError(last_err) from None
        except Exception as e:  # noqa: BLE001
            last_err = type(e).__name__ + ": " + str(e)
        time.sleep(1.5 * (attempt + 1))
    raise LLMError(last_err or "unknown error")


def _log_usage(model, data) -> None:
    """把 API 返回的 usage 追加到 HARNESS_USAGE_LOG（run_recipe 会设为 runs/<臂>/api_usage.jsonl）。"""
    path = os.environ.get("HARNESS_USAGE_LOG", "")
    if not path:
        return
    usage = (data or {}).get("usage") or {}
    if not usage:
        return
    row = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "prompt_cache_hit_tokens": usage.get("prompt_cache_hit_tokens", 0),
        "prompt_cache_miss_tokens": usage.get("prompt_cache_miss_tokens", 0),
    }
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def ping(model: str | None = None) -> str:
    """用一次极小调用验证 key 是否有效；401/403 抛 LLMAuthError。"""
    return chat([{"role": "user", "content": "ping"}], model=model, temperature=0.0, timeout=30, retries=0)


def chat_json(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.0,
    timeout: int = 120,
) -> Any:
    """要求模型输出 JSON，并解析；解析失败返回 None（调用方要处理）。"""
    text = chat(messages, model=model, temperature=temperature, json_mode=True, timeout=timeout)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
