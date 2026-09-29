"""POSIX shell 解析（跨平台「一键复现」入口 · Windows 上不再崩栈）。

为什么需要：`nf release` 要跑 `verify.sh` 与 `scripts/per_module_coverage.sh`，两者都要 POSIX
shell。原先写死 `["bash", ...]` —— Windows 上 `bash` 不在 PATH 时 subprocess 直接
`FileNotFoundError: [WinError 2]` 崩栈（实测 2026-09-29），多平台「一键复现」就此断链，
而现场明明装着 Git for Windows（`git` 在 PATH 里，bash 就在它旁边）。

解析顺序（只读；不静默换成别的解释器）：
0. 显式覆盖 `NF_BASH`（诊断/异形安装位用）；
1. PATH 里的 `bash` / `sh`；
2. Windows：从 `git` 的位置反推 Git for Windows 自带的 `<git-root>/bin/bash.exe`；
3. 常见 Unix 绝对路径 `/bin/bash`、`/usr/bin/bash`、`/bin/sh`、`/usr/bin/sh`。

解析不到时**打印修复指引并 exit 1**（fail-closed）：宁可当场报「缺 shell」，
也不静默降级成一个跑不了 verify.sh 的假成功。
"""
from __future__ import annotations

import os
import shutil
import sys

#: PATH 被裁剪时的兜底绝对路径（Unix 常规安装位）。
UNIX_FALLBACKS = ("/bin/bash", "/usr/bin/bash", "/bin/sh", "/usr/bin/sh")


def posix_shell() -> str:
    """→ POSIX shell 的可用路径；解析不到 → 打印修复指引并 `sys.exit(1)`。"""
    env = os.environ.get("NF_BASH") or ""
    found = env if os.path.isfile(env) else (shutil.which("bash") or shutil.which("sh"))
    if not found and os.name == "nt":
        git = shutil.which("git")
        if git:
            # Git for Windows 布局：<root>/cmd/git.exe + <root>/bin/bash.exe
            found = os.path.join(os.path.dirname(os.path.dirname(git)), "bin", "bash.exe")
    for cand in (found,) + UNIX_FALLBACKS:
        if cand and os.path.isfile(cand):
            return cand
    print("  缺 POSIX shell：verify.sh 需要 bash（修复指引：装 Git for Windows / WSL，"
          "或把 bash 放进 PATH）", file=sys.stderr)
    sys.exit(1)
