"""HTTP client for local llama-server (127.0.0.1 only — SECURITY C5).

Docs: Phase 5 architecture streams via llama-server; contest requires offline
inference with zero outbound calls once weights are on disk.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


DEFAULT_BASE = "http://127.0.0.1:8080"


class LlamaServerError(RuntimeError):
    pass


def chat_completion(
    messages: list[dict[str, str]],
    *,
    base_url: str = DEFAULT_BASE,
    temperature: float = 0.2,
    max_tokens: int = 180,
    timeout_s: float = 120.0,
) -> str:
    """Call OpenAI-compatible /v1/chat/completions on local llama-server."""
    url = base_url.rstrip("/") + "/v1/chat/completions"
    body: dict[str, Any] = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise LlamaServerError(
            f"Cannot reach llama-server at {url}. "
            "Start it with: bash scripts/start_llama_server.sh"
        ) from exc

    try:
        return str(payload["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise LlamaServerError(f"Unexpected llama-server response: {payload!r}") from exc


def health(base_url: str = DEFAULT_BASE, timeout_s: float = 2.0) -> bool:
    url = base_url.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False
