#!/usr/bin/env bash
# Pulso oficial: 23:30 America/Sao_Paulo.
# Unittest, depois Cursor Agent de verdade. Sem agent = pulso morto.
# O wrapper não faz git write. O agent (filho) pode, só como sparetoken-shop.
set -euo pipefail
if [[ "${1:-}" == "commit" || "${1:-}" == "push" ]]; then
  echo "heartbeat: git write forbidden in the wrapper" >&2
  exit 78
fi
git() {
  echo "heartbeat: git is forbidden in the wrapper (ceo/GIT.md) — the agent process is separate" >&2
  return 78
}
export TZ=America/Sao_Paulo
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAMP="$(date +%Y-%m-%dT%H:%M:%S%z)"
LOG="${WDTSOT_HEARTBEAT_LOG:-$ROOT/data/heartbeat.log}"
mkdir -p "$(dirname "$LOG")"

{
  echo "=== sparetoken heartbeat $STAMP ==="
  echo "root=$ROOT"
  echo
  echo "--- 7 days ---"
  cat "$ROOT/ceo/ROADMAP-7D.md"
  echo
  echo "--- payment lock ---"
  head -n 14 "$ROOT/ceo/PAYMENT.md"
  echo
  echo "--- unittest ---"
  (cd "$ROOT" && python3 -m unittest discover -s tests -v)
  echo
  echo "--- cursor agent ---"
} | tee -a "$LOG"

"$ROOT/ceo/launch/run-cursor-agent.sh" heartbeat 2>&1 | tee -a "$LOG"

{
  echo "PULSE_OK $STAMP"
  echo "AGENT: on"
  echo "NEXT: 23:30 tomorrow = one feature. 11:30 = one publish. Do not touch pay.py."
} | tee -a "$LOG"

exit 0
