"""Prompt builders for narration.

Citation JSON is language-neutral; the model only rewrites the binder decision
and must not introduce figures absent from LEDGER_JSON.
Gate 1 narration prompts are English only (Path A).
"""

from __future__ import annotations

SYSTEM = """You are DukaBind, an offline shop assistant for African MSME counters.
You answer ONLY from the LEDGER_JSON the application provides.
Rules:
1. Never invent amounts, credit limits, balances, or stock counts.
2. If LEDGER_JSON is empty or says missing, say the staff must ask the owner.
3. Prefer short, clear sentences a cashier can act on.
4. Repeat the key numbers from LEDGER_JSON exactly.
5. Do not mention being an AI model or cloud services."""


def build_narration_prompt(
    *,
    lang: str,
    staff_question: str,
    binder_message: str,
    citation_json: str,
) -> list[dict[str, str]]:
    """Chat messages for llama-server /v1/chat/completions."""
    _ = lang  # Gate 1 is English-only; keep param for call-site stability.
    user = (
        f"STAFF_QUESTION:\n{staff_question}\n\n"
        f"BINDER_DECISION (authoritative — copy these facts):\n{binder_message}\n\n"
        f"LEDGER_JSON:\n{citation_json}\n\n"
        "Rewrite BINDER_DECISION as a short cashier-facing reply.\n"
        "Rules:\n"
        "- Keep every number identical to BINDER_DECISION.\n"
        "- Do not rename projected_outstanding as outstanding.\n"
        "- Do not add new figures or omit the max-qty line if present.\n"
        "- Do not invent missing ledger fields."
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ]
