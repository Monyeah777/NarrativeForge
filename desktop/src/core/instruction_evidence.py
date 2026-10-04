"""规范入口指令的**实测记录**判据（文档可执行性面 · 顶层化目标 GAP-6）。

为什么需要：文档里的入口指令（`bash verify.sh`、`python scripts/nf.py release` …）此前
只有「写着」，没有任何证据表明它**被真跑过、跑出什么结果、什么时候跑的**——读者与下游
无从区分「可执行」与「曾经可执行」。本模块把「指令块挂实测记录」落成判据：

- **声明面**（真源）= `protocol/instruction_evidence.json` 的 `instructions`
  （id / cmd / note / tier / max_age_days），不写死在代码里；
- **证据面** = 同件 `evidence`（由 `--record` 真跑写入：命令 / 退出码 / 时间 / 输出摘要
  / 输出 sha256）；
- **判据**：① 每条声明须有记录（缺 = FAIL）；② 记录须**退出码 0**（非 0 = FAIL）；
  ③ 记录须在 `max_age_days` 内（过期 = FAIL）；④ 记录键必须都是已声明指令（凭空记录 = FAIL）。

纪律：纯标准库；本模块不自己执行命令（执行发生在 `scripts/instruction_evidence.py` 的
`--record` 里），以便「判据只读、实测显式」。
"""
from __future__ import annotations

import datetime as _dt

from core import atomic_write
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

DECL_REL = "protocol/instruction_evidence.json"
SCHEMA = "nf-instruction-evidence/1"

#: 机器绝对路径（Windows 盘符 / macOS / Linux 家目录）——证据件进公开仓，**不得**带作者机器路径。
_MACHINE_PATH = re.compile(r"(?:[A-Za-z]:[\\/][^\s\"'）)】]*)|(?:/(?:Users|home)/[^\s\"'）)】]*)")


def redact_paths(text: str) -> str:
    """把输出摘要里的机器绝对路径换成 `<path>`（泄漏面收口；只影响人读摘要，不动哈希）。"""
    return _MACHINE_PATH.sub("<path>", text or "")


def load(root: str = ".") -> Tuple[Dict[str, Any], List[str]]:
    """读声明+证据件 → (doc, issues)；缺失/不可解析/字段不全一律 fail-closed。"""
    p = Path(root) / DECL_REL
    if not p.is_file():
        return {}, ["缺指令实测记录件 %s（修复指引：新建并声明入口指令，再跑 "
                    "python scripts/instruction_evidence.py --record）" % DECL_REL]
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {}, ["%s 不是合法 JSON：%s（修复指引：修好 JSON 语法）" % (DECL_REL, exc)]
    issues: List[str] = []
    if doc.get("schema") != SCHEMA:
        issues.append("%s schema 不匹配（期望 %s）（修复指引：改为声明件当前形态）"
                      % (DECL_REL, SCHEMA))
    if not isinstance(doc.get("instructions"), list) or not doc["instructions"]:
        issues.append("%s 缺 instructions 声明（修复指引：至少声明一条入口指令）" % DECL_REL)
    return doc, issues


def _age_days(stamp: str, today: _dt.date) -> int:
    try:
        d = _dt.date.fromisoformat(str(stamp)[:10])
    except ValueError:
        return 10 ** 6                       # 时间戳不可解析 → 视作无限旧（判 FAIL）
    return (today - d).days


def scan(root: str = ".", today: _dt.date | None = None
         ) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：缺记录/非零退出/过期/凭空记录 = FAIL。

    例外：`evidence_policy: "recorded"` 的指令只要求「真跑记录存在 + 新鲜」——它们与判据表
    互为不动点（见声明件 note）：`verify` / `release` 要绿必须判据表全绿，而判据表里就要求
    它们绿。这类入口的绿由 CI 跨平台 workflow 与发布流程另判，不在这里自证。
    """
    doc, issues = load(root)
    warns: List[str] = []
    if not doc or issues:
        return issues, warns, {"declared": 0, "recorded": 0}
    today = today or _dt.date.today()  # noqa: DTZ011 - 本地日历日期是有意语义（UTC 会在跨零点给出错误「今天」）
    decl = doc.get("instructions") or []
    ev = doc.get("evidence") or {}
    for item in decl:
        iid = str((item or {}).get("id") or "")
        if not iid:
            issues.append("%s 有声明项缺 id（修复指引：补齐 id/cmd/note）" % DECL_REL)
            continue
        rec = ev.get(iid)
        policy = str(item.get("evidence_policy") or "green")
        if policy not in ("green", "recorded"):
            issues.append("指令 %s 的 evidence_policy 非法：%s（修复指引：只许 green / recorded）"
                          % (iid, policy))
        if not isinstance(rec, dict):
            issues.append("指令 %s（%s）无实测记录（修复指引：python scripts/"
                          "instruction_evidence.py --record）" % (iid, item.get("cmd")))
            continue
        if int(rec.get("exit_code", 1)) != 0 and policy != "recorded":
            issues.append("指令 %s 实测退出码 %s（修复指引：先修到 0 再 --record）"
                          % (iid, rec.get("exit_code")))
        max_age = int(item.get("max_age_days", 30) or 30)
        age = _age_days(str(rec.get("ran_at") or ""), today)
        if age > max_age:
            issues.append("指令 %s 的实测记录已过期（%d 天 > 上限 %d 天）（修复指引："
                          "python scripts/instruction_evidence.py --record --only %s）"
                          % (iid, age, max_age, iid))
    known = {str((i or {}).get("id") or "") for i in decl}
    for iid in sorted(set(ev) - known):
        issues.append("记录 %s 无对应声明（修复指引：要么在 %s 声明该指令，要么删掉记录）"
                      % (iid, DECL_REL))
    stats = {"declared": len(known), "recorded": len(set(ev) & known)}
    stats["recorded_policy"] = sum(
        1 for i in decl if str((i or {}).get("evidence_policy") or "") == "recorded")
    return issues, warns, stats


def record(root: str = ".", only: str = "", runner=None,
           today: _dt.date | None = None) -> Tuple[List[str], Dict[str, Any]]:
    """真跑声明指令并写回证据 → (bad_ids, doc)。

    `runner(cmd) -> (exit_code, output)` 由调用方注入（CLI 里是 subprocess），便于单测注入
    假执行器；`only` 可为 `all` / `fast` / 具体 id。
    """
    import hashlib as _h

    doc, issues = load(root)
    if not doc or issues:
        return issues, doc
    today = today or _dt.date.today()  # noqa: DTZ011 - 本地日历日期是有意语义（UTC 会在跨零点给出错误「今天」）
    ev = doc.setdefault("evidence", {})
    for item in doc.get("instructions") or []:
        iid = str((item or {}).get("id") or "")
        if not iid:
            continue
        if only and only not in ("all", iid) and not (only == "fast"
                                                      and item.get("tier") == "fast"):
            continue
        cmd = str(item.get("cmd") or "")
        code, out = runner(cmd)
        ev[iid] = {"cmd": cmd, "exit_code": int(code), "ran_at": today.isoformat(),
                   "output_tail": redact_paths(
                       "\n".join(out.strip().splitlines()[-3:]))[:400],
                   "output_sha256": _h.sha256(out.encode("utf-8", "replace")).hexdigest()}
    p = Path(root) / DECL_REL
    atomic_write.write_text(p, json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    # 汇总口径与 scan 一致：`evidence_policy: recorded` 的入口（不动点例外）非零退出不算 bad。
    pol = {str((i or {}).get("id") or ""): str((i or {}).get("evidence_policy") or "green")
           for i in doc.get("instructions") or []}
    bad = [k for k, v in ev.items() if int((v or {}).get("exit_code", 1)) != 0
           and pol.get(k, "green") != "recorded"]
    return bad, doc
