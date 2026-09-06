# -*- coding: utf-8 -*-
"""钢人论证模块单测（v2.6-A：nf design steelman——可选决策辅助）。

运行：cd desktop && python -m unittest tests.test_steelman -v
覆盖：init 工作单 schema（frontmatter + 六段 + 模板注释）/
check 四步齐备与缺项 warn / ls 索引 / 模板引导三套。
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.steelman import (  # noqa: E402
    init_worksheet,
    check_worksheet,
    scan_steelman,
    STEELMAN_SECTIONS,
)
from core import steelman as sm  # noqa: E402


class TestSteelmanInit(unittest.TestCase):
    def test_init_has_frontmatter_and_six_sections(self):
        txt = init_worksheet("是否该为端壳大规模重构立项？", context="38 方案")
        self.assertTrue(txt.startswith("---\n"))
        for key in ("decision:", "date:", "decider:", "context:", "related:"):
            self.assertIn(key, txt.split("---")[1])
        for sec in ("## 1. 问题重述", "## 2. 支持侧最强论据",
                    "## 3. 反对侧最强论据", "## 4. 核心变量",
                    "## 5. 判断与理由", "## 6. 回退路径"):
            self.assertIn(sec, txt)
        self.assertEqual(len(STEELMAN_SECTIONS), 6)

    def test_init_includes_prompt_templates(self):
        txt = init_worksheet("测试问题", context="")
        for marker in ("Prompt A", "Prompt B", "Prompt C"):
            self.assertIn(marker, txt)

    def test_init_writes_file_when_path_given(self):
        d = Path(tempfile.mkdtemp(prefix="nf_steelman_"))
        out = d / "steelman.md"
        init_worksheet("测试问题", context="", path=out)
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("测试问题", content)


class TestSteelmanCheck(unittest.TestCase):
    def test_complete_worksheet_passes(self):
        """六段齐备 + 正反论据各 ≥3 + 核心变量 + 判断含理由与回退 → 无缺项。"""
        full = _make_complete()
        warns = check_worksheet(full)
        self.assertEqual(warns, [])

    def test_missing_opposing_arguments_warns(self):
        txt = init_worksheet("问题", context="")
        warns = check_worksheet(txt)
        self.assertTrue(any("反对侧" in w for w in warns))

    def test_check_reports_section_gaps(self):
        """空工作单（仅占位模板）应报缺项：正反论据不足/核心变量缺/回退缺。

        注：问题重述已在 init 时预填（**问题** 即 1 节内容）——不属缺项。
        """
        txt = init_worksheet("问题", context="")
        warns = check_worksheet(txt)
        joined = "\n".join(warns)
        self.assertIn("支持侧论据", joined)
        self.assertIn("反对侧论据", joined)
        self.assertIn("核心变量", joined)
        self.assertIn("回退路径", joined)


def _make_complete() -> str:
    """构造一份 check 全过的工作单（六段齐备 + 正反论据各 3 + 核心变量 + 判断 + 回退）。"""
    lines = [
        "---", "decision: 做", "date: 2026-09-06", "decider: 测试者",
        "context: 38 方案", "related: []", "---",
        "## 1. 问题重述", "这是完整重述，足够长的一段话说明真正要解决的问题及其背景约束。",
        "## 2. 支持侧最强论据",
        "- 支持论据一", "- 支持论据二", "- 支持论据三",
        "## 3. 反对侧最强论据",
        "- 反对论据一", "- 反对论据二", "- 反对论据三",
        "## 4. 核心变量", "市场是否接受该形态",
        "## 5. 判断与理由",
        "**判断**：做",
        "**理由**：", "1. 理由一", "2. 理由二", "3. 理由三",
        "## 6. 回退路径", "回退到薄壳接线交付",
    ]
    return "\n".join(lines) + "\n"


class TestSteelmanScan(unittest.TestCase):
    def test_scan_finds_md_files_with_frontmatter(self):
        d = Path(tempfile.mkdtemp(prefix="nf_steelman_scan_"))
        (d / "a.md").write_text(init_worksheet("决策甲", context="x"),
                                encoding="utf-8")
        (d / "b.txt").write_text("不是工作单", encoding="utf-8")
        hits = scan_steelman(d)
        self.assertEqual(len(hits), 1)
        self.assertIn("决策甲", hits[0])

    def test_scan_empty_dir(self):
        d = Path(tempfile.mkdtemp(prefix="nf_steelman_empty_"))
        self.assertEqual(scan_steelman(d), [])


class TestSteelmanConstantDriven(unittest.TestCase):
    """回归：check/init 的六节标题与 STEELMAN_SECTIONS 单一来源——
    改常量（标题文案）须同时作用于 init 生成与 check 校验，不得硬编码字面量。"""

    def test_renamed_section_title_propagates_to_init_and_check(self):
        orig = list(sm.STEELMAN_SECTIONS)
        renamed = [t.replace("最强论据", "论据") if "最强论据" in t else t
                   for t in orig]
        self.assertNotEqual(orig, renamed)
        try:
            sm.STEELMAN_SECTIONS = renamed
            # init 写出的是常量里的新标题
            emitted = init_worksheet("常量驱动测试", context="38")
            for new in renamed:
                self.assertIn(f"## {new}", emitted)
            self.assertNotIn("## 2. 支持侧最强论据", emitted)
            # check 按新标题定位节——用新标题写的完整工作单应零缺项
            full = _make_complete()
            for old, new in zip(orig, renamed):
                if old != new:
                    full = full.replace(f"## {old}", f"## {new}")
            self.assertEqual(check_worksheet(full), [])
        finally:
            sm.STEELMAN_SECTIONS = orig


class TestSteelmanPlaceholder(unittest.TestCase):
    """回归：占位判定只认 init 预置模板的精确文本——
    整行括号包裹的真实论据不得被误判为占位（避免误报缺项）。"""

    def test_parenthesized_real_bullet_is_counted(self):
        full = _make_complete()
        full = full.replace(
            "- 支持论据二",
            "- （真实论据：需在括号内完整陈述，见 38 方案社区路线约束）")
        self.assertEqual(check_worksheet(full), [])


if __name__ == "__main__":
    unittest.main()
