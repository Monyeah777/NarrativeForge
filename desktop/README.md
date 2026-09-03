# 桌面工具

Narrative Forge 协议的桌面实现：把 .md 模块拖进窗口，逐项校验、勾选装配，输出结构化文档。

- 技术栈：Python 3.10+ / PySide6 / PyInstaller
- 数据目录：默认 `~/.NarrativeForge`，可用 `NARRATIVE_FORGE_HOME` 覆盖

## 运行（源码）

```bash
python main.py
```

## 验证

```bash
python3 -m unittest tests.test_core -v   # 核心层单测
NARRATIVE_FORGE_HOME=<数据目录> QT_QPA_PLATFORM=offscreen python3 scripts/smoke_gui.py
```

## 打包

见 `packaging/README.md`。Windows 上运行 `packaging/build_windows.bat`，产物为 `dist\NarrativeForge.exe`；macOS 用 `build_macos.sh`，Linux 用 `build_linux.sh`。
