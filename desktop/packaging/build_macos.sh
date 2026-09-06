#!/usr/bin/env bash
# macOS 构建：产物 dist/NarrativeForge（单文件 Mach-O GUI 可执行）
# 用法：bash packaging/build_macos.sh
cd "$(dirname "$0")/.." || exit 1

echo "==> 安装/升级 PyInstaller"
python3 -m pip install --upgrade pyinstaller || exit 1

echo "==> 执行打包"
python3 -m PyInstaller --noconfirm packaging/narrative_forge.spec || exit 1

echo ""
echo "==> 产物：dist/NarrativeForge"
echo "    运行：./dist/NarrativeForge"
echo "    （可选）后续可用 create-dmg 封装为 .dmg 分发"
