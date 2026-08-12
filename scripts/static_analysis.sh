#!/usr/bin/env bash
# Static analysis gate: ruff + bandit + shellcheck in one pass.
#
# Usage:
#   bash scripts/static_analysis.sh
#
# Exit 0 = every tool is clean (run before commit / PR).

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

# shellcheck disable=SC1091
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

echo "== ruff =="
ruff check app tests evals scripts

echo
echo "== bandit (shipped code, no exclusions) =="
bandit -q -r app evals

echo
echo "== bandit (tests, skip assert_used; pytest is assert-based) =="
bandit -q -r tests -s B101

echo
echo "== shellcheck =="
shellcheck scripts/*.sh download_model.sh

echo
echo "PASS: static analysis clean (ruff + bandit + shellcheck)"
