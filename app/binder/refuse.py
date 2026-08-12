"""Fail-closed refuse rules (control C4).

If a required field is NULL/missing, we refuse — the LLM must not invent amounts.
Cashier messages are localized (English / French / Swahili); the deterministic
message is authoritative in every language.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.binder.intents import Intent


@dataclass(frozen=True)
class BinderResult:
    """Authoritative binder answer: message, citations, and optional refuse reason.

    ``ok`` means the binder finished a lookup/decision (or a structured refuse).
    ``approved`` is set only for credit decisions: True = within limit, False = over
    limit. Other intents leave it None so consumers do not treat ``ok`` as approval.
    """

    ok: bool
    intent: Intent
    lang: str
    citation_rows: list[dict[str, Any]]
    message: str
    refuse_reason: str | None = None
    approved: bool | None = None


def _t(lang: str, en: str, fr: str, sw: str) -> str:
    """Pick the localized template; English is the fallback for unknown langs."""
    return {"en": en, "fr": fr, "sw": sw}.get(lang, en)


# Internal ``not_found`` identifiers from the pipeline are translated so the
# localized message never mixes languages ("… pour customer"). Ledger names
# supplied by the user are preserved unchanged — they are not keys here.
_NOT_FOUND_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "customer": "customer",
        "supplier": "supplier",
        "sku": "product",
        "quantity": "quantity",
        "unit_price": "unit price",
    },
    "fr": {
        "customer": "client",
        "supplier": "fournisseur",
        "sku": "produit",
        "quantity": "quantité",
        "unit_price": "prix unitaire",
    },
    "sw": {
        "customer": "mteja",
        "supplier": "msambazaji",
        "sku": "bidhaa",
        "quantity": "idadi",
        "unit_price": "bei ya kitengo",
    },
}


def _label(lang: str, what: str) -> str:
    """Localize an internal identifier; leave user-supplied names untouched."""
    return _NOT_FOUND_LABELS.get(lang, _NOT_FOUND_LABELS["en"]).get(what, what)


def refuse_credit_missing_limit(lang: str, name: str) -> BinderResult:
    """Refuse when credit_limit is NULL — never invent a limit."""
    return BinderResult(
        ok=False,
        intent=Intent.CREDIT_CHECK,
        lang=lang,
        citation_rows=[],
        refuse_reason="credit_limit_null",
        message=_t(
            lang,
            f"No credit limit on file for {name} — ask the owner.",
            f"Pas de limite de crédit enregistrée pour {name} — demandez au propriétaire.",
            f"Hakuna kikomo cha kreti kwa {name} — uliza mmiliki.",
        ),
    )


def refuse_credit_missing_outstanding(lang: str, name: str) -> BinderResult:
    """Refuse when outstanding is NULL — never invent a balance."""
    return BinderResult(
        ok=False,
        intent=Intent.CREDIT_CHECK,
        lang=lang,
        citation_rows=[],
        refuse_reason="outstanding_null",
        message=_t(
            lang,
            f"No outstanding balance on file for {name} — ask the owner.",
            f"Pas de solde impayé enregistré pour {name} — demandez au propriétaire.",
            f"Hakuna salio linalodaiwa kwa {name} — uliza mmiliki.",
        ),
    )


def refuse_supplier_missing_balance(lang: str, name: str) -> BinderResult:
    """Refuse when balance_owed is NULL — never invent an amount."""
    return BinderResult(
        ok=False,
        intent=Intent.SUPPLIER_BALANCE,
        lang=lang,
        citation_rows=[],
        refuse_reason="balance_owed_null",
        message=_t(
            lang,
            f"Amount owed to {name} is not on file — ask the owner.",
            f"Le montant dû à {name} n'est pas enregistré — demandez au propriétaire.",
            f"Kiasi kinachodaiwa na {name} hakipo kwenye kumbukumbu — uliza mmiliki.",
        ),
    )


def refuse_not_found(lang: str, what: str) -> BinderResult:
    """Refuse when the named customer, supplier, or SKU is absent.

    ``what`` may be an internal identifier (``customer``, ``supplier``,
    ``sku``, ``quantity``, ``unit_price``) — localized — or a user-supplied
    ledger name, which is preserved verbatim.
    """
    what = _label(lang, what)
    return BinderResult(
        ok=False,
        intent=Intent.UNKNOWN,
        lang=lang,
        citation_rows=[],
        refuse_reason="not_found",
        message=_t(
            lang,
            f"No ledger row found for {what} — ask the owner.",
            f"Aucune ligne de registre trouvée pour {what} — demandez au propriétaire.",
            f"Hakuna rekodi ya {what} — uliza mmiliki.",
        ),
    )


def refuse_unknown(lang: str) -> BinderResult:
    """Refuse intents outside credit, supplier balance, and stock."""
    return BinderResult(
        ok=False,
        intent=Intent.UNKNOWN,
        lang=lang,
        citation_rows=[],
        refuse_reason="unknown_intent",
        message=_t(
            lang,
            "I can only answer credit, supplier balances, or stock from this shop ledger.",
            "Je ne peux répondre qu'aux questions de crédit, de soldes fournisseurs "
            "ou de stock de ce registre de la boutique.",
            "Naweza kujibu tu maswali ya kreti, salio la wasambazaji, au hifadhi "
            "kutoka kwenye rekodi za duka.",
        ),
    )


def credit_decision(
    lang: str,
    row: dict[str, Any],
    qty: int,
    unit_price: int,
) -> BinderResult:
    """Deterministic arithmetic — do not leave this to the LLM."""
    if qty < 1 or unit_price <= 0:
        return refuse_not_found(lang, "quantity" if qty < 1 else "unit_price")

    limit = row["credit_limit"]
    if limit is None:
        return refuse_credit_missing_limit(lang, row["display_name"])

    outstanding = row["outstanding"]
    if outstanding is None:
        return refuse_credit_missing_outstanding(lang, row["display_name"])

    outstanding = int(outstanding)
    limit_i = int(limit)
    add = qty * unit_price
    projected = outstanding + add
    currency = row.get("currency") or "XAF"
    citation = [
        dict(row),
        {
            "sku_unit_price": unit_price,
            "qty_requested": qty,
            "projected_outstanding": projected,
            "currency": currency,
        },
    ]

    if projected > limit_i:
        over = projected - limit_i
        room = limit_i - outstanding
        max_qty = max(0, room // unit_price) if unit_price else 0
        return BinderResult(
            ok=True,
            intent=Intent.CREDIT_CHECK,
            lang=lang,
            citation_rows=citation,
            approved=False,
            message=_t(
                lang,
                (
                    f"No — {qty} × {unit_price} = {add}; "
                    f"{outstanding} + {add} = {projected} exceeds limit {limit_i} "
                    f"by {over} {currency}. "
                    f"Max qty within limit: {max_qty}."
                ),
                (
                    f"Non — {qty} × {unit_price} = {add} ; "
                    f"{outstanding} + {add} = {projected} dépasse la limite "
                    f"{limit_i} de {over} {currency}. "
                    f"Quantité maximale dans la limite : {max_qty}."
                ),
                (
                    f"Hapana — {qty} × {unit_price} = {add}; "
                    f"{outstanding} + {add} = {projected} inazidi kikomo {limit_i} "
                    f"kwa {over} {currency}. "
                    f"Idadi ya juu ndani ya kikomo: {max_qty}."
                ),
            ),
        )

    return BinderResult(
        ok=True,
        intent=Intent.CREDIT_CHECK,
        lang=lang,
        citation_rows=citation,
        approved=True,
        message=_t(
            lang,
            (
                f"Yes — {qty} × {unit_price} = {add}; "
                f"projected outstanding {projected} ≤ limit {limit_i} {currency}."
            ),
            (
                f"Oui — {qty} × {unit_price} = {add} ; "
                f"solde prévisionnel {projected} ≤ limite {limit_i} {currency}."
            ),
            (
                f"Ndiyo — {qty} × {unit_price} = {add}; "
                f"salio linalotarajiwa {projected} ≤ kikomo {limit_i} {currency}."
            ),
        ),
    )
