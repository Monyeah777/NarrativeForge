# -*- coding: utf-8 -*-
"""联动注册表机读加载器（T1.2）单元测试。

覆盖 registry_loader.py 四件套 API 与收敛点助手：
  - load_registry 解析 / 文件缺失 / JSON 损坏显式抛错（不静默回退）
  - list_core_modules 官方核心 13 件（含 M90）
  - get_module 双形态标识解析（注册表形态 / 模型形态长名）+ 裸号歧义防护
  - layer_mounts 挂载点读取（P90 领域实例层返回 None）
  - validate_assembly R3 装配校验（空装配 / 缺核心锚点 / 歧义 / 社区不入表 / P90 豁免）
  - core_anchor_modules 核心锚点推导（== [M00, M80]，CP1 收敛点数据源）

运行：cd desktop && python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.registry_loader import (  # noqa: E402
    load_registry, Registry, P90_DOMAIN_LAYER)

CORE_DIR = Path(__file__).resolve().parent.parent / "src" / "core"
REGISTRY_JSON = CORE_DIR / "registry.json"


def _registry() -> Registry:
    """取默认 registry.json 的 Registry 实例（lru_cache 共享，只读安全）。"""
    return load_registry()


class TestLoadRegistry(unittest.TestCase):
    """load_registry 解析与异常路径。"""

    def test_load_registry_parses_snapshot(self):
        r = _registry()
        self.assertEqual(r.registry_schema_version, "2")
        # 与磁盘投影一致性：modules 13 件、mount_points 九层 P00-P80
        raw = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
        self.assertEqual(len(r.modules), len(raw["modules"]))
        self.assertEqual(len(r.modules), 13)
        self.assertEqual(
            sorted(r.mount_points.keys()),
            sorted(raw["mount_points"].keys()))
        self.assertEqual(
            sorted(r.mount_points.keys()),
            ["P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80"])
        self.assertNotIn("P90", r.mount_points)  # 02 §9 P90 不纳入投影

    def test_load_registry_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_registry(CORE_DIR / "no_such_registry.json")

    def test_load_registry_bad_json_raises(self):
        bad = CORE_DIR / "_bad_registry_tmp.json"
        bad.write_text("{ not valid json", encoding="utf-8")
        try:
            with self.assertRaises(json.JSONDecodeError):
                load_registry(bad)
        finally:
            bad.unlink(missing_ok=True)

    def test_registry_post_init_builds_indexes(self):
        r = _registry()
        # 内部索引可由公开行为间接验证：裸号与短前缀均可达
        self.assertIsNotNone(r.get_module("M00"))
        self.assertIsNotNone(r.get_module("事件:M22"))


class TestListCoreModules(unittest.TestCase):
    """官方核心模块表 13 件。"""

    def test_list_core_modules_count_and_contains_m90(self):
        r = _registry()
        ids = r.list_core_modules()
        self.assertEqual(len(ids), 13)
        self.assertIn("M00", ids)
        self.assertIn("M80", ids)
        self.assertIn("M90", ids)          # P90 实证样例在册
        self.assertIn("事件:M22", ids)     # 短前缀限定 ID
        self.assertIn("通用:M10", ids)


class TestGetModule(unittest.TestCase):
    """get_module 双形态解析与歧义防护。"""

    def test_get_module_bare_hit(self):
        r = _registry()
        for bare in ("M00", "M23", "M24", "M50", "M80",
                     "M06", "M12", "M13", "M20", "M08", "M90"):
            with self.subTest(bare=bare):
                m = r.get_module(bare)
                self.assertIsNotNone(m, f"裸号 {bare} 应命中")
                self.assertEqual(m["id"], bare)

    def test_get_module_prefixed_hit(self):
        r = _registry()
        self.assertEqual(r.get_module("事件:M22")["id"], "事件:M22")
        self.assertEqual(r.get_module("通用:M10")["id"], "通用:M10")

    def test_get_module_model_form_long_category(self):
        """模型形态长名（类别长名 + : + 裸号）→ 短前缀归一命中。"""
        r = _registry()
        m = r.get_module("事件类:M22")
        self.assertIsNotNone(m)
        self.assertEqual(m["id"], "事件:M22")   # 注册表形态短前缀

    def test_get_module_model_form_bare_unify(self):
        """模型形态长名 + 裸号号段（通用类:M00）→ 类别一致时解引用到裸号。"""
        r = _registry()
        m = r.get_module("通用类:M00")
        self.assertIsNotNone(m)
        self.assertEqual(m["id"], "M00")

    def test_get_module_ambiguous_bare_miss(self):
        """裸号歧义防护：M22/M10 号段存在前缀登记 → 裸号引用必须 miss。"""
        r = _registry()
        self.assertIsNone(r.get_module("M22"))
        self.assertIsNone(r.get_module("M10"))

    def test_get_module_unregistered_miss(self):
        """社区模块 / 未知号段不在注册表 → None。"""
        r = _registry()
        self.assertIsNone(r.get_module("情感:M22"))   # 社区 情感类模块不入表
        self.assertIsNone(r.get_module("X99"))
        self.assertIsNone(r.get_module("M99"))         # 第三方保留段

    def test_get_module_empty_or_none(self):
        r = _registry()
        self.assertIsNone(r.get_module(""))
        self.assertIsNone(r.get_module(None))
        self.assertIsNone(r.get_module("   "))


class TestLayerMounts(unittest.TestCase):
    """layer_mounts 挂载点读取。"""

    def test_layer_mounts_p00_p80_default(self):
        r = _registry()
        p00 = r.layer_mounts("P00")
        self.assertIsNotNone(p00)
        self.assertEqual(p00["default"], ["M00"])
        self.assertIn("M20", p00["available"])
        p80 = r.layer_mounts("P80")
        self.assertEqual(p80["default"], ["M80"])

    def test_layer_mounts_p90_none(self):
        """P90 领域实例层不纳入 mount_points 投影 → None（02 §9 设计意图）。"""
        r = _registry()
        self.assertIsNone(r.layer_mounts("P90"))

    def test_layer_mounts_p40_empty_default(self):
        """P40 空层 optional:true——官方空层不阻塞主循环（01 §6 R3）。"""
        r = _registry()
        p40 = r.layer_mounts("P40")
        self.assertIsNotNone(p40)
        self.assertEqual(p40["default"], [])
        self.assertIs(p40["optional"], True)

    def test_layer_mounts_unknown_none(self):
        r = _registry()
        self.assertIsNone(r.layer_mounts("P99"))


class TestValidateAssembly(unittest.TestCase):
    """validate_assembly R3 装配校验。"""

    def test_validate_assembly_empty(self):
        issues = _registry().validate_assembly([])
        self.assertTrue(issues)               # 非空 issues（与 validator 语义一致）
        self.assertTrue(any("未选择" in i for i in issues))

    def test_validate_assembly_ok(self):
        r = _registry()
        self.assertEqual(r.validate_assembly(["M00", "事件:M22", "M80"]), [])
        self.assertEqual(r.validate_assembly(["M00", "M80"]), [])

    def test_validate_assembly_missing_core(self):
        r = _registry()
        issues = r.validate_assembly(["M00", "事件:M22"])     # 缺 M80
        self.assertTrue(issues)
        self.assertTrue(any("M80" in i for i in issues))
        issues = r.validate_assembly(["事件:M22", "M80"])     # 缺 M00
        self.assertTrue(any("M00" in i for i in issues))

    def test_validate_assembly_ambiguous_bare(self):
        """裸号 M22 歧义 → 未登记提示（须用限定 ID）。"""
        issues = _registry().validate_assembly(["M22", "M00", "M80"])
        self.assertTrue(any("M22" in i and "未在注册表登记" in i for i in issues))

    def test_validate_assembly_community_module(self):
        """社区模块不入注册表 → 提示经社区包 Pxx 管线装载（R3 语义）。"""
        issues = _registry().validate_assembly(["情感:M22", "M00", "M80"])
        self.assertTrue(any("情感:M22" in i and "社区" in i for i in issues))

    def test_validate_assembly_p90_exempt(self):
        """M90 挂载层 P90 不在 mount_points → 豁免（02 §7/§9 设计意图）。"""
        r = _registry()
        issues = r.validate_assembly(["M90", "M00", "M80"])
        self.assertEqual(issues, [])


class TestCoreAnchorModules(unittest.TestCase):
    """收敛点助手：核心锚点由 mount_points P00/P80 default 推导。"""

    def test_core_anchor_modules_derived(self):
        self.assertEqual(_registry().core_anchor_modules(), ["M00", "M80"])

    def test_anchor_matches_mount_points_defaults(self):
        r = _registry()
        expected = (r.mount_points["P00"].get("default", [])
                    + r.mount_points["P80"].get("default", []))
        self.assertEqual(r.core_anchor_modules(), expected)


class TestAssetGet(unittest.TestCase):
    """T1-3 cross-package read-only asset addressing (C3 feat(runtime)).

    asset_get(source_package, key) semantics:
      - whitelist only: references[].asset_readonly is True and non-empty
        source_package (02 sect8.4 -> registry protocols[].references[])
      - authorized path: real file text under community/<source_package>/assets/
        read-only, no copy (I5 single-truth discipline)
      - key normalization: strip, drop .md suffix, forbid '/' and '..', must be
        plain file base name; unauthorized/traversal/missing -> None (no raise)
    """
    CAMPUS = "\u6821\u56ed\u60c5\u611f\u9886\u57df\u5305"   # campus emotion pack
    FANTASY = "\u897f\u5e7b\u751f\u5b58\u9886\u57df\u5305"  # fantasy survival pack

    @staticmethod
    def _registry_with_readonly(*packages):
        """Registry with whitelisted refs; bypasses load_registry lru_cache."""
        refs = [{'source_package': pkg, 'asset_readonly': True} for pkg in packages]
        return Registry(modules=[], mount_points={}, subscriptions={},
                        protocols=[{'id': 'demo', 'references': refs}])

    def test_authorized_package_reads_real_asset(self):
        r = self._registry_with_readonly(self.CAMPUS)
        content = r.asset_get(self.CAMPUS, 'ATTR_TEMPLATES')
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 1000)
        self.assertIn('ATTR_TEMPLATES', content[:200])

    def test_md_suffix_tolerated(self):
        r = self._registry_with_readonly(self.CAMPUS)
        self.assertEqual(r.asset_get(self.CAMPUS, 'ATTR_TEMPLATES.md'),
                         r.asset_get(self.CAMPUS, 'ATTR_TEMPLATES'))

    def test_unauthorized_package_returns_none(self):
        r = self._registry_with_readonly(self.CAMPUS)
        self.assertIsNone(r.asset_get(self.FANTASY, 'ATTR_TEMPLATES'))

    def test_traversal_and_separator_rejected(self):
        r = self._registry_with_readonly(self.CAMPUS)
        self.assertIsNone(r.asset_get(self.CAMPUS, '../README'))
        self.assertIsNone(r.asset_get(self.CAMPUS, 'a/b'))
        self.assertIsNone(r.asset_get(self.CAMPUS, '..'))

    def test_missing_key_returns_none(self):
        r = self._registry_with_readonly(self.CAMPUS)
        self.assertIsNone(r.asset_get(self.CAMPUS, 'NO_SUCH_ASSET'))

    def test_empty_whitelist_rejects_all(self):
        r = self._registry_with_readonly()
        self.assertIsNone(r.asset_get(self.CAMPUS, 'ATTR_TEMPLATES'))

    def test_empty_args_returns_none(self):
        r = self._registry_with_readonly(self.CAMPUS)
        self.assertIsNone(r.asset_get('', ''))
        self.assertIsNone(r.asset_get(self.CAMPUS, ''))

if __name__ == "__main__":
    unittest.main()
