#!/usr/bin/env bash
# Read-only UTM / click report. No PII dump.
set -euo pipefail
export TZ=America/Sao_Paulo
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DB="${WDTSOT_DB:-$ROOT/data/wdtsot.sqlite}"
echo "=== track-report $(date +%Y-%m-%dT%H:%M:%S%z) ==="
if [[ ! -f "$DB" ]]; then
  echo "no sqlite here. set WDTSOT_DB on the VPS."
  exit 0
fi
sqlite3 -readonly "$DB" <<'SQL'
SELECT IFNULL(event,'?'), IFNULL(utm_source,'-'), IFNULL(utm_content,'-'), COUNT(*)
FROM track_events
GROUP BY 1, 2, 3
ORDER BY 4 DESC
LIMIT 20;
SELECT event, COUNT(*) FROM track_events GROUP BY 1;
SQL
