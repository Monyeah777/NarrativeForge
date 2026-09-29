#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作流供应链策略（`core/workflow_policy.py`）回归测试 —— 外部标准落地面。

标准出处：`ossf/scorecard` `docs/checks.md` §Pinned-Dependencies（构建/发布依赖须钉具体哈希）
与 §Token-Permissions（GITHUB_TOKEN 权限须显式且最小）。
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import workflow_policy as wp  # noqa: E402

SHA = "1" * 40


def _wf(tmp: str, name: str, body: str) -> None:
    d = Path(tmp) / wp.WORKFLOWS_REL
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(body, encoding="utf-8")


def _reqs(tmp: str, lines) -> None:
    d = Path(tmp) / ".github"
    d.mkdir(parents=True, exist_ok=True)
    (d / "requirements-ci.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


class WorkflowPolicyTest(unittest.TestCase):
    def test_pinned_uses_with_permissions_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "ok.yml", "name: ok\npermissions:\n  contents: read\n"
                               "steps:\n  - uses: actions/checkout@%s  # v4\n" % SHA)
            issues, warns, stats = wp.scan(tmp)
        self.assertEqual([], issues)
        self.assertEqual([], warns)
        self.assertEqual({"workflows": 1, "pinned_uses": 1, "with_explicit_permissions": 1,
                          "requirements_files": 0}, stats)

    def test_mutable_ref_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "bad.yml", "permissions: read-all\nsteps:\n  - uses: actions/checkout@v4\n")
            issues, _w, _s = wp.scan(tmp)
        self.assertTrue(any("未钉提交 SHA" in i and "修复指引" in i for i in issues), issues)

    def test_missing_or_write_all_permissions_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "noperm.yml", "steps:\n  - uses: actions/checkout@%s  # v4\n" % SHA)
            missing, _w, _s = wp.scan(tmp)
            _wf(tmp, "wide.yml", "permissions: write-all\nsteps:\n"
                                 "  - uses: actions/checkout@%s  # v4\n" % SHA)
            wide, _w2, _s2 = wp.scan(tmp)
        self.assertTrue(any("缺显式 permissions" in i for i in missing), missing)
        self.assertTrue(any("write-all" in i for i in wide), wide)

    def test_local_action_is_exempt_and_missing_comment_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "local.yml", "permissions: read-all\nsteps:\n  - uses: ./.github/actions/x\n")
            issues, _w, _s = wp.scan(tmp)
            _wf(tmp, "nocomment.yml", "permissions: read-all\n"
                                      "steps:\n  - uses: actions/checkout@%s\n" % SHA)
            _i2, warns, _s2 = wp.scan(tmp)
        self.assertEqual([], issues, "本地动作不该被判")
        self.assertTrue(any("版本注释" in w for w in warns), warns)

    def test_real_repo_workflows_are_all_pinned(self):
        """真仓：所有 `uses:` 都钉提交 SHA，且每个工作流都有显式 permissions。"""
        issues, _warns, stats = wp.scan(str(ROOT))
        self.assertEqual([], issues)
        self.assertGreaterEqual(stats["workflows"], 10, "工作流件数须有规模（判据自身要有效）")
        self.assertGreaterEqual(stats["pinned_uses"], 10)
        self.assertGreaterEqual(stats["requirements_files"], 3, "固定依赖清单须在场")
        self.assertEqual(stats["workflows"], stats["with_explicit_permissions"],
                         "每个工作流都须显式声明 permissions")

    def test_unpinned_requirement_is_rejected(self):
        """FAIR4RS 的 R 面：依赖清单须钉 `==`（浮动的 `>=` 判 FAIL）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "ok.yml", "permissions: read-all\nsteps:\n  - uses: ./.local\n")
            _reqs(tmp, ["# 注释行豁免", "pyyaml==6.0.1"])
            pinned, _w, _s = wp.scan(tmp)
            _reqs(tmp, ["pyyaml>=6"])
            floating, _w2, _s2 = wp.scan(tmp)
        self.assertEqual([], pinned, pinned)
        self.assertTrue(any("未钉版本" in i and "修复指引" in i for i in floating), floating)


if __name__ == "__main__":
    unittest.main()
