#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PyYAML 的**惰性**入口：`import yaml` ≈ 40 ms，而缓存命中的冷跑根本不解析 YAML。

依据（实测 2026-09-29，`-X importtime`）：冷 `nf score` 的导入自时 184.6 ms 里 **yaml 子树 39.9 ms**
（22%），而派生结果全部命中落盘缓存时**一次都不解析**——那 40 ms 是纯浪费。于是把导入推迟到真要
用的时候；缺 PyYAML 一律返回 `None`，调用方维持既有「缺依赖即报」的语义（不吞不造）。

`conformance_scan` 另用 PEP 562 的 `__getattr__` 继续暴露 `yaml` / `SAFE_LOADER` 两个名字——
`pipeline_loader`（存在性探测）与其它调用方过去直接读它们，**名字不许消失**。
"""
from __future__ import annotations

import os

_YAML = None
_TRIED = False


def module():
    """PyYAML 模块（缺依赖 → None）；首次调用才真导入，之后记忆。"""
    global _YAML, _TRIED
    if not _TRIED:
        _TRIED = True
        try:
            import yaml as _m
            _YAML = _m
        except Exception:                                    # noqa: BLE001 - 缺依赖不是崩溃理由
            _YAML = None
    return _YAML


def safe_loader():
    """最快的**安全**加载器类（libyaml 的 C 实现优先）；缺依赖 → None。"""
    m = module()
    if m is None:
        return None
    return getattr(m, "CSafeLoader", None) or getattr(m, "SafeLoader", None)


def dist_version(name: str = "PyYAML") -> str:
    """**不导入**发行版就读到它的版本号（读不到 → `""`，调用方自行退回真导入）。

    依据（实测 2026-09-29）：`disk_cache.runtime_tag()` 只是要把 PyYAML 版本写进缓存键，而
    `import yaml` 本机 **34.5 ms**（yaml 子树 18 个模块）——冷跑每次都要付。直扫 `sys.path` 上的
    `<name>-<ver>.dist-info` 目录名只要 **0.7 ms**（`importlib.metadata` 反而 75 ms，因为它自己
    要导入 email/zipfile 一串）。**必须覆盖 user site**：本机 PyYAML 就装在 user site，
    `sysconfig.get_paths()["purelib"]` 里没有。
    """
    #: 前缀**大小写不敏感**：本机装出来的目录名是小写 `pyyaml-6.0.3.dist-info`（Windows 上
    #: `startswith` 仍然按大小写比，所以不能直接拿发行名去比）。
    prefix = (str(name).split("-")[0] + "-").lower()
    for base in os.sys.path:
        if not base or not os.path.isdir(base):
            continue
        try:
            for ent in os.scandir(base):
                low = ent.name.lower()
                if ent.is_dir() and low.startswith(prefix) and low.endswith(".dist-info"):
                    return ent.name[len(prefix):-len(".dist-info")].split("-")[0]
        except OSError:
            continue
    return ""
