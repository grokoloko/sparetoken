#!/usr/bin/env bash
set -x
LOG=/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot/data/shots.log
exec >"$LOG" 2>&1
echo "uid=$(id) home=$HOME"
curl -sS -H Host:wdtsot.shop http://127.0.0.1/api/health || true
echo
curl -sS http://127.0.0.1:8787/api/health || true
echo
getent hosts wdtsot.shop || true
which chromium-browser chromium
OUT=/home/ubuntu/wdtsot-shots
mkdir -p "$OUT"
# snap chromium can write under $HOME
/usr/bin/chromium-browser --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --user-data-dir=/home/ubuntu/wdtsot-chrome \
  --window-size=390,1400 \
  --screenshot=/home/ubuntu/wdtsot-shots/wdtsot-390.png \
  http://wdtsot.shop/ || true
ls -la /home/ubuntu/wdtsot-shots /tmp/wdtsot-shots || true
DEST=/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot/data/screenshots
cp -a /home/ubuntu/wdtsot-shots/. "$DEST/" || true
ls -la "$DEST"
echo DONE
