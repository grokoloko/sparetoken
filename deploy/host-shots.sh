#!/usr/bin/env bash
set -euo pipefail
OUT="/tmp/wdtsot-shots"
mkdir -p "$OUT"
CHROME=/usr/bin/chromium-browser
export XDG_RUNTIME_DIR=/run/user/1001
for w in 360 390 430 768 1280; do
  "$CHROME" --headless --disable-gpu --no-sandbox --hide-scrollbars \
    --window-size="${w},1400" \
    --screenshot="${OUT}/wdtsot-${w}.png" \
    "http://wdtsot.shop/" || true
done
ls -la "$OUT"
