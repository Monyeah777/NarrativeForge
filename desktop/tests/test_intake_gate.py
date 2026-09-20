# -*- coding: utf-8 -*-
"""投稿闸门声明的三方一致门禁测试（check34 子断言 `core.intake`）。

覆盖：仓库真源零 issue（两通道）；负例九类——缺声明 / schema 错 / updated 非法 /
缺 after_action / channels 空 / mode 越词表 / author_only 无白名单 / index_label 未出现在
INDEX / 机器人未引用声明件；以及 fail-closed：声明不可解析即 FAIL。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import intake as ik  # noqa: E402


def _decl(**over) -> dict:
    doc = {
        "schema": "nf-intake/1",
        "updated": "2026-09-20",
        "after_action": "lifecycle",
        "channels": {
            "gitee": {"mode": "open", "index_label": "公开开放 · 零门槛"},
            "github": {"mode": "author_only", "allowlist": ["author_one"],
                       "index_label": "仅作者本人自投"},
        },
        "note": "夹具",
    }
    doc.update(over)
    return doc


def _tree(tmp: str, doc: dict = None, index_text: str = None, bots: bool = True) -> str:
    root = Path(tmp)
    (root / "library").mkdir(parents=True, exist_ok=True)
    (root / "library" / "intake.json").write_text(
        json.dumps(doc if doc is not None else _decl(), ensure_ascii=False), encoding="utf-8")
    (root / "library" / "INDEX.md").write_text(
        index_text if index_text is not None else "# INDEX\n\n公开开放 · 零门槛\n仅作者本人自投\n",
        encoding="utf-8")
    if bots:
        for rel in ik.BOTS:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("# 机器人夹具（读 %s）\n" % ik.INTAKE_REL, encoding="utf-8")
    return tmp


class RepoIntakeTest(unittest.TestCase):
    def test_repo_declaration_is_consistent(self):
        issues, stats = ik.scan(str(ROOT))
        self.assertEqual(issues, [], issues)
        self.assertEqual(stats["channels"], 2)
        self.assertEqual(stats["modes"], ["author_only", "open"])

    def test_repo_bots_are_wired(self):
        for rel in ik.BOTS:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn(ik.INTAKE_REL, text, rel)


class IntakeNegativeTest(unittest.TestCase):
    def _scan(self, **kw):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, **kw)
            return ik.scan(tmp)

    def test_missing_declaration_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _ = ik.scan(tmp)
        self.assertTrue(any("缺投稿闸门声明" in i for i in issues), issues)

    def test_broken_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp)
            (Path(tmp) / ik.INTAKE_REL).write_text("{ 不是 JSON", encoding="utf-8")
            issues, _ = ik.scan(tmp)
        self.assertTrue(any("缺投稿闸门声明" in i for i in issues), issues)

    def test_schema_and_updated_and_after_action_checked(self):
        issues, _ = self._scan(doc=_decl(schema="nf-intake/9", updated="today",
                                         after_action=""))
        self.assertTrue(any("schema 不匹配" in i for i in issues), issues)
        self.assertTrue(any("updated 非 YYYY-MM-DD" in i for i in issues), issues)
        self.assertTrue(any("after_action" in i for i in issues), issues)

    def test_empty_channels_rejected(self):
        issues, _ = self._scan(doc=_decl(channels={}))
        self.assertTrue(any("channels 为空" in i for i in issues), issues)

    def test_unknown_mode_rejected(self):
        doc = _decl(channels={"gitee": {"mode": "whatever",
                                        "index_label": "公开开放 · 零门槛"}})
        issues, _ = self._scan(doc=doc)
        self.assertTrue(any("mode 非法" in i for i in issues), issues)

    def test_author_only_without_allowlist_rejected(self):
        doc = _decl(channels={"github": {"mode": "author_only", "allowlist": [],
                                         "index_label": "仅作者本人自投"}})
        issues, _ = self._scan(doc=doc)
        self.assertTrue(any("allowlist 为空" in i for i in issues), issues)

    def test_index_label_drift_detected(self):
        """闸门变了、须知没变 → FAIL（防漂移，这正是外部实证的失败模式）。"""
        issues, _ = self._scan(index_text="# INDEX\n\n只有一句别的话\n")
        self.assertTrue(any("未出现在" in i for i in issues), issues)

    def test_bot_not_wired_detected(self):
        issues, _ = self._scan(bots=False)
        self.assertTrue(any("未引用闸门声明" in i or "缺入库机器人脚本" in i for i in issues),
                        issues)

    def test_paused_mode_is_a_legal_switch(self):
        """作者一键关闸：paused 是合法 mode（且无需白名单）。"""
        doc = _decl(channels={"gitee": {"mode": "paused",
                                        "index_label": "公开开放 · 零门槛"}})
        issues, stats = self._scan(doc=doc)
        self.assertEqual(issues, [], issues)
        self.assertEqual(stats["modes"], ["paused"])


if __name__ == "__main__":
    unittest.main()
