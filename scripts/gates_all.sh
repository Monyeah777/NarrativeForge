#!/usr/bin/env bash
# 42 audit 行动建议④：本地三闸门一键（lint + coverage + verify）。
# lint/coverage 为可选本地工具（缺失则提示，由 CI 对应 job 兜底）；verify 为铁律必跑。
set -e
cd "$(dirname "$0")/.."

find_ruff() {
  if command -v ruff >/dev/null 2>&1; then
    echo "ruff"
    return 0
  fi
  for p in "${APPDATA:-$HOME/AppData/Roaming}/Python/Python311/Scripts/ruff.exe" \
           "$HOME/.local/bin/ruff"; do
    if [ -x "$p" ]; then
      echo "$p"
      return 0
    fi
  done
  return 1
}

echo "== 闸门 1/3 · lint（ruff E9/F63/F7/F82）=="
if RUFF="$(find_ruff)"; then
  "$RUFF" check desktop/src scripts
else
  echo "  skip：本地未装 ruff（CI lint job 覆盖同集规则）"
fi

echo "== 闸门 2/3 · coverage（desktop/src/core ≥80%）=="
if python -m coverage --version >/dev/null 2>&1; then
  python -m coverage run --source=desktop/src/core -m unittest discover -s desktop/tests
  python -m coverage report --fail-under=80 --include="desktop/src/core/*"
else
  echo "  skip：本地未装 coverage（CI coverage job 兜底）"
fi

echo "== 闸门 3/3 · verify（check1-27 PASS=41 铁律）=="
bash verify.sh
echo "== 三闸门全绿 =="
