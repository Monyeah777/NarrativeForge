#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`core/content_face.py`（叶子件）与 `conformance_scan` 的**口径逐位一致**回归。

为什么单列：指纹拆到叶子件是为了断模块级环（`disk_cache` 不再反向依赖校验层），
代价是「帧 + payload 口径」存在两份实现——本文件把两份钉成**同一个值**，防止悄悄漂移。
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import conformance_scan as csc  # noqa: E402
from core import content_face as cf  # noqa: E402


class FrameAndPayloadParityTest(unittest.TestCase):
    def test_hash_face_matches_conformance_scan(self):
        rels = ["a.md", "b/c.py"]
        digests = {"a.md": b"\x01\x02", "b/c.py": b"\x03"}
        self.assertEqual(csc._hash_face(rels, digests), cf.hash_face(rels, digests))

    def test_payload_digest_matches_on_real_files(self):
        rels = ["README.md", "verify.sh", "desktop/src/core/content_face.py"]
        for rel in rels:
            self.assertEqual(csc._payload_digest(str(ROOT), rel),
                             cf.payload_digest(str(ROOT), rel), rel)

    def test_payload_digest_matches_on_crlf_text(self):
        """CR 是最难的一条：通用换行翻译后才摘要（两份实现都必须如此）。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "crlf.md"
            p.write_bytes("第一行\r\n第二行\r\n".encode("utf-8"))
            csc.clear_resident()
            self.assertEqual(csc._payload_digest(tmp, "crlf.md"), cf.payload_digest(tmp, "crlf.md"))

    def test_code_face_digest_matches_face_fingerprint(self):
        """整面指纹：叶子件的枚举 + 摘要 + 帧 == 校验层的 face_fingerprint（逐位相同）。"""
        from core import disk_cache  # noqa: E402 - 取真实的代码面模式集
        self.assertEqual(csc.face_fingerprint(str(ROOT), disk_cache.CODE_FACE),
                         cf.code_face_digest(str(ROOT), disk_cache.CODE_FACE))
        overlap = ("desktop/src/core/content_face.py", "desktop/src/core/*.py")
        self.assertEqual(csc.face_fingerprint(str(ROOT), overlap),
                         cf.code_face_digest(str(ROOT), overlap),
                         "重叠模式集也必须逐位一致（逐模式追加、不去重）")

    def test_list_core_files_is_the_live_core_listing(self):
        got = cf.list_core_files(str(ROOT))
        self.assertIn("content_face.py", got)
        self.assertIn("conformance_scan.py", got)
        self.assertTrue(all(n.endswith(".py") for n in got))

    def test_empty_pattern_is_empty_face(self):
        self.assertEqual(cf.rels_for(str(ROOT), ("no/such/*.md",)), [])
        self.assertEqual(cf.code_face_digest(str(ROOT), ("no/such/*.md",)),
                         cf.hash_face([], {}))


if __name__ == "__main__":
    unittest.main()
