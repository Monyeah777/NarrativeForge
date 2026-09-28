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
from typing import Any, Dict, List, Optional, Tuple

PROTO = 1
#: 监听地址：**只允许回环**（与 scripts/serve_decision_model.py 同一条纪律；本模块不提供
#: 「显式放行外网」的开关——守护进程能执行任意 nf 命令，绝不能出回环）。
BIND_HOST = "127.0.0.1"
#: 请求体上限（1 MiB）：一条命令的 argv 远小于此；设上限防「自称超长」的无界读。
MAX_REQUEST_BYTES = 1 << 20
#: 守护内**拒跑**的命令：长驻（serve / shell）与自指（daemon）。
REFUSED_COMMANDS = ("serve", "shell", "daemon")
#: 连接读写超时（秒）：客户端卡住不得拖死守护。
SOCKET_TIMEOUT = 30.0
STATE_NAME = "daemon.json"

#: bash 快路模板（`nf daemon shell-init bash` 原样输出，供 `eval "$(…)"` 装进交互 shell）。
#: 关键点：**全部用 bash 内建**（/dev/tcp + printf + read -N），因此 `nf …` 是当前 shell 里的
#: 一次函数调用 + 一次套接字往返——没有子进程、没有解释器启动，这才是真正的毫秒级客户端。
#: 长驻/自指命令（daemon/shell/serve）与「无参」一律直落 python 入口（与守护拒绝面一致）。
SHELL_INIT_BASH = """# NF 执行层快路（生成自 `nf daemon shell-init bash`）
# 用法：  eval "$(nf daemon shell-init bash)"        # 或写进 ~/.bashrc
# 卸载：  unset -f nf
nf() {
  case "${1:-}" in
    daemon|shell|serve|"") command {py} "{root}/scripts/nf.py" "$@"; return $? ;;
  esac
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
          if [ "$_olen" -gt 0 ]; then LC_ALL=C IFS= read -r -N "$_olen" _o <&9 || true; printf '%s' "$_o"; fi
          if [ "$_elen" -gt 0 ]; then LC_ALL=C IFS= read -r -N "$_elen" _e <&9 || true; printf '%s' "$_e" >&2; fi
          exec 9<&- || true
          return "$_code"
          ;;
      esac
    fi
    exec 9<&- 2>/dev/null || true
  fi
  command {py} "{root}/scripts/nf.py" "$@"
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
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or doc.get("proto") != PROTO:
        return None
    if not isinstance(doc.get("port"), int) or not doc.get("token"):
        return None
    return doc


def write_state(doc: Dict[str, Any]) -> None:
    """写状态文件（UTF-8 + LF；父目录按需创建）。空表 = 已停用标记。"""
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(tmp, p)          # 原子替换：读者永远看不到半截 JSON


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


def _recv_line(sock: socket.socket, limit: int = MAX_REQUEST_BYTES) -> bytes:
    """读一行（含上限）：超限即抛 ValueError（调用方转成错误响应）。"""
    buf = bytearray()
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        buf += chunk
        if len(buf) > limit:
            raise ValueError("请求超过上限 %d 字节" % limit)
        if b"\n" in chunk:
            break
    return bytes(buf).split(b"\n", 1)[0]


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
        return {"proto": PROTO, "token": parts[2], "cwd": cwd, "argv": argv}
    req = json.loads(head or "{}")
    if not isinstance(req, dict):
        raise ValueError("请求不是 JSON 对象")
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
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # type: ignore[union-attr]
    return mod


#: CLI 模块缓存（含源码指纹）：守护最怕「代码改了还在跑旧逻辑」——见 `_sync_code`。
_CLI_CACHE: Dict[str, Any] = {}
#: `start()` 拉起的子进程句柄（回收它，避免解释器退出时的 ResourceWarning）。
_CHILD: Optional[Any] = None


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
        except OSError:
            continue
    rows.sort()
    return tuple(rows)


def _sync_code(root: Path) -> None:
    """源码变了就整块重载（丢弃 `core.*` 与 CLI 模块）：保证守护不跑旧代码。"""
    fp = _code_fingerprint(root)
    if _CLI_CACHE.get("fp") == fp:
        return
    for name in [m for m in list(sys.modules) if m == "core" or m.startswith("core.")]:
        if name != "core.daemon":           # 守护自身模块留着（改它需重启，见模块 docstring）
            sys.modules.pop(name, None)
    _CLI_CACHE.clear()
    _CLI_CACHE["fp"] = fp


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
    return code, out_buf.getvalue(), err_buf.getvalue()


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
    argv = req.get("argv")
    if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
        send_framed(conn, 2, b"", "argv 必须是字符串列表\n".encode("utf-8"))
        return False
    code, out, err = execute(argv, root, cwd=req.get("cwd"))
    send_framed(conn, code, out, err)
    return False


def serve_forever(root: Path, idle_timeout: float = 0.0, ready: Optional[Any] = None) -> int:
    """守护主循环（单线程串行）：直到收到 shutdown / 空闲超时 / 被中断。"""
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
            except socket.timeout:
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
        srv.close()
        clear_state()
    return 0


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


def start(root: Path, idle_timeout: float = 3600.0, wait: float = 15.0
          ) -> Tuple[bool, str]:
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
    args = ap.parse_args(argv)
    if not args.serve:
        ap.print_help()
        return 2
    return serve_forever(Path(args.root).resolve(), idle_timeout=args.idle)


if __name__ == "__main__":                                # pragma: no cover - 进程入口
    raise SystemExit(main())
