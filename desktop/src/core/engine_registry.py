"""引擎 provider 注册表（Registry Pattern）——「有哪些引擎实现 / 各实现什么 / 本机能否装载」的唯一出处。

内部差距（2026-10-09 实测，G5）：engine/rust（Rust 快线）与 engine/dotnet（.NET 引擎线）是只读第二
实现（ADR-0005），但仓内没有运行期解析面回答「按接口/能力，现在能装载哪个实现、入口是什么、要装
什么工具链」。本模块把 integrations/<id>/integration.json 里入口落在 engine/ 的接入面解析成引擎
provider 记录 + 能力矩阵；工具链缺失只记 tool_present=false（本机无 cargo/dotnet 是环境事实，不是
缺陷），不判死。

边界（诚实）：本模块只做解析与登记，不做进程装载（真跑仍由各自入口与 CI 负责）；真正的 in-process
动态库装载（Rust cdylib + C ABI + ctypes）未实现——原因与选项记在内部档案 63 §七。

依赖姿态：零 core 依赖（只 stdlib）——按 SDP 沉在叶子侧，任何模块都能安全依赖它而不抬高自身的 I。
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

INTEGRATIONS_DIR = "integrations"
ENGINE_PREFIX = "engine/"


def _face_docs(root: str = ".") -> List[Dict[str, Any]]:
    """在场接入面描述件（可解析者；坏件/缺件跳过，不裸崩）。"""
    d = Path(root) / INTEGRATIONS_DIR
    out: List[Dict[str, Any]] = []
    if not d.is_dir():
        return out
    for sub in sorted(p for p in d.iterdir() if p.is_dir()):
        f = sub / "integration.json"
        if not f.is_file():
            continue
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):  # 坏件跳过：消费方按缺件如实呈现，不打断枚举
            continue
        if isinstance(rec, dict) and rec.get("id"):
            out.append(rec)
    return out


def _language(requires: Any) -> str:
    """从 requires（cargo>=1.75 / dotnet>=8 / python>=3.11）取工具名（比较符前段）。"""
    for item in (requires or []):
        s = str(item).strip()
        if not s:
            continue
        for sep in (">=", "<=", "==", ">", "<", "~="):
            if sep in s:
                return s.split(sep, 1)[0].strip()
        return s
    return ""


def providers(root: str = ".") -> List[Dict[str, Any]]:
    """全部接入面 → provider 记录（engine 标记 / 语言 / 入口在场 / 工具链在场）。"""
    out: List[Dict[str, Any]] = []
    for rec in _face_docs(root):
        entry = rec.get("entry") if isinstance(rec.get("entry"), dict) else {}
        path = str(entry.get("path") or "")
        tool = _language(rec.get("requires"))
        out.append({
            "id": str(rec.get("id")),
            "title": str(rec.get("title") or ""),
            "kind": str(rec.get("kind") or ""),
            "status": str(rec.get("status") or ""),
            "version": str(rec.get("version") or ""),
            "engine": path.startswith(ENGINE_PREFIX),
            "language": tool,
            "entry_path": path,
            "entry_present": bool(path) and (Path(root) / path).exists(),
            "tool_present": bool(tool) and shutil.which(tool) is not None,
        })
    return out


def engines(root: str = ".") -> List[Dict[str, Any]]:
    """引擎实现 provider（入口落在 engine/ 的接入面）。"""
    return [p for p in providers(root) if p["engine"]]


def resolve(root: str = ".", want: str = "") -> Optional[Dict[str, Any]]:
    """按 provider id 或语言解析到一条记录；未命中 None。"""
    key = str(want).strip().lower()
    if not key:
        return None
    for p in providers(root):
        if str(p["id"]).lower() == key or str(p["language"]).lower() == key:
            return p
    return None


def matrix(root: str = ".") -> Dict[str, List[str]]:
    """能力矩阵：语言 → provider id 列表（按 id 排序）。"""
    out: Dict[str, List[str]] = {}
    for p in providers(root):
        out.setdefault(str(p["language"]) or "(未声明)", []).append(str(p["id"]))
    return {k: sorted(v) for k, v in sorted(out.items())}


def status(root: str = ".") -> Dict[str, Any]:
    """装载就绪概览：引擎数 / 就绪数（entry 与 toolchain 都在场）/ 逐引擎明细。"""
    engs = engines(root)
    ready = [p for p in engs if p["entry_present"] and p["tool_present"]]
    return {
        "engines": len(engs),
        "ready": len(ready),
        "detail": [{"id": p["id"], "language": p["language"],
                    "entry_present": p["entry_present"],
                    "tool_present": p["tool_present"]} for p in engs],
    }


def report_lines(root: str = ".") -> List[str]:
    """人读报告行（供脚本逐行打印；无内嵌换行）。"""
    st = status(root)
    out = ["== 引擎 provider（只读）=="]
    for p in engines(root):
        out.append("  %-16s %-8s entry=%s tool=%s" % (
            p["id"], p["language"] or "-",
            "在" if p["entry_present"] else "缺", "在" if p["tool_present"] else "缺"))
    out.append("  引擎 %d · 本机就绪 %d（就绪 = 入口与工具链都在场）"
               % (st["engines"], st["ready"]))
    return out
