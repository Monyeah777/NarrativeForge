"""发布编排（release orchestration）：把「tag 前要做什么」做成**机读策略 + 可编译计划 + 可机检前置**。

为什么需要（内部差距实证 2026-10-05）：发布动作此前散在四处——`nf release`（体检）、
`scripts/release_freeze.sh`（golden master 快照）、`scripts/bump_verify.sh`（版本换标）、
`docs/42_M5_Release-checklist.md`（人工清单），再加 `decisions/ADR-0005-新增NET引擎线.md`
记载的**冻结链**（conformance --write → approve → receipts --write）——**顺序**与**前置**只在
文档与人的记忆里。2026-10-05 第二轮补上同类顶尖项目的两项机制：**配置即契约**（策略落
`protocol/release_policy.json` + `protocol/schema/release.schema.json`，参照 release-please 的
`$schema` 模式）与**变更条目收集**（`changes/unreleased/*.md`，参照 changesets）。

三件可证的事（纯标准库、只读、不执行）：

1. `plan(root)` —— 确定性计划：前置 → 门禁 → 冻结链 → golden master → 版本面 → 变更归档 → 审计 → tag。
2. `check(root)` —— 机检前置（check38 子扫描）：策略 JSON 过 schema、人读策略件锚点齐、必需产物在场、
   冻结链按序、golden 快照结构完整、**版本面登记不悬空**、**变更条目可归档**。
3. `manifest(root)` —— 确定性证据摘要（无墙钟）。

纪律：纯标准库；只读；无网络；无墙钟；同输入同输出；缺件/空根一律如实报 issue 并给修复指引，不抛裸异常。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

#: 人读策略投影（三段声明 + 锚点面）。
POLICY_DOC = "docs/release.md"
#: 机读策略真源（配置即契约）。
POLICY_JSON = "protocol/release_policy.json"
POLICY_SCHEMA_ID = "nf:release-policy"
INTEGRATION_SCHEMA_ID = "nf:integration"
#: golden master 冻结根（scripts/release_freeze.sh 的产出面）。
GOLDEN_DIR = ".release-frozen"
#: 策略件必须写明的锚点（缺一即 FAIL——写了却没人看与没写同等不可核）。
POLICY_ANCHORS: Tuple[str, ...] = (
    "## 冻结链", "## 版本面", "## Golden Master", "## 变更条目",
    "bash verify.sh", "scripts/release_freeze.sh",
    "python scripts/nf.py conformance --write", "nf approve",
    "python scripts/nf.py receipts --scope protocol --write",
)
#: 冻结链兜底（策略件缺件时用于成形；正常路径以策略 JSON 为准）。
DEFAULT_FREEZE_CHAIN: Tuple[str, ...] = (
    "python scripts/nf.py conformance --write",
    "python scripts/nf.py approve protocol/conformance_report.json",
    "python scripts/nf.py receipts --scope protocol --write",
)
DEFAULT_GOLDEN: Tuple[str, ...] = (
    "01_核心协议.md", "02_联动注册表.md", "06_Agent执行协议.md",
    "07_官方核心出厂与社区预设导航.md", "verify.sh",
)
#: 变更条目允许的类型词表（对齐提交信息纪律的 type 词表 + release）。
CHANGE_TYPES: Tuple[str, ...] = ("feat", "fix", "docs", "refactor", "perf", "test", "chore", "release")


def policy(root: str = ".") -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """读机读策略件并过 schema（缺件/坏件/越界都如实报）。"""
    import json as _json
    r = Path(root)
    p = r / POLICY_JSON
    if not p.is_file():
        return None, ["缺机读发布策略 %s（修复指引：落一份 nf-release-policy/1，"
                      "字段见 protocol/schema/release.schema.json）" % POLICY_JSON]
    try:
        data = _json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, ["%s 不可解析：%s" % (POLICY_JSON, exc)]
    issues: List[str] = []
    try:
        from core import schema_lint as sl
        schema = sl.load_schema(str(r), POLICY_SCHEMA_ID)
        if schema is None:
            issues.append("缺 release schema（%s；修复指引：protocol/schema/release.schema.json）"
                          % POLICY_SCHEMA_ID)
        else:
            for v in sl.subset_validate(data, schema, POLICY_JSON):
                issues.append("发布策略越界：%s" % v)
    except Exception as exc:  # 校验器不可用不静默
        issues.append("发布策略 schema 校验不可用：%s" % exc)
    return data, issues


def _version(root: Path) -> Tuple[str, int, int]:
    """门禁版本 / check 数 / PASS 基线（真源 = verify.sh，经 quality_baseline 单一口径）。

    缺基线面时返回空三元组——由 check 如实报 issue，不在读文件处裸崩。
    """
    need = ("verify.sh", "README.md", "CHANGELOG.md", "VERSION-MATRIX.md")
    if not all((root / f).is_file() for f in need):
        return ("", 0, 0)
    from core import quality_baseline as qb
    _, stats = qb.scan(str(root))
    return (str(stats.get("verify_version") or ""),
            int(stats.get("checks") or 0),
            int(getattr(qb, "EXPECTED_PASS", 0)))


def release_line(root: str = ".") -> str:
    """待发布版本线（CHANGELOG 最新节的 X.Y.Z；无则空串）。"""
    p = Path(root) / "CHANGELOG.md"
    if not p.is_file():
        return ""
    m = re.search(r"(?m)^## \[([0-9]+\.[0-9]+\.[0-9]+)\]", p.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def plan(root: str = ".") -> List[Dict[str, str]]:
    """确定性发布计划（有序）。每步 = 命令 / 产出 / 判据；顺序取自机读策略。"""
    r = Path(root)
    _pol, _ = policy(root)
    chain = list((_pol or {}).get("freeze_chain") or DEFAULT_FREEZE_CHAIN)
    ver, checks, expected_pass = _version(r)
    rel = release_line(root)
    tag = ("v" + rel) if rel else "vX.Y.Z"
    return [
        {"id": "pre-1", "title": "工作区状态",
         "cmd": "git status --porcelain", "out": "空输出（发布内容已提交）",
         "judge": "无未提交改动；发布提交即 tag 指向的提交"},
        {"id": "pre-2", "title": "发布策略件",
         "cmd": "读 " + POLICY_DOC + " 三段声明 + " + POLICY_JSON + "（过 schema）",
         "out": POLICY_JSON, "judge": "策略 JSON 过 nf:release-policy schema；人读件锚点齐"},
        {"id": "gate-1", "title": "全量门禁",
         "cmd": "bash verify.sh", "out": "PASS=%d / WARN=0 / FAIL=0" % expected_pass,
         "judge": "退出码 0（check1-%d 全过）" % checks},
        {"id": "gate-2", "title": "发布前体检",
         "cmd": "python scripts/nf.py release", "out": "体检报告",
         "judge": "退出码 0（含 e2e 冒烟 / 逐模块覆盖率 / 门禁报告新鲜度 / ruff）"},
        {"id": "changes-1", "title": "变更日志生成与归档",
         "cmd": "python scripts/nf.py changelog --version %s --date <发布日期> --write" % (rel or "X.Y.Z"),
         "out": "CHANGELOG.md 版本节（+ changes/%s/）" % (rel or "X.Y.Z"),
         "judge": "渲染确定且逐条可溯源（只分组不改写）；归档后 changes/unreleased 为空"},
        {"id": "freeze-1", "title": "一致性报告重算",
         "cmd": chain[0], "out": "protocol/conformance_report.json",
         "judge": "verdict=conformant（27/27 契约）"},
        {"id": "freeze-2", "title": "内容绑定批准",
         "cmd": chain[1] + " --by <批准人> --note <本波说明>",
         "out": "protocol/approvals", "judge": "批准记录有效（对象内容绑定）"},
        {"id": "freeze-3", "title": "协议层回执重签",
         "cmd": chain[2], "out": "protocol/RECEIPTS.json（+ receipt_chain / interop 派生面）",
         "judge": "每条折叠到根、根与实时重算一致"},
        {"id": "golden-1", "title": "Golden Master 冻结",
         "cmd": "bash scripts/release_freeze.sh %s" % tag,
         "out": GOLDEN_DIR + "/" + tag + "/sha256.manifest",
         "judge": "快照齐策略声明的 golden_required + desktop/src/core/*.py + nf sig --verify 指纹"},
        {"id": "ver-1", "title": "版本面同步",
         "cmd": "CHANGELOG 版本节 + VERSION-MATRIX 行 + README 版本块",
         "out": "三处同版", "judge": "登记不悬空（发布线可达 CHANGELOG ↔ VERSION-MATRIX）"},
        {"id": "audit-1", "title": "审计建档",
         "cmd": "results/audit/docs_audit-<N>-<主题>.md（含五维自评段）",
         "out": "审计件", "judge": "本波审计件在册且 verdict 通过"},
        {"id": "tag-1", "title": "打标",
         "cmd": "git tag -a %s -m \"<版本说明>\"" % tag, "out": "annotated tag",
         "judge": "tag 指向发布提交；打标后不再改协议与代码"},
    ]


def render_plan(root: str = ".") -> str:
    """人读计划（逐行可复制）。"""
    lines = ["== nf release plan（发布计划 · 有序）=="]
    for i, s in enumerate(plan(root), 1):
        lines.append("  %2d. [%s] %s" % (i, s["id"], s["title"]))
        lines.append("      命令：%s" % s["cmd"])
        lines.append("      产出：%s" % s["out"])
        lines.append("      判据：%s" % s["judge"])
    return "\n".join(lines)


def _golden_issues(r: Path, required: Tuple[str, ...]) -> Tuple[List[str], List[str]]:
    """golden master 快照结构完整性（在场时）。"""
    issues: List[str] = []
    root = r / GOLDEN_DIR
    names: List[str] = []
    if not root.is_dir():
        return issues, names
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        names.append(d.name)
        man = d / "sha256.manifest"
        if not man.is_file():
            issues.append("%s/%s 缺 sha256.manifest（修复指引：重跑 bash scripts/release_freeze.sh %s）"
                          % (GOLDEN_DIR, d.name, d.name))
            continue
        text = man.read_text(encoding="utf-8", errors="replace")
        missing = [f for f in required if f not in text]
        if missing:
            issues.append("%s/%s 快照不完整，缺 %s（修复指引：重跑 bash scripts/release_freeze.sh %s）"
                          % (GOLDEN_DIR, d.name, "、".join(missing), d.name))
        if not re.search(r"(?m)^[0-9a-f]{64}\s", text):
            issues.append("%s/%s 的 sha256.manifest 空或无摘要行" % (GOLDEN_DIR, d.name))
    return issues, names


def _changes_issues(r: Path, changes_dir: str) -> Tuple[List[str], List[str]]:
    """变更条目（changesets 式）：规则件在场 + 每条含 type/note（发布时归档进 CHANGELOG）。"""
    issues: List[str] = []
    d = r / changes_dir
    if not d.is_dir():
        issues.append("缺变更条目目录 %s/（修复指引：建目录 + README 写明规则；"
                      "发布前把条目归档进 CHANGELOG）" % changes_dir)
        return issues, []
    rule = d.parent / "README.md"
    if not rule.is_file():
        issues.append("缺变更条目规则件 %s/README.md（修复指引：写明条目字段与归档方式）"
                      % changes_dir.split("/")[0])
    names = sorted(p.name for p in d.glob("*.md"))
    for name in names:
        txt = (d / name).read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?m)^type:\s*([a-z]+)\s*$", txt)
        if not m or m.group(1) not in CHANGE_TYPES:
            issues.append("%s/%s 缺合法 type（词表：%s）"
                          % (changes_dir, name, "/".join(CHANGE_TYPES)))
        if not re.search(r"(?m)^note:\s*\S", txt):
            issues.append("%s/%s 缺 note（一句话说明改了什么）" % (changes_dir, name))
    return issues, names


def check(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """可机检发布前置（check38 子扫描口径）。缺根如实报 issue，不裸崩。"""
    r = Path(root)
    if not (r / "verify.sh").is_file():
        return (["读不到仓库根（缺 verify.sh）——发布编排须在 NF 仓库根运行"], {})
    issues: List[str] = []
    stats: Dict[str, Any] = {}

    # 1 机读策略件：在场 + 过 schema
    pol, p_issues = policy(root)
    issues += p_issues
    pol = pol or {}

    # 2 人读策略件：三段锚点齐
    doc = r / POLICY_DOC
    if not doc.is_file():
        issues.append("缺人读发布策略 %s（修复指引：写明冻结链/版本面/Golden Master/变更条目四段；"
                      "锚点见 core/release_gate.py::POLICY_ANCHORS）" % POLICY_DOC)
    else:
        ptxt = doc.read_text(encoding="utf-8")
        miss = [a for a in POLICY_ANCHORS if a not in ptxt]
        if miss:
            issues.append("%s 缺声明锚点：%s" % (POLICY_DOC, "、".join(miss)))

    # 3 必需产物在场（策略声明）
    for rel in pol.get("required_artifacts") or []:
        if not (r / rel).exists():
            issues.append("发布必需产物不在场：%s（修复指引：按冻结链重生成）" % rel)

    # 4 版本面 + 计划可编译 + 冻结链按序
    for rel in pol.get("version_faces") or []:
        if not (r / rel).is_file():
            issues.append("版本面不在场：%s" % rel)
    steps = plan(root)
    bad = [s["id"] for s in steps if not (s.get("cmd") and s.get("out") and s.get("judge"))]
    if bad:
        issues.append("发布计划步骤缺栏：%s" % "、".join(bad))
    chain = list(pol.get("freeze_chain") or DEFAULT_FREEZE_CHAIN)
    cmds = [s["cmd"] for s in steps]
    pos = [next((i for i, c in enumerate(cmds) if c.startswith(x)), -1) for x in chain]
    if any(p < 0 for p in pos) or pos != sorted(pos):
        issues.append("冻结链未按序进计划（%s）（修复指引：conformance → approve → receipts 顺序不可颠倒）"
                      % "、".join(str(p) for p in pos))

    # 5 golden master 结构完整（在场时）
    required = tuple(pol.get("golden_required") or DEFAULT_GOLDEN)
    g_issues, g_names = _golden_issues(r, required)
    issues += g_issues

    # 6 变更条目可归档 + 变更日志生成可溯源（release-please 的最后一环）
    ch_dir = str(pol.get("changes_dir") or "changes/unreleased")
    ch_issues, ch_names = _changes_issues(r, ch_dir)
    issues += ch_issues
    try:
        from core import changelog_gen as _cg
        for i in _cg.check(root, changes_dir=ch_dir)[0]:
            issues.append("变更日志：%s" % i)
    except Exception as exc:
        issues.append("变更日志生成检查不可用：%s" % exc)
    if not any("changelog --version" in s["cmd"] for s in steps):
        issues.append("发布计划缺变更日志生成步（修复指引：changes-1 步须调 nf changelog）")

    # 7 版本面登记不悬空（发布线可达 CHANGELOG ↔ VERSION-MATRIX）
    if not (r / "README.md").is_file():
        issues.append("缺版本面入口 README.md（修复指引：版本块须在场）")
    rel = release_line(root)
    if not rel:
        issues.append("CHANGELOG 无版本节（修复指引：加 \"## [X.Y.Z] - 未发布\" 节）")
    else:
        matrix = r / "VERSION-MATRIX.md"
        mtxt = matrix.read_text(encoding="utf-8") if matrix.is_file() else ""
        if rel not in mtxt:
            issues.append("发布线 v%s 未登记 VERSION-MATRIX（修复指引：补一行 v%s）" % (rel, rel))

    ver, checks, expected_pass = _version(r)
    stats.update({
        "policy": POLICY_JSON, "policy_doc": POLICY_DOC, "release_line": rel,
        "gate_version": ver, "checks": checks, "expected_pass": expected_pass,
        "plan_steps": len(steps), "golden_snapshots": g_names,
        "freeze_chain": chain, "changes": ch_names,
    })
    return issues, stats


#: check38 子扫描统一入口名（与 repo_stats / integrations / locales 一致）。
scan = check


def manifest(root: str = ".") -> Dict[str, Any]:
    """确定性证据摘要（无墙钟；同输入同输出）。"""
    issues, stats = check(root)
    return {
        "schema": "nf-release-manifest/1",
        "policy": POLICY_JSON,
        "chain": stats.get("freeze_chain", []),
        "plan": [{"id": s["id"], "title": s["title"], "cmd": s["cmd"]} for s in plan(root)],
        "stats": stats,
        "issues": issues,
    }
