"""NF 定义库品类注册表（Registry Pattern）——「有哪些定义库品类、各自在哪、怎么枚举」的唯一出处。

内部差距（2026-10-09 实测）：protocol/LAYERS.json 已是层级与资产子级 glob 的真源，但 core 有
60+ 处 .glob() 各自硬编码同一批路径（repo_stats / community_inventory / mcp_runtime / knowledge /
domain_pack / pack_combo / pipeline_loader / module_lifecycle / nf_language / asset_ledger /
asset_line_baseline / machine_contract / conformance_report）。同一路径知识多份 = 改一份忘一份；
本模块把「品类 → glob」收进注册表，消费方按品类名取件，路径知识只此一处。

真源纪律（避免双真源）：
- 层级归属的品类**从 protocol/LAYERS.json 派生**（tiers.source.globs 与 asset_levels.globs），
  本模块不重抄这些 glob；
- LAYERS 尚未归属、或属其**命名子面**的品类，显式登记进 LOCAL_CATEGORIES 并标 attributed=false，
  如实暴露「全树归属」缺口（ADR-0004 遗留），待回填 LAYERS 后删除。

纪律：纯标准库；只读；无网络；同输入同输出；缺件/坏件如实报 issue 不裸崩。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

LAYERS_REL = "protocol/LAYERS.json"

#: LAYERS 未归属（或为其命名子面）的品类：attributed=false 即「待回填抽象阶梯」。
LOCAL_CATEGORIES: Tuple[Dict[str, Any], ...] = (
    {"id": "patterns", "title": "实践包品类", "tier": "asset",
     "globs": ("patterns/*/PATTERN.md",), "attributed": False,
     "note": "LAYERS 四阶/五子级均未含 patterns/*（全树归属缺口，见 ADR-0004）。"},
    {"id": "integrations", "title": "接入面", "tier": "surface",
     "globs": ("integrations/*/integration.json",), "attributed": False,
     "note": "接入面是入口面（非真源）；LAYERS surfaces 只登记件，不登记本 glob。"},
    {"id": "core-pipelines", "title": "官方核心管线（P*）", "tier": "asset",
     "globs": ("03_管线库/P*.md",), "attributed": False,
     "note": "content 子级的编号子面（P*）：固定编号口径，免消费方重写路径。"},
    {"id": "package-assets", "title": "域包资产", "tier": "asset",
     "globs": ("community/*/assets/*.md",), "attributed": False,
     "note": "data 子级的 community 侧子面（官方资产库 05_资产库 另计）。"},
    {"id": "concept-graphs", "title": "域包概念图", "tier": "asset",
     "globs": ("community/*/assets/CONCEPT_GRAPH.md",), "attributed": False,
     "note": "data 子级的固定名子面。"},
    {"id": "library-items", "title": "馆藏条目", "tier": "asset",
     "globs": ("library/*.md",), "attributed": False,
     "note": "asset 阶 source 的 library 子面；INDEX/ALIAS 由消费方按名剔除。"},
)


def layers_doc(root: str) -> Dict[str, Any]:
    """读抽象阶梯真源（缺件/坏件返回 {}，由 scan 如实报）。"""
    p = Path(root) / LAYERS_REL
    if not p.is_file():
        return {}
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return doc if isinstance(doc, dict) else {}


def _rec(rec_id: str, title: str, tier: str, globs: Any, note: str) -> Dict[str, Any]:
    return {"id": rec_id, "title": title, "tier": tier,
            "globs": tuple(str(g) for g in (globs or ())),
            "attributed": True, "note": note}


def categories(root: str = ".") -> List[Dict[str, Any]]:
    """品类表（按 id 排序）：LAYERS 派生（attributed=true）+ 本地登记（attributed=false）。"""
    doc = layers_doc(root)
    out: List[Dict[str, Any]] = []
    for t in doc.get("tiers") or []:
        if not isinstance(t, dict):
            continue
        src = t.get("source") or {}
        out.append(_rec("tier:" + str(t.get("id")),
                        "%s阶真源" % (t.get("name") or t.get("id")),
                        "tier", src.get("globs"), str(src.get("note") or "")))
    for a in doc.get("asset_levels") or []:
        if not isinstance(a, dict):
            continue
        out.append(_rec("level:" + str(a.get("id")),
                        "%s子级" % (a.get("name") or a.get("id")),
                        str(a.get("tier") or "asset"), a.get("globs"),
                        str(a.get("note") or "")))
    out.extend(dict(c) for c in LOCAL_CATEGORIES)
    out.sort(key=lambda c: str(c["id"]))
    return out


def category(root: str, cat_id: str) -> Dict[str, Any]:
    """按 id 取品类记录；不存在返回 {}。"""
    for c in categories(root):
        if c["id"] == cat_id:
            return c
    return {}


def globs(root: str, cat_id: str) -> Tuple[str, ...]:
    """品类声明的 glob 元组（未知品类返回空元组）。"""
    return tuple(category(root, cat_id).get("globs") or ())


def files(root: str, cat_id: str) -> List[str]:
    """按品类枚举文件（仓库相对 posix 路径；逐 glob 各自排序，不跨 glob 去重）。"""
    base = Path(root)
    out: List[str] = []
    for pat in globs(root, cat_id):
        out.extend(sorted(p.relative_to(base).as_posix()
                          for p in base.glob(pat) if p.is_file()))
    return out


def locate(root: str, rel: str) -> List[str]:
    """反查：某仓库相对路径落在哪些品类里（含命名子面；按 id 排序）。"""
    target = Path(str(rel)).as_posix()
    hit: List[str] = []
    for c in categories(root):
        if target in set(files(root, str(c["id"]))):
            hit.append(str(c["id"]))
    return sorted(hit)


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """注册表自检 → (issues, warns, stats)：id 唯一 / 缺真源件 / 归属缺口如实报。"""
    issues: List[str] = []
    warns: List[str] = []
    if not layers_doc(root):
        issues.append("缺抽象阶梯真源 %s（品类表无从派生；修复指引：在 NF 仓库根运行）" % LAYERS_REL)
    cats = categories(root)
    seen: Dict[str, int] = {}
    empty: List[str] = []
    for c in cats:
        cid = str(c["id"])
        seen[cid] = seen.get(cid, 0) + 1
        if not c["globs"]:
            issues.append("品类 %s 未声明任何 glob" % cid)
        elif not files(root, cid):
            empty.append(cid)
    for cid, n in sorted(seen.items()):
        if n > 1:
            issues.append("品类 id 重复 %d 次：%s" % (n, cid))
    by_globs: Dict[Tuple[str, ...], List[str]] = {}
    for c in cats:
        by_globs.setdefault(tuple(c["globs"]), []).append(str(c["id"]))
    for gl, ids in sorted(by_globs.items()):
        if len(ids) > 1:
            issues.append("品类 glob 集合重复（同一件事多个 id——请并入 LAYERS 真源或改名）：%s -> %s"
                          % ("、".join(sorted(ids)), " , ".join(gl)))
    if empty:
        warns.append("以下品类 glob 未命中在場件（缺件或路径漂移）：%s" % "、".join(empty))
    unattributed = [str(c["id"]) for c in cats if not c.get("attributed")]
    if unattributed:
        warns.append("LAYERS 未归属品类 %d 个（待回填抽象阶梯）：%s"
                     % (len(unattributed), "、".join(unattributed)))
    stats = {"categories": len(cats), "attributed": len(cats) - len(unattributed),
             "unattributed": len(unattributed)}
    return issues, warns, stats
