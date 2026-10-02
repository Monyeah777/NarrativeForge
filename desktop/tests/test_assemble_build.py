# -*- coding: utf-8 -*-
"""组装式命令（`core/assemble_build.py`）回归测试。

判据：产物必须是**八段骨架**的单文件完整版、经 `assemble_plan.check` 零 issue
（编号在允许集 / 决策句带引用）、且**同输入同输出**（确定性）。预设与自定义两条路都测。
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import assemble_build as ab  # noqa: E402
from core import assemble_plan as ap  # noqa: E402


class AssembleBuildTest(unittest.TestCase):
    def _build(self, requirement):
        plan = ap.plan(requirement)
        return plan, ab.build(str(ROOT), requirement, plan)

    def test_preset_build_covers_skeleton_and_passes_check(self):
        requirement = "帮我组装一个校园情感世界的完整版"
        plan, (text, stats) = self._build(requirement)
        self.assertTrue(plan["matched"], "示例需求应命中官方预设")
        self.assertEqual(8, stats["segments"])
        for seg in range(8):
            self.assertIn("## %d." % seg, text, "缺段 ##%d" % seg)
        issues, cstats = ap.check(text, plan)
        self.assertEqual([], issues, "产物未过自组装机器验收：%s" % issues)
        self.assertEqual(8, cstats["segments"])
        # 预设档：官方核心 + 包题材件都应在册（数量 > 官方核心 13 件）
        self.assertGreater(stats["modules"], 13)

    def test_custom_build_falls_back_to_core_only(self):
        requirement = "帮我做一个悬疑都市的完整版"
        plan, (text, stats) = self._build(requirement)
        self.assertFalse(plan["matched"])
        self.assertEqual([], ap.check(text, plan)[0])
        self.assertEqual(13, stats["modules"], "自定义档应只装官方核心，避免 200+ 件灌水")
        self.assertIn("自定义取件口径", text)

    def test_build_is_deterministic(self):
        requirement = "帮我组装一个西幻生存世界的完整版"
        _, (a, _) = self._build(requirement)
        _, (b, _) = self._build(requirement)
        self.assertEqual(a, b, "组装式命令必须同输入同输出（禁写入时间戳）")


class DestGuardTest(unittest.TestCase):
    """落点安全（agent 密集重复调用面）：真源面默认拒写，仓库外/普通目录放行。"""

    def test_true_source_faces_are_refused(self):
        for dest in ("04_模块库", "protocol", "community", "05_资产库", "docs/standards"):
            msg = ab.check_dest(str(ROOT), dest)
            self.assertTrue(msg, "落点 %s 应被拒" % dest)
            self.assertIn("修复指引", msg)

    def test_normal_destinations_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual("", ab.check_dest(str(ROOT), tmp))
            self.assertEqual("", ab.check_dest(str(ROOT), ""))
            self.assertEqual("", ab.check_dest(str(ROOT), "out"))

    def test_protected_prefixes_come_from_layers_declaration(self):
        """单一真源：受保护前缀取自 protocol/LAYERS.json，不是代码里的第二份清单。"""
        pre = ab.protected_prefixes(str(ROOT))
        self.assertIn("protocol/", pre)
        self.assertIn("04_模块库/", pre)


if __name__ == "__main__":
    unittest.main()
