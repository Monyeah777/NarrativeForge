# -*- coding: utf-8 -*-
"""双语入口（README.md / README.en.md）机读事实一致性测试。

背景（外部实证）：某清单开了中英双语面却无一致性判据，中文面腐烂到英文面的 ~54%。
本仓的防线 = verify check34 的「双语入口机读锚点」断言；本测试把同一判据在单测面钉住，
期望值取自 `quality_baseline`（不写字面量，随基线自适应）。
"""
import contextlib
import importlib.util
import io
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import quality_baseline as qb  # noqa: E402

ANCHORS = ("check1-%d" % qb.EXPECTED_CHECKS, "PASS=%d" % qb.EXPECTED_PASS,
           "01_核心协议.md", "06_Agent执行协议.md", "llms.txt", "community/")
ENTRIES = ("README.md", "README.en.md")


class BilingualEntryTest(unittest.TestCase):
    def _read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_both_entries_exist(self):
        for rel in ENTRIES:
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_shared_machine_anchors(self):
        for rel in ENTRIES:
            text = self._read(rel)
            for anchor in ANCHORS:
                self.assertIn(anchor, text, "%s 缺机读锚点 %s" % (rel, anchor))

    def test_both_entries_carry_version(self):
        for rel in ENTRIES:
            self.assertRegex(self._read(rel), r"v\d+\.\d+", rel)

    def test_machine_index_points_to_english_entry(self):
        self.assertIn("README.en.md", self._read("llms.txt"))


class ExternalLinkToolTest(unittest.TestCase):
    """外链巡检工具（**非门禁**）：解析判据 + 注入 fetcher 的正负例（离线可跑）。"""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "nf_ext_links", ROOT / "scripts" / "check_external_links.py")
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def test_extract_dedup_and_strip_punctuation(self):
        text = "见 https://a.example/x，还有 https://a.example/x 与 https://b.example/y）。"
        self.assertEqual(self.tool.extract_links(text),
                         ["https://a.example/x", "https://b.example/y"])

    def test_skips_anchors_and_mail(self):
        text = "[锚](#section) [邮件](mailto:a@b.c) 正文 https://c.example/z"
        self.assertEqual(self.tool.extract_links(text), ["https://c.example/z"])

    def test_check_reports_ok_and_fail_with_injected_fetcher(self):
        links = {"README.md": ["https://ok.example/1", "https://dead.example/2"],
                 "docs/x.md": ["https://ok.example/1"]}
        fake = lambda url: (not url.startswith("https://dead"), "fake")   # noqa: E731
        report = self.tool.check(links, fake)
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["checked"], 2)      # 同链接只探一次
        self.assertEqual(report["failed"], 1)
        self.assertEqual([r["status"] for r in report["rows"]].count("fail"), 1)

    def test_limit_skips_beyond_sample(self):
        links = {"README.md": ["https://a.example/1", "https://a.example/2"]}
        report = self.tool.check(links, lambda url: (True, "fake"), limit=1)
        self.assertEqual(report["checked"], 1)
        self.assertIn("skipped", [r["status"] for r in report["rows"]])

    def test_scan_mode_does_not_fetch(self):
        """默认（不 --fetch）必须只解析、不联网：main 返回 0。"""
        with contextlib.redirect_stdout(io.StringIO()):
            code = self.tool.main(["--root", str(ROOT)])
        self.assertEqual(code, 0)

    def test_write_into_protocol_layer_is_rejected(self):
        """报告不得写入协议层（保静态可复现）。"""
        with contextlib.redirect_stderr(io.StringIO()):
            code = self.tool.main(["--root", str(ROOT),
                                   "--write", "protocol/x.json"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
