#!/usr/bin/env bash
set -euo pipefail
DEST="/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot/data/screenshots"
mkdir -p /tmp/wdtsot-shots "$DEST"
ls -la /tmp/wdtsot-shots || true
if ! ls /tmp/wdtsot-shots/*.png >/dev/null 2>&1; then
  CHROME=/usr/bin/chromium-browser
  export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1001}
  for w in 360 390 430 768 1280; do
    "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
      --user-data-dir=/tmp/wdtsot-chrome \
      --window-size="${w},1400" \
      --screenshot="/tmp/wdtsot-shots/wdtsot-${w}.png" \
      "http://wdtsot.shop/" || true
  done
fi
# dest may be root-owned
if [[ ! -w "$DEST" ]]; then
  sudo -n chown ubuntu:ubuntu "$DEST" || true
fi
cp -a /tmp/wdtsot-shots/. "$DEST/"
ls -la "$DEST"
