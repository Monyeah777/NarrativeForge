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
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core import conformance_scan as csc
from core import face_key as _fk
from core import atomic_write

# 导入闭包指纹：由调用方算（持久层不再反向依赖解析层，见 2026-09-29 拆环）

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
#: L6 的**文本预筛**：只把含入口面 import 的文件交给 AST（避免全量解析，见 _rule_issues）
_ENTRY_IMPORT_RE = re.compile(r"\b(?:import|from)\s+(?:nf|scripts)\b")

#: L6 的**逐件**事实缓存（键 = 该件正文的 sha256；值 = [(行号, 顶层模块名), …]）。
#: 依据（实测 2026-09-29）：L6 每次要把 255 份 `desktop/src/core/*.py`（约 2 MB）读进来再做 AST
#: walk，而「本件是否 import nf/scripts」只是**该件正文**的纯函数 ⇒ 与引擎无关的改动整笔可省。
_ENTRY_IMPORT_CACHE: Dict[str, List[Tuple[int, str]]] = {}
_ENTRY_IMPORT_CACHE_MAX = 4096


def _entry_imports(text: str) -> List[Tuple[int, str]]:
    """`text` 对入口面（`nf` / `scripts`）的 import 清单 `(行号, 顶层模块名)`；键即内容。

    等价性由 `test_layer_model.EntryImportFactTest` 守着：用**未缓存的参考实现**（原先那段
    「预筛 + `ast.parse` + `ast.walk`」原样搬进测试）在真仓库全部 core/*.py 上逐件比对，
    并在合成树上验证**顺序与重复项都不丢**（一件同时 import nf 与 scripts 必须出两条）。
    """
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    hit = _ENTRY_IMPORT_CACHE.get(key)
    if hit is not None:
        return hit
    out: List[Tuple[int, str]] = []
    if _ENTRY_IMPORT_RE.search(text):          # 文本预筛：绝大多数件不含入口 import
        try:
            tree = ast.parse(text)
        except (OSError, SyntaxError):
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module.split(".")[0]]
                else:
                    names = []
                for name in names:
                    if name in ENTRY_MODULE_NAMES:
                        out.append((node.lineno, name))
    if len(_ENTRY_IMPORT_CACHE) >= _ENTRY_IMPORT_CACHE_MAX:
        _ENTRY_IMPORT_CACHE.clear()
    _ENTRY_IMPORT_CACHE[key] = out
    return out


def _pattern_to_regex(pattern: str):
    """glob → **逐段**正则（`**` 跨目录、`*` 不跨、`?` 单字符）——只在本相对路径上匹配。"""
    out, i = [], 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                if i < len(pattern) and pattern[i] == "/":
                    i += 1
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
        i += 1
    return re.compile("^" + "".join(out) + "$")


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
                         % (DECL_REL, exc)) from exc
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


def _expand_many(root: str, globs, cache: dict) -> set:
    """同一次扫描内按 pattern 缓存展开（**每个子树只走一次文件系统**）。

    效率（实测）：`_rule_issues` 的 L1/L2/L3 会重复展开同一批 glob（约 10.5k 次 `stat`
    全花在这里）。两层缓存：① 每个子树的文件清单只 `os.walk` 一次；② 每个 pattern 的
    匹配结果复用。缓存是**每次扫描一份**（不是模块级），所以临时目录/被改动的树不会被
    陈旧结果污染（单测反复扫同一路径也不受影响）。等价性由 `_expand`（参考实现）兜底：
    字符类等 Path.glob 专有语义直接回退，其余由 `test_layer_model` 的等价断言守住。
    """
    base = Path(root)
    out = set()
    for pattern in globs or []:
        key = ("pat", str(pattern))
        if key not in cache:
            cache[key] = _expand_one(base, str(pattern), str(root), cache)
        out |= cache[key]
    return out


def _is_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?[")


def _glob_root(pattern: str) -> str:
    """pattern 中**通配符之前**的固定目录前缀（无则 `.`）——用于「同子树只走一次」。"""
    parts = str(pattern).split("/")
    keep: List[str] = []
    for part in parts[:-1] if len(parts) > 1 else []:
        if _is_glob(part):
            break
        keep.append(part)
    return "/".join(keep) if keep else "."


def _walk_files(base: Path, rel_root: str) -> List[str]:
    """收集 rel_root 子树下全部文件的**仓库相对 posix 路径**（走共享子树索引）。

    依据（实测）：本函数原本自己 `os.walk`，而一次 `evaluate` 里 `community` 这棵树被
    layer_model、两个指纹、若干扫描器**各走了一遍**——一次 evaluate 共建了 5403 个
    `os.scandir`，光建扫描器就 687 ms。改走 `conformance_scan.tree_files`（作用域内按目录
    记忆、出口即清）后同一棵树只走一遍，其他调用方直接复用清单。
    """
    from core import conformance_scan as _csc
    return _csc.tree_files(str(base), "" if rel_root in (".", "") else rel_root)


def _expand_one(base: Path, pattern: str, ref_root: str, cache: dict) -> set:
    """单个 glob 的等价快路径：固定件直接探在不在，通配件走子树索引 + 正则。"""
    if not _is_glob(pattern):
        return {pattern} if (base / pattern).is_file() else set()
    if "[" in pattern:                    # 字符类等 Path.glob 专有语义 → 回退参考实现
        return _expand(ref_root, [pattern])
    rel_root = _glob_root(pattern)
    key = ("tree", rel_root)
    if key not in cache:
        cache[key] = _walk_files(base, rel_root)
    rx = _pattern_to_regex(pattern)
    return {rel for rel in cache[key] if rx.match(rel)}


def _exists(root: str, rel: str) -> bool:
    return (Path(root) / str(rel)).exists()


def _derived_files(root: str, doc: Dict[str, Any], cache: Optional[dict] = None) -> set:
    if cache is None:
        return _expand(root, doc.get("derived") or [])
    return _expand_many(root, doc.get("derived") or [], cache)


def tier_faces(root: str, doc: Dict[str, Any]) -> Dict[str, set]:
    """每阶真源面（已扣除派生物）→ {tier_id: {rel, …}}。"""
    cache: dict = {}
    derived = _derived_files(root, doc, cache)
    out = {}
    for tier in doc.get("tiers") or []:
        out[str(tier.get("id"))] = \
            _expand_many(root, (tier.get("source") or {}).get("globs"), cache) - derived
    return out


def _rule_issues(root: str, doc: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    tiers = doc.get("tiers") or []
    tier_ids = [str(t.get("id")) for t in tiers]
    cache: dict = {}                       # 本次扫描的 glob 展开缓存（见 _expand_many）
    derived = _derived_files(root, doc, cache)

    # L1 真源在位
    for tier in tiers:
        face = _expand_many(root, (tier.get("source") or {}).get("globs"), cache)
        if not (tier.get("source") or {}).get("globs"):
            issues.append("L1 阶 %s 未声明真源面（修复指引：在 source.globs 写明真源落点）"
                          % tier.get("id"))
        elif not face:
            issues.append("L1 阶 %s 的真源面展开为空：%s（修复指引：核对 globs 与实况）"
                          % (tier.get("id"), (tier.get("source") or {}).get("globs")))
    for lv in doc.get("asset_levels") or []:
        if not _expand_many(root, lv.get("globs"), cache):
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
    faces = {tid: _expand_many(root, (t.get("source") or {}).get("globs"), cache) - derived
             for t, tid in zip(tiers, tier_ids, strict=True)}
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
        iface = _expand_many(root, (tier.get("interface") or {}).get("globs"), cache)
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
    for rel in sorted(_expand_many(root, ["desktop/src/core/*.py"], cache)):
        try:
            src = csc.read_text_cached(Path(root) / rel)   # 与 purity 的 core/*.py 读同一份语料
        except OSError:
            continue
        # 事实按**正文**缓存（`_entry_imports`）：文本预筛 + AST 只在「这一件没算过」时付。
        for lineno, name in _entry_imports(src):
            issues.append("L6 引擎阶反向 import 入口面件：%s:%d import %s"
                          "（修复指引：入口可替换，core 不得依赖它——改由 CLI 层注入）"
                          % (rel, lineno, name))

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
    checks = set(_CHECK_DEF.findall(csc.read_text_cached(Path(root, VERIFY_REL)))) \
        if _exists(root, VERIFY_REL) else set()
    a_path = Path(root, ASSERTIONS_REL)
    assertion_ids = set()
    if a_path.is_file():
        assertion_ids = {str(a.get("id")) for a in
                         (json.loads(csc.read_text_cached(a_path))
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
        # 走**快路径**（子树索引 + 正则）：等价性由 `test_expand_fast_path_matches_reference` 逐 pattern
        # 守着；原先是逐 pattern 的 `Path.glob`（本仓 6 条 derived），与别处的展开两套口径（实测）。
        if not _expand_many(root, [pattern], cache):
            issues.append("L9 derived 条目命中零文件：%s（修复指引：删掉该豁免或修正 glob）"
                          % pattern)

    # L10 生成区 == 实时渲染
    if not _exists(root, DOC_REL):
        issues.append("L10 缺阶梯文档 %s（修复指引：补件并跑 nf layers --write）" % DOC_REL)
    else:
        body = csc.read_text_cached(Path(root, DOC_REL))
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
    # 原子写（2026-09-30 收口）：`docs/layers.md` 是**活文档**，且 `layer_model` 自己会把
    # 它当常驻语料读（L8/L10）——裸 `open(w)` 下并发读者可能读到半截正文。
    atomic_write.write_text(path, new)
    return DOC_REL


def patterns(root: str = ".") -> Tuple[str, ...]:
    """`scan()` 的输入面：**由阶梯声明动态给出**（各阶真源面 + 资产子级 + 纵切件 + 派生物），
    外加声明件本身与判据脚本。

    动态取是安全的：声明件（`protocol/LAYERS.json`）本身就在面内 ⇒ 声明一变指纹必变；声明新列的
    根即使一台空，结果也会变（「真源面须存在且非空」）——而「声明变了」这一点同样已经在指纹里。
    """
    pats = list(_READ_FACE)          # 真读面先入面（含 L6 的 core/*.py 与断言集——后者此前漏申报）
    try:
        doc = load(root)
    except ValueError:
        return tuple(pats)
    for tier in doc.get("tiers") or []:
        pats += [str(g) for g in ((tier.get("source") or {}).get("globs") or [])]
    for level in doc.get("asset_levels") or []:
        pats += [str(g) for g in (level.get("globs") or [])]
    for comp in ((doc.get("crosscut") or {}).get("components") or []):
        if comp.get("artifact"):
            pats.append(str(comp["artifact"]))
    pats += [str(p) for p in (doc.get("derived") or [])]
    out = []
    for pat in pats:
        pat = pat.strip()
        if not pat:
            continue
        # 声明里的「目录」写成不带通配的路径（如 `results/audit`）：按**它下面的件**入面，
        # 否则 `iter_files` 会把它当成一个叫 audit 的**文件**、什么都匹配不到（面会缺口）。
        if not any(ch in pat for ch in "*?[" ) and os.path.isdir(os.path.join(str(root), pat)):
            pat = pat.rstrip("/") + "/**/*"
        out.append(pat)
    return tuple(dict.fromkeys(out))


#: 规则**真读**的件（实测 130 件）；其余申报件只做**枚举级**判断（「存在且非空」）⇒ 键分两段取
#: （内容 + 成员，见 `core.face_key`）：L6 的 core/*.py + 声明 + 断言集 + 判据脚本 + 渲染投影。
_READ_FACE = ("desktop/src/core/*.py", "protocol/LAYERS.json", "protocol/assertions.json",
              "verify.sh", "docs/layers.md")


def face_fingerprint(root: str = ".") -> str:
    """`scan()` 的缓存键：**真读面内容 + 申报面成员集**（实测依据与两段语义见 `core.face_key`）。

    `purity_scan` 拿它组合「自有面 + 本面」的键并把值传给 `scan(_fp=...)`：同一张面只枚举一次。
    """
    return _fk.fingerprint(root, _READ_FACE, patterns(root))


def scan(root: str = ".", _fp: Optional[str] = None) -> Tuple[List[str], Dict[str, Any]]:
    """阶梯体检 → (issues, stats)；issues 空 = 阶梯自洽（并入 check27 纯度面）。

    派生结果按**输入内容指纹**缓存（输入面见 `patterns()`：声明列了整棵语料，面很宽）。
    **冷进程也走这层**（2026-09-29 改）：过去写「只在常驻语料层在位时才缓存」，理由是「冷进程里取
    指纹比直接算更贵」——实测不成立（冷进程本来就要为别的站点读整棵语料，摘要共享 ⇒ 指纹近乎白拿）；
    实测数字见 `quality_depth_scan.scan`。
    """
    return csc.memo_pair("layer-model", patterns(root), _scan_impl, root,
                         code_modules=("core.layer_model",), fp=_fp)


def _scan_impl(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """真算（未命中缓存时走这里）。"""
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
