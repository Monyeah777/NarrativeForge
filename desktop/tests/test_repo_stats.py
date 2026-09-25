#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自述数字实算真源（`core/repo_stats.py`）单测。

为什么要补这一件：`repo_stats.py` 由 5157419 引入（237 行），但仓内没有对应测试，
于是 `scripts/per_module_coverage.sh 30` 的单模块覆盖率门禁直接把它判 0.0% → 发布前体检不过
→ pre-push 拦截推送。本测试覆盖：真源读数、缺口如实报 issue、marker 生成区写入与一致性回检。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import repo_stats as rs  # noqa: E402


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def _mkroot(root):
    """造一个「真源齐全」的最小仓：数量都由文件数决定，便于反查口径。"""
    _write(root, "desktop/src/core/registry.json", json.dumps(
        {"modules": [{"id": "M00"}, {"id": "M10"}], "protocols": [{"id": "P1"}]}))
    _write(root, "03_管线库/P01_装配流.md", "# P01\n")
    _write(root, "community/packA/protocol.yaml", "schema_version: '2'\n")
    _write(root, "community/packA/assets/A1.md", "# A1\n")
    _write(root, "community/packA/assets/CONCEPT_GRAPH.md", "# graph\n")
    _write(root, "protocol/standards_catalog.json", json.dumps({"coverage": {
        "standards": 370, "reachable": 332, "unreachable": 38, "bodies": 194,
        "depends_edges": 206, "by_layer": {"data": 148, "iface": 84}}}))
    _write(root, "protocol/standards_binding.json", json.dumps({"bindings_total": 1200}))
    _write(root, "protocol/domain_packs.json", json.dumps(
        {"count": 100, "subdivisions_total": 1200}))
    _write(root, "library/NF-1.md", "# 条目\n")
    _write(root, "library/INDEX.md", "# 索引\n")
    _write(root, "verify.sh", "#!/usr/bin/env bash\n# 版本 : v2.28\ncheck1(){\n  :\n}\ncheck2(){\n  :\n}\n")
    for rel in rs.BLOCK_FILES:
        _write(root, rel, "# 头部\n\n%s\n\n%s\n\n# 尾部\n" % (rs.BEGIN, rs.END))


class ReadJsonTest(unittest.TestCase):
    def test_missing_and_invalid_json_return_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(rs._read_json(os.path.join(tmp, "nope.json")))
            bad = _write(tmp, "bad.json", "{not json")
            self.assertIsNone(rs._read_json(bad))
            ok = _write(tmp, "ok.json", '{"a": 1}')
            self.assertEqual({"a": 1}, rs._read_json(ok))


class ComputeTest(unittest.TestCase):
    def test_numbers_come_from_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mkroot(tmp)
            stats, issues = rs.compute(tmp)
            self.assertEqual(2, stats["core_modules"])
            self.assertEqual(1, stats["registered_packs"])
            self.assertEqual(["P01"], stats["core_pipelines"])
            self.assertEqual(1, stats["pack_dirs"])
            # community/*/assets/*.md 计 2（A1.md + CONCEPT_GRAPH.md）；概念图单计 1
            self.assertEqual(2, stats["pack_assets"])
            self.assertEqual(1, stats["concept_graphs"])
            self.assertEqual(370, stats["standards_total"])
            self.assertEqual(206, stats["standards_edges"])
            self.assertEqual(1200, stats["standard_bindings"])
            self.assertEqual(100, stats["domain_packs"])
            self.assertEqual(1200, stats["subdivisions_total"])
            self.assertEqual(1, stats["library_items"], "INDEX/ALIAS 不计入馆藏")
            self.assertEqual(2, stats["verify_checks"])
            self.assertEqual("2.28", stats["verify_version"])
            self.assertEqual("nf-repo-stats/1", stats["schema"])
            # 本最小仓的包目录数与登记数一致 → 不应报该条
            self.assertFalse([i for i in issues if "盘上包目录" in i], issues)

    def test_missing_truth_sources_are_reported_not_silently_zeroed(self):
        with tempfile.TemporaryDirectory() as tmp:
            stats, issues = rs.compute(tmp)
            self.assertEqual(0, stats["core_modules"])
            joined = " ".join(issues)
            self.assertIn("registry.json", joined)
            self.assertIn("verify.sh", joined)
            self.assertIn("标准目录 coverage 缺", joined)

    def test_pack_dir_registration_mismatch_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mkroot(tmp)
            _write(tmp, "community/packB/protocol.yaml", "schema_version: '2'\n")
            _, issues = rs.compute(tmp)
            self.assertTrue([i for i in issues if "盘上包目录" in i], issues)

    def test_missing_coverage_keys_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mkroot(tmp)
            _write(tmp, "protocol/standards_catalog.json", json.dumps({"coverage": {"standards": 1}}))
            _, issues = rs.compute(tmp)
            self.assertTrue([i for i in issues if "coverage 缺" in i], issues)


class RenderTest(unittest.TestCase):
    def _stats(self, tmp):
        _mkroot(tmp)
        return rs.compute(tmp)[0]

    def test_blocks_cover_three_entry_files_with_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocks = rs.render(self._stats(tmp))
            self.assertEqual(set(rs.BLOCK_FILES), set(blocks))
            for rel, block in blocks.items():
                self.assertTrue(block.startswith(rs.BEGIN), rel)
                self.assertTrue(block.rstrip().endswith(rs.END), rel)
            self.assertIn("PASS=", blocks["README.md"])
            self.assertIn("370", blocks["README.en.md"])
            self.assertIn("verify v2.28", blocks["llms.txt"])
            self.assertIn("馆藏", blocks["llms.txt"])


class ReplaceBlockTest(unittest.TestCase):
    def test_replaces_only_between_markers(self):
        text = "head\n%s\nold\n%s\ntail\n" % (rs.BEGIN, rs.END)
        new, ok = rs._replace_block(text, "%s\nnew\n%s" % (rs.BEGIN, rs.END))
        self.assertTrue(ok)
        self.assertIn("new", new)
        self.assertNotIn("old", new)
        self.assertTrue(new.startswith("head"))
        self.assertTrue(new.rstrip().endswith("tail"))

    def test_missing_markers_leave_text_untouched(self):
        text = "no markers here\n"
        new, ok = rs._replace_block(text, "BLOCK")
        self.assertFalse(ok)
        self.assertEqual(text, new)


class WriteCheckRoundTripTest(unittest.TestCase):
    @staticmethod
    def _generation_issues(issues):
        """只挑「生成区/机器读数与实算不一致」类——环境类 issue（如临时根无 quality_baseline）不算。"""
        return [i for i in issues if "与实算不一致" in i]

    def test_write_then_check_is_generation_consistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mkroot(tmp)
            issues, stats = rs.write(tmp)
            self.assertTrue(os.path.isfile(os.path.join(tmp, rs.STATS_REL)),
                            "写入须落 protocol/repo_stats.json")
            recorded = rs._read_json(os.path.join(tmp, rs.STATS_REL))
            self.assertEqual(stats, recorded)
            again, _ = rs.check(tmp)
            self.assertEqual([], self._generation_issues(again), again)

    def test_check_detects_tampered_generated_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mkroot(tmp)
            rs.write(tmp)
            readme = os.path.join(tmp, "README.md")
            with open(readme, encoding="utf-8") as fh:
                text = fh.read()
            with open(readme, "w", encoding="utf-8") as fh:
                fh.write(text.replace(rs.BEGIN, rs.BEGIN + "\n手改一行", 1))
            issues, _ = rs.check(tmp)
            self.assertTrue([i for i in issues if "README.md" in i and "实算不一致" in i], issues)

    def test_check_detects_stale_recorded_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mkroot(tmp)
            rs.write(tmp)
            _write(tmp, rs.STATS_REL, json.dumps({"schema": "nf-repo-stats/1", "core_modules": 999}))
            issues, _ = rs.check(tmp)
            self.assertTrue([i for i in issues if rs.STATS_REL in i], issues)

    def test_write_reports_missing_entry_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mkroot(tmp)
            os.unlink(os.path.join(tmp, "llms.txt"))
            issues, _ = rs.write(tmp)
            self.assertTrue([i for i in issues if "llms.txt" in i], issues)

    def test_scan_delegates_to_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mkroot(tmp)
            rs.write(tmp)
            self.assertEqual(rs.check(tmp)[0], rs.scan(tmp)[0])


if __name__ == "__main__":
    unittest.main()
