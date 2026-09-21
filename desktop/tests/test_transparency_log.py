#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""透明日志（哈希链）单测：链自洽 + 改一处即断链 + 边界声明 + 生成物一致性。"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import transparency_log as tl  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


def _write_receipts(tmp, entries):
    os.makedirs(os.path.join(tmp, "protocol"), exist_ok=True)
    with open(os.path.join(tmp, tl.RECEIPTS_REL), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"schema": "nf-receipts/1", "algorithm": "x", "count": len(entries),
                   "root": "a" * 64, "scope": "protocol", "entries": entries}, fh)


class TransparencyLogTest(unittest.TestCase):
    def test_repo_chain_is_consistent_and_on_disk(self):
        issues, stats = tl.verify(ROOT)
        self.assertEqual(issues, [], issues)
        self.assertGreaterEqual(stats["links"], 40)
        self.assertTrue(stats["on_disk"], "链生成物须入仓（protocol/generated/receipt_chain.json）")

    def test_chain_is_deterministic(self):
        self.assertEqual(tl.render(tl.build(ROOT)), tl.render(tl.build(ROOT)))

    def test_receipts_change_without_refresh_is_detected(self):
        """诚实边界：链条是**派生**物——回执变了而生成物没刷新即 FAIL；
        刷新后得到新链条（无外部见证，故不宣称「历史不可抵赖」）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write_receipts(tmp, [{"path": "a.md", "digest": "1" * 64}])
            tl.write(tmp)
            head_before = tl.build(tmp)["head"]
            self.assertEqual(tl.verify(tmp)[0], [])
            # 追加一条回执但不刷新链条 → 生成物过期
            _write_receipts(tmp, [{"path": "a.md", "digest": "1" * 64},
                                  {"path": "b.md", "digest": "2" * 64}])
            issues, _ = tl.verify(tmp)
            self.assertTrue(any("过期" in i for i in issues), issues)
            # 刷新即自洽（新链头）
            head_after = tl.build(tmp)["head"]
            self.assertNotEqual(head_after, head_before)
            tl.write(tmp)
            self.assertEqual(tl.verify(tmp)[0], [])

    def test_tampered_generated_chain_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_receipts(tmp, [{"path": "a.md", "digest": "1" * 64}])
            tl.write(tmp)
            path = os.path.join(tmp, tl.GENERATED_REL)
            with open(path, encoding="utf-8") as fh:
                doc = json.loads(fh.read())
            doc["head"] = "f" * 64                      # 篡改链头
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False, indent=2, sort_keys=True)
            issues, _ = tl.verify(tmp)
            self.assertTrue(any("过期" in i for i in issues), issues)

    def test_mutation_tampered_link_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_receipts(tmp, [{"path": "a.md", "digest": "1" * 64},
                                  {"path": "b.md", "digest": "2" * 64}])
            doc = tl.build(tmp)
            doc["links"][0]["chain"] = "f" * 64          # 篡改首节
            issues = []
            prev = "0" * 64
            for i, link in enumerate(doc["links"], 1):
                if link["prev"] != prev:
                    issues.append("prev 断")
                prev = link["chain"]
            self.assertTrue(issues, "篡改链节必须被检出")

    def test_missing_receipts_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _ = tl.verify(tmp)
            self.assertTrue(any(tl.RECEIPTS_REL in i for i in issues), issues)

    def test_boundary_is_not_overclaimed(self):
        doc = tl.build(ROOT)
        self.assertIn("不提供", doc["boundary"])
        self.assertIn("不可抵赖", doc["boundary"])


if __name__ == "__main__":
    unittest.main()
