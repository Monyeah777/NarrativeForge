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
    # 对外形态：**列表**（[{layer, modules}]）而非「层名做键的字典」——JSON Schema 的
    # patternProperties 需要正则键，而仓库编码卫生按标识面判键（实测 2026-09-23 冲突）；
    # 列表形态两边都干净，且层序天然显式。
    stack_list = [{"layer": k, "modules": v} for k, v in sorted(stacks.items())]
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
        "layer_stacks": stack_list,
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
            quint_sample: int = 120, sext_sample: int = 60,
            seed: int = 20260923) -> Dict[str, Any]:
    """广度证明：全部两两 + 定种子抽样三元 / 四元 / 五元 / 六元，跑同一套不变量。

    参与面 = `community/` 下全部已登记协议包（域包 + 组合包 + 既有社区包）——
    组合包带 `references`（借阅源包模块），本轮起一并进入广度抽样，验证
    「组合包本身也能当组合成员」（摊平后不变量仍成立）。
    """
    key = _cache_key(root)
    prof = profiles(root)
    contracts = _module_contracts(root)
    cached = _CACHE.get(key) or {}
    cached.update({"prof": prof, "contracts": contracts})
    _CACHE[key] = cached
    names = sorted(prof)
    stats: Dict[str, Any] = {"packs": len(names), "pairs": 0, "pairs_legal": 0,
                             "triples": 0, "triples_legal": 0, "quads": 0, "quads_legal": 0,
                             "quints": 0, "quints_legal": 0,
                             "sexts": 0, "sexts_legal": 0,
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
    for size, tag in ((5, "quints"), (6, "sexts")):
        want = min(quint_sample if size == 5 else sext_sample, 5000)
        picks: Set[Tuple[str, ...]] = set()
        if len(names) >= size:
            while len(picks) < want:
                picks.add(tuple(sorted(rnd.sample(names, size))))
        for p in sorted(picks):
            c = combine(root, packs=list(p), _prof=prof, _contracts=contracts)
            stats[tag] += 1
            stats[tag + "_legal"] += 1 if c["legal"] else 0
            if not c["legal"] and len(stats["failures"]) < 10:
                stats["failures"].append({"combo": list(p),
                                          "dangling": c["dependency_closure"]["dangling"][:2],
                                          "unbridged": c["event_closure"]["unbridged"][:2]})
    stats["all_legal"] = bool(
        stats["pairs"] == stats["pairs_legal"]
        and stats["triples"] == stats["triples_legal"]
        and stats["quads"] == stats["quads_legal"]
        and stats["quints"] == stats["quints_legal"]
        and stats["sexts"] == stats["sexts_legal"])
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
            "type": "array", "minItems": 1,
            "items": {"type": "object", "additionalProperties": False,
                      "required": ["layer", "modules"],
                      "properties": {
                          "layer": {"type": "string", "minLength": 3},
                          "modules": {"type": "array", "minItems": 1,
                                      "items": {"type": "string", "minLength": 2}}}}},
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


# ---------------------------------------------------------------- 组合包产物化

def _flatten_sources(root: str, packs: Sequence[str]) -> Tuple[Dict[str, List[str]], List[str]]:
    """把选中包摊平成 {源包名: [模块 id…]}（组合包本身再展开一层，避免多层嵌套 references）。"""
    prof = profiles(root)
    out: Dict[str, List[str]] = {}
    combo_packs: List[str] = []
    for name in packs:
        pr = prof.get(name)
        if not pr:
            continue
        if pr.get("references"):
            # 组合包作为来源 → **显式摊平**：保留它自己的模块（它们是真实模块，且是其它源包
            # 发布事件的消费者），同时把它的 references 一并升为本次组合的 references ——
            # 这样嵌套引用是「显式闭合」的（check15 ② 新增判据：嵌套必须显式闭合）。
            combo_packs.append(name)
        out.setdefault(name, [])
        for mid in pr["modules"]:
            if mid not in out[name]:
                out[name].append(mid)
        for ref in pr.get("references") or []:
            src = str(ref.get("source_package") or "")
            if not src:
                continue
            out.setdefault(src, [])
            mid = str(ref.get("module_id") or "")
            if mid and mid not in out[src]:
                out[src].append(mid)
    return out, combo_packs


def _yaml_kv(items: List[Tuple[str, str]], indent: int = 2) -> List[str]:
    pad = " " * indent
    return ["%s%s: %s" % (pad, k, v) for k, v in items]


def materialize(root: str = ".", packs: Sequence[str] = (), combo_id: str = "",
                category: str = "", write: bool = False) -> Dict[str, Any]:
    """把一次组合落成**可装载的组合包**（派生协议 + 派生管线 + 借阅索引 + 机验产出面）。

    设计（守既有关禁）：
    - 组合包**不新增模块**（module_id_range/modules 均空）；全部模块经 `references` 只读借阅
      → check15 ①②④⑤ 可过，且避免多层组合（组合包自身的引用被**摊平**成源包直引）；
    - 层位堆叠写进 `available`（**default 留空**）→ 规避 check15 ③「同层 default 冲突」；
    - 派生管线沿用 P00 九层骨架，`allowed_modules` = 官方核心 ∪ 借阅模块；
    - 产出面含 **T4 证书**（由 pack_combo 重算）与图表/图结构，全部 ≥T2。
    """
    cert = combine(root, packs=packs)
    if not cert["legal"]:
        return {"ok": False, "reason": "组合非法（先修五不变量）", "certificate": cert}
    prof = profiles(root)
    src_map, combo_packs = _flatten_sources(root, packs)
    own = sorted({m for ms in src_map.values() for m in ms})
    if not own:
        return {"ok": False, "reason": "空组合（无借阅模块）", "certificate": cert}
    name = combo_id or ("组合包-" + "-".join(packs[:2]))
    if not re.fullmatch(r"[\u4e00-\u9fffA-Za-z0-9_\-]{2,40}", name):
        return {"ok": False, "reason": "组合包名不合形：%r" % name}
    cat = category or ("组合域-%s" % name.replace("组合包-", ""))
    # 管线 id：三级池里取未占用
    used = set()
    reg = _read_json(Path(root) / "desktop/src/core/registry.json") or {}
    used |= {str(p.get("pipeline")) for p in reg.get("protocols") or []}
    # 幂等：本组合包若已存在（protocol.yaml 有合形管线号）→ 复用，不再重新分配
    # （实测 2026-09-23：重复 materialize 会把 P108 换成 P109，产生无谓 churn 与陈旧管线文件）
    pid = ""
    existing = Path(root) / "community" / name / "protocol.yaml"
    if existing.is_file():
        m = re.search(r"(?m)^\s*pipeline:\s*(P\d{2,3})\s*$", existing.read_text(encoding="utf-8"))
        if m:
            pid = m.group(1)
    if not pid:
        pid = next((x for x in ["P%03d" % i for i in range(100, 200)] if x not in used), "")
    if not pid:
        return {"ok": False, "reason": "管线 id 池已用尽", "certificate": cert}
    layers: Dict[str, List[str]] = {}
    for m in cert["modules"]:
        rec = prof_get_module(root, m)
        lay = str(rec.get("layer") or "P40")
        layers.setdefault(lay, [])
        if m not in layers[lay]:
            layers[lay].append(m)
    pkg_dir = Path(root) / "community" / name
    files: Dict[str, str] = {}
    refs = [(sp, ms) for sp, ms in sorted(src_map.items()) if ms]
    proto = [
        "# protocol.yaml — 组合包协议声明（组合引擎产物化：%s）" % name,
        "# 由 `nf combine materialize` 生成；机读真相 = 本文件，人读速览 = README.md（双源一致）",
        "protocol:",
        '  schema_version: "2"',
        "package:",
        '  conformance: "L2"',
        "  id: %s" % name,
        "  name: %s" % name,
        '  version: "1.0.0"',
        "  pipeline: %s" % pid,
        "  module_id_range: []          # 组合包不新增模块（全部经 references 只读借阅）",
        "  categories:",
        "    - %s" % cat,
        "  dependencies:",
        "    core_only: true",
        "    core_modules: [%s]" % ", ".join(CORE13),
        "    cross_package: []",
        "  references:",
    ]
    for sp, ms in refs:
        for m in ms:
            proto += ["    - source_package: %s" % sp,
                      "      module_id: %s" % m,
                      '      source_schema_version: "2"',
                      "      asset_readonly: true"]
    proto += ["  modules: []", "  assets:",
              "    count: 0",
              "    readme: README.md",
              "  mount_layers:          # 堆叠写入 available（default 留空，规避同层 default 冲突）"]
    for lay, ms in sorted(layers.items()):
        proto.append("    %s: {default: [], available: [%s]}" % (lay, ", ".join(ms)))
    files["community/%s/protocol.yaml" % name] = "\n".join(proto) + "\n"
    files["community/%s/README.md" % name] = combo_readme(name, packs, cert, refs, layers, pid)
    files["community/%s/assets/README.md" % name] = combo_assets_readme(refs, layers)
    files["community/%s/pipelines/%s_%s装配流管线.md" % (name, pid, name)] = combo_pipeline(
        name, pid, layers, cert)
    files.update(combo_outputs(root, name, cert, layers))
    written, changed = [], []
    for f in sorted((pkg_dir / "pipelines").glob("*.md")) if (pkg_dir / "pipelines").is_dir() else []:
        tok = f.name.split("_")[0]
        if re.fullmatch(r"P\d{2,3}", tok) and tok != pid:
            f.unlink()                        # 陈旧管线（改号残留）
    for rel, text in sorted(files.items()):
        p = Path(root) / rel
        if p.is_file() and p.read_bytes() == text.encode("utf-8"):
            continue
        changed.append(rel)
        if write:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8", newline="\n")
            written.append(rel)
    return {"ok": True, "package": name, "pipeline": pid, "category": cat,
            "references": sum(len(ms) for _, ms in refs), "modules": len(own),
            "layers": {k: len(v) for k, v in sorted(layers.items())},
            "files": len(files), "changed": len(changed), "written": len(written),
            "combo_packs_flattened": combo_packs, "certificate": cert}


def prof_get_module(root: str, module_id: str) -> Dict[str, Any]:
    by_id, _pi, _cp = indexes(root)
    return by_id.get(module_id) or by_id.get(str(module_id).split(":")[-1]) or {}


def combo_readme(name: str, packs: Sequence[str], cert: Dict[str, Any],
                 refs: Sequence[Tuple[str, List[str]]], layers: Dict[str, List[str]],
                 pid: str) -> str:
    lines = [
        "# %s（组合包 · 由组合引擎产物化）" % name,
        "> 定位：**自由组合包**——由 `nf combine materialize` 从 %d 个域包组合而成；" % len(packs),
        "> 组合包**不新增内容资产**，全部模块经 `references` **只读借阅**（源包模块不改号、资产不复制）。",
        "> 唯一机读真相 = `protocol.yaml`；本 README 为人读速览（双源一致由 check14 ⑥ 断言）。",
        "> 管线：**%s** %s装配流（派生自 P00 九层骨架）｜借阅模块 **%d** 个｜产出面 8 件（含 T4 证书）"
        % (pid, name, cert["module_count"]),
        "",
        "## 1. 组合构成",
        "",
        "| 源包 | 借阅模块 |",
        "|---|---|",
    ]
    for sp, ms in refs:
        lines.append("| %s | %s |" % (sp, "、".join("`%s`" % m for m in ms)))
    lines += ["", "## 2. 层位堆叠（available 槽）", "", "| 层 | 模块（堆叠序） |", "|---|---|"]
    for lay, ms in sorted(layers.items()):
        lines.append("| %s | %s |" % (lay, "、".join("`%s`" % m for m in ms)))
    lines += [
        "",
        "## 3. 复现与验收",
        "",
        "```",
        "python scripts/nf.py combine plan --packs \"%s\"" % ",".join(packs),
        "python scripts/nf.py combine verify",
        "python scripts/nf.py output verify",
        "```",
        "",
        "## 4. 边界",
        "",
        "- 组合包**不改源包**：借阅只读；组合不产生新内容资产。",
        "- 合法性与可复算性由组合证书（`outputs/COMBO_CERT.json`）与五不变量保证；",
        "  内容质量仍由各源包口径与 T4 面承担。",
    ]
    return "\n".join(lines) + "\n"


def combo_assets_readme(refs: Sequence[Tuple[str, List[str]]],
                        layers: Dict[str, List[str]]) -> str:
    lines = ["<!-- ai-index: borrow-only -->",
             "# 借阅索引（本包无自有内容资产）",
             "",
             "> 本组合包 `assets.count = 0`：不复制任何源包资产；下表是**借阅来源**清单，"
             "运行时经 `asset_get` 只读访问源包资产（`asset_readonly: true`）。",
             "",
             "| 源包 | 借阅模块 | 源包资产键 |",
             "|---|---|---|"]
    for sp, ms in refs:
        lines.append("| %s | %s | 见源包 `assets/provenance.json` |" % (sp, "、".join(ms)))
    return "\n".join(lines) + "\n"


def combo_pipeline(name: str, pid: str, layers: Dict[str, List[str]],
                   cert: Dict[str, Any]) -> str:
    order = ["P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80"]
    lname = {"P00": "数据基座", "P10": "世界推进", "P20": "角色状态", "P30": "事件生产",
             "P40": "行为决策", "P50": "交互执行", "P60": "长期演变", "P70": "叙事素材",
             "P80": "输出呈现"}
    core_allow = {"P00": ["M00"], "P10": ["通用:M10"], "P20": ["M23"], "P30": ["事件:M22", "M06", "M13"],
                  "P50": ["M12"], "P70": ["M20", "M24"], "P80": ["M80"]}
    lines = [
        "# 管线 %s · %s装配流（组合包派生）" % (pid, name),
        "",
        "> 由组合引擎产物化：九层位名沿用 P00 骨架；`allowed_modules` = 官方核心承载件 ∪ "
        "本组合**借阅**模块（写在各层 `available`）；组合包不新增模块。",
        "> 组合合法性、层栈与闭包结果见 `outputs/COMBO_CERT.json`（T4：由 `nf combine verify` 重算）。",
        "```yaml",
        "Pipeline:",
        "  id: %s" % pid,
        "  name: %s装配流" % name,
        "  structure:",
        "    type: linear",
        "    flow:",
    ]
    for i, lay in enumerate(order):
        nxt = order[i + 1] if i + 1 < len(order) else "P00"
        lines += ["      - from: %s" % lay, "        to: %s" % nxt]
    lines.append("  layers:")
    for lay in order:
        borrow = layers.get(lay) or []
        allow = sorted(set(core_allow.get(lay, [])) | set(borrow))
        lines += [
            "    - id: %s" % lay,
            "      name: %s" % lname[lay],
            "      description: %s" % (("借阅模块堆叠：" + "、".join(borrow)) if borrow
                                      else "由官方核心承载（%s）" % "/".join(core_allow.get(lay, []))),
            "      optional: false",
            "      default_modules: []",
            "      allowed_modules: [%s]" % ", ".join(allow),
        ]
    lines += ["```", "",
              "## 说明",
              "",
              "- 本管线是**组合实例**：层位 default 全空，借阅模块入 available（不改源包挂载）。",
              "- 生成命令：`nf combine materialize --packs \"%s\" --write`。" % "、".join(cert["packs"])]
    return "\n".join(lines) + "\n"


def combo_outputs(root: str, name: str, cert: Dict[str, Any],
                  layers: Dict[str, List[str]]) -> Dict[str, str]:
    """组合包的机验产出面（8 件）：证书（T4）+ 契约 + 数据 + 图表 + 图示 + 系统卡。"""
    pkg = "community/%s" % name
    import json as _json

    cert_doc = dict(cert)
    cert_doc["label"] = cert_doc.get("label") or ("组合包 %s" % name)
    cert_doc["note"] = cert_doc.get("note") or ("由 nf combine materialize 产物化；"
                                                "组合合法性由五不变量给出")
    params = {"packs": cert["packs"], "extra_modules": cert.get("extra_modules") or [],
              "label": cert_doc["label"], "note": cert_doc["note"]}
    borrow = {}
    for m in cert["modules"]:
        rec = prof_get_module(root, m)
        borrow.setdefault(str(rec.get("pack") or ""), []).append(m)
    borrow_doc = {"schema": "nf-combo-borrow/1",
                  "package": name,
                  "note": "借阅索引：本组合包不复制资产/模块，全部经 references 只读访问",
                  "borrowed": [{"source_package": k, "modules": sorted(v),
                                "mode": "asset_readonly"}
                               for k, v in sorted(borrow.items())]}
    index = {
        "schema": "nf-output-index/1",
        "package": name,
        "note": "组合包产出面（由组合引擎生成；check32 output_forms 与 nf output 按此判定）。",
        "outputs": [
            {"path": "outputs/schemas/COMBO_CERT.schema.json", "form": "json-schema",
             "tier": "T2", "role": "schema", "note": "组合证书契约"},
            {"path": "outputs/COMBO_CERT.json", "form": "combo-cert", "tier": "T4",
             "role": "functional", "schema": "outputs/schemas/COMBO_CERT.schema.json",
             "recompute": {"id": "combo-cert", "params": params},
             "note": "组合证书（T4：按 packs+extra_modules 重算逐字段比对）"},
            {"path": "outputs/schemas/BORROW_INDEX.schema.json", "form": "json-schema",
             "tier": "T2", "role": "schema", "note": "借阅索引契约"},
            {"path": "outputs/BORROW_INDEX.json", "form": "json", "tier": "T2",
             "role": "data", "schema": "outputs/schemas/BORROW_INDEX.schema.json",
             "note": "借阅索引（源包 → 模块，只读）"},
            {"path": "outputs/charts/LAYER_STACK.vega.json", "form": "vega-lite",
             "tier": "T3", "role": "chart",
             "render": {"id": "vega-layer-stack", "inputs": ["outputs/COMBO_CERT.json"],
                        "params": {"title": "%s · 层位堆叠" % name}},
             "note": "层位堆叠条形图（由证书确定性生成）"},
            {"path": "outputs/charts/LOAD_ORDER.mmd", "form": "mermaid", "tier": "T3",
             "role": "diagram",
             "render": {"id": "mermaid-layer-load", "inputs": ["outputs/COMBO_CERT.json"]},
             "note": "装载序图（按层分组的 Mermaid）"},
            {"path": "outputs/DEPENDENCY.graphml", "form": "graphml", "tier": "T3",
             "role": "diagram",
             "render": {"id": "graphml-module-deps", "inputs": ["outputs/COMBO_CERT.json"]},
             "note": "模块依赖图（GraphML；端点引用完整性由形态校验器判定）"},
            {"path": "outputs/SYSTEM_CARD.json", "form": "system-card", "tier": "T3",
             "role": "data", "schema": "outputs/schemas/SYSTEM_CARD.schema.json",
             "note": "组合包系统卡（用途 / 限制 / 借阅边界 / 不宣称）"},
        ],
    }
    from core import domain_pack as dpk

    card = {
        "kind": "nf-system-card/1",
        "system": {"id": "NF-COMBO-%s" % re.sub(r"[^A-Za-z0-9]", "-", name)[:20].upper(),
                   "name": name, "version": "1.0.0",
                   "kind_of_system": "domain-package", "model_agnostic": True},
        "intended_use": {
            "purpose": "把 %d 个域包按声明组合成一个可装载装配单元：层位堆叠、依赖与事件闭包、"
                       "只读借阅全部由组合证书机验。" % len(cert["packs"]),
            "consumers": ["装配运行时（%s）" % cert.get("pipeline", ""), "组合调用方"],
            "in_scope": ["组合合法性（五不变量）", "层位堆叠与装载序", "只读借阅索引"]},
        "limitations": [
            "组合包不改源包：借阅只读，模块不改号、资产不复制",
            "组合只保证结构合法与可复算，不保证组合内容的领域质量",
            "广度证明为两两全集 + 定种子抽样，非 2^N 全枚举",
        ],
        "data": {"sources": [{"id": "COMBO_CERT", "kind": "generated",
                              "note": "证书由组合引擎确定性生成并可复算"}],
                 "provenance_policy": "源包资产经 references 只读借阅；组合不新增内容资产",
                 "personal_data": "none"},
        "evaluation": {"method": "组合五不变量 + 证书 T4 复算 + check32 combos 子扫描",
                       "faces": [{"name": "组合合法性", "gate": "check32 combos",
                                  "result": "五不变量全成立"}],
                       "reproduce_command": "python scripts/nf.py combine verify",
                       "not_measured": ["组合内容质量", "高阶组合的全枚举"]},
        "human_oversight": ["组合声明变更须重跑 materialize 与门禁", "借阅边界由 references 白名单控制"],
        "risk_management": {"framework": "NIST AI RMF 1.0",
                            "functions": {"GOVERN": ["借阅白名单可审计"],
                                          "MAP": ["组合构成表（源包 → 模块）"],
                                          "MEASURE": ["证书 T4 复算 + 广度证明"],
                                          "MANAGE": ["组合非法即拒（fail-closed）"]},
                            "residual_risks": ["抽样广度非全枚举", "源包演进会使组合证书过期（须重签）"]},
        "out_of_scope": ["新增内容资产", "替代源包职责"],
        "not_claims": ["不宣称组合内容质量", "不宣称已穷举所有高阶组合",
                       "不宣称组合包等价于任何源包"],
    }
    return {
        "%s/outputs/INDEX.json" % pkg: _json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        "%s/outputs/COMBO_CERT.json" % pkg: _json.dumps(cert_doc, ensure_ascii=False,
                                                       indent=2, sort_keys=True) + "\n",
        "%s/outputs/schemas/COMBO_CERT.schema.json" % pkg:
            _json.dumps(CERT_SCHEMA, ensure_ascii=False, indent=2) + "\n",
        "%s/outputs/BORROW_INDEX.json" % pkg:
            _json.dumps(borrow_doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "%s/outputs/schemas/BORROW_INDEX.schema.json" % pkg:
            _json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "组合包借阅索引",
                "type": "object", "additionalProperties": False,
                "required": ["schema", "package", "borrowed"],
                "properties": {"schema": {"const": "nf-combo-borrow/1"},
                               "package": {"type": "string", "minLength": 2},
                               "note": {"type": "string"},
                               "borrowed": {"type": "array", "minItems": 1, "items": {
                                   "type": "object", "additionalProperties": False,
                                   "required": ["source_package", "modules", "mode"],
                                   "properties": {
                                       "source_package": {"type": "string", "minLength": 2},
                                       "modules": {"type": "array", "minItems": 1,
                                                   "items": {"type": "string", "minLength": 2}},
                                       "mode": {"const": "asset_readonly"}}}}},
            }, ensure_ascii=False, indent=2) + "\n",
        "%s/outputs/schemas/SYSTEM_CARD.schema.json" % pkg:
            _json.dumps(dpk.SYSTEM_CARD_SCHEMA_JSON, ensure_ascii=False, indent=2) + "\n",
        "%s/outputs/SYSTEM_CARD.json" % pkg:
            _json.dumps(card, ensure_ascii=False, indent=2) + "\n",
    }


def combo_register(root: str, name: str, category: str, pipeline: str,
                   packages: Sequence[str], refs: int, cert: Dict[str, Any]) -> Dict[str, Any]:
    """登记组合包（三要件）：02 §8 段（**模块（0）**）+ verify.sh DOMAIN + registry protocols[]。

    组合包不走 `domain_pack._append_section02`（那条路径假设自有 2 模块 → 空 module_ids 会 IndexError，
    实测 2026-09-23），这里给组合专用段。
    """
    from core import domain_pack as dpk

    doc_path = Path(root) / dpk.DOC02_REL
    text = doc_path.read_text(encoding="utf-8")
    did02 = False
    if "%s（community/%s/）" % (name, name) not in text:
        m = re.search(r"(?m)^## 9\.", text)
        nums = [int(x) for x in re.findall(r"(?m)^### 8\.(\d+) ", text)]
        nxt = (max(nums) + 1) if nums else 1
        seg = "\n".join([
            "### 8.%d %s（community/%s/）" % (nxt, name, name),
            "> **定位**：**组合包**（组合引擎产物化）——由 %d 个域包组合而成；"
            "**不新增模块、不新增内容资产**，全部模块经 `references` 只读借阅"
            "（源包模块不改号、资产不复制）。独占类别：%s（R2）。" % (len(packages), category),
            "- 管线：%s %s装配流（pipelines/%s_%s装配流管线.md；九层位骨架同 P00，"
            "层位 default 全空、借阅模块入 available——规避 check15 ③ 同层 default 冲突）"
            % (pipeline, name, pipeline, name),
            "- 模块（0）：组合包不新增模块；借阅模块 %d 个（%d 条 references，asset_readonly）"
            % (cert["module_count"], refs),
            "- 资产（0 内容文件 + README.md）：assets/README.md 为**借阅索引**（非内容资产，"
            "count = 0，与既有无资产包同为合法形态）",
            "- 产出面（8 机验件）：outputs/ 下 schema 3 / 数据 2 / 图表 1 / 图示 2，"
            "含 **T4 组合证书**（`outputs/COMBO_CERT.json`，由 `nf combine verify` 重算比对）",
            "- 合法性：组合五不变量（模块可定位 / 依赖闭合 / 事件闭合 / 层位堆叠确定 / 资产可寻址）"
            "＋ 广度证明（全部两两 + 定种子抽样）——见 docs/combos.md 与 AUD-0020",
            "",
        ])
        text = text[:m.start()] + seg + text[m.start():]
        dpk._write_text_retry(doc_path, text)
        did02 = True
    spec_like = {"code": "COMBO", "name": name, "pack_name": name, "category": category}
    did_dom = dpk._append_domain_list(root, spec_like)
    reg_msg = dpk._register_protocols(root, spec_like,
                                      {"pipeline": pipeline, "module_ids": [],
                                       "exist": True})
    return {"section02": did02, "domain_list": did_dom, "protocols": reg_msg}


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
        issues.append("广度证明不成立：两两 %d/%d · 三元 %d/%d · 四元 %d/%d · 五元 %d/%d · "
                      "六元 %d/%d（样本 %s）"
                      % (br["pairs_legal"], br["pairs"], br["triples_legal"], br["triples"],
                         br["quads_legal"], br["quads"], br["quints_legal"], br["quints"],
                         br["sexts_legal"], br["sexts"], br["failures"][:2]))
    return issues, {"declared_certificates": len(certs), "breadth": br}
