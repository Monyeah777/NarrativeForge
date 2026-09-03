# -*- coding: utf-8 -*-
"""叙事工坊桌面工具 · 核心逻辑层单元测试（unittest，无 GUI 依赖）。

运行：cd /tmp/nf-desktop && python3 -m unittest discover -s tests -v
隔离：所有 Store 用例使用 tempfile 临时目录，绝不触碰真实 ~/.NarrativeForge。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.models import (  # noqa: E402
    Module, Pipeline, PipelineLayer, AssetPack, Preset, CATEGORIES, LAYER_IDS)
from core.parser import (  # noqa: E402
    parse_module, parse_asset_entries_from_text)
from core.validator import validate_module, check_assembly  # noqa: E402
from core.generator import (  # noqa: E402
    order_modules, generate_document, default_filename, collect_asset_keys)
from core.pipeline_loader import (  # noqa: E402
    parse_pipeline_md, discover_pipelines, load_pipeline_file)
from core.storage import Store  # noqa: E402
from core.preset_manager import (  # noqa: E402
    snapshot_preset, apply_preset, export_preset_json, import_preset_json,
    import_preset_file, export_preset_file)

# ------------------------------------------------------------------ 样例数据
DIRECTIVE_MD = """# M44：社团竞争系统
## 定义
- 层：P30
- 输入：M40, M22
- 输出：competition_score:int
- 发布：event_battle
- 资产：LOCATIONS, GANG
## 规则
1. 每月一次社团对抗，输出分数；
2. 分数影响人物关系（交 M40）。
## 引用的资产
- GANG
- NPC_TEMPLATES
"""

NF_MD = """# 模块 情感:M22 · 三冲动驱动
> 类别：情感｜来源：校园｜挂载点：P40 行为决策（active）｜依赖：M00、M40｜发布：npc_action
## 1. 职责
三冲动（性冲动/恶作剧/逃离）驱动角色行为决策。
## 2. 核心逻辑
```python
def decide(ctx):
    return pick_by_impulse(ctx)
```
"""

PIPELINE_YAML = """---
# 管线 P01 · 标准管线
```yaml
Pipeline:
  id: P01
  name: 标准管线
  description: 通用叙事装配实例
  structure:
    type: linear
  layers:
    - id: P00
      name: 数据基座
      description: 世界状态容器
      optional: false
      default_modules: [M00]
      allowed_modules: [M00, M20]
    - id: P40
      name: 行为决策
      description: 角色行为决策
      optional: false
      default_modules: [情感:M22, M40]
      allowed_modules: [情感:M22, M40, M41]
    - id: P80
      name: 输出呈现
      description: 渲染输出
      optional: false
      default_modules: [M80]
      allowed_modules: [M80]
  dependencies: []
  tags: [标准]
```
## 运行规则
按层序执行。
"""


def make_pipeline() -> Pipeline:
    return Pipeline.from_json({
        "id": "P01", "name": "标准管线",
        "layers": [
            {"id": "P00", "name": "数据基座", "optional": False,
             "default_modules": ["M00"], "allowed_modules": ["M00", "M20"]},
            {"id": "P40", "name": "行为决策", "optional": False,
             "default_modules": ["情感:M22", "M40"], "allowed_modules": ["情感:M22", "M40"]},
            {"id": "P80", "name": "输出呈现", "optional": False,
             "default_modules": ["M80"], "allowed_modules": ["M80"]},
        ],
    })


def make_mod(fid: str = "情感:M22", layer: str = "P40",
             enabled: bool = True, assets=None) -> Module:
    cat, num = fid.split(":", 1)
    return Module(id=num, name="测试模块", category=cat, layer=layer,
                  inputs=[], outputs=["x:int"], logic="pass",
                  assets=assets or [], enabled=enabled)


# ---------------------------------------------------------------- parser
class TestParser(unittest.TestCase):
    def test_directive_style(self):
        m = parse_module(DIRECTIVE_MD)
        self.assertEqual(m.id, "M44")
        self.assertEqual(m.name, "社团竞争系统")
        self.assertEqual(m.layer, "P30")
        self.assertIn("M40", m.inputs)
        self.assertIn("LOCATIONS", m.assets)
        self.assertIn("GANG", m.assets)
        self.assertIn("NPC_TEMPLATES", m.assets)
        self.assertIn("社团对抗", m.logic)

    def test_nf_style(self):
        m = parse_module(NF_MD, "情感类")
        self.assertEqual(m.id, "M22")
        self.assertEqual(m.name, "三冲动驱动")
        self.assertEqual(m.category, "情感类")
        self.assertEqual(m.layer, "P40")
        self.assertFalse(m.replaceable)  # active → 不可替换
        self.assertIn("M00", m.inputs)
        self.assertIn("decide", m.logic)

    def test_nf_style_metadata_only_without_logic_blocks(self):
        md = "# 模块 世界类:M07 · 地图区域\n> 类别：世界｜挂载点：P60 长期演变（active）｜依赖：M00\n## 职责\n维护地图区域状态。\n"
        m = parse_module(md, "世界类")
        self.assertEqual(m.layer, "P60")
        self.assertIn("维护地图区域", m.logic)

    def test_unknown_title_raises(self):
        with self.assertRaises(ValueError):
            parse_module("随便一段没有标题的文字")

    def test_asset_entries_split(self):
        text = "# 校园包\n## GANG\n帮派列表\n- 青龙帮\n## NPC_TEMPLATES\n角色模板库\n"
        out = parse_asset_entries_from_text(text)
        self.assertIn("GANG", out)
        self.assertIn("NPC_TEMPLATES", out)
        self.assertIn("青龙帮", out["GANG"])


# ---------------------------------------------------------------- validator
class TestValidator(unittest.TestCase):
    def test_ok_module(self):
        m = Module(id="M44", name="x", layer="P30", outputs=["y"],
                   logic="code")
        errs = validate_module(m, installed_ids=["情感:M40", "情感:M22"])
        self.assertEqual(errs, [])

    def test_missing_fields(self):
        m = Module()
        errs = validate_module(m)
        self.assertTrue(any("id" in e for e in errs))
        self.assertTrue(any("name" in e for e in errs))
        self.assertTrue(any("logic" in e for e in errs))

    def test_bad_layer(self):
        m = Module(id="M1", name="x", layer="P99", outputs=["y"], logic="c")
        errs = validate_module(m)
        self.assertTrue(any("P99" in e for e in errs))

    def test_uninstalled_dependency(self):
        m = Module(id="M44", name="x", layer="P30", outputs=["y"], logic="c",
                   inputs=["M99"])
        errs = validate_module(m, installed_ids=["M01"])
        self.assertTrue(any("M99" in e for e in errs))

    def test_allowed_set_check(self):
        p = make_pipeline()
        # M44 不在 P30/P40 允许集（P40 allowed 只有 情感:M22/M40）
        m = Module(id="M44", name="x", category="情感类", layer="P40",
                   outputs=["y"], logic="c")
        errs = validate_module(m, pipeline=p)
        self.assertTrue(any("允许集" in e for e in errs))
        # 在允许集内 → 无错误
        m2 = Module(id="M22", name="x", category="情感类", layer="P40",
                    outputs=["y"], logic="c")
        self.assertEqual(validate_module(m2, pipeline=p), [])

    def test_check_assembly_empty_and_core(self):
        p = make_pipeline()
        self.assertTrue(check_assembly([], p))
        issues = check_assembly([make_mod("情感:M22")], p)
        self.assertTrue(any("M00" in i for i in issues))
        self.assertTrue(any("M80" in i for i in issues))


# ---------------------------------------------------------------- pipeline_loader
class TestPipelineLoader(unittest.TestCase):
    def test_parse_pipeline_md(self):
        p = parse_pipeline_md(PIPELINE_YAML)
        self.assertIsNotNone(p)
        self.assertEqual(p.id, "P01")
        self.assertEqual(p.layer_ids, ["P00", "P40", "P80"])
        p40 = p.layer("P40")
        self.assertEqual(p40.name, "行为决策")
        self.assertIn("情感:M22", p40.default_modules)
        self.assertEqual(p.structure_type, "linear")

    def test_parse_invalid_returns_none(self):
        self.assertIsNone(parse_pipeline_md("# 没有 yaml 的文档"))

    def test_discover(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "pl"
            d.mkdir()
            (d / "P01.md").write_text(PIPELINE_YAML, encoding="utf-8")
            (d / "bad.md").write_text("无 frontmatter", encoding="utf-8")
            out = discover_pipelines(d)
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0].id, "P01")


# ---------------------------------------------------------------- generator
class TestGenerator(unittest.TestCase):
    def test_order_modules_pipeline_order(self):
        p = make_pipeline()
        m80 = make_mod("通用类:M80", "P80")
        m22 = make_mod("情感:M22", "P40")
        m00 = make_mod("通用类:M00", "P00")
        ordered, warns = order_modules([m80, m22, m00], p)
        self.assertEqual([m.layer for m in ordered], ["P00", "P40", "P80"])

    def test_order_missing_default_layer_warns(self):
        p = make_pipeline()
        ordered, warns = order_modules([make_mod("情感:M22", "P40")], p)
        self.assertTrue(any("P00" in w and "M00" in w for w in warns))
        self.assertTrue(any("P80" in w and "M80" in w for w in warns))

    def test_order_optional_layer_no_warn(self):
        p = make_pipeline()
        p.layers.append(PipelineLayer(id="P90", name="可选层", optional=True))
        _, warns = order_modules([make_mod("情感:M22", "P40")], p)
        self.assertFalse(any("P90" in w for w in warns))

    def test_disabled_module_skipped(self):
        p = make_pipeline()
        ordered, warns = order_modules(
            [make_mod("情感:M22", "P40", enabled=False)], p)
        self.assertEqual(ordered, [])
        self.assertTrue(any("停用" in w for w in warns))

    def test_outside_layer_appended(self):
        p = make_pipeline()
        m90 = make_mod("技术文档类:M90", "P90")
        ordered, warns = order_modules([m90], p)
        self.assertEqual([m.layer for m in ordered], ["P90"])
        self.assertTrue(any("P90" in w for w in warns))

    def test_generate_document_structure(self):
        p = make_pipeline()
        m00 = make_mod("通用类:M00", "P00")
        m22 = make_mod("情感:M22", "P40", assets=["GANG", "MISSING_KEY"])
        ap = AssetPack(name="校园包", entries={
            "GANG": "青龙帮、白虎帮、朱雀帮"})
        md, warns = generate_document(p, [m22, m00], ap, "测试文档")
        self.assertIn("# 测试文档", md)
        self.assertIn("## 目录", md)
        self.assertIn("## 层 P00", md)
        self.assertIn("## 层 P40", md)
        self.assertIn("情感:M22", md)
        # 标题提升（模块自带 # → ###）
        self.assertNotIn("\n# 模块", md)
        # 资产附录：内联 + 缺失提示
        self.assertIn("青龙帮", md)
        self.assertIn("MISSING_KEY", md)
        # 资产包名出现在元信息
        self.assertIn("校园包", md)

    def test_generate_no_asset_no_appendix(self):
        p = make_pipeline()
        md, _ = generate_document(p, [make_mod("情感:M22", "P40")], None)
        self.assertNotIn("资产引用附录", md)

    def test_generate_heading_lift(self):
        p = make_pipeline()
        m = make_mod("情感:M22", "P40")
        m.source_md = "# 我的大标题\n## 我的小标题\n正文"
        md, _ = generate_document(p, [m], None, "t")
        self.assertIn("### 我的大标题", md)
        self.assertNotIn("\n# 我的大标题", md)

    def test_default_filename(self):
        p = make_pipeline()
        fn = default_filename(p)
        self.assertTrue(fn.startswith("P01_"))
        self.assertTrue(fn.endswith(".md"))

    def test_collect_asset_keys_dedup(self):
        a = make_mod("情感:M22", "P40", assets=["GANG", "GANG", "NPC"])
        b = make_mod("通用类:M80", "P80", assets=["NPC"])
        self.assertEqual(collect_asset_keys([a, b]), ["GANG", "NPC"])


# ---------------------------------------------------------------- storage
class TestStorage(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.home = Path(self._td.name) / "nf-home"
        self.store = Store(self.home)

    def tearDown(self):
        self._td.cleanup()

    def test_default_home_override(self):
        old = os.environ.pop("NARRATIVE_FORGE_HOME", None)
        try:
            os.environ["NARRATIVE_FORGE_HOME"] = str(self.home)
            from core.storage import default_home
            self.assertEqual(default_home(), self.home)
        finally:
            if old is None:
                os.environ.pop("NARRATIVE_FORGE_HOME", None)
            else:
                os.environ["NARRATIVE_FORGE_HOME"] = old

    def test_module_crud(self):
        self.assertEqual(self.store.stats()["modules"], 0)
        m = make_mod("情感:M22", "P40")
        m.source_md = "# 模块 情感:M22 · 三冲动驱动\n正文"
        self.store.save_module(m)
        self.assertEqual(self.store.stats()["modules"], 1)
        got = self.store.get_module("情感:M22")
        self.assertIsNotNone(got)
        self.assertEqual(got.name, "测试模块")
        self.assertIn("正文", got.source_md)
        # 更新
        m2 = make_mod("情感:M22", "P40")
        m2.name = "改名"
        m2.source_md = "新正文"
        self.store.save_module(m2)
        self.assertEqual(self.store.get_module("情感:M22").name, "改名")
        # 删除
        self.assertTrue(self.store.remove_module("情感:M22"))
        self.assertIsNone(self.store.get_module("情感:M22"))

    def test_duplicate_id_different_category(self):
        a = make_mod("情感:M22", "P40")
        b = make_mod("事件:M22", "P30")
        self.store.save_module(a)
        self.store.save_module(b)
        self.assertEqual(len(self.store.list_modules()), 2)
        self.assertIsNotNone(self.store.get_module("情感:M22"))
        self.assertIsNotNone(self.store.get_module("事件:M22"))

    def test_toggle_module(self):
        self.store.save_module(make_mod("情感:M22", "P40"))
        m = self.store.toggle_module("情感:M22")
        self.assertFalse(m.enabled)
        self.assertFalse(self.store.get_module("情感:M22").enabled)

    def test_asset_pack_crud(self):
        ap = AssetPack(name="校园包", entries={"GANG": "帮派"})
        self.store.save_asset_pack(ap)
        got = self.store.get_asset_pack("校园包")
        self.assertEqual(got.entries["GANG"], "帮派")
        self.assertTrue(self.store.remove_asset_pack("校园包"))
        self.assertIsNone(self.store.get_asset_pack("校园包"))

    def test_preset_and_config(self):
        self.store.set_config("pipeline", "P03")
        self.assertEqual(self.store.get_config("pipeline"), "P03")
        p = Preset(name="我的预设", pipeline="P01", modules=["情感:M22"])
        self.store.save_preset(p)
        self.assertEqual(len(self.store.list_presets()), 1)
        self.assertTrue(self.store.remove_preset("我的预设"))

    def test_cache_roundtrip(self):
        self.store.save_cache("test_key", {"a": 1})
        self.assertEqual(self.store.load_cache("test_key"), {"a": 1})
        self.assertIsNone(self.store.load_cache("missing"))


# ---------------------------------------------------------------- preset_manager
class TestPresetManager(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.store = Store(Path(self._td.name) / "h")
        for fid in ("情感:M22", "通用类:M80"):
            self.store.save_module(make_mod(fid))

    def tearDown(self):
        self._td.cleanup()

    def test_snapshot_and_apply(self):
        mods = [make_mod("情感:M22", "P40"), make_mod("通用类:M80", "P80")]
        p = snapshot_preset("预设A", "P01", mods, "校园包")
        self.assertEqual(p.modules, ["情感:M22", "通用类:M80"])
        out = apply_preset(self.store, p)
        self.assertEqual(out["pipeline"], "P01")
        self.assertEqual(len(out["modules"]), 2)
        self.assertEqual(out["asset_pack"], "校园包")

    def test_apply_missing_module_warns(self):
        p = Preset(name="x", pipeline="P01",
                   modules=["情感:M22", "不存在:X99"])
        out = apply_preset(self.store, p)
        self.assertEqual(len(out["modules"]), 1)
        self.assertTrue(any("X99" in w for w in out["warnings"]))

    def test_export_import_roundtrip(self):
        p = snapshot_preset("导出测试", "P02",
                            [make_mod("情感:M22", "P40")], "西幻包")
        text = export_preset_json(p)
        p2 = import_preset_json(text)
        self.assertEqual(p2.name, "导出测试")
        self.assertEqual(p2.pipeline, "P02")
        self.assertEqual(p2.modules, ["情感:M22"])

    def test_import_invalid(self):
        self.assertIsNone(import_preset_json("not json"))
        self.assertIsNone(import_preset_json('{"a": 1}'))

    def test_import_export_file(self):
        p = snapshot_preset("文件预设", "P03", [], "")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "preset.json"
            self.assertTrue(export_preset_file(p, path))
            self.assertIsNone(import_preset_file(self.store, Path(td) / "none.json"))
            p2 = import_preset_file(self.store, path)
            self.assertEqual(p2.name, "文件预设")
            self.assertIn("文件预设", [x.name for x in self.store.list_presets()])


# ---------------------------------------------------------------- models
class TestModels(unittest.TestCase):
    def test_module_full_id(self):
        m = Module(id="M22", category="情感类")
        self.assertEqual(m.full_id, "情感类:M22")

    def test_pipeline_layer_lookup(self):
        p = make_pipeline()
        self.assertEqual(p.layer_ids, ["P00", "P40", "P80"])
        self.assertIsNotNone(p.layer("P40"))
        self.assertIsNone(p.layer("P99"))

    def test_pipeline_from_json_roundtrip(self):
        p = make_pipeline()
        p2 = Pipeline.from_json(json.loads(json.dumps(p.to_json())))
        self.assertEqual(p2.layer_ids, p.layer_ids)
        self.assertEqual(p2.layer("P40").default_modules,
                         p.layer("P40").default_modules)

    def test_constants(self):
        self.assertIn("情感类", CATEGORIES)
        self.assertEqual(len(LAYER_IDS), 9)


if __name__ == "__main__":
    unittest.main()
