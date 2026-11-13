import os
import sys
import json
import subprocess
import tempfile
import urllib.request
import re
from pathlib import Path

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1/chat/completions"

def call_llm(model: str, messages: list[dict], temperature: float = 0.2) -> str:
    """
    Calls LLM via DeepSeek API or Ollama OpenAI-compatible endpoint.
    """
    is_ollama = "qwen" in model.lower()
    url = OLLAMA_BASE_URL if is_ollama else DEEPSEEK_BASE_URL
    api_key = "ollama" if is_ollama else DEEPSEEK_API_KEY

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4096
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM API Error ({e.code}): {err_msg}")
    except Exception as e:
        raise RuntimeError(f"LLM Network Error: {e}")
