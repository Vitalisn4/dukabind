"""Build language-neutral citation blocks for the LLM (and for bare-GGUF prompts)."""

from __future__ import annotations

import json
from typing import Any


def citations_to_json(rows: list[dict[str, Any]], *, as_of: str | None = None) -> str:
    payload: dict[str, Any] = {"ledger_rows": rows}
    if as_of:
        payload["as_of"] = as_of
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
