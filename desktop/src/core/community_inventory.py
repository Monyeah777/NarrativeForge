"""community 仓库盘点（v2.0.x-E5：模块市场雏形深化——可发现 → 可装载）。

E5 承接 E4（方案 21）：zone_g 从「本地已装检索」扩到「community 仓库可发现 +
一键装载入库」。本模块盘点仓库内已检出的 community/* 四包（校园 P02/西幻 P03/
轻混 P04/通用 P05）的 modules + pipelines：

- catalog(store) -> list[CommunityItem]：盘点全部可装载项 + 已装判定
  （module: store.get_module 命中；pipeline: pipelines cache 含 id）。
- install_module(store, item)：parse community/<pkg>/modules/*.md →
  Store.save_module 装入用户工作区（~/.NarrativeForge/modules），幂等。
- install_pipeline(store, item)：与 pipelines cache 按 id merge 去重 → save。
- load_community_module / load_community_pipeline：只读源正文加载（I5：从源包
  parse，不复制进任何包目录）。

边界（I5 单一真相源）：本模块与 E3 composer.references 只读引用正交——references
是组合包跨包引用「源包模块正文运行时只读入装配」；本模块是用户把 community 包自带
模块「安装进自己的桌面工作区」（等同 seed_from_repo 导入官方核心/zone_g 目录导入
第三方模块的既有模式）。只读源永不写 community/ 目录。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .models import Module, Pipeline, fid_key
from .storage import Store


@dataclass
class CommunityItem:
    """盘点单条（轻量元数据，对齐 retriever.Hit）。"""
    kind: str                # community_module / community_pipeline
    pkg: str                 # 来源包名（校园情感领域包…）
    ref: str                 # full_id（情感类:M55）/ pipeline id（P02）
    name: str
    layer: str = ""          # 仅 module
    installed: bool = False  # 已装判定（module: store 命中；pipeline: cache 含 id）


def _community_root() -> Optional[Path]:
    """定位仓库 community/ 根（复用 registry_loader.Registry._community_root）。"""
    from .registry_loader import Registry
    return Registry._community_root()


def _package_dirs() -> List[Path]:
    root = _community_root()
    if root is None:
        return []
    return sorted(d for d in root.iterdir()
                  if d.is_dir() and not d.name.startswith("."))


def _pipeline_ids_in_cache(store: Store) -> set:
    raw = store.load_cache("pipelines")
    ids: set = set()
    if isinstance(raw, list):
        for d in raw:
            if isinstance(d, dict) and d.get("id"):
                ids.add(str(d["id"]))
    return ids


def _module_file(pkg_dir: Path, module_ref: str) -> Optional[Path]:
    """在包 modules/ 目录定位 <id>_*.md（id 取 ref 末段，如 M55）。"""
    mod_dir = pkg_dir / "modules"
    if not mod_dir.is_dir():
        return None
    num = str(module_ref).split(":")[-1]
    for f in sorted(mod_dir.glob("*.md")):
        if f.name.startswith(num + "_") or f.stem == num:
            return f
    return None


def load_community_module(pkg: str, full_id: str) -> Optional[Module]:
    """只读加载 community/<pkg>/modules 模块正文（parse，I5 不写源）。"""
    from .parser import parse_module
    root = _community_root()
    if root is None:
        return None
    pkg_dir = root / pkg
    f = _module_file(pkg_dir, full_id)
    if f is None:
        return None
    try:
        return parse_module(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_community_pipeline(pkg: str, pid: str) -> Optional[Pipeline]:
    """只读加载 community/<pkg>/pipelines 管线。"""
    from .pipeline_loader import load_pipeline_file
    root = _community_root()
    if root is None:
        return None
    pdir = root / pkg / "pipelines"
    if not pdir.is_dir():
        return None
    for f in sorted(pdir.glob("*.md")):
        try:
            pl = load_pipeline_file(f)
        except Exception:
            continue
        if pl is not None and pl.id == pid:
            return pl
    return None


# ---------------------------------------------------------------- 盘点
def catalog(store: Store) -> List[CommunityItem]:
    """盘点 community 四包全部模块 + 管线，附已装判定。

    module 已装 = store.get_module(full_id) 命中；pipeline 已装 =
    pipelines cache 含该 id。parse 失败的单件跳过（不静默吞——catalog 不抛，
    坏文件只影响自身；合规包不应触发，若出现需人工查）。
    """
    items: List[CommunityItem] = []
    installed_pipes = _pipeline_ids_in_cache(store)
    for pkg_dir in _package_dirs():
        pkg = pkg_dir.name
        mod_dir = pkg_dir / "modules"
        if mod_dir.is_dir():
            for f in sorted(mod_dir.glob("*.md")):
                try:
                    m = load_community_module(pkg, f.stem.split("_")[0])
                except Exception:
                    m = None
                if m is None:
                    # 文件主名可能非 <id>_<名>；退回整名匹配
                    try:
                        from .parser import parse_module
                        m = parse_module(f.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                installed = store.get_module(m.full_id) is not None
                items.append(CommunityItem(
                    kind="community_module", pkg=pkg, ref=m.full_id,
                    name=m.name, layer=m.layer, installed=installed))
        pipe_dir = pkg_dir / "pipelines"
        if pipe_dir.is_dir():
            for f in sorted(pipe_dir.glob("*.md")):
                try:
                    from .pipeline_loader import load_pipeline_file
                    pl = load_pipeline_file(f)
                except Exception:
                    continue
                if pl is not None:
                    items.append(CommunityItem(
                        kind="community_pipeline", pkg=pkg, ref=pl.id,
                        name=pl.name, installed=pl.id in installed_pipes))
    return items


# ---------------------------------------------------------------- 装载
def install_module(store: Store, item: CommunityItem) -> bool:
    """把盘点模块装入用户工作区（幂等：已装判定命中即 True 不重复写）。"""
    if item.kind != "community_module":
        return False
    if store.get_module(item.ref) is not None:
        return True
    m = load_community_module(item.pkg, item.ref)
    if m is None:
        return False
    try:
        store.save_module(m)
        return True
    except Exception:
        return False


def install_pipeline(store: Store, item: CommunityItem) -> bool:
    """把盘点管线并入 pipelines cache（按 id merge 去重，不覆盖既有管线）。"""
    if item.kind != "community_pipeline":
        return False
    pl = load_community_pipeline(item.pkg, item.ref)
    if pl is None:
        return False
    raw = store.load_cache("pipelines")
    cur = list(raw) if isinstance(raw, list) else []
    seen = set()
    merged = []
    for d in cur:
        if isinstance(d, dict) and d.get("id"):
            if d["id"] in seen:
                continue
            seen.add(d["id"])
            merged.append(d)
        else:
            merged.append(d)   # 非标准条目原样保留
    if pl.id not in seen:
        merged.append(pl.to_json())
    store.save_cache("pipelines", merged)
    return True
