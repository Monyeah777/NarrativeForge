#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 追加 · IDL 元工具对照（可选：jsonschema 标准实现交叉验证）。

仓库校验器为自实现 JSON-schema 子集（零第三方红线）。本测试仅当环境装有
标准实现 jsonschema 时执行：① schema 文件本身是合法 draft 2020-12；
② 代表实例（M00 machine_contract）在标准实现下零错误——与子集校验器结论一致。
未安装则跳过（不触碰 verify 零第三方依赖红线）。
"""
import glob
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover - 可选对照依赖
    jsonschema = None
    Draft202012Validator = None

from core import schema_lint as sl  # noqa: E402


@unittest.skipIf(jsonschema is None, "jsonschema 未安装（可选对照依赖）")
class SchemaReferenceTest(unittest.TestCase):
    def test_schema_files_valid_draft2020(self):
        for f in sorted(glob.glob(os.path.join(ROOT, "protocol", "schema", "*.json"))):
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            Draft202012Validator.check_schema(data)

    def test_representative_instance_matches_reference(self):
        contract = sl.load_schema(ROOT, "contract.schema.json")
        m00 = os.path.join(ROOT, "04_模块库", "通用类", "M00_数据结构.md")
        with open(m00, encoding="utf-8") as fh:
            parsed = sl._fence_yaml(fh.read(), "machine_contract")
        self.assertIsNotNone(parsed)
        errors = list(Draft202012Validator(contract).iter_errors(parsed["machine_contract"]))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
