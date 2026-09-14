# -*- coding: utf-8 -*-
"""云端图书馆机器面单测（frontmatter 真源 / 投影一致 / 生命周期 / 检索）。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import library as lib  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])

GOOD = """---
id: {eid}
type: 世界（测试件）
title: 测试条目 {eid}
description: 一句话描述
author: tester
license: MIT
generated: 2026-09-14
status: {status}
{extra}sources:
  - Issue #1
tags:
  - 测试
  - 雨天
---

# 测试条目 {eid}

## 是什么
一段正文，含关键词：毕业遗憾。
"""


def _tree(tmp, entries):
    d = Path(tmp, "library")
    d.mkdir(parents=True, exist_ok=True)
    for eid, body in entries.items():
        Path(d, "%s.md" % eid).write_text(body, encoding="utf-8")
    Path(d, "INDEX.md").write_text(
        "# INDEX\n\n## 登记表\n\n" + lib.BEGIN_INDEX + "\n" + lib.END_INDEX + "\n",
        encoding="utf-8")
    return tmp


class TestFrontmatter(unittest.TestCase):
    def test_parse_scalar_list_and_inline(self):
        text = ("---\nid: NF-9\ntype: T\ntitle: 标题\n"
                "tags: [a, b]\nsources:\n  - x\n  - y\n---\n正文\n")
        fm, body = lib.parse_frontmatter(text)
        self.assertEqual(fm["id"], "NF-9")
        self.assertEqual(fm["tags"], ["a", "b"])
        self.assertEqual(fm["sources"], ["x", "y"])
        self.assertEqual(body.strip(), "正文")

    def test_no_frontmatter_returns_empty(self):
        fm, body = lib.parse_frontmatter("# 标题\n正文\n")
        self.assertEqual(fm, {})
        self.assertIn("标题", body)


class TestRealRepo(unittest.TestCase):
    def test_entries_and_ids(self):
        rows = lib.entries(ROOT)
        ids = [e["id"] for e in rows]
        self.assertIn("NF-1", ids)
        self.assertIn("NF-WORLDCAMPUS-Monyeah777-1", ids)
        for e in rows:
            self.assertFalse(e["path"].startswith("C:"), "path 应为仓库相对路径")

    def test_verify_clean(self):
        issues, _warns, stats = lib.verify(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["entries"], 2)

    def test_projection_consistent(self):
        self.assertEqual(lib.check_projection(ROOT), [])

    def test_search_body_and_title(self):
        hit = lib.search("雨天", ROOT)
        self.assertEqual(hit[0]["id"], "NF-WORLDCAMPUS-Monyeah777-1")
        hit2 = lib.search("毕业遗憾", ROOT)
        self.assertEqual(hit2[0]["id"], "NF-1")

    def test_render_index_has_lifecycle_columns(self):
        block = lib.render_index_block(ROOT)
        for col in ("编号", "标题", "许可", "状态"):
            self.assertIn(col, block)
        self.assertIn(lib.END_INDEX, block)


class TestValidationNegative(unittest.TestCase):
    def test_anchor_hmac_sign_verify_and_self_reference(self):
        """签名锚：落锚不改规范摘要（自指安全）· 带钥可验 · 错钥 FAIL · 缺钥只 WARN。"""
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-9": GOOD.format(eid="NF-9", status="active", extra="")})
            lib.write_projection(tmp)
            before = lib.entry_digest(tmp, "library/NF-9.md")
            key = b"k" * 32
            out = lib.set_attestation(tmp, "NF-9", key=key)
            self.assertEqual(out["level"], "hmac-sha256")
            self.assertEqual(lib.entry_digest(tmp, "library/NF-9.md"), before,
                             "落锚不得改变规范摘要（自指避免）")
            self.assertEqual(lib.verify(tmp, key=key)[0], [])
            bad = lib.verify(tmp, key=b"w" * 32)[0]
            self.assertTrue(any("签名锚校验失败" in i for i in bad), bad)
            warns = lib.verify(tmp)[1]
            self.assertTrue(any("未提供密钥" in w for w in warns), warns)
            fm = lib.entries(tmp)[0]["fm"]
            for k in ("anchor_scheme", "anchor_mac", "anchor_key_id"):
                self.assertIn(k, fm)

    def test_anchor_downgrade_clears_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-9": GOOD.format(eid="NF-9", status="active", extra="")})
            lib.write_projection(tmp)
            lib.set_attestation(tmp, "NF-9", key=b"k" * 32)
            self.assertTrue(lib.entries(tmp)[0]["fm"].get("anchor_scheme"))
            lib.set_attestation(tmp, "NF-9")
            fm = lib.entries(tmp)[0]["fm"]
            self.assertFalse([k for k in fm if k.startswith("anchor_")],
                             "降级必须清掉旧锚，避免假可信")

    def test_receipts_carry_anchor_and_root_stable(self):
        """回执带锚信息；落锚不改变全馆根（根只绑规范摘要）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-9": GOOD.format(eid="NF-9", status="active", extra="")})
            lib.write_projection(tmp)
            from core import receipts as rc
            root_before = rc.build(tmp)["root"]
            lib.set_attestation(tmp, "NF-9", key=b"k" * 32)
            doc = rc.build(tmp)
            self.assertEqual(doc["root"], root_before)
            self.assertEqual(doc["entries"][0]["anchor"]["scheme"], "hmac-sha256")
            self.assertEqual(rc.verify(doc, tmp)[0], [])

    def test_attestation_hook_sign_stable_and_tamper(self):
        """attestation 字段：落签后校验通过、重复落签稳定、内容改动即报不符。"""
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-9": GOOD.format(eid="NF-9", status="active", extra="")})
            lib.write_projection(tmp)
            first = lib.set_attestation(tmp, "nf-9")
            self.assertEqual(len(first["attestation"]), 64)
            self.assertEqual(lib.verify(tmp)[0], [])
            self.assertEqual([w for w in lib.verify(tmp)[1] if "attestation" in w], [])
            second = lib.set_attestation(tmp, "NF-9")
            self.assertEqual(first["attestation"], second["attestation"])
            with open(Path(tmp, "library", "NF-9.md"), "a", encoding="utf-8") as fh:
                fh.write("\n改动\n")          # 追加正文（保留 frontmatter，模拟真实改动）
            warns = lib.verify(tmp)[1]
            self.assertTrue(any("attestation 与当前内容不符" in w for w in warns), warns)

    def test_attestation_bad_format_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = GOOD.format(eid="NF-9", status="active",
                               extra="attestation: not-a-digest\n")
            _tree(tmp, {"NF-9": body})
            issues, _w, _s = lib.verify(tmp)
            self.assertTrue(any("attestation 非 64 位" in i for i in issues), issues)

    def test_lifecycle_flow_deprecate_supersede_restore(self):
        """生命周期写面：deprecate → supersede（带取代链）→ restore，投影同步。"""
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {
                "NF-8": GOOD.format(eid="NF-8", status="active", extra=""),
                "NF-9": GOOD.format(eid="NF-9", status="active", extra=""),
            })
            lib.write_projection(tmp)
            lib.set_status(tmp, "NF-8", "deprecated")
            self.assertEqual(lib.entries(tmp)[0]["fm"]["status"], "deprecated")
            lib.set_status(tmp, "NF-8", "superseded", superseded_by="NF-9")
            fm = lib.entries(tmp)[0]["fm"]
            self.assertEqual(fm["status"], "superseded")
            self.assertEqual(fm["superseded_by"], "NF-9")
            self.assertEqual(lib.verify(tmp)[0], [])
            self.assertEqual(lib.check_projection(tmp), [])
            lib.set_status(tmp, "NF-8", "active")
            self.assertEqual(lib.entries(tmp)[0]["fm"]["status"], "active")
            self.assertNotIn("superseded_by", lib.entries(tmp)[0]["fm"])

    def test_lifecycle_rejects_bad_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-8": GOOD.format(eid="NF-8", status="active", extra="")})
            with self.assertRaises(ValueError):
                lib.set_status(tmp, "NF-8", "superseded", superseded_by="NF-404")
            with self.assertRaises(ValueError):
                lib.set_status(tmp, "NF-404", "deprecated")
            with self.assertRaises(ValueError):
                lib.set_status(tmp, "NF-8", "gone")

    def test_missing_frontmatter_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-9": "# 无 frontmatter\n正文\n"})
            issues, _w, _s = lib.verify(tmp)
            self.assertTrue(any("缺 YAML frontmatter" in i for i in issues), issues)

    def test_superseded_requires_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-9": GOOD.format(eid="NF-9", status="superseded", extra="")})
            issues, _w, _s = lib.verify(tmp)
            self.assertTrue(any("缺 superseded_by" in i for i in issues), issues)

    def test_superseded_target_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-9": GOOD.format(eid="NF-9", status="superseded",
                                            extra="superseded_by: NF-404\n")})
            issues, _w, _s = lib.verify(tmp)
            self.assertTrue(any("指向不存在的条目" in i for i in issues), issues)

    def test_bad_status_and_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = GOOD.format(eid="NF-9", status="gone", extra="")
            body = body.replace("generated: 2026-09-14", "generated: 09/14/2026")
            _tree(tmp, {"NF-9": body})
            issues, _w, _s = lib.verify(tmp)
            self.assertTrue(any("status 不在词表" in i for i in issues), issues)
            self.assertTrue(any("非 YYYY-MM-DD" in i for i in issues), issues)

    def test_projection_drift_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, {"NF-9": GOOD.format(eid="NF-9", status="active", extra="")})
            lib.write_projection(tmp)
            self.assertEqual(lib.check_projection(tmp), [])
            Path(tmp, "library", "NF-9.md").write_text(
                GOOD.format(eid="NF-9", status="active", extra="")
                .replace("测试条目 NF-9", "改了标题"), encoding="utf-8")
            self.assertTrue(lib.check_projection(tmp))


if __name__ == "__main__":
    unittest.main()
