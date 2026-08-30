#!/usr/bin/env bash
# Guest SSH → isolated Cursor Agent (Grok 4.6 High Fast) under development/guest-sessions
set -euo pipefail

if [[ ! -t 0 ]]; then
  echo "Este acesso e interativo. Use: ssh -t agent-guest@HOST" >&2
  echo "Para retomar: ssh -t agent-guest@HOST resume <session-id|chat-uuid>" >&2
  exit 1
fi

GUEST_ROOT="/home/ubuntu/development/guest-sessions"
MODEL="cursor-grok-4.6-high-fast"
AGENT_BIN="/home/ubuntu/.local/bin/agent"
REAL_HOME="/home/ubuntu"
RESOLVE_BIN="/opt/cursor-agent-tunnel/resolve-resume.py"
GATE_BIN="/opt/cursor-agent-tunnel/tunnel-gate.py"
WATCH_PID=""

mkdir -p "$GUEST_ROOT"

TUNNEL_CMD="${1:-${SSH_ORIGINAL_COMMAND:-}}"
RESUME_TOKEN=""
GUEST_INFO_JSON="{}"
IS_RESUME=0

if [[ -n "$TUNNEL_CMD" ]]; then
  if ! RESUME_TOKEN="$(/usr/bin/python3 "$RESOLVE_BIN" --parse "$TUNNEL_CMD")"; then
    echo "Comando invalido. Use: ssh -t agent-guest@HOST resume <session-id|chat-uuid>" >&2
    exit 1
  fi
else
  GUEST_INFO_JSON="$(/usr/bin/python3 /opt/cursor-agent-tunnel/collect-guest.py)"
  RESUME_TOKEN="$(
    /usr/bin/python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("resume") or "")' \
      "$GUEST_INFO_JSON"
  )"
fi

write_cli_config() {
  local state_dir="$1"
  local workspace="$2"
  if [[ ! -f "${state_dir}/cli-config.json" ]]; then
    cat > "${state_dir}/cli-config.json" <<'JSON'
{
  "permissions": {
    "allow": [
      "Shell(**)",
      "Read(**)",
      "Write(**)",
      "Edit(**)",
      "Delete(**)",
      "Glob(**)",
      "Grep(**)",
      "SemanticSearch(**)"
    ],
    "deny": []
  },
  "approvalMode": "allowlist",
  "sandbox": {
    "mode": "enabled",
    "networkAccess": "user_config_with_defaults"
  },
  "network": {
    "useHttp1ForAgent": false
  },
  "version": 1
}
JSON
  fi
  mkdir -p "${workspace}/.cursor"
  if [[ ! -f "${workspace}/.cursor/cli.json" ]]; then
    cat > "${workspace}/.cursor/cli.json" <<'JSON'
{
  "permissions": {
    "allow": [
      "Shell(**)",
      "Read(**)",
      "Write(**)",
      "Edit(**)",
      "Delete(**)",
      "Glob(**)",
      "Grep(**)"
    ],
    "deny": []
  }
}
JSON
  fi
  /usr/bin/python3 - "${state_dir}/cli-config.json" <<'PY'
import json, sys
path = sys.argv[1]
try:
    data = json.loads(open(path, encoding="utf-8").read())
except Exception:
    data = {}
data["statusLine"] = {
    "type": "command",
    "command": "/usr/bin/python3 /opt/cursor-agent-tunnel/wdtsot_statusline.py",
    "padding": 1,
    "updateIntervalMs": 2000,
    "timeoutMs": 1500,
}
open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2) + "\n")
PY
}

stop_live_session() {
  local dir="$1"
  local workspace="$2"
  local pid
  local me=$$
  while read -r pid; do
    [[ -z "${pid:-}" || "$pid" == "$me" ]] && continue
    kill "$pid" 2>/dev/null || true
  done < <(pgrep -f -- "--bind ${dir} ${dir}" || true)
  while read -r pid; do
    [[ -z "${pid:-}" || "$pid" == "$me" ]] && continue
    kill "$pid" 2>/dev/null || true
  done < <(pgrep -f -- "--workspace ${workspace}" || true)
  sleep 0.8
}

SSH_PEER="${SSH_CLIENT:-}"
SSH_CONN="${SSH_CONNECTION:-}"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
STARTED_MS="$(date +%s%3N)"
CHAT_ID=""

if [[ -n "$RESUME_TOKEN" ]]; then
  IS_RESUME=1
  RESOLVED="$(/usr/bin/python3 "$RESOLVE_BIN" --resolve "$RESUME_TOKEN")" || {
    echo "Nao foi possivel retomar: token ${RESUME_TOKEN}" >&2
    exit 1
  }
  SESSION_ID="$(/usr/bin/python3 -c 'import json,sys; print(json.loads(sys.argv[1])["session_id"])' "$RESOLVED")"
  SESSION_DIR="$(/usr/bin/python3 -c 'import json,sys; print(json.loads(sys.argv[1])["session_dir"])' "$RESOLVED")"
  WORKSPACE="$(/usr/bin/python3 -c 'import json,sys; print(json.loads(sys.argv[1])["workspace"])' "$RESOLVED")"
  LOG_DIR="$(/usr/bin/python3 -c 'import json,sys; print(json.loads(sys.argv[1])["log_dir"])' "$RESOLVED")"
  CURSOR_STATE="$(/usr/bin/python3 -c 'import json,sys; print(json.loads(sys.argv[1])["cursor_state"])' "$RESOLVED")"
  CHAT_ID="$(/usr/bin/python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("chat_id") or "")' "$RESOLVED")"
  mkdir -p "$WORKSPACE" "$LOG_DIR" "$CURSOR_STATE"
  write_cli_config "$CURSOR_STATE" "$WORKSPACE"
  stop_live_session "$SESSION_DIR" "$WORKSPACE"
  {
    echo "resume at=${STARTED_AT} peer=${SSH_PEER} token=${RESUME_TOKEN} chat=${CHAT_ID}"
  } >> "${LOG_DIR}/session.log"
else
  SESSION_ID="session-$(date -u +%Y%m%d-%H%M%S)-$(openssl rand -hex 3)"
  SESSION_DIR="${GUEST_ROOT}/${SESSION_ID}"
  WORKSPACE="${SESSION_DIR}/workspace"
  LOG_DIR="${SESSION_DIR}/logs"
  CURSOR_STATE="${SESSION_DIR}/cursor-state"
  mkdir -p "$WORKSPACE" "$LOG_DIR" "$CURSOR_STATE"
  write_cli_config "$CURSOR_STATE" "$WORKSPACE"
  cat > "${WORKSPACE}/README.txt" <<TXT
Workspace isolado desta sessão SSH.
Só arquivos dentro desta pasta podem ser alterados.
Sessão: ${SESSION_ID}
Modelo: ${MODEL}
TXT
fi

export GUEST_INFO_JSON
export GUEST_ROOT MODEL AGENT_BIN REAL_HOME
export SESSION_ID SESSION_DIR WORKSPACE LOG_DIR CURSOR_STATE
export STARTED_AT STARTED_MS SSH_PEER SSH_CONN IS_RESUME CHAT_ID

if [[ "$IS_RESUME" -eq 0 ]]; then
  python3 - <<'PY'
import json, os
from pathlib import Path

guest = {}
raw = os.environ.get("GUEST_INFO_JSON") or "{}"
try:
    guest = json.loads(raw)
except json.JSONDecodeError:
    guest = {}

record = {
  "session_id": os.environ["SESSION_ID"],
  "session_dir": os.environ["SESSION_DIR"],
  "workspace": os.environ["WORKSPACE"],
  "model": os.environ["MODEL"],
  "started_at": os.environ["STARTED_AT"],
  "started_at_ms": int(os.environ["STARTED_MS"]),
  "ssh_client": os.environ.get("SSH_PEER", ""),
  "ssh_connection": os.environ.get("SSH_CONN", ""),
  "remote_user": "agent-guest",
  "isolation": "bubblewrap+sandbox",
  "guest": {
    "name": guest.get("name", ""),
    "whatsapp": guest.get("whatsapp", ""),
    "email": guest.get("email", ""),
  },
}

logs = Path(os.environ["LOG_DIR"])
logs.joinpath("session.start.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
logs.joinpath("session.log").write_text(
    f"start model={record['model']} peer={record['ssh_client']} "
    f"guest={record['guest']['name']!r} wa={record['guest']['whatsapp']} email={record['guest']['email']}\n"
)

guest_row = {
    "session_id": record["session_id"],
    "started_at": record["started_at"],
    "name": record["guest"]["name"],
    "whatsapp": record["guest"]["whatsapp"],
    "email": record["guest"]["email"],
    "ssh_client": record["ssh_client"],
    "model": record["model"],
}
root = Path(os.environ["GUEST_ROOT"])
with (root / "guests.jsonl").open("a", encoding="utf-8") as f:
    f.write(json.dumps(guest_row, ensure_ascii=False) + "\n")
PY
fi

if ! /usr/bin/python3 "$GATE_BIN" gate; then
  echo "wdtsot: sessao nao liberada." >&2
  exit 4
fi

cleanup() {
  local code=$?
  export AGENT_EXIT_CODE="$code"
  if [[ -n "${WATCH_PID:-}" ]]; then
    kill "$WATCH_PID" 2>/dev/null || true
    wait "$WATCH_PID" 2>/dev/null || true
  fi
  /usr/bin/python3 "$GATE_BIN" finalize || true
  /usr/bin/python3 /opt/cursor-agent-tunnel/finalize-session.py || true
}
trap cleanup EXIT

/usr/bin/python3 "$GATE_BIN" watch >/dev/null 2>>"${LOG_DIR}/session.log" &
WATCH_PID=$!

echo
echo "=== Cursor Agent Tunnel · GROK 4.6 High Fast ==="
echo "Sessao: ${SESSION_ID}"
if [[ "$IS_RESUME" -eq 1 ]]; then
  echo "Retomando conversa: ${CHAT_ID:-anterior}"
fi
echo "Workspace isolado: ${WORKSPACE}"
echo "So esta pasta e gravavel. Ctrl+C / exit para sair."
echo

AGENT_ARGS=(
  --model "${MODEL}"
  --trust
  --sandbox enabled
  --workspace "${WORKSPACE}"
)
if [[ "$IS_RESUME" -eq 1 && -n "$CHAT_ID" ]]; then
  AGENT_ARGS+=(--resume "${CHAT_ID}")
elif [[ "$IS_RESUME" -eq 1 ]]; then
  AGENT_ARGS+=(--continue)
fi

bwrap \
  --die-with-parent \
  --ro-bind / / \
  --dev /dev \
  --proc /proc \
  --tmpfs /tmp \
  --tmpfs "${REAL_HOME}" \
  --ro-bind "${REAL_HOME}/.local" "${REAL_HOME}/.local" \
  --ro-bind "${REAL_HOME}/.config" "${REAL_HOME}/.config" \
  --dir "${REAL_HOME}/development" \
  --dir "${REAL_HOME}/development/guest-sessions" \
  --bind "${SESSION_DIR}" "${SESSION_DIR}" \
  --bind "${CURSOR_STATE}" "${REAL_HOME}/.cursor" \
  --chdir "${WORKSPACE}" \
  --setenv HOME "${REAL_HOME}" \
  --setenv PATH "${REAL_HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin" \
  --setenv TMPDIR /tmp \
  --setenv LOG_DIR "${LOG_DIR}" \
  --setenv SESSION_DIR "${SESSION_DIR}" \
  --setenv SESSION_ID "${SESSION_ID}" \
  --unsetenv CURSOR_AGENT \
  --unsetenv CURSOR_CONVERSATION_ID \
  --unsetenv CURSOR_ASKPASS_SOCKET \
  --unsetenv CURSOR_ASKPASS_SECRET \
  --unsetenv AGENT_TRANSCRIPTS \
  -- \
  "${AGENT_BIN}" \
    "${AGENT_ARGS[@]}"
exit $?
