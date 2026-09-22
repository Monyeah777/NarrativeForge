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
            fields = [t.split(":")[0].strip().strip("?")
                      for t in ph._split_top_level(m.group(1))]
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
    out: List[Dict[str, Any]] = []
    for pat in ("desktop/src/core/*.py", "scripts/*.py"):
        for p in sorted(Path(root).glob(pat)):
            lines = p.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if not re.match(r"\s*except\b", line):
                    continue
                nxt = [l.strip() for l in lines[i + 1:i + 3]]
                if not nxt or nxt[0] not in ("pass", "continue"):
                    continue
                prev = lines[i - 1].strip() if i else ""
                # 说明可以写在上一行，也可以内联在 except 行（仓库既有写法）
                if prev.startswith("#") or "#" in line.split(":", 1)[-1]:
                    continue
                out.append({"class": "silent-skip",
                            "file": os.path.relpath(p, root).replace(os.sep, "/"),
                            "line": i + 2,
                            "detail": "except → %s 且无说明" % nxt[0],
                            "snippet": "%s / %s" % (line.strip()[:80], nxt[0])})
    return out


def _quality_rule_candidates(root: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
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
           limit: int = 0, batch: int = 8, timeout: float = 120.0) -> Dict[str, Any]:
    """模型逐行判定 + 证据复核 → fixable / suspected 两张清单。"""
    rows = candidates(root)
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
            "fixable": [r for r in verdicts if r["verdict"] == "fixable"],
            "suspected": [r for r in verdicts if r["verdict"] == "suspected"],
            "model_meta": {"calibrated": adapter != "stub", "threshold": MODEL_THRESHOLD,
                           "note": "模型判定只用于排序；进修复清单必须另有确定性证据"}}


def summary(doc: Dict[str, Any]) -> str:
    return ("扫描 %d 行 · 可修 %d（有证据）· 模型怀疑无证据 %d · 分类 %s"
            % (doc.get("scanned", 0), len(doc.get("fixable") or []),
               len(doc.get("suspected") or []), doc.get("by_class")))
