#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解释器「节食」自愈：用 `-S` 起解释器省掉 site 定制，同时把 site-packages 显式加回来。

依据（2026-09-29 实测，min-of-N）：
- **省下什么**：解释器启动里 site 一档 ≈ 88 ms 累计（`pywin32_bootstrap` 33 ms + `_distutils_hack`
  22 ms + `usercustomize` / `sitecustomize`），而本仓核心层零第三方依赖 ⇒ `python -S -c pass`
  **205 → 141 ms**、`python -S scripts/nf.py --version` **697 → 570 ms**（CJK 输出 md5 逐字节一致）。
- **不省什么（关键）**：`-S` 会把 site-packages 一起关掉。后果**不是「慢一点」而是「静默算错」**：
  缺 PyYAML 时 `lazy_yaml` 按设计退回内置子集解析器，实测 `nf doctor` 的 `tool_face` 1/1/1 →
  0/0/0、`world_model` 1/4/3/4 → 0/0/0/0、`jsonschema` 一行从「CI 与本地同跑」变成「可选依赖未装」。
  故「加回目录」是**正确性要求**，不是优化。
- **为什么加目录就够**：`.pth` 的副作用只是把路径挂上（本机那两条是 pywin32 的 DLL 目录与
  setuptools 的 distutils 垫片，仓库都不 import）；显式 `sys.path.append` 只保留**可导入性**，
  不吃启动税。跨模式行为等价由 `desktop/tests/test_launcher.py` 逐字节比对钉住。
"""
from __future__ import annotations

import os
import sys


def site_dirs() -> list:
    """当前解释器的 site-packages 目录表（含 user site；`-S` 下也拿得到，只是没被自动挂上）。"""
    import site
    dirs = list(getattr(site, "getsitepackages", lambda: [])())
    getuser = getattr(site, "getusersitepackages", None)
    if getuser is not None:
        try:
            dirs.append(getuser())
        except Exception:                      # noqa: BLE001 - 拿不到就少挂一条，不影响主流程
            pass
    return [d for d in dirs if d and os.path.isdir(d)]


def restore() -> list:
    """把 site-packages 目录显式加回 `sys.path`（已在就跳过）→ 返回实际追加的目录。

    幂等：普通解释器里就是一轮 `isdir` 判断，调用方不必先判 `sys.flags.no_site`。
    """
    added = []
    for d in site_dirs():
        if d not in sys.path:
            sys.path.append(d)
            added.append(d)
    return added


def available(names=("yaml", "jsonschema")) -> str:
    """本解释器下可导入的第三方名（逗号连接）——启动器用它比对「节食 / 普通」两模式是否等价。"""
    import importlib.util
    return ",".join(n for n in names if importlib.util.find_spec(n) is not None)

