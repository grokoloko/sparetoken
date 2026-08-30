#!/usr/bin/env bash
set -euo pipefail
LOG=/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot/data/units.log
exec >"$LOG" 2>&1
export XDG_RUNTIME_DIR=/run/user/1001
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus
systemctl --user stop wdtsot.service || true
systemctl --user disable wdtsot.service || true
sudo -n systemctl daemon-reload
sudo -n systemctl enable --now wdtsot.service
sleep 1
echo "system: $(sudo -n systemctl is-active wdtsot.service) $(sudo -n systemctl is-enabled wdtsot.service)"
echo "user: $(systemctl --user is-active wdtsot.service || true)"
ss -tulpn | grep 8787 || true
curl -sS http://127.0.0.1:8787/api/health; echo
curl -sS -H Host:wdtsot.shop http://127.0.0.1/api/health; echo
# conecte.mail default still
curl -sS http://127.0.0.1/ | head -c 80; echo
echo DONE
