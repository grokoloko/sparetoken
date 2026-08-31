#!/usr/bin/env bash
# Read-only research pulse. No git write. No mint.
set -euo pipefail
export TZ=America/Sao_Paulo
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "=== research $(date +%Y-%m-%dT%H:%M:%S%z) ==="
echo "brain=ceo/launch/research.md"
tail -n 12 "$ROOT/ceo/RESEARCH.md"
echo "NEXT: three URLs into RESEARCH.md then stop."
