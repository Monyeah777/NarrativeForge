"""NF 包管理器核心解析面（Registry Pattern 之上的「按品类取件」统一 API）。

内部差距（2026-10-09 实测，G3）：品类各写各的解析——community_inventory 自己 glob
community/*/modules|pipelines、asset_ledger 自定 SHELF_GLOBS、mcp_runtime 有 15 处 glob、
patterns / knowledge / library 各写 entries()。「按品类定位一个件」多份实现 = 改一份忘一份。
本模块把「品类 → 条目（id/path）→ 解析/读取/检索」收成一处，底层枚举走 category_registry
（其 glob 又派生自 protocol/LAYERS.json 真源），故路径知识只有一条链。

分工：
- category_registry = 品类注册表（有哪些品类、各自 glob）；
- package_index    = 包管理器面（按品类/id 取件、读取、检索）；消费方只用本面。

纪律：纯标准库；只读；无网络；同输入同输出；未知品类/缺件一律 fail-closed 返回空，不裸崩。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core import category_registry as cr

#: 包管理器默认检索面（不含 tier:* 全树 glob——那是审计面，不是包面）
SEARCH_CATEGORIES: Tuple[str, ...] = (
    "patterns", "library-items", "core-pipelines",
    "community-modules", "community-pipelines", "package-assets",
)


def item_id(rel: str) -> str:
    """从相对路径取条目 id：PATTERN.md 取目录名，其余取文件名首段（M55_x.md 到 M55）。"""
    p = Path(str(rel))
    if p.name == "PATTERN.md":
        return p.parent.name
    stem = p.stem
    return stem.split("_")[0] if "_" in stem else stem


def entries(root: str = ".", cat_id: str = "", under: str = "") -> List[Dict[str, Any]]:
    """品类条目表（{id, path, category, name}）；under 为仓库相对前缀过滤。"""
    out: List[Dict[str, Any]] = []
    for rel in cr.files(root, cat_id):
        if under and not rel.startswith(under):
            continue
        out.append({"id": item_id(rel), "path": rel, "category": cat_id,
                    "name": Path(rel).stem})
    return out


def files_under(root: str = ".", cat_id: str = "", under: str = "") -> List[Path]:
    """品类内某仓库相对前缀下的件 → Path 列表（消费方便捷面）。"""
    return [Path(root) / str(rec["path"]) for rec in entries(root, cat_id, under=under)]


def resolve(root: str = ".", cat_id: str = "", ref: str = "",
            under: str = "") -> Dict[str, Any]:
    """按 id 定位条目：精确命中，或文件名以 id_ 开头（模块/管线的编号约定）。"""
    want = str(ref).strip()
    if not want:
        return {}
    for rec in entries(root, cat_id, under=under):
        base = str(rec["path"]).split("/")[-1]
        if rec["id"] == want or base.startswith(want + "_"):
            return rec
    return {}


def path_of(root: str = ".", cat_id: str = "", ref: str = "",
            under: str = "") -> Optional[Path]:
    """定位条目到 Path；未命中 None（读盘与否由调用方按各自错误口径决定）。"""
    rec = resolve(root, cat_id, ref, under=under)
    return (Path(root) / str(rec["path"])) if rec else None


def read_text(root: str = ".", cat_id: str = "", ref: str = "",
              under: str = "") -> str:
    """读条目正文；未命中/不可读返回空串（调用方据此报「不可用」，不裸崩）。"""
    p = path_of(root, cat_id, ref, under=under)
    if p is None or not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def find(root: str = ".", ref: str = "") -> List[Dict[str, Any]]:
    """按「品类:编号」或裸编号检索（限定 SEARCH_CATEGORIES）。→ 记录列表（可为空）。"""
    want = str(ref).strip()
    if not want:
        return []
    head, _, tail = want.partition(":")
    if tail:
        if head in SEARCH_CATEGORIES:
            rec = resolve(root, head, tail)
            return [rec] if rec else []
        want = tail          # 全限定 id（如 情感类:M55）按末段编号检索
    hits: List[Dict[str, Any]] = []
    for cat in SEARCH_CATEGORIES:
        rec = resolve(root, cat, want)
        if rec:
            hits.append(rec)
    return hits


def package_dirs(root: str = ".") -> List[str]:
    """域包目录名（community/<pkg>/），按名排序；缺 community/ 返回空。"""
    base = Path(root) / "community"
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir()
                  if p.is_dir() and not p.name.startswith("."))


