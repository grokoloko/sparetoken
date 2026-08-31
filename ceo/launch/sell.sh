#!/usr/bin/env bash
# Pulso oficial de VENDA: 11:30 America/Sao_Paulo.
# Publicar ou enfileirar. Anotar sem sair = falhou.
# NUNCA git write. Ver ceo/GIT.md.
set -euo pipefail
if [[ "${1:-}" == "commit" || "${1:-}" == "push" ]]; then
  echo "sell: git write forbidden" >&2
  exit 78
fi
git() {
  echo "heartbeat: git is forbidden on the VPS pulse (ceo/GIT.md)" >&2
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
  echo "{\"day\":\"$DAY\",\"pulse\":\"sell\",\"status\":\"queued-or-published\",\"note\":\"one venue, one UTM, X warmup only\"}" >> "$QUEUE"
  echo "QUEUED $DAY → $QUEUE"
  echo "SELL_OK $STAMP"
  echo "NEXT: 11:30 tomorrow = one publish. 23:30 tonight = one feature."
  echo "X: no replies. Cookie stays off this host."
} | tee -a "$LOG"

exit 0
