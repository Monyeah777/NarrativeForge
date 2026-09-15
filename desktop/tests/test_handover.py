# -*- coding: utf-8 -*-
"""接力协议（SBAR）正式与否定用例。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import handover as ho  # noqa: E402

GOOD = """---
id: HO-0001
title: t
date: 2026-09-15
from: a
to: b
status: open
refs:
  - art.md
---

## 情境
s
## 背景
b
## 评估
e
## 建议
r
## 未决项

- 做 X：判据 = Y
"""


def _mk(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _scene(tmp, text=GOOD, name="HO-0001-x.md"):
    _mk(tmp, "verify.sh", "check1(){ :; }\n")
    _mk(tmp, "art.md", "x")
    _mk(tmp, ho.DECL_REL, (ROOT / ho.DECL_REL).read_text(encoding="utf-8"))
    _mk(tmp, "handovers/" + name, text)
    return tmp


class TestRealRepo(unittest.TestCase):
    def test_scan_clean(self):
        issues, _w, stats = ho.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["handovers"], 1)
        self.assertGreaterEqual(stats["pending"], 1)


class TestNegatives(unittest.TestCase):
    def test_empty_pending_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), text=GOOD.split("## 未决项")[0] + "## 未决项\n")
        self.assertTrue(any("未决项为空" in i for i in ho.check_doc(tmp, "handovers/HO-0001-x.md")[0]))

    def test_pending_without_judgement_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), text=GOOD.replace("：判据 = Y", ""))
        self.assertTrue(any("缺判据" in i for i in ho.check_doc(tmp, "handovers/HO-0001-x.md")[0]))

    def test_missing_section_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), text=GOOD.replace("## 评估", "## 概况"))
        self.assertTrue(any("正文缺段落" in i for i in ho.check_doc(tmp, "handovers/HO-0001-x.md")[0]))

    def test_unresolvable_ref_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), text=GOOD.replace("art.md", "nowhere.md"))
        self.assertTrue(any("refs 无法解析" in i for i in ho.check_doc(tmp, "handovers/HO-0001-x.md")[0]))

    def test_bad_status_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), text=GOOD.replace("status: open", "status: wip"))
        self.assertTrue(any("status 越词表" in i for i in ho.check_doc(tmp, "handovers/HO-0001-x.md")[0]))


if __name__ == "__main__":
    unittest.main()
