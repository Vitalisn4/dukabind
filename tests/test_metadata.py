"""Contest-claims validation: ``metadata.json`` must match what DukaBind proves.

Runs in CI under pytest so a drift in the public claims fails the build.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "metadata.json"


@pytest.fixture()
def meta() -> dict:
    return json.loads(METADATA.read_text(encoding="utf-8"))


def test_domain_locked(meta: dict) -> None:
    assert meta["domain"] == "corporate_enterprise"


def test_language_scope_matches_shipped_tracks(meta: dict) -> None:
    # English is the primary language; French (Cameroon official language) and
    # Swahili (pan-African) binder tracks are shipped and tested.
    assert meta["language_scope"] == ["en", "fr", "sw"]


def test_claims_match_what_is_proven(meta: dict) -> None:
    # african_alpha_claim = Cameroon MSME offline use-case; budget laptop measured.
    assert meta["african_alpha_claim"] is True
    assert meta["budget_laptop_claim"] is True


def test_submitter_identity(meta: dict) -> None:
    assert meta["submitter"]["name"]
    assert meta["submitter"]["github_handle"] == "Vitalisn4"
    assert "@" in meta["submitter"]["email"]


def test_exactly_two_test_prompts(meta: dict) -> None:
    prompts = meta["test_prompts"]
    assert len(prompts) == 2
    for p in prompts:
        assert p["prompt_id"].startswith("tp_")
        # Both prompts must be ledger-grounded (mention a ledger field).
        assert (
            "credit_limit" in p["prompt"]
            or "balance_owed" in p["prompt"]
            or "on_hand" in p["prompt"]
        )


def test_submission_prompts_disjoint_from_heldout(meta: dict) -> None:
    """T13: the two submission staff asks must not appear in the held-out set."""
    held = json.loads(
        (ROOT / "evals" / "heldout" / "prompts.json").read_text(encoding="utf-8")
    )
    held_asks = {p["prompt"].strip().lower() for p in held["prompts"]}
    for p in meta["test_prompts"]:
        ask = re.search(r"Staff ask: (.+?)\? ", p["prompt"])
        assert ask is not None, f"{p['prompt_id']} lacks the 'Staff ask: ...? ' frame"
        staff_ask = (ask.group(1).strip().lower() + "?").replace("  ", " ")
        assert staff_ask not in held_asks, (
            f"{p['prompt_id']} staff ask overlaps the held-out set (T13)"
        )


def test_model_runtime_is_llama_cpp(meta: dict) -> None:
    assert meta["model"]["runtime"] == "llama.cpp"
    assert meta["model"]["quantization"] == "GGUF Q4_K_M"
