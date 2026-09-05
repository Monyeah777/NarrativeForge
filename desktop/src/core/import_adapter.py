"""读入适配器（v2.3.0 34 方案：A4 双向读入——外部→NF 反向解析层）。

与 exporter._REGISTRY 五出口（全 export-only）对称，提供 adapter_in 反向符号：
- parse_skill(text) -> SkillParseResult：SKILL.md 文本 → NF IRDocument 高保真
  重建（round-trip 与 export(ir,'skill') 逐字节对称）或宽容保留（外部自由文）。
- parse_ccv3(chara, world) -> Ccv3ParseResult：chara_card_v3 dict（+可选独立
  world dict）→ 叙事型 IR 骨架结构还原。

设计约束（34 方案核心 + 外部兼容实证驱动）：
- parse_skill 双层：**结构层**识别 NF 导出 body 层级模式（`## 层 {id} · {name}`、
  `### {full_id} · {name}`、`## 附加规则`）→ 高保真重建 IRDocument；
  **宽容层**对非 NF 层级 body（官方技能自由说明文）不强套层级：frontmatter
  name/description 必填校验 + 扩展字段（license 等）透传 metadata，正文整体
  保留——不崩、不静默丢；是否够格升 IR 由消费方判定（mode='external' 时
  ir=None）。
- frontmatter 解析**自写轻量解析器**（仓库无 PyYAML 硬依赖，pipeline_loader
  用内置回退策略——本模块同样不假设 yaml 在场）；description 支持引号包裹
  （官方 docx 长英文触发描述为双引号单行、内部可含裸单引号）。
- 失败路径（无 frontmatter / 缺 name·description / 空 body / spec 不符）→
  明确 ValueError，不静默产出坏 IR（静默丢内容不变式）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .ir import IRDocument, IRLayer, IRModule


# ============================================================== frontmatter
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """SKILL.md 文本 → (frontmatter dict, body)。

    轻量 YAML 子集：`---` 开闭行之间逐行 `key: value`；value 支持：
    - 裸值（skill-creator：无引号英文说明）
    - 双引号包裹单行（docx：含裸单引号与冒号，剥外层引号保留内部）
    - 单引号包裹单行（剥外层）
    扩展字段（license 等）一律透传。无法解析出闭合 frontmatter 时抛 ValueError。
    """
    if not text.startswith("---"):
        raise ValueError("无 YAML frontmatter（SKILL.md 应以 `---` 开头）")
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("frontmatter 未闭合（缺少第二个 `---`）")
    fm: dict = {}
    for ln in lines[1:end]:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", s)
        if not m:
            raise ValueError(f"frontmatter 行无法解析：{ln!r}")
        key, val = m.group(1), m.group(2)
        fm[key] = _unquote_yaml_value(val)
    body = "\n".join(lines[end + 1:])
    return fm, body


def _unquote_yaml_value(val: str) -> str:
    """剥 YAML 标量引号（双引号内 \\" 转义、单引号内 '' 转义）。"""
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        return val[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(val) >= 2 and val[0] == "'" and val[-1] == "'":
        return val[1:-1].replace("''", "'")
    return val


# ============================================================== 结果结构
@dataclass
class SkillParseResult:
    """parse_skill 结果。

    mode='nf'：NF 导出结构，ir 为高保真重建 IRDocument（可 round-trip）。
    mode='external'：非 NF 层级外部技能，ir=None（升 IR 由消费方判定），
    frontmatter/body 原样保留供消费。
    """
    ok: bool
    mode: str                                   # 'nf' | 'external'
    ir: Optional[IRDocument] = None             # nf 模式：重建 IR
    frontmatter: dict = field(default_factory=dict)
    body: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class Ccv3ParseResult:
    """parse_ccv3 结果：叙事型 IR 骨架 + chara 顶层字段透传。"""
    ok: bool
    ir: Optional[IRDocument] = None
    chara_meta: dict = field(default_factory=dict)   # chara/world 顶层透传
    warnings: List[str] = field(default_factory=list)


# ============================================================== parse_skill
# NF 导出 body 层级模式（对称面：skill_adapter._build_skill_md）
_RE_LAYER = re.compile(r"^## 层\s+([^\s·]+)\s*·\s*(.+)$")
_RE_MODULE = re.compile(r"^###\s+([^\s·]+)\s*·\s*(.+)$")
_RE_EXTRA = re.compile(r"^## 附加规则\s*$")
# NF 导出 description 格式：f"{pipeline_name}（{pipeline_id}）生成：协议/文档操作规格，共 N 个规则块。"
_RE_DESC_NF = re.compile(
    r"^(.+?)[（(]([^（）()]+)[)）]生成[:：]协议/文档操作规格，共\s*(\d+)\s*个规则块。?$")
_PLACEHOLDER_NO_BODY = "（无正文）"


def _parse_nf_body(body: str) -> tuple[Optional[str], List[IRLayer], List[IRModule],
                                       List[str]]:
    """解析 NF 层级正文 → (title, layers, extra_modules, warnings)。"""
    title: Optional[str] = None
    layers: List[IRLayer] = []
    extra: List[IRModule] = []
    warnings: List[str] = []

    cur_layer: Optional[IRLayer] = None
    cur_mod: Optional[IRModule] = None
    buf: List[str] = []
    in_extra = False

    def flush() -> None:
        nonlocal cur_mod, buf
        if cur_mod is None:
            buf = []
            return
        content = "\n".join(buf).strip("\n")
        if content == _PLACEHOLDER_NO_BODY:
            content = ""                      # 占位还原为空正文（高保真）
        cur_mod.content = content
        if in_extra:
            extra.append(cur_mod)
        elif cur_layer is not None:
            cur_layer.modules.append(cur_mod)
        else:                                  # 模块头出现在任何层头之前 → 损坏
            warnings.append(f"模块 {cur_mod.full_id} 前无层头，归入层外模块")
            extra.append(cur_mod)
        cur_mod = None
        buf = []

    lines = body.split("\n")
    # 一级标题 = title（NF 导出 body 首行 # {title}）
    for ln in lines:
        if ln.startswith("# ") and title is None:
            title = ln[2:].strip()
            break
    for raw in lines:
        ln = raw.rstrip("\r")
        lm = _RE_LAYER.match(ln)
        if lm:
            flush()
            in_extra = False
            cur_layer = IRLayer(id=lm.group(1).strip(),
                                name=lm.group(2).strip())
            layers.append(cur_layer)
            continue
        if _RE_EXTRA.match(ln):
            flush()
            in_extra = True
            cur_layer = None
            continue
        mm = _RE_MODULE.match(ln)
        if mm:
            flush()
            full_id = mm.group(1).strip()
            cur_mod = IRModule(full_id=full_id,
                               name=mm.group(2).strip(),
                               layer=(cur_layer.id if cur_layer else ""))
            continue
        if title is not None and ln == lines[0]:
            continue                           # # title 行本身不入 content
        if ln.startswith(("# ", "## ", "### ", "#### ")):
            # 未匹配 NF 层级模板的标题行：宽容保留进当前 content，不静默丢
            if cur_mod is not None or cur_layer is not None:
                buf.append(ln)
            continue
        if cur_mod is not None or in_extra:
            buf.append(ln)
        # 层头与模块头之间的空行/游离行不收集（对齐 _build_skill_md 结构）
    flush()
    return title, layers, extra, warnings


def parse_skill(text: str) -> SkillParseResult:
    """SKILL.md 文本 → SkillParseResult（结构层高保真重建 / 宽容层保留）。"""
    if not text or not text.strip():
        raise ValueError("SKILL.md 内容为空")
    fm, body = parse_frontmatter(text)
    name = fm.get("name", "").strip()
    desc = fm.get("description", "").strip()
    if not name:
        raise ValueError("frontmatter 缺少必填字段 name")
    if not desc:
        raise ValueError("frontmatter 缺少必填字段 description")
    if not body.strip():
        raise ValueError("SKILL.md 正文为空")

    # ---- 宽容层判定：body 无 NF 层级模式（官方技能自由说明文）→ 不套层级
    # 注意：正则无 re.MULTILINE，`^` 只锚定串首——须逐行 match 而非整串 search
    has_nf_hierarchy = any(
        _RE_LAYER.match(ln) or _RE_EXTRA.match(ln)
        for ln in body.splitlines())
    if not has_nf_hierarchy:
        return SkillParseResult(
            ok=True, mode="external", ir=None,
            frontmatter=fm, body=body,
            warnings=["正文非 NF 导出层级结构（`## 层`/`## 附加规则` 未命中），"
                      "按宽容层保留 frontmatter 与正文；是否升 IR 由消费方判定"])

    # ---- 结构层：NF 层级 body → 高保真重建 IRDocument（techdoc 型）
    title, layers, extra, w = _parse_nf_body(body)
    warnings = list(w)
    if title is None:
        # NF 导出必有 # title；缺失时回退 frontmatter name（罕见，记警告）
        title = name
        warnings.append("正文未找到一级标题 `# ...`，title 回退 frontmatter name")
    # description 回填 pipeline 字段（NF 导出格式）
    pipeline_id = pipeline_name = ""
    mdesc = _RE_DESC_NF.match(desc)
    if mdesc:
        pipeline_name = mdesc.group(1).strip()
        pipeline_id = mdesc.group(2).strip()
        n_declared = int(mdesc.group(3))
        n_actual = sum(len(l.modules) for l in layers) + len(extra)
        if n_declared != n_actual:
            warnings.append(
                f"frontmatter description 声明 {n_declared} 个规则块，"
                f"正文解析出 {n_actual} 个——以正文为准")
    else:
        warnings.append(
            "description 非 NF 导出格式（未解析出 pipeline/规则块计数），"
            "pipeline 字段留空，正文层级仍按结构层重建")
    ir = IRDocument(
        type="techdoc", title=title,
        pipeline_id=pipeline_id, pipeline_name=pipeline_name,
        layers=layers, extra_modules=extra,
        warnings=warnings,
        meta={"adapter_in": "parse_skill",
              "source": "SKILL.md",
              "frontmatter": fm},
    )
    return SkillParseResult(ok=True, mode="nf", ir=ir,
                            frontmatter=fm, body=body, warnings=warnings)


# ============================================================== parse_ccv3
_RE_COMMENT_LAYER = re.compile(r"^NF 层\s*([^\s·]+)\s*·\s*(.+)$")
_COMMENT_EXTRA = "NF 层外模块"
_COMMENT_ASSET = "NF 资产素材"
# NF 导出 chara description：f"{pipeline_name}（{pipeline_id}）装配产物 · N 个规则模块 + M 项资产素材。由叙事工坊 2.0 导出层生成。"
_RE_DESC_CCV3 = re.compile(
    r"^(.+?)[（(]([^（）()]+)[)）]装配产物")


def _entry_to_module(e: dict, seen: set, warnings: List[str]) -> Optional[IRModule]:
    """chara/world lorebook 条目 → IRModule（含层位/资产/层外归属判定）。"""
    keys = e.get("keys") or []
    full_id = str(keys[0]) if keys else str(e.get("name") or "")
    if not full_id:
        warnings.append("world 条目缺少 keys/name，跳过")
        return None
    if full_id in seen:
        return None                            # 已收集（chara 与 world 重复）
    seen.add(full_id)
    name = str(e.get("name") or full_id)
    content = str(e.get("content") or "")
    comment = str(e.get("comment") or "")
    if comment == _COMMENT_ASSET:
        return None                            # 资产条目由调用方还原 asset_refs
    lm = _RE_COMMENT_LAYER.match(comment)
    layer_id = lm.group(1).strip() if lm else ""
    layer_name = lm.group(2).strip() if lm else ""
    if not lm:
        warnings.append(f"条目 {full_id} 无 NF 层位注释（comment={comment!r}），"
                        "归入层外模块（extra_modules）")
    return IRModule(full_id=full_id, name=name,
                    layer=layer_id,
                    content=content)


def parse_ccv3(chara: dict, world: Optional[dict] = None) -> Ccv3ParseResult:
    """chara_card_v3 dict（+可选独立 world dict）→ 叙事型 IR 骨架。

    校验：spec == chara_card_v3 且 spec_version 非空（不符 → ValueError）。
    结构还原：character_book.entries[]（+ world.entries[] 补充）逐条 → IRModule，
    按 comment `NF 层 {id} · {name}` 归层、`NF 层外模块` 归 extra、资产条目还原
    asset_refs；无 NF 层位注释的外部条目归 extra（不静默丢）。
    chara 顶层字段（personality/scenario 等）透传 chara_meta，不冒充语义理解。
    """
    if not isinstance(chara, dict):
        raise ValueError("chara 应为 dict（chara_card_v3 JSON 对象）")
    if chara.get("spec") != "chara_card_v3":
        raise ValueError(f"spec 应为 chara_card_v3，实际：{chara.get('spec')!r}")
    if not chara.get("spec_version"):
        raise ValueError("缺少 spec_version（chara_card_v3 必填）")

    warnings: List[str] = []
    name = str(chara.get("name") or "")
    desc = str(chara.get("description") or "")
    cb = chara.get("character_book") or {}
    entries = list(cb.get("entries") or [])

    # pipeline 字段：chara description 若为 NF 导出格式则回填（round-trip 对称）
    pipeline_id = pipeline_name = ""
    mdesc = _RE_DESC_CCV3.match(desc)
    if mdesc:
        pipeline_name = mdesc.group(1).strip()
        pipeline_id = mdesc.group(2).strip()
    else:
        warnings.append("description 非 NF 装配产物格式，pipeline 字段留空")

    seen: set = set()
    layers: List[IRLayer] = []
    extra: List[IRModule] = []
    asset_refs: dict = {}
    layer_map: dict = {}

    def place(m: IRModule) -> None:
        if m.layer and m.layer in layer_map:
            layer_map[m.layer].modules.append(m)
            return
        if m.layer and m.layer not in layer_map:
            # 无对应层名时补层名（同一 id 首次出现处）
            pass
        extra.append(m)

    # chara entries
    for e in entries:
        keys = e.get("keys") or []
        full_id = str(keys[0]) if keys else str(e.get("name") or "")
        comment = str(e.get("comment") or "")
        if comment == _COMMENT_ASSET and full_id:
            asset_refs[full_id] = str(e.get("content") or "")
            seen.add(full_id)
            continue
        m = _entry_to_module(e, seen, warnings)
        if m is None:
            continue
        if m.layer:
            if m.layer not in layer_map:
                lm = _RE_COMMENT_LAYER.match(str(e.get("comment") or ""))
                layer_map[m.layer] = IRLayer(
                    id=m.layer,
                    name=lm.group(2).strip() if lm else m.layer)
                layers.append(layer_map[m.layer])
            layer_map[m.layer].modules.append(m)
        else:
            extra.append(m)

    # world entries 补充（chara 内嵌 character_book 与独立 world 通常同源，
    # 重复条目按 full_id 去重——不重复入 IR）
    if world is not None:
        if not isinstance(world, dict):
            raise ValueError("world 应为 dict")
        w_name = str(world.get("name") or "")
        for e in list((world.get("entries") or [])):
            keys = e.get("keys") or []
            full_id = str(keys[0]) if keys else str(e.get("name") or "")
            if not full_id:
                continue
            if full_id in seen:
                continue
            comment = str(e.get("comment") or "")
            if comment == _COMMENT_ASSET:
                asset_refs[full_id] = str(e.get("content") or "")
                seen.add(full_id)
                continue
            m = _entry_to_module(e, seen, warnings)
            if m is None:
                continue
            if m.layer:
                if m.layer not in layer_map:
                    lm = _RE_COMMENT_LAYER.match(comment)
                    layer_map[m.layer] = IRLayer(
                        id=m.layer,
                        name=lm.group(2).strip() if lm else m.layer)
                    layers.append(layer_map[m.layer])
                layer_map[m.layer].modules.append(m)
            else:
                extra.append(m)

    if not name:
        warnings.append("chara 缺少 name，IR title 留空")
    ir = IRDocument(
        type="narrative", title=name,
        pipeline_id=pipeline_id, pipeline_name=pipeline_name,
        layers=layers, extra_modules=extra,
        asset_refs=asset_refs, asset_missing=[],
        warnings=warnings,
        meta={"adapter_in": "parse_ccv3",
              "source": "chara_card_v3"
                        + (" + world" if world is not None else ""),
              "spec": chara.get("spec"),
              "spec_version": chara.get("spec_version")},
    )
    chara_meta = {
        "chara": {k: v for k, v in chara.items()
                  if k not in ("character_book",)},
        "world_name": (world or {}).get("name") if world else None,
    }
    return Ccv3ParseResult(ok=True, ir=ir, chara_meta=chara_meta,
                           warnings=warnings)
