#!/usr/bin/env bash
# Open the conta.vc home so the founder can passkey-authenticate.
# Needs a real display (Mac / local Chrome). Does nothing useful on a headless VPS.
set -euo pipefail
URL="${1:-https://app.conta.vc/receive/link/charge/new}"

if [[ -z "${DISPLAY:-}" && "$(uname -s)" != "Darwin" ]]; then
  echo "sem DISPLAY. abra no Chrome do Mac: $URL" >&2
  exit 2
fi

if command -v open >/dev/null && [[ "$(uname -s)" == "Darwin" ]]; then
  open "$URL"
  exit 0
fi

for bin in google-chrome chromium-browser chromium; do
  if command -v "$bin" >/dev/null; then
    exec "$bin" --new-window "$URL"
  fi
done

echo "chrome/chromium não encontrado. abra: $URL" >&2
exit 1
