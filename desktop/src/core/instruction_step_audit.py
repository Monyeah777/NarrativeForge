"""45 A5 · 指令档步进级可机检审计。

对核心指令/规范档做「步骤可执行性」审计：
1) 代码内联命令 `nf <sub>` / `python scripts/<file> …` —— 子命令/脚本必须存在；
2) 引用仓库路径（community/docs/protocol/03_管线库 等以 .md/.json/.yaml 结尾）
   必须真实存在；
3) 未检出上述任一引用即 OK（不是每条 prose 都要可执行，只审可机检步骤）。
"""

from __future__ import annotations

import re
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
    nf_subs = set(re.findall(r'add_parser\(\s*"([^"]+)"',
                             (r / "scripts/nf.py").read_text(encoding="utf-8")))
    steps = 0
    for rel in AUDIT_DOCS:
        path = r / rel
        if not path.exists():
            issues.append("%s 缺失（审计清单内档须在场）" % rel)
            continue
        text = path.read_text(encoding="utf-8")
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
