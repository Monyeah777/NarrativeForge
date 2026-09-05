"""Agentic 检索（v1.3.0 retriever：四类对象统一检索入口，2.0 E0-②）。

- search(store, kind, query) -> list[Hit]：module / asset_pack / pipeline /
  protocol 四类对象统一检索，query 在 ref/name/tags/描述 上大小写不敏感子串匹配。
  E5 扩展：kind=community_module / community_pipeline 显式检索 community 仓库
  盘点（可装载未装 + 已装项，入 kind=None 全量）。
- **不上向量库**：对象量级几十~几百，全表线性扫描足够（结构化 grep 原则）。
- **Discovery 轻量**：每 Hit 只带元数据卡片（ref/name/tags/layer），不带正文——
  全文按需在装配/选择时加载（对齐 Agent Skills 渐进披露 Discovery/Activation 两层）。
- 装配动作因此可基于已有资源（检索 → 复用），不从零开始。

数据源：
  module       Store.list_modules()（已装模块库）
  asset_pack   Store.list_asset_packs()（本地资产包）
  pipeline     Store.load_cache('pipelines')（桌面侧管线缓存，I5 单一真相源）
  protocol     registry_loader.load_registry().protocols（registry.json，I5）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .models import Module, AssetPack
from .storage import Store


@dataclass
class Hit:
    """元数据卡片（Discovery 层）。"""
    kind: str                # module / asset_pack / pipeline / protocol
    ref: str                 # full_id / pack_name / pipeline_id / protocol_id
    name: str
    tags: list = field(default_factory=list)
    layer: str = ""          # 仅 module（挂载层）；其它类型空


def _match(query: str, *fields) -> bool:
    q = query.strip().lower()
    if not q:
        return True
    return any(q in (f or "").lower() for f in fields)


# ------------------------------------------------------------------ 四源
def _module_hits(store: Store, q: str, limit: int) -> List[Hit]:
    out = []
    for m in store.list_modules():
        if _match(q, m.full_id, m.id, m.name, m.category, m.layer):
            out.append(Hit(kind="module", ref=m.full_id, name=m.name,
                           tags=[m.category], layer=m.layer))
        if len(out) >= limit:
            break
    return out


def _asset_pack_hits(store: Store, q: str, limit: int) -> List[Hit]:
    out = []
    for a in store.list_asset_packs():
        tag = f"{len(a.entries)}键"
        if _match(q, a.name, tag):
            out.append(Hit(kind="asset_pack", ref=a.name, name=a.name,
                           tags=[tag]))
        if len(out) >= limit:
            break
    return out


def _pipeline_hits(store: Store, q: str, limit: int) -> List[Hit]:
    out = []
    raw = store.load_cache("pipelines")
    if isinstance(raw, list):
        for p in raw:
            pid = p.get("id", "")
            pname = p.get("name", "")
            if _match(q, pid, pname):
                out.append(Hit(kind="pipeline", ref=pid, name=pname))
            if len(out) >= limit:
                break
    return out


def _protocol_hits(q: str, limit: int) -> List[Hit]:
    """协议源：registry.json protocols[]（I5 真相源；社区协议已投影在册）。"""
    out = []
    try:
        from .registry_loader import load_registry
        registry = load_registry()
        for p in (registry.protocols or []):
            pid = p.get("id", "")
            refs = p.get("references") or []
            tag = f"{len(refs)}引用"
            if _match(q, pid, pid, tag):
                out.append(Hit(kind="protocol", ref=pid, name=pid, tags=[tag]))
            if len(out) >= limit:
                break
    except Exception:
        pass    # registry 缺失/损坏：protocol 源空（不阻断其它源检索）
    return out


# ------------------------------------------------------------------ 入口
def _community_hits(store: Store, kind: str, q: str, limit: int) -> List[Hit]:
    """社区仓库盘点源（E5）：community/<pkg> 可装载未装 + 已装判定。

    仅在显式 kind=community_module / community_pipeline 时检索（不入
    kind=None 全量混排——社区项与已装 module 可能同 ref 双行，噪音大于
    价值；E4 四类「本地已装/在册」语义保持独立）。
    """
    out = []
    try:
        from .community_inventory import catalog
        for it in catalog(store):
            if it.kind != kind:
                continue
            if not _match(q, it.ref, it.name, it.pkg, it.layer):
                continue
            state = "✓已装" if it.installed else "可装载"
            tags = [it.pkg, state]
            out.append(Hit(kind=kind, ref=it.ref, name=it.name,
                           tags=tags, layer=it.layer))
            if len(out) >= limit:
                break
    except Exception:
        pass    # 盘点失败（仓库缺 community/）：社区源空（不阻断其它源）
    return out


def search(store: Store, kind: Optional[str] = None,
           query: str = "", *, limit: int = 30) -> List[Hit]:
    """统一检索入口。kind=None 跨四类（本地已装/在册）；query 空串返回 Discovery 列表。

    E5 扩展：kind='community_module' / 'community_pipeline' 检索 community
    仓库盘点（可装载未装 + 已装项），显式指定才并入。
    """
    q = (query or "").strip()
    hits: List[Hit] = []
    wanted = kind in (None, "module")
    if wanted:
        hits.extend(_module_hits(store, q, limit))
    if kind in (None, "asset_pack"):
        hits.extend(_asset_pack_hits(store, q, limit))
    if kind in (None, "pipeline"):
        hits.extend(_pipeline_hits(store, q, limit))
    if kind in (None, "protocol"):
        hits.extend(_protocol_hits(q, limit))
    if kind in ("community_module", "community_pipeline"):
        hits.extend(_community_hits(store, kind, q, limit))
    return hits[:limit]
