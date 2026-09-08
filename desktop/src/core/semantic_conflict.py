"""v2.8.0 波C C3：跨模块语义矛盾扫描（41 规划——编译期矛盾拦截）。

语义级自洽校验（补 check15/21 结构自洽之上的语义空白），testcase 驱动，
首测范围 = 技术文档域包内自检（M90/M97/M98 互引链 + 与官方核心边界）：

R1 事件契约断链：模块 machine_contract 订阅的事件在全库（04 + community）
   无任何 machine_contract 发布 → 订阅即死契约（真实例：M90 intent_received /
   M97 term_conflict_detected / M98 doc_delta_committed 曾断链，已随 C3 修复）。
R2 挂载点漂移：模块头元信息「挂载点：Pxx」与 machine_contract.layer 不一致。
R3 类别漂移：模块头元信息「类别」与 machine_contract.category 不一致。

纪律：只读扫描 + 报告；yaml 按文本片段解析（零第三方依赖红线保持）。
"""
from __future__ import annotations

import os
import re

from core import module_lifecycle as ml

_YAML_FENCE = re.compile(r"^```[ \t]*[Yy][Aa][Mm][Ll]?[ \t]*$", re.M)
_EVENT_LIST = re.compile(r"^\s*(publish|subscribe):\s*\[(.*?)\]\s*$", re.M)
_MOUNT_P = re.compile(r"(P\d{2,4})")

#: R1 语义作用域（41 §四.2 首测范围 = techdoc 域包自检链）
TECHDOC_IDS = {"M90", "M97", "M98"}


def _contract(text: str) -> str:
    """返回含 machine_contract 的 yaml 代码块文本（无则空串）。"""
    fences = []
    in_fence = False
    buf = []
    for ln in text.splitlines():
        if not in_fence:
            if _YAML_FENCE.match(ln):
                in_fence = True
                buf = []
        else:
            if ln.strip().startswith("```"):
                in_fence = False
                fences.append("\n".join(buf))
            else:
                buf.append(ln)
    for f in fences:
        if re.search(r"(?m)^\s*machine_contract\s*:", f):
            return f
    return ""


def _fence_field(fence: str, field: str) -> str:
    m = re.search(r"(?m)^\s*%s:\s*(.+?)\s*$" % re.escape(field), fence)
    return m.group(1).strip() if m else ""


def _events_of(fence: str) -> dict:
    out = {"publish": [], "subscribe": []}
    for m in _EVENT_LIST.finditer(fence):
        kind = m.group(1)
        for e in re.split(r"[,\s]+", m.group(2).strip()):
            if e:
                out[kind].append(e)
    return out


def _module_info(root: str, rel: str) -> dict:
    text = ml.read_text(root, rel)
    fence = _contract(text)
    mid = ml.module_id_from_text(text)
    meta = ml.parse_meta(text)
    events = _events_of(fence)
    return {
        "id": mid,
        "file": rel,
        "meta": meta,
        "layer": _fence_field(fence, "layer"),
        "category": _fence_field(fence, "category"),
        "publish": events["publish"],
        "subscribe": events["subscribe"],
    }


def scan(root: str = ".") -> tuple:
    """check26 语义：语义级矛盾扫描 → (issues, stats)。"""
    infos = []
    for rel in ml.iter_module_files(root):
        info = _module_info(root, rel)
        if info["id"]:
            infos.append(info)
    publishers = {}
    for info in infos:
        for e in info["publish"]:
            publishers.setdefault(e, []).append(info["id"])
    issues = []
    for info in infos:
        mid = info["id"]
        # R1：techdoc 链订阅事件必须存在 machine_contract 发布方
        if mid in TECHDOC_IDS:
            for e in info["subscribe"]:
                if e not in publishers:
                    issues.append("%s 订阅事件 %s 无任何模块 machine_contract 发布（事件契约断链）"
                                  % (info["file"], e))
        # R2：挂载点 vs contract layer 漂移
        mount = _MOUNT_P.search(info["meta"].get("挂载点", ""))
        mp = mount.group(1) if mount else ""
        if mp and info["layer"] and mp != info["layer"]:
            issues.append("%s 头挂载点 %s ≠ machine_contract.layer %s（挂载点漂移）"
                          % (info["file"], mp, info["layer"]))
        # R3：类别 meta vs contract category 漂移
        cat_meta = re.split(r"[｜|]", info["meta"].get("类别", ""), maxsplit=1)[0].strip()
        if cat_meta and info["category"] and cat_meta != info["category"]:
            issues.append("%s 头类别 %s ≠ machine_contract.category %s（类别漂移）"
                          % (info["file"], cat_meta, info["category"]))
    stats = {
        "modules": len(infos),
        "publishers": len(publishers),
        "techdoc_chain": sum(1 for i in infos if i["id"] in TECHDOC_IDS),
    }
    return issues, stats
