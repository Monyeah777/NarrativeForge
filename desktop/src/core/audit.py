"""审计 / 验收门禁（Audit Report + Acceptance/Sign-off + Baseline）。

真源：`protocol/audit.json`（规范件：审计该怎么写）+ `results/audit/*.md`（说明件：审计内容）。

判据（全部可证，零第三方依赖）：
- 声明：schema、required_fields、verdict 词表、rules 非空；
- 带审计头的报告：必填齐；verdict 在词表；date 为 YYYY-MM-DD；
  **`subjects` 每条 `路径:sha256` 必须与当前文件一致**——对象一改，旧审计即失效；
  `accepted_by` 出现则必须有 `accepted_at`（验收签收双要素）；
- 无审计头的存量件：按 **WARN** 挂账（legacy），不判死。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core.library import parse_frontmatter

DECL_REL = "protocol/audit.json"
GLOB = "results/audit/*.md"
SCHEMA = "nf-audit/1"
_DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------- M_AUDIT 门面
# （`nf design audit` 的实现此前依赖本模块的 init_audit/check_audit/scan_audit，
#   但这三个名字在本模块被审计报告族取代后消失，且调用点曾被同名函数遮蔽
#   （flake8 F811 实证）→ 该子命令实际打到了 nf audit。现按**单源委托**修活：
#   M_AUDIT 的 steelman 模式直接委托 core.steelman（钢人节判据的唯一实现），
#   未实装的 blindspot/full 模式 fail-closed 并给修复指引——不编造语义。）

def init_audit(question: str, context: str = "", decider: str = "",
               mode: str = "steelman", path=None) -> str:
    """M_AUDIT init（mode=steelman）：委托 core.steelman.init_worksheet。"""
    from core import steelman
    if mode != "steelman":
        raise ValueError(
            "M_AUDIT 模式 %r 未实装（修复指引：用 --mode steelman；blindspot/full 的"
            "模板与判据尚未成文，须先落规范再实现——见 docs_f2-decision-steelman.md）" % mode)
    return steelman.init_worksheet(question, context=context, decider=decider, path=path)


def check_audit(target) -> List[str]:
    """M_AUDIT check：委托 core.steelman.check_worksheet（同一套钢人节判据）。"""
    from core import steelman
    from pathlib import Path as _Path
    p = _Path(target)
    if not p.is_file():
        return ["审计件不存在：%s（修复指引：先 nf design audit init 生成工作单）" % p]
    return steelman.check_worksheet(p.read_text(encoding="utf-8"))


def scan_audit(root: str = ".") -> List[str]:
    """M_AUDIT ls：委托 core.steelman.scan_steelman（设计审计记录索引）。"""
    from core import steelman
    return steelman.scan_steelman(root)


def decl(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / DECL_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entries(root: str = ".") -> List[Dict[str, Any]]:
    r = Path(root)
    out = []
    for p in sorted(r.glob(GLOB)):
        fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        out.append({"path": p.relative_to(r).as_posix(), "file": p.name,
                    "fm": fm or {}, "body": body or ""})
    return out


def check_doc(root: str, rel: str) -> Tuple[List[str], Dict[str, Any]]:
    """单件机检 → (issues, stats)。无审计头者返回空 issues + legacy 统计。"""
    p = Path(root) / rel
    if not p.is_file():
        return ["审计件不存在：%s" % rel], {}
    d = decl(root)
    fm, _body = parse_frontmatter(p.read_text(encoding="utf-8"))
    fm = fm or {}
    if not fm.get("id"):
        return [], {"legacy": True, "subjects": 0}
    issues: List[str] = []
    for k in (d.get("required_fields") or ["id", "date", "scope", "verdict",
                                           "auditor", "subjects"]):
        if not fm.get(k):
            issues.append("缺必填字段：%s" % k)
    if str(fm.get("verdict")) not in (d.get("verdict_vocabulary") or ["pass", "fail", "warn"]):
        issues.append("verdict 越词表：%s" % fm.get("verdict"))
    if not _DATED.match(str(fm.get("date") or "")):
        issues.append("date 非 YYYY-MM-DD：%s" % fm.get("date"))
    subs = fm.get("subjects") or []
    if isinstance(subs, str):
        subs = [subs]
    ok_subs = 0
    for s in subs:
        t = str(s).strip()
        if ":" not in t:
            issues.append("subjects 条目格式须为 路径:sha256：%s" % t[:40])
            continue
        rel_p, want = t.rsplit(":", 1)
        sp = Path(root) / rel_p.replace("\\", "/")
        if not sp.is_file():
            issues.append("被审对象不存在：%s" % rel_p)
            continue
        if _sha(sp) != want.strip():
            issues.append("被审对象已变，旧审计失效：%s（修复指引：重审并更新 digest）" % rel_p)
            continue
        ok_subs += 1
    if fm.get("accepted_by") and not _DATED.match(str(fm.get("accepted_at") or "")):
        issues.append("有 accepted_by 但 accepted_at 缺失或格式非法（签收须双要素）")
    return issues, {"legacy": False, "subjects": ok_subs}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """声明 + 全部审计件 → (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    d = decl(root)
    if not d:
        return ["缺审计协议声明 %s" % DECL_REL], warns, {}
    if str(d.get("schema") or "") != SCHEMA:
        issues.append("审计协议 schema 不匹配（期望 %s）" % SCHEMA)
    if tuple(d.get("verdict_vocabulary") or ()) != ("pass", "fail", "warn"):
        issues.append("verdict 词表与判据不一致（期望 pass/fail/warn）")
    if not (d.get("rules") or []):
        issues.append("rules 不得为空（审计纪律必须成文）")
    rows = entries(root)
    legacy, subs = [], 0
    for e in rows:
        i, st = check_doc(root, e["path"])
        if st.get("legacy"):
            legacy.append(e["file"])
            continue
        issues += ["%s：%s" % (e["fm"].get("id") or e["file"], x) for x in i]
        subs += st.get("subjects", 0)
    if legacy:
        warns.append("存量审计件无审计头（legacy，按回合收）：%d 件 —— %s"
                     % (len(legacy), "、".join(legacy[:3])))
    if not rows:
        warns.append("暂无审计件（%s）" % GLOB)
    return issues, warns, {"audits": len(rows), "with_header": len(rows) - len(legacy),
                           "legacy": len(legacy), "subjects_ok": subs}
