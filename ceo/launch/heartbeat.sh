#!/usr/bin/env bash
# Pulso oficial: 23:30 America/Sao_Paulo.
# NÃO invoca cursor-agent enquanto o login da VPS for conta pessoal.
set -euo pipefail
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
  echo "PULSE_OK $STAMP"
  echo "AGENT: off (VPS cursor-agent is a personal login — anonymity lock)"
  echo "NEXT: 23:30 tomorrow. Ship one feature. Do not touch pay.py."
} | tee -a "$LOG"

exit 0
