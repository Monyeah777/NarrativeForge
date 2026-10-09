"""双向锚定对齐面：反向量化「项目对已收集标准的内化度」，正向按词汇找标准交叉候选。

内部差距（2026-10-09 实测）：protocol/standards_catalog.json 收集 370 条可扩展标准，但
protocol/standards_binding.json 的 100 包 × 1200 条绑定只实际引用 68 条 —— 302 条（81.6%）
从未被任何域包绑定。现有判据（check32 domain_packs）只判「每条细分都有 standard_ref」这一侧，
不判「收集来的标准被用得怎么样」。本模块把两侧打通：

- stats(root)：反向量化内化度（目录利用率 / 各 layer 已绑定与未绑定数 / 包与绑定总数）；
- unbound(root, layer)：未绑定标准清单（可按 layer 过滤）；
- intersect(root, term)：正向按词汇在（未）绑定标准里找交叉候选（id/title/body 词面命中，确定性）。

纪律：纯标准库；只读；无网络；同输入同输出；缺件/坏件返回零值，不裸崩。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

CATALOG_REL = "protocol/standards_catalog.json"
BINDING_REL = "protocol/standards_binding.json"
_TOKEN = re.compile(r"[a-z0-9_]+")
_HAN = re.compile("[一-龥]+")


def _read(root: str, rel: str) -> Dict[str, Any]:
    p = Path(root) / rel
    if not p.is_file():
        return {}
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:  # 坏件按缺件处理：不打断报告，消费方据 stats 全 0 自证
        return {}
    return doc if isinstance(doc, dict) else {}


def catalog(root: str = ".") -> List[Dict[str, Any]]:
    """标准目录条目（缺件/坏件返回空表）。"""
    return [s for s in (_read(root, CATALOG_REL).get("standards") or []) if isinstance(s, dict)]


def bound_ids(root: str = ".") -> set:
    """被任一域包绑定引用过的标准 id 集合（standard / standard_ref 两种键名都认）。"""
    out: set = set()
    for p in (_read(root, BINDING_REL).get("packs") or []):
        if not isinstance(p, dict):
            continue
        for b in (p.get("bindings") or []):
            sid = (b.get("standard") or b.get("standard_ref")) if isinstance(b, dict) else b
            if sid:
                out.add(str(sid))
    return out


def stats(root: str = ".") -> Dict[str, Any]:
    """反向：目录利用率总览（确定性）。"""
    rows = catalog(root)
    ids = [str(s.get("id")) for s in rows if s.get("id")]
    bound = bound_ids(root) & set(ids)
    by_layer: Dict[str, Dict[str, int]] = {}
    for s in rows:
        cell = by_layer.setdefault(str(s.get("layer") or "(未声明)"),
                                   {"total": 0, "bound": 0, "unbound": 0})
        cell["total"] += 1
        if str(s.get("id")) in bound:
            cell["bound"] += 1
        else:
            cell["unbound"] += 1
    packs = [p for p in (_read(root, BINDING_REL).get("packs") or []) if isinstance(p, dict)]
    total = len(ids)
    return {
        "standards": total,
        "bound": len(bound),
        "unbound": total - len(bound),
        "utilization": round(len(bound) / total, 4) if total else 0.0,
        "packs": len(packs),
        "bindings": sum(len(p.get("bindings") or []) for p in packs),
        "by_layer": {k: by_layer[k] for k in sorted(by_layer)},
    }


def unbound(root: str = ".", layer: str = "") -> List[Dict[str, Any]]:
    """未绑定标准清单（可按 layer 过滤；按 id 排序）。"""
    b = bound_ids(root)
    want = str(layer).strip()
    rows = [s for s in catalog(root)
            if str(s.get("id")) not in b and (not want or str(s.get("layer")) == want)]
    return sorted(rows, key=lambda s: str(s.get("id")))


def _terms(text: Any) -> List[str]:
    """词元：英文 [a-z0-9_] 词 + 中文整段与 2-gram（中英混排口径，同 core.library 检索精神）。"""
    s = str(text or "").lower()
    out = _TOKEN.findall(s)
    for h in _HAN.findall(s):
        out.append(h)
        if len(h) > 1:
            out.extend(h[i:i + 2] for i in range(len(h) - 1))
    return out


def intersect(root: str = ".", term: str = "", layer: str = "",
              limit: int = 0, include_bound: bool = False) -> List[Dict[str, Any]]:
    """正向：按词汇在标准里找交叉候选（命中数降序，同分按 id 升序）。

    词面 = term 的 [a-z0-9_] 词元与「id + title + body」词元的交集大小；0 命中不进表。
    """
    want = {t for t in _terms(term) if len(t) > 1}
    if not want:
        return []
    b = bound_ids(root)
    look = str(layer).strip()
    rows: List[Dict[str, Any]] = []
    for s in catalog(root):
        sid = str(s.get("id"))
        if not include_bound and sid in b:
            continue
        if look and str(s.get("layer")) != look:
            continue
        hay = set(_terms(sid) + _terms(s.get("title")) + _terms(s.get("body")))
        hit = sum(1 for t in want if t in hay)
        if hit:
            rows.append({"id": sid, "layer": str(s.get("layer") or ""),
                         "body": str(s.get("body") or ""),
                         "title": str(s.get("title") or ""), "hits": hit,
                         "bound": sid in b})
    rows.sort(key=lambda r: (-int(r["hits"]), str(r["id"])))
    return rows[:limit] if limit and limit > 0 else rows


def report(root: str = ".") -> str:
    """人读报告（反向利用率 + 各 layer 未绑定数）。"""
    st = stats(root)
    out = ["# 双向锚定对齐报告", "",
           "标准目录 %d 条 · 已绑定 %d · 未绑定 %d · 利用率 %.1f%% · 域包 %d · 绑定 %d"
           % (st["standards"], st["bound"], st["unbound"], st["utilization"] * 100.0,
              st["packs"], st["bindings"]), "",
           "| layer | 总 | 已绑定 | 未绑定 |", "|---|---|---|---|"]
    for lay, c in st["by_layer"].items():
        out.append("| %s | %d | %d | %d |" % (lay, c["total"], c["bound"], c["unbound"]))
    return "\n".join(out) + "\n"
