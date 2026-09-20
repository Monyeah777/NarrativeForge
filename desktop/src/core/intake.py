"""投稿闸门声明的一致性门禁（2026-09-20 作者裁决执行）。

背景（内部差距实证）：投稿闸门此前是**代码常量**（`.github/scripts/library_ingest.py` 的
`ALLOWED = {'monyeah777'}`），而「谁能投 / 走哪条通道 / 暂停与下架怎么处置」只散落在
`library/INDEX.md` 投稿须知与脚本 docstring 里——改闸门不留痕，读者从须知看不出当前接收模式。
外部实证（`results/audit/docs_audit-52-external-inputs.md` §二）：某精选清单因投稿腐化**整仓
暂停投稿**，闸门可见可控是首要观察项。

本模块把闸门做成**声明驱动的三方一致**判据（并入 verify check34，既有 check 内追加）：

1. 声明件 `library/intake.json` 在场 / JSON 合法 / `schema` 正确 / `updated` 合法 /
   `after_action` 非空；
2. 每通道 `mode ∈ {open, author_only, paused}`；`author_only` 必须给非空 `allowlist`；
   `index_label` 非空；
3. `library/INDEX.md` 须出现每通道声明的 `index_label`（防「闸门变了、须知没变」）；
4. 两个入库机器人脚本（GitHub / Gitee）都须**引用**声明件路径（防「声明成摆设：改了没人读」）。

纪律：只读；fail-closed —— 声明缺失 / 不可解析即 FAIL，不静默放行。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

INTAKE_REL = "library/intake.json"
INDEX_REL = "library/INDEX.md"
BOTS = (".github/scripts/library_ingest.py", ".github/scripts/gitee_ingest.py")
MODES = ("open", "author_only", "paused")
SCHEMA = "nf-intake/1"
_DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load(root: str = ".") -> Dict[str, Any]:
    """读声明件 → dict（缺失 / 非法 JSON → 空 dict，由 scan 报 FAIL）。"""
    p = Path(root) / INTAKE_REL
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """声明的三方一致体检 → (issues, stats)。"""
    issues: List[str] = []
    doc = load(root)
    if not doc:
        return ["缺投稿闸门声明 %s（修复指引：补声明件，字段见 results/audit 与 library/INDEX.md）"
                % INTAKE_REL], {"channels": 0, "modes": []}
    if str(doc.get("schema") or "") != SCHEMA:
        issues.append("%s schema 不匹配（期望 %s）" % (INTAKE_REL, SCHEMA))
    if not _DATED.match(str(doc.get("updated") or "")):
        issues.append("%s updated 非 YYYY-MM-DD：%r" % (INTAKE_REL, doc.get("updated")))
    if not str(doc.get("after_action") or "").strip():
        issues.append("%s 缺 after_action（事后处置口径须成文：违规内容怎么下架）" % INTAKE_REL)
    channels = doc.get("channels") if isinstance(doc.get("channels"), dict) else {}
    if not channels:
        issues.append("%s channels 为空（修复指引：至少声明一条接收通道）" % INTAKE_REL)
    index_text = ""
    idx = Path(root) / INDEX_REL
    if idx.is_file():
        index_text = idx.read_text(encoding="utf-8")
    else:
        issues.append("缺 %s（闸门措辞无处可查）" % INDEX_REL)
    for name, ch in sorted(channels.items()):
        ch = ch if isinstance(ch, dict) else {}
        mode = str(ch.get("mode") or "")
        if mode not in MODES:
            issues.append("通道 %s mode 非法：%r（取值 %s）" % (name, mode, " / ".join(MODES)))
        if mode == "author_only":
            allow = [str(x).strip().lower() for x in (ch.get("allowlist") or []) if str(x).strip()]
            if not allow:
                issues.append("通道 %s 为 author_only 但 allowlist 为空（修复指引：给白名单，"
                              "或改为 open / paused）" % name)
        label = str(ch.get("index_label") or "")
        if not label:
            issues.append("通道 %s 缺 index_label（修复指引：给须在 %s 出现的措辞）"
                          % (name, INDEX_REL))
        elif index_text and label not in index_text:
            issues.append("通道 %s 的 index_label 未出现在 %s：%r（修复指引：同步投稿须知措辞，"
                          "防闸门与须知漂移）" % (name, INDEX_REL, label))
    for rel in BOTS:
        p = Path(root) / rel
        if not p.is_file():
            issues.append("缺入库机器人脚本 %s（修复指引：闸门须有执行面）" % rel)
            continue
        if INTAKE_REL not in p.read_text(encoding="utf-8"):
            issues.append("%s 未引用闸门声明 %s（修复指引：机器人须读声明件，"
                          "否则改闸门不生效 = 声明成摆设）" % (rel, INTAKE_REL))
    return issues, {"channels": len(channels),
                    "modes": sorted({str((c or {}).get("mode") or "")
                                     for c in channels.values()})}
