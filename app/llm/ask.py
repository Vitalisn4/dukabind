"""End-to-end ask: binder decision plus optional local narration.

`message` is always the binder decision; model output stays in `narration`.
Refusals skip the model entirely (control C4).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from app.binder.pipeline import handle_ask, result_with_citation_json
from app.llm.client import (
    LlamaServerError,
    assert_loopback_http,
    chat_completion,
    health,
)
from app.prompts.narrate import build_narration_prompt


def ask(
    conn: sqlite3.Connection,
    text: str,
    *,
    use_llm: bool = True,
    base_url: str = "http://127.0.0.1:8080",
) -> dict[str, Any]:
    """Run binder; optionally attach local narration without overriding truth."""
    result = handle_ask(conn, text)
    payload = result_with_citation_json(result)
    payload["narrated"] = False
    payload["narration"] = None
    payload["source"] = "binder"

    # Never hand a refusal to the model; it would be tempted to fill in a number.
    if not result.ok and result.refuse_reason:
        return payload

    # Swahili answers are binder-only: the frozen Qwen2.5-1.5B model invents
    # or mangles figures when narrating in Swahili (verified empirically). The
    # deterministic binder message is authoritative, so narration is
    # deliberately skipped and a money figure is never mis-stated.
    if result.lang == "sw":
        payload["llm_note"] = (
            "Swahili narration skipped by design: the binder message is "
            "authoritative and the local model does not reliably narrate in Swahili"
        )
        return payload

    if not use_llm:
        return payload

    try:
        assert_loopback_http(base_url)
    except LlamaServerError as exc:
        payload["llm_note"] = str(exc)
        return payload

    if not health(base_url):
        payload["llm_note"] = "llama-server not running; returning binder message"
        return payload

    messages = build_narration_prompt(
        lang=result.lang,
        staff_question=text,
        binder_message=result.message,
        citation_json=payload["citation_json"],
    )
    try:
        narrated = chat_completion(messages, base_url=base_url)
    except LlamaServerError as exc:
        payload["llm_note"] = str(exc)
        return payload

    payload["message"] = result.message
    payload["narration"] = narrated
    payload["narrated"] = True
    payload["source"] = "binder+llm"
    return payload
