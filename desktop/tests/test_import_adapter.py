# -*- coding: utf-8 -*-
"""读入适配器单测（v2.3.0 34 方案：A4 双向读入——parse_skill / parse_ccv3）。

对称面：export(ir, 'skill'|'ccv3')（exporter._REGISTRY，全 export-only）→
import_adapter 的 parse_skill / parse_ccv3 反向闭环。五组用例：

1. NF 结构层 round-trip 逐字节：自举 SKILL.md（fixtures/external/技术文档装配战例
   /SKILL.md，428B）→ parse_skill(mode='nf') → export(ir, 'skill')
   → 输出 == 原文（逐字节，含 frontmatter/空行/末尾无换行）。
2. 外部宽容层：anthropic-official 官方 docx / skill-creator 两份 SKILL.md
   parse 不抛错、mode='external'、frontmatter name/description 正确提取
   （docx description 为双引号包裹单行，剥外层引号保留内部裸单引号与冒号）、
   docx license 扩展字段透传、body 原样保留（由消费方判定升 IR）。
3. 失败路径：空文本 / 无 frontmatter / frontmatter 未闭合 / 缺 name /
   缺 description / 空正文 → ValueError；parse_ccv3：chara 非 dict /
   spec 不符 / 缺 spec_version / world 非 dict → ValueError。
4. parse_ccv3 结构还原：自举 chara.json（+ 同源 world.json）→ 叙事 IR 骨架
   ——IRLayer(P90 · 技术文档生成) + M90/M97 模块 + chara/world 同源按
   full_id 去重不重复入 IR + description「（P06）装配产物」回填 pipeline
   字段 + chara_meta 顶层透传。
5. exporter 反向登记：exporter._REGISTRY_IN 只挂已交付的 skill/ccv3 两格
   （范围纪律——agents/claude/mcp 未交付读入适配器不登记），且经该登记面
   skill 格 parse→export 逐字节 round-trip 走通（登记不是摆设）。

运行：cd desktop && python3 -m unittest tests.test_import_adapter -v
（check12 经 `python3 -m unittest discover -s tests -q` 自动收编）
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.import_adapter import parse_ccv3, parse_frontmatter, parse_skill  # noqa: E402
from core import exporter  # noqa: E402
from core.exporter import export  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "external"
BOOTSTRAP_SKILL = FIXTURES / "技术文档装配战例" / "SKILL.md"
DOCX_OFFICIAL = FIXTURES / "anthropic-official" / "docx.SKILL.md"
SC_OFFICIAL = FIXTURES / "anthropic-official" / "skill-creator.SKILL.md"
BOOTSTRAP_CHARA = FIXTURES / "chara.json"
BOOTSTRAP_WORLD = FIXTURES / "world.json"


# ---------------------------------------------------------- NF 结构层 round-trip
class TestParseSkillRoundTrip(unittest.TestCase):
    """自举 techdoc SKILL.md：parse_skill → export(ir,'skill') 逐字节闭环。"""

    def setUp(self):
        self.dest = Path(tempfile.mkdtemp(prefix="nf_import_skill_"))
        self.text = BOOTSTRAP_SKILL.read_text(encoding="utf-8")
        self.res = parse_skill(self.text)

    def test_mode_nf_and_ir_present(self):
        self.assertTrue(self.res.ok)
        self.assertEqual(self.res.mode, "nf")
        self.assertIsNotNone(self.res.ir)

    def test_ir_shape_techdoc(self):
        ir = self.res.ir
        self.assertEqual(ir.type, "techdoc")
        self.assertEqual(ir.title, "技术文档装配战例")
        self.assertEqual(ir.pipeline_id, "P06")          # description 回填
        self.assertEqual(ir.pipeline_name, "技术文档题材装配流")
        self.assertEqual(len(ir.layers), 1)
        layer = ir.layers[0]
        self.assertEqual(layer.id, "P90")
        self.assertEqual(layer.name, "技术文档生成")
        ids = [m.full_id for m in layer.modules]
        self.assertEqual(ids, ["M90", "M97"])
        by_id = {m.full_id: m for m in layer.modules}
        self.assertEqual(by_id["M90"].name, "技术文档结构")
        self.assertEqual(
            by_id["M90"].content,
            "结构骨架与模板装载规则：文档 = 骨架 + 装载规则。")
        self.assertEqual(
            by_id["M97"].content,
            "术语表：新词先定义后使用，术语条目 = 原文 + 译名 + 上下文约束。")
        self.assertEqual(ir.extra_modules, [])
        self.assertEqual(ir.meta.get("adapter_in"), "parse_skill")

    def test_roundtrip_byte_exact(self):
        """parse_skill → export(ir,'skill') → 输出与原 SKILL.md 逐字节相等。"""
        out = export(self.res.ir, "skill", dest_dir=self.dest)
        self.assertEqual(len(out.files), 1)
        out_text = Path(out.files[0]).read_text(encoding="utf-8")
        self.assertEqual(out_text, self.text)

    def test_no_spurious_warning(self):
        """描述声明 2 块、正文实解 2 块 → 无「以正文为准」类警告。"""
        self.assertFalse(any("以正文为准" in w for w in self.res.warnings))


# ------------------------------------------------------ 外部宽容层（官方兼容）
class TestParseSkillExternalTolerant(unittest.TestCase):
    """anthropic-official 两份官方技能：不崩、不静默丢、引号/扩展字段正确。"""

    def setUp(self):
        self.dest = Path(tempfile.mkdtemp(prefix="nf_import_ext_"))

    def test_docx_official_tolerant(self):
        text = DOCX_OFFICIAL.read_text(encoding="utf-8")
        res = parse_skill(text)
        self.assertTrue(res.ok)
        self.assertEqual(res.mode, "external")           # 自由说明文不强套层级
        self.assertIsNone(res.ir)
        self.assertEqual(res.frontmatter["name"], "docx")
        desc = res.frontmatter["description"]
        # 双引号包裹单行 → 剥外层引号；内部裸单引号与冒号原样保留
        self.assertTrue(desc.startswith("Use this skill whenever"))
        self.assertIn("'Word doc'", desc)
        self.assertIn(".docx", desc)
        self.assertFalse(desc.startswith('"'))
        # 扩展字段透传（license 紧随 description）
        self.assertEqual(res.frontmatter["license"],
                         "Proprietary. LICENSE.txt has complete terms")
        # body 原样保留（含首行 # DOCX ...）
        self.assertIn("# DOCX creation, editing, and analysis", res.body)
        _, body0 = parse_frontmatter(text)
        self.assertEqual(res.body, body0)
        self.assertTrue(any("非 NF 导出层级结构" in w for w in res.warnings))

    def test_skill_creator_official_tolerant(self):
        text = SC_OFFICIAL.read_text(encoding="utf-8")
        res = parse_skill(text)
        self.assertTrue(res.ok)
        self.assertEqual(res.mode, "external")
        self.assertEqual(res.frontmatter["name"], "skill-creator")
        # 裸值 description：无引号包裹，原样保留
        desc = res.frontmatter["description"]
        self.assertTrue(desc.startswith("Create new skills"))
        self.assertFalse(desc.startswith(('"', "'")))
        self.assertIn("# Skill Creator", res.body)
        _, body0 = parse_frontmatter(text)
        self.assertEqual(res.body, body0)


# ---------------------------------------------------------------- 失败路径
class TestParseSkillFailures(unittest.TestCase):
    """明确 ValueError：不静默产出坏 IR（静默丢内容不变式）。"""

    def test_empty_text(self):
        with self.assertRaises(ValueError):
            parse_skill("")
        with self.assertRaises(ValueError):
            parse_skill("   \n  ")

    def test_no_frontmatter(self):
        with self.assertRaises(ValueError):
            parse_skill("# 没有 frontmatter 的正文\n内容")

    def test_unclosed_frontmatter(self):
        with self.assertRaises(ValueError):
            parse_skill("---\nname: x\n没有闭合")

    def test_missing_name(self):
        with self.assertRaises(ValueError):
            parse_skill("---\ndescription: 只有描述\n---\n# 标题\n正文")

    def test_missing_description(self):
        with self.assertRaises(ValueError):
            parse_skill("---\nname: x\n---\n# 标题\n正文")

    def test_empty_body(self):
        with self.assertRaises(ValueError):
            parse_skill("---\nname: x\ndescription: y\n---\n   \n  ")


class TestParseCcv3Failures(unittest.TestCase):
    def test_chara_not_dict(self):
        with self.assertRaises(ValueError):
            parse_ccv3("not-a-dict")

    def test_spec_mismatch(self):
        chara = json.loads(BOOTSTRAP_CHARA.read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            parse_ccv3(dict(chara, spec="tavern"))

    def test_missing_spec_version(self):
        chara = json.loads(BOOTSTRAP_CHARA.read_text(encoding="utf-8"))
        del chara["spec_version"]
        with self.assertRaises(ValueError):
            parse_ccv3(chara)

    def test_world_not_dict(self):
        chara = json.loads(BOOTSTRAP_CHARA.read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            parse_ccv3(chara, world="nope")


# -------------------------------------------------- parse_ccv3 结构还原
class TestParseCcv3Restore(unittest.TestCase):
    """自举 chara.json（+ 同源 world.json）→ 叙事 IR 骨架还原。"""

    def setUp(self):
        self.chara = json.loads(BOOTSTRAP_CHARA.read_text(encoding="utf-8"))
        self.world = json.loads(BOOTSTRAP_WORLD.read_text(encoding="utf-8"))

    def test_chara_only_restores_layer_and_modules(self):
        res = parse_ccv3(self.chara)
        self.assertTrue(res.ok)
        ir = res.ir
        self.assertEqual(ir.type, "narrative")
        self.assertEqual(ir.title, "技术文档装配战例")
        # description「（P06）装配产物」回填 pipeline
        self.assertEqual(ir.pipeline_id, "P06")
        self.assertEqual(ir.pipeline_name, "技术文档题材装配流")
        self.assertEqual(len(ir.layers), 1)
        layer = ir.layers[0]
        self.assertEqual(layer.id, "P90")
        self.assertEqual(layer.name, "技术文档生成")
        ids = [m.full_id for m in layer.modules]
        self.assertEqual(ids, ["M90", "M97"])
        self.assertEqual(ir.extra_modules, [])
        self.assertEqual(ir.meta.get("adapter_in"), "parse_ccv3")
        self.assertEqual(ir.meta.get("spec"), "chara_card_v3")
        self.assertFalse(res.warnings)

    def test_chara_plus_world_dedup(self):
        """chara 内嵌 character_book 与独立 world 同源 → 按 full_id 去重。"""
        res = parse_ccv3(self.chara, self.world)
        ir = res.ir
        ids = [m.full_id for m in ir.layers[0].modules]
        self.assertEqual(ids, ["M90", "M97"])            # 不重复入 IR
        self.assertEqual(res.chara_meta["world_name"],
                         "技术文档装配战例 · 世界书")
        self.assertEqual(res.chara_meta["chara"]["name"], "技术文档装配战例")

    def test_ccv3_export_entries_roundtrip(self):
        """parse_ccv3 → export(ir,'ccv3') → description 与 entries 往返一致。"""
        dest = Path(tempfile.mkdtemp(prefix="nf_import_ccv3_"))
        res = parse_ccv3(self.chara)
        out = export(res.ir, "ccv3", dest_dir=dest)
        new_chara = json.loads(Path(out.files[0]).read_text(encoding="utf-8"))
        # description 逐字一致（含 pipeline/块数/资产数措辞）
        self.assertEqual(new_chara["description"], self.chara["description"])
        orig = {e["keys"][0]: e for e in
                self.chara["character_book"]["entries"]}
        new = {e["keys"][0]: e for e in
               new_chara["character_book"]["entries"]}
        self.assertEqual(set(new), set(orig))
        for fid in orig:
            self.assertEqual(new[fid]["keys"], orig[fid]["keys"])
            self.assertEqual(new[fid]["content"], orig[fid]["content"])
            self.assertEqual(new[fid]["comment"], orig[fid]["comment"])


# ------------------------------------------------ exporter 反向登记（范围纪律）
class TestExporterReverseRegistry(unittest.TestCase):
    """exporter._REGISTRY_IN：A4 读入反向符号只挂已交付 skill/ccv3 两格。"""

    def test_registry_in_only_delivered_slots(self):
        reg = exporter._REGISTRY_IN
        self.assertEqual(set(reg), {"skill", "ccv3"})
        # 未交付读入适配器的格式不出厂（范围纪律锚点）
        for fmt in ("agents", "claude", "mcp"):
            self.assertNotIn(fmt, reg)
        # 值与 import_adapter 顶层符号同一对象（登记不是复制品）
        self.assertIs(reg["skill"], parse_skill)
        self.assertIs(reg["ccv3"], parse_ccv3)

    def test_registry_in_skill_roundtrip_closed_loop(self):
        """经反向登记面 skill 格走通 parse→export 逐字节闭环。"""
        dest = Path(tempfile.mkdtemp(prefix="nf_registry_in_"))
        text = BOOTSTRAP_SKILL.read_text(encoding="utf-8")
        res = exporter._REGISTRY_IN["skill"](text)
        self.assertTrue(res.ok)
        self.assertEqual(res.mode, "nf")
        out = export(res.ir, "skill", dest_dir=dest)
        out_text = Path(out.files[0]).read_text(encoding="utf-8")
        self.assertEqual(out_text, text)


if __name__ == "__main__":
    unittest.main()
