"""Prompt builders for narration.

Citation JSON is language-neutral; the model only rewrites the binder decision
and must not introduce figures absent from LEDGER_JSON.
Narration follows the ask language for English and French. Swahili answers are
binder-only by design (see app/llm/ask.py) — the prompt below exists for
direct use and testing, not for the shipped Swahili path, because the frozen
Qwen2.5-1.5B model does not narrate Swahili reliably.

Swahili uses a deliberately minimal prompt: the frozen Qwen2.5-1.5B model
follows short Swahili instructions but echoes back a long structured prompt.
All facts live in BINDER_DECISION, so LEDGER_JSON is omitted for Swahili.
"""

from __future__ import annotations

_SYSTEM_EN = """You are DukaBind, an offline shop assistant for African MSME counters.
You answer ONLY from the LEDGER_JSON the application provides.
Rules:
1. Never invent amounts, credit limits, balances, or stock counts.
2. If LEDGER_JSON is empty or says missing, say the staff must ask the owner.
3. Prefer short, clear sentences a cashier can act on.
4. Repeat the key numbers from LEDGER_JSON exactly.
5. Do not mention being an AI model or cloud services."""

_SYSTEM_FR = """Vous êtes DukaBind, un assistant de boutique hors ligne pour les comptoirs MSME africains.
Vous répondez UNIQUEMENT à partir de LEDGER_JSON fourni par l'application.
Règles :
1. N'inventez jamais de montants, de limites de crédit, de soldes ou de quantités en stock.
2. Si LEDGER_JSON est vide ou signale une donnée manquante, dites que l'on doit demander au propriétaire.
3. Préférez des phrases courtes et claires qu'un caissier peut appliquer.
4. Répétez exactement les chiffres clés de LEDGER_JSON.
5. Ne mentionnez pas être un modèle d'IA ni des services cloud."""

_SYSTEM_SW = (
    "Wewe ni DukaBind, msaidizi wa duka wa kaunta za MSME za Kiafrika. "
    "Jibu kwa Kiswahili kwa sentensi fupi. Usibuni kiasi chochote."
)

_SYSTEMS = {"en": _SYSTEM_EN, "fr": _SYSTEM_FR, "sw": _SYSTEM_SW}

_USER_TAIL = {
    "en": (
        "Rewrite BINDER_DECISION as a short cashier-facing reply.\n"
        "Rules:\n"
        "- Keep every number identical to BINDER_DECISION.\n"
        "- Do not rename projected_outstanding as outstanding.\n"
        "- Do not add new figures or omit the max-qty line if present.\n"
        "- Do not invent missing ledger fields."
    ),
    "fr": (
        "Réécrivez BINDER_DECISION en une courte réponse destinée au caissier.\n"
        "Règles :\n"
        "- Gardez chaque chiffre identique à BINDER_DECISION.\n"
        "- Ne renommez pas projected_outstanding en outstanding.\n"
        "- N'ajoutez pas de nouveaux chiffres et n'omettez pas la ligne de quantité "
        "maximale si elle est présente.\n"
        "- N'inventez pas de champs manquants du registre."
    ),
    "sw": (
        "Andika upya BINDER_DECISION kama jibu fupi la mkarani. "
        "Weka kila namba sawa na BINDER_DECISION. Usiongeze namba mpya."
    ),
}


def build_narration_prompt(
    *,
    lang: str,
    staff_question: str,
    binder_message: str,
    citation_json: str,
) -> list[dict[str, str]]:
    """Chat messages for llama-server /v1/chat/completions."""
    system = _SYSTEMS.get(lang, _SYSTEM_EN)
    tail = _USER_TAIL.get(lang, _USER_TAIL["en"])
    ledger = "" if lang == "sw" else f"\nLEDGER_JSON:\n{citation_json}\n"
    user = (
        f"STAFF_QUESTION:\n{staff_question}\n\n"
        f"BINDER_DECISION (authoritative — copy these facts):\n{binder_message}\n"
        f"{ledger}\n"
        f"{tail}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
