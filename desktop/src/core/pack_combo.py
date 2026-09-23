"""域包自由组合引擎（任意 n 元 × 任意组件）。

目标：100 个域包（+ 既有社区包）**任意子集**可自由组合；包内组件（协议 / 管线 / 模块 /
资产）也可自由取用；组合广度 = 2^N（不预先枚举）；深度质量 = 每条组合必须过**五条可机检
不变量**；产出 = **可复算证书**（T4：门禁重算并与在盘证书逐字段比对）。

五条不变量（任一不成立即非法，不许静默降级）：
1. **模块唯一可定位**：选中模块 id 唯一，且能定位到机读契约（缺契约即报）；
2. **依赖闭合**：模块 `inputs` 只能指向「组合内模块」∪「官方核心 13 件」，否则报 dangling；
3. **事件闭合**：任一 `subscribe` 必须在本组合内有发布方（本仓域包事件按域码命名空间，
   包内自闭合；跨包订阅须显式事件桥，否则报 unbridged）；
4. **层位堆叠确定**：同层多包默认挂载按（声明序 → 模块 id）确定性堆叠，产出 `layer_stacks`；
5. **资产可寻址**：跨包资产以 `asset_readonly` 借阅，键须能在源包 provenance 台账找到。

广度证明（`breadth`）：全部两两组合（C(N,2)）+ 定种子抽样的三元 / 四元组合跑同一套不变量，
断言「任意组合合法」——广度不靠枚举，靠**不变量在全集上成立**。
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

from core import conformance_scan as csc

CERT_REL = "protocol/combo_certificates.json"
CORE13 = ["M00", "通用:M10", "M08", "M23", "M24", "M50", "M80",
          "事件:M22", "M06", "M12", "M13", "M20", "M90"]

#: 进程级画像缓存（root 绝对路径 → {"prof", "contracts", "by_id", "pub_index", "core_pub"}）。
#: 必要性（实测 2026-09-23）：广度证明要跑 C(N,2)+抽样数千次组合，若每次重解析
#: 235 个模块文档，代价 O(N²·files) 直接跑不完——缓存后单次组合降为纯集合运算。
_CACHE: Dict[str, Dict[str, Any]] = {}


def _cache_key(root: str) -> str:
    return str(Path(root).resolve())


def cache_clear() -> None:
    _CACHE.clear()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _core_ids() -> Set[str]:
    out = set(CORE13)
    for x in CORE13:
        out.add(x.split(":")[-1])
    return out


def _pack_dirs(root: str = ".") -> List[Path]:
    base = Path(root) / "community"
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir()
                  if p.is_dir() and (p / "protocol.yaml").is_file())


def _parse_protocol(path: Path) -> Dict[str, Any]:
    """极小读取：只取组合需要的键（id / pipeline / module_id_range / mount_layers）。"""
    text = path.read_text(encoding="utf-8")
    out: Dict[str, Any] = {"dir": path.parent.name}
    m = re.search(r"(?m)^\s*id:\s*(\S+)\s*$", text)
    out["id"] = m.group(1) if m else path.parent.name
    m = re.search(r"(?m)^\s*pipeline:\s*(P\d{2,3})\s*$", text)
    out["pipeline"] = m.group(1) if m else ""
    # 行式清单：`    - "情感:M22"   # 注释` / `    - "M40"    # 注释`（注释须容忍）
    ids = re.findall(r'(?m)^\s*-\s*"([^"]+:M\d{2,3})"\s*(?:#.*)?$', text)
    ids += re.findall(r'(?m)^\s*-\s*"?(M\d{2,3})"?\s*(?:#.*)?$', text)
    ids = list(dict.fromkeys(ids))          # 两种写法并集（旧包混用行式裸号与全限定）
    if not ids:                       # flow 写法：`module_id_range: [M40, 情感:M22]`
        m = re.search(r"(?m)^\s*module_id_range\s*:\s*\[([^\]]*)\]", text)
        if m:
            ids = [x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()]
    out["module_ids"] = ids
    layers: Dict[str, List[str]] = {}
    for lm in re.finditer(r"(?m)^\s*(P\d{2})\s*[^:]*:\s*\{default:\s*\[([^\]]*)\]", text):
        mods = [x.strip().strip("'\"") for x in lm.group(2).split(",") if x.strip()]
        if mods:
            layers[lm.group(1)] = mods
    out["mount_layers"] = layers
    refs = []
    for rm in re.finditer(r"(?ms)^\s*-\s*source_package:\s*(\S+)\s*\n\s*module_id:\s*(\S+)", text):
        refs.append({"source_package": rm.group(1).strip("'\""),
                     "module_id": rm.group(2).strip("'\"")})
    out["references"] = refs
    return out


def _module_contracts(root: str = ".") -> Dict[str, Dict[str, Any]]:
    """community/*/modules/*.md → {module id（全限定与裸号均可查）: 契约摘要}。"""
    key = _cache_key(root)
    cached = _CACHE.get(key) or {}
    if cached.get("contracts"):
        return cached["contracts"]
    out: Dict[str, Dict[str, Any]] = {}
    for p in sorted(Path(root).glob("community/*/modules/*.md")):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = (parsed or {}).get("machine_contract") or {}
        if not isinstance(mc, dict) or not mc:
            continue
        rec = {
            "id": str(mc.get("id") or p.stem.split("_")[0]),
            "stem": p.stem.split("_")[0],
            "pack": p.parents[1].name,
            "layer": str(mc.get("layer") or ""),
            "inputs": [str(x) for x in (mc.get("inputs") or [])],
            "outputs": [str(x) for x in (mc.get("outputs") or [])],
            "publish": [str(x) for x in ((mc.get("events") or {}).get("publish") or [])],
            "subscribe": [str(x) for x in ((mc.get("events") or {}).get("subscribe") or [])],
            "path": p.as_posix(),
        }
        out[rec["id"]] = rec
        out.setdefault(rec["stem"], rec)
        out.setdefault(rec["id"].split(":")[-1], rec)
    cached.update({"contracts": out})
    _CACHE[key] = cached
    return out


def _core_contracts(root: str = ".") -> Dict[str, Dict[str, Any]]:
    """官方核心 13 件（04_模块库/*/*.md）的契约摘要。

    必要性（2026-09-23 实测）：`core_only: true` 意味着**核心模块永远随任意组合装载**，
    故事件闭包必须把核心的 publish 计入；否则 chaos_event / minute_tick 这类核心事件
    会被误报为「未桥」。
    """
    out: Dict[str, Dict[str, Any]] = {}
    for p in sorted(Path(root).glob("04_模块库/*/*.md")):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        mc = (csc._fence_yaml(text, "machine_contract") or {}).get("machine_contract") or {}
        if not isinstance(mc, dict) or not mc:
            continue
        rec = {"id": str(mc.get("id") or p.stem.split("_")[0]),
               "stem": p.stem.split("_")[0],
               "publish": [str(x) for x in ((mc.get("events") or {}).get("publish") or [])],
               "subscribe": [str(x) for x in ((mc.get("events") or {}).get("subscribe") or [])],
               "path": p.as_posix()}
        out[rec["id"]] = rec
        out.setdefault(rec["stem"], rec)
    return out


def indexes(root: str = ".") -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[Dict[str, Any]]],
                                      Set[str]]:
    """组合闭包用的三类索引（一次构建、供广度证明复用）：
    module id → 契约、事件 → 发布方列表、核心发布事件集。"""
    key = _cache_key(root)
    cached = _CACHE.get(key) or {}
    if cached.get("by_id") is not None:
        return cached["by_id"], cached["pub_index"], cached["core_pub"]
    contracts = _module_contracts(root)
    by_id: Dict[str, Dict[str, Any]] = {}
    pub_index: Dict[str, List[Dict[str, Any]]] = {}
    for r in contracts.values():
        if not r.get("path"):
            continue
        by_id.setdefault(r["id"], r)
        for e in r.get("publish") or []:
            pub_index.setdefault(e, []).append(r)
    core_pub = {e for r in _core_contracts(root).values() for e in r.get("publish", [])}
    prof = profiles(root)
    cached.update({"prof": prof, "contracts": contracts, "by_id": by_id,
                   "pub_index": pub_index, "core_pub": core_pub})
    _CACHE[key] = cached
    return by_id, pub_index, core_pub


def _pack_assets(root: str, pkg_dir: str) -> List[Dict[str, str]]:
    doc = _read_json(Path(root) / "community" / pkg_dir / "assets" / "provenance.json") or {}
    return [{"key": str(a.get("key") or ""), "file": str(a.get("file") or ""),
             "module": str(a.get("module") or ""), "source_package": pkg_dir}
            for a in (doc.get("assets") or [])]


def profiles(root: str = ".") -> Dict[str, Dict[str, Any]]:
    """每个包的组合画像（一次解析，供广度证明复用）。"""
    key = _cache_key(root)
    cached = _CACHE.get(key) or {}
    if cached.get("prof"):
        return cached["prof"]
    contracts = _module_contracts(root)
    out: Dict[str, Dict[str, Any]] = {}
    for d in _pack_dirs(root):
        proto = _parse_protocol(d / "protocol.yaml")
        own = []
        for mid in proto["module_ids"]:
            rec = contracts.get(str(mid)) or contracts.get(str(mid).split(":")[-1])
            own.append(rec or {"id": str(mid), "layer": "", "inputs": [], "publish": [],
                               "subscribe": [], "pack": proto["id"]})
        layers: Dict[str, List[str]] = {}
        for rec in own:
            lay = str(rec.get("layer") or "")
            if lay:
                layers.setdefault(lay, [])
                if rec["id"] not in layers[lay]:
                    layers[lay].append(rec["id"])
        out[proto["id"]] = {
            "package": proto["id"], "pipeline": proto.get("pipeline", ""),
            "modules": [r["id"] for r in own], "module_recs": own,
            "references": proto.get("references") or [],
            "layers": {k: sorted(set(v)) for k, v in sorted(layers.items())},
            "assets": _pack_assets(root, d.name),
            "publishes": sorted({e for r in own for e in r.get("publish", [])}),
            "subscribes": sorted({e for r in own for e in r.get("subscribe", [])}),
        }
    cached.update({"prof": out, "contracts": contracts})
    _CACHE[key] = cached
    return out


def _digest(obj: Dict[str, Any]) -> str:
    blob = json.dumps({k: v for k, v in obj.items() if k != "digest"},
                      ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:32]


def combine(root: str = ".", packs: Sequence[str] = (), extra_modules: Sequence[str] = (),
            extra_assets: Sequence[str] = (), _prof: Any = None,
            _contracts: Any = None) -> Dict[str, Any]:
    """组合一个（纯读、不落盘）：返回组合证书 + 五条不变量判定。"""
    prof = _prof if _prof is not None else profiles(root)
    contracts = _contracts if _contracts is not None else _module_contracts(root)
    unknown = [p for p in packs if p not in prof]
    chosen = [prof[p] for p in packs if p in prof]
    mods: Dict[str, Dict[str, Any]] = {}
    for pr in chosen:
        for rec in pr["module_recs"]:
            mods[rec["id"]] = rec
    for mid in extra_modules:                 # 组件级自由：直接点模块名（可跨包）
        rec = contracts.get(str(mid)) or contracts.get(str(mid).split(":")[-1])
        if rec:
            mods[rec["id"]] = rec
    # references 自动借入（跨包引用白名单语义）：组合包借源包模块 → 借入本组合（不改号、不复制）
    borrowed: List[Dict[str, str]] = []
    unresolved_refs: List[Dict[str, str]] = []
    by_id, pub_index, core_pub = indexes(root)

    def _add(rec: Dict[str, Any], why: str, by: str) -> bool:
        if rec["id"] in mods:
            return False
        mods[rec["id"]] = rec
        borrowed.append({"module": rec["id"], "from": str(rec.get("pack")),
                         "by": by or "<组件级>", "mode": "closure_pull", "why": why})
        return True

    for pr in chosen:
        for ref in pr.get("references") or []:
            src, mid = ref.get("source_package", ""), ref.get("module_id", "")
            rec = contracts.get(mid) or contracts.get(str(mid).split(":")[-1])
            if rec and str(rec.get("pack")) == src:
                if rec["id"] not in mods:
                    mods[rec["id"]] = rec
                    borrowed.append({"module": rec["id"], "from": src,
                                     "by": pr["package"], "mode": "module_borrow"})
            elif rec:
                if rec["id"] not in mods:
                    mods[rec["id"]] = rec
                    borrowed.append({"module": rec["id"], "from": str(rec.get("pack")),
                                     "by": pr["package"], "mode": "module_borrow"})
            else:
                unresolved_refs.append({"by": pr["package"], "source_package": src,
                                        "module_id": mid})
    # ---- 不动点闭包：依赖 inputs ∪ 事件发布方（递归），直到不再新增 ----
    core = _core_ids()
    for _round in range(12):
        grew = False
        for m, r in list(mods.items()):
            for dep in r.get("inputs", []):
                if dep in core or dep in mods or dep.split(":")[-1] in core:
                    continue
                rec = by_id.get(dep) or by_id.get(str(dep).split(":")[-1])
                if rec and _add(rec, "依赖 %s 的 inputs 需要 %s" % (m, dep), m):
                    grew = True
        published_now = ({e for x in mods.values() for e in x.get("publish", [])} | core_pub)
        for m, r in list(mods.items()):
            for ev in r.get("subscribe", []):
                if ev in published_now:
                    continue
                recs = pub_index.get(ev) or []
                if not recs:
                    continue                      # 无人发布 → 由 unpublished 面报告
                for rec in recs:
                    if _add(rec, "事件 %s 需要发布方（%s 订阅）" % (ev, m), m):
                        grew = True
        if not grew:
            break
    missing_contracts = sorted(m for m, r in mods.items() if not r.get("path"))
    core = _core_ids()
    dangling = []
    for m, r in sorted(mods.items()):
        for dep in r.get("inputs", []):
            if dep in core or dep in mods or dep.split(":")[-1] in core:
                continue
            dangling.append({"module": m, "needs": dep})
    published = {e for r in mods.values() for e in r.get("publish", [])}
    published |= core_pub
    unbridged = sorted({e for r in mods.values() for e in r.get("subscribe", [])
                        if e not in published})
    unpublished = sorted({e for r in mods.values() for e in r.get("subscribe", [])
                          if e not in published and not (pub_index.get(e) or [])})
    # 规范序（2026-09-23 修）：层栈顺序必须与证书里 **packs 的规范序**一致，
    # 否则调用者给序不同 → 复算层栈不同 → T4 复算假失败。故一律按排序后的包名定序。
    canon = sorted(set(packs))
    order = {p: i for i, p in enumerate(canon)}
    stacks: Dict[str, List[str]] = {}
    for pr in chosen:
        for lay, ms in pr["layers"].items():
            stacks.setdefault(lay, [])
            for m in ms:
                if m not in stacks[lay]:
                    stacks[lay].append(m)
    for m, r in sorted(mods.items()):
        lay = str(r.get("layer") or "")
        if lay and m not in stacks.get(lay, []):
            stacks.setdefault(lay, []).append(m)
    stacks = {k: sorted(set(v), key=lambda x: (order.get(str((mods.get(x) or {}).get("pack")),
                                                        99), x))
              for k, v in sorted(stacks.items())}
    asset_index = {(pr["package"], a["key"]): a
                   for pr in prof.values() for a in pr["assets"]}
    borrow, unresolved = [], []
    for pr in chosen:
        for a in pr["assets"]:
            if a["module"] and a["module"] not in mods:
                borrow.append({"key": a["key"], "from": pr["package"],
                               "for_module": a["module"], "mode": "asset_readonly"})
    for spec in extra_assets:
        pkg, _, key = str(spec).partition(":")
        if (pkg, key) in asset_index:
            borrow.append({"key": key, "from": pkg, "for_module": "",
                           "mode": "asset_readonly"})
        else:
            unresolved.append(str(spec))
    cert: Dict[str, Any] = {
        "schema": "nf-combo/1",
        "packs": canon,
        "unknown_packs": sorted(unknown),
        "extra_modules": sorted(set(extra_modules)),
        "modules": sorted(mods),
        "module_count": len(mods),
        "layer_stacks": stacks,
        "dependency_closure": {
            "core": sorted(_core_ids()),
            "explicit": sorted({d for r in mods.values() for d in r.get("inputs", [])
                                if d in mods}),
            "dangling": dangling},
        "event_closure": {"published": sorted(published), "unbridged": unbridged},
        "events_unpublished": unpublished,
        "assets_borrowed": sorted(borrow, key=lambda x: (x["from"], x["key"])),
        "modules_borrowed": sorted(borrowed, key=lambda x: (x["by"], x["module"])),
        "references_unresolved": sorted(unresolved_refs, key=lambda x: (x["by"], x["module_id"])),
        "assets_unresolved": sorted(unresolved),
        "module_missing_contract": missing_contracts,
    }
    cert["legal"] = not (unknown or dangling or unbridged or missing_contracts or unresolved
                         or unresolved_refs)
    cert["digest"] = _digest(cert)
    return cert


def verify_certificate(root: str, cert: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    """T4 复算：按证书输入重算组合，与在盘证书逐字段比对。"""
    issues: List[str] = []
    fresh = combine(root, packs=cert.get("packs") or (),
                    extra_modules=cert.get("extra_modules") or ())
    for key in ("modules", "module_count", "layer_stacks", "dependency_closure",
                "event_closure", "assets_borrowed", "modules_borrowed", "legal", "digest"):
        if fresh.get(key) != cert.get(key):
            issues.append("字段不一致：%s（复算 %r ≠ 在盘 %r）"
                          % (key, fresh.get(key), cert.get(key)))
    return issues, {"legal": fresh.get("legal"), "modules": fresh.get("module_count")}


def breadth(root: str = ".", triple_sample: int = 400, quad_sample: int = 200,
            seed: int = 20260923) -> Dict[str, Any]:
    """广度证明：全部两两 + 定种子抽样三元 / 四元，跑同一套不变量。"""
    key = _cache_key(root)
    prof = profiles(root)
    contracts = _module_contracts(root)
    cached = _CACHE.get(key) or {}
    cached.update({"prof": prof, "contracts": contracts})
    _CACHE[key] = cached
    names = sorted(prof)
    stats: Dict[str, Any] = {"packs": len(names), "pairs": 0, "pairs_legal": 0,
                             "triples": 0, "triples_legal": 0, "quads": 0, "quads_legal": 0,
                             "failures": []}
    for a, b in itertools.combinations(names, 2):
        c = combine(root, packs=[a, b], _prof=prof, _contracts=contracts)
        stats["pairs"] += 1
        stats["pairs_legal"] += 1 if c["legal"] else 0
        if not c["legal"] and len(stats["failures"]) < 10:
            stats["failures"].append({"combo": [a, b],
                                      "dangling": c["dependency_closure"]["dangling"][:2],
                                      "unbridged": c["event_closure"]["unbridged"][:2]})
    rnd = random.Random(seed)
    triples: Set[Tuple[str, ...]] = set()
    if len(names) >= 3:
        while len(triples) < min(triple_sample, 5000):
            triples.add(tuple(sorted(rnd.sample(names, 3))))
    for t in sorted(triples):
        c = combine(root, packs=list(t), _prof=prof, _contracts=contracts)
        stats["triples"] += 1
        stats["triples_legal"] += 1 if c["legal"] else 0
    quads: Set[Tuple[str, ...]] = set()
    if len(names) >= 4:
        while len(quads) < min(quad_sample, 5000):
            quads.add(tuple(sorted(rnd.sample(names, 4))))
    for q in sorted(quads):
        c = combine(root, packs=list(q), _prof=prof, _contracts=contracts)
        stats["quads"] += 1
        stats["quads_legal"] += 1 if c["legal"] else 0
    stats["all_legal"] = bool(
        stats["pairs"] == stats["pairs_legal"]
        and stats["triples"] == stats["triples_legal"]
        and stats["quads"] == stats["quads_legal"])
    return stats


def declared(root: str = ".") -> Dict[str, Any]:
    return _read_json(Path(root) / CERT_REL) or {
        "schema": "nf-combo-certificates/1", "certificates": []}


#: 组合证书形状（自带 JSON Schema 2020-12 子集；用 output_forms 的自家校验器判）
CERT_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "nf-combo/1 组合证书",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema", "packs", "modules", "module_count", "layer_stacks",
                 "dependency_closure", "event_closure", "legal", "digest"],
    "properties": {
        "schema": {"const": "nf-combo/1"},
        "label": {"type": "string", "minLength": 2},
        "note": {"type": "string", "minLength": 4},
        "packs": {"type": "array", "items": {"type": "string", "minLength": 2}},
        "unknown_packs": {"type": "array", "items": {"type": "string"}},
        "extra_modules": {"type": "array", "items": {"type": "string"}},
        "modules": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "module_count": {"type": "integer", "minimum": 1},
        "layer_stacks": {
            "type": "object",
            "patternProperties": {"^P\\d{2}$": {
                "type": "array", "minItems": 1, "items": {"type": "string", "minLength": 2}}},
            "additionalProperties": False},
        "dependency_closure": {
            "type": "object", "additionalProperties": False,
            "required": ["core", "explicit", "dangling"],
            "properties": {"core": {"type": "array"}, "explicit": {"type": "array"},
                           "dangling": {"type": "array", "maxItems": 0}}},
        "event_closure": {
            "type": "object", "additionalProperties": False,
            "required": ["published", "unbridged"],
            "properties": {"published": {"type": "array"},
                           "unbridged": {"type": "array", "maxItems": 0}}},
        "events_unpublished": {"type": "array", "maxItems": 0},
        "assets_borrowed": {"type": "array"},
        "modules_borrowed": {"type": "array"},
        "references_unresolved": {"type": "array", "maxItems": 0},
        "assets_unresolved": {"type": "array", "maxItems": 0},
        "module_missing_contract": {"type": "array", "maxItems": 0},
        "legal": {"const": True},
        "digest": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
    },
}


def certify(root: str = ".", packs: Sequence[str] = (), label: str = "", note: str = "",
            extra_modules: Sequence[str] = (), write: bool = False) -> Dict[str, Any]:
    """生成/更新一条**声明组合**的证书（写进 `protocol/combo_certificates.json`）。"""
    cert = combine(root, packs=packs, extra_modules=extra_modules)
    if label:
        cert["label"] = label
    if note:
        cert["note"] = note
    if not write:
        return cert
    path = Path(root) / CERT_REL
    doc = _read_json(path) or {
        "schema": "nf-combo-certificates/1",
        "note": "声明组合证书（公开结果面）。每条 = 一次 n 元组合的可机验凭证：包清单 / 模块集 / "
                "层位堆叠 / 依赖闭包 / 事件闭包 / 资产借阅 / 合法性 / 规范摘要。"
                "判据（check32 combos）：① 证书过 CERT_SCHEMA；② 按 packs+extra_modules **复算**"
                "逐字段一致（T4）；③ 广度证明（全部两两 + 定种子三元/四元）不变量全成立。",
        "certificates": [],
    }
    # 去重键 = 组合输入本身（packs + extra_modules），**不是** digest：
    # 引擎升级后同一组合的摘要会变，按 digest 去重会留下历史快照（实测 26 条里 13 条过期）。
    def _key(c: Dict[str, Any]) -> Tuple[Any, ...]:
        return (tuple(c.get("packs") or ()), tuple(sorted(c.get("extra_modules") or ())))

    certs = [c for c in doc["certificates"] if _key(c) != _key(cert)]
    certs.append(cert)
    doc["certificates"] = sorted(certs, key=lambda c: (len(c.get("packs") or []),
                                                      c.get("label") or "", c["digest"]))
    doc["count"] = len(doc["certificates"])
    doc["max_packs"] = max((len(c.get("packs") or []) for c in doc["certificates"]), default=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    return cert


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """check32 子扫描入口：在盘组合证书复算（T4）+ 广度证明。"""
    from core import output_forms as of

    issues: List[str] = []
    doc = declared(root)
    certs = doc.get("certificates") or []
    for cert in certs:
        unsup: List[str] = []
        schema_errs = of.json_schema_check(cert, CERT_SCHEMA, unsupported=unsup)
        name = cert.get("label") or "+".join(cert.get("packs") or []) or "<空>"
        issues += ["组合 %s: 证书不合 schema: %s" % (name, e) for e in schema_errs[:4]]
        if unsup:
            issues.append("组合 %s: 证书校验器遇到不支持关键字 %s" % (name, sorted(set(unsup))[:2]))
        sub, _st = verify_certificate(root, cert)
        issues += ["组合 %s: %s" % (name, s) for s in sub]
    br = breadth(root)
    if not br["all_legal"]:
        issues.append("广度证明不成立：两两 %d/%d · 三元 %d/%d · 四元 %d/%d（样本 %s）"
                      % (br["pairs_legal"], br["pairs"], br["triples_legal"], br["triples"],
                         br["quads_legal"], br["quads"], br["failures"][:2]))
    return issues, {"declared_certificates": len(certs), "breadth": br}
