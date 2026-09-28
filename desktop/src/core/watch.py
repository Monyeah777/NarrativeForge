"""目录变更监听（仅标准库）：给守护进程一个**「树没变」的可证信号**。

用途：守护把「只读命令的响应」按「树没变」复用——没有变更通知就不重算，重命令从秒级落到
毫秒级（见 `daemon.execute` 的响应缓存）。这是「毫秒级执行层」的最后一段：前面几波把
**重算**做便宜了，这一波把**不重算**变成可能。

纪律（fail-closed，宁可多算不可错答）：
- **通知制**：只有「收到变更通知」才认为树变了；**缓冲溢出、句柄失效、线程异常一律转「脏」**
  ——绝不把「没收到」当成「没变」。溢出时直接让代际跳变并清空响应缓存（下一问必然重算）。
- 本波**不解析变更路径**：任何一次通知都算「树变了」。粗粒度换来的是不可能漏判——细粒度
  失效（按输入面只废相关缓存）留后续波，且有判据后再上。
- 平台不支持 → `available()` 假、`DirWatcher.start()` 假：守护**不启用缓存**，
  行为与今天完全一致（正确性不受影响，只是没有加速）。

已实现平台：**Windows（ReadDirectoryChangesW，递归子树）**。Linux/macOS 走 inotify/FSEvents 的
实现本波未落地——`available()` 在那些平台为假，守护自动降级；不写没跑过的平台代码。
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Optional

#: 一次通知批次的缓冲（64 KiB）：溢出时 Windows 用「零长度回报」告知，我们据此转脏。
_BUFFER_BYTES = 64 * 1024
#: **被忽略的目录**（仓库相对、小写、`/` 分隔）：`.git` 下的变更不影响任何判据——
#: 证据（2026-09 实测 + 判据）：追踪一次 `regression_score.evaluate` 的全部打开与尝试打开，
#: 仓内 **2560 件、`.git` 下 0 件**；代码面里 `.git` 只出现在「排除它」的遍历过滤与写 hooks 的
#: 安装脚本里（`asset_ledger` / `text_hygiene` 的 EXCLUDE 集合）。被缓存的只读命令也都不跑 git。
#: 忽略它的收益是**日常 git 工作流**（status/add/commit 都会写 `.git/`）不再把响应缓存整批作废——
#: 否则每跑一次 git 命令，下一个 `nf score` 就要退回 ~2.2 s 重算。
#: **安全边界**：只忽略「这一批通知里全部路径都在忽略面内」的情形；混批、解析不出路径、缓冲溢出
#: 一律照旧转脏（宁可多算，不可错答）。
#: **实测细节**：`ReadDirectoryChangesW` 在**创建/删除**文件时会额外为**目录本身**发一条通知
#: （路径无尾斜杠，如 `.git`）——只判前缀 `.git/` 会被这条否决（本波实测踩过：真仓库根上
#: `.git` 探针照样推进代际，而临时目录里"写已存在文件"不推进，差别就在这条目录通知）。
_IGNORED_DIRS = (".git",)


def available() -> bool:
    """本平台是否**真的**有实现（不是「理论上支持」）。"""
    return os.name == "nt"


class DirWatcher:
    """递归监听 `root` 下的任何变更；对外只暴露「代际」与「健康」。

    - `generation`：每收到一批变更通知 +1；配合响应缓存的键使用。
    - `healthy`：监听是否仍然可信。**只有它为真，调用方才允许用代际做「没变」的判据**。
    - `overflowed`：是否发生过缓冲溢出（溢出后本对象自动把代际跳变并标记，供调用方清缓存）。
    """

    def __init__(self, root) -> None:
        self.root = str(Path(root).resolve())
        self._lock = threading.Lock()
        self._generation = 0
        self._healthy = False
        self._overflowed = False
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._handle = None
        self._ignored_batches = 0

    # ---------------------------------------------------------------- 对外读

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation

    @property
    def healthy(self) -> bool:
        with self._lock:
            return self._healthy

    @property
    def overflowed(self) -> bool:
        with self._lock:
            return self._overflowed

    @property
    def ignored_batches(self) -> int:
        """只含忽略面变更、因而**没有**推进代际的通知批次数（观测用）。"""
        with self._lock:
            return self._ignored_batches

    # ---------------------------------------------------------------- 生命周期

    def start(self) -> bool:
        """开始监听 → 是否成功。失败即保持 `healthy=False`（调用方不得据此判「没变」）。"""
        if not available():
            return False
        if self._thread is not None:
            return self.healthy
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="nf-watch", daemon=True)
        self._thread.start()
        # 等第一轮就绪（打开句柄成功才算健康）；超时则视为不可用。
        for _ in range(200):
            if self.healthy or self._thread is None or not self._thread.is_alive():
                break
            self._stop.wait(0.01)
        return self.healthy

    def stop(self) -> None:
        """停止监听（幂等）。"""
        self._stop.set()
        self._cancel()
        th = self._thread
        if th is not None:
            th.join(timeout=3.0)
        self._thread = None
        with self._lock:
            self._healthy = False

    # ---------------------------------------------------------------- 内部

    def _bump(self, overflow: bool = False) -> None:
        with self._lock:
            self._generation += 1
            if overflow:
                self._overflowed = True

    def _run(self) -> None:                                # pragma: no cover - 平台实现
        try:
            self._run_windows()
        except Exception:                                  # noqa: BLE001 - 任何异常都转脏
            with self._lock:
                self._healthy = False

    def _run_windows(self) -> None:                        # pragma: no cover - 平台实现
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel32.CreateFileW
        create_file.restype = wintypes.HANDLE
        create_file.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                wintypes.HANDLE]
        read_changes = kernel32.ReadDirectoryChangesW
        read_changes.restype = wintypes.BOOL
        read_changes.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                 wintypes.BOOL, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
                                 ctypes.c_void_p, ctypes.c_void_p]
        cancel_io = kernel32.CancelIoEx
        cancel_io.restype = wintypes.BOOL
        cancel_io.argtypes = [wintypes.HANDLE, ctypes.c_void_p]

        handle = create_file(self.root, 0x0001, 1 | 2 | 4, None, 3, 0x02000000, None)
        if not handle or handle == wintypes.HANDLE(-1).value:
            with self._lock:
                self._healthy = False
            return
        self._handle = handle
        buf = ctypes.create_string_buffer(_BUFFER_BYTES)
        returned = wintypes.DWORD(0)
        with self._lock:
            self._healthy = True
        while not self._stop.is_set():
            ok = read_changes(handle, buf, _BUFFER_BYTES, True,
                              0x01 | 0x02 | 0x04 | 0x08 | 0x10 | 0x40,
                              ctypes.byref(returned), None, None)
            if self._stop.is_set():
                break
            if not ok:                                     # 句柄失效/被取消 → 不再可信
                with self._lock:
                    self._healthy = False
                break
            if returned.value == 0:                        # 零长度 = 缓冲溢出（通知被丢弃）
                self._bump(overflow=True)
            elif self._only_ignored(ctypes.string_at(buf, returned.value)):
                with self._lock:
                    self._ignored_batches += 1
            else:
                self._bump()
        kernel32.CloseHandle(handle)
        self._handle = None

    @staticmethod
    def _notify_paths(raw: bytes):
        """解析 `FILE_NOTIFY_INFORMATION` 链 → 仓库相对路径（`/` 分隔、小写）。解析不出即空。"""
        out = []
        off = 0
        total = len(raw)
        while off + 12 <= total:
            nxt = int.from_bytes(raw[off:off + 4], "little")
            length = int.from_bytes(raw[off + 8:off + 12], "little")
            name = raw[off + 12:off + 12 + length]
            if length and len(name) == length:
                try:
                    out.append(name.decode("utf-16-le").replace("\\", "/").lower())
                except UnicodeDecodeError:
                    return []                             # 解不出就当「不知道」→ 转脏
            if nxt == 0 or off + nxt >= total:
                break
            off += nxt
        return out

    def _only_ignored(self, raw: bytes) -> bool:
        """这一批是否**全部**落在忽略面内（解析不出任何路径 → 假，即照旧转脏）。"""
        paths = self._notify_paths(raw)
        if not paths:
            return False
        return all(any(p == d or p.startswith(d + "/") for d in _IGNORED_DIRS)
                   for p in paths)

    def _cancel(self) -> None:
        """取消阻塞中的 ReadDirectoryChangesW（否则线程要等下一次变更才醒）。"""
        if not available() or self._handle is None:
            return
        try:
            import ctypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CancelIoEx(self._handle, None)
        except Exception:                                  # noqa: BLE001 - 取消失败不影响停止
            pass
