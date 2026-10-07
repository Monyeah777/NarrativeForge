# -*- coding: utf-8 -*-
"""发布编排（core/release_gate.py）回归：机读策略过 schema + 计划有序 + golden 快照 + 变异自证。"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import release_gate as rg  # noqa: E402

GOLDEN = ROOT / "desktop" / "tests" / "fixtures" / "release" / "plan.golden.json"
GOOD_POLICY = "\n".join(["## 冻结链", "## 版本面", "## Golden Master", "## 变更条目",
                          "bash verify.sh", "scripts/release_freeze.sh",
                          "python scripts/nf.py conformance --write", "nf approve",
                          "python scripts/nf.py receipts --scope protocol --write"])
GOOD_JSON = {
    "schema": "nf-release-policy/1", "policy_doc": "docs/release.md",
    "freeze_chain": list(rg.DEFAULT_FREEZE_CHAIN),
    "required_artifacts": ["verify.sh"], "golden_required": ["verify.sh", "README.md", "CHANGELOG.md"],
    "version_faces": ["README.md", "CHANGELOG.md"], "changes_dir": "changes/unreleased",
}


def _mini(root: Path, policy_doc: str, policy_json=None) -> None:
    (root / "verify.sh").write_text("# 版本 : v9.9\ncheck1(){\n:\n}\n", encoding="utf-8")
    (root / "README.md").write_text("# T\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## [9.9.0] - 未发布\n", encoding="utf-8")
    (root / "docs/meta").mkdir(parents=True, exist_ok=True)
    (root / "docs/meta/VERSION-MATRIX.md").write_text("| v9.9.0 | \u2705 |\n", encoding="utf-8")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "release.md").write_text(policy_doc, encoding="utf-8")
    (root / "protocol").mkdir(parents=True, exist_ok=True)
    sdir = root / "protocol" / "schema"
    sdir.mkdir(parents=True, exist_ok=True)
    src = ROOT / "protocol" / "schema" / "release.schema.json"
    if src.is_file():
        (sdir / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    if policy_json is not None:
        (root / "protocol" / "release_policy.json").write_text(
            json.dumps(policy_json, ensure_ascii=False), encoding="utf-8")


class PlanTest(unittest.TestCase):
    def test_plan_covers_freeze_chain_in_order(self):
        steps = rg.plan(str(ROOT))
        cmds = [s["cmd"] for s in steps]
        pos = [next(i for i, c in enumerate(cmds) if c.startswith(x)) for x in rg.DEFAULT_FREEZE_CHAIN]
        self.assertEqual(sorted(pos), pos, "冻结链顺序不可颠倒：%s" % pos)
        self.assertGreaterEqual(len(steps), 10, "计划退化成空转")

    def test_every_step_has_three_columns(self):
        for s in rg.plan(str(ROOT)):
            for k in ("cmd", "out", "judge"):
                self.assertTrue(s.get(k), "步骤 %s 缺 %s" % (s["id"], k))

    def test_plan_matches_golden_snapshot(self):
        """golden 快照（release-please __snapshots__ 同法）：计划**结构**漂移即红。"""
        want = json.loads(GOLDEN.read_text(encoding="utf-8"))
        got = {"freeze_chain": list(rg.policy(str(ROOT))[0]["freeze_chain"]),
               "steps": [[s["id"], s["title"]] for s in rg.plan(str(ROOT))],
               "policy_schema": rg.POLICY_SCHEMA_ID}
        self.assertEqual(want, got, "发布计划与 golden 快照不一致（有意改动请重出快照）")


class CheckTest(unittest.TestCase):
    def test_real_repo_has_no_issue(self):
        issues, stats = rg.check(str(ROOT))
        self.assertEqual([], issues, issues)
        self.assertTrue(stats["release_line"], "发布线读不到（判据可能空转）")
        self.assertGreaterEqual(stats["plan_steps"], 10)

    def test_policy_schema_violation_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            bad = dict(GOOD_JSON)
            bad["schema"] = "nope/9"
            _mini(Path(d), GOOD_POLICY, bad)
            issues, _ = rg.check(d)
            self.assertTrue(any("越界" in i for i in issues), issues)

    def test_missing_policy_doc_anchor_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            _mini(Path(d), "## 冻结链\n缺其余段\n", GOOD_JSON)
            issues, _ = rg.check(d)
            self.assertTrue(any("缺声明锚点" in i for i in issues), issues)

    def test_change_entry_without_note_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            _mini(Path(d), GOOD_POLICY, GOOD_JSON)
            ch = Path(d) / "changes" / "unreleased"
            ch.mkdir(parents=True)
            (Path(d) / "changes" / "README.md").write_text("# rule\n", encoding="utf-8")
            (ch / "x.md").write_text("type: feat\n", encoding="utf-8")
            issues, _ = rg.check(d)
            self.assertTrue(any("note" in i for i in issues), issues)

    def test_golden_snapshot_structure_caught(self):
        with tempfile.TemporaryDirectory() as d:
            _mini(Path(d), GOOD_POLICY, GOOD_JSON)
            snap = Path(d) / rg.GOLDEN_DIR / "v9.9.0"
            snap.mkdir(parents=True)
            (snap / "sha256.manifest").write_text("deadbeef\n", encoding="utf-8")
            issues, _ = rg.check(d)
            self.assertTrue(any(rg.GOLDEN_DIR in i for i in issues), issues)

    def test_empty_root_reports_issue_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            issues, stats = rg.check(d)
            self.assertTrue(issues)
            self.assertEqual({}, stats)

    def test_manifest_is_deterministic(self):
        a = json.dumps(rg.manifest(str(ROOT)), ensure_ascii=False, sort_keys=True)
        b = json.dumps(rg.manifest(str(ROOT)), ensure_ascii=False, sort_keys=True)
        self.assertEqual(a, b)


class PolicyJsonTest(unittest.TestCase):
    def test_policy_json_is_schema_clean(self):
        pol, issues = rg.policy(str(ROOT))
        self.assertEqual([], issues)
        self.assertEqual("nf-release-policy/1", pol["schema"])
        self.assertTrue(re.match(r"^docs/.+\.md$", pol["policy_doc"]))


if __name__ == "__main__":
    unittest.main()
