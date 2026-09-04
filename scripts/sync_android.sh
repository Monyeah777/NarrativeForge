#!/usr/bin/env bash
# 同步 Android 工程依赖的共享源码与种子数据（单一事实源保持仓库根）。
# 用法：bash scripts/sync_android.sh [--check] [仓库根]
#   - desktop/src/core  → android/app/core    （纯 Python 逻辑层，零第三方依赖）
#   - 03_管线库/04_模块库/05_资产库 → android/app/seed
#   - --check：只读差异模式（v0.6.0 T3/A3）——不加参数行为不变（rm -rf + cp 覆盖）；
#     加 --check 为只读 diff：core 段 diff -rq desktop/src/core android/app/core、
#     seed 段逐目录 diff -rq；输出差异清单（新增/缺失/内容差异分列），
#     有差异 exit 1、无差异 exit 0。生成物缺失（新 clone 未 sync）时明确提示先 sync。
#     全程只读不写任何文件（接入 CI 归 v0.9.0，本版交付模式本体）。
# 幂等：重复执行安全；android/app/{core,seed} 为 .gitignore 生成物，不入库。
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_CORE="$ROOT/desktop/src/core"
DST_CORE="$ROOT/android/app/core"
SRC_SEED=("$ROOT/03_管线库" "$ROOT/04_模块库" "$ROOT/05_资产库")
DST_SEED="$ROOT/android/app/seed"

# ---- --check：只读差异模式（v0.6.0 T3/A3；双端一致性提交前可自证）----
if [ "${1:-}" = "--check" ]; then
  shift
  _ck_err=0
  echo "== --check 只读差异模式（不写任何文件）=="
  # 边界：生成物缺失（新 clone 未 sync）——明确提示先 sync，不误报 diff
  if [ ! -d "$DST_CORE" ] || [ ! -d "$DST_SEED" ]; then
    echo "  ! 生成物缺失：android/app/core 或 android/app/seed 不在场（新 clone 未 sync？）"
    echo "  ! 请先运行：bash scripts/sync_android.sh"
    exit 1
  fi
  # core 段：diff -rq（排除 __pycache__ 生成物；差异清单含 Files..differ 内容差异 / Only in.. 新增缺失）
  echo "== check core =="
  if [ -d "$SRC_CORE" ]; then
    _ck_core="$(diff -rq "$SRC_CORE" "$DST_CORE" 2>&1 | grep -v '__pycache__' || true)"
    if [ -n "$_ck_core" ]; then
      echo "  [core] 差异清单（内容差异/新增/缺失）："
      echo "$_ck_core" | sed 's/^/    /'
      _ck_err=1
    else
      echo "  [core] 一致：desktop/src/core ↔ android/app/core 无差异"
    fi
  else
    echo "  ! 未找到源 $SRC_CORE"; _ck_err=1
  fi
  # seed 段：逐目录 diff -rq（03/04/05 ↔ android/app/seed/<同名>）
  echo "== check seed =="
  for _d in "${SRC_SEED[@]}"; do
    _name="$(basename "$_d")"
    if [ ! -d "$_d" ]; then
      echo "  ! 未找到源 $_d"; _ck_err=1; continue
    fi
    if [ ! -d "$DST_SEED/$_name" ]; then
      echo "  [seed/$_name] 缺失：android/app/seed/$_name 不在场（需先 sync）"; _ck_err=1; continue
    fi
    _ck_seed="$(diff -rq "$_d" "$DST_SEED/$_name" 2>&1 || true)"
    if [ -n "$_ck_seed" ]; then
      echo "  [seed/$_name] 差异清单（内容差异/新增/缺失）："
      echo "$_ck_seed" | sed 's/^/    /'
      _ck_err=1
    else
      echo "  [seed/$_name] 一致：$(basename "$_d") ↔ android/app/seed/$_name 无差异"
    fi
  done
  echo "== done =="
  if [ "$_ck_err" -eq 0 ]; then
    echo ">>> 双端一致：--check 通过（exit 0），变更可提交 <<<"
    exit 0
  else
    echo ">>> 存在差异：--check 未通过（exit 1）——请先运行 bash scripts/sync_android.sh 同步 <<<"
    exit 1
  fi
fi

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