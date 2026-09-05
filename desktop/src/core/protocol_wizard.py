"""协议定义向导（v2.0.x-E2：ProtocolForm → protocol.yaml v2 生成 + self_check）。

- GUI 表单（不懂 Schema 用户）→ ProtocolForm → build_protocol_yaml 产合规
  protocol.yaml（对齐 01 §6.1 Schema v2 + 真实实例结构：schema_version "2"、
  references []/cross_package [] 自动填——用户只管业务字段）。
- self_check 自检（对齐 verify check14 ①-⑤ 粗校验）：yaml 可解析 /
  schema_version / module_id_range 非空 / modules desc 齐 / mount default ⊆
  编号清单。产出的 protocol.yaml 应能过 v1 协议登记门禁的粗校验。
- 非目标：无 LLM 自然语言（表单驱动）；不改协议层；登记沿用 v1 三要件。

官方核心配合集（DEFAULT_CORE_MODULES）：12 件（两真实实例 core_modules 同列）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# 官方核心配合 12 件（实例实证：通用核心基础包 + 校园包 core_modules 同列）
DEFAULT_CORE_MODULES: List[str] = [
    "M00", "通用:M10", "M08", "M23", "事件:M22", "M06",
    "M12", "M13", "M20", "M24", "M50", "M80",
]


@dataclass
class ProtocolForm:
    """向导表单结构化输入（业务字段；结构字段由生成器自动）。"""
    id: str = ""
    name: str = ""
    pipeline: str = "P01"
    module_id_range: List[str] = field(default_factory=list)   # Mxx / 类别:Mxx
    categories: List[str] = field(default_factory=list)
    core_only: bool = True
    modules: List[Tuple[str, str]] = field(default_factory=list)  # [(id, desc)]
    mount_layers: Dict[str, Dict] = field(default_factory=dict)  # {层名:{default,available}}
    core_modules: List[str] = field(default_factory=list)  # 缺省 = DEFAULT_CORE_MODULES
    # A1 补遗（28 方案）：产出语义声明——"" 未声明 / "project_rules" / "skill"
    # （对齐 semantics.PROJECT_RULES / SKILL；声明后写入 yaml 供 self_check 校验、
    # 下游按裁决路由 AGENTS/CLAUDE 或 SKILL）
    doc_semantics: str = ""


def _fmt_list(items) -> str:
    return "\n".join(f"    - {i!r}" if not str(i).startswith("M") or ":" in str(i)
                     else f'    - "{i}"' for i in items)


def build_protocol_yaml(form: ProtocolForm) -> str:
    """表单 → 合规 protocol.yaml 文本（结构对齐真实实例）。"""
    # A1 补遗：产出语义声明非空时校验值域并写入 package 段（空=不写，兼容真实实例）
    sem_line = ""
    if form.doc_semantics:
        from .semantics import PROJECT_RULES, SKILL
        if form.doc_semantics not in (PROJECT_RULES, SKILL):
            raise ValueError(
                f"doc_semantics 应为 '{PROJECT_RULES}' 或 '{SKILL}'"
                f"（产物×适配矩阵：AGENTS=项目约定 / SKILL=能力包），实际 {form.doc_semantics}")
        sem_line = f"  doc_semantics: {form.doc_semantics}\n"
    core = list(form.core_modules) if form.core_modules else DEFAULT_CORE_MODULES
    core_l = "\n".join(f'    - "{c}"' if ":" in c or c == "M00"
                       else f"    - {c}" for c in core)
    mod_l = "\n".join(
        f'    - id: "{i}"\n      desc: {d}' for i, d in form.modules)
    ids_l = "\n".join(f'    - "{i}"' for i in form.module_id_range)
    cat_l = "\n".join(f"    - {c}" for c in form.categories)
    mount_l = ""
    for layer, spec in form.mount_layers.items():
        d = ", ".join(f'"{x}"' for x in (spec.get("default") or []))
        a = ", ".join(f'"{x}"' for x in (spec.get("available") or []))
        mount_l += f"    {layer}: {{default: [{d}], available: [{a}]}}\n"
    mount_l = mount_l.rstrip("\n")
    n_asset = 0  # 向导新包默认零资产（机制包先例）；用户后续补资产手改 count
    return f"""# protocol.yaml — 第三方协议声明（{form.name}，由叙事工坊协议定义向导生成）
# 依据 01 §6.1 Schema 模板骨架 + 02 §8.3 第三方协议登记；机读真相 = 本文件，人读速览 = README.md（双源一致，check14 ⑥ / check15 ⑤ 断言）
protocol:
  schema_version: "2"          # 引用 Schema 版本，v2 起支持 references
package:
  id: {form.id}
  name: {form.name}
  pipeline: {form.pipeline}
{sem_line}  module_id_range:
{ids_l}
  categories:
{cat_l}
  dependencies:
    core_only: {str(form.core_only).lower()}
    core_modules: [{', '.join(f'"{c}"' if ':' in c or c == 'M00' else c for c in core)}]
    cross_package: []
  references: []
  modules:
{mod_l}
  assets:
    count: {n_asset}
    readme: README.md
  mount_layers:
{mount_l}
"""


def self_check(yaml_text: str) -> List[str]:
    """自检（对齐 verify check14 ①-⑤ 粗校验）。返回警告/失败列表；空 = 通过。"""
    warns: List[str] = []
    try:
        import re
        body = "\n".join(l for l in yaml_text.splitlines()
                         if not l.strip().startswith("#"))
        import yaml
        data = yaml.safe_load(body)
    except Exception as exc:
        return [f"yaml 解析失败：{exc}"]
    pkg = (data or {}).get("package") or {}
    proto = (data or {}).get("protocol") or {}
    if proto.get("schema_version") not in ("2",):
        warns.append(f"schema_version 应为 '2'，实际 {proto.get('schema_version')}")
    if not pkg.get("module_id_range"):
        warns.append("module_id_range 为空——需声明模块编号（M91-M99 社区段规则）")
    mods = pkg.get("modules") or []
    for m in mods:
        if not m.get("desc"):
            warns.append(f"模块 {m.get('id')} 缺 desc")
    # 挂载 default ⊆ module_id_range（允许类别前缀命中）
    id_range = [str(x).split(":")[-1] for x in (pkg.get("module_id_range") or [])]
    for layer, spec in (pkg.get("mount_layers") or {}).items():
        for d in (spec.get("default") or []):
            if str(d).split(":")[-1] not in id_range:
                warns.append(f"挂载层 {layer} default {d} 不在 module_id_range 内")
    # A1 裁决规则集成（25 方案）：协议若声明产出语义（doc_semantics），
    # 校验值域并提示出口——project_rules → AGENTS/CLAUDE，skill → SKILL。
    sem = pkg.get("doc_semantics") or proto.get("doc_semantics")
    if sem is not None:
        from .semantics import PROJECT_RULES, SKILL
        if sem not in (PROJECT_RULES, SKILL):
            warns.append(
                f"doc_semantics 应为 '{PROJECT_RULES}' 或 '{SKILL}'，"
                f"实际 {sem}（产物×适配矩阵：AGENTS=项目约定 / SKILL=能力包）")
    return warns
