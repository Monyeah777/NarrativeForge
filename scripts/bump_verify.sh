#!/usr/bin/env bash
# 45 A4 · verify 版本标签多文件同步（vX.Y 换标；check 数/PASS 不变时使用）。
# 用法：scripts/bump_verify.sh v2.21   （改动后自行跑 verify 复核）
set -e
cd "$(dirname "$0")/.."
NEW="$1"
if [[ ! "$NEW" =~ ^v[0-9]+\.[0-9]+$ ]]; then
  echo "用法: scripts/bump_verify.sh vX.Y" >&2; exit 2
fi
python - "$NEW" <<'PY'
import sys
new = sys.argv[1]
targets = ["verify.sh", "README.md"]
for p in targets:
    d = open(p, encoding="utf-8").read()
    if "v2.20" in d:
        d = d.replace("v2.20", new)
        open(p, "w", encoding="utf-8", newline="\n").write(d)
        print("updated", p)
PY
python scripts/nf.py release --fast
echo "bump done: verify label -> $NEW（改动已写入，确认后提交）"
