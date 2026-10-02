# -*- coding: utf-8 -*-
"""协议多出口 rules 渲染单测（v2.5.0 Wave4 A3：protocol.yaml → agents/claude/skill）。

运行：cd desktop && python -m unittest tests.test_rules_render -v
真实 community 包 protocol.yaml → 三格式渲染，断言结构 + 范围纪律。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.rules_render import _RULES_RENDERERS, render_protocol  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
PKG = ROOT / "community" / "技术文档域包"


class TestRenderProtocol(unittest.TestCase):
    def test_agents_has_header_and_modules(self):
        txt = render_protocol(str(PKG), "agents")
        self.assertIn("# Agent Operating Rules", txt)
        self.assertIn("技术文档域包", txt)
        self.assertIn("M97", txt)   # 模块清单进 rules
        self.assertIn("M98", txt)

    def test_claude_matches_agents(self):
        self.assertEqual(render_protocol(str(PKG), "claude"),
                         render_protocol(str(PKG), "agents"))

    def test_skill_has_frontmatter_and_body(self):
        txt = render_protocol(str(PKG), "skill")
        self.assertTrue(txt.startswith("---\n"))
        self.assertIn("name:", txt)
        self.assertIn("description:", txt)
        self.assertIn("# 技术文档域包", txt)

    def test_registry_scope_discipline(self):
        # 范围纪律：只挂已交付 agents/claude/skill 三格
        self.assertEqual(set(_RULES_RENDERERS), {"agents", "claude", "skill"})

    def test_unregistered_fmt_raises(self):
        with self.assertRaises(KeyError):
            render_protocol(str(PKG), "mcp")


class RenderCliErrorFramingTest(unittest.TestCase):
    """`nf render <dir>` 的**输入错误**必须是干净错误（不得报成「内部错误」）。

    实测（2026-09-30 全命令面系统扫：65 命令 × 2 种畸形输入）——此处是唯一余项：修复前
    给不存在的目录会漏成「内部错误：No such file or directory: '…\\protocol.yaml'（重跑
    NF_DEBUG=1 看堆栈）」，把用户输入问题说成内部故障。
    """

    def _run(self, *argv):
        import subprocess
        root = Path(__file__).resolve().parents[2]
        return subprocess.run([sys.executable, str(root / "scripts" / "nf.py"), *argv],
                              capture_output=True, encoding="utf-8", errors="replace",
                              timeout=180)

    def test_missing_package_dir_is_a_clean_error(self):
        p = self._run("render", "__NF_PROBE__")
        self.assertEqual(2, p.returncode)
        self.assertIn("不是协议包目录", p.stderr)
        self.assertNotIn("内部错误", p.stderr)
        self.assertNotIn("NF_DEBUG", p.stderr)

    def test_dir_without_protocol_yaml_is_a_clean_error(self):
        p = self._run("render", "protocol")
        self.assertEqual(2, p.returncode)
        self.assertIn("protocol.yaml", p.stderr)
        self.assertNotIn("内部错误", p.stderr)


if __name__ == "__main__":
    unittest.main()
