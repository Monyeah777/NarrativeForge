#!/usr/bin/env bash
# 42 M5.1 本地覆盖率摘要（与 CI coverage job 同构；coverage 为可选本地工具，
# 不触碰 verify.sh 零依赖红线）。
set -e
cd "$(dirname "$0")/.."
if ! python -m coverage --version >/dev/null 2>&1; then
  echo "缺少 coverage：pip install coverage 后重跑（可选本地工具，非 verify 依赖）" >&2
  exit 2
fi
python -m coverage run --source=desktop/src/core -m unittest discover -s desktop/tests
python -m coverage report --include="desktop/src/core/*"
