# 打包（Packaging）

NarrativeForge（叙事工坊）桌面工具基于 **PySide6 + PyInstaller** 三平台打包：

| 平台 | 脚本 | 产物 |
|---|---|---|
| Windows | `build_windows.bat`（在 Windows 上运行） | `dist\NarrativeForge.exe` |
| macOS | `build_macos.sh`（在 macOS 上运行） | `dist/NarrativeForge`（Mach-O） |
| Linux | `build_linux.sh`（在 Linux 上运行） | `dist/NarrativeForge`（ELF） |

## 共同说明

- 三平台共用 `narrative_forge.spec`：单文件 GUI 模式（`console=False`），
  通过 `collect_all("PySide6")` 完整收集 Qt 动态库与平台插件。
- 构建机需 Python 3.10+；**PySide6 必须在构建机同架构环境安装**
  （三平台各自在自己的系统上执行构建脚本）。
- 产物为"单文件可执行"，不依赖目标机预装 Python。
- `.dmg` / `.AppImage` / Windows 安装包属于分发层封装，
  可在产物基础上用 create-dmg / appimagetool / Inno Setup 二次制作。

## 运行行为

- 首次启动在 `~/.NarrativeForge/` 自动创建目录骨架
  （`config.json / modules/ / assets/ / presets/ / cache/`）。
- 可用环境变量 `NARRATIVE_FORGE_HOME` 覆盖数据目录（便携模式/测试）。

## 验证打包产物（Linux 示例）

```bash
# 无显示环境自检（产物能启动并完成 GUI 初始化即视为通过）
NARRATIVE_FORGE_HOME=/tmp/nf-test-home QT_QPA_PLATFORM=offscreen \
  ./dist/NarrativeForge &
sleep 2
# 冒烟脚本方式（开发环境，非打包产物）：
NARRATIVE_FORGE_HOME=/tmp/nf-test-home QT_QPA_PLATFORM=offscreen \
  python3 scripts/smoke_gui.py
```
