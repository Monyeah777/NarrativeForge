#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 A1 —— 协议层 IDL schema 校验器单测（自实现 JSON-schema 子集 + 全量件扫描）。"""
import os
import unittest

import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import schema_lint as sl  # noqa: E402


class SchemaSubsetValidatorTest(unittest.TestCase):
    def test_type_and_required_catch(self):
        schema = {
            "type": "object",
            "required": ["id", "events"],
            "properties": {
                "id": {"type": "string", "pattern": "^M[0-9]{2}$"},
                "count": {"type": "integer", "minimum": 0},
                "events": {
                    "type": "object",
                    "required": ["publish"],
                    "properties": {"publish": {"type": "array", "items": {"type": "string"}}},
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        }
        msgs = sl.subset_validate({"id": 12, "count": -1, "extra": 1}, schema)
        joined = "\n".join(msgs)
        self.assertIn("缺必填字段 events", joined)
        self.assertIn("应为 string", joined)
        self.assertIn("未知字段 extra", joined)

    def test_real_contract_mutation_detected(self):
        """真实机读块逐字段变异 → 均被 schema 拦截（漂移即 FAIL 的实证）。"""
        m00 = os.path.join(ROOT, "04_模块库", "通用类", "M00_数据结构.md")
        with open(m00, encoding="utf-8") as fh:
            text = fh.read()
        parsed = sl._fence_yaml(text, "machine_contract")
        self.assertIsNotNone(parsed)
        mc = parsed["machine_contract"]
        schema = sl.load_schema(ROOT, "contract.schema.json")
        self.assertIsNotNone(schema)
        # 基线：原样零违例
        self.assertEqual(sl.subset_validate(mc, schema), [])
        # 枚举变异
        mut = dict(mc, schema="2")
        self.assertTrue(any("枚举" in m for m in sl.subset_validate(mut, schema)))
        # pattern 变异
        mut = dict(mc, id="X1")
        self.assertTrue(any("pattern" in m for m in sl.subset_validate(mut, schema)))
        # 类型变异
        mut = dict(mc, name=123)
        self.assertTrue(any("应为 string" in m for m in sl.subset_validate(mut, schema)))
        # 必填删除（events.subscribe 缺键）
        events = dict(mc["events"])
        del events["subscribe"]
        mut = dict(mc, events=events)
        self.assertTrue(any("未知字段" in m or "缺必填" in m for m in sl.subset_validate(mut, schema)))
        # 事件对象内未知字段
        events = dict(mc["events"], extra_event="x")
        mut = dict(mc, events=events)
        self.assertTrue(any("未知字段 extra_event" in m for m in sl.subset_validate(mut, schema)))

    def _m00_contract(self):
        m00 = os.path.join(ROOT, "04_模块库", "通用类", "M00_数据结构.md")
        with open(m00, encoding="utf-8") as fh:
            parsed = sl._fence_yaml(fh.read(), "machine_contract")
        self.assertIsNotNone(parsed)
        return parsed["machine_contract"]

    def test_extension_face_closed(self):
        """扩展面封闭（01 §1.1 扩展键纪律）：词表外键 → 未知字段 FAIL。"""
        schema = sl.load_schema(ROOT, "contract.schema.json")
        mut = dict(self._m00_contract(), novel_face={"x": 1})
        msgs = sl.subset_validate(mut, schema)
        self.assertTrue(any("未知字段 novel_face" in m for m in msgs), msgs)

    def test_extension_key_naming_discipline(self):
        """键名纪律（propertyNames）：snake_case + ≤20 字符，违约即 pattern FAIL。"""
        schema = {
            "type": "object",
            "properties": {"ok": {"type": "string"}},
            "propertyNames": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,19}$"},
            "additionalProperties": False,
        }
        self.assertEqual(sl.subset_validate({"ok": "v"}, schema), [])
        for bad in ("Bad-Key", "HasCaps", "a" * 21):
            msgs = sl.subset_validate({bad: "v"}, schema)
            self.assertTrue(any("pattern" in m for m in msgs), (bad, msgs))

    def test_registered_extension_key_passes(self):
        """已登记扩展键照常通过——纪律是「先登记」，不是「禁扩展」。"""
        schema = sl.load_schema(ROOT, "contract.schema.json")
        mut = dict(self._m00_contract(),
                   tool_face=[{"purpose": "示例能力", "guidance": {"check": "在场"}}])
        self.assertEqual(sl.subset_validate(mut, schema), [])


class DirectEnumerationTest(unittest.TestCase):
    """`discover()` 换枚举器（`os.walk`/`os.listdir`/`glob` → `csc.iter_files`）后**面必须逐件一致**。

    依据（实测 2026-09-29）：旧写法 **54 ms**（三种写法各自真走一遍文件系统），新写法 **0.8 ms**
    （目录清单已在常驻层 `dirs` 桶里）——**65×**。提速只有在「面不变」时才允许，所以这里把旧口径
    **原样重算一遍**逐件比对（真仓库：模块 248 / 管线 114 / 协议声明 111 件）。
    """

    def test_faces_match_legacy_enumeration(self):
        import glob

        def walk_md(sub):
            out = []
            for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, sub)):
                dirnames[:] = [d for d in dirnames if d != "__pycache__"]
                for f in sorted(filenames):
                    if f.endswith(".md"):
                        out.append(os.path.join(dirpath, f))
            return out

        pkg = os.path.join(ROOT, "community")
        legacy_mod, legacy_pipe = walk_md("04_模块库"), walk_md("03_管线库")
        for name in sorted(os.listdir(pkg)):
            mdir = os.path.join(pkg, name, "modules")
            if os.path.isdir(mdir):
                legacy_mod += sorted(os.path.join(mdir, f) for f in os.listdir(mdir)
                                     if f.endswith(".md"))
            pdir = os.path.join(pkg, name, "pipelines")
            if os.path.isdir(pdir):
                legacy_pipe += sorted(os.path.join(pdir, f) for f in os.listdir(pdir)
                                      if f.endswith(".md"))
        legacy_proto = sorted(glob.glob(os.path.join(pkg, "*", "protocol.yaml")))

        got = sl.discover(ROOT)
        for key, legacy in (("module_docs", legacy_mod), ("pipeline_docs", legacy_pipe),
                            ("protocol_files", legacy_proto)):
            self.assertTrue(legacy, "%s 面为空，判据没测到东西" % key)
            self.assertEqual(sorted(legacy), sorted(got[key]),
                             "%s 面与旧枚举不一致（换实现改动了面）" % key)


class SchemaScanTest(unittest.TestCase):
    def test_schema_files_meta(self):
        issues, schemas = sl.check_schema_files(ROOT)
        self.assertEqual(issues, [])
        self.assertEqual(len(schemas), 5)

    def test_repo_scan_clean(self):
        issues, stats = sl.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["module_docs"], 40)
        self.assertGreaterEqual(stats["contract_covered"], 20)
        self.assertGreaterEqual(stats["pipelines"], 8)
        self.assertGreaterEqual(stats["protocols"], 5)
        self.assertGreaterEqual(stats["asset_entries"], 2)
        self.assertEqual(stats["schema_files"], 5)

    def test_unsupported_keyword_rejected(self):
        """子集边界自洽：校验器未实现的关键字出现在 schema 定义即 FAIL（防假绿）。"""
        bad = sl.subset_key_violations({
            "type": "object",
            "properties": {"a": {"type": "string", "oneOf": []}},
            "items": {"$ref": "#/definitions/x"},
        })
        joined = "\n".join(bad)
        self.assertIn("oneOf", joined)
        self.assertIn("$ref", joined)

    def test_schema_dialect_declaration_must_match(self):
        """方言声明：$schema 与校验器实现的方言不一致即 FAIL（防「声明 2020-12、实现是别的」）。"""
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            sdir = os.path.join(tmp, "protocol", "schema")
            os.makedirs(sdir)
            ok_doc = {"$schema": sl.DIALECT, "$id": "x.schema.json", "title": "t",
                      "type": "object", "properties": {}}
            bad_doc = dict(ok_doc, **{"$schema": "http://json-schema.org/draft-07/schema#"})
            with open(os.path.join(sdir, "x.schema.json"), "w", encoding="utf-8") as fh:
                json.dump(bad_doc, fh)
            issues, _schemas = sl.check_schema_files(tmp)
            self.assertTrue(any("方言" in i for i in issues), issues)
            with open(os.path.join(sdir, "x.schema.json"), "w", encoding="utf-8") as fh:
                json.dump(ok_doc, fh)
            self.assertEqual(sl.check_schema_files(tmp)[0], [])

    def test_repo_schemas_within_subset(self):
        """仓库五份 schema 全在子集白名单内（零越界 = 校验器无静默忽略面）。"""
        for s in sl.check_schema_files(ROOT)[1]:
            self.assertEqual(sl.subset_key_violations(s), [])


if __name__ == "__main__":
    unittest.main()
