#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试套件**接线**门禁：不许有「写好了却没人跑」的套件。

为什么（2026-10-03 两次实证）：
① `packaging/npm/test/smoke.test.mjs` 只在发布工作流里跑，常驻面从没跑过它（已接线，
   见 `desktop/tests/test_npm_package.py`）；
② 本会话新增的 CLI 入口 `scripts/orchestrate.py` 一度只有自己能跑、没有任何判据。
这类缺口**不会报错**，只会静默积累——所以把「要么进 discover 面，要么登记由谁跑」立成常驻判据。

面 = 仓库件（`core.repo_face`）；`desktop/tests/**` 即 `unittest discover` 面；
其余语种的套件（.NET / Rust / node）登记进 `EXTERNAL_SUITES` 并写明由谁跑。
"""
import fnmatch
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import repo_face as _repo_face  # noqa: E402

#: discover 面（`cd desktop && python -m unittest discover -s tests`）
DISCOVERED_PREFIX = "desktop/tests/"
#: 扫描根（只在这些树里找套件；`.rivet/` 是本地工作区，`community/` 是内容面）
ROOTS = ("desktop/", "scripts/", "engine/", "packaging/", "tui/", ".github/")
#: 套件命名模式（各语言惯例；刻意不收「目录名叫 tests」这种宽判据，避免误伤夹具目录）
PATTERNS = ("test_*.py", "*_test.py", "*.test.mjs", "test_*.mjs", "*.test.js",
            "*Test.cs", "*Tests.cs", "test_*.rs", "*_test.rs")
#: 不在 discover 面、但**有明确执行方**的套件（逐条写明由谁跑；本表只许缩小）
EXTERNAL_SUITES = {
    "packaging/npm/test/smoke.test.mjs":
        "由 desktop/tests/test_npm_package.py 常驻执行（node --test）",
    "engine/dotnet/src/Nf.Engine/SelfTest.cs":
        ".NET 线自带工作流（net-engine.yml）与 engine/dotnet/RUNBOOK.md 流程",
}
#: 塌缩下限（本仓当前 180+；低于此值说明判据面失效）
MIN_DISCOVERED = 150


def _suites(root=ROOT):
    """仓库里的测试套件相对路径（面 = 仓库件，单一出处）。"""
    out = []
    for p in _repo_face.walk_repo_paths(str(root)):
        rel = p.relative_to(root).as_posix()
        if not rel.startswith(ROOTS):
            continue
        if "/node_modules/" in rel or "/target/" in rel or "/obj/" in rel or "/bin/" in rel:
            continue
        if any(fnmatch.fnmatch(p.name, pat) for pat in PATTERNS):
            out.append(rel)
    return sorted(out)


def unwired(suites, external=None):
    """既不在 discover 面、也没登记的套件（纯函数，便于变异自证）。"""
    known = EXTERNAL_SUITES if external is None else external
    return [s for s in suites if not s.startswith(DISCOVERED_PREFIX) and s not in known]


class SuiteWiringTest(unittest.TestCase):
    def test_no_suite_is_left_unwired(self):
        suites = _suites()
        discovered = [s for s in suites if s.startswith(DISCOVERED_PREFIX)]
        self.assertGreaterEqual(len(discovered), MIN_DISCOVERED,
                                "discover 面塌缩（判据可能已失效）：%d" % len(discovered))
        bad = unwired(suites)
        self.assertEqual([], bad,
                         "有测试套件没人跑（修复指引：放进 desktop/tests 由 discover 执行，"
                         "或登记进 EXTERNAL_SUITES 并写明由谁跑）：%s" % bad)

    def test_external_registry_is_not_stale(self):
        suites = set(_suites())
        stale = sorted(k for k in EXTERNAL_SUITES if k not in suites)
        self.assertEqual([], stale, "登记表里有已不存在的套件（表只许缩小）：%s" % stale)


class SuiteWiringRuleTest(unittest.TestCase):
    def test_predicate_flags_unwired_and_spares_wired(self):
        self.assertEqual([], unwired(sorted(DISCOVERED_PREFIX + "test_x.py" for _ in range(3))
                                     + sorted(EXTERNAL_SUITES), external=EXTERNAL_SUITES))
        self.assertEqual(["engine/rust/tests/foo_test.rs"],
                         unwired(["engine/rust/tests/foo_test.rs"]))


if __name__ == "__main__":
    unittest.main()
