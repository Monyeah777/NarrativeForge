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

#: 当前基线声明（verify 每次扩 check 时同步：check 数 + PASS 期望值）。
#: 本模块以 verify.sh 为单一真值做四处自洽断言，期望值集中在此，避免散落字面量。
EXPECTED_CHECKS = 36
EXPECTED_PASS = 59


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    issues: List[str] = []
    verify_text = (r / "verify.sh").read_text(encoding="utf-8")
    m = re.search(r"# 版本 : (v\d+\.\d+)", verify_text)
    ver = m.group(1) if m else ""
    nums = sorted({int(x) for x in re.findall(r"^check(\d+)\(\)\{", verify_text, re.M)})
    n_checks = len(nums)
    if not ver:
        issues.append("verify.sh 缺版本头（vX.Y）")
    if n_checks != EXPECTED_CHECKS or nums != list(range(1, EXPECTED_CHECKS + 1)):
        issues.append("verify.sh check 函数数/编号异常：%s" % nums)

    checks: List[Tuple[str, str, int]] = []
    readme = (r / "README.md").read_text(encoding="utf-8")
    checks.append(("README", "基线句",
                  1 if all(t in readme for t in (
                      ver, "check1-%d" % EXPECTED_CHECKS,
                      "PASS=%d" % EXPECTED_PASS))
                   else 0))
    changelog = (r / "CHANGELOG.md").read_text(encoding="utf-8")
    head = changelog.split("\n## [2.8.0]", 1)[0]
    checks.append(("CHANGELOG 最新节", "PASS=%d" % EXPECTED_PASS,
                   head.count("PASS=%d" % EXPECTED_PASS)))
    matrix = (r / "VERSION-MATRIX.md").read_text(encoding="utf-8")
    checks.append(("VERSION-MATRIX", "PASS=%d" % EXPECTED_PASS,
                   matrix.count("PASS=%d" % EXPECTED_PASS)))
    for name, what, n in checks:
        if n < 1:
            issues.append("%s 缺 %s 声明（预期含 v2.x/check1-%d/PASS=%d）"
                          % (name, what, EXPECTED_CHECKS, EXPECTED_PASS))
    return issues, {"verify_version": ver, "checks": n_checks}
