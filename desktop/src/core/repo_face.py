"""仓库件判据（扫描面的**单一出处**）：扫描面 = 仓库件，不含 VCS / 工具缓存 / 被忽略的生成物。

为什么单独成模块（2026-10-03 实证）：扫描器此前各持一份硬编码排除表（`text_hygiene.EXCLUDE_DIRS`
与若干测试里的 `SKIP_PARTS`），且**只走文件系统、不看 `.gitignore`**——于是生成物只要落在树里，
就会以「第二份正文」的身份进面。npm 一键包把受跟踪文件暂存成 `packaging/npm/payload/`（已
gitignore）后，CoT 泄漏 / 文档路径可达 / 编码卫生三处**同时假红**；`engine/dotnet/RUNBOOK.md`
也记过同一瑕疵（构建产物撞编码卫生）。判据收在这里，扫描面只许调用 `walk_repo_paths`。

真源分两层：
- `SKIP_DIR_NAMES`：与 `.gitignore` 无关也一律不进的目录名（VCS / 工具缓存 / 依赖树）；
- `.gitignore` 覆盖面：由 **git 自己判**（`git -C <root> ls-files -o -i --exclude-standard
  --directory`）——「什么不算仓库件」是版本库的既定事实，不由各扫描器各写一份猜测。
非 git 目录 / git 不在场 → 忽略面为空（闸门只做加法，退回静态目录名）。

纪律：纯标准库；不写盘；无网络；同输入同输出。
"""
from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - 只跑 `git -C <root> ls-files`（argv 列表、无 shell、路径经 which 解析）
from pathlib import Path
from typing import Iterator, Set

#: 与 `.gitignore` 无关也一律不进扫描面的**目录名**（VCS 元数据 / 工具缓存 / 依赖树）。
SKIP_DIR_NAMES = frozenset({
    ".git", ".rivet", "__pycache__", ".ruff_cache", ".mypy_cache",
    ".pylint.d", ".pytest_cache", ".tox", ".venv", "venv", "node_modules",
})


def _git_executable() -> str:
    """git 的**绝对路径**（裸名走 PATH 有 cwd 劫持面，与 attest / storage 同口径）；无则空串。"""
    return shutil.which("git") or ""


def ignored_paths(root: str) -> Set[str]:
    """根下**被 `.gitignore` 覆盖**的路径集（posix 相对、已去尾斜杠；目录覆盖其下全部）。

    git 不在场 / 调用失败 / 非 git 检出（含临时目录里的单测）→ 返回空集。
    """
    exe = _git_executable()
    if not exe:
        return set()
    try:
        proc = subprocess.run(  # nosec B603  # noqa: S603 - argv 列表、无 shell、子命令固定
            [exe, "-C", str(root), "ls-files", "-o", "-i", "--exclude-standard",
             "--directory", "-z"],
            capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return set()
    if proc.returncode != 0:
        return set()
    out: Set[str] = set()
    for raw in proc.stdout.decode("utf-8", "replace").split("\0"):
        rel = raw.strip().replace("\\", "/").strip("/")
        if rel and ".." not in rel.split("/"):
            out.add(rel)
    return out


def is_ignored(rel: str, ignored: Set[str]) -> bool:
    """`rel`（根内相对）是否落在 `ignored`（`ignored_paths` 的产出）里——含其子路径。"""
    path = str(rel or "").replace("\\", "/").strip("/")
    if not path:
        return False
    for entry in ignored:
        if path == entry or path.startswith(entry + "/"):
            return True
    return False


def walk_repo_paths(root: str) -> Iterator[Path]:
    """遍历**仓库件**（跳过 `SKIP_DIR_NAMES` 与 `.gitignore` 覆盖面）→ 逐个产出 `Path`。"""
    root_abs = os.path.abspath(str(root))
    ignored = ignored_paths(root_abs)
    for dirpath, dirnames, filenames in os.walk(root_abs):
        rel_dir = os.path.relpath(dirpath, root_abs).replace(os.sep, "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        keep = []
        for name in dirnames:
            if name in SKIP_DIR_NAMES:
                continue
            rel = ("%s/%s" % (rel_dir, name)) if rel_dir else name
            if is_ignored(rel, ignored):
                continue
            keep.append(name)
        dirnames[:] = keep
        for name in filenames:
            rel = ("%s/%s" % (rel_dir, name)) if rel_dir else name
            if is_ignored(rel, ignored):
                continue
            yield Path(dirpath) / name
