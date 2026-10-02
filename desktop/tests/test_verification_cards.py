# -*- coding: utf-8 -*-
"""验证卡册一致性门禁（`docs/verification-cards.md` ↔ `verify.sh`）。

动机（本轮取证）：卡册自称由 `build_verification_cards.ps1` 生成，**该脚本不在仓库**——
对外是「不可复现的产物」，且漂移已经实际发生（卡册写 2409 行，verify.sh 实为 2516 行）。
本件把三件事钉死：① 生成区 == 实时重算（生成器已入库）；② 卡片覆盖全部 check；
③ 卡册引用的生成器**真实存在**（不许再指向仓外脚本）。
"""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

spec = importlib.util.spec_from_file_location("bvc", ROOT / "scripts" / "build_verification_cards.py")
bvc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bvc)


class VerificationCardsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = bvc.DOC.read_text(encoding="utf-8")
        cls.checks = bvc._checks()

    def test_generated_region_matches_live_recompute(self):
        self.assertEqual(self.doc, bvc.render(),
                         "卡册生成区与 verify.sh 不一致（跑 scripts/build_verification_cards.py --write）")

    def test_every_check_has_a_card_and_index_row(self):
        cards = {int(m) for m in re.findall(r"^### V(\d+) ·", self.doc, re.M)}
        index = {int(m) for m in re.findall(r"^\| (\d+) \|", self.doc, re.M)}
        want = {c["n"] for c in self.checks}
        self.assertEqual(want, cards, "卡片与 check 函数不一一对应")
        self.assertEqual(want, index, "索引表未覆盖全部 check")

    def test_line_count_claim_is_current(self):
        n = len(bvc.VERIFY.read_text(encoding="utf-8").splitlines())
        self.assertIn("| 门禁脚本 | %d 行（verify.sh 实测） |" % n, self.doc)

    def test_referenced_generator_is_shipped(self):
        """卡册引用的生成器必须**在仓库内**（此前指向仓外的 .ps1）。"""
        cited = set(re.findall(r"`([\w/.\-]*build_verification_cards[\w.\-]*)`", self.doc))
        self.assertTrue(cited, "卡册未标生成方式")
        for rel in cited:
            self.assertTrue((ROOT / rel).is_file(), "卡册引用了仓外生成器：%s" % rel)


if __name__ == "__main__":
    unittest.main()
