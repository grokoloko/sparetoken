#!/usr/bin/env bash
# Cron helper: wake Cursor Agent on the VPS. heartbeat.sh + sell.sh call this.
# The wrapper never stubs `git` inside the agent process.
set -euo pipefail

pulse="${1:?pulse: heartbeat|sell}"
ROOT="${ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
export PATH="${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
AGENT_BIN="${AGENT_BIN:-${HOME}/.local/bin/agent}"

case "$pulse" in
  heartbeat) prompt_file="$ROOT/ceo/launch/prompts/heartbeat.txt" ;;
  sell) prompt_file="$ROOT/ceo/launch/prompts/sell.txt" ;;
  *)
    echo "run-cursor-agent: unknown pulse $pulse" >&2
    exit 2
    ;;
esac

if [[ ! -x "$AGENT_BIN" ]]; then
  echo "AGENT_MISSING $AGENT_BIN" >&2
  exit 1
fi
if [[ ! -f "$prompt_file" ]]; then
  echo "AGENT_PROMPT_MISSING $prompt_file" >&2
  exit 1
fi

echo "AGENT: on pulse=$pulse bin=$AGENT_BIN workspace=$ROOT"
# -p = non-interactive log to journal. --trust --force = no TTY hang on cron.
"$AGENT_BIN" -p --trust --force --workspace "$ROOT" "$(cat "$prompt_file")"
echo "AGENT_DONE pulse=$pulse"
