# -*- coding: utf-8 -*-
"""读者侧独立验证器（scripts/nf_verify.py）端到端测试。

刻意**不 import NF 的任何模块**来跑被测脚本——它就是给"没有 NF 的读者"用的，
所以测试也必须用子进程按"读者姿势"调用。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "nf_verify.py"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import library as lib  # noqa: E402
from core import receipts as rc  # noqa: E402

ENTRY = """---
id: NF-9
type: 测试件
title: 测试条目
description: 一句话
author: tester
license: MIT
generated: 2026-09-14
status: active
sources:
  - Issue #1
---

# 测试条目
正文。
"""


def _fixture(tmp, key=None, ssh_key="", ssh_identity=""):
    d = Path(tmp, "library")
    d.mkdir(parents=True, exist_ok=True)
    (d / "NF-9.md").write_text(ENTRY, encoding="utf-8")
    lib.write_projection(tmp)
    if key or ssh_key:
        lib.set_attestation(tmp, "NF-9", key=key, ssh_key=ssh_key,
                            ssh_identity=ssh_identity)
    else:
        rc.write(tmp)
    return tmp


def _run(tmp, *extra, cwd):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(VERIFIER), "--entry", "NF-9",
         "--receipts", str(Path(tmp, "library", "RECEIPTS.json")),
         "--entry-file", str(Path(tmp, "library", "NF-9.md")), *extra],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=cwd, env=env)


class TestReaderVerifier(unittest.TestCase):
    def test_inclusion_and_content_pass_without_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp)
            r = _run(tmp, cwd=tmp)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("包含证明折叠到根", r.stdout)
            self.assertIn("内容摘要与回执一致", r.stdout)

    def test_tampered_content_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp)
            with open(Path(tmp, "library", "NF-9.md"), "a", encoding="utf-8") as fh:
                fh.write("\n被改了\n")
            r = _run(tmp, cwd=tmp)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("内容被改", r.stdout)

    def test_hmac_anchor_requires_key_and_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = b"k" * 32
            _fixture(tmp, key=key)
            kp = Path(tmp, "k.bin")
            kp.write_bytes(key)
            self.assertEqual(_run(tmp, cwd=tmp).returncode, 1, "缺钥必须 fail-closed")
            ok = _run(tmp, "--key-file", str(kp), cwd=tmp)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("hmac 锚匹配", ok.stdout)
            kp.write_bytes(b"w" * 32)
            bad = _run(tmp, "--key-file", str(kp), cwd=tmp)
            self.assertEqual(bad.returncode, 1)
            self.assertIn("hmac 锚不匹配", bad.stdout)

    @unittest.skipUnless(shutil.which("ssh-keygen"), "需要 ssh-keygen")
    def test_ssh_anchor_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp, "id_ed25519")
            subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "",
                            "-C", "t@nf", "-f", str(key)],
                           capture_output=True, stdin=subprocess.DEVNULL)
            _fixture(tmp, ssh_key=str(key), ssh_identity="t@nf")
            asf = Path(tmp, "allowed_signers")
            asf.write_text("t@nf " + Path(str(key) + ".pub").read_text(encoding="utf-8").strip() + "\n",
                           encoding="utf-8")
            missing = _run(tmp, cwd=tmp)
            self.assertEqual(missing.returncode, 1, "缺 allowed_signers 必须 fail-closed")
            ok = _run(tmp, "--ssh-allowed-signers", str(asf), cwd=tmp)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("ssh-sig 匹配", ok.stdout)
            doc = json.loads(Path(tmp, "library", "RECEIPTS.json").read_text(encoding="utf-8"))
            self.assertEqual(doc["entries"][0]["anchor"]["scheme"], "ssh-sig")


if __name__ == "__main__":
    unittest.main()
