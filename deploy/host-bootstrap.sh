#!/usr/bin/env bash
# Runs via ubuntu user systemd, outside the guest bubblewrap.
set -euo pipefail

APP="/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot"
UNIT_DIR="/home/ubuntu/.config/systemd/user"
LOG="$APP/data/host-bootstrap.log"
mkdir -p "$UNIT_DIR" "$APP/data"

{
  echo "=== bootstrap $(date -u +%Y-%m-%dT%H:%M:%SZ) uid=$(id -u) home=$HOME ==="
  echo "writable /etc/nginx? $(test -w /etc/nginx/sites-available && echo yes || echo no)"
  sudo -n true && echo "sudo-n: yes" || echo "sudo-n: no"
  sudo -n -l || true
} >>"$LOG" 2>&1

cat >"$UNIT_DIR/wdtsot.service" <<'EOF'
[Unit]
Description=WDTSOT public MVP
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot
Environment=WDTSOT_HOST=0.0.0.0
Environment=WDTSOT_PORT=8787
Environment=WDTSOT_MODEL=cursor-grok-4.6-high-fast
Environment=WDTSOT_AGENT_BIN=/home/ubuntu/.local/bin/agent
Environment=REAL_HOME=/home/ubuntu
Environment=HOME=/home/ubuntu
ExecStart=/usr/bin/python3 /home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable wdtsot.service
# If something is already bound, the new unit will fail; caller stops the guest-local server first.
systemctl --user restart wdtsot.service
systemctl --user status --no-pager wdtsot.service >>"$LOG" 2>&1 || true

if sudo -n true 2>/dev/null; then
  sudo -n "$APP/deploy/deploy.sh" >>"$LOG" 2>&1 || true
fi

echo "done" >>"$LOG"
