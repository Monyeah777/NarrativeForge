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
