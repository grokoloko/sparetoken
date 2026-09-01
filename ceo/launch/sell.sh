#!/usr/bin/env bash
# Pulso oficial de VENDA: 11:30 America/Sao_Paulo.
# REGRA ZERO: faixa + cursor-agent (print + trust + force). Publicar ou enfileirar.
# Anotar sem agent = falhou. Wrapper NUNCA git write. Ver ceo/GIT.md.
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

resolve_agent() {
  if [[ -n "${CURSOR_AGENT_BIN:-}" && -x "${CURSOR_AGENT_BIN}" ]]; then
    printf '%s\n' "${CURSOR_AGENT_BIN}"
    return 0
  fi
  local c
  for c in agent cursor-agent "${HOME}/.local/bin/agent" "${HOME}/.local/bin/cursor-agent"; do
    if [[ -x "$c" ]]; then
      printf '%s\n' "$c"
      return 0
    fi
    if command -v "$c" >/dev/null 2>&1; then
      command -v "$c"
      return 0
    fi
  done
  return 1
}

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
} | tee -a "$LOG"

AGENT_BIN="$(resolve_agent || true)"
if [[ -z "${AGENT_BIN}" ]]; then
  {
    echo "PULSE_FAIL $STAMP AGENT: missing (cursor-agent not on PATH)"
    echo "NEXT: do not stamp SELL_OK. Put agent on this host, then rerun."
  } | tee -a "$LOG" >&2
  exit 1
fi

PROMPT=$(cat <<'EOF'
You are the sparetoken CEO on the official 11:30 America/Sao_Paulo SELL pulse.

Read and follow: ceo/CEO.md, ceo/HEARTBEAT.md, ceo/VENUES.md, ceo/QUEUE.md, ceo/launch/sell.md, ceo/launch/AGENTS.md, ceo/GIT.md, AGENTS.md, .cursor/rules/anonimato.mdc.

Rule zero:
1. You exist and you run real intelligence.
2. One venue from VENUES.md (not the whole list). Publish the link with UTM, or write a real queue line if the channel needs a human.
3. Annotating without publishing or queueing is a failed pulse.
4. Plant D+8 sales work in SALES-7D.md.
5. No X cookie on this host. No reply farm. No second Pix. No PII.
6. Git identity of any commit is sparetoken <sparetoken-shop@users.noreply.github.com>. Never a personal GitHub account.

If you cannot publish or queue, say why and exit non-zero.
EOF
)

unset -f git || true
set +e
"${AGENT_BIN}" -p --trust --force --workspace "${ROOT}" --model "${CURSOR_AGENT_MODEL:-cursor-grok-4.6-high-fast}" "${PROMPT}"
AGENT_RC=$?
set -e

{
  echo "AGENT_BIN=${AGENT_BIN} rc=${AGENT_RC}"
  echo "{\"day\":\"$DAY\",\"pulse\":\"sell\",\"status\":\"queued-or-published\",\"note\":\"one venue, one UTM, X warmup only\"}" >> "$QUEUE"
  echo "QUEUED $DAY → $QUEUE"
  if [[ "${AGENT_RC}" -ne 0 ]]; then
    echo "PULSE_FAIL $STAMP AGENT: rc=${AGENT_RC}"
    echo "NEXT: 11:30 is not SUCCESS until the agent publishes or queues for real."
  else
    echo "SELL_OK $STAMP"
    echo "AGENT: on"
    echo "NEXT: 11:30 tomorrow = one publish. 23:30 tonight = one feature."
    echo "X: no replies. Cookie stays off this host."
  fi
} | tee -a "$LOG"

exit "${AGENT_RC}"
