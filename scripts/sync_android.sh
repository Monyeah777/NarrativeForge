#!/usr/bin/env bash
# 同步 Android 工程依赖的共享源码与种子数据（单一事实源保持仓库根）。
# 用法：bash scripts/sync_android.sh [仓库根]
#   - desktop/src/core  → android/app/core    （纯 Python 逻辑层，零第三方依赖）
#   - 03_管线库/04_模块库/05_资产库 → android/app/seed
# 幂等：重复执行安全；android/app/{core,seed} 为 .gitignore 生成物，不入库。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_CORE="$ROOT/desktop/src/core"
DST_CORE="$ROOT/android/app/core"
SRC_SEED=("$ROOT/03_管线库" "$ROOT/04_模块库" "$ROOT/05_资产库")
DST_SEED="$ROOT/android/app/seed"

echo "== sync core =="
if [ -d "$SRC_CORE" ]; then
  rm -rf "$DST_CORE"
  mkdir -p "$(dirname "$DST_CORE")"
  cp -r "$SRC_CORE" "$DST_CORE"
  find "$DST_CORE" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
  echo "  core -> $(find "$DST_CORE" -name '*.py' | wc -l) 个 py 文件"
else
  echo "  ! 未找到 $SRC_CORE，跳过"
fi

echo "== sync seed =="
rm -rf "$DST_SEED"
mkdir -p "$DST_SEED"
for d in "${SRC_SEED[@]}"; do
  if [ -d "$d" ]; then
    cp -r "$d" "$DST_SEED/"
    echo "  $(basename "$d") -> ok"
  else
    echo "  ! 未找到 $d"
  fi
done
echo "seed 源文件总数: $(find "$DST_SEED" -type f | wc -l)"
echo "== done =="