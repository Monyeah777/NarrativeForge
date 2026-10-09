# -*- coding: utf-8 -*-
"""导出契约面 manifest 的**门禁判据**单测（check29 面，2026-10-07 强化）。

原差距（三轴审计 G3）：判据是「gate 出现在 verify.sh 文本里」——**注释里写一句 check18/22
就算过**。本件把强化后的三类负例钉死：未定义 / 未在主执行体调用 / 任何分支都不会红；
并给正例对照，另设「真仓零 issue」防判据误伤（强化不能把真仓判红）。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import conformance_scan as cs  # noqa: E402

MANIFEST = {"items": [{"id": "demo", "conformance": "L3", "evidence": [],
                       "gates": ["check18"]}]}
RUN_HEAD = "# ================= 主执行体（三段式） =================\n"
GOOD_BODY = 'check18(){\n  no "x"; err=1\n}\n'


def _issues(verify_text):
    issues, _n = cs.export_manifest_issues(str(ROOT), verify_text, MANIFEST)
    return issues


class ExportManifestGateTest(unittest.TestCase):
    def test_gate_mentioned_only_in_comment_is_rejected(self):
        issues = _issues("#!/bin/bash\n# 导出面由 check18/22 锁定\n")
        self.assertEqual(1, len(issues))
        self.assertIn("无 check 定义", issues[0])

    def test_defined_but_never_called_is_rejected(self):
        issues = _issues(GOOD_BODY + RUN_HEAD + "check19\n")
        self.assertEqual(1, len(issues))
        self.assertIn("未在主执行体调用", issues[0])

    def test_called_but_cannot_fail_is_rejected(self):
        issues = _issues('check18(){\n  ok "x"\n}\n' + RUN_HEAD + "check18\n")
        self.assertEqual(1, len(issues))
        self.assertIn("无可失败路径", issues[0])

    def test_legal_gate_passes(self):
        self.assertEqual([], _issues(GOOD_BODY + RUN_HEAD + "check18\n"))

    def test_real_repo_manifest_is_clean(self):
        """强化后的判据不得把真仓判红（真仓的 check18/22 都是定义 + 调用 + 有失败路径）。"""
        verify = (ROOT / "verify.sh").read_text(encoding="utf-8")
        self.assertEqual([], _issues(verify))

    def test_gate_name_is_resolved_not_substring_matched(self):
        """check18extra 不得被当成 check18 的证据（旧口径的子串匹配正会放它过去）。"""
        bad = {"items": [{"id": "demo", "conformance": "L3", "evidence": [],
                          "gates": ["check18extra"]}]}
        issues, _n = cs.export_manifest_issues(str(ROOT), GOOD_BODY + RUN_HEAD + "check18\n", bad)
        self.assertEqual(1, len(issues))
        self.assertIn("无 check 定义", issues[0])


if __name__ == "__main__":
    unittest.main()
