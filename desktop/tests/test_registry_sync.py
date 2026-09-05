"""协议登记同步测试（v2.1.0-B3-B：nf register 本地登记助手纯函数层）。

覆盖 registry_sync 两个核心纯函数：
- check_registerable(pkg_dir, doc)：三要件校验（① protocol.yaml ② 02 §8 在册 ③ registry）
- merge_protocols(reg_protocols, entries)：只增不删合并 + 幂等 + 保序
"""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import registry_sync  # noqa: E402
from core.protocol_projection import project_entry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
COMMUNITY = ROOT / "community"
DOC = ROOT / "02_联动注册表.md"
REGISTRY = Path(__file__).resolve().parent.parent / "src" / "core" / "registry.json"

CAMPUS = COMMUNITY / "校园情感领域包"
LIGHTMIX = COMMUNITY / "校园西幻轻混组合包"


def _doc_text() -> str:
    with open(DOC, encoding="utf-8") as f:
        return f.read()


def _reg_protocols() -> list:
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)["protocols"]


class CheckRegisterableTest(unittest.TestCase):
    """三要件校验：① protocol.yaml 在场 ② 02 §8 在册 ③ registry 可读。"""

    def test_in_register_lightmix_passes(self):
        issues = registry_sync.check_registerable(str(LIGHTMIX), _doc_text())
        self.assertEqual(issues, [], "轻混包已 02 §8.4 在册，应通过")

    def test_register_absent_package_rejected(self):
        """不在 02 §8 在册的包目录 → 拒绝（② 缺失）。"""
        fake = ROOT / ".rivet" / "scratch" / "nf_not_registered_pkg"
        fake.mkdir(parents=True, exist_ok=True)
        (fake / "protocol.yaml").write_text(
            "protocol:\n  schema_version: \"2\"\npackage:\n  id: 未登记测试包\n  name: 未登记测试包\n",
            encoding="utf-8")
        try:
            issues = registry_sync.check_registerable(str(fake), _doc_text())
            self.assertTrue(issues, "02 未在册包应产生 issue")
            joined = "\n".join(issues)
            self.assertIn("未登记测试包", joined)
            self.assertIn("02", joined)
        finally:
            (fake / "protocol.yaml").unlink()
            fake.rmdir()

    def test_schema_version_invalid_rejected(self):
        fake = ROOT / ".rivet" / "scratch" / "nf_bad_schema_pkg"
        fake.mkdir(parents=True, exist_ok=True)
        (fake / "protocol.yaml").write_text(
            "protocol:\n  schema_version: \"9\"\npackage:\n  id: 坏版本包\n  name: 坏版本包\n",
            encoding="utf-8")
        try:
            issues = registry_sync.check_registerable(str(fake), _doc_text())
            self.assertTrue(issues, "schema_version 非 v1/v2 应拒绝")
        finally:
            (fake / "protocol.yaml").unlink()
            fake.rmdir()

    def test_projection_matches_existing_registry(self):
        """已登记轻混包：projection 产物与 registry 现有条目一致 → diff 无更新。"""
        entry = project_entry(str(LIGHTMIX))
        existing = next(p for p in _reg_protocols() if p["id"] == entry["id"])
        self.assertEqual(entry, existing)


class MergeProtocolsTest(unittest.TestCase):
    """合并语义：id 命中更新 / 缺失追加 / 多余不删 / 幂等。"""

    def _sample(self, pid="校园情感领域包", module_ids=None):
        e = project_entry(str(CAMPUS))
        e["id"] = pid
        if module_ids is not None:
            e["module_ids"] = list(module_ids)
        return e

    def test_merge_updates_existing_id(self):
        reg = list(_reg_protocols())
        entry = self._sample(module_ids=["情感:M22", "M40"])
        out = registry_sync.merge_protocols(reg, [entry])
        got = next(p for p in out if p["id"] == entry["id"])
        self.assertEqual(got["module_ids"], ["情感:M22", "M40"])

    def test_merge_appends_new_id(self):
        reg = list(_reg_protocols())
        entry = self._sample(pid="测试新包X", module_ids=["M91"])
        out = registry_sync.merge_protocols(reg, [entry])
        ids = [p["id"] for p in out]
        self.assertIn("测试新包X", ids)
        # 既有条目保序在前（只增不删），新 id 追加末尾——条数动态（现 5 包，勿硬编码）
        orig = [p["id"] for p in _reg_protocols()]
        self.assertEqual(ids[: len(orig)], orig)
        self.assertEqual(ids[-1], "测试新包X")

    def test_merge_never_removes(self):
        reg = list(_reg_protocols())
        # 传入的 entries 只含 1 个 → 其余条必须保留（只增不删）
        entry = self._sample(pid="校园情感领域包")
        out = registry_sync.merge_protocols(reg, [entry])
        self.assertEqual(len(out), len(reg))

    def test_merge_idempotent(self):
        reg = list(_reg_protocols())
        entry = self._sample(module_ids=["情感:M22", "M40"])
        once = registry_sync.merge_protocols(reg, [entry])
        twice = registry_sync.merge_protocols(once, [entry])
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
