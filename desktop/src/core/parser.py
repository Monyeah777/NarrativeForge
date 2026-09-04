"""模块解析器：从文本中提取模块结构（指令集 5.1 parse_module）。

兼容两种来源格式：
1. 指令集格式（AI 按模板生成，导入对话框示例）：
   # M44：社团竞争系统
   ## 定义
   - 层：P30
   - 输入：M40, M22
   - 输出：competition_score:int
   ## 规则 / ## 核心逻辑：...
   ## 引用的资产：LOCATIONS, GANG
2. NarrativeForge 仓库格式（真实模块，如 community/校园情感领域包/modules/M22_三冲动驱动.md）：
   # 模块 情感:M22 · 三冲动驱动
   > 类别：情感｜来源：校园｜挂载点：P40 行为决策（active）｜依赖：M00、M40｜发布：npc_action
   ## 1. 职责 / ## 2. 出厂规则 ...
"""
from __future__ import annotations

import re
from typing import Optional

from .models import Module, CATEGORIES


def _norm_list(v) -> list:
    """把 'M40, M22' / ['M40','M22'] / '' 统一成 list[str]"""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        # 支持中文顿号/逗号/空格分隔
        parts = re.split(r"[、,，;\s]+", s)
        return [p.strip() for p in parts if p.strip()]
    return [str(v)]


def _extract_yaml_list(text: str) -> list:
    """从规则文本里抓 [] 列表：['M00','M40'] 或 [M00, M40]"""
    m = re.search(r"\[([^\]]*)\]", text)
    if not m:
        return []
    inner = m.group(1).replace("'", "").replace('"', "")
    return [p.strip() for p in re.split(r"[、,，;\s]+", inner) if p.strip()]


def parse_module(content: str, category_hint: str = "") -> Module:
    """从文本解析模块。解析失败时抛 ValueError（附原因）。"""
    if not content or not content.strip():
        raise ValueError("内容为空，无法解析")

    m = Module()
    m.source_md = content.strip()
    lines = content.splitlines()

    # ---- 识别标题行 ----
    title_line = ""
    for ln in lines:
        if ln.startswith("# "):
            title_line = ln
            break

    # ---- 格式2：仓库式头部 # 模块 情感:M22 · 三冲动驱动 ----
    m2 = re.match(r"#\s*模块\s*([A-Za-z\u4e00-\u9fff]+)?:?(M?\d+)\s*[·.、\-]?\s*(.+)",
                  title_line)
    if m2 and ("模块" in title_line[:4] or ":" in title_line.split("·")[0]):
        prefix = m2.group(1) or category_hint or ""
        m.id = m2.group(2).lstrip("M").rjust(2, "0")
        m.id = "M" + m.id
        m.name = m2.group(3).strip()
        # 类别归一（情感/生存/世界/事件/通用/技术文档 → 情感类…）
        cat_map = {c.rstrip("类"): c for c in CATEGORIES}
        if prefix in cat_map:
            m.category = cat_map[prefix]
        elif category_hint:
            m.category = category_hint
        else:
            m.category = "通用类"
        return _parse_nf_style(m, lines)

    # ---- 格式1：指令集式 # M44：社团竞争系统 ----
    m1 = re.match(r"#\s*(?:模块\s*)?([A-Za-z\u4e00-\u9fff]+:)?(M?\d+)[:：·.\-\s]*(.*)", title_line)
    if m1:
        prefix = m1.group(1).rstrip(":：") if m1.group(1) else ""
        m.id = m1.group(2).lstrip("M").rjust(2, "0")
        m.id = "M" + m.id
        m.name = m1.group(3).strip() or m.id
        cat_map = {c.rstrip("类"): c for c in CATEGORIES}
        if prefix in cat_map:
            m.category = cat_map[prefix]
        elif category_hint:
            m.category = category_hint
        else:
            m.category = "通用类"
        return _parse_directive_style(m, lines)

    raise ValueError("无法识别模块标题（期望 `# M44：名称` 或 `# 模块 情感:M22 · 名称`）")


def _parse_directive_style(m: Module, lines: list) -> Module:
    """指令集格式：## 定义 / - key: value / ## 规则 / ## 引用的资产"""
    current_section = ""
    logic_buf: list[str] = []
    definition_fields: dict[str, str] = {}

    for ln in lines:
        s = ln.strip()
        if s.startswith("## "):
            current_section = s[3:].strip()
            continue
        if not s or s.startswith("#"):
            continue
        if current_section in ("定义", "Definition", "def"):
            mm = re.match(r"^[-*]\s*([^:：]{1,16})[:：]\s*(.+)$", s)
            if mm:
                definition_fields[mm.group(1).strip()] = mm.group(2).strip()
        elif current_section in ("规则", "核心逻辑", "逻辑", "Rules", "logic"):
            logic_buf.append(s)
        elif current_section in ("引用的资产", "资产", "Assets", "assets"):
            mm = re.match(r"^[-*]\s*(.+)$", s)
            if mm:
                m.assets.extend(_norm_list(mm.group(1)))

    # 字段名归一（层/layer、输入/inputs、输出/outputs、发布/events_publish…）
    f = definition_fields
    if not m.name:
        m.name = m.id
    if f.get("层") or f.get("layer") or f.get("挂载"):
        m.layer = (f.get("层") or f.get("layer") or f.get("挂载") or "").strip()
        lm = re.search(r"P\d\d", m.layer)
        m.layer = lm.group(0) if lm else (m.layer or "P40")
    m.inputs = _norm_list(f.get("输入") or f.get("inputs") or f.get("依赖"))
    m.outputs = _norm_list(f.get("输出") or f.get("outputs"))
    m.events_publish = _norm_list(f.get("发布") or f.get("events_publish") or
                                   f.get("发布事件"))
    m.events_subscribe = _norm_list(f.get("订阅") or f.get("events_subscribe"))
    # 定义区资产（- 资产：LOCATIONS, GANG）与『## 引用的资产』段落合并去重
    for a in _norm_list(f.get("资产") or f.get("assets")):
        if a and a not in m.assets:
            m.assets.append(a)
    if f.get("可替换") is not None or f.get("replaceable") is not None:
        raw = (f.get("可替换") or f.get("replaceable") or "true").strip().lower()
        m.replaceable = raw not in ("false", "否", "0", "no")

    logic = "\n".join(logic_buf).strip()
    if logic:
        m.logic = logic
    elif f.get("logic"):
        m.logic = f["logic"]
    return m


def _parse_nf_style(m: Module, lines: list) -> Module:
    """仓库格式：> 类别：…｜来源：…｜挂载点：P40 …（active）｜依赖：M00、M40｜发布：…"""
    for ln in lines:
        s = ln.strip()
        if s.startswith(">"):
            # 元信息行
            for seg in re.split(r"[｜|]", s.lstrip("> ")):
                kv = re.split(r"[:：]", seg, maxsplit=1)
                if len(kv) != 2:
                    continue
                k, v = kv[0].strip(), kv[1].strip()
                if k in ("类别", "分类"):
                    cat_map = {c.rstrip("类"): c for c in CATEGORIES}
                    m.category = cat_map.get(v.rstrip("类"), v + "类" if v else m.category)
                elif k == "挂载点":
                    lm = re.search(r"P\d\d", v)
                    if lm:
                        m.layer = lm.group(0)
                    if "active" in v:
                        m.replaceable = False
                elif k == "依赖":
                    m.inputs = _norm_list(v)
                elif k == "发布":
                    m.events_publish = _norm_list(v)
                elif k == "订阅":
                    m.events_subscribe = _norm_list(v)
        elif s.startswith("## ") and "职责" in s:
            # 后续段落视为逻辑
            pass

    # 逻辑：抓取规则/职责正文（精简：取 ## 后代码块/要点，最多 2000 字）
    buf: list[str] = []
    in_code = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code and s:
            buf.append(s)
    logic = "\n".join(buf).strip()
    if logic:
        m.logic = logic[:2000]
    if not m.logic:  # 无代码块则抓 ## 职责 后正文
        hit = False
        for ln in lines:
            s = ln.strip()
            if s.startswith("## "):
                hit = "职责" in s or "规则" in s
                continue
            if hit and s and not s.startswith(("#", "```", ">")):
                buf.append(s)
        m.logic = "\n".join(buf)[:2000]
    return m


def parse_asset_entries_from_text(text: str) -> dict:
    """把资产文本按 '## 键' 分段拆成 {键: 内容}"""
    out: dict = {}
    cur_key = None
    buf: list[str] = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("## ") and len(s) < 80:
            if cur_key:
                out[cur_key] = "\n".join(buf).strip()
            cur_key = s[3:].strip()
            buf = []
        elif cur_key:
            buf.append(ln)
    if cur_key:
        out[cur_key] = "\n".join(buf).strip()
    return out