# -*- coding: utf-8 -*-
"""组合运行时调度单测（v2.0.x-E3：resolve_combination references 运行时消费）。

运行：cd desktop && python -m unittest tests.test_composer -v
覆盖：轻混 P04 registry references → own(M91/M92) + ref(M55校园/M17西幻) + core
    引用模块从 source 包 parse 装载；引用缺失 warn；build_assembly 合并入装配。
真实 repo 依赖：community/（校园情感领域包/西幻生存领域包/校园西幻轻混组合包）。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.storage import Store  # noqa: E402
from core.pipeline_loader import load_pipeline_file  # noqa: E402
from core.composer import (  # noqa: E402
    resolve_combination, build_assembly, Combination)

_REPO = Path(__file__).resolve().parents[2]


def _store_with_lightmix():
    """Store 装载轻混自带模块 M91/M92（官方核心不装——composer 只管组合解析）。"""
    store = Store(home=tempfile.mkdtemp(prefix="nf_com_"))
    from core.parser import parse_module
    pkg = _REPO / "community" / "校园西幻轻混组合包" / "modules"
    for f in sorted(pkg.glob("*.md")):
        try:
            store.save_module(parse_module(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return store


def _p04():
    return load_pipeline_file(
        _REPO / "community" / "校园西幻轻混组合包" / "pipelines" /
        "P04_轻混装配流管线.md")


class TestResolveCombination(unittest.TestCase):
    def setUp(self):
        self.store = _store_with_lightmix()
        self.p04 = _p04()

    def test_references_resolved_from_registry(self):
        combo = resolve_combination(self.store, self.p04)
        self.assertIsInstance(combo, Combination)
        # own 由调用方 selected 决定（build_assembly 填）；本函数验 references
        ref_ids = [m.full_id for m in combo.reference_modules]
        self.assertTrue(any("M55" in i for i in ref_ids),
                        f"引用校园 M55 未解析：{ref_ids}")
        self.assertTrue(any("M17" in i for i in ref_ids),
                        f"引用西幻 M17 未解析：{ref_ids}")

    def test_reference_module_has_content(self):
        combo = resolve_combination(self.store, self.p04)
        for m in combo.reference_modules:
            self.assertTrue(m.source_md or m.logic,
                            f"{m.full_id} 无正文——引用模块应装载 source 内容")

    def test_no_reference_protocol_empty(self):
        # 官方 P01（registry 无 protocols 条目）→ references 空，无引用模块
        p01 = load_pipeline_file(_REPO / "03_管线库" / "P01_标准管线.md")
        combo = resolve_combination(self.store, p01)
        self.assertEqual(combo.reference_modules, [])


class TestBuildAssembly(unittest.TestCase):
    def setUp(self):
        self.store = _store_with_lightmix()
        self.p04 = _p04()

    def test_assembly_merges_references(self):
        sel = [m for m in self.store.list_modules()]   # M91/M92 全选
        mods = build_assembly(self.store, self.p04, sel,
                              include_references=True)
        full = {m.full_id for m in mods}
        self.assertTrue(any("M91" in f for f in full))
        self.assertTrue(any("M92" in f for f in full))
        # references 运行时入装配（M55/M17 正文进 mods）
        self.assertTrue(any("M55" in f for f in full),
                        f"引用 M55 未入装配：{sorted(full)}")
        self.assertTrue(any("M17" in f for f in full))

    def test_include_references_off_keeps_own(self):
        sel = [m for m in self.store.list_modules()]
        mods = build_assembly(self.store, self.p04, sel,
                              include_references=False)
        full = {m.full_id for m in mods}
        self.assertFalse(any("M55" in f for f in full))


if __name__ == "__main__":
    unittest.main()
