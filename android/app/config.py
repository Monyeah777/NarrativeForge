"""应用路径与版本常量。
- 数据目录：Android 应用私有目录（ANDROID_PRIVATE）下 .NarrativeForge，
  与桌面端 ~/.NarrativeForge 布局/格式一致（模块/管线/资产包互通）。
- 种子目录：打包进 APK 的 app/seed（03_管线库/04_模块库/05_资产库 源文件）。
"""
from __future__ import annotations
import os
from pathlib import Path

APP_NAME = "叙事工坊"
APP_VERSION = "0.2.0"
PACKAGE_ID = "org.narrativeforge.narrativeforge"


def app_dir() -> Path:
    """应用根目录（含 main.py；打包后即 APK private 根）。"""
    # main.py 位于 android/；app 包位于 android/app
    return Path(__file__).resolve().parent.parent


def mobile_home() -> Path:
    """模块数据目录。优先环境变量，其次 Android 私有目录，最后用户主目录。"""
    env = os.environ.get("NARRATIVE_FORGE_HOME")
    if env:
        return Path(env).expanduser()
    priv = os.environ.get("ANDROID_PRIVATE") or os.environ.get("ANDROID_APP_PATH")
    if priv:
        return Path(priv) / ".NarrativeForge"
    return Path.home() / ".NarrativeForge"


def seed_dir() -> Path:
    """内置种子源（由 scripts/sync_android.sh 从仓库根同步生成）。"""
    return Path(__file__).resolve().parent / "seed"