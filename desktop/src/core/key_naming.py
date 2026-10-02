"""资产键命名规范机检（资产密度面 · 顶层化目标 GAP-5）。

为什么需要：资产键（`nf-asset key="..."` 文件头 + `provenance.json` 的 `assets[].key`）
是**跨包寻址面**——下游按键取件、按键借阅。此前键只有「用到就算」的散点约束，
没有「形态合规 + 词表在册」的判据；键一旦各自为政，寻址面就会漂。

A. 口径（真源 = 声明件 `protocol/asset_keys.json`，不写死在代码里）：
- **形态**：键须匹配声明件里的 `pattern`（实测存量：9 键 / 长度 10–17 / 全大写蛇形）。
- **在册**：键须在声明件的 `keys` 词表里——未登记即 FAIL（新增键 = 改声明件 + 写明用途）。
- **回看**：词表登记但盘上从未出现的键 → WARN（词表腐化可见，不判死）。

纪律：纯标准库；只读扫描；错误消息带修复指引。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DECL_REL = "protocol/asset_keys.json"
#: 键采集面：文件头 nf-asset（域包资产 + 用户自定义资产）与 provenance 台账
HEADER_GLOBS = ("05_资产库/**/*.md", "community/*/assets/*.md")
PROVENANCE_GLOBS = ("05_资产库/**/provenance.json", "community/*/assets/provenance.json")


def declaration(root: str = ".") -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """读键词表声明 → (doc, issues)；缺失/不可解析/字段不全一律 fail-closed。"""
    p = Path(root) / DECL_REL
    if not p.is_file():
        return None, ["缺键词表声明 %s（修复指引：新建该声明件并写明 pattern 与 keys）" % DECL_REL]
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        return None, ["%s 不是合法 JSON：%s（修复指引：修好 JSON 语法）" % (DECL_REL, exc)]
    issues: List[str] = []
    if not str(doc.get("pattern") or "").strip():
        issues.append("%s 缺 pattern（修复指引：写明键的形态正则）" % DECL_REL)
    if not isinstance(doc.get("keys"), dict) or not doc["keys"]:
        issues.append("%s 缺 keys 词表（修复指引：把在册键逐条写进 keys）" % DECL_REL)
    return doc, issues


def collect(root: str = ".") -> Dict[str, List[str]]:
    """盘上按键采集 → {key: [仓库相对路径,...]}（文件头 + provenance 两源）。"""
    r = Path(root)
    found: Dict[str, List[str]] = {}
    for pat in HEADER_GLOBS:
        for p in sorted(r.glob(pat)):
            try:
                head = p.read_text(encoding="utf-8", errors="replace")[:600]
            except OSError:  # 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁另行报出（见 AUD-0016）
                continue
            m = re.search(r'nf-asset:\s*key="([^"]*)"', head)
            if m:
                found.setdefault(m.group(1), []).append(p.relative_to(r).as_posix())
    for pat in PROVENANCE_GLOBS:
        for p in sorted(r.glob(pat)):
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):  # 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁另行报出（见 AUD-0016）
                continue
            for a in (doc.get("assets") or []) if isinstance(doc, dict) else []:
                k = (a or {}).get("key")
                if k:
                    found.setdefault(str(k), []).append(p.relative_to(r).as_posix())
    return found


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：形态不合 / 未登记 = FAIL；词表未回看 = WARN。"""
    doc, issues = declaration(root)
    warns: List[str] = []
    found = collect(root)
    stats: Dict[str, Any] = {"keys_seen": len(found), "occurrences": sum(len(v) for v in found.values())}
    if doc is None or issues:
        stats.update({"registered": 0, "max_key_len": 0})
        return issues, warns, stats
    rx = re.compile(str(doc["pattern"]))
    registered = {str(k) for k in doc["keys"]}
    for key, files in sorted(found.items()):
        if not rx.match(key):
            issues.append("资产键形态不合规范：%r（%s）（修复指引：匹配 %s；示例：%s）"
                          % (key, files[0], doc["pattern"],
                             "、".join(sorted(registered)[:3])))
        elif key not in registered:
            issues.append("资产键未登记进词表：%r（%s）（修复指引：把该键与用途写进 %s 的 keys，"
                          "或改用既有键之一：%s）"
                          % (key, files[0], DECL_REL, "、".join(sorted(registered)[:5])))
    unused = sorted(registered - set(found))
    if unused:
        warns.append("词表登记但盘上未见：%s（修复指引：确认键仍在使用，或从 %s 移除）"
                     % ("、".join(unused), DECL_REL))
    stats.update({"registered": len(registered),
                  "max_key_len": max((len(k) for k in found), default=0)})
    return issues, warns, stats
