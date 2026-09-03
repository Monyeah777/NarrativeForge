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

见 `packaging/README.md`。三平台产物由 GitHub Actions 自动构建（仓库根 `.github/workflows/build-desktop.yml`），发布在 Releases / Actions Artifacts：

- Windows：`dist\NarrativeForge.exe`
- macOS：`dist/NarrativeForge`（Mach-O）
- Linux：`dist/NarrativeForge`（ELF）

本地手动构建：macOS 用 `packaging/build_macos.sh`，Linux 用 `packaging/build_linux.sh`。原 `build_windows.bat` 已移除，Windows 产物由 CI 自动构建。
