# -*- coding: utf-8 -*-
"""zone_a_import 外部产物登记回归（38 W1 复核：类别契约 + 空 IR 守卫）。

RED 来源（对抗验证 rejected 根因）：_install_external_ir 把 IR full_id 的
短类别段（情感:M22 → 情感）直接作 Module.category 落盘；而存储层契约
（models.CATEGORIES / parser.cat_map / fid_key docstring）为长类别
（情感类）。短类别目录 modules/情感/M22_x 与 canonical modules/情感类/
M22_x 同 fid_key → 同一 full_id 双模块，击穿 save_module 幂等装载语义。

用例：
1. _external_ir_modules 类别归一：IR full_id 短类别（情感:M22）→ 落盘
   Module.category 为长类别（情感类）；长类别（情感类:M22）幂等保持；
   裸号（M90）兜底通用类。
2. 空 IR / 0 模块条目 → []（do_install 据此不发空信号/刷新噪音）。
3. 真实 Store 集成：短类别转换落盘后与 canonical 长类别目录收敛为单目录，
   get_module 按短名（情感:M22）与长名（情感类:M22）双向命中且唯一。

运行：cd desktop && python3 -m unittest tests.test_zone_a_import -v
（unittest discover -s tests -q 自动收编）
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # desktop/

from src.core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from src.core.models import CATEGORIES, fid_key  # noqa: E402
from src.core.storage import Store  # noqa: E402
from src.ui.zone_a_import import (  # noqa: E402
    _canon_category,
    _external_ir_modules,
)


def _ir(*mods: IRModule, extra: list | None = None) -> IRDocument:
    """构造含一层 modules + extra 的 IRDocument。"""
    ir = IRDocument(pipeline_id="P01")
    if mods:
        ir.layers.append(IRLayer(id="P40", name="层", modules=list(mods)))
    ir.extra_modules = list(extra or [])
    return ir


class TestCanonCategory(unittest.TestCase):
    """类别短名 → 存储层长名契约（对齐 parser.cat_map 与 CATEGORIES）。"""

    def test_short_to_long(self):
        for long_name in CATEGORIES:
            short = long_name.rstrip("类")
            self.assertEqual(_canon_category(short), long_name,
                             f"{short} 应归一到 {long_name}")

    def test_long_passthrough(self):
        self.assertEqual(_canon_category("情感类"), "情感类")
        self.assertEqual(_canon_category("技术文档类"), "技术文档类")

    def test_empty_defaults_common(self):
        self.assertEqual(_canon_category(""), "通用类")
        self.assertEqual(_canon_category("  "), "通用类")


class TestExternalIrModules(unittest.TestCase):
    """IRModule → 落盘 Module：类别归一是根因修复点。"""

    def test_short_category_normalized(self):
        ir = _ir(IRModule(full_id="情感:M22", name="三冲动驱动",
                          layer="P40", content="正文"))
        ms = _external_ir_modules(ir)
        self.assertEqual(len(ms), 1)
        m = ms[0]
        self.assertEqual(m.category, "情感类")   # 不再落短类别 情感
        self.assertEqual(m.id, "M22")
        self.assertEqual(m.full_id, "情感类:M22")
        self.assertEqual(m.source_md, "正文")

    def test_long_category_idempotent(self):
        ir = _ir(IRModule(full_id="情感类:M22", name="三冲动驱动",
                          layer="P40"))
        m = _external_ir_modules(ir)[0]
        self.assertEqual(m.category, "情感类")

    def test_bare_id_falls_back_common(self):
        ir = _ir(IRModule(full_id="M90", name="技术文档结构", layer="P90"))
        m = _external_ir_modules(ir)[0]
        self.assertEqual(m.category, "通用类")
        self.assertEqual(m.id, "M90")

    def test_extra_modules_also_normalized(self):
        ir = IRDocument(pipeline_id="P01")
        ir.extra_modules = [IRModule(full_id="生存:M10", name="死亡处理",
                                     layer="P40")]
        m = _external_ir_modules(ir)[0]
        self.assertEqual(m.category, "生存类")

    def test_empty_ir_yields_empty(self):
        # 空 IR / 0 模块条目 → []（do_install 据此不发空信号/空刷新）
        self.assertEqual(_external_ir_modules(_ir()), [])
        self.assertEqual(_external_ir_modules(
            IRDocument(pipeline_id="")), [])


class TestStoreConvergence(unittest.TestCase):
    """真实 Store 集成：短/长类别最终收敛为单目录（幂等装载不双模块）。"""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="nf_zone_a_")
        self.store = Store(home=self.home)

    def test_short_then_long_converges_single(self):
        # 旧路径：短类别直接落盘 → modules/情感/M22_x
        m_short = _external_ir_modules(_ir(
            IRModule(full_id="情感:M22", name="三冲动驱动", layer="P40")))[0]
        self.assertEqual(m_short.category, "情感类")   # 修复后即长类别
        # 直接构造短类别模块模拟历史/其它入口遗留
        from src.core.models import Module
        legacy = Module(id="M22", name="三冲动驱动", category="情感",
                        layer="P40", source_md="正文")
        d_legacy = self.store.save_module(legacy)
        self.assertTrue("情感" in str(d_legacy))       # 遗留目录 情感/M22_x
        # 再存 canonical 长类别（与 _external_ir_modules 落盘形态一致）
        self.store.save_module(m_short)
        mods = self.store.list_modules()
        self.assertEqual(len(mods), 1)                  # 收敛为单模块
        # 双向命中且唯一
        self.assertIsNotNone(self.store.get_module("情感:M22"))
        self.assertIsNotNone(self.store.get_module("情感类:M22"))
        self.assertEqual(fid_key(mods[0].full_id), "情感:M22")
        self.assertEqual(mods[0].category, "情感类")    # 最终为长类别


if __name__ == "__main__":
    unittest.main()
