#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门禁可见性回归测试 —— 「门禁本身有没有门禁」里**看得见**的那一半。

背景（实证）：2026-09-26～27 云端 `ci-verify` 连红 21 次（#155–#175，此前最后一次成功 #154），
仓库侧没有任何一处把这件事摆到人读面，也没有判据要求「push 触发的那条 workflow 跑的必须是
**全量** `verify.sh`」——`verify.sh` 与 core/scripts 的 check 都不读 `.github/`，该面此前只有
`test_ci_supply_chain` 管了 action 固定。于是「本机绿、云端红」可以静默持续三周。

本测试把两条钉住：
① 两份入口都带 ci-verify 徽章，且徽章指向的 workflow **真实在场**（改名即红，防徽章静默 404）；
② ci-verify.yml 跑的是全量 `bash verify.sh` 且 push→main 即触发（不是某个 check 子集、不是只手动）。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
ENTRIES = ("README.md", "README.en.md")

#: GitHub 徽章 URL：https://github.com/<owner>/<repo>/actions/workflows/<wf>.yml/badge.svg
_BADGE = re.compile(
    r"https://github\.com/[^/\s)]+/[^/\s)]+/actions/workflows/([A-Za-z0-9_.\-]+\.ya?ml)/badge\.svg")
_RUN = re.compile(r"(?m)^\s*-?\s*run:\s*(.+?)\s*$")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class GateVisibilityTest(unittest.TestCase):
    def test_entries_carry_ci_badge_pointing_at_real_workflow(self):
        """两份入口都须带徽章，且徽章指向的 workflow 件真实在场（改名即红）。"""
        for rel in ENTRIES:
            hits = _BADGE.findall(_read(ROOT / rel))
            self.assertTrue(hits, "%s 缺 CI 徽章 —— 云端连红将再次无人察觉" % rel)
            for wf in hits:
                self.assertTrue((WORKFLOWS / wf).is_file(),
                                "%s 的徽章指向不存在的 workflow：%s（徽章会静默 404）" % (rel, wf))

    def test_badge_covers_the_workflow_that_runs_the_gate(self):
        """徽章盯的必须是跑全量 `verify.sh` 的那条 workflow（不是 lint/coverage 之类旁支）。"""
        names = {wf for rel in ENTRIES for wf in _BADGE.findall(_read(ROOT / rel))}
        self.assertTrue(names, "两份入口都没有 CI 徽章")
        for wf in names:
            self.assertRegex(_read(WORKFLOWS / wf), r"(?m)^\s*-?\s*run:\s*bash verify\.sh\s*$",
                             "%s 不是跑全量 verify.sh 的那条 workflow" % wf)

    def test_gate_workflow_runs_full_verify_not_a_subset(self):
        """唯一入口纪律：CI 里只许裸跑全量，传子集参数即等于假绿。"""
        runs = [r.strip() for r in _RUN.findall(_read(WORKFLOWS / "ci-verify.yml"))]
        verify_runs = [r for r in runs if "verify.sh" in r]
        self.assertEqual(["bash verify.sh"], verify_runs,
                         "CI 里的 verify.sh 调用必须恰好是 `bash verify.sh`")

    def test_gate_workflow_triggers_on_push_to_main(self):
        """推 main 即跑：徽章盯的是推送后的真实结论，不是手动才跑的空壳。"""
        text = _read(WORKFLOWS / "ci-verify.yml")
        self.assertRegex(text, r"(?m)^on:\s*$")
        self.assertRegex(text, r"(?m)^\s{2}push:\s*$")
        self.assertRegex(text, r"(?m)^\s{4}branches:\s*\[main\]\s*$")

