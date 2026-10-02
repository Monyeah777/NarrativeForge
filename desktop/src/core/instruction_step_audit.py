"""45 A5 · 指令档步进级可机检审计。

对核心指令/规范档做「步骤可执行性」审计：
1) 代码内联命令 `nf <sub>` / `python scripts/<file> …` —— 子命令/脚本必须存在；
2) 引用仓库路径（community/docs/protocol/03_管线库 等以 .md/.json/.yaml 结尾）
   必须真实存在；
3) 未检出上述任一引用即 OK（不是每条 prose 都要可执行，只审可机检步骤）。
"""

from __future__ import annotations

import re

from core import conformance_scan as csc
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]
AUDIT_DOCS = [
    "agent_组装指令包_v0.2.md",
    "docs/45_执行遥测规范.md",
    "docs/45_M2_回合级drill.md",
    "docs/45_M3_techdoc载荷提案.md",
    "docs/44_M2_AI通道内容规范.md",
]
_CMD = re.compile(r"`([^`\n]{1,160})`")


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    issues: List[str] = []
    # 缺根/缺 CLI 真源时**如实报 issue**，不抛裸 FileNotFoundError（与 `payload_registry.scan`
    # 同一条纪律——极端渗透 F-5 只修了那一个入口，2026-10-01 空根普查发现本入口漏修）。
    if not (r / "scripts/nf.py").is_file():
        return (["读不到 CLI 真源 scripts/nf.py（修复指引：在 NF 仓库根运行本扫描，"
                 "或先补齐该件——本扫描要拿它当子命令面的单一真值）"], {})
    nf_subs = set(re.findall(r'add_parser\(\s*"([^"]+)"',
                             csc.read_text_cached(r / "scripts/nf.py")))
    steps = 0
    for rel in AUDIT_DOCS:
        path = r / rel
        if not path.exists():
            issues.append("%s 缺失（审计清单内档须在场）" % rel)
            continue
        text = csc.read_text_cached(path)
        for m in _CMD.finditer(text):
            code = m.group(1).strip()
            if code.startswith("nf "):
                steps += 1
                sub = code.split()[1]
                if sub not in nf_subs:
                    issues.append("%s: 引用未知子命令 nf %s" % (rel, sub))
            elif code.startswith("python scripts/"):
                steps += 1
                fname = code.split()[1].lstrip("./")
                if not (r / fname).exists():
                    issues.append("%s: 引用脚本不存在 %s" % (rel, fname))
            elif re.search(r"(?:community|docs|protocol|03_管线库)/", code) and \
                    code.endswith((".md", ".json", ".yaml")):
                steps += 1
                if not (r / code).exists():
                    issues.append("%s: 引用路径不存在 %s" % (rel, code))
    return issues, {"docs": len(AUDIT_DOCS), "steps": steps}
