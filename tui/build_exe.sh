#!/usr/bin/env bash
# NF 终端 TUI 单文件打包（PyInstaller onefile）
#
# 用法：bash tui/build_exe.sh
# 产物：tui/dist/nf（单文件；构建中间件在 tui/build/，均不入仓）
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here"

echo "[1/3] 源码态自检"
python nf.py --selftest

# Build intermediates go to the system temp dir, never into the repo: the
# public-surface gate scans the working tree, and PyInstaller writes absolute
# build paths into build/*/warn-*.txt.
work="$(mktemp -d "${TMPDIR:-/tmp}/nf-tui-build-XXXXXX")"

echo "[2/3] PyInstaller 单文件打包（工作目录：$work）"
python -m PyInstaller --noconfirm --clean --onefile --name nf \
    --distpath dist --workpath "$work" --specpath "$work" nf.py

echo "[3/3] 产物自检"
./dist/nf --version
./dist/nf --selftest
echo "完成：$here/dist/nf"
