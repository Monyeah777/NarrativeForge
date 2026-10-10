"""引擎动态加载器（Dynamic Link Library / .so / .dylib 的装载面）。

内部差距（2026-10-10，G5 的「装载」半）：engine_registry 能回答「有哪些引擎实现、工具链在不在」，
但**没有装载面**——真「动态链接库」缺的正是这一段：把实现编成共享库后按 ABI 载入进程。

本模块把**装载机制**落成可验证的一段：
- c_library()：定位平台 C 运行库（Windows=msvcrt / 其余=libc）；确定性、无网络；
- load(path)：载入任意共享库；缺件 / 架构不符 / 依赖缺失一律 fail-closed 返回 None，不抛；
- abi_probe()：真实装载一次平台 C 运行库并调用 abs(-5)==5——用一次 dlopen + 调用证明机制可用；
- provider_libs(root, engine_dir)：引擎目录下的候选共享库（仓库相对路径）。

边界（诚实）：本模块**不编译**任何引擎（本机无 cargo / dotnet）；Rust / .NET 侧要产出 cdylib，
须在该线补 [lib] crate-type 与 C ABI，属另一波（须作者裁）。本模块只保证：库在就载、不在就 fail-closed。

依赖姿态：零 core 依赖（只 stdlib ctypes）——SDP 叶子；由 scripts/engine_status.py 消费。
"""
from __future__ import annotations

import ctypes
import ctypes.util
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional

_LIB_SUFFIXES = (".dll", ".so", ".dylib")


def c_library() -> str:
    """平台 C 运行库名（可能是裸名，由系统解析；确定性）。"""
    found = ctypes.util.find_library("c")
    if found:
        return found
    return "msvcrt" if platform.system() == "Windows" else "libc.so.6"


def load(path: str) -> Optional[ctypes.CDLL]:
    """载入共享库；失败返回 None（fail-closed），不抛异常。"""
    try:
        return ctypes.CDLL(str(path))
    except OSError:
        return None


def abi_probe() -> Dict[str, Any]:
    """真实装载一次平台 C 运行库并调用 abs(-5)，证明 dlopen + 调用机制可用。"""
    name = c_library()
    lib = load(name)
    if lib is None:
        return {"library": name, "ok": False, "detail": "装载失败（fail-closed）"}
    try:
        got = int(lib.abs(-5))
    except (AttributeError, TypeError, ValueError) as exc:
        return {"library": name, "ok": False, "detail": "符号调用失败：%s" % exc}
    return {"library": name, "ok": got == 5, "detail": "abs(-5)=%d" % got}


#: 引擎共享库须导出的 C ABI 符号（Rust / .NET 侧产出 cdylib 时按此名导出）。
ABI_SYMBOL = "nf_engine_abi_version"


def engine_abi(path: str) -> Optional[int]:
    """载入引擎共享库并调用其 C ABI 版本号；未产出 / 符号缺失一律 fail-closed 返回 None。"""
    lib = load(path)
    if lib is None:
        return None
    try:
        return int(getattr(lib, ABI_SYMBOL)())
    except (AttributeError, TypeError, ValueError):  # 符号缺失/签名不符：按「未产出」处理，不假装
        return None


def provider_libs(root: str = ".", engine_dir: str = "") -> List[str]:
    """某引擎目录下的候选共享库（仓库相对路径，按路径排序；缺目录返回空表）。"""
    if not engine_dir:
        return []
    base = Path(root) / "engine" / str(engine_dir)
    if not base.is_dir():
        return []
    out: List[str] = []
    for pat in ("target/release/*", "target/debug/*", "lib/*", "dist/*", "bin/*"):
        for p in sorted(base.glob(pat)):
            if p.is_file() and p.suffix.lower() in _LIB_SUFFIXES:
                out.append(p.relative_to(Path(root)).as_posix())
    return sorted(out)
