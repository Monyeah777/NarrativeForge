"""45 W1 · 质量纵深顶尖化——基线自描述一致性机检。

静态可核验维度最隐蔽的漂移：verify 版本 / check 数 / PASS 声明分处 verify.sh、
README（版本块与基线句）、CHANGELOG（最新发布节）、VERSION-MATRIX（最新行），
人工维护极易改一处漏三处。本模块以 verify.sh 为单一真值，断言其余四处声明与其
自洽；任何一处落后即 FAIL（防「口头 PASS=49、文档 PASS=41」类失配）。

口径只认「当前基线句」（含最新版本/check1-N/PASS=N 组合）；历史归档句不算漂移。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    issues: List[str] = []
    verify_text = (r / "verify.sh").read_text(encoding="utf-8")
    m = re.search(r"# 版本 : (v\d+\.\d+)", verify_text)
    ver = m.group(1) if m else ""
    nums = sorted({int(x) for x in re.findall(r"^check(\d+)\(\)\{", verify_text, re.M)})
    n_checks = len(nums)
    if ver != "v2.20":
        issues.append("verify.sh 版本非 v2.20（当前 %s）" % (ver or "空"))
    if n_checks != 31 or nums != list(range(1, 32)):
        issues.append("verify.sh check 函数数/编号异常：%s" % nums)

    claim = "v%s check1-31 PASS=49" % ver
    checks: List[Tuple[str, str, int]] = []
    readme = (r / "README.md").read_text(encoding="utf-8")
    checks.append(("README", "基线句",
                   1 if all(t in readme for t in ("v2.20", "check1-31", "PASS=49"))
                   else 0))
    changelog = (r / "CHANGELOG.md").read_text(encoding="utf-8")
    head = changelog.split("\n## [2.8.0]", 1)[0]
    checks.append(("CHANGELOG 最新节", "版本头+PASS 声明",
                   head.count("[2.9.0]") + head.count("PASS=49")))
    matrix = (r / "VERSION-MATRIX.md").read_text(encoding="utf-8")
    checks.append(("VERSION-MATRIX v2.9.0 行", "PASS=49",
                   matrix.count("v2.9.0（内容波收口）")
                   + matrix.count("PASS=49")))
    for name, what, n in checks:
        if n < 1:
            issues.append("%s 缺 %s 声明（预期含 v2.20/check1-31/PASS=49）" % (name, what))
    return issues, {"verify_version": ver, "checks": n_checks}
