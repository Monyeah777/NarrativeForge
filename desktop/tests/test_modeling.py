# -*- coding: utf-8 -*-
"""内容建模三件（词表 / 规范说明件 / 数据契约）正式与否定用例。"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import modeling as M  # noqa: E402


def _mk(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class TestRealRepo(unittest.TestCase):
    def test_all_three_clean(self):
        issues, warns, stats = M.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertEqual(warns, [])
        self.assertEqual(stats["vocabularies"]["schemes"], 12)
        self.assertGreaterEqual(stats["normative"]["normative"], 25)
        self.assertGreaterEqual(stats["data_contracts"]["contracts"], 8)

    def test_every_contract_rule_resolves(self):
        doc = json.loads((ROOT / M.DC_REL).read_text(encoding="utf-8"))
        verify = (ROOT / "verify.sh").read_text(encoding="utf-8")
        for c in doc["contracts"]:
            rule = c["quality_rule"]
            if rule.startswith("check"):
                self.assertIn("check%s(){" % rule[5:], verify, c["id"])
            else:
                self.assertTrue(rule.startswith("assertion:"), c["id"])


class TestVocabNegatives(unittest.TestCase):
    def _scene(self, tmp):
        for rel in (M.VOCAB_REL, "protocol/knowledge_sources.json"):
            _mk(tmp, rel, (ROOT / rel).read_text(encoding="utf-8"))
        return json.loads((Path(tmp) / M.VOCAB_REL).read_text(encoding="utf-8"))

    def test_drift_against_source_is_fail(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        doc = self._scene(tmp)
        doc["schemes"][0]["values"] = ["tutorial", "how-to", "reference", "essay"]
        _mk(tmp, M.VOCAB_REL, json.dumps(doc, ensure_ascii=False))
        self.assertTrue(any("与真源漂移" in i for i in M.verify_vocabularies(tmp)[0]))

    def test_unknown_probe_kind_is_fail(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        doc = self._scene(tmp)
        doc["schemes"][0]["probe"] = {"kind": "telepathy"}
        _mk(tmp, M.VOCAB_REL, json.dumps(doc, ensure_ascii=False))
        self.assertTrue(any("probe.kind 不在册" in i for i in M.verify_vocabularies(tmp)[0]))

    def test_alias_collision_is_fail(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        doc = self._scene(tmp)
        doc["schemes"][0]["aliases"] = ["tutorial"]
        _mk(tmp, M.VOCAB_REL, json.dumps(doc, ensure_ascii=False))
        self.assertTrue(any("alias 与值撞车" in i for i in M.verify_vocabularies(tmp)[0]))


class TestNormativeAndContractsNegatives(unittest.TestCase):
    def _base(self, tmp):
        _mk(tmp, "verify.sh", "check1(){ :; }\ncheck2(){ :; }\n")
        _mk(tmp, "protocol/assertions.json", json.dumps(
            {"schema": "nf-assertions/1", "assertions": [{"id": "a1"}]}, ensure_ascii=False))
        _mk(tmp, "art.json", "{}")
        _mk(tmp, "norm.md", "# n\n")

    def test_normative_without_owner_rights_is_fail(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        self._base(tmp)
        _mk(tmp, M.NORM_REL, json.dumps(
            {"schema": "nf-normative/1", "rule": "x",
             "normative": [{"path": "norm.md"}], "informative": []}, ensure_ascii=False))
        _mk(tmp, M.RECEIPTS_REL, json.dumps({"entries": []}, ensure_ascii=False))
        self.assertTrue(any("既未被回执锚定也无 covered_by" in i
                            for i in M.verify_normative(tmp)[0]))

    def test_informative_pinned_in_receipts_is_fail(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        self._base(tmp)
        _mk(tmp, M.NORM_REL, json.dumps(
            {"schema": "nf-normative/1", "rule": "x", "normative": [],
             "informative": ["norm.md"]}, ensure_ascii=False))
        _mk(tmp, M.RECEIPTS_REL, json.dumps({"entries": [{"id": "norm.md"}]},
                                            ensure_ascii=False))
        self.assertTrue(any("说明件被回执锚定" in i for i in M.verify_normative(tmp)[0]))

    def test_bad_quality_rule_is_fail(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        self._base(tmp)
        _mk(tmp, M.DC_REL, json.dumps(
            {"schema": "nf-data-contracts/1", "status_vocabulary": ["active"],
             "rule_prefixes": ["check", "assertion:"],
             "contracts": [{"id": "x", "artifact": "art.json", "quality_rule": "check999",
                            "owner": "机制", "status": "active", "freshness": "f",
                            "consumers": []}]}, ensure_ascii=False))
        self.assertTrue(any("不存在的 check" in i for i in M.verify_contracts(tmp)[0]))

    def test_missing_owner_is_fail(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        self._base(tmp)
        _mk(tmp, M.DC_REL, json.dumps(
            {"schema": "nf-data-contracts/1", "status_vocabulary": ["active"],
             "rule_prefixes": ["check", "assertion:"],
             "contracts": [{"id": "x", "artifact": "art.json", "quality_rule": "check1",
                            "owner": "", "status": "active", "freshness": "f",
                            "consumers": []}]}, ensure_ascii=False))
        self.assertTrue(any("缺 owner" in i for i in M.verify_contracts(tmp)[0]))

    def test_assertion_rule_resolves(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        self._base(tmp)
        _mk(tmp, M.DC_REL, json.dumps(
            {"schema": "nf-data-contracts/1", "status_vocabulary": ["active"],
             "rule_prefixes": ["check", "assertion:"],
             "contracts": [{"id": "x", "artifact": "art.json",
                            "quality_rule": "assertion:a1", "owner": "机制",
                            "status": "active", "freshness": "f", "consumers": []}]},
            ensure_ascii=False))
        self.assertEqual(M.verify_contracts(tmp)[0], [])


if __name__ == "__main__":
    unittest.main()
