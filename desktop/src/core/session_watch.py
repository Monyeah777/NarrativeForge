#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**长驻会话**（`nf shell`）的两层缓存：监听 + 常驻语料层 + **响应缓存**。

依据（实测 2026-09-29）：会话里连跑重命令时每条都要重读整棵语料取指纹——`score` 实测
**554 ms/条**；接上「监听 ⇒ 常驻层精确失效」后 **34 ms/条（16×）**。再往下一层：**树没变 +
命令纯读 ⇒ 整条响应复用**（与守护同一套判据，见 `core.response_cache`）——`stats --check`
实测 158 → 1 ms/条。命中不改变任何输出：回放的就是上一次捕获到的同一份字节。

纪律（缺一不可，全部 fail-closed）：监听不可用/不健康/启动失败 ⇒ **两层都不装**（逐字退回
原路径）；说得清变了什么 ⇒ 只失效那几件；说不清 ⇒ 整批作废；会话退出（正常/异常）一律
`release()`，不留跨会话残影。
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Optional

_WATCHER: Optional[Any] = None


def _install(root, watcher) -> None:
    """把监听登记成**本进程**的树代际来源并维护一次常驻层（`watcher=None` = 注销 + 整批作废）。

    这里直接借守护的 `_WATCHER` / `_sync_resident`（本仓既有做法：`disk_cache` 也直接调
    `conformance_scan._payload_digest`）——两者本就是**同一套状态与同一条 fail-closed 纪律**，
    另起一层公共 API 只会让「谁维护代际」有两种说法。
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
    """会话收尾：注销监听 + 整批作废常驻层与响应缓存（正常与异常路径都要调）。"""
    global _WATCHER
    from core import response_cache as _rc
    _WATCHER = None
    _install(None, None)
    _rc.clear()


def _wrap(base, root):
    """给 runner 套上响应缓存（判据/捕获/回放都在 `core.response_cache`；这里提供代际与同步）。"""
    from core import daemon as _dm
    from core import response_cache as _rc
    return _rc.wrap_runner(
        base,
        lambda argv: (_dm._watch_generation(), _dm.cacheable(argv)),
        lambda: sync(root))


@contextmanager
def _attached(root):
    """装上监听 ⇒ 套缓存 runner；收尾一律 `release`（装不上 ⇒ 调用方逐字走原路径）。"""
    ok = root is not None and attach(root)
    try:
        yield ok
    finally:
        if ok:
            release()


def run_session(runner, stdin, stdout, watch_root=None, **kw) -> int:
    """`terminal.run_session` 的**带会话缓存**包装（`nf shell` 走这条）。"""
    from core import terminal as _term
    with _attached(watch_root) as ok:
        return _term.run_session(_wrap(runner, watch_root) if ok else runner,
                                 stdin, stdout, **kw)


def run_script(script, runner, watch_root=None, **kw) -> tuple:
    """`terminal.run_script`（`--exec "cmd1; cmd2"`）的带会话缓存包装。"""
    from core import terminal as _term
    with _attached(watch_root) as ok:
        return _term.run_script(script, _wrap(runner, watch_root) if ok else runner, **kw)


def run_file(path, runner, watch_root=None, **kw) -> tuple:
    """`terminal.run_file`（`nf shell --file tour.nf`）的带会话缓存包装。"""
    from core import terminal as _term
    with _attached(watch_root) as ok:
        return _term.run_file(path, _wrap(runner, watch_root) if ok else runner, **kw)
