"""End-to-end ask: binder truth → optional llama-server narration.

Fail-closed refuses skip the LLM (Phase 5 / SECURITY C4).
Successful binder decisions may be narrated if llama-server is up;
otherwise we return the deterministic binder message (still correct).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from app.binder.pipeline import handle_ask, result_with_citation_json
from app.llm.client import LlamaServerError, chat_completion, health
from app.prompts.narrate import build_narration_prompt


def ask(
    conn: sqlite3.Connection,
    text: str,
    *,
    use_llm: bool = True,
    base_url: str = "http://127.0.0.1:8080",
) -> dict[str, Any]:
    result = handle_ask(conn, text)
    payload = result_with_citation_json(result)
    payload["narrated"] = False
    payload["source"] = "binder"

    # Hard refuse: never ask the model to invent a fill-in.
    if not result.ok and result.refuse_reason:
        return payload

    if not use_llm:
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

    payload["binder_message"] = result.message
    payload["message"] = narrated
    payload["narrated"] = True
    payload["source"] = "binder+llm"
    return payload
