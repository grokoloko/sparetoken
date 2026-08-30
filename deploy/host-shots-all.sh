#!/usr/bin/env bash
set -euo pipefail
DEST=/home/ubuntu/development/guest-sessions/session-20260829-212831-83c1eb/workspace/wdtsot/data/screenshots
OUT=/home/ubuntu/wdtsot-shots
mkdir -p "$OUT" "$DEST"
for w in 360 430 768 1280; do
  /usr/bin/chromium-browser --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --user-data-dir=/home/ubuntu/wdtsot-chrome \
    --window-size="${w},1600" \
    --screenshot="${OUT}/wdtsot-${w}.png" \
    http://wdtsot.shop/ || true
done
# scrolled mid-page desktop
/usr/bin/chromium-browser --headless --disable-gpu --no-sandbox --hide-scrollbars \
  --user-data-dir=/home/ubuntu/wdtsot-chrome \
  --window-size=1280,2200 \
  --screenshot="${OUT}/wdtsot-1280-tall.png" \
  http://wdtsot.shop/ || true
cp -a "$OUT"/. "$DEST/"
ls -la "$DEST"
