#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**长驻会话**（`nf shell`）的监听 + 常驻语料层：与守护**同一套** fail-closed 纪律。

依据（实测 2026-09-29）：会话里连跑重命令时每条都要重读整棵语料取指纹——`score` 实测
**554 ms/条**（10 条 6.6 s）。而守护早就有「监听给出确知变更面 ⇒ 常驻层精确失效」这一层
（`daemon._sync_resident`）；会话本来就是长驻进程，缺的只是把它接上。接上后同一实验
**34 ms/条（16×）**。命中不改变任何输出：常驻层只换「怎么读到同一份字节」，值逐位相同
（既有 `ResidentRawEquivalenceTest` 等判据守着）。

纪律（缺一不可，全部 fail-closed）：
- 监听**不可用/不健康/启动失败** → 不装（`run_session` 退回原样跑），行为与今天完全一致；
- 每条命令前 `sync()`：监听说不清变了什么 ⇒ 整批作废重建；说得清 ⇒ 只失效那几件；
- 会话退出（正常/异常）**一律** `release()`：注销监听 + 整批作废，不留跨会话残影。
"""
from __future__ import annotations

from typing import Any, Optional

_WATCHER: Optional[Any] = None


def _install(root, watcher) -> None:
    """把监听登记成**本进程**的树代际来源并维护一次常驻层。

    这里直接借守护的 `_WATCHER` / `_sync_resident`（本仓既有做法：`disk_cache` 也直接调
    `conformance_scan._payload_digest`）——两者本就是**同一套状态与同一条 fail-closed 纪律**，
    另起一层公共 API 只会让「谁维护代际」有两种说法；`watcher=None` ＝ 注销并整批作废。
    """
    from core import conformance_scan as _csc
    from core import daemon as _dm
    _dm._WATCHER = watcher
    if watcher is None:
        _csc.clear_resident()
    else:
        _dm._sync_resident(root)


def attach(root) -> bool:
    """装监听 + 常驻层（本进程内）。返回是否装上；任何一步不成 ⇒ False（不抛、不降级语义）。"""
    global _WATCHER
    from core import daemon as _dm
    from core import watch as _watch
    try:
        if not _watch.available():
            return False
        watcher = _watch.DirWatcher(root)
        if not watcher.start():
            return False
    except Exception:                                    # noqa: BLE001 - 装不上就照旧跑
        return False
    _WATCHER = watcher
    _install(root, watcher)
    return True


def sync(root) -> None:
    """每条命令前调：按监听的「确知变更面」维护常驻层（未装监听时是空操作）。"""
    if _WATCHER is None:
        return
    _install(root, _WATCHER)


def release() -> None:
    """会话收尾：注销监听 + 整批作废常驻层（正常与异常路径都要调）。"""
    global _WATCHER
    if _WATCHER is None:
        return
    _WATCHER = None
    _install(None, None)


def run_session(runner, stdin, stdout, watch_root=None, **kw) -> int:
    """`terminal.run_session` 的**带会话缓存**包装（`nf shell` 走这条）。

    装上就：① 每条命令前按监听失效常驻层；② 退出（含异常）注销并整批作废。
    装不上就**逐字**走原路径（不新增任何行为差异）。
    """
    from core import terminal as _term
    attached = watch_root is not None and attach(watch_root)
    if attached:
        base = runner

        def runner(argv, *a, **k):                       # noqa: F811 - 有意遮蔽
            sync(watch_root)
            return base(argv, *a, **k)
    try:
        return _term.run_session(runner, stdin, stdout, **kw)
    finally:
        if attached:
            release()


def run_script(cmds, runner, watch_root=None, **kw):
    """`terminal.run_script`（`--exec "cmd1; cmd2"`）的带会话缓存包装。"""
    from core import terminal as _term
    attached = watch_root is not None and attach(watch_root)
    if attached:
        base = runner

        def runner(argv, *a, **k):                       # noqa: F811 - 有意遮蔽
            sync(watch_root)
            return base(argv, *a, **k)
    try:
        return _term.run_script(cmds, runner, **kw)
    finally:
        if attached:
            release()


def run_file(path, runner, watch_root=None, **kw):
    """`terminal.run_file`（`--file 脚本`）的带会话缓存包装。"""
    from core import terminal as _term
    attached = watch_root is not None and attach(watch_root)
    if attached:
        base = runner

        def runner(argv, *a, **k):                       # noqa: F811 - 有意遮蔽
            sync(watch_root)
            return base(argv, *a, **k)
    try:
        return _term.run_file(path, runner, **kw)
    finally:
        if attached:
            release()
