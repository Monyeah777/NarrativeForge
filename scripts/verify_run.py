#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跑 verify.sh（自动解析 POSIX shell）——「一键复现」的跨平台入口。

为什么需要：全量门禁本体是 POSIX shell 脚本，`bash verify.sh` 在 Windows 上只在 Git bash
进了 PATH 时可用（不在时 subprocess 直接 WinError 2）。本入口用 `core.posix_shell` 解析
shell（PATH → Git for Windows 反推 → Unix 常规位），把「一键复现」做成三平台同一条命令。

用法：
  python scripts/verify_run.py            # 跑全量门禁（退出码 = verify.sh 的退出码）
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import posix_shell as psh  # noqa: E402


def main() -> int:
    argv = [psh.posix_shell(), "verify.sh"]
    print("== 一键复现：%s（cwd=%s）" % (" ".join(argv), ROOT))
    return subprocess.run(argv, cwd=ROOT).returncode  # nosec B603/B607 —— argv 列表、无 shell


if __name__ == "__main__":
    # stdio 钉 UTF-8（2026-10-01）：同一纪律——中文结论行不该依赖宿主控制台编码。
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
