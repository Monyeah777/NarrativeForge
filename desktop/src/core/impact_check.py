"""registry 变更影响面检查库（v2.2.0 A4：registry 引用图闭合门禁 + 反查影响面）。

verify.sh check15 ① 验证 references 可寻址——但它的数据源是 community/*/protocol.yaml，
需 PyYAML 与 community 目录在场；两条件任一缺失即降级为 references 键文本粗校验
（不 FAIL），registry 内部悬空引用漏检。A4 补此空白：

- **registry 自洽（check21 承载）**：直接以 registry.json（装配/寻址消费真源）为
  起点做纯 JSON 引用图闭合断言——无 PyYAML / community 目录依赖，无降级：
    ① 每条 references.source_package 必须在 registry protocols[] 在册；
    ② references.module_id（裸号归一）必须在源包 module_ids（裸号归一）在列；
    ③ 包内 module_ids 无裸号重复（寻址歧义：同包同号段多登记 = 引用不唯一）。
- **变更影响面（nf 前置可选）**：registry 字段变更前查引用方——给定拟删除的
  module_id / protocol id，列出引用它的 protocol（registry references 反查），
  破坏性变更先见影响清单再落盘。

非目标：不做依赖闭包（check15 ② / market_analyzer.dependencies 已承载）；不做
02 文档↔registry 双源比对（check14 ⑦ / check15 ⑤ 已承载）；不改 verify.sh 门禁
既有断言——本库与 verify check21 同构接线。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _norm(mid) -> str:
    """模块 id 裸号归一：'情感类:M55'/'情感:M55'/'M55' → 'M55'。

    同 verify check15 ① 判据（mid.split(':',1)[-1]）——references.module_id 与
    module_ids 条目可能带短前缀（情感:M22，重号段限定）或裸号（M55，独占段），
    归属比对须剥前缀取裸号。
    """
    return str(mid).split(":", 1)[-1]


def _pkg_map(registry: Any) -> Dict[str, dict]:
    """protocols[] → {id: entry}（id 缺失条目跳过）。"""
    out = {}
    for p in registry.protocols or []:
        pid = p.get("id")
        if pid:
            out[pid] = p
    return out


def registry_integrity_issues(registry: Any) -> List[str]:
    """registry 引用图闭合断言（A4/check21）：返回问题清单，空 = 自洽 PASS。

    只依赖 registry 自身（protocols[].references / module_ids / modules[]）——
    community 目录与 PyYAML 不在场不影响判断。裸号归一后比对。
    """
    issues: List[str] = []
    pkgs = _pkg_map(registry)
    for p in registry.protocols or []:
        pid = p.get("id") or "<匿名>"
        mids = [_norm(m) for m in (p.get("module_ids") or [])]
        # ③ 同包 module_ids 裸号重复（含限定/裸号并存 = 寻址歧义）
        seen: Dict[str, str] = {}
        for raw in p.get("module_ids") or []:
            n = _norm(raw)
            if n in seen:
                issues.append(f"③{pid} module_ids 裸号重复（寻址歧义）: "
                              f"{seen[n]} 与 {raw} 同为 {n}")
            else:
                seen[n] = raw
        # ①② references 目标闭合
        for r in p.get("references") or []:
            sp = r.get("source_package")
            if sp not in pkgs:
                issues.append(f"①②{pid} references.source_package 不在 registry "
                              f"protocols[] 在册: {sp!r}")
                continue
            src_mids = {_norm(m) for m in (pkgs[sp].get("module_ids") or [])}
            mid = _norm(r.get("module_id"))
            if mid not in src_mids:
                issues.append(f"②{pid} references.module_id 不在源包 {sp} "
                              f"module_ids 在列: {r.get('module_id')!r}")
    # 官方 modules 层：references 可指向官方核心？——registry 语义中 references 源包
    # 均为 community 包（protocols[]），官方核心模块不经 references 装配（P01 官方
    # 空层 optional 自行装载）。故 modules[] 不参与引用闭合；其完整性由 check14/20 承载。
    return issues


def referenced_by_packages(registry: Any, module_id: str) -> List[dict]:
    """引用反查（变更影响面）：registry protocols[].references 中引用 module_id 的包。

    module_id 支持裸号（M55）与限定/长类别前缀（情感类:M55 / 情感:M55）——裸号
    归一比对。返回 [{protocol, source_package, source_schema_version, asset_readonly}]，
    空 = 无引用方（删除该模块不破坏任何 references）。
    """
    n = _norm(module_id)
    out: List[dict] = []
    for p in registry.protocols or []:
        for r in p.get("references") or []:
            if _norm(r.get("module_id")) != n:
                continue
            out.append({
                "protocol": p.get("id"),
                "source_package": r.get("source_package"),
                "source_schema_version": r.get("source_schema_version"),
                "asset_readonly": r.get("asset_readonly"),
            })
    return out


def removal_impact(registry: Any, module_id: str) -> Dict[str, Any]:
    """拟删除 module_id 的影响面：registry 内被谁引用 + 是否官方核心在册。

    变更前置查询（不写盘）：返回 {module_id, referenced_by, in_official_core,
    in_packages}——破坏性变更（referenced_by 非空）先看清单再落盘。
    """
    n = _norm(module_id)
    refs = referenced_by_packages(registry, module_id)
    core_hits = [m for m in (registry.modules or []) if _norm(m.get("id")) == n]
    pkg_hits = [p.get("id") for p in registry.protocols or []
                if n in {_norm(m) for m in (p.get("module_ids") or [])}]
    return {
        "module_id": module_id,
        "referenced_by": refs,
        "in_official_core": [m.get("id") for m in core_hits],
        "in_packages": pkg_hits,
    }


def check_registry(path: Optional[str] = None) -> List[str]:
    """文件级便捷入口：读 registry.json → integrity issues（verify check21 接线）。"""
    from .registry_loader import load_registry
    reg = load_registry(path)
    return registry_integrity_issues(reg)
