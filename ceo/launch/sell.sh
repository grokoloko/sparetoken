#!/usr/bin/env bash
# Pulso oficial de VENDA: 11:30 America/Sao_Paulo.
# Cursor Agent primeiro. SELL_OK só com URL público verificado fora do Twitter.
# O wrapper não faz git write.
set -euo pipefail
if [[ "${1:-}" == "commit" || "${1:-}" == "push" ]]; then
  echo "sell: git write forbidden in the wrapper" >&2
  exit 78
fi
git() {
  echo "heartbeat: git is forbidden in the wrapper (ceo/GIT.md) — the agent process is separate" >&2
  return 78
}
export TZ=America/Sao_Paulo
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAMP="$(date +%Y-%m-%dT%H:%M:%S%z)"
DAY="$(date +%Y-%m-%d)"
LOG="${WDTSOT_SELL_LOG:-$ROOT/data/sell.log}"
QUEUE="${WDTSOT_SELL_QUEUE:-$ROOT/data/sell-queue.jsonl}"
mkdir -p "$(dirname "$LOG")" "$(dirname "$QUEUE")"

{
  echo "=== sparetoken SELL $STAMP ==="
  echo "root=$ROOT"
  echo
  echo "--- sales 7 days ---"
  cat "$ROOT/ceo/SALES-7D.md"
  echo
  echo "--- venues ---"
  cat "$ROOT/ceo/VENUES.md"
  echo
  echo "--- queue ---"
  cat "$ROOT/ceo/QUEUE.md"
  echo
  echo "--- track ---"
  if [[ -x "$ROOT/ceo/launch/track-report.sh" ]]; then
    WDTSOT_DB="${WDTSOT_DB:-$ROOT/data/wdtsot.sqlite}" "$ROOT/ceo/launch/track-report.sh" || true
  fi
  echo
  echo "--- cursor agent ---"
} | tee -a "$LOG"

"$ROOT/ceo/launch/run-cursor-agent.sh" sell 2>&1 | tee -a "$LOG"

{
  echo "--- publish (verify or die) ---"
} | tee -a "$LOG"

if ! python3 "$ROOT/scripts/sell_publish.py" 2>&1 | tee -a "$LOG"; then
  echo "SELL_DEAD $STAMP — no live URL outside Twitter" | tee -a "$LOG"
  exit 78
fi

{
  echo "{\"day\":\"$DAY\",\"pulse\":\"sell\",\"status\":\"verified-live\",\"note\":\"url passed verify_sell_live\"}" >> "$QUEUE"
  echo "VERIFIED $DAY → $QUEUE"
  echo "SELL_OK $STAMP"
  echo "AGENT: on"
  echo "NEXT: 11:30 tomorrow = one live URL. 23:30 tonight = one feature."
  echo "X: warmup only. Cookie stays off this host. X is never the proof."
} | tee -a "$LOG"

exit 0
