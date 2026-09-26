#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽象阶梯（protocol/LAYERS.json）—— 真源唯一 + 生成投影 + 语义判据。

**这是什么**：NF 的分层此前只有四套互不相干的「层」词汇（L0-L3 依赖治理编号 / P00-P80
管线层位 / mount_layers 模块挂载层 / 标准目录 layer），而「谁在动」（终端、AI）与
「被加工的物」（协议、资产）混在一根梯子上。本模块把阶梯收成**两轴 + 纵切**：

- **抽象轴四阶**：契约 → 资产 → 引擎 → 出口（越往下越稳定、越贵改）；
- **入口面**：只登记角色（人机 / AI 装配线 / MCP / 图书馆取件），永不作为真源；
- **验证纵切**：门禁与证据切过四阶，故不是「层」。

**分工**（遵 ADR-0003 断言表 kind 封闭集）：
- 形状类断言（声明件在场、生成区在场、无绝对路径）→ `protocol/assertions.json` 一行数据；
- 语义类判据（归属互斥 / 接口面子集 / 依赖向下 / 入口非真源 / 退役阶不被依赖 …）→ 留本模块代码。

**单一真源 + 生成投影**：`protocol/LAYERS.json` 是唯一真源；`docs/layers.md` 的生成区与
`nf layers` 的输出都是它的投影——生成区与实时渲染不一致即 FAIL（L10）。

本模块纯 stdlib、纯只读（除显式 `--write` 渲染），确定性（同输入同输出）。
"""
from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

DECL_REL = "protocol/LAYERS.json"
SCHEMA = "nf-layers/1"
DOC_REL = "docs/layers.md"
VERIFY_REL = "verify.sh"
ASSERTIONS_REL = "protocol/assertions.json"
MARK_BEGIN = "<!-- nf:layers:begin -->"
MARK_END = "<!-- nf:layers:end -->"
#: 引擎阶不得反向 import 的入口面模块名（入口可替换，真源不行）
ENTRY_MODULE_NAMES = ("nf", "scripts")
_CHECK_DEF = re.compile(r"^check(\d+)\(\)\{", re.M)
_JUDGE_CHECK = re.compile(r"^check(\d+)$")
_JUDGE_ASSERTION = "assertion:"


def load(root: str = ".") -> Dict[str, Any]:
    """读阶梯真源；缺件或 schema 不符 → 抛带修复指引的错误（不静默降级）。"""
    path = Path(root) / DECL_REL
    if not path.is_file():
        raise ValueError("缺阶梯真源 %s（修复指引：先落该件再跑 nf layers --verify）"
                         % DECL_REL)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("阶梯真源 %s 不是合法 JSON：%s（修复指引：修 JSON 语法后重跑）"
                         % (DECL_REL, exc))
    if str(doc.get("schema") or "") != SCHEMA:
        raise ValueError("阶梯真源 schema 不匹配（期望 %s；修复指引：核对 schema 字段）"
                         % SCHEMA)
    return doc


def _expand(root: str, globs) -> set:
    """展开 glob → 仓库相对路径集合（只取文件；确定性排序无关，返回集合）。"""
    out = set()
    base = Path(root)
    for pattern in globs or []:
        for p in base.glob(str(pattern)):
            if p.is_file():
                out.add(p.relative_to(base).as_posix())
    return out


def _exists(root: str, rel: str) -> bool:
    return (Path(root) / str(rel)).exists()


def _derived_files(root: str, doc: Dict[str, Any]) -> set:
    return _expand(root, doc.get("derived") or [])


def tier_faces(root: str, doc: Dict[str, Any]) -> Dict[str, set]:
    """每阶真源面（已扣除派生物）→ {tier_id: {rel, …}}。"""
    derived = _derived_files(root, doc)
    out = {}
    for tier in doc.get("tiers") or []:
        out[str(tier.get("id"))] = \
            _expand(root, (tier.get("source") or {}).get("globs")) - derived
    return out


def _rule_issues(root: str, doc: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    tiers = doc.get("tiers") or []
    tier_ids = [str(t.get("id")) for t in tiers]
    derived = _derived_files(root, doc)

    # L1 真源在位
    for tier in tiers:
        face = _expand(root, (tier.get("source") or {}).get("globs"))
        if not (tier.get("source") or {}).get("globs"):
            issues.append("L1 阶 %s 未声明真源面（修复指引：在 source.globs 写明真源落点）"
                          % tier.get("id"))
        elif not face:
            issues.append("L1 阶 %s 的真源面展开为空：%s（修复指引：核对 globs 与实况）"
                          % (tier.get("id"), (tier.get("source") or {}).get("globs")))
    for lv in doc.get("asset_levels") or []:
        if not _expand(root, lv.get("globs")):
            issues.append("L1 资产子级 %s 的真源面为空：%s（修复指引：核对 globs）"
                          % (lv.get("id"), lv.get("globs")))
        if str(lv.get("tier") or "") not in tier_ids:
            issues.append("L1 资产子级 %s 的 tier 不在阶名单：%s（修复指引：改成真实阶 id）"
                          % (lv.get("id"), lv.get("tier")))
    for sf in doc.get("surfaces") or []:
        for rel in sf.get("entries") or []:
            if not _exists(root, rel):
                issues.append("L1 入口面 %s 的入口件不存在：%s（修复指引：补件或改成真实路径）"
                              % (sf.get("id"), rel))
    for comp in (doc.get("crosscut") or {}).get("components") or []:
        if not _exists(root, comp.get("artifact")):
            issues.append("L1 纵切件 %s 不存在：%s（修复指引：补件或改成真实路径）"
                          % (comp.get("id"), comp.get("artifact")))

    # L2 归属互斥（派生物已扣除）
    faces = {tid: _expand(root, (t.get("source") or {}).get("globs")) - derived
             for t, tid in zip(tiers, tier_ids)}
    for i, a in enumerate(tier_ids):
        for b in tier_ids[i + 1:]:
            overlap = sorted(faces.get(a, set()) & faces.get(b, set()))
            if overlap:
                issues.append("L2 阶 %s 与阶 %s 真源面重叠：%s（修复指引：把件归给唯一一阶，"
                              "或把派生物登记进 derived）"
                              % (a, b, "、".join(overlap[:3])))

    # L3 接口面 ⊆ 真源面
    for tier in tiers:
        tid = str(tier.get("id"))
        iface = _expand(root, (tier.get("interface") or {}).get("globs"))
        if not iface:
            issues.append("L3 阶 %s 未声明接口面（修复指引：在 interface.globs 写明跨阶可依赖面）"
                          % tid)
        stray = sorted(iface - faces.get(tid, set()) - derived)
        if stray:
            issues.append("L3 阶 %s 接口面超出真源面：%s（修复指引：接口必须是真源面的子集）"
                          % (tid, "、".join(stray[:3])))

    # L4 依赖向下无环
    order = {str(t.get("id")): int(t.get("order", 99)) for t in tiers}
    for tier in tiers:
        tid = str(tier.get("id"))
        for dep in tier.get("depends_on") or []:
            dep = str(dep)
            if dep not in order:
                issues.append("L4 阶 %s 依赖了不存在的阶：%s（修复指引：改成真实阶 id）"
                              % (tid, dep))
            elif order[dep] >= order[tid]:
                issues.append("L4 阶 %s 依赖方向不向下：%s（order %d ≥ 自身 %d；"
                              "修复指引：依赖只能指向更下位的阶）"
                              % (tid, dep, order[dep], order[tid]))
    graph = {str(t.get("id")): [str(d) for d in t.get("depends_on") or []]
             for t in tiers}
    walked: set = set()
    reported_cycles: set = set()

    def _walk(tid, stack):
        if tid in stack:
            if " → ".join(list(stack) + [tid]) not in reported_cycles:
                reported_cycles.add(" → ".join(list(stack) + [tid]))
                issues.append("L4 依赖图存在环：%s（修复指引：断开上行依赖）"
                              % " → ".join(list(stack) + [tid]))
            return
        if tid in walked:
            return
        for dep in graph.get(tid, []):
            if dep in order:
                _walk(dep, stack + [tid])
        walked.add(tid)

    for tid in tier_ids:
        _walk(tid, [])

    # L5 入口面只登记角色
    for sf in doc.get("surfaces") or []:
        if sf.get("is_source_of_truth") is not False:
            issues.append("L5 入口面 %s 的 is_source_of_truth 必须为 false"
                          "（修复指引：入口是角色，真源只能是四阶）" % sf.get("id"))
        for served in sf.get("serves") or []:
            if str(served) not in tier_ids:
                issues.append("L5 入口面 %s 的 serves 指向不存在的阶：%s"
                              "（修复指引：改成真实阶 id）" % (sf.get("id"), served))

    # L6 引擎不反向 import 入口面
    for rel in sorted(_expand(root, ["desktop/src/core/*.py"])):
        try:
            tree = ast.parse((Path(root) / rel).read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                if name in ENTRY_MODULE_NAMES:
                    issues.append("L6 引擎阶反向 import 入口面件：%s:%d import %s"
                                  "（修复指引：入口可替换，core 不得依赖它——改由 CLI 层注入）"
                                  % (rel, node.lineno, name))

    # L7 退役阶不被依赖
    retired = {str(t.get("id")) for t in tiers if str(t.get("status")) == "retired"}
    for tier in tiers:
        if str(tier.get("status")) == "retired":
            continue
        for dep in tier.get("depends_on") or []:
            if str(dep) in retired:
                issues.append("L7 在役阶 %s 依赖了退役阶 %s（修复指引：把该能力改依赖重分派后的阶）"
                              % (tier.get("id"), dep))
        if str(tier.get("status")) not in (doc.get("vocabulary") or {}).get("status", []):
            issues.append("L7 阶 %s 的 status 越词表：%s" % (tier.get("id"), tier.get("status")))

    # L8 judged_by 可解析
    checks = set(_CHECK_DEF.findall(Path(root, VERIFY_REL).read_text(encoding="utf-8"))) \
        if _exists(root, VERIFY_REL) else set()
    a_path = Path(root, ASSERTIONS_REL)
    assertion_ids = set()
    if a_path.is_file():
        assertion_ids = {str(a.get("id")) for a in
                         (json.loads(a_path.read_text(encoding="utf-8"))
                          .get("assertions") or [])}
    refs = []
    for tier in tiers:
        refs += [(str(tier.get("id")), r) for r in tier.get("judged_by") or []]
    for lv in doc.get("asset_levels") or []:
        refs += [(str(lv.get("id")), r) for r in lv.get("judged_by") or []]
    for comp in (doc.get("crosscut") or {}).get("components") or []:
        refs += [(str(comp.get("id")), r) for r in comp.get("judged_by") or []]
    for owner, raw in refs:
        ref = str(raw)
        m = _JUDGE_CHECK.match(ref)
        if m:
            if m.group(1) not in checks:
                issues.append("L8 %s 的判据 %s 在 %s 中不存在（修复指引：改指向真实 check）"
                              % (owner, ref, VERIFY_REL))
        elif ref.startswith(_JUDGE_ASSERTION):
            if ref[len(_JUDGE_ASSERTION):] not in assertion_ids:
                issues.append("L8 %s 的判据 %s 未登记（修复指引：在 %s 补该断言）"
                              % (owner, ref, ASSERTIONS_REL))
        else:
            issues.append("L8 %s 的判据形式不合法：%s（修复指引：写成 checkN 或 assertion:<id>）"
                          % (owner, ref))

    # L9 豁免诚实
    for pattern in doc.get("derived") or []:
        if not _expand(root, [pattern]):
            issues.append("L9 derived 条目命中零文件：%s（修复指引：删掉该豁免或修正 glob）"
                          % pattern)

    # L10 生成区 == 实时渲染
    if not _exists(root, DOC_REL):
        issues.append("L10 缺阶梯文档 %s（修复指引：补件并跑 nf layers --write）" % DOC_REL)
    else:
        body = Path(root, DOC_REL).read_text(encoding="utf-8")
        got = _region_of(body)
        want = render_markdown(doc)
        if got is None:
            issues.append("L10 %s 缺生成区标记 %s / %s（修复指引：补标记后跑 nf layers --write）"
                          % (DOC_REL, MARK_BEGIN, MARK_END))
        elif got.strip() != want.strip():
            issues.append("L10 %s 生成区与实时渲染不一致（修复指引：跑 nf layers --write 刷新）"
                          % DOC_REL)
    return issues


def _region_of(text: str):
    """取生成区正文；缺标记返回 None。"""
    if MARK_BEGIN not in text or MARK_END not in text:
        return None
    return text.split(MARK_BEGIN, 1)[1].split(MARK_END, 1)[0]


def _table(rows: List[List[str]], header: List[str]) -> List[str]:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


def render_markdown(doc: Dict[str, Any]) -> str:
    """把阶梯真源渲染成 markdown 生成区（确定性；`nf layers --write` 写它）。"""
    lines: List[str] = []
    lines.append("### 抽象轴：四阶")
    lines.append("")
    rows = []
    for t in doc.get("tiers") or []:
        rows.append([
            "**%s**" % t.get("name"),
            "、".join("`%s`" % g for g in (t.get("source") or {}).get("globs") or []),
            "、".join("`%s`" % g for g in (t.get("interface") or {}).get("globs") or []),
            "、".join(t.get("judged_by") or []),
            "%s（%s）" % (t.get("status"), t.get("change_tier")),
        ])
    lines += _table(rows, ["阶", "真源面", "接口面（跨阶唯一可依赖）", "既有判据", "状态 / 变更档"])
    lines.append("")
    lines.append("### 资产阶五子级（同一格内异质，分开看代价）")
    lines.append("")
    rows = []
    for lv in doc.get("asset_levels") or []:
        rows.append(["**%s**" % lv.get("name"),
                     "、".join("`%s`" % g for g in lv.get("globs") or []),
                     "、".join(lv.get("judged_by") or []),
                     str(lv.get("note") or "")])
    lines += _table(rows, ["子级", "真源面", "既有判据", "口径"])
    lines.append("")
    lines.append("### 入口面（只登记角色，永不作为真源）")
    lines.append("")
    rows = []
    for sf in doc.get("surfaces") or []:
        rows.append(["**%s**" % sf.get("name"),
                     "、".join("`%s`" % e for e in sf.get("entries") or []),
                     "、".join(sf.get("serves") or []),
                     str(sf.get("note") or "")])
    lines += _table(rows, ["面", "入口件", "服务阶", "口径"])
    lines.append("")
    lines.append("### 验证纵切（贯穿四阶，不是层）")
    lines.append("")
    cross = doc.get("crosscut") or {}
    rows = []
    for comp in cross.get("components") or []:
        rows.append(["**%s**" % comp.get("id"), "`%s`" % comp.get("artifact"),
                     "、".join(comp.get("judged_by") or [])])
    lines += _table(rows, ["件", "落点", "既有判据"])
    lines.append("")
    lines.append("> 本区由 `nf layers --write` 渲染，禁止手改；真源 = `protocol/LAYERS.json`。")
    return "\n".join(lines)


def write_region(root: str = ".") -> str:
    """把渲染结果写回 `docs/layers.md` 生成区（LF 落盘，避免 Windows CRLF 漂移）。"""
    doc = load(root)
    path = Path(root) / DOC_REL
    if not path.is_file():
        raise ValueError("缺阶梯文档 %s（修复指引：先建文件并放 %s / %s 标记）"
                         % (DOC_REL, MARK_BEGIN, MARK_END))
    text = path.read_text(encoding="utf-8")
    if MARK_BEGIN not in text or MARK_END not in text:
        raise ValueError("%s 缺生成区标记（修复指引：先补 %s 与 %s 再写）"
                         % (DOC_REL, MARK_BEGIN, MARK_END))
    head, rest = text.split(MARK_BEGIN, 1)
    _old, tail = rest.split(MARK_END, 1)
    new = head + MARK_BEGIN + "\n" + render_markdown(doc) + "\n" + MARK_END + tail
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new)
    return DOC_REL


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """阶梯体检 → (issues, stats)；issues 空 = 阶梯自洽（并入 check27 纯度面）。"""
    try:
        doc = load(root)
    except ValueError as exc:
        return [str(exc)], {"tiers": 0, "asset_levels": 0, "surfaces": 0}
    issues = _rule_issues(root, doc)
    stats = {
        "tiers": len(doc.get("tiers") or []),
        "asset_levels": len(doc.get("asset_levels") or []),
        "surfaces": len(doc.get("surfaces") or []),
        "crosscut": len((doc.get("crosscut") or {}).get("components") or []),
        "rules": len(doc.get("rules") or []),
        "derived": len(doc.get("derived") or []),
    }
    return issues, stats
