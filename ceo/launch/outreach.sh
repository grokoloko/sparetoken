#!/usr/bin/env bash
# Outreach pulse. No git write. No PII.
set -euo pipefail
export TZ=America/Sao_Paulo
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "=== outreach $(date +%Y-%m-%dT%H:%M:%S%z) ==="
tail -n 8 "$ROOT/ceo/POSTS.md"
echo "NEXT: one post, one utm_content. See outreach.md + x-pulse.md"
