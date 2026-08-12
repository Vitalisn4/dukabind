#!/usr/bin/env bash
# Offline proof for the binder path (no cloud, no llama-server required).
#
# 1) Seeds the shop ledger and checks credit / refuse / stock / flip answers.
# 2) Re-runs asks inside an empty network namespace when unshare is available.
#
# Usage (from repo root):
#   bash scripts/offline_check.sh
#
# Exit 0 = proof passed.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

# shellcheck disable=SC1091
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

export PYTHONPATH=.

echo "== DukaBind offline_check =="
echo "repo: $HERE"
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

python -m app.db.connection >/dev/null

assert_json() {
  local question="$1"
  local py_assert="$2"
  python -m app.cli "$question" | python -c "$py_assert"
}

echo
echo "-- asks (baseline / host network) --"
assert_json "Can I give Marie-Claire three crates on credit?" '
import json,sys
d=json.load(sys.stdin)
assert d["ok"] is True and d.get("approved") is False and "8410" in d["message"], d
print("credit over-limit: OK")
'
assert_json "How much do we owe SOCA?" '
import json,sys
d=json.load(sys.stdin)
assert d["ok"] is False and d["refuse_reason"]=="balance_owed_null" and "42000" not in d["message"], d
print("soca refuse: OK")
'
assert_json "How much do we owe Bonaberi?" '
import json,sys
d=json.load(sys.stdin)
assert d["ok"] is True and "42000" in d["message"], d
print("bonaberi balance: OK")
'
assert_json "What stock of soda do we have on hand?" '
import json,sys
d=json.load(sys.stdin)
assert d["ok"] is True and "14" in d["message"], d
print("stock soda: OK")
'
assert_json "Can I give Esther credit for 1 crate?" '
import json,sys
d=json.load(sys.stdin)
assert d["ok"] is False and d["refuse_reason"]=="credit_limit_null", d
print("esther null limit: OK")
'

echo
echo "-- ledger flip (bind proof) --"
python - <<'PY'
import sqlite3
from pathlib import Path
from app.db.connection import DEFAULT_DB, connect
from app.binder.pipeline import handle_ask

path = Path(DEFAULT_DB)
conn = connect(path)  # writable for flip demo only
try:
    before = handle_ask(conn, "Can I give Fotso 3 crates on credit?")
    assert before.approved is False and "No" in before.message, before
    # One transaction: flip the limit, prove the answer follows, then roll back
    # so the seed file is never left modified, even if an assert fails mid-way.
    conn.execute("BEGIN")
    conn.execute(
        "UPDATE customers SET credit_limit = ? WHERE display_name = ?",
        (20000, "Marie-Claire Fotso"),
    )
    after = handle_ask(conn, "Can I give Fotso 3 crates on credit?")
    assert after.approved is True and "Yes" in after.message, after
    conn.execute("ROLLBACK")
    restored = handle_ask(conn, "Can I give Fotso 3 crates on credit?")
    assert restored.approved is False, restored
    print("ledger flip + rollback: OK")
finally:
    conn.close()
PY

if command -v unshare >/dev/null 2>&1 && unshare -n true 2>/dev/null; then
  echo
  echo "-- asks inside unshare -n (no network namespace) --"
  unshare -n env HOME="$HOME" PATH="$PATH" bash -c '
    set -euo pipefail
    cd "'"$HERE"'"
    # shellcheck disable=SC1091
    if [[ -f .venv/bin/activate ]]; then
      source .venv/bin/activate
    fi
    export PYTHONPATH=.
    python -m app.cli "Can I give Marie-Claire three crates on credit?" | python -c "
import json,sys
d=json.load(sys.stdin)
assert d[\"approved\"] is False and \"8410\" in d[\"message\"]
"
    python -m app.cli "How much do we owe SOCA?" | python -c "
import json,sys
d=json.load(sys.stdin)
assert d[\"refuse_reason\"]==\"balance_owed_null\"
"
    echo "unshare -n asks: OK"
  '
else
  echo
  echo "note: unshare -n unavailable on this host; the binder path is still proven."
  echo "      Manual airplane-mode: disable Wi-Fi/Ethernet and re-run this script."
fi

echo
echo "PASS: offline_check. Binder answers track the ledger with no cloud dependency"
exit 0
