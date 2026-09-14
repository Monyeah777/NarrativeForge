# -*- coding: utf-8 -*-
"""内容外挂签名 / attestation 单测（三级信任 + fail-closed）。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import attest  # noqa: E402


class TestAttest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="nf_attest_")
        self.rel = "01_核心协议.md"
        self.p = Path(self.dir, self.rel)
        self.p.write_text("# 核心协议\n\n正文\n", encoding="utf-8")

    def test_digest_only_roundtrip_then_drift(self):
        """digest_only 级：一致时通过，内容被改即检出主体漂移。"""
        att = attest.build(self.rel, root=self.dir)
        ok, issues, level = attest.verify(att, self.dir)
        self.assertTrue(ok, issues)
        self.assertEqual(level, "digest_only")
        self.p.write_text("# 核心协议\n\n正文被改\n", encoding="utf-8")
        ok, issues, _ = attest.verify(att, self.dir)
        self.assertFalse(ok)
        self.assertTrue(any("漂移" in i for i in issues), issues)

    def test_envelope_tamper_detected(self):
        """信封自身被改（issued_at 漂移）→ 信封摘要不一致。"""
        att = attest.build(self.rel, root=self.dir)
        att["issued_at"] = "2030-01-01T00:00:00Z"
        ok, issues, _ = attest.verify(att, self.dir)
        self.assertFalse(ok)
        self.assertTrue(any("信封摘要" in i for i in issues), issues)

    def test_hmac_sign_verify_and_wrong_key(self):
        """hmac 级：持钥可验真伪；错钥/缺钥一律不可信。"""
        key = b"k" * 32
        att = attest.sign_hmac(attest.build(self.rel, root=self.dir), key)
        ok, issues, level = attest.verify(att, self.dir, key=key)
        self.assertTrue(ok, issues)
        self.assertEqual(level, "hmac-sha256")
        ok_wrong, _, _ = attest.verify(att, self.dir, key=b"w" * 32)
        self.assertFalse(ok_wrong)
        ok_missing, issues_missing, _ = attest.verify(att, self.dir)
        self.assertFalse(ok_missing)
        self.assertTrue(any("缺密钥" in i for i in issues_missing), issues_missing)

    def test_sigstore_fail_closed(self):
        """外挂锚：验证器缺失或 bundle 缺失 → 拒绝（绝不降级为 digest_only）。"""
        att = attest.build(self.rel, root=self.dir)
        att["signature"] = {"scheme": "sigstore-keyless", "bundle": "/nonexistent.bundle"}
        ok, issues, level = attest.verify(att, self.dir)
        self.assertFalse(ok)
        self.assertEqual(level, "sigstore-keyless")
        self.assertTrue(issues)

    def test_unknown_scheme_rejected(self):
        att = attest.build(self.rel, root=self.dir)
        att["signature"] = {"scheme": "no-such-scheme"}
        ok, issues, level = attest.verify(att, self.dir)
        self.assertFalse(ok)
        self.assertEqual(level, "unsupported")

    def test_bad_schema_rejected(self):
        ok, issues, level = attest.verify({"schema": "other/9"}, self.dir)
        self.assertFalse(ok)
        self.assertEqual(level, "invalid")

    def test_empty_key_file_rejected(self):
        kp = Path(self.dir, "empty.key")
        kp.write_bytes(b"\n")
        with self.assertRaises(ValueError):
            attest.read_key_file(str(kp))


if __name__ == "__main__":
    unittest.main()
