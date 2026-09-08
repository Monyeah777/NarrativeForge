#!/usr/bin/env bash
# 42 M5.6 golden master 冻结：tag 点产物快照 + nf-sig 指纹双存。
# 用法：bash scripts/release_freeze.sh vX.Y.Z
set -e
cd "$(dirname "$0")/.."
TAG="${1:?用法: bash scripts/release_freeze.sh vX.Y.Z}"
OUT=".release-frozen/${TAG}"
mkdir -p "$OUT"
: > "$OUT/sha256.manifest"
for f in 01_核心协议.md 02_联动注册表.md 06_Agent执行协议.md \
         07_官方核心出厂与社区预设导航.md verify.sh; do
  [ -f "$f" ] && sha256sum "$f" >> "$OUT/sha256.manifest"
done
for f in desktop/src/core/*.py; do
  sha256sum "$f" >> "$OUT/sha256.manifest"
done
python scripts/nf.py sig --verify >> "$OUT/sig-fingerprint.txt"
echo "== golden master 冻结完成：$OUT =="
cat "$OUT/sha256.manifest"
