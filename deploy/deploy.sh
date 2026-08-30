#!/usr/bin/env bash
# Install nginx vhost + systemd unit. Requires root. Never overwrites unrelated hosts.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/var/backups/wdtsot-${STAMP}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Need root. Try: sudo $0" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
if [[ -f /etc/nginx/sites-available/default ]]; then
  cp -a /etc/nginx/sites-available/default "$BACKUP_DIR/default"
fi
if [[ -f /etc/nginx/nginx.conf ]]; then
  cp -a /etc/nginx/nginx.conf "$BACKUP_DIR/nginx.conf"
fi
if [[ -f /etc/nginx/sites-available/wdtsot.shop ]]; then
  cp -a /etc/nginx/sites-available/wdtsot.shop "$BACKUP_DIR/wdtsot.shop"
fi

install -m 0644 "$ROOT/deploy/nginx-wdtsot.shop.conf" /etc/nginx/sites-available/wdtsot.shop
ln -sfn /etc/nginx/sites-available/wdtsot.shop /etc/nginx/sites-enabled/wdtsot.shop

install -m 0644 "$ROOT/deploy/wdtsot.service" /etc/systemd/system/wdtsot.service
systemctl daemon-reload
systemctl enable --now wdtsot.service

nginx -t
systemctl reload nginx
echo "WDTSOT deployed. Health: curl -s http://127.0.0.1:8787/api/health"
echo "Rollback: restore files from $BACKUP_DIR and systemctl disable --now wdtsot.service"
