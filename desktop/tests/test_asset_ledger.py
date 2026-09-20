#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""40 总纲 v2.7 S2 —— nf asset 供应链台账单测（纯 unittest，L2 core 零依赖）。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from core import asset_ledger as al


class AssetLedgerTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def _make_asset(self, name="A1.md", body="# 资产 A1\n内容行\n"):
        path = os.path.join(self.root, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return path

    def _ledger_path(self):
        return al.default_ledger_path(self.root)


class AddAssetTest(AssetLedgerTestBase):
    def test_add_creates_ledger_header_and_entry(self):
        self._make_asset()
        entry = al.add_asset(self.root, "A1.md", "A1", source="测试源 v1",
                             module="M00", version="1.0")
        self.assertEqual(entry["status"], al.STATUS_ACTIVE)
        self.assertTrue(os.path.isfile(self._ledger_path()))
        with open(os.path.join(self.root, "A1.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("<!-- nf-asset:"), text[:60])
        header = al.parse_header(text)
        self.assertEqual(header["key"], "A1")
        self.assertEqual(header["version"], "1.0")
        ledger = al.load_ledger(self._ledger_path())
        self.assertEqual(len(ledger["assets"]), 1)
        self.assertEqual(ledger["tier"], "official")

    def test_duplicate_key_and_file_rejected(self):
        self._make_asset()
        al.add_asset(self.root, "A1.md", "A1", source="s1")
        with self.assertRaises(al.AssetLedgerError):
            al.add_asset(self.root, "A1.md", "A2", source="s2")
        with self.assertRaises(al.AssetLedgerError):
            al.add_asset(self.root, "A1.md", "A1", source="s3")

    def test_missing_file_and_traversal_rejected(self):
        with self.assertRaises(al.AssetLedgerError):
            al.add_asset(self.root, "missing.md", "K", source="s")
        with self.assertRaises(al.AssetLedgerError):
            al.add_asset(self.root, "../evil.md", "K", source="s")

    def test_existing_header_rejects_double_trust(self):
        self._make_asset()
        al.add_asset(self.root, "A1.md", "A1", source="s1")
        with self.assertRaises(al.AssetLedgerError):
            al.add_asset(self.root, "A1.md", "A9", source="s9")


class EntryValidationTest(unittest.TestCase):
    def test_missing_required_fields_rejected(self):
        with self.assertRaises(al.AssetLedgerError):
            al.make_entry("f.md", "", "s")
        with self.assertRaises(al.AssetLedgerError):
            al.make_entry("f.md", "K", "")
        with self.assertRaises(al.AssetLedgerError):
            al.make_entry("f.md", "K", "s", version="")
        with self.assertRaises(al.AssetLedgerError):
            al.make_entry("f.md", "K", "s", status="bogus")

    def test_valid_entry_fields(self):
        e = al.make_entry("f.md", "K", "s", module="M93", version="2.1")
        self.assertEqual(e["module"], "M93")
        self.assertTrue(e["added"])


class VerifyLedgerTest(AssetLedgerTestBase):
    def test_clean_ledger_no_issues(self):
        self._make_asset()
        al.add_asset(self.root, "A1.md", "A1", source="s1", module="M00")
        issues, stats = al.verify_ledger_dir(self.root)
        self.assertEqual(issues, [])
        self.assertEqual(stats["assets"], 1)

    def test_missing_file_is_issue(self):
        self._make_asset()
        al.add_asset(self.root, "A1.md", "A1", source="s1")
        os.remove(os.path.join(self.root, "A1.md"))
        issues, _ = al.verify_ledger_dir(self.root)
        self.assertTrue(any("文件缺失" in i for i in issues))

    def test_header_tamper_is_issue(self):
        self._make_asset()
        al.add_asset(self.root, "A1.md", "A1", source="s1")
        p = os.path.join(self.root, "A1.md")
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        text = text.replace('status="active"', 'status="retired"', 1)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        issues, _ = al.verify_ledger_dir(self.root)
        self.assertTrue(any("不一致" in i for i in issues))

    def test_orphan_header_is_issue(self):
        self._make_asset("A1.md")
        al.add_asset(self.root, "A1.md", "A1", source="s1")
        self._make_asset("ORPHAN.md", body="# orphan\n")
        with open(os.path.join(self.root, "ORPHAN.md"), encoding="utf-8") as f:
            body = f.read()
        with open(os.path.join(self.root, "ORPHAN.md"), "w", encoding="utf-8") as f:
            f.write('<!-- nf-asset: key="GHOST" version="1.0" status="active" -->\n' + body)
        issues, stats = al.verify_ledger_dir(self.root)
        self.assertTrue(any("孤儿文件头" in i for i in issues))
        self.assertEqual(stats["orphans"], 1)

    def test_no_ledger_dir_is_not_an_issue(self):
        self._make_asset()
        issues, stats = al.verify_ledger_dir(self.root)
        self.assertEqual(issues, [])
        self.assertEqual(stats["assets"], 0)


class LifecycleTest(AssetLedgerTestBase):
    def test_deprecate_restore_touches_header_and_ledger(self):
        self._make_asset()
        al.add_asset(self.root, "A1.md", "A1", source="s1")
        al.set_status(self.root, "A1", al.STATUS_DEPRECATED)
        with open(os.path.join(self.root, "A1.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('status="deprecated"', text)
        ledger = al.load_ledger(self._ledger_path())
        self.assertEqual(ledger["assets"][0]["status"], al.STATUS_DEPRECATED)
        al.set_status(self.root, "A1", al.STATUS_ACTIVE)
        with open(os.path.join(self.root, "A1.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('status="active"', text)

    def test_remove_entry_keeps_file(self):
        self._make_asset()
        al.add_asset(self.root, "A1.md", "A1", source="s1")
        removed = al.remove_entry(self.root, "A1")
        self.assertEqual(removed["key"], "A1")
        self.assertTrue(os.path.isfile(os.path.join(self.root, "A1.md")))
        with self.assertRaises(al.AssetLedgerError):
            al.remove_entry(self.root, "A1")


class RootScanTest(AssetLedgerTestBase):
    def test_verify_root_and_inventory_find_ledger(self):
        sub = os.path.join(self.root, "pkg", "assets")
        os.makedirs(sub)
        with open(os.path.join(sub, "X.md"), "w", encoding="utf-8") as f:
            f.write("# X\n")
        al.add_asset(sub, "X.md", "X", source="s1", tier="community", package="demo")
        issues, stats = al.verify_root(self.root)
        self.assertEqual(issues, [])
        self.assertEqual(stats["ledgers"], 1)
        rows = al.inventory_root(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["package"], "demo")
        self.assertEqual(rows[0]["tier"], "community")
        self.assertEqual(rows[0]["assets"], 1)

    def test_iter_assets_and_filters(self):
        sub = os.path.join(self.root, "assets")
        os.makedirs(sub)
        with open(os.path.join(sub, "X.md"), "w", encoding="utf-8") as f:
            f.write("# X\n")
        al.add_asset(sub, "X.md", "X", source="s1", tier="community", package="demo")
        rows = al.iter_assets(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(al.filter_rows(rows, tier="community")[0]["key"], "X")
        self.assertEqual(al.filter_rows(rows, tier="official"), [])
        self.assertEqual(al.filter_rows(rows, pkg="demo")[0]["file"], "X.md")


class ShelfShapeTest(unittest.TestCase):
    """资产货架**单层不变量**（2026-09-20 作者裁决收口）。

    背景：密度 / 键表投影 / 行数基线三面以非递归 glob 取件，台账面走 os.walk——
    货架出现子目录时文件会「台账可见、三面不可见」（静默丢口径），故子目录即 FAIL。
    """

    def _shelf(self, tmp: str, pkg: str = "某包") -> str:
        d = os.path.join(tmp, "community", pkg, "assets")
        os.makedirs(d, exist_ok=True)
        return d

    def test_flat_shelf_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._shelf(tmp)
            with open(os.path.join(d, "A.md"), "w", encoding="utf-8") as f:
                f.write("# A\n")
            issues, stats = al.verify_shelf_shape(tmp)
            self.assertEqual(issues, [])
            self.assertEqual(stats["shelves"], 1)

    def test_nested_dir_under_package_shelf_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self._shelf(tmp)
            os.makedirs(os.path.join(d, "sub"))
            with open(os.path.join(d, "sub", "B.md"), "w", encoding="utf-8") as f:
                f.write("# B\n")
            issues, _ = al.verify_shelf_shape(tmp)
            self.assertTrue(any("资产货架含子目录" in i for i in issues), issues)
            self.assertTrue(any("community/某包/assets" in i for i in issues), issues)

    def test_user_shelf_is_covered_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "05_资产库", "用户自定义", "sub"))
            issues, _ = al.verify_shelf_shape(tmp)
            self.assertTrue(any("用户自定义" in i for i in issues), issues)

    def test_verify_root_aggregates_shape_issues_and_shelf_stat(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(self._shelf(tmp), "sub"))
            issues, stats = al.verify_root(tmp)
            self.assertIn("shelves", stats)
            self.assertEqual(stats["shelves"], 1)
            self.assertTrue(any("资产货架含子目录" in i for i in issues), issues)

    def test_repo_shelves_are_flat(self):
        """仓库真源：三个域包货架与用户自定义货架当前均为单层（本不变量成立）。"""
        repo = str(Path(__file__).resolve().parents[2])
        issues, stats = al.verify_shelf_shape(repo)
        self.assertEqual(issues, [], issues)
        self.assertGreaterEqual(stats["shelves"], 4)


if __name__ == "__main__":
    unittest.main()
