#!/usr/bin/env bash
# 45 · 逐模块覆盖率门槛（防“总量绿、单文件裸奔”）：core 每文件 ≥ MIN（缺省 50，
# __init__ 豁免）。失败 exit 1 并打印低于线文件清单。
set -e
cd "$(dirname "$0")/.."
MIN="${1:-50}"
python -m coverage run --source=desktop/src/core -m unittest discover -s desktop/tests >/dev/null 2>&1 || true
python -m coverage json --include="desktop/src/core/*" -o _cov_tmp.json
python - <<PY
import json
data = json.load(open("_cov_tmp.json", encoding="utf-8"))
files = data.get("files", {})
bad = []
for path, info in files.items():
    if path.replace("\\\\", "/").endswith("__init__.py"):
        continue
    pct = info.get("summary", {}).get("percent_covered", 100)
    if pct < $MIN:
        bad.append((path, round(pct, 1)))
print("per-module gate: files=%d below=%d (min=%s)" % (len(files), len(bad), "$MIN"))
for path, pct in sorted(bad):
    print("  LOW %-60s %.1f%%" % (path, pct))
exit(1 if bad else 0)
PY
rm -f _cov_tmp.json
