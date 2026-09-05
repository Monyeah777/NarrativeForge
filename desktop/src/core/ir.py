"""IR 内容归一化层（v1.2.0 协议中转站 v2，2.0 E0-①）。

统一中间表示（Intermediate Representation）：
- render_ir（generator.py）把装配结果归一化为 IRDocument
- ir_to_md 是 IR 的默认原生适配器（MD 序列化）
- v2.0 的 CCV3/SKILL/AGENTS 适配器消费同一 IR，不改 IR 只加适配器

IR 原则（宁薄勿厚，防第五套协议）：只承载够渲染外部格式的最小结构。
IR→CCV3 投影契约预留：content 为纯正文（标题已归一，可折叠入 persona/
scenario/world 条目）；layer 保留（世界书可按键映射）；asset_refs 分离
（资产不混入正文，供 world 素材引用）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


# ------------------------------------------------------------------ 结构
@dataclass
class IRModule:
    """装配中单个模块的归一化表示。"""
    full_id: str = ""
    name: str = ""
    layer: str = ""
    content: str = ""          # 归一正文（标题提升后；供外部格式折叠）

    def to_md_block(self) -> str:
        """模块块：head + 归一正文（对齐原 generator _module_block）。"""
        head = f"### {self.full_id} · {self.name}（{self.layer}）"
        return "\n\n".join([head, self.content])


@dataclass
class IRLayer:
    """装配层（仅含选中模块的层，按管线层序）。"""
    id: str = ""
    name: str = ""
    description: str = ""
    modules: List[IRModule] = field(default_factory=list)

    def to_md_header(self) -> str:
        # 对齐原 generate_document 的层头 part 格式（首尾换行）
        return f"\n## 层 {self.id} · {self.name}\n\n{self.description}\n"


@dataclass
class IRDocument:
    """装配结果的统一中间表示。"""
    type: str = "narrative"             # narrative / techdoc（管线 structure_type）
    title: str = ""
    pipeline_id: str = ""
    pipeline_name: str = ""
    layers: List[IRLayer] = field(default_factory=list)     # 层间按管线层序
    extra_modules: List[IRModule] = field(default_factory=list)  # 层外模块
    asset_refs: dict = field(default_factory=dict)          # 键 → 值（缺失 None）
    asset_missing: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)                 # timestamp/generator


# ------------------------------------------------------------------ 正文归一
def normalize_module_body(body: str) -> str:
    """模块正文归一：一级/二级标题提升为 ###/####（防干扰文档层级）。"""
    if not body:
        return ""
    lines: List[str] = []
    for ln in body.splitlines():
        if ln.startswith("# "):
            lines.append("### " + ln[2:].strip())
        elif ln.startswith("## "):
            lines.append("#### " + ln[2:].strip())
        else:
            lines.append(ln)
    return "\n".join(lines).strip("\n")


# ------------------------------------------------------------------ MD 序列化（IR 默认适配器）
def _toc(ir: IRDocument) -> str:
    """目录（对齐原 generator._toc：按层分组，层名括号，层间顺序 = 装配顺序）。"""
    lines = ["## 目录"]
    last = None
    for layer in ir.layers:
        for m in layer.modules:
            if m.layer != last:
                lname = f"（{layer.name}）" if layer.name else ""
                lines.append(f"- **{m.layer} {lname}**")
                last = m.layer
            lines.append(f"  - {m.full_id} · {m.name}")
    for m in ir.extra_modules:
        if m.layer != last:
            # 层外模块在管线中无对应层 → 无层名括号（对齐原实现空 lname）
            lines.append(f"- **{m.layer} **")
            last = m.layer
        lines.append(f"  - {m.full_id} · {m.name}")
    return "\n".join(lines)


def _json_text(v) -> str:
    import json
    return json.dumps(v, ensure_ascii=False, indent=2)


def _asset_appendix(ir: IRDocument) -> str:
    if not ir.asset_refs and not ir.asset_missing:
        return ""
    out = ["---", "", "## 资产引用附录", ""]
    for k, v in ir.asset_refs.items():
        if v is None:
            continue
        if isinstance(v, str):
            out.append(f"### {k}\n\n{v}\n")
        else:
            out.append(f"### {k}\n\n```json\n{_json_text(v)}\n```\n")
    if ir.asset_missing:
        out.append("> 以下资产键在本地资产包中缺失：")
        out.append("> " + "、".join(ir.asset_missing))
    return "\n".join(out)


def ir_to_md(ir: IRDocument) -> str:
    """IR → MD（默认原生适配器）。输出格式对齐原 generate_document。"""
    ts = ir.meta.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M")
    asset_text = ir.meta.get("asset_text") or "无"
    header = f"""# {ir.title}

> 由叙事工坊桌面工具生成
> 管线：{ir.pipeline_name}（{ir.pipeline_id}）｜ 模块 {sum(len(l.modules) for l in ir.layers) + len(ir.extra_modules)} 个 ｜ 资产包：{asset_text}
> 生成时间：{ts}

{_toc(ir)}
---
"""
    parts = [header]
    for layer in ir.layers:
        parts.append(layer.to_md_header())
        parts.extend(m.to_md_block() for m in layer.modules)
    if ir.extra_modules:
        last = None
        for m in ir.extra_modules:
            if m.layer != last:
                parts.append(f"\n## 层 {m.layer}（未在管线中声明）\n")
                last = m.layer
            parts.append(m.to_md_block())
    parts.append(_asset_appendix(ir))
    return "\n\n".join(parts)
