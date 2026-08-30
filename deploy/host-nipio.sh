#!/usr/bin/env bash
set -euo pipefail
APP=/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot
cp -a /etc/nginx/sites-available/wdtsot.shop /var/backups/wdtsot-20260829T214520Z/wdtsot.shop.before-nipio
install -m 0644 "$APP/deploy/nginx-wdtsot.shop.conf" /etc/nginx/sites-available/wdtsot.shop
nginx -t
systemctl reload nginx
echo OK
