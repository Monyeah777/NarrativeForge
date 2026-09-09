#!/usr/bin/env bash
# 45 A4 · verify 版本标签多文件同步（vX.Y 换标；check 数/PASS 不变时使用）。
# 用法：scripts/bump_verify.sh v2.21 [--dry-run]
set -e
cd "$(dirname "$0")/.."
NEW="$1"
if [[ ! "$NEW" =~ ^v[0-9]+\.[0-9]+$ ]]; then
  echo "用法: scripts/bump_verify.sh vX.Y" >&2; exit 2
fi
DRY="${2:-}"
if [ "$DRY" = "--dry-run" ]; then
  export DRY=1
  MODE=dry
else
  MODE=apply
fi
python - "$NEW" <<'PY'
import os
import sys
new = sys.argv[1]
paths = ["verify.sh", "README.md"]
total = 0
for p in paths:
    d = open(p, encoding="utf-8").read()
    n = d.count("v2.20")
    if n:
        total += n
        if os.environ.get("DRY") != "1":
            d = d.replace("v2.20", new)
            open(p, "w", encoding="utf-8", newline="\n").write(d)
        print(("dry " if os.environ.get("DRY") == "1" else "") + "updated", p, "x%d" % n)
if total == 0:
    print("no v2.20 label found")
PY
if [ "$MODE" = "dry" ]; then
  echo "dry-run done（未写盘）"
else
  python scripts/nf.py release --fast
  echo "bump done: verify label -> $NEW（改动已写入，确认后提交）"
fi
