"""探针默认路径的**唯一出处**（可移植，无作者机器路径）。

为什么要有这个文件：42 条探针原来各自把编制者的机器路径写死在常量里
（`C:\\Users\\<作者>\\Downloads\\NF-NET-engine\\...`）。这些仪器现在要进仓库给别人用，
默认值写死等于"只有我这台机器能跑"。这里改成**按环境变量或相对位置派生**：

    NF_ENGINE_ROOT    引擎工作区根（缺省 = 本文件上一级目录）
    NF_SNAPSHOT       金标快照（缺省 = 引擎工作区同级的 nf-snap-h5）
    NF_SNAPSHOT_OTHER 对照快照（缺省 = 同级的 nf-snap-h6）
    NF_RECORDS_DIR    具名记录件所在目录（缺省 = 引擎工作区同级）
    NF_PYTHON / NF_DOTNET / NF_BASH   解释器与工具（缺省 = 宿主解释器 / PATH 上的 dotnet、bash）

任何探针都只是**默认值**引用这里；命令行参数（`--snap`/`--cli`/…）依旧优先。
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ENGINE: Path = Path(os.environ.get("NF_ENGINE_ROOT") or HERE.parent.parent)
_SIBLING: Path = ENGINE.parent

RECORDS_DIR: str = os.environ.get("NF_RECORDS_DIR") or str(_SIBLING)
#: 金标基线快照。**第一百二十一片复基线**：真源前移到 348577d 后，基线从 `nf-snap-h5` 移到 `nf-snap-h7`
#: （h5 留作「上一版基线」，用于语料身份/漂移归因的对照）。
SNAP: str = os.environ.get("NF_SNAPSHOT") or str(_SIBLING / "nf-snap-h16")
SNAP_OTHER: str = os.environ.get("NF_SNAPSHOT_OTHER") or str(_SIBLING / "nf-snap-h5")
ENGINE_ROOT: str = str(ENGINE)
FIXTURES: Path = ENGINE / "probes" / "_fixtures"

PY: str = os.environ.get("NF_PYTHON") or sys.executable
DOTNET: str = os.environ.get("NF_DOTNET") or (shutil.which("dotnet") or "dotnet")
BASH: str = os.environ.get("NF_BASH") or (shutil.which("bash") or "bash")


def engine(*parts: str) -> str:
    """引擎工作区内的路径（字符串，供 argparse 默认值用）。"""
    return str(ENGINE.joinpath(*parts))


def records(name: str) -> str:
    """具名记录件的路径（引擎工作区同级目录）。"""
    return str(Path(RECORDS_DIR) / name)


def snap_src(snap: str | None = None) -> str:
    """快照里的真源 Python 源码目录（`<snap>/desktop/src`）。"""
    return str(Path(snap or SNAP) / "desktop" / "src")


def portable(path: str | Path) -> str:
    """绝对路径 → **便携标签**（只留末段目录名）。

    金标注据会进仓库、给别人用——写成绝对路径既是**作者机器路径泄漏**，也让记录只在
    一台机器上可解释。证据里一律只留标签（如 `nf-snap-h16`），机器相关的路径由调用方
    自己的 `NF_SNAPSHOT` 决定。
    """
    name = Path(str(path)).name
    return name or "<snapshot>"


def newest_dist(rid: str) -> Path:
    """`dist/` 下该 RID 的最大 `fNN` 交付形态目录；找不到时返回当前目录（调用方一般都会显式覆盖）。"""
    best, best_n = Path("."), -1
    root = ENGINE / "dist"
    if not root.is_dir():
        return best
    for d in root.glob(f"nf-dotnet-{rid}-f*-*"):
        parts = d.name.split("-f")
        if len(parts) > 1:
            try:
                n = int(parts[1].split("-")[0])
            except ValueError:
                continue
            if n > best_n:
                best_n, best = n, d
    return best
