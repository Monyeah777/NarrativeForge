# -*- coding: utf-8 -*-
"""派生空壳台账（`core/shell_ledger.py`）回归测试：可数 + 只减不增 + 有捕获力。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import shell_ledger as sl  # noqa: E402


class ShellLedgerTest(unittest.TestCase):
    def test_real_repo_within_baseline(self):
        issues, stats = sl.ratchet(str(ROOT))
        self.assertEqual([], issues, "派生空壳超基线：%s" % issues)
        self.assertEqual(sl.BASELINE["packs_total"], stats["packs_total"])
        self.assertLessEqual(stats["hits"], sl.BASELINE["hits"])
        self.assertEqual([], stats["mismatches"], "域口径表 md↔json 双源不一致")

    def test_every_shell_pack_has_the_same_shape(self):
        """空壳包的口径表是「12 条 × 3 处占位」的同型派生——形状漂了要能被看见。"""
        stats = sl.survey(str(ROOT))
        odd = {k: v for k, v in stats["per_package"].items()
               if v != sl.BASELINE["per_shell_pack"]}
        self.assertEqual({}, odd, "空壳包出现异型条目数（要么补全了、要么派生走样）")

    def test_ratchet_catches_a_new_shell_pack(self):
        """变异自证：新造一个带占位的域包必须被判红（否则棘轮是空转）。"""
        with tempfile.TemporaryDirectory() as tmp:
            body = "".join("| 领域细则待作者补全 |\n" for _ in range(36))
            for i in range(sl.BASELINE["packs_total"]):
                d = Path(tmp, "community", "域包%03d" % i, "assets")
                d.mkdir(parents=True)
                (d / "DOMAIN_SPEC.md").write_text(body, encoding="utf-8")
            issues, stats = sl.ratchet(tmp)
            self.assertEqual(sl.BASELINE["packs_total"] * 36, stats["hits"])
            self.assertTrue(any("空壳" in i for i in issues), issues)


class TierDeclarationTest(unittest.TestCase):
    """**档位如实**：人读声明 ⇄ 机读 `content_tier` ⇄ 正文占位，三处必须同真。

    依据（2026-10-01 取证）：档位行只是声明，条目正文来自内部规格的 `definition/check/pitfall`
    原文 ⇒ 两条静默错误路径都不拦——① 把 `content_tier` 标成 `authored`（或新包忘了标 derived）
    而正文仍带占位 = **虚报完成度**；② 真填了却忘翻档位 = **少报完成度**（缺口台账虚高）。
    补全这件事此前只按占位计数记账，现在三处钉在一起。
    """

    def test_real_repo_tier_declarations_are_truthful(self):
        stats = sl.survey(str(ROOT))
        self.assertEqual([], stats["tier_mismatches"],
                         "档位声明与实况不符：%s" % stats["tier_mismatches"][:3])
        # 非空转：仓里**同时**存在两种档位，判据才有区分力
        tiers = set()
        import json as _json
        for p in ROOT.glob("community/*/outputs/DOMAIN_SPEC.json"):
            tiers.add(_json.loads(p.read_text(encoding="utf-8")).get("content_tier"))
        self.assertEqual({"authored", "derived"}, tiers, "真仓应同时有 authored 与 derived 两档")

    def test_mutation_lying_tier_is_caught(self):
        """变异自证：① 声明 authored 却留占位；② 声明 derived 却已无占位——两条都要报。"""
        with tempfile.TemporaryDirectory() as tmp:
            for name, tier, body in (
                    ("虚报", "authored", "| 领域细则待作者补全 |\n" * 3),   # 声称已撰写，实带占位
                    ("少报", "derived", "| 真判据：字段齐全 |\n"),          # 真填了却仍标 derived
            ):
                pkg = Path(tmp, "community", name)
                (pkg / "assets").mkdir(parents=True)
                (pkg / "assets" / "DOMAIN_SPEC.md").write_text(
                    "> **内容档位**：authored（逐条撰写）\n" if tier == "authored"
                    else "> **内容档位（如实标注）**：本包为 **derived 档**——领域细则待作者逐条补全。\n",
                    encoding="utf-8")
                (pkg / "outputs").mkdir()
                (pkg / "outputs" / "DOMAIN_SPEC.json").write_text(
                    '{"content_tier": "%s", "subdivisions": []}' % tier, encoding="utf-8")
                # 把正文拼到 md 里（含占位与不含占位两种）
                with (pkg / "assets" / "DOMAIN_SPEC.md").open("a", encoding="utf-8") as fh:
                    fh.write(body)
            stats = sl.survey(tmp)
            joined = " ".join(stats["tier_mismatches"])
            self.assertIn("虚报", joined, "声称 authored 却带占位必须报：%s" % stats["tier_mismatches"])
            self.assertIn("少报", joined, "真填了却仍标 derived 必须报：%s" % stats["tier_mismatches"])

    def test_tier_mismatch_feeds_the_ratchet(self):
        """接线：对账结果必须进 `ratchet` 的 issues（否则只是台账里的一行数据）。"""
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp, "community", "错档")
            (pkg / "assets").mkdir(parents=True)
            (pkg / "assets" / "DOMAIN_SPEC.md").write_text(
                "> **内容档位**：authored（逐条撰写）\n| 领域专属判据待补 |\n", encoding="utf-8")
            (pkg / "outputs").mkdir()
            (pkg / "outputs" / "DOMAIN_SPEC.json").write_text(
                '{"content_tier": "authored"}', encoding="utf-8")
            issues, _stats = sl.ratchet(tmp)
            self.assertTrue(any("档位声明与实况不符" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
