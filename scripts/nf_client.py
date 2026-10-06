#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NF 守护快路客户端（**纯 stdlib**，`python -S` 可跑）——Windows 默认路径的毫秒级入口。

用法（`scripts/nf.cmd` 调用；POSIX 侧由 `scripts/nf` 的 bash 内建客户端负责，两者同语义）：

    python -S scripts/nf_client.py <nf 子命令…>

语义（**只加速、不改可用性**，与 `scripts/nf` 的 `daemon_try` 同口径）：

1. 拿不到守护（无状态文件 / 连不上 / 协议头不是数字 / 长驻与自指命令）→ **退出码 111**，
   调用方据此回退 python 直跑；
2. 拿到守护 → 把命令经**明文 `NFREQ` 帧**交给守护（与 `scripts/nf` 的 bash 客户端同一套框），
   **原样写出 stdout / stderr 字节**并以命令自身退出码退出；
3. 默认路径开：没有守护时**非阻塞**后台拉起带 `--watch` 的守护（`NF_AUTOSTART=0` 可关），
   本条命令照常回退——与 POSIX 启动器同一取舍（首条只多一次 fork，从第二条起落快路）。

为什么要有这个文件（2026-10-01 取证）：`scripts\\nf.cmd` 走 python 直跑，实测 ≈391 ms/条，
而 POSIX 侧有 bash 内建快路（≈132 ms）——**同一条命令两条平台两种量级**，Windows 上的
agent 密集重复调用拿不到「稳态毫秒级」。本客户端把「解释器节食（-S）+ 一次套接字往返」
做到 ≈50–90 ms：不 import 仓库任何模块，只读状态文件、发帧、回写字节。

边界：本文件**不**执行业务逻辑，命令真源仍是 `scripts/nf.py`；长驻/自指命令一律不接
（与 `core.daemon.REFUSED_COMMANDS` 同集合，由 `test_daemon_parity` 的集合判据钉住）。
"""
from __future__ import annotations

#: 热路径只 import 这三个（`python -S` 下实测：裸解释器 23 ms，+os/socket ≈ 40 ms；
#: 而 `json` 单独就要 +16 ms -> 状态文件与请求框都按**与 `scripts/nf` 同一套**读法处理：
#: 明文 `NFREQ` 框 + 字符串定位，不用 JSON 编解码器。`subprocess`/`time` 只在自动拉起路径里懒加载。）
import os
import socket
import sys

#: 「快路不接手」的退出码：调用方（`scripts/nf.cmd` / 测试）据此回退直跑。
FALLBACK = 111
#: 与 `core.daemon.PROTO` 同值（协议版本）。
PROTO = 1
#: 长驻/自指命令：本客户端一律不接（集合与 `core.daemon.REFUSED_COMMANDS` 逐项一致，判据钉住）。
LONG_RUNNING = ("daemon", "shell", "terminal", "serve", "lsp")
#: 自动拉起标记的 60 s 自愈窗口（同 `scripts/nf`：崩溃/半途失败不会永久封住）。
START_MARKER_TTL = 60.0


def _home() -> str:
    env = os.environ.get("NARRATIVE_FORGE_HOME")
    return os.path.expanduser(env) if env else os.path.join(os.path.expanduser("~"),
                                                            ".NinFenz")


def _read_state():
    """→ `(port, token)`；不可用时抛 OSError/ValueError（调用方按回退处理）。

    读法与 `scripts/nf` 的 bash 客户端**同一套**（字符串定位，不引 JSON 编解码器）：
    状态文件由 `core.daemon.write_state` 单行 JSON 落盘，两个键的形态固定。
    """
    with open(os.path.join(_home(), "daemon.json"), encoding="utf-8") as fh:
        raw = fh.readline()
    if '"port": ' not in raw or '"token": "' not in raw:
        raise ValueError("状态文件缺 port/token"
                         "（修复指引：删掉 <NF_HOME>/daemon.json 后 `nf daemon start` 重起守护）")
    port = raw.split('"port": ', 1)[1].split(",", 1)[0].strip()
    token = raw.split('"token": "', 1)[1].split('"', 1)[0]
    if not port.isdigit() or not token:
        raise ValueError("状态文件 port/token 形态不对"
                         "（修复指引：删掉 <NF_HOME>/daemon.json 后 `nf daemon start` 重起守护）")
    return int(port), token


def _serve(argv) -> int:
    """把命令交给守护；成功即写字节并返回其退出码。任何连接层问题抛异常（调用方回退）。"""
    port, token = _read_state()
    # **明文框是逐行 argv**：参数含换行会被拆开、静默改变参数个数 -> 这类命令不接快路
    # （与 `scripts/nf` 的 daemon_try 同口径）。
    for arg in argv:
        if "\n" in str(arg):
            raise ValueError("参数含换行，明文框无法精确传递"
                             "（修复指引：本客户端会回退 python 直跑，命令本身无需改动）")
    with socket.create_connection(("127.0.0.1", port), timeout=30.0) as sock:
        sock.settimeout(30.0)
        frame = ["NFREQ %d %s" % (PROTO, token), os.getcwd(), str(len(argv))] + [str(a) for a in argv]
        sock.sendall(("\n".join(frame) + "\n").encode("utf-8"))
        fh = sock.makefile("rb")
        head = []
        for _ in range(3):
            line = fh.readline()
            if not line:
                raise OSError("响应头被截断（修复指引：本客户端会回退直跑；反复出现请"
                              "`nf daemon stop && nf daemon start`）")
            head.append(line.strip())
        try:
            code = int(head[0])
            out_len, err_len = int(head[1]), int(head[2])
        except ValueError as exc:
            raise OSError("协议头不是数字：%r（修复指引：本客户端会回退直跑；端口被别的"
                          "服务占用时 `nf daemon stop && nf daemon start`）" % (head,)) from exc
        out = fh.read(out_len) if out_len else b""
        err = fh.read(err_len) if err_len else b""
    if out:
        sys.stdout.buffer.write(out)
        sys.stdout.buffer.flush()
    if err:
        sys.stderr.buffer.write(err)
        sys.stderr.buffer.flush()
    return code


def _maybe_autostart() -> bool:
    """没有守护时**非阻塞**拉起一个（默认开；`NF_AUTOSTART=0|false|no|off` 关）。→ 是否真的发起。"""
    import subprocess  # nosec B404 - 只用来拉起守护（argv 列表、无 shell、路径自仓库，同 attest.py 口径）
    import time

    if (os.environ.get("NF_AUTOSTART") or "1").lower() in ("0", "false", "no", "off"):
        return False
    home = _home()
    marker = os.path.join(home, "daemon.starting")
    now = time.time()
    try:
        with open(marker, encoding="utf-8") as fh:
            prev = float(fh.read().strip() or 0)
    except (OSError, ValueError):
        prev = 0.0
    if now - prev < START_MARKER_TTL:
        return False                      # 上一轮已经拉过 -> 连发命令不重复拉（防赛出多个守护）
    try:
        os.makedirs(home, exist_ok=True)
        # 落盘走仓库统一的原子写（`core.atomic_write`，脚本面落盘单一出处）。**只在自动拉起
        # 这条冷路径导入**：热路径（读状态 → 发帧 → 回写字节）仍然不 import 仓库任何模块。
        _src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "desktop", "src")
        if _src not in sys.path:
            sys.path.insert(0, _src)
        from core import atomic_write              # noqa: PLC0415
        atomic_write.write_text(marker, "%.0f\n" % now)
    except (OSError, ImportError):
        marker_ok = False                 # 标记写不进 -> 本轮不保证「串行化」，但仍照常回退
    else:
        marker_ok = True
    root = os.path.dirname(os.path.abspath(__file__))
    cmd = [sys.executable, "-S", os.path.join(root, "nf.py"), "daemon", "start", "--watch"]
    flags = 0
    if os.name == "nt":                   # 脱离控制台：不占本条命令的时间，也不随父进程死
        flags = 0x00000008 | 0x00000200   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    try:
        subprocess.Popen(  # noqa: S603  # nosec B603 - argv 列表、无 shell、路径自仓库
            cmd, cwd=root, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags, start_new_session=(os.name != "nt"))
    except OSError:
        return False
    return marker_ok


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and str(argv[0]) in LONG_RUNNING:
        return FALLBACK                   # 占住前台的命令：交调用方直跑（不进守护，也不拉起守护）
    try:
        return _serve(argv)
    except Exception:                     # noqa: BLE001 - 回退是设计面：任何连接层问题都不改可用性
        if argv:
            _maybe_autostart()
        return FALLBACK


if __name__ == "__main__":
    raise SystemExit(main())
