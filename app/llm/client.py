"""HTTP client for local llama-server.

Requests are restricted to loopback (control C5) so a staff question and its
ledger citations can never leave the machine.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_BASE = "http://127.0.0.1:8080"


class LlamaServerError(RuntimeError):
    """Raised when local llama-server is unreachable or returns bad data."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Reject redirects so a poisoned Location cannot leave loopback."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        """Block every redirect so citations cannot leave loopback."""
        raise LlamaServerError(
            f"Refusing HTTP redirect from {req.full_url!r} to {newurl!r} "
            "(llama-server client allows 127.0.0.1 only)."
        )


def assert_loopback_http(url: str) -> None:
    """Require exact http://127.0.0.1 with no credentials (control C5)."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "http":
        raise LlamaServerError(f"Only http://127.0.0.1 is allowed, got scheme={parsed.scheme!r}")
    if parsed.hostname != "127.0.0.1":
        raise LlamaServerError(
            f"Only hostname 127.0.0.1 is allowed, got {parsed.hostname!r}"
        )
    if parsed.username is not None or parsed.password is not None:
        raise LlamaServerError("Credentials are not allowed in llama-server URLs")


def _opener() -> urllib.request.OpenerDirector:
    """Build a urllib opener that refuses HTTP redirects."""
    return urllib.request.build_opener(_NoRedirect())


def chat_completion(
    messages: list[dict[str, str]],
    *,
    base_url: str = DEFAULT_BASE,
    temperature: float = 0.2,
    max_tokens: int = 180,
    timeout_s: float = 120.0,
) -> str:
    """Call OpenAI-compatible /v1/chat/completions on local llama-server."""
    assert_loopback_http(base_url)
    url = base_url.rstrip("/") + "/v1/chat/completions"
    assert_loopback_http(url)
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
        with _opener().open(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw)
    except urllib.error.URLError as exc:
        raise LlamaServerError(
            f"Cannot reach llama-server at {url}. "
            "Start it with: bash scripts/start_llama_server.sh"
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        raise LlamaServerError(
            f"Malformed response from llama-server at {url}: {exc}"
        ) from exc

    try:
        return str(payload["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise LlamaServerError(f"Unexpected llama-server response: {payload!r}") from exc


def health(base_url: str = DEFAULT_BASE, timeout_s: float = 2.0) -> bool:
    """Return True if local llama-server /health responds with 2xx."""
    try:
        assert_loopback_http(base_url)
        url = base_url.rstrip("/") + "/health"
        assert_loopback_http(url)
        with _opener().open(url, timeout=timeout_s) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False
