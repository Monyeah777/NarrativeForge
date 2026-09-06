"""叙事工坊 · 桌面工具入口（支持 ``python -m src`` 启动）。"""
import sys

from .ui.main_window import run

if __name__ == "__main__":
    sys.exit(run())
