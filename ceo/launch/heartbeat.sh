#!/usr/bin/env bash
# Pulso oficial: 23:30 America/Sao_Paulo.
# REGRA ZERO: unittest verde, DEPOIS cursor-agent (print + trust + force).
# Sem agent = falha mortal. Unittest sozinho NÃO é SUCCESS.
# Wrapper NUNCA git commit / push / tag. Ver ceo/GIT.md.
set -euo pipefail
if [[ "${1:-}" == "commit" || "${1:-}" == "push" ]]; then
  echo "heartbeat: git write forbidden" >&2
  exit 78
fi
git() {
  echo "heartbeat: git is forbidden on the VPS pulse (ceo/GIT.md)" >&2
  return 78
}
export TZ=America/Sao_Paulo
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAMP="$(date +%Y-%m-%dT%H:%M:%S%z)"
LOG="${WDTSOT_HEARTBEAT_LOG:-$ROOT/data/heartbeat.log}"
mkdir -p "$(dirname "$LOG")"

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
} | tee -a "$LOG"

AGENT_BIN="$(resolve_agent || true)"
if [[ -z "${AGENT_BIN}" ]]; then
  {
    echo "PULSE_FAIL $STAMP AGENT: missing (cursor-agent not on PATH)"
    echo "NEXT: do not stamp PULSE_OK. Put agent on this host, then rerun."
  } | tee -a "$LOG" >&2
  exit 1
fi

PROMPT=$(cat <<'EOF'
You are the sparetoken CEO on the official 23:30 America/Sao_Paulo PRODUCT pulse.

Read and follow: ceo/CEO.md, ceo/HEARTBEAT.md, ceo/launch/AGENTS.md, ceo/GIT.md, ceo/HARNESS.md, ceo/PAYMENT.md, AGENTS.md, .cursor/rules/anonimato.mdc.

Rule zero:
1. You exist and you run real intelligence (review, research, new ideas).
2. Unittest already ran green in this process. If you change code, run python3 -m unittest discover -s tests -v again. Red = stop.
3. Ship ONE small tested feature for tonight. Tests-only is a failed pulse.
4. Plant D+8 product work.
5. Any git identity is sparetoken <sparetoken-shop@users.noreply.github.com>. Never a personal GitHub account. Never a tool Co-authored-by handle.
6. Do not touch pay.py. No second Pix. No PII.

If you cannot ship, say why and exit non-zero.
EOF
)

unset -f git || true
set +e
"${AGENT_BIN}" -p --trust --force --workspace "${ROOT}" --model "${CURSOR_AGENT_MODEL:-cursor-grok-4.6-high-fast}" "${PROMPT}"
AGENT_RC=$?
set -e

{
  echo "AGENT_BIN=${AGENT_BIN} rc=${AGENT_RC}"
  if [[ "${AGENT_RC}" -ne 0 ]]; then
    echo "PULSE_FAIL $STAMP AGENT: rc=${AGENT_RC}"
    echo "NEXT: 23:30 is not SUCCESS until the agent ships."
  else
    echo "PULSE_OK $STAMP"
    echo "AGENT: on"
    echo "NEXT: 23:30 tomorrow = one feature. 11:30 = one publish. Do not touch pay.py."
  fi
} | tee -a "$LOG"

exit "${AGENT_RC}"
