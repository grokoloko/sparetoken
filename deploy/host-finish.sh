#!/usr/bin/env bash
set -euo pipefail
APP="/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot"
LOG="$APP/data/host-finish.log"
exec > >(tee -a "$LOG") 2>&1
echo "=== finish $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
loginctl enable-linger ubuntu
echo "linger: $(ls /var/lib/systemd/linger)"
# refresh nginx vhost from repo (www -> http apex until TLS exists)
cp -a /etc/nginx/sites-available/wdtsot.shop /var/backups/wdtsot-20260829T214520Z/wdtsot.shop.before-wwwfix || true
install -m 0644 "$APP/deploy/nginx-wdtsot.shop.conf" /etc/nginx/sites-available/wdtsot.shop
nginx -t
systemctl reload nginx
echo "system unit enabled: $(systemctl is-enabled wdtsot.service || true)"
echo "system unit active: $(systemctl is-active wdtsot.service || true)"
# Prefer the system unit on reboot. Stop it now if it would race; user unit is already serving.
if systemctl is-active --quiet wdtsot.service; then
  echo "system unit already active"
else
  echo "system unit not active (user unit is serving). enabled for reboot."
fi
# screenshots
if ! command -v chromium-browser >/dev/null && ! command -v chromium >/dev/null && ! command -v google-chrome >/dev/null; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq chromium-browser || apt-get install -y -qq chromium || true
fi
CHROME="$(command -v chromium-browser || command -v chromium || command -v google-chrome || true)"
echo "chrome=$CHROME"
mkdir -p "$APP/data/screenshots"
if [[ -n "$CHROME" ]]; then
  for w in 360 390 430 768 1280; do
    "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
      --window-size="$w",900 \
      --screenshot="$APP/data/screenshots/home-${w}.png" \
      --default-background-color=FFF3EEE4 \
      "http://127.0.0.1/" \
      --virtual-time-budget=4000 || true
    # Host header is not settable easily; use a temp hosts? Instead curl via a local hostname.
  done
fi
# Use a local name via /etc/hosts for accurate vhost screenshots
if ! grep -q 'wdtsot.shop' /etc/hosts; then
  echo '127.0.0.1 wdtsot.shop' >> /etc/hosts
  echo "added hosts entry"
fi
if [[ -n "$CHROME" ]]; then
  for w in 360 390 430 768 1280; do
    "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
      --window-size="$w",1100 \
      --screenshot="$APP/data/screenshots/wdtsot-${w}.png" \
      "http://wdtsot.shop/" || true
  done
fi
echo DONE
ls -la "$APP/data/screenshots" || true
