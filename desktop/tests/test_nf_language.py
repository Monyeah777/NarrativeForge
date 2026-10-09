# -*- coding: utf-8 -*-
"""NF 语言面符号索引单测（编辑器智能的数据真源）。

判据：符号必须**从既有真源派生**且**歧义不猜**——模块身份取模块文件自身
`machine_contract.id/name`（域包文件名与编号不对应时仍要解析正确），
层位/订阅来自 registry.json，事件来自 event_registry.json，资产键取文件名令牌。
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import nf_language as nl  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class TestIndexFacts(unittest.TestCase):
    """索引内容与真源逐一对照。"""

    @classmethod
    def setUpClass(cls):
        cls.idx = nl.build(ROOT)

    def test_module_identity_comes_from_contract_not_filename(self):
        # 大语言模型域包的模块文件叫 A01a_*.md，模块 id 是 大语言模型:M01——
        # 按文件名反解必漏，本索引必须按契约块解析。
        hit = self.idx.resolve("大语言模型:M01")
        self.assertIsNotNone(hit)
        self.assertIn("A01a_", hit["path"])

    def test_official_and_community_ids_both_present(self):
        self.assertIsNotNone(self.idx.resolve("M00"))
        self.assertIsNotNone(self.idx.resolve("通用:M10"))
        self.assertIsNotNone(self.idx.resolve("情感:M22"))
        self.assertIsNotNone(self.idx.resolve("生存:M10"))

    def test_layers_events_pipelines_assets(self):
        # P40 只属层位；P00 同属层位与官方 P00 管线（既有同名先例）→ 判为歧义，见下一测。
        self.assertIsNotNone(self.idx.resolve("P40"))
        self.assertIsNotNone(self.idx.resolve("narrative_event"))
        self.assertIsNotNone(self.idx.resolve("P01"))
        self.assertIsNotNone(self.idx.resolve("ATTR_TEMPLATES"))

    def test_bare_number_ambiguity_is_fail_closed(self):
        # 通用:M10 与 生存:M10 共用裸号 M10——解析必须失败关闭，候选面给全。
        self.assertIsNone(self.idx.resolve("M10"))
        names = {s["name"] for s in self.idx.resolve_all("M10")}
        self.assertEqual(names, {"通用:M10", "生存:M10"})

    def test_unique_symbol_definitions_are_repo_paths(self):
        for token in ("M00", "ATTR_TEMPLATES", "P01"):
            sym = self.idx.resolve(token)
            self.assertTrue((Path(ROOT) / sym["path"]).is_file(), sym["path"])

    def test_completion_needs_prefix(self):
        self.assertEqual(self.idx.complete(""), [])
        self.assertIn("P01", {s["name"] for s in self.idx.complete("P0")})

    def test_module_meta_reads_heading_first(self):
        p = Path(ROOT) / "community/校园情感领域包/modules/M22_三冲动驱动.md"
        mid, name = nl.module_meta(p)
        self.assertEqual(mid, "情感:M22")
        self.assertEqual(name, "三冲动驱动")

    def test_signature_changes_with_content(self):
        sig = nl.signature(ROOT)
        self.assertTrue(sig)
        self.assertTrue(all(isinstance(x[1], int) for x in sig))


class TestStructuredReferences(unittest.TestCase):
    """引用面：**只给登记关系**（事件↔发布/订阅模块、模块↔挂载层、管线←域包采用）。

    内部差距实证（2026-10-08）：编辑器此前只能「跳定义」，问「谁引用了这个事件」没有答案；
    而 NF 的引用本来就是**有登记**的（registry.json 的 subscriptions / mounts / protocols）。
    判据要点：每条引用都带 why（可解释）；位置必须真在盘上；未登记 token 一律空表（不猜）。
    """

    @classmethod
    def setUpClass(cls):
        cls.idx = nl.build(str(ROOT))

    def test_event_references_carry_reason_and_real_paths(self):
        refs = self.idx.references("tick_day")
        self.assertGreaterEqual(len(refs), 2, "事件应给出发布方与订阅方")
        whys = {r["why"] for r in refs}
        self.assertIn("发布方", whys)
        self.assertIn("订阅方", whys)
        for r in refs:
            self.assertTrue((Path(ROOT) / r["path"]).is_file(), "引用位置必须真在盘上：%s" % r["path"])
            self.assertIn(r["kind"], nl.KINDS + ("package",))

    def test_module_and_layer_references_are_symmetric(self):
        up = self.idx.references("M00")                 # 模块 → 挂载层
        self.assertTrue(any(r["kind"] == "layer" for r in up), "模块应给出挂载层引用")
        down = self.idx.references("P00")               # 层 → 挂载模块
        self.assertTrue(any(r["kind"] == "module" for r in down), "层应给出挂载模块引用")

    def test_pipeline_reference_points_at_adopting_package(self):
        refs = self.idx.references("P02")
        pkgs = [r for r in refs if r["kind"] == "package"]
        self.assertTrue(pkgs, "管线应给出采用它的域包位置")
        self.assertTrue((Path(ROOT) / pkgs[0]["path"]).is_file())

    def test_unknown_token_is_empty_not_fuzzy(self):
        self.assertEqual([], self.idx.references("没有这个符号"))
        self.assertEqual([], self.idx.references(""))


if __name__ == "__main__":
    unittest.main()
