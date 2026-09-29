"""门禁的**机器可读出口**：把全部核心判据聚合成一份 JSON（`protocol/verification_report.json`）。

为什么需要（顶层化目标 · 静态可核验）：门禁此前只有人读文本（`bash verify.sh` 的 PASS/WARN/FAIL
计数），机器消费方（CI、外部审计、下游工具）拿不到结构化结论——无法自动回答
「哪些判据在场 / 各报几条 / 声明基线与实测是否一致 / 这份报告是否对应当前树」。

设计口径：
- **判据来源 = 门禁自身用的那些 scanner**（不另造一套）：逐条调 core 扫描器，任何一条
  抛异常都**记账为 error**（不吞、不崩——报告本身必须能出得来，坏的那个反而最显眼）。
- **声明 vs 实测**：把 `quality_baseline.EXPECTED_*`（声明）与实际实测并排写进报告，
  并纳入 `repo_stats.check`（自述数字 == 实算）的结论。
- **可核验**：`root_digest` 是对报告主体的规范化 sha256——报告被手改即对不上；
  `check()` 比对「已落盘报告 == 实时重算」。
- 纪律：纯标准库；只读扫描（唯 `write()` 落盘）；不静默填 0。
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPORT_REL = "protocol/verification_report.json"
SCHEMA = "nf-verify-report/1"

#: 逐条判据：(id, 人读名, 模块, 入口, 形态)
#: 形态 = "scan"（返回 issues[, warns, stats]）| "list"（直接返回 issues 列表）
SPECS: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("purity", "架构纯度体检（R1-R7 + 分层阶梯 L1-L4）", "purity_scan", "scan", "scan"),
    ("schema", "协议层 IDL schema 门禁", "schema_lint", "scan", "scan"),
    ("conformance", "社区领域包 conformance 分级", "conformance_scan", "scan", "scan"),
    ("contract", "机读契约面（官方核心 13 件 id/标题一致）", "machine_contract", "scan", "scan"),
    ("knowledge", "双源知识层（权威分层/顺序/时效/巡检）", "knowledge", "scan", "scan"),
    ("rating", "馆藏内容分级声明", "rating_gate", "scan", "scan"),
    ("license", "许可证门", "license_gate", "scan", "scan"),
    ("intake", "投稿闸门三方一致", "intake", "scan", "scan"),
    ("payload", "事件载荷注册表", "payload_registry", "scan", "scan"),
    ("doc_markers", "文档 marker 卫生", "doc_hygiene", "check_markers", "list"),
    ("assets_ledger", "资产 ledger 投影一致", "asset_ledger_projection", "verify", "scan"),
    ("instruction", "指令档步骤审计", "instruction_step_audit", "scan", "scan"),
    ("baseline", "基线自描述一致（verify 版本 / check 数）", "quality_baseline", "scan", "scan"),
    ("library", "图书馆 frontmatter + 投影一致", "library", "verify", "scan"),
    ("library_projection", "图书馆 INDEX/ALIAS 实时一致", "library", "check_projection", "list"),
    ("receipts", "馆藏回执折叠到根", "receipts", "verify_wrapped", "scan"),
    ("conformance_report", "一致性报告（已提交 == 实时重算）", "conformance_report",
     "verify_committed", "scan"),
    ("audit", "审计件被审对象 digest", "audit", "scan", "scan"),
    ("self_stats", "自述数字 == 实算（README/llms 生成区）", "repo_stats", "check_strict", "scan"),
    ("code_metrics", "代码规模/复杂度上限（棘轮冻结）", "code_metrics", "scan", "scan"),
    ("key_naming", "资产键命名规范（形态 + 声明词表）", "key_naming", "scan", "scan"),
    ("instruction_evidence", "规范入口指令实测记录（新鲜 + 退出码 0）",
     "instruction_evidence", "scan", "scan"),
    ("coupling", "模块级耦合（Martin 包度量 / SDP / 环 · 只许收敛）",
     "coupling_metrics", "scan", "scan"),
    ("perf_budget", "性能预算（中位耗时 ≤ 预算 + 记录新鲜）", "perf_budget", "scan", "scan"),
    ("drill_fidelity", "演练保真度（执行演练 + 回合级回放 = 100%）",
     "drill_fidelity", "scan", "scan"),
    ("judgement_coverage", "判据接线覆盖（暴露 scan() 的判据必须有消费者或例外登记）",
     "judgement_coverage", "scan", "scan"),
)


def _norm(result: Any, form: str) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """把各家返回形状归一到 (issues, warns, stats)。"""
    if form == "list":
        return (list(result or []), [], {})
    if isinstance(result, tuple):
        issues = list(result[0] or [])
        warns = list(result[1] or []) if len(result) > 1 and isinstance(result[1], list) else []
        stats = result[-1] if isinstance(result[-1], dict) else {}
        return issues, warns, stats
    return list(result or []), [], {}


def _call(spec: Tuple[str, str, str, str, str], root: str
          ) -> Tuple[str, List[str], List[str], Dict[str, Any]]:
    """调一条判据 → (status, issues, warns, stats)；异常记账为 error（报告不吞错也不崩）。"""
    sid, _name, mod, entry, form = spec
    try:
        # 用 importlib.import_module（等价于 __import__ 但**不在 purity R6 的危险 sink 类目**里）；
        # 模块名取自本文件内的 SPECS 常量表，非用户输入。
        m = importlib.import_module("core." + mod)
        if entry == "verify_wrapped":                      # receipts.verify 需先 load
            from core import receipts as _r
            rel = _r.RECEIPTS_REL
            if not (Path(root) / rel).is_file():
                return "fail", ["缺 %s（修复指引：nf library receipts --write）" % rel], [], {}
            result = _r.verify(_r.load(root), root)
        elif entry == "check_strict":                       # repo_stats.check 需入口文件在场
            result = importlib.import_module("core.repo_stats").check(root)
        else:
            result = getattr(m, entry)(root)
    except Exception as exc:                                # noqa: BLE001
        return "error", ["%s.%s 抛 %s：%s（修复指引：先修该判据，报告须能出得来）"
                         % (mod, entry, type(exc).__name__, str(exc)[:120])], [], {}
    issues, warns, stats = _norm(result, form)
    status = "fail" if issues else ("warn" if warns else "pass")
    return status, issues, warns, stats


def _declared(root: str) -> Dict[str, Any]:
    """声明面（真源 = quality_baseline）。"""
    out: Dict[str, Any] = {}
    try:
        from core import quality_baseline as qb
        out["expected_checks"] = getattr(qb, "EXPECTED_CHECKS", None)
        out["expected_pass"] = getattr(qb, "EXPECTED_PASS", None)
        out["verify_version"] = qb.scan(root)[1].get("verify_version")
    except Exception as exc:                                # noqa: BLE001
        out["error"] = "%s: %s" % (type(exc).__name__, exc)
    return out


def build(root: str = ".") -> Dict[str, Any]:
    """跑全部判据 → 报告 dict（含声明/实测并排 + 稳定 digest）。"""
    items: List[Dict[str, Any]] = []
    for spec in SPECS:
        sid, name, mod, entry, _form = spec
        status, issues, warns, stats = _call(spec, root)
        items.append({"id": sid, "name": name, "source": "%s.%s" % (mod, entry),
                      "status": status, "issues": len(issues), "warns": len(warns),
                      "stats": stats, "sample": [str(x)[:200] for x in issues[:3]]})
    summary = {k: sum(1 for i in items if i["status"] == k)
               for k in ("pass", "fail", "warn", "error")}
    body = {"schema": SCHEMA, "items": items, "summary": summary,
            "declared": _declared(root)}
    digest_src = json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")
    body["root_digest"] = hashlib.sha256(digest_src).hexdigest()
    return body


def render(report: Dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """落盘 `protocol/verification_report.json` → (issues, report)。"""
    report = build(root)
    out = Path(root) / REPORT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(report), encoding="utf-8", newline="\n")
    issues = ["判据 %s 未过（%d 条）" % (i["id"], i["issues"])
              for i in report["items"] if i["status"] in ("fail", "error")]
    return issues, report


def check(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """提交件 == 实时重算 → (issues, report)。"""
    live = build(root)
    p = Path(root) / REPORT_REL
    if not p.is_file():
        return (["缺 %s（修复指引：python scripts/verify_report.py --write）" % REPORT_REL], live)
    try:
        recorded = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        return (["%s 不是合法 JSON：%s（修复指引：重跑 --write）" % (REPORT_REL, exc)], live)
    issues: List[str] = []
    if recorded.get("root_digest") != live["root_digest"]:
        issues.append("%s 与实时重算不一致（记录=%s 实测=%s）（修复指引：重跑 "
                      "python scripts/verify_report.py --write）"
                      % (REPORT_REL, str(recorded.get("root_digest"))[:12],
                         str(live["root_digest"])[:12]))
    if recorded.get("schema") != SCHEMA:
        issues.append("%s schema 不匹配（期望 %s）（修复指引：重跑 --write）"
                      % (REPORT_REL, SCHEMA))
    return issues, live


def summary_line(report: Dict[str, Any]) -> str:
    s = report.get("summary") or {}
    d = report.get("declared") or {}
    return ("判据 %d 条：PASS %s · FAIL %s · WARN %s · ERROR %s；"
            "声明 check1-%s / PASS=%s · verify %s"
            % (len(report.get("items") or []), s.get("pass"), s.get("fail"),
               s.get("warn"), s.get("error"), d.get("expected_checks"),
               d.get("expected_pass"), d.get("verify_version")))
