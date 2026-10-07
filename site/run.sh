#!/bin/sh
# NinFenz（宁封子 · NF）免安装引导脚本
# 来源：https://ninfenz.dev/run.sh   ·   POSIX sh，无第三方依赖，不发遥测
#
# 用法：
#   curl -fsSL https://ninfenz.dev/run.sh | sh                  默认：clone 到 ./NinFenz，跑只读体检
#   curl -fsSL https://ninfenz.dev/run.sh | sh -s -- --full     追加：跑 check1-40 全量门禁
#   curl -fsSL https://ninfenz.dev/run.sh | sh -s -- --dir /tmp/nf --mirror gitee
#
# 本脚本只做三件事：1) git clone 仓库；2) 逐条打印将要执行的命令；3) 执行它。
# 无 sudo、不写目标目录以外的路径；每条命令都先打印再执行，便于核对后再信。

set -eu

REPO_GITHUB="https://github.com/Monyeah777/NinFenz"
REPO_GITEE="https://gitee.com/monyeah777/ninfenz"
REPO="$REPO_GITHUB"
DEST="./NinFenz"
FULL="no"

while [ $# -gt 0 ]; do
  case "$1" in
    --full) FULL="yes" ;;
    --mirror)
      shift
      if [ "${1:-}" = "gitee" ]; then REPO="$REPO_GITEE"; else echo "未知镜像：${1:-}（可选 gitee）" >&2; exit 2; fi
      ;;
    --dir)
      shift
      if [ -z "${1:-}" ]; then echo "--dir 需要一个目标目录" >&2; exit 2; fi
      DEST="$1"
      ;;
    -h|--help)
      echo "用法：sh run.sh [--full] [--mirror gitee] [--dir <目标目录>]"
      echo "  --full         clone 后追加跑 bash verify.sh（check1-40 全量门禁）"
      echo "  --mirror gitee 用 Gitee 镜像（国内可达）"
      exit 0
      ;;
    *) echo "未知参数：$1（跑 sh run.sh --help 看用法）" >&2; exit 2 ;;
  esac
  shift
done

say() { printf '%s\n' "$*"; }
run() { say "+ $*"; "$@"; }

say "== NinFenz 免安装引导（https://ninfenz.dev/run.sh）=="
say "仓库：$REPO"
say "目标目录：$DEST"
say "许可：MIT · 全部内容可公开引用"

if ! command -v git >/dev/null 2>&1; then
  say "缺 git：请先安装 git。本脚本不做包管理，也不申请 sudo。"
  exit 1
fi

PY=""
if command -v python >/dev/null 2>&1; then PY="python"; elif command -v python3 >/dev/null 2>&1; then PY="python3"; fi
if [ -z "$PY" ]; then
  say "缺 python：需要 Python >= 3.11（NF 核心纯标准库，无 pip 依赖）。"
  exit 1
fi

if [ -d "$DEST/.git" ]; then
  say "目标目录已是 git 检出：跳过 clone（不在已有检出上做重置/清理）"
else
  run git clone "$REPO" "$DEST"
fi

run cd "$DEST"
run "$PY" scripts/nf.py doctor

if [ "$FULL" = "yes" ]; then
  if ! command -v bash >/dev/null 2>&1; then
    say "缺 bash：verify.sh 需要 POSIX shell（Windows 用 Git Bash）。"
    exit 1
  fi
  run bash verify.sh
else
  say "只读路径到此为止。要跑全量门禁：sh run.sh --full，或在检出目录里跑 bash verify.sh"
fi

say "== 完成。人机入口：$PY tui/nf.py ｜ 客户端 AI 指令：https://ninfenz.dev/nf.txt =="
