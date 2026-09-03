"""文档生成器（指令集 5.3 generate_document）。

按管线层序组合所选模块 → 输出结构化 MD 文档：
  1) 文档头（管线元信息 + 生成时间 + 统计）
  2) 逐层输出：层头（层位 id/名称/描述）→ 层内各模块 source.md
  3) 资产引用附录（收集模块声明的 assets 键，从资产包 entries 解析）

模块顺序规则：
  - 以 pipeline.layer_ids 为骨架（P00→P80）
  - 层内多个模块按传入顺序保留
  - 层外的模块（layer 不在管线内）追加到"未挂载模块"节
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from .models import Module, Pipeline, AssetPack

DOC_TEMPLATE = """# {title}

> 由叙事工坊桌面工具生成
> 管线：{pipeline_name}（{pipeline_id}）｜ 模块 {module_count} 个 ｜ 资产包：{asset_text}
> 生成时间：{timestamp}

{toc}
---
"""


def order_modules(modules: List[Module],
                  pipeline: Pipeline) -> Tuple[List[Module], List[str]]:
    """按管线层序排序模块。返回 (有序列表, 警告列表)。

    - 管线声明层但未选中 → 记入警告（可选层忽略）
    - 模块层不在管线内 → 记入警告并排到队尾
    """
    ordered: List[Module] = []
    warnings: List[str] = []
    by_layer: dict = {}
    for m in modules:
        if not m.enabled:
            warnings.append(f"模块 {m.full_id} 已停用，跳过")
            continue
        by_layer.setdefault(m.layer, []).append(m)

    # 管线内层
    for lid in pipeline.layer_ids:
        layer = pipeline.layer(lid)
        if lid in by_layer:
            ordered.extend(by_layer.pop(lid))
        elif layer and not layer.optional and (layer.default_modules or []):
            # 非可选层有默认模块但没选中 → 提示
            warnings.append(
                f"层 {lid}（{layer.name}）无选中模块，默认 {layer.default_modules} 未装配")
    # 管线外层
    for lid in sorted(by_layer):
        warnings.append(f"模块层 {lid} 不在管线 {pipeline.id} 层序内，已追加到文末")
        ordered.extend(by_layer[lid])
    return ordered, warnings


def _doc_title(pipeline: Pipeline) -> str:
    if pipeline.structure_type == "techdoc":
        return f"{pipeline.name} · 技术文档"
    return f"{pipeline.name} · 叙事输出"


def _toc(modules: List[Module], pipeline: Pipeline) -> str:
    """目录（按层分组）"""
    lines = ["## 目录"]
    last = None
    for m in modules:
        if m.layer != last:
            layer = pipeline.layer(m.layer)
            lname = f"（{layer.name}）" if layer else ""
            lines.append(f"- **{m.layer} {lname}**")
            last = m.layer
        lines.append(f"  - {m.full_id} · {m.name}")
    return "\n".join(lines)


def _module_block(m: Module) -> str:
    """单个模块的内容块：优先 source.md 全文，缺失时回退到 logic。"""
    body = (m.source_md or "").strip()
    if not body:
        body = f"### 逻辑\n\n```\n{m.logic or '（无逻辑描述）'}\n```\n"
    # 防止模块 md 自带一级标题干扰文档层级 → 提升为三级
    lines: List[str] = []
    for ln in body.splitlines():
        if ln.startswith("# "):
            lines.append("### " + ln[2:].strip())
        elif ln.startswith("## "):
            lines.append("#### " + ln[2:].strip())
        else:
            lines.append(ln)
    head = f"### {m.full_id} · {m.name}（{m.layer}）"
    return "\n\n".join([head, "\n".join(lines)])


def collect_asset_keys(modules: List[Module]) -> List[str]:
    """收集全部模块引用的资产键（保序去重）"""
    seen: List[str] = []
    for m in modules:
        for k in m.assets or []:
            if k not in seen:
                seen.append(k)
    return seen


def _asset_appendix(keys: List[str],
                    asset_pack: Optional[AssetPack]) -> str:
    if not keys:
        return ""
    out = ["---", "", "## 资产引用附录", ""]
    entries = (asset_pack.entries if asset_pack else {}) or {}
    missing = []
    for k in keys:
        if k in entries:
            v = entries[k]
            if isinstance(v, str):
                out.append(f"### {k}\n\n{v}\n")
            else:
                out.append(f"### {k}\n\n```json\n{_json_text(v)}\n```\n")
        else:
            missing.append(k)
    if missing:
        out.append("> 以下资产键在本地资产包中缺失：")
        out.append("> " + "、".join(missing))
    return "\n".join(out)


def _json_text(v) -> str:
    import json
    return json.dumps(v, ensure_ascii=False, indent=2)


def generate_document(pipeline: Pipeline,
                      modules: List[Module],
                      asset_pack: Optional[AssetPack] = None,
                      title: str = "",
                      ) -> Tuple[str, List[str]]:
    """生成完整文档。返回 (md文本, 警告列表)。"""
    ordered, warnings = order_modules(modules, pipeline)
    title = title or _doc_title(pipeline)
    asset_text = asset_pack.name if asset_pack else "无"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    parts = [DOC_TEMPLATE.format(
        title=title,
        pipeline_name=pipeline.name,
        pipeline_id=pipeline.id,
        module_count=len(ordered),
        asset_text=asset_text,
        timestamp=timestamp,
        toc=_toc(ordered, pipeline),
    )]

    # 逐层输出
    last_layer = None
    for m in ordered:
        if m.layer != last_layer:
            layer = pipeline.layer(m.layer)
            if layer:
                parts.append(
                    f"\n## 层 {layer.id} · {layer.name}\n\n{layer.description}\n")
            else:
                parts.append(f"\n## 层 {m.layer}（未在管线中声明）\n")
            last_layer = m.layer
        parts.append(_module_block(m))

    parts.append(_asset_appendix(collect_asset_keys(ordered), asset_pack))
    return "\n\n".join(parts), warnings


def default_filename(pipeline: Pipeline) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{pipeline.id}_{pipeline.name}_{ts}.md"
