#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""响应缓存：**树代际 ⇒ 整条命令响应**（守护 `daemon.execute` 与长驻会话 `session_watch` 共用）。

这两条路径做的是**同一件事**——「树没变 + 命令纯读 ⇒ 回放同一份字节」。判据与账本放一处，
「什么可缓存、何时作废」就只有一种说法；分散两处必然漂移（本仓既有教训：`disk_cache` 的
说明里写过「接了线但没生效」这类最难发现的假绿）。

纪律（fail-closed，与守护/会话其余部分同源）：
- **代际不可知（监听不可用）⇒ 一律不命中，且旧响应整批作废**：宁可全废，不可错答；
- 只存「准入表命中 + 无写盘开关 + 退出码 0」的响应；
- **任何非准入命令（可能写仓库）⇒ 立刻整批作废**，不等监听线程异步察觉（竞态判据见 test_watch）。
"""
from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, Optional, Sequence, Tuple

#: 观测计数（`nf daemon status` 显示；单测**就地清零**，故必须是同一个字典对象）。
STATS: Dict[str, int] = {"hits": 0, "misses": 0, "stores": 0, "skipped": 0}
#: 上限：超出即整批清空（宁可重算，不可无界增长）。
MAX_ENTRIES = 256
_CACHE: Dict[Any, Tuple[int, int, bytes, bytes]] = {}


def entries() -> int:
    """当前缓存条目数（观测面）。"""
    return len(_CACHE)


def clear() -> None:
    """整批作废（监听不可用 / 非准入命令 / 超过上限）。"""
    _CACHE.clear()


def key(argv: Sequence[Any], cwd: Optional[str] = None) -> Tuple[Any, ...]:
    """缓存键含**会改变输出文本**的环境面：`terminal` 按 NO_COLOR / CLICOLOR_FORCE 决定是否着色，
    不含它就会出现「在无色环境里回放了带 ANSI 的旧响应」。"""
    return (tuple(str(a) for a in argv), cwd or os.getcwd(),
            os.environ.get("NO_COLOR", ""), os.environ.get("CLICOLOR_FORCE", ""))


def lookup(argv: Sequence[Any], gen: Optional[int], allowed: bool,
           cwd: Optional[str] = None) -> Optional[Tuple[int, bytes, bytes]]:
    """→ (code, out, err) 命中；None = 未命中 / 非准入 / 代际不可知（并记账、按需整批作废）。"""
    if gen is None:
        if _CACHE:
            clear()
        if allowed:
            STATS["skipped"] += 1
        return None
    if not allowed:
        return None
    hit = _CACHE.get(key(argv, cwd))
    if hit is not None and hit[0] == gen:
        STATS["hits"] += 1
        return hit[1], hit[2], hit[3]
    STATS["misses"] += 1
    return None


def store(argv: Sequence[Any], gen: Optional[int], allowed: bool, code: int,
          out: bytes, err: bytes, cwd: Optional[str] = None) -> None:
    """只存「准入 + 成功」的响应；非准入/失败请调 `note_uncacheable()`。"""
    if gen is None or not allowed or code != 0:
        return
    if len(_CACHE) >= MAX_ENTRIES:
        clear()
    _CACHE[key(argv, cwd)] = (int(gen), int(code), bytes(out), bytes(err))
    STATS["stores"] += 1


def note_uncacheable(allowed: bool, code: int = 0, gen: Optional[int] = None) -> None:
    """非准入（无法证明只读）或失败 ⇒ 记账并**立刻整批作废**，不等监听线程异步察觉。

    竞态（实测判据 `test_watch.test_unknown_command_invalidates_*`）：只靠监听的话有几十毫秒
    窗口，脚本里 `nf conformance --write; nf score` 连跑就能吃到写之前的旧响应。
    """
    if gen is None:
        return
    if not allowed:
        STATS["skipped"] += 1
    if _CACHE and not (allowed and code == 0):
        clear()


def _text(buf: io.BytesIO) -> io.TextIOWrapper:
    """BytesIO → **写通**的 UTF-8 文本层（命令按文本写、捕获按字节存 ⇒ 回放逐字节等值）。

    `newline=""` 是**必须**的：默认值会在 Windows 上把 `\\n` 翻成 `\\r\\n`，于是回放的字节与
    原路径不同（实测踩到），进而在会话捕获层里再翻一次变成 `\\r\\r\\n`。
    """
    return io.TextIOWrapper(buf, encoding="utf-8", write_through=True, newline="")


def _replay(out: bytes, err: bytes) -> None:
    """把捕获到的字节**原样**回到当前 stdout/stderr（捕获层是文本流时就解码回写）。"""
    for stream, blob in ((sys.stdout, out), (sys.stderr, err)):
        if not blob:
            continue
        buf = getattr(stream, "buffer", None)
        if buf is None:
            stream.write(blob.decode("utf-8", "replace"))
        else:
            buf.write(blob)
        stream.flush()


def wrap_runner(base, decide, sync=None):
    """把**会话 runner** 包成「常驻层同步 + 响应缓存」的 runner（守护之外的第二处呼叫点）。

    命中即回放同一份字节、不重算；**非准入**（无法证明只读）⇒ 原样跑（写盘闸门照旧）再整批
    作废；准入命令捕获 stdout/stderr 后再回放并入库。`decide(argv) -> (代际, 是否准入)` 由调用方
    给出（会话传 `daemon._watch_generation` + `daemon.cacheable`）⇒ 本模块**不依赖上层**，
    避免「稳定模块反过来依赖不稳模块」（耦合判据会判红，实测）。`sync` = 每条命令前的常驻层
    同步回调；装不上监听时调用方**不套本包装**（逐字退回原路径）。
    """
    def runner(argv, *a, **k):                           # noqa: F811 - 有意遮蔽
        if sync is not None:
            sync()
        argv = [str(x) for x in argv]
        gen, allowed = decide(argv)
        allowed = bool(allowed)
        hit = lookup(argv, gen, allowed)
        if hit is not None:                              # 命中 = 树没变且命令纯读 ⇒ 回放同一份字节
            _replay(hit[1], hit[2])
            return hit[0]
        if not allowed:
            try:
                return base(argv, *a, **k)
            finally:
                note_uncacheable(allowed, 0, gen)
        out_buf, err_buf = io.BytesIO(), io.BytesIO()
        # 两个文本层必须**活到读走字节之后**：它们被回收时会连底层 BytesIO 一起关掉（实测踩到
        # `ValueError: I/O operation on closed file`），故不写成 `redirect_stdout(_text(...))`。
        out_txt, err_txt = _text(out_buf), _text(err_buf)
        code = 0
        try:
            with redirect_stdout(out_txt), redirect_stderr(err_txt):
                code = int(base(argv, *a, **k) or 0)
        finally:
            # **必须放 finally**：argparse 的 `--help` / 用法错误走 `SystemExit` 穿出 `with`——
            # 修复前回放被整段跳过 ⇒ **输出丢失**（实测：`nf shell --exec "nf stats --help"`
            # 只剩「结果：run（exit=0）」，帮助文本一个字都没有；参数错误同样只留 exit=2 而无
            # usage）。捕获层是适配器，不得吞掉被包装者的输出。SystemExit 在 finally 之后继续上抛
            # ⇒ 走到 `store` 的只有正常返回，失败/帮助路径不入缓存。
            out_txt.flush()
            err_txt.flush()
            out, err = out_buf.getvalue(), err_buf.getvalue()
            _replay(out, err)
        store(argv, gen, allowed, code, out, err)
        return code

    return runner
