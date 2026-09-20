#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提交信息机检单测（CONTRIBUTING §1 判据化 · 含"不打断自动化"回归）。

工具：`scripts/commit_msg_check.py`（commit-msg 钩子消费）。判据由**仓库提交史实证**校准：
type 词表含 `release`/`merge`/`ci`/`lib`，scope 从宽、多 type 可并联、不设行长上限。
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cmc", ROOT / "scripts" / "commit_msg_check.py")
cmc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmc)


class CommitMsgCheckTest(unittest.TestCase):
    def test_valid_forms_pass(self):
        for msg in ("feat(core): 新增判据",
                    "docs: 补登记",
                    "refactor(verify): 收口",
                    "test(core): 补例",
                    "chore: 杂项",
                    "release(v2.10.0): 收口发布",
                    "merge(remote main): 并流",
                    "ci(workflow): 分层",
                    "lib(Y12): 云端代收 NF-9 自动入库（Issue #1，投稿人 X）",
                    "feat!: 破坏性变更",
                    "docs+feat(quality): 多 type 并联",
                    "feat(41,B1): scope 带逗号",
                    "feat(docs+test): scope 带加号",
                    "feat(core): 主题\n\n正文",
                    "# 注释行\nfeat(core): 带注释模板"):
            self.assertEqual(cmc.check(msg), [], "应合规：%r" % msg)

    def test_bypass_forms_pass(self):
        for msg in ("Merge branch 'main'", 'Revert "feat: x"', "fixup! feat: x", "squash! x", "", "\n\n"):
            self.assertEqual(cmc.check(msg), [], "应放行：%r" % msg)

    def test_invalid_forms_caught(self):
        cases = {
            "少冒号": "feat(core) 新增判据",
            "type 越词表": "unknown(core): 类型不在词表",
            "缺 subject": "feat(core): ",
            "句号结尾": "feat(core): 以句号结尾。",
            "英文句点结尾": "feat(core): ends with period.",
            "正文未空行": "feat(core): 摘要\n正文紧贴",
        }
        for label, msg in cases.items():
            self.assertTrue(cmc.check(msg), "%s 未被捕获：%r" % (label, msg))

    def test_automation_commits_pass(self):
        """**不得打断自动化**：两个入库机器人的提交格式必须通过。"""
        for msg in ("lib(Y12): 云端代收 NF-9 自动入库（Issue #1，投稿人 X）",
                    "lib(Y12): Gitee 云端代收 NF-9 自动入库（Gitee Issue #1，投稿人 X）"):
            self.assertEqual(cmc.check(msg), [])

    def test_self_test_flag_green(self):
        self.assertEqual(cmc.main(["--self-test"]), 0)


if __name__ == "__main__":
    unittest.main()
