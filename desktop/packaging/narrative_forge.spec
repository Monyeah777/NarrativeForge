# -*- mode: python ; coding: utf-8 -*-
"""NarrativeForge（叙事工坊桌面工具）PyInstaller 打包配置（三平台通用）。

单文件 GUI 可执行：Windows → NarrativeForge.exe；macOS → NarrativeForge
（Mach-O）；Linux → NarrativeForge（ELF）。console=False 保证无黑窗。

用法（在项目根执行，SPECPATH 由 PyInstaller 注入）：
    pyinstaller --noconfirm packaging/narrative_forge.spec
"""
import os
from PyInstaller.utils.hooks import collect_all

# 收集 PySide6 全部动态库/插件/Qt 翻译，避免运行时缺插件
datas, binaries, hiddenimports = [], [], []
for pkg in ("PySide6",):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [os.path.join(os.path.dirname(SPECPATH), "main.py")],
    pathex=[os.path.dirname(SPECPATH)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "PyInstaller"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="NarrativeForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # UPX 常与 Qt 插件冲突，默认关闭
    console=False,          # GUI 应用
    disable_windowed_traceback=False,
)
