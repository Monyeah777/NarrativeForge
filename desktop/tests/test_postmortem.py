# -*- coding: utf-8 -*-
"""复盘（postmortem）正式与否定用例。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import postmortem as pm  # noqa: E402

GOOD = """---
id: PO-0001
title: t
date: 2026-09-15
trigger: check35
status: open
refs:
  - art.md
---

## 现象
s
## 影响
i
## 根因
门禁顺序未成文
## 行动项

- 把顺序写进文档：**负责人** = 机制；**判据** = check35 恒绿
"""


def _mk(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _scene(tmp, text=GOOD, name="PO-0001-x.md"):
    _mk(tmp, "verify.sh", "check35(){ :; }\n")
    _mk(tmp, "art.md", "x")
    _mk(tmp, pm.DECL_REL, (ROOT / pm.DECL_REL).read_text(encoding="utf-8"))
    _mk(tmp, "postmortems/" + name, text)
    return tmp


class TestRealRepo(unittest.TestCase):
    def test_scan_clean(self):
        issues, _w, stats = pm.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["postmortems"], 1)
        self.assertGreaterEqual(stats["actions"], 1)


class TestNegatives(unittest.TestCase):
    def _check(self, text):
        return pm.check_doc(_scene(tempfile.mkdtemp(), text=text),
                            "postmortems/PO-0001-x.md")[0]

    def test_blame_is_fail(self):
        self.assertTrue(any("指责性归因" in i
                            for i in self._check(GOOD.replace("门禁顺序未成文", "个人失误"))))

    def test_root_cause_must_point_to_mechanism(self):
        self.assertTrue(any("根因段未指向机制" in i
                            for i in self._check(GOOD.replace("门禁顺序未成文", "没注意"))))

    def test_action_without_judgement_is_fail(self):
        self.assertTrue(any("缺判据" in i for i in self._check(GOOD.replace("；**判据** = check35 恒绿", ""))))

    def test_action_without_owner_is_fail(self):
        self.assertTrue(any("缺负责人" in i for i in self._check(GOOD.replace("**负责人** = 机制；", ""))))

    def test_empty_actions_is_fail(self):
        self.assertTrue(any("行动项为空" in i
                            for i in self._check(GOOD.split("## 行动项")[0] + "## 行动项\n")))


if __name__ == "__main__":
    unittest.main()
