"""构建回路（决策层驱动）：**决策模型挑活，生成式 worker 落笔，NF 门禁验收**。

作者意图（2026-09-22）：「让这些模型替我干活，来构建 NF」。诚实边界先写在最前：

- Laya 是**编码器分类模型**（ModernBERT-large + 决策头）、Open-Jev 是**非自回归 + 决策头**——
  **两者都不生成代码或正文**。它们能替人干的是**决策类活**：挑下一个工作项、判改动风险、
  定某件事能不能在不碰回执锚定件的条件下做、给候选排序；
- 真正的改动（写模块正文、补类型证据、改代码）必须由**生成式 worker**（人 / Codex / 生成式模型）
  完成——这一层把「决策」与「落笔」分开，避免把分类器当成会写代码的东西；
- 决策层与 worker 都在**门禁之外**；验收只认 `verify.sh` / `nf conformance`。

回路三步：
    ① `plan()`  读**公开声明真源**（type_backlog / pipeline_advisory）→ 组类型化问题 → 问决策层
                → 产出**工单**（chosen item + 风险 + 是否可安全做 + 完成判据 + 该跑的验收命令）
    ② 落笔      worker 按工单改仓库（决策模型只提供选择，不提供内容）
    ③ `close()` 回收结果（门禁结论 + 是否落地），写回内部档案（计划类产品内部消化，不入公开仓）

为什么工单只落内部档案：`STRATEGY §四` 规定计划/过程类产物内部消化，公开仓只承载
结果（代码 + 收口注记 + audit）。本模块因此**只读公开声明、只写 `.rivet/`**。
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Tuple

from core import decision_layer as dl

#: 待办真源（公开声明件 → 工作项）。顺序即稳定排序键（确定性优先于「看起来聪明」）
SOURCES = (
    ("type-backlog", "protocol/type_backlog.json"),
    ("pipeline-advisory", "protocol/pipeline_advisory.json"),
)
#: 「扩展 / 深化 / 创新」三族（**机械派生**：每条都带可核验的缺口事实，不靠想象）
FAMILIES = ("extend", "deepen", "innovate")
ORDER_DIR = ".rivet/private_archive/work_orders"
#: 工单必须落在这个前缀下（内部档案）；落到别处即 FAIL
ARCHIVE_PREFIX = ".rivet/"


def _read(root: str, rel: str) -> Dict[str, Any]:
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return {}
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def state(root: str = ".") -> Dict[str, Any]:
    """回路状态快照（只读公开声明，确定性）。"""
    backlog = _read(root, "protocol/type_backlog.json")
    advisory = _read(root, "protocol/pipeline_advisory.json")
    decl = dl.load_decl(root)
    return {
        "untyped_fields": int(backlog.get("count") or len(backlog.get("fields") or [])),
        "advisories": int(advisory.get("count") or len(advisory.get("items") or [])),
        "advisory_by_category": dict(advisory.get("counts") or {}),
        "candidates_pulled": [c.get("id") for c in (decl.get("candidates") or [])
                              if c.get("pulled")],
        "adapters": dl.adapter_ids(root),
    }


def items(root: str = ".", limit: int = 0, source: str = "") -> List[Dict[str, Any]]:
    """工作项清单（来自公开声明件；每条带 id/kind/title/detail/落点提示/完成判据）。"""
    out: List[Dict[str, Any]] = []
    backlog = _read(root, "protocol/type_backlog.json")
    for i, f in enumerate(backlog.get("fields") or [], 1):
        ev, fld = str(f.get("event") or ""), str(f.get("field") or "")
        out.append({
            "id": "TB-%03d:%s.%s" % (i, ev, fld),
            "source": "type-backlog", "kind": "type-evidence",
            "title": "补类型证据：%s.%s" % (ev, fld),
            "detail": str(f.get("note") or "事件载荷字段类型待核"),
            "where_hint": "事件发布方模块正文（%s 的载荷表）" % (ev or "?"),
            "done_when": ["模块正文补出该字段的类型证据", "nf lint / verify 全绿"],
        })
    advisory = _read(root, "protocol/pipeline_advisory.json")
    for i, a in enumerate(advisory.get("items") or [], 1):
        out.append({
            "id": "PA-%03d:%s" % (i, str(a.get("pipeline") or "?")),
            "source": "pipeline-advisory", "kind": "advisory-shrink",
            "title": "收敛 advisory：%s（%s）" % (str(a.get("category") or "?"),
                                                 str(a.get("pipeline") or "?")),
            "detail": str(a.get("detail") or ""),
            "where_hint": "对应管线声明与所涉模块的 references/事件声明",
            "done_when": ["该类别计数下降或转为在册机制", "nf pipeline dryrun --all 零 hard"],
        })
    out += capability_gaps(root)
    if source:
        out = [it for it in out if it["source"] == source]
    return out[:limit] if limit else out


def capability_gaps(root: str = ".") -> List[Dict[str, Any]]:
    """现有功能的延伸/深化/创新候选（**全部机械派生**，每条附缺口事实）。

    设计纪律：候选不是"我觉得可以做 XXX"，而是**仓库状态里可核验的缺口**——
    ① 已有只读面未接 MCP（extend）；② 同一份事实在两处声明却无一致性判据（deepen，
    实例：CLI 可选值 ↔ 声明件曾两次漏同步）；③ 两个既有面之间尚未接线（innovate）。
    """
    import re
    out: List[Dict[str, Any]] = []

    # ① extend：只读治理面未接 MCP
    nf_path = os.path.join(root, "scripts", "nf.py")
    cmds: List[str] = []
    if os.path.isfile(nf_path):
        with open(nf_path, encoding="utf-8") as fh:
            cmds = sorted(set(re.findall(r'sub\.add_parser\(\s*"([a-z0-9-]+)"', fh.read())))
    try:
        from core import mcp_runtime as _mcp
        tools = {t["name"] for t in _mcp.TOOL_DEFS}
    except Exception:  # pragma: no cover
        tools = set()
    readonly_governance = [c for c in cmds if c in (
        "decisions", "handover", "postmortem", "audit", "transparency", "score",
        "conformance", "assertions", "model", "cognition", "events", "rfc",
        "endpoint", "interop", "workloop", "decide", "explain", "related",
        "who-refers", "impact")]
    covered = {"receipts", "endpoint", "driver", "patterns", "knowledge"}
    missing = [c for c in readonly_governance if c not in covered]
    if missing:
        out.append({
            "id": "CAP-EXTEND-MCP-READONLY",
            "source": "capability-gaps", "family": "extend",
            "kind": "capability-extension",
            "title": "把只读治理面接入 MCP（当前 %d 个只读面未暴露，工具仅 %d 个）"
                     % (len(missing), len(tools)),
            "detail": "未接 MCP 的只读面：%s" % "、".join(missing[:8]),
            "where_hint": "core/mcp_runtime.py（TOOL_DEFS + 只读白名单）+ protocol/"
                          "mcp_package.json 登记",
            "done_when": ["新增工具逐名与实现一致", "check33 新面扫描含逐名一致断言",
                          "MCP 工具仍全只读（无写路径）"],
        })

    # ② deepen：同一事实两处声明、却无「一致性判据」的实例（先报已证实的那个）
    interop_decl: List[str] = []
    try:
        from core import interop_export as _ie
        interop_decl = sorted(_ie.KINDS)
    except Exception:  # pragma: no cover —— 导出面声明不可读：本轮不产 innovate 候选（不静默：候选缺失即结果为少一条）  # nosec B110/B112 —— 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁与 AUD-0016 静默跳过清单另行报出
        pass
    cli_kinds: List[str] = []
    if cmds:
        with open(nf_path, encoding="utf-8") as fh:
            text = fh.read()
        m = re.search(r'add_argument\(\s*"--kind",\s*default="[a-z]+",\s*choices=\[([^\]]+)\]',
                      text)
        if m:
            cli_kinds = sorted(re.findall(r'"([a-z]+)"', m.group(1)))
    if interop_decl and cli_kinds and cli_kinds != interop_decl:
        out.append({
            "id": "CAP-DEEPEN-DECL-CONSISTENCY",
            "source": "capability-gaps", "family": "deepen",
            "kind": "judgement-deepening",
            "title": "加「CLI 可选值 ↔ 声明件」一致性判据（已抓到实例：缺 %s）"
                     % "、".join(sorted(set(interop_decl) - set(cli_kinds))),
            "detail": "interop CLI kinds=%s / 导出面声明=%s —— 同类漏同步此前已发生一次"
                      "（slsa/a2a），属可机检的判据缺口" % (cli_kinds, interop_decl),
            "where_hint": "scripts/nf.py 的 choices + core/interop_export.KINDS（判据落 check33）",
            "done_when": ["修掉实例差异", "新增通用判据：CLI choices ⊆ 声明件（或相等）",
                          "负例单测：故意漏一个 kind 应被抓"],
        })

    # ③ innovate：两个既有面之间尚未接线（**接线完成即自动撤单**——候选池必须反映当前状态）
    if "decisions" not in interop_decl:
        out.append({
            "id": "CAP-INNOVATE-DECISION-INTEROP",
            "source": "capability-gaps", "family": "innovate",
            "kind": "capability-innovation",
            "title": "把决策层/工单面接进互操作导出（决策可被外部工具链读）",
            "detail": "现状：decision_layer.json 与 workloop 工单都在仓内，互操作导出面"
                      "（%d 面）尚无「决策面」投影；外部工具链读不到「谁按什么概率决定了什么」"
                      % len(interop_decl),
            "where_hint": "core/interop_export.py 新增 kind（纯派生自 decision_layer.json + 公开裁决索引）",
            "done_when": ["新导出面纯派生（不改真源）",
                          "外部 schema 校验口径成立或如实记 no-schema",
                          "check33 入仓面逐字节一致"],
        })
    return out


def questions(root: str = ".", top: int = 5, source: str = "") -> Dict[str, Any]:
    """组类型化问题：挑活（choice）+ 每项风险（score）+ 每项「能否安全做」（noul）。"""
    picked = items(root, limit=max(1, top), source=source)
    q: Dict[str, Any] = {}
    if not picked:
        return q
    q["family"] = {"type": "choice",
                   "instructions": "这一轮要哪一类工作（extend 加面 / deepen 深化判据 / "
                                   "innovate 新组合）",
                   "options": list(FAMILIES)}
    q["next_item"] = {"type": "choice",
                      "instructions": "选下一个要推进的工作项（优先小改动面、可门禁验收）",
                      "options": [it["id"] for it in picked]}
    for it in picked:
        q["risk:%s" % it["id"]] = {"type": "score", "levels": ["低", "中", "高"],
                                   "instructions": "预估改动面风险：%s" % it["title"]}
        q["gate_safe:%s" % it["id"]] = {
            "type": "noul",
            "true_hints": ["正文", "注释", "文档", "提示"],
            "instructions": "是否可在不触碰回执锚定件的条件下完成：%s" % it["title"]}
    return q


def _order_id(chosen: str, st: Dict[str, Any]) -> str:
    payload = json.dumps({"chosen": chosen, "state": st}, ensure_ascii=False,
                         sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "WO-%s" % hashlib.sha256(payload).hexdigest()[:12]


def plan(root: str = ".", adapter: str = "stub", top: int = 5, endpoint: str = "",
         timeout: float = 30.0, source: str = "") -> Dict[str, Any]:
    """回路第一步：问决策层 → 产出工单（**只读声明，不落笔内容**）。"""
    st = state(root)
    picked = items(root, limit=max(1, top), source=source)
    qs = questions(root, top=top, source=source)
    if not qs:
        return {"schema": "nf-workorder/1", "status": "empty",
                "reason": "公开声明里没有待办项（type_backlog / pipeline_advisory 均为空）",
                "state": st}
    # 决策请求必须**自带证据**：这些模型只对给定 state 作答，不给候选正文它们无从判断
    state_text = json.dumps({
        "facts": st,
        "candidates": [{"id": it["id"], "title": it["title"], "detail": it["detail"],
                        "where": it["where_hint"]} for it in picked],
    }, ensure_ascii=False, sort_keys=True)
    req = {"state": state_text, "questions": qs}
    out = dl.decide(req, adapter=adapter, endpoint=endpoint, timeout=timeout, root=root)
    if out.get("status") != "ok":
        return {"schema": "nf-workorder/1", "status": "abstained",
                "reason": out.get("reason"), "state": st,
                "decision_meta": out.get("meta")}
    answers = out["answers"]
    chosen_id = answers["next_item"]["argmax"]
    chosen = next(it for it in items(root, source=source) if it["id"] == chosen_id)
    risk = answers.get("risk:%s" % chosen_id) or {}
    safe = answers.get("gate_safe:%s" % chosen_id) or {}
    return {
        "schema": "nf-workorder/1", "status": "ok",
        "order_id": _order_id(chosen_id, st),
        "state": st,
        "decision": {"adapter": out["meta"].get("adapter"),
                     "calibrated": out["meta"].get("calibrated"),
                     "non_gate": out["meta"].get("non_gate"),
                     "next_item_prob": answers["next_item"]["probs"][
                         answers["next_item"]["options"].index(chosen_id)],
                     "risk_level": risk.get("value"), "risk_probs": risk.get("probs"),
                     "gate_safe_p": safe.get("p"),
                     "note": "决策层只给选择与概率；**它不写内容**"},
        "chosen": chosen,
        "worker_brief": {
            "goal": chosen["title"],
            "item": chosen["id"],
            "evidence": chosen["detail"],
            "where": chosen["where_hint"],
            "done_when": chosen["done_when"],
            "accept": "bash verify.sh（全绿）+ nf conformance（conformant）",
            "worker_role": "生成式 worker（人 / Codex / 生成式模型）——决策模型不落笔",
        },
    }


def write_order(root: str, doc: Dict[str, Any]) -> str:
    """工单落**内部档案**（计划类产品内部消化；公开仓只收结果）。"""
    if doc.get("status") != "ok":
        raise ValueError("只落 status=ok 的工单（修复指引：先跑 nf workloop 拿到决定）")
    rel = "%s/%s.json" % (ORDER_DIR, doc["order_id"])
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    return rel


def render_brief(doc: Dict[str, Any], closed: Dict[str, Any] = None) -> str:
    """人读工单（给 worker 执行用）。"""
    if doc.get("status") != "ok":
        return "工单未成形：%s" % doc.get("reason")
    b = doc["worker_brief"]
    lines = ["# 工单 %s" % doc["order_id"], "",
             "- 目标：%s" % b["goal"],
             "- 条目：`%s`（%s）" % (b["item"], doc["chosen"]["source"]),
             "- 证据/背景：%s" % b["evidence"],
             "- 落点提示：%s" % b["where"],
             "- 完成判据：%s" % "；".join(b["done_when"]),
             "- 验收：%s" % b["accept"],
             "- 决策层（只选择、不写内容）：%s · 风险期望 %.2f · gate_safe=%.2f"
             % (doc["decision"]["adapter"], doc["decision"]["risk_level"] or 0.0,
                doc["decision"]["gate_safe_p"] or 0.0), ""]
    if closed:
        lines += ["## 收口", "- 结果：%s" % closed.get("outcome"),
                  "- 门禁：%s" % closed.get("gate"), "- 说明：%s" % closed.get("note", "")]
    return "\n".join(lines)


def close(root: str, order_id: str, outcome: str, gate: str, note: str = "") -> str:
    """回路第三步：回收结果 → 内部档案记档（不改公开仓）。"""
    rec = {"schema": "nf-workorder-close/1", "order_id": order_id,
           "outcome": outcome, "gate": gate, "note": note}
    rel = "%s/%s.close.json" % (ORDER_DIR, order_id)
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    return rel


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """回路体检（离线）：待办真源可读 + 问题形状合法 + 工单只落内部档案 + stub 确定性。"""
    issues: List[str] = []
    st = state(root)
    all_items = items(root)
    if not all_items:
        issues.append("待办真源为空（%s 均无条目）——回路无活可挑"
                      % "、".join(rel for _n, rel in SOURCES))
    ids = [it["id"] for it in all_items]
    if len(set(ids)) != len(ids):
        issues.append("工作项 id 重复（%d 项 / %d 唯一）——选项重复会让决策无意义"
                      % (len(ids), len(set(ids))))
    for it in all_items[:5]:
        for k in ("id", "kind", "title", "detail", "where_hint", "done_when"):
            if not it.get(k):
                issues.append("工作项 %s 缺字段 %s（工单须能自述怎么干、怎么验收）"
                              % (it.get("id"), k))
    qs = questions(root, top=3)
    if not qs:
        issues.append("问题面为空（无法向决策层提问）")
    else:
        bad = dl.request_issue({"state": "x", "questions": qs})
        if bad:
            issues.append("回路产出的问题不合规：%s" % bad)
    p1 = plan(root, adapter="stub", top=3)
    p2 = plan(root, adapter="stub", top=3)
    if p1 != p2:
        issues.append("stub 工单非确定性（同输入两次结果不一致）")
    if p1.get("status") != "ok" and all_items:
        issues.append("stub 工单未成形：%s" % p1.get("reason"))
    if p1.get("status") == "ok":
        if p1["chosen"]["id"] not in [it["id"] for it in all_items[:3]]:
            issues.append("工单所选工作项不在候选集内（%s）" % p1["chosen"]["id"])
        brief = p1["worker_brief"]
        for k in ("goal", "done_when", "accept", "worker_role"):
            if not brief.get(k):
                issues.append("工单缺 %s（缺判据的工单等于没有验收）" % k)
    if not ORDER_DIR.startswith(ARCHIVE_PREFIX):
        issues.append("工单目录不在内部档案前缀 %s 下（计划类产品不得入公开仓）"
                      % ARCHIVE_PREFIX)
    stats = {"items": len(all_items), "untyped": st["untyped_fields"],
             "advisories": st["advisories"], "adapters": len(st["adapters"]),
             "pulled_candidates": st["candidates_pulled"],
             "stub_order": (p1.get("order_id") if p1.get("status") == "ok" else ""),
             "issues": len(issues)}
    return issues, stats


def summary(stats: Dict[str, Any]) -> str:
    return ("待办 %(items)d 项（未定型字段 %(untyped)d · advisory %(advisories)d）· "
            "适配器 %(adapters)d · 已拉取候选 %(pulled_candidates)s · stub 工单 %(stub_order)s"
            % stats)
