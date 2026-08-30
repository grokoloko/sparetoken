#!/usr/bin/env bash
set -euo pipefail
OUT=/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot/data/tunnel-url.txt
journalctl -u cloudflared-wdtsot.service -n 120 --no-pager > /tmp/cf.log
grep -E 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf.log | tail -5 > "$OUT" || true
cat /tmp/cf.log
echo '---URL---'
cat "$OUT"
systemctl is-active cloudflared-wdtsot.service
