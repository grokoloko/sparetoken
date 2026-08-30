#!/usr/bin/env bash
set -euo pipefail
APP=/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot
LOG=$APP/data/public-link.log
exec > >(tee -a "$LOG") 2>&1
echo "=== public-link $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

install -m 0755 "$APP/deploy/cloudflared-linux-arm64" /usr/local/bin/cloudflared
/usr/local/bin/cloudflared version

cp -a /etc/nginx/sites-available/wdtsot.shop /var/backups/wdtsot-20260829T214520Z/wdtsot.shop.before-ip || true
install -m 0644 "$APP/deploy/nginx-wdtsot.shop.conf" /etc/nginx/sites-available/wdtsot.shop
nginx -t
systemctl reload nginx

install -m 0644 "$APP/deploy/cloudflared-wdtsot.service" /etc/systemd/system/cloudflared-wdtsot.service
systemctl daemon-reload
systemctl enable --now cloudflared-wdtsot.service
sleep 4
systemctl is-active cloudflared-wdtsot.service
journalctl -u cloudflared-wdtsot.service -n 40 --no-pager
echo DONE
