# -*- coding: utf-8 -*-
"""双源知识层（knowledge）正式与否定用例：声明 / 顺序 / 溯源 / 巡检。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import knowledge as kn  # noqa: E402


def _mk(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _tree(tmp):
    """最小双源树：复制真源声明/记录，并按声明补出 locator 与在册模块。"""
    decl = json.loads((ROOT / kn.DECL_REL).read_text(encoding="utf-8"))
    log = json.loads((ROOT / kn.LOG_REL).read_text(encoding="utf-8"))
    _mk(tmp, kn.DECL_REL, json.dumps(decl, ensure_ascii=False))
    _mk(tmp, kn.LOG_REL, json.dumps(log, ensure_ascii=False))
    for s in decl["sources"]:
        p = Path(tmp, s["locator"])
        if p.suffix:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x", encoding="utf-8")
        else:
            p.mkdir(parents=True, exist_ok=True)
    _mk(tmp, "04_模块库/通用类/M23_认知边界.md",
        "# 模块 M23\n\n```yaml\nmachine_contract:\n  id: M23\n```\n")
    _mk(tmp, "library/NF-1.md", "---\nid: NF-1\nstale_after: 2027-03-14\n---\n\n# NF-1\n")
    _mk(tmp, "library/INDEX.md", "| NF-1 | 世界 |\n")
    _mk(tmp, "llms.txt", "# NF\nlibrary/NF-1.md\n")
    return decl, log


def _write_decl(tmp, decl):
    _mk(tmp, kn.DECL_REL, json.dumps(decl, ensure_ascii=False))


class TestDeclarationRealRepo(unittest.TestCase):
    def test_scan_clean(self):
        issues, _warns, stats = kn.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertEqual(stats["sources"], 6)
        self.assertEqual(stats["contract"], 3)
        self.assertEqual(stats["reference"], 3)

    def test_query_order_is_contract_first(self):
        order = kn.resolve_order(str(ROOT))
        auths = [x["authority"] for x in order]
        self.assertEqual(auths, sorted(auths, key=lambda a: 0 if a == "contract" else 1))
        self.assertEqual(len(order), 6)

    def test_every_reference_requires_source_label(self):
        rows = kn.sources(str(ROOT))
        refs = [s for s in rows if s["authority"] == "reference"]
        self.assertTrue(refs)
        for s in refs:
            self.assertTrue(s["requires_source_label"], s["id"])


class TestDeclarationNegatives(unittest.TestCase):
    def _cases(self, tmp, mutate):
        decl, _log = _tree(tmp)
        mutate(decl)
        _write_decl(tmp, decl)
        return kn.scan(tmp)[0]

    def test_reference_without_source_label_is_fail(self):
        def m(decl):
            for s in decl["sources"]:
                if s["authority"] == "reference":
                    s["requires_source_label"] = False
                    return
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("未要求标注来源" in i for i in issues), issues)

    def test_reference_without_freshness_is_fail(self):
        def m(decl):
            for s in decl["sources"]:
                if s["authority"] == "reference":
                    s["freshness"] = {"policy": "stale_after"}
                    return
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("时效策略非法" in i for i in issues), issues)

    def test_ttl_without_positive_days_is_fail(self):
        def m(decl):
            for s in decl["sources"]:
                if s["freshness"].get("policy") == "ttl":
                    s["freshness"]["ttl_days"] = 0
                    return
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("ttl_days 非正整数" in i for i in issues), issues)

    def test_missing_locator_is_fail(self):
        def m(decl):
            decl["sources"][0]["locator"] = "nowhere/at/all"
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("locator 不存在" in i for i in issues), issues)

    def test_order_missing_id_is_fail(self):
        def m(decl):
            decl["query_order"] = decl["query_order"][:-1]
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("query_order 与 sources 不是同一集合" in i for i in issues), issues)

    def test_reference_before_contract_is_fail(self):
        def m(decl):
            decl["query_order"] = decl["query_order"][::-1]
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("查询有序被破坏" in i for i in issues), issues)

    def test_promotion_tier_vocab_is_fail(self):
        def m(decl):
            decl["promotion"]["evidence_tiers"] = ["machine-checkable"]
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("evidence_tiers" in i for i in issues), issues)

    def test_missing_on_missing_evidence_is_fail(self):
        def m(decl):
            decl["promotion"]["on_missing_evidence"] = "promote-anyway"
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("stay-reference" in i for i in issues), issues)

    def test_cognition_filter_module_absent_is_fail(self):
        def m(decl):
            decl["cognition"]["filter_module"] = "M99"
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("不在册模块" in i for i in issues), issues)

    def test_duplicate_source_id_is_fail(self):
        def m(decl):
            decl["sources"].append(dict(decl["sources"][0]))
        issues = self._cases(tempfile.mkdtemp(), m)
        self.assertTrue(any("源 id 重复" in i for i in issues), issues)


class TestTransform(unittest.TestCase):
    def _log(self, tmp, entry):
        _tree(tmp)
        _mk(tmp, kn.LOG_REL, json.dumps(
            {"schema": kn.LOG_SCHEMA, "entries": [entry]}, ensure_ascii=False))
        return kn.verify_transform(tmp)[0]

    def _base(self, tmp, **over):
        _tree(tmp)                      # 先建最小树，digest 才可算（_tree 确定性，重复调用不扰动）
        digest = kn.sha256_file(str(Path(tmp, "library/NF-1.md")))
        e = {"from": "ext-fixtures", "to": "library/NF-1.md", "digest": digest,
             "reviewed_by": "", "reviewed_at": "", "evidence": [],
             "promoted": False, "reuse_count": 0}
        e.update(over)
        return e

    def test_valid_entry_passes(self):
        tmp = tempfile.mkdtemp()
        issues = self._log(tmp, self._base(tmp))
        self.assertEqual(issues, [])

    def test_digest_mismatch_is_fail(self):
        tmp = tempfile.mkdtemp()
        issues = self._log(tmp, self._base(tmp, digest="0" * 64))
        self.assertTrue(any("摘要与记录不一致" in i for i in issues), issues)

    def test_from_must_be_declared_reference_source(self):
        tmp = tempfile.mkdtemp()
        issues = self._log(tmp, self._base(tmp, **{"from": "nf-library"}))
        self.assertTrue(any("不是已声明的参考级源" in i for i in issues), issues)

    def test_promotion_without_full_evidence_is_fail(self):
        tmp = tempfile.mkdtemp()
        issues = self._log(tmp, self._base(tmp, promoted=True,
                                          evidence=["machine-checkable"],
                                          reviewed_by="作者", reviewed_at="2026-09-15"))
        self.assertTrue(any("缺证据档" in i for i in issues), issues)

    def test_promotion_without_reviewer_is_fail(self):
        tmp = tempfile.mkdtemp()
        issues = self._log(tmp, self._base(tmp, promoted=True,
                                          evidence=list(kn.TIERS),
                                          reviewed_by="", reviewed_at="2026-09-15"))
        self.assertTrue(any("无复核人" in i for i in issues), issues)

    def test_bad_reuse_count_is_fail(self):
        tmp = tempfile.mkdtemp()
        issues = self._log(tmp, self._base(tmp, reuse_count="many"))
        self.assertTrue(any("reuse_count" in i for i in issues), issues)


class TestLint(unittest.TestCase):
    def test_real_repo_lints_clean_with_freshness_warn(self):
        issues, warns, stats = kn.lint(str(ROOT))
        self.assertEqual(issues, [])
        self.assertEqual(stats["orphan"], 0)
        self.assertEqual(stats["dangling"], 0)
        self.assertTrue(any("stale_after" in w for w in warns), warns)

    def test_dangling_reference_is_fail(self):
        tmp = tempfile.mkdtemp()
        _tree(tmp)
        _mk(tmp, "llms.txt", "# NF\nlibrary/NF-1.md\nlibrary/NF-9.md\n")
        issues = kn.lint(tmp)[0]
        self.assertTrue(any("悬空引用" in i for i in issues), issues)

    def test_orphan_entry_is_fail(self):
        tmp = tempfile.mkdtemp()
        _tree(tmp)
        _mk(tmp, "library/NF-9.md", "---\nid: NF-9\nstale_after: 2027-01-01\n---\n\n# NF-9\n")
        issues = kn.lint(tmp)[0]
        self.assertTrue(any("孤儿条目" in i for i in issues), issues)

    def test_missing_stale_after_is_warn_not_fail(self):
        tmp = tempfile.mkdtemp()
        _tree(tmp)
        _mk(tmp, "library/NF-1.md", "---\nid: NF-1\n---\n\n# NF-1\n")
        issues, warns, _stats = kn.lint(tmp)
        self.assertEqual(issues, [])
        self.assertTrue(any("stale_after" in w for w in warns), warns)


if __name__ == "__main__":
    unittest.main()
