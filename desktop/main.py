#!/usr/bin/env python3
"""叙事工坊 · 桌面工具启动入口。

用法：
    python main.py            # 使用默认数据目录 ~/.NarrativeForge
    NARRATIVE_FORGE_HOME=/path/to/home python main.py   # 指定数据目录
"""
import sys

from src.ui.main_window import run

if __name__ == "__main__":
    sys.exit(run())
