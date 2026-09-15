"""一致性报告工件（机制借鉴 MCOP `runConformanceSuite()` → Merkle-rooted ConformanceReport）。

NF 有 35 道 check，但**没有「报告」这一形态**——第二维护者拿不到「一次跑完、可归档、
可比对」的结论。MCOP 的原话值得照抄进 NF 的处境：*make the framework checkable instead
of trusted*（NF 同样是 Bus Factor 1）。

本模块把**廉价、离线可复算**的契约跑一遍并封缄：

| 契约 id | 钉住什么 |
|---|---|
| `canonical-digest-determinism` | 规范化摘要两遍一致（所有溯源的地基） |
| `schema-clean` | IDL 五定义在场且全量件过 schema |
| `purity-clean` | 架构纯度（端壳残留/私货/修复指引） |
| `doc-kinds` | 文档四型覆盖 |
| `library-verify` | 馆藏 frontmatter 真源 |
| `library-projection` | INDEX/ALIAS 投影 == 实时重算 |
| `pipeline-dryrun` | 全仓管线零 hard 缺陷（抽象执行） |
| `module-signature` | 模块边界零漂移 |
| `io-types` | I/O 类型面零可证不匹配（未收窄记覆盖缺口，不判死） |
| `type-backlog` | 类型积压台账与注册表同步，且无「无 note 的 untyped」（不可无声增长） |
| `event-backing` | 全仓事件背书：每个被订阅的事件都有发布方（外部通道须显式挂账） |
| `declaration` | 一致性声明（scope 白名单 + 显式排除 + 版本与真源逐条一致） |
| `rfc-heads` | 协议件 RFC 头齐备、日期自洽、supersede 链可解析 |
| `patterns` | 实践包格式合规、适用面/证据可证、INDEX 投影一致 |
| `endpoint-contract` | 服务端点契约的 maps_to 全部指向现存 CLI 子命令或 MCP 工具 |
| `public-surface` | 公开导出面不泄漏内部件/绝对路径（借 specadia 分发白名单思路） |
| `knowledge-sources` | 双源知识层：权威分层 / 查询有序 / 时效 / 消化可追溯 与声明逐条一致 |

`verdict = conformant | non-conformant`；`root` = 各契约摘要的 Merkle 根（复用
receipts 的 RFC 6962 折叠规则，不另造密码学）。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from core import receipts

SCHEMA = "nf-conformance/1"
REPORT_REL = "protocol/conformance_report.json"

#: 公开导出面（必须无绝对路径/内部件泄漏的产物）
EXPORT_GLOBS = ("desktop/tests/fixtures/external/**/*", "docs/external-validation-assets/*")
_ABS_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/[a-z]|\\Users\\")


def _c_canonical(root: str) -> Tuple[bool, str]:
    from core import attest
    a = attest.canonical({"b": 2, "a": 1})
    b = attest.canonical({"a": 1, "b": 2})
    return (a == b, "canonical digest 两遍一致" if a == b else "不一致")


def _c_schema(root: str) -> Tuple[bool, str]:
    from core import schema_lint
    issues, stats = schema_lint.scan(root)
    return (not issues, "schema 零漂移（%d 类件）" % len(stats) if not issues
            else "; ".join(issues[:2]))


def _c_purity(root: str) -> Tuple[bool, str]:
    from core import purity_scan
    issues = purity_scan.scan(root)[0]
    return (not issues, "纯度零违规" if not issues else "; ".join(issues[:2]))


def _c_doc_kinds(root: str) -> Tuple[bool, str]:
    from core import doc_hygiene
    issues = doc_hygiene.kind_coverage(root)
    warns = doc_hygiene.kind_rules(root)
    detail = "四型全覆盖 · 写法 WARN %d" % len(warns)
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_library_verify(root: str) -> Tuple[bool, str]:
    from core import library as nflib
    issues = nflib.verify(root)[0]
    return (not issues, "馆藏 frontmatter 真源零 FAIL" if not issues
            else "; ".join(issues[:2]))


def _c_library_projection(root: str) -> Tuple[bool, str]:
    from core import library as nflib
    issues = nflib.check_projection(root)
    return (not issues, "投影一致" if not issues else "; ".join(issues[:2]))


def _c_pipeline_dryrun(root: str) -> Tuple[bool, str]:
    from core import pipelinerun as pr
    issues, tot = pr.sweep(root)
    return (not issues,
            "管线 %d 条零 hard 缺陷（advisory %d）" % (tot["pipelines"], tot["notes"])
            if not issues else "; ".join(issues[:2]))


def _c_module_signature(root: str) -> Tuple[bool, str]:
    from core import module_signature as ms
    issues = ms.verify(root)[0]
    return (not issues, "模块边界零漂移" if not issues else "; ".join(issues[:2]))


def _c_io_types(root: str) -> Tuple[bool, str]:
    from core import io_types as iot
    issues, _warns, stats = iot.scan(root)
    cov = iot.coverage(root)
    detail = "可证不匹配 %d · 类型覆盖 %.1f%%（%d/%d 字段）" % (
        len(issues), cov["coverage"], cov["typed_fields"],
        cov["typed_fields"] + cov["untyped_fields"])
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_type_backlog(root: str) -> Tuple[bool, str]:
    from core import payload_harvest as ph
    issues, stats = ph.verify_backlog(root)
    return (not issues, "不可推断 untyped %d 项（台账同步）" % stats.get("untyped", 0)
            if not issues else "; ".join(issues[:2]))


def _c_event_backing(root: str) -> Tuple[bool, str]:
    from core import registry_cross as rx
    issues, warns, stats = rx.scan(root)
    detail = "事件 %d · 跨包 %d · 挂账 %d" % (
        stats["events"], len(stats["cross_pkg"]), len(warns) - len(stats["cross_pkg"]))
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_declaration(root: str) -> Tuple[bool, str]:
    from core import conformance_decl as cd
    issues, stats = cd.scan(root)
    detail = "版本 %d · scope %d · 排除 %d" % (
        stats.get("versions", 0), stats.get("scope", 0), stats.get("excluded", 0))
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_rfc_heads(root: str) -> Tuple[bool, str]:
    from core import rfc as rf
    issues, _warns, stats = rf.scan(root)
    return (not issues, "RFC 件 %d · 链 %d" % (stats.get("docs", 0), stats.get("chains", 0))
            if not issues else "; ".join(issues[:2]))


def _c_patterns(root: str) -> Tuple[bool, str]:
    from core import patterns as pt
    issues = pt.scan(root)[0] + pt.check_projection(root)
    return (not issues, "实践包 %d 条（格式/可证/投影）" % len(pt.entries(root))
            if not issues else "; ".join(issues[:2]))


def _c_endpoint(root: str) -> Tuple[bool, str]:
    from core import endpoint
    issues, _warns, stats = endpoint.scan(root)
    detail = "端点 %d（status=%s）" % (stats.get("endpoints", 0), stats.get("status", "?"))
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_knowledge(root: str) -> Tuple[bool, str]:
    from core import knowledge as kn
    issues, _warns, stats = kn.scan(root)
    issues = issues + kn.verify_transform(root)[0] + kn.verify_usage(root)[0]
    events = kn.verify_usage(root)[2].get("events", 0)
    detail = "源 %d（合同 %d / 参考 %d）· 消化记录 %d · 频次事件 %d" % (
        stats.get("sources", 0), stats.get("contract", 0),
        stats.get("reference", 0), stats.get("transforms", 0), events)
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_handover(root: str) -> Tuple[bool, str]:
    """接力协议：五段齐 / 未决非空且每条带判据 / refs 可解析。"""
    from core import handover as ho
    issues, _warns, stats = ho.scan(root)
    detail = "交接件 %d 件 · 未决 %d 条" % (stats.get("handovers", 0), stats.get("pending", 0))
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_decisions(root: str) -> Tuple[bool, str]:
    """决策记录：编号/状态/取代链/证据可解析/三段齐 + accepted 须被回执锚定 + 投影一致。"""
    from core import decisions as dc
    issues, _warns, stats = dc.scan(root)
    issues = issues + dc.check_projection(root)
    detail = "决策 %d 条（accepted %d · 取代链 %d）" % (
        stats.get("decisions", 0), stats.get("accepted", 0), stats.get("chains", 0))
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_modeling(root: str) -> Tuple[bool, str]:
    """内容建模三件：词表与真源一致 / 规范件皆有主 / 契约 quality_rule 可解析。"""
    from core import modeling as M
    issues, _warns, stats = M.scan(root)
    v = stats.get("vocabularies", {})
    n = stats.get("normative", {})
    d = stats.get("data_contracts", {})
    detail = "词表 %d · 规范件 %d / 说明件 %d · 数据契约 %d" % (
        v.get("schemes", 0), n.get("normative", 0),
        n.get("informative_files", 0), d.get("contracts", 0))
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_assertions(root: str) -> Tuple[bool, str]:
    """数据化断言表：跑一遍，fail 级不通过即 FAIL。"""
    from core import assertions as at
    results, issues = at.run(root)
    passed = sum(1 for r in results if r["ok"])
    detail = "断言 %d 条（通过 %d）· kind 封闭集 %d 种" % (
        len(results), passed, len(at.KINDS))
    return (not issues, detail if not issues else "; ".join(issues[:2]))


def _c_public_surface(root: str) -> Tuple[bool, str]:
    """公开导出面泄漏审计：绝对路径 / 内部件路径不得出现在对外产物里。"""
    bad: List[str] = []
    r = Path(root)
    for pat in EXPORT_GLOBS:
        for p in sorted(r.glob(pat)):
            if not p.is_file() or p.suffix not in (".md", ".json", ".yaml", ".yml", ".txt"):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if _ABS_PATH.search(text):
                bad.append("%s 含绝对路径" % p.relative_to(r).as_posix())
    ok = not bad
    return (ok, "公开导出面零泄漏" if ok else "; ".join(bad[:2]))


CONTRACTS: List[Tuple[str, Callable[[str], Tuple[bool, str]], str]] = [
    ("canonical-digest-determinism", _c_canonical, "规范化摘要可复现"),
    ("schema-clean", _c_schema, "IDL 单一真相零漂移"),
    ("purity-clean", _c_purity, "架构纯度零违规"),
    ("doc-kinds", _c_doc_kinds, "文档四型覆盖"),
    ("library-verify", _c_library_verify, "馆藏 frontmatter 真源"),
    ("library-projection", _c_library_projection, "INDEX/ALIAS 投影一致"),
    ("pipeline-dryrun", _c_pipeline_dryrun, "管线抽象执行零 hard 缺陷"),
    ("module-signature", _c_module_signature, "模块边界冻结"),
    ("io-types", _c_io_types, "I/O 类型面（可证不匹配）"),
    ("type-backlog", _c_type_backlog, "类型积压显式化"),
    ("event-backing", _c_event_backing, "全仓事件背书"),
    ("declaration", _c_declaration, "一致性声明"),
    ("rfc-heads", _c_rfc_heads, "协议件版本史头"),
    ("patterns", _c_patterns, "实践包品类"),
    ("endpoint-contract", _c_endpoint, "服务端点契约指向真实性"),
    ("knowledge-sources", _c_knowledge, "双源知识层（权威分层/查询有序/时效/溯源）"),
    ("assertions", _c_assertions, "数据化断言表（形状类断言数据化）"),
    ("modeling", _c_modeling, "内容建模三件（词表/规范说明件/数据契约）"),
    ("decisions", _c_decisions, "决策记录（ADR：不可改 + 取代链）"),
    ("handover", _c_handover, "接力协议（SBAR 五段 + 未决带判据）"),
    ("public-surface", _c_public_surface, "公开导出面零泄漏"),
]


def run(root: str = ".") -> Dict[str, Any]:
    """跑全部契约 → 封缄报告（含 Merkle 根与 verdict）。"""
    rows = []
    for cid, fn, desc in CONTRACTS:
        try:
            ok, detail = fn(root)
        except Exception as exc:                      # 契约自身异常 = 不通过
            ok, detail = False, "契约执行异常：%s" % exc
        payload = json.dumps({"id": cid, "ok": bool(ok), "detail": detail},
                             sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")
        rows.append({"id": cid, "ok": bool(ok), "detail": detail,
                     "description": desc,
                     "digest": hashlib.sha256(payload).hexdigest()})
    leaves = [receipts.leaf_hash(json.dumps({"id": r["id"], "digest": r["digest"]},
                                            sort_keys=True,
                                            separators=(",", ":")).encode("utf-8"))
              for r in rows]
    root_hash = receipts.merkle_root(leaves)
    return {"schema": SCHEMA, "contracts": rows,
            "passed": sum(1 for r in rows if r["ok"]), "total": len(rows),
            "root": root_hash.hex() if root_hash else "",
            "verdict": "conformant" if all(r["ok"] for r in rows) else "non-conformant"}


def write(root: str = ".", rel: str = REPORT_REL) -> str:
    doc = run(root)
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8", newline="\n")
    return rel


def verify_committed(root: str = ".", rel: str = REPORT_REL) -> Tuple[List[str], Dict[str, Any]]:
    """在盘报告 == 实时重算？（防「报告是旧的/被改过」）"""
    p = Path(root) / rel
    if not p.is_file():
        return ["缺一致性报告 %s（修复指引：nf conformance --write）" % rel], {}
    try:
        committed = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        return ["报告 JSON 不可解析：%s" % exc], {}
    live = run(root)
    issues: List[str] = []
    if committed.get("root") != live.get("root"):
        issues.append("报告过期或被改：root 记录=%s 实测=%s（修复指引：nf conformance --write）"
                      % (str(committed.get("root"))[:16], str(live.get("root"))[:16]))
    if committed.get("verdict") != live.get("verdict"):
        issues.append("verdict 不一致：记录=%s 实测=%s"
                      % (committed.get("verdict"), live.get("verdict")))
    stats = {"contracts": live["total"], "passed": live["passed"],
             "verdict": live["verdict"], "root": live["root"]}
    return issues, stats
