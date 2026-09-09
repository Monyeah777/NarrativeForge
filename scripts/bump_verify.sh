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
total = 0
# verify.sh：全量替换当前版本 token（历史注解不以 vX.Y 出现）。
for p in ["verify.sh"]:
    d = open(p, encoding="utf-8").read()
    n = d.count("v2.22")
    if n:
        total += n
        if os.environ.get("DRY") != "1":
            d = d.replace("v2.22", new)
            open(p, "w", encoding="utf-8", newline="\n").write(d)
        print(("dry " if os.environ.get("DRY") == "1" else "") + "updated", p, "x%d" % n)
# README：只替换当前基线行（跳过发布历史块 `> **v...**`），避免时间线错乱。
p = "README.md"
d = open(p, encoding="utf-8").read()
lines = d.splitlines(keepends=True)
out = []
n = 0
for ln in lines:
    if ln.startswith("> **v") and "verify v2.22" in ln:
        out.append(ln)
    elif not ln.startswith("> **v") and "v2.22" in ln:
        n += 1
        out.append(ln.replace("v2.22", new))
    else:
        out.append(ln)
if n:
    total += n
    if os.environ.get("DRY") != "1":
        open(p, "w", encoding="utf-8", newline="\n").write("".join(out))
    print(("dry " if os.environ.get("DRY") == "1" else "") + "updated", p, "x%d" % n)
if total == 0:
    print("no v2.22 label found")
PY
if [ "$MODE" = "dry" ]; then
  echo "dry-run done（未写盘）"
else
  python scripts/nf.py release --fast
  echo "bump done: verify label -> $NEW（改动已写入，确认后提交）"
fi
