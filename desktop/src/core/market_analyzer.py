"""市场协议分析库（v2.1.0-B4：依赖闭包 + 挂载冲突判据，verify check15 ②③ 同构）。

B4 CLI/库先行：把 verify.sh check15 ②③ 判据（依赖闭包无环/叶⊆官方13 + 挂载层
default 交集冲突）提为可 import 纯函数——登记前可查（门禁前移），future GUI 市场
视图解冻时即其库层。

- 判据与 verify.sh check15 ②③ 同构（非同一实例）——语义锚定由 test_market_analyzer
  真实 4 包零 issue + verify PASS 集成自证。
- 非目标：不改 verify.sh 门禁；不做包版本/上架规则（GUI 解冻后立项）。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

#: 官方核心 13 件（对齐 verify check14/check15 硬编码 + 01 §6 官方核心）
OFFICIAL13: List[str] = [
    "M00", "通用:M10", "M08", "M23", "M24", "M50", "M80",
    "事件:M22", "M06", "M12", "M13", "M20", "M90",
]

#: 质量分级（v2.4.0 A6：模块/包分级徽章——官方核心 / 社区 / 实验）
GRADE_OFFICIAL = "official"
GRADE_COMMUNITY = "community"
GRADE_EXPERIMENTAL = "experimental"
VALID_GRADES = (GRADE_OFFICIAL, GRADE_COMMUNITY, GRADE_EXPERIMENTAL)

#: M91-M99 社区预留段（02 §8 编号规则：第三方段，实验级默认）
_EXPERIMENTAL_NUMS = {"M91", "M92", "M93", "M94", "M95", "M96", "M97", "M98", "M99"}


def _norm_num(mid: Any) -> str:
    """模块 id 裸号（M55 / 情感:M55 → M55）。"""
    return str(mid).split(":")[-1]


def grade_of_module(module_id: str) -> str:
    """模块质量分级（A6）：官方核心 13 件 → official；M91-M99 段 → experimental；
    其余（社区自带模块）→ community。

    官方判定匹配**完整 id**（含前缀，如 事件:M22 官方 vs 情感:M22 社区重号段——
    裸号 M22 无法区分，必须比完整 id）；M91-M99 段按裸号（该段全局唯一）。
    """
    mid = str(module_id)
    # 官方核心 13 件完整 id 命中（含前缀，防 M22 重号段误判）
    if mid in set(OFFICIAL13):
        return GRADE_OFFICIAL
    n = _norm_num(mid)
    if n in _EXPERIMENTAL_NUMS:
        return GRADE_EXPERIMENTAL
    return GRADE_COMMUNITY


def grades_of_package(prots: Dict[str, Dict[str, Any]], pkg_id: str) -> Dict[str, str]:
    """包内各 module_id → grade 映射（A6 查询，供 nf market 徽章输出）。"""
    entry = prots.get(pkg_id) or {}
    out: Dict[str, str] = {}
    for mid in entry.get("module_ids") or []:
        out[str(mid)] = grade_of_module(str(mid))
    return out


def package_grade(prots: Dict[str, Dict[str, Any]], pkg_id: str) -> str:
    """包级分级（v2.5.0 Wave3）：模块全 experimental → experimental；
    否则 community（官方核心不在 protocols[]，由 list_market 单列）。"""
    grades = grades_of_package(prots, pkg_id)
    if not grades:
        return GRADE_COMMUNITY
    if all(g == GRADE_EXPERIMENTAL for g in grades.values()):
        return GRADE_EXPERIMENTAL
    return GRADE_COMMUNITY


def list_market(reg: Any, tier: Optional[str] = None) -> List[dict]:
    """市场目录（v2.5.0 Wave3）：官方核心 13 件 + community 包，各带 grade。

    tier 筛选（official/community/experimental）；None 返回全量。
    消费 35-A6 grade_of_module 分级字段做目录视图（C-a 消费方兑现）。
    """
    out: List[dict] = []
    # 官方核心（registry modules[] 13 件 → official）
    for m in (reg.modules or []):
        out.append({"kind": "module", "id": m.get("id"), "name": m.get("name"),
                    "grade": GRADE_OFFICIAL})
    # 社区包（registry protocols[] → community/experimental）
    prots = {p.get("id"): p for p in (reg.protocols or []) if p.get("id")}
    for p in (reg.protocols or []):
        pid = p.get("id")
        if not pid:
            continue
        out.append({"kind": "package", "id": pid, "name": p.get("name", pid),
                    "grade": package_grade(prots, pid),
                    "version": str(p.get("version") or "1.0.0"),
                    "modules": len(p.get("module_ids") or [])})
    if tier:
        out = [x for x in out if x["grade"] == tier]
    return out


def layer_key(key: Any) -> str:
    """挂载层键归一：protocol 长键（'P40 行为决策'）→ Pxx 短键（同 check15 ③）。"""
    s = str(key)
    return s.split()[0] if s.split() else s


def _pkg_deps(data: Dict[str, Any], pkg_id: str) -> Dict[str, Any]:
    """取包 protocol.yaml 的 package.dependencies（缺省空 dict，异常不抛）。"""
    raw = data.get(pkg_id) or {}
    pkg = raw.get("package") if isinstance(raw, dict) else None
    deps = pkg.get("dependencies") if isinstance(pkg, dict) else None
    return deps if isinstance(deps, dict) else {}


def _pkg_ml(data: Dict[str, Any], pkg_id: str) -> Dict[str, Any]:
    """取包 mount_layers（长键 → dict 值，未归一）。"""
    raw = data.get(pkg_id) or {}
    pkg = raw.get("package") if isinstance(raw, dict) else None
    ml = pkg.get("mount_layers") if isinstance(pkg, dict) else None
    return ml if isinstance(ml, dict) else {}


def _pkg_raw(data: Dict[str, Any], pkg_id: str) -> Dict[str, Any]:
    """取包完整 protocol.yaml dict（含 package 层，供 references 层级访问）。"""
    raw = data.get(pkg_id) or {}
    pkg = raw.get("package") if isinstance(raw, dict) else None
    return pkg if isinstance(pkg, dict) else {}


def dependencies(pkg_id: str,
                 prots: Dict[str, Dict[str, Any]],
                 data: Dict[str, Dict[str, Any]]) -> Tuple[set, List[str]]:
    """以 references 为起点沿源包 core_modules 递归展开依赖闭包（verify check15 ② 同构）。

    - seen：已访问源包 id 集（不含根 pkg_id 自身）；
    - issues：空 = 通过；命中 = 源包不可读 / 叶节点越界官方 13 /
      源包嵌套 references（多层组合不支持，须闭合官方核心）。
    注：源包嵌套检查取 **package 层 references**（protocol.yaml 中 references 与
    dependencies 平级）。verify.sh check15 ② 误取 dependencies.references 恒空
    （死检查）——本库按真实层级修正，差异记入交付报告与 ROADMAP 待修项。
    """
    issues: List[str] = []
    entry = prots.get(pkg_id) or {}
    refs = list(entry.get("references") or [])
    stack: List[Tuple[str, List[str]]] = []
    for r in refs:
        sp = r.get("source_package")
        if not sp:
            continue
        if sp not in data:
            issues.append(f"依赖闭包源包不可读: {sp}")
            continue
        stack.append((sp, list(_pkg_deps(data, sp).get("core_modules") or [])))

    seen: set = set()
    while stack:
        sp, cms = stack.pop()
        if sp in seen:
            issues.append(f"依赖闭包成环: {sp}")
            continue
        seen.add(sp)
        for x in cms:
            if x not in OFFICIAL13:
                issues.append(f"依赖闭包叶节点越界官方核心 13 件: {x}（源包 {sp} core_modules）")
        # 源包嵌套 references（package 层真实判据；verify 误取 dependencies 层恒空）
        if _pkg_raw(data, sp).get("references"):
            issues.append(f"依赖闭包检测到源包嵌套 references: {sp}（当前不支持多层组合）")
    return seen, issues


def conflicts(pkg_id: str,
              prots: Dict[str, Dict[str, Any]],
              data: Dict[str, Dict[str, Any]]) -> List[str]:
    """组合包 mount_layers 各层 default 与源包同层 default 交集非空即冲突。

    键归一（P40 行为决策 → P40）后逐层比 default——同 check15 ③ 判据。
    """
    issues: List[str] = []
    entry = prots.get(pkg_id) or {}
    refs = list(entry.get("references") or [])
    pkg_ml = _pkg_ml(data, pkg_id)
    for r in refs:
        sp = r.get("source_package")
        if not sp or sp not in data:
            continue
        sp_ml = _pkg_ml(data, sp)
        for raw_key, spec in pkg_ml.items():
            if not isinstance(spec, dict):
                continue
            key = layer_key(raw_key)
            sp_spec = None
            for lk, ls in sp_ml.items():
                if layer_key(lk) == key or str(lk) == key:
                    sp_spec = ls
                    break
            if not isinstance(sp_spec, dict):
                continue
            inter = set(spec.get("default") or []) & set(sp_spec.get("default") or [])
            if inter:
                issues.append(
                    f"挂载层 {key} default 冲突: {pkg_id}∩{sp}={sorted(inter)}")
    return issues


def related_of(target: str, prots: Dict[str, Dict[str, Any]],
               module_graph: Optional[Dict[str, set]] = None,
               owner_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """C4 See-Also：图书馆/市场条目的人读关联层（41 波C C4）。

    以 registry protocols[] 为图：目标 = 包 id 或模块 id → 返回
    ① references.source_package 关联源包（目标包引用了谁）；
    ② 反向引用方（谁引用了目标包/包含目标模块的包）；
    ③ 相关模块互见（反向引用方与目标包共享的模块视野）。
    module_graph/owner_map（可选）注入模块级依赖（machine_contract inputs →
    官方核心 / 归属包），使 techdoc↔官方核心 之类跨层互见可人读暴露。
    references/who-refers 机读基底不变，本函数只做人读暴露（不新增图数据）。
    """
    pkgs = {}
    for pid, p in prots.items():
        if isinstance(p, dict) and p.get("module_ids") is not None:
            pkgs[pid] = p
    mod2pkgs = {}
    for pid, p in pkgs.items():
        for m in p.get("module_ids") or []:
            mod2pkgs.setdefault(m, set()).add(pid)

    def _refs_of(pid: str) -> set:
        return {r.get("source_package") for r in (pkgs[pid].get("references") or [])
                if r.get("source_package")}

    pkg_modules = {pid: set(p.get("module_ids") or []) for pid, p in pkgs.items()}
    graph = module_graph or {}
    owner = owner_map or {}

    def _owner_label(mid: str) -> str:
        return owner.get(mid, "官方核心")

    refs = set()
    referenced_by = set()
    related_modules = set()
    kind = "package"
    if target in pkgs:
        refs = _refs_of(target)
        own = pkg_modules[target]
        deps = set()
        for m in own:
            deps |= set(graph.get(m) or [])
        deps -= own
        refs |= {_owner_label(m) for m in deps}
        related_modules |= deps
        for pid in pkgs:
            if pid == target:
                continue
            shared = pkg_modules[pid] & own
            dep_hit = any(set(graph.get(m) or []) & own for m in pkg_modules[pid])
            if target in _refs_of(pid) or dep_hit or shared:
                referenced_by.add(pid)
                related_modules |= pkg_modules[pid]
    else:
        kind = "module"
        owners = mod2pkgs.get(target, set())
        deps = set(graph.get(target) or [])
        refs |= {_owner_label(m) for m in deps}
        related_modules |= deps
        for pid in owners:
            refs |= _refs_of(pid)
        for pid in pkgs:
            if pid in owners:
                continue
            dep_hit = any(target in set(graph.get(m) or []) for m in pkg_modules[pid])
            if target in pkg_modules[pid] or dep_hit:
                referenced_by.add(pid)
                related_modules |= pkg_modules[pid]
        if not related_modules and owners:
            related_modules = owners
    return {
        "kind": kind,
        "target": target,
        "refs": sorted(refs - {target}),
        "referenced_by": sorted(referenced_by),
        "related_modules": sorted(related_modules),
    }
