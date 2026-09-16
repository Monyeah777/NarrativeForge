# -*- coding: utf-8 -*-
"""审计/验收（audit）正式与否定用例。"""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import audit as au  # noqa: E402


def _mk(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _scene(tmp, digest=None, verdict="pass", accepted_by="作者", accepted_at="2026-09-16"):
    _mk(tmp, "subject.md", "x")
    if digest is None:
        digest = hashlib.sha256(b"x").hexdigest()
    _mk(tmp, au.DECL_REL, (ROOT / au.DECL_REL).read_text(encoding="utf-8"))
    _mk(tmp, "results/audit/docs_audit-99-x.md", """---
id: AUD-0099
date: 2026-09-16
scope: s
verdict: %s
auditor: a
subjects:
  - subject.md:%s
accepted_by: %s
accepted_at: %s
---

## 结论
ok
""" % (verdict, digest, accepted_by, accepted_at))
    return tmp


class TestRealRepo(unittest.TestCase):
    def test_scan_clean_with_legacy_warns(self):
        issues, warns, stats = au.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["with_header"], 1)
        self.assertTrue(any("legacy" in w for w in warns))

    def test_header_digests_match(self):
        issues, st = au.check_doc(str(ROOT), "results/audit/docs_audit-49-audit-protocol.md")
        self.assertEqual(issues, [])
        self.assertEqual(st["subjects"], 2)


class TestNegatives(unittest.TestCase):
    def test_subject_digest_drift_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), digest="0" * 64)
        self.assertTrue(any("旧审计失效" in i
                            for i in au.check_doc(tmp, "results/audit/docs_audit-99-x.md")[0]))

    def test_bad_verdict_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), verdict="maybe")
        self.assertTrue(any("verdict 越词表" in i
                            for i in au.check_doc(tmp, "results/audit/docs_audit-99-x.md")[0]))

    def test_acceptance_without_date_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), accepted_at="—")
        self.assertTrue(any("签收须双要素" in i
                            for i in au.check_doc(tmp, "results/audit/docs_audit-99-x.md")[0]))

    def test_missing_subject_file_is_fail(self):
        tmp = _scene(tempfile.mkdtemp())
        _mk(tmp, "results/audit/docs_audit-98-y.md",
            (Path(tmp, "results/audit/docs_audit-99-x.md").read_text(encoding="utf-8"))
            .replace("subject.md:", "gone.md:"))
        self.assertTrue(any("被审对象不存在" in i
                            for i in au.check_doc(tmp, "results/audit/docs_audit-98-y.md")[0]))

    def test_legacy_is_warn_not_fail(self):
        tmp = tempfile.mkdtemp()
        _mk(tmp, au.DECL_REL, (ROOT / au.DECL_REL).read_text(encoding="utf-8"))
        _mk(tmp, "results/audit/docs_audit-90-old.md", "# 旧审计\n\n无头。\n")
        issues, warns, stats = au.scan(tmp)
        self.assertEqual(issues, [])
        self.assertEqual(stats["legacy"], 1)
        self.assertTrue(warns)


if __name__ == "__main__":
    unittest.main()
