"""缺口逐行审查：**决策模型逐行判 + 确定性规则复核**（双轨，缺一不进修复清单）。

为什么必须双轨：Laya 系是**未校准的分类器**（模型卡自述 ECE 0.213 偏自信），它只能
**排序与提示**，不能单独当"这是漏洞"的判决。故本模块的三段式是：

    候选行（机械预筛，行级可定位） → 模型逐行判定（noul 缺口 / score 严重度）
        → 证据复核（该行是否可由确定性规则证实） → fixable / suspected / not-a-gap

三类候选（全部行级、全部可证）：
  ① unharvestable-payload：正文 payload 含类型信息，但收割器不认该写法 → 证据收不到
  ② silent-skip：`except → pass/continue` 且无说明 → 静默吞错面
  ③ missing-quality-rule：规范件在名单却未登记数据契约（无 quality_rule/owner/freshness）
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core import decision_layer as dl

#: 模型判定阈值（仅用于排序与提示；进修复清单必须另有确定性证据）
MODEL_THRESHOLD = 0.5

#: 候选类别**单一真相源**（`--scope` 的取值面 + `--help` 的枚举文本都以此为准）。
#: 为什么单列：`--help` 曾写「unharvestable-payload / silent-skip / missing-quality-rule」，
#: 而实际会产出的还有 `payload-no-evidence`（真仓 26 条，占绝大多数）——列了不存在的、漏了
#: 最常出现的，读者照 help 选 `--scope` 永远看不到那一类（2026-10-01 内外口径对账）。
CLASSES = ("unharvestable-payload", "payload-no-evidence", "silent-skip",
           "missing-quality-rule")


def unknown_classes(classes) -> List[str]:
    """→ 不在 `CLASSES` 里的取值（供调用方 fail-closed：拼错的 scope 不许静默成空表）。"""
    return [c for c in classes if c not in CLASSES]


def _payload_candidates(root: str) -> List[Dict[str, Any]]:
    from core import conformance_scan as csc
    from core import payload_harvest as ph

    out: List[Dict[str, Any]] = []
    for doc in csc._module_docs(root):
        text = Path(doc).read_text(encoding="utf-8")
        found = ph.harvest_doc(text)
        known: set = set()
        for _ev, fmap in found.items():
            known |= {k for k, v in fmap.items() if v != "untyped"}
        rel = os.path.relpath(doc, root).replace(os.sep, "/")
        for i, line in enumerate(text.splitlines(), 1):
            m = re.search(r"payload\s*:\s*\{([^}]*)\}", line)
            if not m:
                continue
            tokens = ph._split_top_level(m.group(1))
            kind = ""
            missing = []
            for tok in tokens:
                name, typ = ph._field_type(tok)
                if not name or name in known:
                    continue
                missing.append(name)
                if typ and typ != "untyped":
                    kind = "unharvestable-payload"   # 正文有类型证据却收不到 → 真缺口
            if missing:
                if not kind:
                    # 只有字段名、无任何类型证据 → 属「缺证据」类（内容工作，不许猜类型）
                    kind = "payload-no-evidence"
                out.append({"class": kind, "file": rel, "line": i,
                            "detail": "未定型字段：%s" % "、".join(missing[:6]),
                            "snippet": line.strip()[:160]})
    return out


def _silent_skip_candidates(root: str) -> List[Dict[str, Any]]:
    """静默跳过候选——**口径与门禁 `test_silent_skip_reasons` 同一实现**（`core.silent_skip`）。

    2026-10-01 对账：本函数此前是**行扫版**（只认紧邻上一行或 except 行内联），比权威口径
    （窗口 = `try` 行及上三行 + handler 体行）窄 ⇒ 真仓报出 **8 条假缺口**（逐条核过：全是有
    理由的站点，理由写在内层 try 体那一行或 try 上行）。假缺口比漏报更伤——缺口清单是给人
    按条去修的。故改为调用单一真相源，两边不可能再漂。
    """
    from core import silent_skip as _ss
    out: List[Dict[str, Any]] = []
    rel_of = {}
    for p in sorted(Path(root).glob("desktop/src/core/*.py")) + sorted(
            Path(root).glob("scripts/*.py")):
        rel_of[os.path.normcase(str(p))] = os.path.relpath(p, root).replace(os.sep, "/")
    for key in sorted(rel_of):
        p = Path(key)
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        rel = rel_of[key]
        for try_line, h_line, kind, justified in _ss.silent_skips(text):
            if justified:
                continue
            body = lines[h_line] if h_line < len(lines) else kind
            out.append({"class": "silent-skip", "file": rel, "line": h_line + 1,
                        "detail": "except → %s 且无说明" % kind,
                        "snippet": "%s / %s" % (lines[h_line - 1].strip()[:80], body.strip()[:20])})
    return out


def _quality_rule_candidates(root: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not _quality_rule_inputs_present(root):
        # 缺协议件的根上本类候选**无从判定**——返回空表，由 `review()` 把缺件当 issue 报出；
        # 不许抛裸 FileNotFoundError（与 `payload_registry.scan` 同一纪律，见 F-5）。
        return out
    dc = json.loads(Path(root, "protocol/data_contracts.json").read_text(encoding="utf-8"))
    norm = json.loads(Path(root, "protocol/normative.json").read_text(encoding="utf-8"))
    registered = {c["artifact"] for c in dc.get("contracts") or []}
    for item in norm.get("normative") or []:
        path = str(item.get("path") or "")
        if path.endswith(".json") and path not in registered and not item.get("covered_by"):
            out.append({"class": "missing-quality-rule", "file": "protocol/normative.json",
                        "line": 0, "detail": "规范件未登记数据契约：%s" % path,
                        "snippet": path})
    return out


#: 本类候选要读的两个协议件（缺一即无从判定）。
_QUALITY_RULE_INPUTS = ("protocol/data_contracts.json", "protocol/normative.json")


def _quality_rule_inputs_present(root: str) -> bool:
    return all(Path(root, rel).is_file() for rel in _QUALITY_RULE_INPUTS)


def missing_inputs(root: str) -> List[str]:
    """本引擎**无法判定**所需的缺件（空表 = 输入齐备）。供 `review()` 如实报 issue。"""
    return [rel for rel in _QUALITY_RULE_INPUTS if not Path(root, rel).is_file()]


def candidates(root: str = ".", classes: Tuple[str, ...] = ()) -> List[Dict[str, Any]]:
    """行级候选（机械预筛，确定性排序）。"""
    rows = (_payload_candidates(root) + _silent_skip_candidates(root)
            + _quality_rule_candidates(root))
    if classes:
        rows = [r for r in rows if r["class"] in classes]
    return sorted(rows, key=lambda r: (r["class"], r["file"], r["line"]))


def evidence(root: str, row: Dict[str, Any]) -> str:
    """确定性复核：该类缺口能否由规则证实（空串 = 无证据 → 不进修复清单）。"""
    cls = row["class"]
    if cls == "unharvestable-payload":
        path = os.path.join(root, row["file"])
        if not os.path.isfile(path):
            return ""
        with open(path, encoding="utf-8") as fh:
            line = fh.read().splitlines()[row["line"] - 1]
        return ("可证：该 payload 行含字段/类型信息，但收割器 `harvest_doc` 只认 "
                "`event:`/`name:`/`publish:` 标记，此行未提供 → 类型证据不可收割"
                if "payload" in line else "")
    if cls == "silent-skip":
        with open(os.path.join(root, row["file"]), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        idx = row["line"] - 2
        if 0 <= idx < len(lines) and re.match(r"\s*except\b", lines[idx]):
            prev = lines[idx - 1].strip() if idx else ""
            if not prev.startswith("#") and "#" not in lines[idx].split(":", 1)[-1]:
                return "可证：except 后直接 pass/continue，且前一行无说明（静默吞错面）"
        return ""
    if cls == "missing-quality-rule":
        if not _quality_rule_inputs_present(root):
            return ""
        dc = json.loads(Path(root, "protocol/data_contracts.json").read_text(encoding="utf-8"))
        if row["snippet"] not in {c["artifact"] for c in dc.get("contracts") or []}:
            return ("可证：该规范件在 normative 名单却不在数据契约登记表"
                    "（无 quality_rule/owner/freshness）")
        return ""
    if cls == "payload-no-evidence":
        # 「缺证据」类：**不能靠改代码修**（类型要模块作者给），故只作挂账与统计，
        # 不进修复清单（返回空串 = 无"可修"证据）
        return ""
    return ""


def review(root: str = ".", adapter: str = "stub", endpoint: str = "",
           limit: int = 0, batch: int = 8, timeout: float = 120.0,
           classes: Tuple[str, ...] = ()) -> Dict[str, Any]:
    """模型逐行判定 + 证据复核 → fixable / suspected 两张清单。

    `classes` 限定候选类别（空 = 全类）——2026-10-01 修：CLI 的 `--scope` 此前**只是算了
    一个没人用的局部变量**，报告永远是全类（用户按类筛也拿到全量，属「文档写了却做不到」）。
    """
    missing = missing_inputs(root)
    rows = candidates(root, classes=classes)
    if limit:
        rows = rows[:limit]
    verdicts: List[Dict[str, Any]] = []
    for start in range(0, len(rows), max(1, batch)):
        chunk = rows[start:start + max(1, batch)]
        state = json.dumps([{"i": i, "class": r["class"], "file": r["file"],
                             "line": r["line"], "snippet": r["snippet"],
                             "detail": r["detail"]} for i, r in enumerate(chunk)],
                           ensure_ascii=False)
        questions: Dict[str, Any] = {}
        for i, r in enumerate(chunk):
            questions["gap:%d" % i] = {
                "type": "noul",
                "instructions": "第 %d 条（%s @ %s:%s）是否构成**可证缺口**：%s"
                                % (i, r["class"], r["file"], r["line"], r["detail"])}
            questions["sev:%d" % i] = {
                "type": "score", "levels": ["低", "中", "高"],
                "instructions": "第 %d 条若成立，严重度如何" % i}
        out = dl.decide({"state": state, "questions": questions},
                        adapter=adapter, endpoint=endpoint, timeout=timeout, root=root)
        for i, r in enumerate(chunk):
            row = dict(r)
            if out.get("status") == "ok":
                ans = out["answers"]
                row["model_gap_p"] = (ans.get("gap:%d" % i) or {}).get("p")
                row["model_severity"] = (ans.get("sev:%d" % i) or {}).get("value")
            else:
                row["model_gap_p"] = None
                row["model_severity"] = None
                row["model_error"] = out.get("reason")
            if adapter == "stub":
                # stub 无判定能力（规则式）：**不得当否决票**——本轮以证据为准
                row["model_gap_p"] = None
                row["model_severity"] = None
                row["model_note"] = "stub 无判定能力：本轮以确定性证据为准"
            row["evidence"] = evidence(root, row)
            if row["evidence"] and (row["model_gap_p"] is None
                                    or row["model_gap_p"] >= MODEL_THRESHOLD):
                row["verdict"] = "fixable"
            elif row["model_gap_p"] and not row["evidence"]:
                row["verdict"] = "suspected"
            else:
                row["verdict"] = "not-a-gap"
            verdicts.append(row)
    by_class: Dict[str, int] = {}
    for r in verdicts:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
    return {"schema": "nf-gap-review/1", "adapter": adapter, "scanned": len(verdicts),
            "by_class": by_class,
            # 缺件导致**某类候选无从判定**时如实报出（不许静默当「无缺口」）：
            "issues": (["缺 %s（修复指引：在 NF 仓库根运行本审查——缺失时 missing-quality-rule "
                        "一类候选无从判定）" % "、".join(missing)] if missing else []),
            "fixable": [r for r in verdicts if r["verdict"] == "fixable"],
            "suspected": [r for r in verdicts if r["verdict"] == "suspected"],
            "model_meta": {"calibrated": adapter != "stub", "threshold": MODEL_THRESHOLD,
                           "note": "模型判定只用于排序；进修复清单必须另有确定性证据"}}


def summary(doc: Dict[str, Any]) -> str:
    return ("扫描 %d 行 · 可修 %d（有证据）· 模型怀疑无证据 %d · 分类 %s"
            % (doc.get("scanned", 0), len(doc.get("fixable") or []),
               len(doc.get("suspected") or []), doc.get("by_class")))
