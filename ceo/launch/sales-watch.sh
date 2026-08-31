#!/usr/bin/env bash
# Read-only sales pulse. Never prints contact, email, pay URL, or names.
set -euo pipefail
export TZ=America/Sao_Paulo
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DB="${WDTSOT_DB:-$ROOT/data/wdtsot.sqlite}"
STAMP="${WDTSOT_SALES_STAMP:-$ROOT/data/sales-watch.stamp}"
echo "=== sales-watch $(date +%Y-%m-%dT%H:%M:%S%z) ==="
if [[ ! -f "$DB" ]]; then
  echo "no sqlite here (ok on Mac). set WDTSOT_DB on the VPS."
  exit 0
fi
python3 - "$DB" "$STAMP" <<'PY'
import sqlite3, sys, time
from pathlib import Path
db, stamp_path = Path(sys.argv[1]), Path(sys.argv[2])
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
paid = con.execute(
    "SELECT COUNT(*) FROM purchases WHERE status IN ('paid','closed','confirmed')"
).fetchone()[0]
open_n = con.execute(
    "SELECT COUNT(*) FROM pay_links WHERE status IN ('idle','open','reserved')"
).fetchone()[0]
closed_n = con.execute(
    "SELECT COUNT(*) FROM pay_links WHERE status IN ('closed','paid')"
).fetchone()[0]
had_stamp = stamp_path.exists()
prev = 0
if had_stamp:
    try:
        prev = int(stamp_path.read_text().split()[0])
    except ValueError:
        prev = 0
delta = paid - prev
print(f"purchases_paid={paid} pay_openish={open_n} pay_closed={closed_n} delta={delta} baseline={not had_stamp}")
if had_stamp and delta > 0:
    print("CELEBRATE")
    flag = db.parent / "celebrate.txt"
    flag.write_text(
        "mais um bloco saiu da prateleira. R$5 · 5h.\n"
        "https://sparetoken.shop/?utm_source=x&utm_medium=social&utm_campaign=sold&utm_content=sale\n",
        encoding="utf-8",
    )
elif not had_stamp:
    print("baseline set — will not celebrate history")
if open_n < 3:
    print("RESTOCK +10")
    (db.parent / "restock.flag").write_text("mint +10 on local Chrome\n", encoding="utf-8")
stamp_path.write_text(f"{paid} {int(time.time())}\n", encoding="utf-8")
PY
