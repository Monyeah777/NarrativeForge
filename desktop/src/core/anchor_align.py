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
#: 标准目录的五个层（口径同 protocol/standards_catalog.json 的 coverage.by_layer）
LAYERS = ("data", "eng", "form", "gov", "iface")
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


def pack_stats(root: str = ".") -> List[Dict[str, Any]]:
    """逐域包标准对齐概览（按层覆盖宽度升序）：绑定数 / 标准数 / 各层计数 / 层覆盖宽度。"""
    rows: List[Dict[str, Any]] = []
    for p in (_read(root, BINDING_REL).get("packs") or []):
        if not isinstance(p, dict):
            continue
        binds = [b for b in (p.get("bindings") or []) if isinstance(b, dict)]
        layers: Dict[str, int] = {}
        for b in binds:
            lay = str(b.get("standard_layer") or "(未声明)")
            layers[lay] = layers.get(lay, 0) + 1
        rows.append({
            "code": str(p.get("code") or ""),
            "package": str(p.get("package") or ""),
            "category": str(p.get("category") or ""),
            "subdivisions": int(p.get("subdivisions") or 0),
            "bindings": len(binds),
            "distinct_standards": len({str(b.get("standard")) for b in binds if b.get("standard")}),
            "layers": {k: layers[k] for k in sorted(layers)},
            "layer_breadth": len(layers),
            "missing_layers": [x for x in LAYERS if x not in layers],
        })
    return sorted(rows, key=lambda r: (int(r["layer_breadth"]), int(r["distinct_standards"]),
                                       str(r["code"])))


def shallow_packs(root: str = ".", max_breadth: int = 2) -> List[Dict[str, Any]]:
    """层覆盖宽度 ≤ max_breadth 的域包（反向对齐的优先补强清单，按宽度升序）。"""
    limit = max(0, int(max_breadth))
    return [r for r in pack_stats(root) if int(r["layer_breadth"]) <= limit]


def depends(root: str = ".") -> Dict[str, List[str]]:
    """标准依赖图（id → depends_on 在册项，去重排序；悬空引用剔除）。"""
    ids = {str(s.get("id")) for s in catalog(root)}
    out: Dict[str, List[str]] = {}
    for s in catalog(root):
        sid = str(s.get("id"))
        out[sid] = sorted({str(d) for d in (s.get("depends_on") or []) if str(d) in ids})
    return out


def dependents(root: str = ".") -> Dict[str, List[str]]:
    """反向依赖图（id → 依赖它的 id 列表，按 id 排序）。"""
    rev: Dict[str, List[str]] = {}
    for sid, ds in depends(root).items():
        for d in ds:
            rev.setdefault(d, []).append(sid)
    return {k: sorted(v) for k, v in rev.items()}


def bootstrap(root: str = ".", term: str = "", depth: int = 1,
              limit: int = 0) -> List[Dict[str, Any]]:
    """正向自举：词汇命中标准（种子）→ 沿依赖与反向依赖各扩 depth 层。

    返回 [{id, layer, title, hits, depth, via}]，按（depth 升、hits 降、id 升）排序；
    hits 只在种子非零；via = 带入者（种子记 term，扩展节点记父标准 id）。depth=0 只回种子。
    """
    seeds = intersect(root, term, include_bound=True)
    if not seeds:
        return []
    by_id = {str(s.get("id")): s for s in catalog(root)}
    fwd, rev = depends(root), dependents(root)
    nodes: Dict[str, Dict[str, Any]] = {}
    frontier: List[str] = []
    for s in seeds:
        sid = str(s["id"])
        nodes[sid] = {"id": sid, "layer": str(s.get("layer") or ""),
                      "title": str(s.get("title") or ""), "hits": int(s["hits"]),
                      "depth": 0, "via": str(term)}
        frontier.append(sid)
    for level in range(1, max(0, int(depth)) + 1):
        nxt: List[str] = []
        for sid in sorted(frontier):
            for nb in sorted(set(fwd.get(sid, []) + rev.get(sid, []))):
                if nb in nodes:
                    continue
                s = by_id.get(nb) or {}
                nodes[nb] = {"id": nb, "layer": str(s.get("layer") or ""),
                             "title": str(s.get("title") or ""), "hits": 0,
                             "depth": level, "via": sid}
                nxt.append(nb)
        frontier = nxt
        if not frontier:
            break
    rows = sorted(nodes.values(), key=lambda r: (int(r["depth"]), -int(r["hits"]), str(r["id"])))
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
