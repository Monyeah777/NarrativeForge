#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NF 执行层常驻守护 —— 把「每条命令一次解释器启动」换成「一次启动、长期热跑」。

**为什么要它（本机实测，2026-09-28）**：裸解释器启动 **146 ms**、`nf --version` **401 ms**
（导入 + argparse ≈ 255 ms）——即**每条命令有 ~400 ms 的固定成本，与命令内容无关**；而同一
命令在热进程里只要 1–5 ms（命令面缓存 v12、内容键缓存 v14–v16 都已就位）。所以「执行层
毫秒级」= 把重活留在常驻进程里，客户端只做一次套接字往返。

**机制借鉴**（工业界的同一范式：`dmypy` / `emacsclient` / `nvim --server` / 语言服务器）：

- **服务端**：只绑 `127.0.0.1` 的 TCP 套接字；回环**不是**信任边界，故另发一次性令牌，
  请求必须带令牌才算数。**单线程串行**处理：不并发跑仓库命令（确定性优先）。
- **协议**（版本化、极简、**纯 bash 可当客户端**）：
    请求 = 一行 JSON：`{"proto":1,"token":"…","cwd":"…","argv":["stats","--check"]}`
    响应 = 三行明文头 + 原始载荷：`<exit>` + `<out_len>` + `<err_len>` + stdout 字节 + stderr 字节
  响应不用 JSON 的原因：客户端常是 shell——`read` 三行 + `head -c` 两个长度即可原样转发，
  不需要 JSON 解码器（也就没有 jq 依赖）。
- **状态**：`<NF_HOME>/daemon.json`（pid/port/token/root/started/proto），`NF_HOME` 复用
  `core.storage.default_home()` 单源；令牌不进日志。
- **新鲜度（关键纪律）**：每次请求前清空**按路径/根键**的进程缓存（`pack_combo` 画像、
  `registry_loader` 注册表），**保留内容键缓存**（围栏 YAML、引用度普查——键即内容，天然
  不陈旧）。于是「热进程」与「新起进程」结果一致：等价性由 `test_daemon` 逐命令比对守住。
- **拒绝面**：长驻/嵌套命令（`serve` / `shell` / `daemon`）在守护内一律拒跑（退出码 2）——
  与终端里「递归长驻拦截」同一条纪律。

边界：本模块**只加速、不改语义**；不写仓库文件（状态只落 NF_HOME）；杀掉守护进程即回到
原来的「每命令一次启动」路径（`scripts/nf` 会静默回退）。
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import secrets
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

PROTO = 1
#: 监听地址：**只允许回环**（与 scripts/serve_decision_model.py 同一条纪律；本模块不提供
#: 「显式放行外网」的开关——守护进程能执行任意 nf 命令，绝不能出回环）。
BIND_HOST = "127.0.0.1"
#: 请求体上限（1 MiB）：一条命令的 argv 远小于此；设上限防「自称超长」的无界读。
MAX_REQUEST_BYTES = 1 << 20
#: 单条 argv 上限（字符）：参数是「命令 + 选项 + 标识符」，不是正文载荷。
MAX_ARGV_CHARS = 8192
#: argv 合计上限（字符）：防「一条 1 MB 请求 → CLI 回吐 200 KB 用法」这类放大。
MAX_ARGV_TOTAL = 65536


def _check_argv_size(argv) -> None:
    """argv 体量上限 → 越界抛 ValueError（上层归「请求不可读」，exit 2）。

    修复前实测：单条 **200 KB** 的 argv 会被照单执行——CLI 回吐 200 KB 的 argparse 用法，
    请求体最大 1 MB 也兜不住这种放大。参数只该是命令/选项/标识符；正文请落盘后传路径。
    """
    if not isinstance(argv, list):
        return
    for a in argv:
        if isinstance(a, str) and len(a) > MAX_ARGV_CHARS:
            raise ValueError("单个参数超过上限 %d 字符（修复指引：正文/长文本先落盘，改传路径）"
                             % MAX_ARGV_CHARS)
    total = sum(len(a) for a in argv if isinstance(a, str))
    if total > MAX_ARGV_TOTAL:
        raise ValueError("参数合计超过上限 %d 字符（修复指引：减少参数，或改传文件路径）"
                         % MAX_ARGV_TOTAL)
#: 守护内**拒跑**的命令：长驻（`serve` / `shell` / `terminal` / `lsp`）与自指（`daemon`）。
#:
#: 为什么是这五个（2026-10-01 修）：此前只有 `serve` / `shell` / `daemon`，于是**别名与常驻面漏网**——
#: `nf terminal`（`shell` 的 argparse 别名）与 `nf lsp`（常驻 stdio 服务）会进守护在进程内执行，
#: 而守护把 stdin 设成空串 ⇒ `lsp` 立刻读到 EOF 后**以 0 退出且零输出**，调用方（编辑器 / agent）
#: 把「静默无事发生」当成成功，直跑却会真的起服务：**同一条命令两条路径两种结果**。
#: 口径：凡是会占住前台的命令，守护一律拒跑（集合与 `core.terminal.BLOCKED_IN_SHELL` 相等，
#: 由 `desktop/tests/test_daemon_parity.py` 的集合判据钉住；别名闭合同件）。
REFUSED_COMMANDS = ("serve", "shell", "terminal", "lsp", "daemon")
#: 连接读写超时（秒）：客户端卡住不得拖死守护。
SOCKET_TIMEOUT = 30.0
STATE_NAME = "daemon.json"

#: bash 快路模板（`nf daemon shell-init bash` 原样输出，供 `eval "$(…)"` 装进交互 shell）。
#: 关键点：**全部用 bash 内建**（/dev/tcp + printf + read -N），因此 `nf …` 是当前 shell 里的
#: 一次函数调用 + 一次套接字往返——没有子进程、没有解释器启动，这才是真正的毫秒级客户端。
#: 长驻/自指命令（见 `REFUSED_COMMANDS`）与「无参」一律直落 python 入口（与守护拒绝面一致）。
SHELL_INIT_BASH = """# NF 执行层快路（生成自 `nf daemon shell-init bash`）
# 用法：  eval "$(nf daemon shell-init bash)"        # 或写进 ~/.bashrc
# 卸载：  unset -f nf
# 注意（2026-09 实测缺陷）：解释器与脚本路径**必须加引号**——本机解释器路径是
# `C:\\Program Files\\Python311\\python.exe`，不加引号时回退那行会被 bash 拆成命令 `C:\\Program`，
# 于是守护不在（含默认 1 小时空闲自退之后）时 `nf <任何命令>` → **rc=127 + `C:Program: command not found`**。
# 语法检查抓不到这种错（它语法合法），所以判据必须是**行为级**的（见 test_launcher/test_daemon）。
nf() {
  case "${1:-}" in
    daemon|shell|terminal|serve|lsp|"") command "{py}" "{root}/scripts/nf.py" "$@"; return $? ;;
  esac
  # 明文框是**逐行** argv：参数里含换行会被拆开、**静默改变参数个数**（实测：`help` 收到
  # `line1\\nline2` 时只看到 `line1`）——这类命令一律不接快路，交 python 直跑
  # （JSON 框才支持任意字符；见 `_parse_request` 的说明）。
  local _nf_a="" _nf_nl=""
  for _nf_a in "$@"; do
    case "$_nf_a" in *$'\\n'*) _nf_nl=1 ;; esac
  done
  if [ -n "$_nf_nl" ]; then command "{py}" "{root}/scripts/nf.py" "$@"; return $?; fi
  local _state="${NARRATIVE_FORGE_HOME:-$HOME/.NarrativeForge}/daemon.json"
  local _s="" _rest="" _port="" _token=""
  if [ -f "$_state" ]; then
    IFS= read -r _s < "$_state" || _s=""
    case "$_s" in *'"port": '* ) ;; *) _s="" ;; esac
  fi
  if [ -n "$_s" ]; then
    _rest=${_s#*'"port": '}; _port=${_rest%%[!0-9]*}
    _rest=${_s#*'"token": "'}; _token=${_rest%%\\"*}
  fi
  if [ -n "$_port" ] && [ -n "$_token" ] && { exec 9<>"/dev/tcp/127.0.0.1/$_port"; } 2>/dev/null; then
    printf 'NFREQ 1 %s\\n%s\\n%s\\n' "$_token" "$PWD" "$#" >&9
    local _a=""
    for _a in "$@"; do printf '%s\\n' "$_a" >&9; done
    local _code="" _olen="" _elen=""
    if IFS= read -r _code <&9 && IFS= read -r _olen <&9 && IFS= read -r _elen <&9; then
      case "$_code$_olen$_elen" in
        *[!0-9]*) : ;;
        *)
          local _o="" _e=""
          if [ "$_olen" -gt 0 ]; then LC_ALL=C IFS= read -r -d '' -n "$_olen" _o <&9 || true; printf '%s' "$_o"; fi
          if [ "$_elen" -gt 0 ]; then LC_ALL=C IFS= read -r -d '' -n "$_elen" _e <&9 || true; printf '%s' "$_e" >&2; fi
          exec 9<&- || true
          return "$_code"
          ;;
      esac
    fi
    exec 9<&- 2>/dev/null || true
  fi
  command "{py}" "{root}/scripts/nf.py" "$@"
}
"""


def state_path() -> Path:
    """守护状态文件落点：`<NF_HOME>/daemon.json`（NF_HOME 约定只在 storage 里定义一次）。"""
    from core import storage
    return Path(storage.default_home()) / STATE_NAME


def read_state() -> Optional[Dict[str, Any]]:
    """读守护状态；文件缺失/不可解析/版本不符 → None（一律按「没有守护」处理）。"""
    try:
        doc = json.loads(state_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):  # 无状态文件/坏件 ⇒ None（等价于「守护未运行」，调用方回退直跑）
        return None
    if not isinstance(doc, dict) or doc.get("proto") != PROTO:
        return None
    if not isinstance(doc.get("port"), int) or not doc.get("token"):
        return None
    return doc


def write_state(doc: Dict[str, Any]) -> None:
    """写状态文件（UTF-8 + LF；父目录按需创建）。空表 = 已停用标记。

    **权限**（2026-09-30 补）：状态文件里带**一次性令牌**，而令牌就是本守护的信任边界
    （module docstring：回环不是信任边界）。POSIX 上把它收紧到 `0600`（只给属主读写）——
    否则在多用户主机上，同机另一个用户读到令牌即可连回环口、以属主身份执行命令。
    Windows 上 ACL 随用户目录继承（`chmod` 无对应语义），故只在 posix 分支收紧。
    """
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, sort_keys=True) + "\n")
    _harden_perms(tmp)
    os.replace(tmp, p)          # 原子替换：读者永远看不到半截 JSON
    _harden_perms(p)


def _harden_perms(path: Path) -> None:
    """POSIX：把含令牌的状态文件收紧到仅属主可读写；Windows 交回 ACL 继承。"""
    if os.name != "posix":
        return
    try:
        os.chmod(path, 0o600)
    except OSError:  # 尽力而为：权限收紧失败不阻断守护（文件系统可能不支持）
        pass


def clear_state() -> None:
    """停用标记：写入空表（不删文件——本仓删除面要过纯度登记，保持零新增 sink）。"""
    write_state({})


def reset_process_caches() -> None:
    """清空**按路径/根键**的进程缓存（内容键缓存保留，见模块 docstring 的「新鲜度」）。

    只在守护进程里逐请求调用——让热进程与「新起进程」看到同一份仓库事实。
    """
    try:
        from core import pack_combo
        pack_combo.cache_clear()
    except Exception:                                    # noqa: BLE001 - 缓存清理不得影响命令
        pass
    try:
        from core import registry_loader
        registry_loader.load_registry.cache_clear()
    except Exception:                                    # noqa: BLE001
        pass


class _LineReader:
    """带缓冲的逐行读（明文请求是多行的，不能用「recv 一次当一行」）。"""

    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._buf = b""

    def readline(self, limit: int = MAX_REQUEST_BYTES) -> bytes:
        while b"\n" not in self._buf:
            chunk = self._sock.recv(65536)
            if not chunk:
                break
            self._buf += chunk
            if len(self._buf) > limit:
                raise ValueError("请求超过上限 %d 字节" % limit)
        line, _, self._buf = self._buf.partition(b"\n")
        return line


def _parse_request(reader: "_LineReader") -> Dict[str, Any]:
    """解析请求框——两种形态，一种语义：

    - **JSON**（程序客户端用，argv 可含任意字符，含换行）；
    - **NFREQ 明文**（shell 客户端用：`NFREQ 1 <token>` / cwd / 条数 / 逐行 argv）——
      纯 bash 无需 JSON 编解码器即可发请求。明文框的 argv **不能含换行**（路径与命令参数
      的常规取值都不含；需要精确传递请走 JSON 框）。
    """
    head = reader.readline().decode("utf-8", "replace")
    if head.startswith("NFREQ"):
        parts = head.split()
        if len(parts) != 3 or parts[1] != str(PROTO):
            raise ValueError("NFREQ 头格式错（期望 `NFREQ %d <token>`）" % PROTO)
        cwd = reader.readline().decode("utf-8", "replace")
        try:
            n = int(reader.readline().decode("ascii", "replace").strip() or "0")
        except ValueError as exc:
            raise ValueError("NFREQ argv 条数不可解析：%s" % exc) from exc
        if n < 0 or n > 4096:
            raise ValueError("NFREQ argv 条数越界：%d" % n)
        argv = [reader.readline().decode("utf-8", "replace") for _ in range(n)]
        _check_argv_size(argv)
        return {"proto": PROTO, "token": parts[2], "cwd": cwd, "argv": argv}
    req = json.loads(head or "{}")
    if not isinstance(req, dict):
        raise ValueError("请求不是 JSON 对象")
    if "argv" in req:
        _check_argv_size(req.get("argv"))
    return req


def send_framed(sock: socket.socket, exit_code: int, out: bytes, err: bytes) -> None:
    """按协议写响应：三行头 + 原始载荷。"""
    head = ("%d\n%d\n%d\n" % (int(exit_code), len(out), len(err))).encode("utf-8")
    sock.sendall(head + out + err)


def read_framed(sock: socket.socket) -> Tuple[int, bytes, bytes]:
    """按协议读响应（客户端侧）：返回 (exit, stdout 字节, stderr 字节)。"""
    fh = sock.makefile("rb")
    code = int(fh.readline().strip() or b"1")
    out_len = int(fh.readline().strip() or b"0")
    err_len = int(fh.readline().strip() or b"0")
    out = fh.read(out_len) if out_len else b""
    err = fh.read(err_len) if err_len else b""
    return code, out, err


def run_request(doc: Dict[str, Any], argv: List[str], cwd: Optional[str] = None,
                timeout: float = SOCKET_TIMEOUT) -> Tuple[int, bytes, bytes]:
    """客户端：把一条命令交给守护执行 → (exit, stdout 字节, stderr 字节)。

    任何连接层失败都**抛异常**——调用方（CLI / 启动器）据此静默回退到进程内执行。
    """
    req = json.dumps({"proto": PROTO, "token": doc["token"], "argv": [str(a) for a in argv],
                      "cwd": cwd or os.getcwd()}, ensure_ascii=False).encode("utf-8") + b"\n"
    if len(req) > MAX_REQUEST_BYTES:
        raise ValueError("请求超过上限 %d 字节" % MAX_REQUEST_BYTES)
    with socket.create_connection((BIND_HOST, int(doc["port"])), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(req)
        return read_framed(sock)


def _cli_module(root: Path):
    """加载 CLI 真源 `scripts/nf.py`（与单测同一手法：按路径 import，不走包导入）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("nfcli_daemon", Path(root) / "scripts" / "nf.py")
    if spec is None:
        raise RuntimeError("scripts/nf.py 路径无法构造加载规格（修复指引：确认 --root 指向 NF 仓库根，且 scripts/nf.py 在场）")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # type: ignore[union-attr]
    return mod


#: CLI 模块缓存（含源码指纹）：守护最怕「代码改了还在跑旧逻辑」——见 `_sync_code`。
_CLI_CACHE: Dict[str, Any] = {}
#: `start()` 拉起的子进程句柄（回收它，避免解释器退出时的 ResourceWarning）。
_CHILD: Optional[Any] = None

#: 响应缓存（**只在守护进程内、只在树没变时**复用整条命令的 stdout/stderr/退出码）。
#: 判据与账本在 `core.response_cache`（会话 `session_watch` 与守护共用同一套 ⇒ 只有一种说法）。
from core import response_cache as _rc  # noqa: E402 - 与下面的常量一组，便于阅读

_CACHE_STATS = _rc.STATS
#: 当前监听件（`serve_forever(watch=True)` 装；单测可注入假件）。
_WATCHER: Optional[Any] = None
#: 关闭「常驻语料层」的开关（诊断/对照用）：设了就整批作废且不再收录，退回每次重读。
RESIDENT_ENV_OFF = "NF_NO_RESIDENT"
#: 观测计数由 `response_cache.STATS` 提供（上面 `_CACHE_STATS` 即同一个字典对象）。

#: 响应缓存的**准入表**：仅纯读、且对同一棵树**逐字节可复现**的命令。
#: 表项是 **argv 前缀**（不是顶层命令名）：`module` / `decisions` / `patterns` 这些顶层命令
#: 里既有读子命令也有**写子命令**（`module deprecate`、`decisions reindex`、`patterns reindex`），
#: 只按顶层名放行会把写形态一起放进来——所以写子命令一律不入表。
#: 两条准入判据都在 test_watch 里真跑：（a）同树连跑两次，exit/stdout/stderr 逐字节相同；
#: （b）逐条 `git status` 前后不变（验证过：12 条候选全部既纯净又可复现）。
CACHEABLE_COMMANDS = (
    ("--version",),
    ("score",), ("conformance",), ("layers",), ("stats",), ("doctor",),
    ("interop",), ("toolface",), ("assertions",), ("cognition",),
    ("patterns", "ls"), ("patterns", "show"), ("patterns", "for"), ("patterns", "verify"),
    ("module", "ls"), ("module", "status"), ("module", "verify"),
    ("decisions", "verify"), ("decisions", "show"),
)
#: 写盘类开关：出现任一前缀即**不缓存**（哪怕命令在准入表里）。宁可不缓存，不可把旧输出当新输出。
_WRITE_FLAG_PREFIXES = ("--write", "--out", "--dest", "--build", "--save", "--fix",
                        "--apply", "--yes", "--baseline", "--freeze", "--record",
                        "--sign", "--delete", "--rm", "--all")
#: 为什么有 `--all`（2026-10-01 判据抓到的洞）：`interop --all` 是**写面**（落盘 results/interop/*），
#: 而 `interop` 在 `CACHEABLE_COMMANDS` 里、`--all` 又不在上面的旗标前缀里 ⇒ 第二次调用会被
#: **响应缓存回放**（命令根本没跑，调用方却拿到成功输出）。这正是本表存在的理由：「宁可不缓存，
#: 不可把旧输出当新输出」。`interop --check --all` 因此也一并放弃缓存（保守方向，代价可忽略）。
#: 对账判据：`test_daemon.ResponseCacheWriteSafetyTest`（闸门表 × 可缓存命令 × 本表三方对齐）。


def cacheable(argv: Sequence[str]) -> bool:
    """这条命令是否允许走响应缓存（**前缀命中准入表** + 无写盘开关）。"""
    argv = [str(a) for a in argv]
    if not argv:
        return False
    if not any(tuple(argv[:len(pre)]) == pre for pre in CACHEABLE_COMMANDS):
        return False
    return not any(a.startswith(_WRITE_FLAG_PREFIXES) for a in argv)


def _watch_generation() -> Optional[int]:
    """当前「树代际」；**None ＝ 不可用**（没有监听件 / 不健康）→ 一律不缓存、不命中。"""
    w = _WATCHER
    if w is None or not getattr(w, "healthy", False):
        return None
    return int(w.generation)


def _sync_resident(root: Path) -> None:
    """按监听给出的**确知变更**维护常驻语料层（`conformance_scan._RESIDENT`）。

    fail-closed 三条：① 没有监听 / 监听不健康 → 常驻层整批作废且不安装；② 监听说不清变了什么
    （缓冲溢出、路径解不出、只跳代际）→ 整批作废重建；③ 只有「确知哪些路径变了」才做精确失效。

    依据（2026-09-29 实测）：不加这一层，改一个文件之后守护的第一条重命令要 **1.6–2.0 s**
    （整棵语料重新枚举 + 重读，而真正变了的只有一件）；加上之后只失效被改的那几件。
    """
    from core import conformance_scan as csc
    if os.environ.get(RESIDENT_ENV_OFF):
        if csc.resident_active():        # 显式关闭：整批作废且不再收录（诊断/对照用）
            csc.clear_resident()
        return
    w = _WATCHER
    if w is None or not getattr(w, "healthy", False):
        if csc.resident_active():
            csc.clear_resident()
        return
    if not csc.resident_active():
        csc.install_resident(root)
    take = getattr(w, "take_changes", None)
    if take is None:                     # 不提供「确知变更面」的监听件 → 当说不清（整批作废）
        csc.clear_resident()
        csc.install_resident(root)
        return
    paths, unknown = take()
    if unknown:
        csc.clear_resident()
        csc.install_resident(root)
    elif paths:
        csc.drop_resident(paths)


def cache_stats() -> Dict[str, Any]:
    """响应缓存观测面（供 `nf daemon status` 与单测）。"""
    gen = _watch_generation()
    from core import conformance_scan as _csc
    return {"enabled": gen is not None, "generation": gen,
            "entries": _rc.entries(), **dict(_CACHE_STATS),
            # 常驻语料层的规模也一并报出来：它是「不重读」的账本，出问题时第一个要看的就是它。
            "resident": _csc.resident_stats()}


def reset_response_cache() -> None:
    """清空响应缓存（监听件报溢出/不可用时调用——宁可全废，不可错答）。"""
    _rc.clear()


def _code_fingerprint(root: Path) -> Tuple:
    """`core/*.py` + `scripts/*.py` 的 (相对路径, mtime_ns, size) 指纹（用 scandir，不做 walk）。

    只用一次 `scandir` 就拿到 mtime/size（Windows 上也是单次目录读），实测 ~1–3 ms；
    换来的是「改了源码，下一条命令就用新代码」——否则守护会拿旧逻辑回话，比慢更糟。
    """
    rows = []
    for rel in ("desktop/src/core", "scripts"):
        try:
            with os.scandir(Path(root) / rel) as it:
                for ent in it:
                    if not ent.name.endswith(".py"):
                        continue
                    st = ent.stat()
                    rows.append((rel + "/" + ent.name, st.st_mtime_ns, st.st_size))
        except OSError:  # 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁另行报出（见 AUD-0016）
            continue
    rows.sort()
    return tuple(rows)


def _sync_code(root: Path) -> None:
    """源码变了就整块重载（丢弃 `core.*` 与 CLI 模块）：保证守护不跑旧代码。"""
    fp = _code_fingerprint(root)
    if _CLI_CACHE.get("fp") == fp:
        return
    # 代码换版必须**同时**清掉「代码面指纹」的记忆：否则持久缓存的键还停在旧代码上，
    # 会拿旧算法算出来的账当新账（见 core.disk_cache.code_fingerprint 的说明）。
    try:
        from core import disk_cache
        disk_cache.reset_code_fingerprint(str(root))
        # 导入图/闭包指纹也要跟着清：代码一变，各派生「自己的代码闭包」可能换了成员
        # （新增 import、换依赖），不清就会拿旧闭包当键。
        from core import import_graph as _igr
        _igr.reset_code_scope(str(root))
    except Exception:                                    # noqa: BLE001 - 清不掉不影响重载
        pass
    # 常驻语料层跨代码换版**保住**：它装的是仓库事实（正文/目录/逐件摘要），与代码无关；
    # 而 `core.*` 被整块摘掉重载时，新模块会是个**空层**——不搬回来，改一行代码就得让下一条
    # 重命令把整棵语料重读一遍（实测 ~2 s）。
    saved = None
    try:
        from core import conformance_scan as _csc_old
        if _csc_old.resident_active():
            saved = _csc_old.take_resident()
    except Exception:                                    # noqa: BLE001
        saved = None
    for name in [m for m in list(sys.modules) if m == "core" or m.startswith("core.")]:
        if name != "core.daemon":           # 守护自身模块留着（改它需重启，见模块 docstring）
            sys.modules.pop(name, None)
    _CLI_CACHE.clear()
    _CLI_CACHE["fp"] = fp
    if saved is not None:
        try:
            from core import conformance_scan as _csc_new       # 重新导入 → 新模块对象
            _csc_new.adopt_resident(saved)
        except Exception:                                    # noqa: BLE001 - 搬不回去就下次重读
            pass


def _load_cli(root: Path):
    mod = _CLI_CACHE.get("mod")
    if mod is None:
        mod = _cli_module(root)
        _CLI_CACHE["mod"] = mod
    return mod


def execute(argv: List[str], root: Path, cwd: Optional[str] = None
            ) -> Tuple[int, bytes, bytes]:
    """在**本进程内**执行一条 nf 命令，并把 stdout/stderr 原样抓成字节。"""
    if argv and str(argv[0]) in REFUSED_COMMANDS:
        msg = ("守护进程内拒跑长驻/嵌套命令 `nf %s`"
               "（修复指引：在普通终端里直接跑；守护只承载一次性命令）\n" % argv[0])
        return 2, b"", msg.encode("utf-8")
    _sync_resident(root)          # 常驻层按监听变更集失效（说不清就整批作废）——必须在任何读之前
    # 响应缓存：**只在「树没变」有可证信号时**才可能命中（判据与账本在 core.response_cache）。
    gen, allowed = _watch_generation(), bool(cacheable(argv))
    hit = _rc.lookup(argv, gen, allowed, cwd)
    if hit is not None:
        return hit
    _sync_code(root)          # 源码变了就先重载（否则会用旧逻辑回话）
    reset_process_caches()
    nf = _load_cli(root)
    out_buf, err_buf = io.BytesIO(), io.BytesIO()
    out_txt = io.TextIOWrapper(out_buf, encoding="utf-8", write_through=True)
    err_txt = io.TextIOWrapper(err_buf, encoding="utf-8", write_through=True)
    old_cwd = os.getcwd()
    old_argv, old_stdin = sys.argv, sys.stdin
    code = 0
    try:
        if cwd and os.path.isdir(cwd):
            os.chdir(cwd)
        sys.argv = ["nf"] + [str(a) for a in argv]
        sys.stdin = io.StringIO("")       # 一次性命令不读交互输入（长驻命令已被拒）
        with contextlib.redirect_stdout(out_txt), contextlib.redirect_stderr(err_txt):
            try:
                code = int(nf.main(list(argv)))
            except SystemExit as exc:                      # argparse --help 等
                code = int(exc.code or 0)
    finally:
        out_txt.flush()
        err_txt.flush()
        sys.argv, sys.stdin = old_argv, old_stdin
        os.chdir(old_cwd)
        reset_process_caches()            # 请求结束再清一次：写命令改了仓库，缓存不留残影
        try:
            from core import conformance_scan as _csc
            _csc.clear_changes()          # 确知变更面**只在当次请求内有效**（否则它单调增长、
        except Exception:                 #  # 几条命令之后会让键层复用退化成全量重算——实测踩过）
            pass
    code, out, err = int(code), out_buf.getvalue(), err_buf.getvalue()
    _rc.store(argv, gen, allowed, code, out, err, cwd)
    # **非准入命令 = 无法证明只读**（可能写仓库）⇒ 立刻整批作废，不等监听线程异步察觉（写在
    # `note_uncacheable` 里：脚本里 `nf conformance --write; nf score` 连跑曾吃到写之前的旧响应）。
    _rc.note_uncacheable(allowed, code, gen)
    return code, out, err


def _handle_conn(conn: socket.socket, token: str, root: Path) -> bool:
    """处理一条连接 → 是否请求关闭守护。"""
    try:
        req = _parse_request(_LineReader(conn))
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        send_framed(conn, 2, b"", ("请求不可读：%s\n" % exc).encode("utf-8"))
        return False
    if req.get("token") != token:
        # 回环不是信任边界：无令牌（或令牌不符）一律拒绝执行
        send_framed(conn, 2, b"", "令牌缺失或不符：拒绝执行"
                                  "（修复指引：用 scripts/nf 启动器，或 nf daemon status）\n"
                                  .encode("utf-8"))
        return False
    if req.get("op") == "shutdown":
        send_framed(conn, 0, b"", b"")
        return True
    if req.get("op") == "stats":
        # 观测面必须**在守护进程内**取：缓存与监听件都是守护的进程状态，客户端看不到。
        payload = json.dumps(cache_stats(), ensure_ascii=False).encode("utf-8")
        send_framed(conn, 0, payload, b"")
        return False
    argv = req.get("argv")
    if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
        send_framed(conn, 2, b"", "argv 必须是字符串列表\n".encode("utf-8"))
        return False
    from core import disk_cache as _dc
    _dc.defer_begin()                # 请求期间：派生结果的写盘只入队
    try:
        code, out, err = execute(argv, root, cwd=req.get("cwd"))
    except BaseException:
        _dc.defer_drop()             # 异常路径：丢队列（缓存不是事实，丢了只是下次重算）
        raise
    send_framed(conn, code, out, err)
    # **回包之后再落盘**：写盘是纯写、只供别的进程（冷进程 / 守护重启）用，不该占客户端关键路径
    # （实测：一次新内容状态的落盘在守护口径下值 20–80 ms）。落盘失败也只是丢缓存。
    try:
        _dc.defer_flush()
    except Exception:                                    # noqa: BLE001 - 落盘尽力而为
        pass
    return False


def serve_forever(root: Path, idle_timeout: float = 0.0, ready: Optional[Any] = None,
                  force: bool = False, watch: bool = False) -> int:
    """守护主循环（单线程串行）：直到收到 shutdown / 空闲超时 / 被中断。

    **一个 NF_HOME 只允许一个守护**（缺省 fail-closed）：状态文件只登记一个端口/令牌，若第二个
    守护直接起，它会覆盖状态、让先起的那个「失联」（CI 实测踩过：同一 NF_HOME 下先后起两个
    服务，后者的 `clear_state()` 把前者的广告位抹掉）。确需另起用 `force=True`。

    `watch=True` 时装上目录监听 → 开「只读命令的响应缓存」（树没变就整条复用）。监听不可用
    或中途失效时**自动降级**：缓存不命中、不复用，行为与今天一致。
    """
    if not force and ping(timeout=1.0):
        print("已有守护在运行（修复指引：先 `nf daemon stop`，或显式 force 另起）", file=sys.stderr)
        return 2
    global _WATCHER
    watcher = None
    if watch:
        from core import watch as _watch
        watcher = _watch.DirWatcher(root)
        if watcher.start():
            _WATCHER = watcher
        else:
            _WATCHER = None
            watcher = None
            print("目录监听不可用（平台未实现或打开失败）→ 不启用响应缓存，"
                  "行为与常规守护一致", file=sys.stderr)
    token = secrets.token_hex(32)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((BIND_HOST, 0))              # 端口 0 = 内核分配（不抢占固定端口）
    srv.listen(8)
    port = int(srv.getsockname()[1])
    write_state({"proto": PROTO, "pid": os.getpid(), "port": port, "token": token,
                 "root": str(root), "started": int(time.time())})
    if ready is not None:
        ready(port)
    srv.settimeout(1.0)
    last = time.time()
    try:
        while True:
            if idle_timeout and (time.time() - last) > idle_timeout:
                break
            try:
                conn, _addr = srv.accept()
            except socket.timeout:  # 空闲 accept 超时属正常循环（继续等下一条连接）
                continue
            except KeyboardInterrupt:
                break
            last = time.time()
            with conn:
                conn.settimeout(SOCKET_TIMEOUT)
                shutdown = _handle_conn(conn, token, root)
            if shutdown:
                break
    finally:
        # 先清状态再关端口：客户端「连不上」与「看不到登记」才是同一时刻的真相，
        # 否则中间会有一个「端口已死但状态还在」的窗口（CI 实测：就是这样让 stop() 报
        # 「守护未响应」而不是「没有守护」）。
        if watcher is not None:
            watcher.stop()
        _WATCHER = None
        from core import conformance_scan as _csc
        _csc.clear_resident()      # 常驻语料层随守护一起消失（进程内起服务的测试不留残影）
        reset_response_cache()
        clear_state()
        srv.close()
    return 0


def query_stats(doc: Optional[Dict[str, Any]] = None,
                timeout: float = 2.0) -> Optional[Dict[str, Any]]:
    """问守护要它的响应缓存/监听状态（**必须在守护进程内取**，见 `_handle_conn` 的 stats op）。"""
    doc = doc or read_state()
    if not doc:
        return None
    try:
        req = json.dumps({"proto": PROTO, "token": doc["token"], "op": "stats"}).encode("utf-8")
        with socket.create_connection((BIND_HOST, int(doc["port"])), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(req + b"\n")
            code, out, _err = read_framed(sock)
        if code != 0:
            return None
        got = json.loads(out.decode("utf-8"))
        return got if isinstance(got, dict) else None
    except Exception:                                    # noqa: BLE001 - 查不到就如实说查不到
        return None


def ping(doc: Optional[Dict[str, Any]] = None, timeout: float = 2.0) -> bool:
    """守护是否在线（带令牌发一次 `--version`）。"""
    doc = doc or read_state()
    if not doc:
        return False
    try:
        code, _out, _err = run_request(doc, ["--version"], timeout=timeout)
        return code == 0
    except Exception:                                    # noqa: BLE001 - 探测失败即「不在线」
        return False


def start(root: Path, idle_timeout: float = 3600.0, wait: float = 15.0,
          watch: bool = False) -> Tuple[bool, str]:
    """拉起守护（后台子进程）→ (是否成功, 说明)。已在跑则直接返回 True。"""
    if ping():
        return True, "守护已在运行"
    global _CHILD
    import subprocess
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(root) / "desktop" / "src") + os.pathsep \
        + env.get("PYTHONPATH", "")
    args = [sys.executable, "-m", "core.daemon", "--serve",
            "--root", str(root), "--idle", str(int(idle_timeout))]
    if watch:
        args.append("--watch")
    kwargs: Dict[str, Any] = {"cwd": str(root), "env": env,
                              "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":                                  # Windows：脱离控制台、不闪窗
        kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0) \
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
    _CHILD = subprocess.Popen(args, **kwargs)             # noqa: S603 - argv 列表，无 shell
    deadline = time.time() + wait
    while time.time() < deadline:
        if ping():
            return True, "守护已启动"
        time.sleep(0.05)
    return False, "守护启动超时（修复指引：手动跑 python -m core.daemon --serve 看报错）"


def _reap_child() -> None:
    """回收 `start()` 拉起的子进程（否则解释器退出时报 ResourceWarning）。"""
    global _CHILD
    if _CHILD is None:
        return
    try:
        _CHILD.wait(timeout=5)
    except Exception:                                    # noqa: BLE001 - 回收失败不影响结果
        pass
    _CHILD = None


def stop(timeout: float = 8.0) -> Tuple[bool, str]:
    """请守护自行退出（协议级 shutdown，不发信号、不删文件）。"""
    doc = read_state()
    if not doc:
        return False, "没有守护在运行"
    try:
        with socket.create_connection((BIND_HOST, int(doc["port"])), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(json.dumps({"proto": PROTO, "token": doc["token"],
                                     "op": "shutdown"}).encode("utf-8") + b"\n")
            read_framed(sock)
    except (ConnectionRefusedError, ConnectionResetError):
        # 登记在、端口却拒连 = 守护早已不在（登记过期）。这不是「停不下来」，而是「没有守护」：
        # 如实报这一条并清除过期登记，才能让下一次 stop 得到确定的答案。
        clear_state()
        return False, "没有守护在运行（状态登记已过期：%s:%s 拒连，已清除）" \
            % (BIND_HOST, doc["port"])
    except Exception as exc:                             # noqa: BLE001
        clear_state()
        return False, "守护未响应（已标记停用）：%s" % exc
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not ping(doc, timeout=0.5):
            _reap_child()
            return True, "守护已停止"
        time.sleep(0.05)
    return False, "守护仍在运行"


def main(argv: Optional[List[str]] = None) -> int:
    """`python -m core.daemon --serve --root <repo> [--idle S]`（内部入口）。"""
    import argparse
    ap = argparse.ArgumentParser(prog="core.daemon",
                                 description="NF 执行层常驻守护（内部入口）")
    ap.add_argument("--serve", action="store_true", help="前台跑守护循环（供 start 拉起）")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    ap.add_argument("--idle", type=float, default=3600.0,
                    help="空闲多少秒后自动退出（0=不退出）")
    ap.add_argument("--force", action="store_true",
                    help="已有守护在运行时仍另起一个（会顶掉先起者的状态登记，默认拒绝）")
    ap.add_argument("--watch", action="store_true",
                    help="启用目录监听 + 只读命令响应缓存（树没变即整条复用；不可用自动降级）")
    args = ap.parse_args(argv)
    if not args.serve:
        ap.print_help()
        return 2
    return serve_forever(Path(args.root).resolve(), idle_timeout=args.idle,
                         force=args.force, watch=args.watch)


if __name__ == "__main__":                                # pragma: no cover - 进程入口
    raise SystemExit(main())
