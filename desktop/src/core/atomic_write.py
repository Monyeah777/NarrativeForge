"""原子写（同目录临时文件 + `os.replace`）：读者永远看不到半截内容。

为什么要有唯一出处：仓库**已有**这个惯用法并写明理由——`disk_cache` 的落盘与 `daemon`
的状态文件都是「先写临时件再 `os.replace`（原子替换：读者看不到半截 JSON）」。但**已发布
产物的写入口**（如 `repo_stats.write` 写 README / README.en / llms.txt / repo_stats.json）
仍是裸 `open(path, "w")`：agent 密集重复调用下，多个进程/线程写同一件时，读者可能读到
半截内容（大文件会被分多次 write 落盘）。本模块把该惯用法收敛成**唯一出处**。

纪律：临时件与目标**同目录**（跨盘 rename 不原子）；写完 `fsync` 再 `os.replace`；
失败路径只清理**本模块刚造的**临时件；一律 LF（与 `text_hygiene` 的行尾纪律一致）。

**平台边界（实测，如实记）**：Windows 上 `os.replace` 与并发读者会互相短时占用——
写侧可能收到 `WinError 5`（本模块按**短重试**处置），读侧也可能瞬时 `PermissionError`。
也就是说「原子」保证的是**不会读到半截内容**，不保证「永不报瞬时占用错」；读侧遇到
瞬时 `PermissionError` 应重试（这是宿主语义，不是本模块能消除的）。
"""
from __future__ import annotations

import contextlib
import hashlib
import os
import tempfile
import time
from pathlib import Path


#: 瞬时写错重试参数（Windows 实测：杀软/句柄扫描会让临时件写入偶发 EINVAL(22)、
#: 也让 `os.replace` 偶发 WinError 5——两者都是「等一个瞬间就好」，不是数据问题）
_WRITE_ATTEMPTS = 5
_WRITE_BACKOFF = 0.05
#: 可重试的 errno：EACCES(13) / EBUSY(16) / EINVAL(22)
_TRANSIENT_ERRNOS = (13, 16, 22)


def _is_transient(exc: OSError) -> bool:
    return isinstance(exc, PermissionError) or getattr(exc, "errno", None) in _TRANSIENT_ERRNOS


def _retry_transient(op):
    """跑 `op()`；**只**对瞬时占用类 `OSError` 短重试，其余原样抛（不做无谓掩盖）。"""
    for i in range(_WRITE_ATTEMPTS):
        try:
            return op()
        except OSError as exc:
            if not _is_transient(exc) or i == _WRITE_ATTEMPTS - 1:
                raise
            time.sleep(_WRITE_BACKOFF * (i + 1))


def _replace(tmp: str, p: Path, attempts: int = 10, backoff: float = 0.05) -> None:
    """`os.replace` + **短重试**：Windows 上目标被读者短暂占用时 replace 会报 WinError 5
    （`PermissionError`）——这不是数据问题，等一个瞬间即可；重试耗尽仍失败则如实抛出
    （绝不退化成裸写：那会丢掉原子性）。"""
    for i in range(attempts):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(backoff)


def write_text(path: str | os.PathLike, text: str) -> None:
    """把 `text` 原子地写到 `path`（LF 落盘；失败不留半截目标文件）。"""
    def _once() -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = text.replace("\r\n", "\n").replace("\r", "\n")
        fd, tmp = tempfile.mkstemp(prefix="." + p.name + ".", suffix=".tmp",
                                   dir=str(p.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            _replace(tmp, p)        # 原子替换：读者只会看到旧全量或新全量
        except BaseException:
            try:
                os.unlink(tmp)      # 只删本模块现造的临时件（见 purity_scan.SINK_ALLOW）
            except OSError:
                pass
            raise

    _retry_transient(_once)         # 瞬时占用错（EINVAL 22 / WinError 5）短重试


def write_bytes(path: str | os.PathLike, data: bytes) -> None:
    """把 `data` 原子地写到 `path`（**二进制**；同目录临时件 + `fsync` + `os.replace`）。

    与 `write_text` 同一纪律，供二进制产物使用（如 `library/anchors/*.sig` 的签名锚
    拷贝——半截的签名件会让校验方判「签名无效」而不是「没写完」）。
    """
    def _once() -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix="." + p.name + ".", suffix=".tmp",
                                   dir=str(p.parent))
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            _replace(tmp, p)        # 原子替换：读者只会看到旧全量或新全量
        except BaseException:
            try:
                os.unlink(tmp)      # 只删本模块现造的临时件
            except OSError:
                pass
            raise

    _retry_transient(_once)         # 瞬时占用错（EINVAL 22 / WinError 5）短重试


# 读侧短重试参数（与写侧 `_replace` 同一取舍）
_READ_ATTEMPTS = 10
_READ_BACKOFF = 0.02


def _read_with_retry(path: str | os.PathLike, binary: bool, encoding: str):
    """按 `_READ_ATTEMPTS` 次短重试读；**只**重试瞬时占用错，其它 OSError 原样抛。

    为什么读侧也要重试（实测 2026-09-30）：原子写的写侧用 `os.replace`，Windows 上并发
    读者会瞬时拿到 `PermissionError`（WinError 5/32：名字正被别人持有）。本机真跑
    「4000 次写 × 3 个读者线程」共 119 万次读：**1055 次读瞬时失败（≈0.09%）**，
    但 **0 次半截、0 次解析错**——「不读到半截」由写侧保证，「读不到」这条得读侧兜。
    不重试的话，agent 密集重复调用（并发 `nf`/verify）会随机冒 `[Errno 13]`。
    """
    last: Exception | None = None
    for i in range(_READ_ATTEMPTS):
        try:
            with open(path, "rb" if binary else "r",
                      **({} if binary else {"encoding": encoding})) as fh:
                return fh.read()
        except PermissionError as exc:      # WinError 5/32：名字被写侧短暂占用
            last = exc
            if i == _READ_ATTEMPTS - 1:
                raise
            time.sleep(_READ_BACKOFF * (i + 1))
    raise last  # type: ignore[misc]        # 不可达（循环内已 return / raise）


def read_text(path: str | os.PathLike, encoding: str = "utf-8") -> str:
    """读文本（**带瞬时占用重试**）：与 `write_text` 对称——写侧原子、读侧不因并发而炸。"""
    return _read_with_retry(path, False, encoding)


def read_bytes(path: str | os.PathLike) -> bytes:
    """读字节（**带瞬时占用重试**）：与 `write_bytes` 对称。"""
    return _read_with_retry(path, True, "utf-8")


#: 排他锁：等待上限（秒）与轮询间隔
LOCK_TIMEOUT = 10.0
_LOCK_POLL = 0.02


def _lock_fd(fd: int) -> None:
    if os.name == "nt":
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_fd(fd: int) -> None:
    if os.name == "nt":
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)


@contextlib.contextmanager
def lock_file(path: str | os.PathLike, timeout: float = LOCK_TIMEOUT, what: str = ""):
    """对 `path` 取**进程级排他锁**（供「读-改-写**共享真源**」的入口串行化）。

    为什么需要（2026-10-01 实测，不是推断）：`write_text` 保证「读者不见半截」，但**不保证
    不丢更新**——两个进程各自「读 → 追加自己的条目 → 原子写」同一份 JSON，本机真跑**丢了一条**
    （最终只剩后写者那条）。而 `registry.json` 的两个 `--apply` 写入口正是这个形状：并发跑
    一次 `nf register --apply`，另一个包会**静默消失**。

    取锁点：`<临时目录>/nf-locks/<sha256(目标绝对路径)>.lock` —— 刻意**不落在仓库里**
    （否则每次写都会在工作树里留一个未跟踪件）。锁由**内核**持有，进程退出/崩溃自动释放，
    故不存在「陈旧锁文件」问题；等待超时则如实报错并给指引，不无限等。
    """
    target = Path(path)
    try:
        key = hashlib.sha256(str(target.resolve()).encode("utf-8")).hexdigest()[:24]
    except OSError:                       # 极端路径（不可解析）⇒ 退回按原样串算键
        key = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:24]
    lock_dir = Path(tempfile.gettempdir()) / "nf-locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / (key + ".lock")
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if os.fstat(fd).st_size == 0:
            os.write(fd, b"\0")           # 保证至少有 1 字节可锁（Windows `msvcrt` 语义）
        deadline = time.monotonic() + max(0.0, float(timeout))
        while True:
            try:
                _lock_fd(fd)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "等待排他锁超时（%.1fs）：%s（修复指引：确认没有另一个 nf 进程正卡在写"
                        "同一真源；锁件 %s）——超时只在**真并发写**时才会出现，等对方结束后重跑即可"
                        % (timeout, what or target.name, lock_path))
                time.sleep(_LOCK_POLL)
        yield
    finally:
        try:
            _unlock_fd(fd)
        except OSError:   # 释放失败无补救动作（也不该把主流程的异常替换掉）：锁由内核持有，
            pass          # 本进程退出即自动释放；真出问题也会在**下一次取锁**处暴露，不静默吞错
        os.close(fd)
