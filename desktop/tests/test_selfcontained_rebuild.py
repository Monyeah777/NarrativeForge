#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自包含装配样本重嵌工具单测（编码漂移检测 + 重嵌幂等 + 源逐字相等）。

工具：`scripts/rebuild_selfcontained_sample.py`。本测在**临时夹具**里造一份最小样本
（1 段管线 + 1 段模块），断言：① 内嵌正文被改坏（编码漂移）时 `--check` 判定有漂移；
② `--write` 后正文与源文件**逐字相等**；③ 再跑一次 `--check` 无漂移（幂等）。
"""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "selfcontained", ROOT / "scripts" / "rebuild_selfcontained_sample.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)


class SelfContainedRebuildTest(unittest.TestCase):
    def _fixture(self, tmp):
        root = Path(tmp)
        (root / "src").mkdir(parents=True, exist_ok=True)
        (root / "src" / "M00.md").write_text(
            "# 模块 M00 · 数据结构\n\n> 类别：通用\n\n## 1. 职责\n\n正文一\n",
            encoding="utf-8")
        (root / "src" / "P06.md").write_text(
            "# 管线 P06 · 装配流\n\nPipeline:\n  id: P06\n", encoding="utf-8")
        art = root / "sample.md"
        art.write_text(
            "---\nid: X\n---\n\n管线声明原文（内嵌）：\n\n```markdown\n# 绠＄嚎 P06\n```\n```\n\n"
            "## 3. 注册表投影\n\n表\n\n"
            "**4.1 M00_数据结构** · 归属：官方核心 · 溯源：src/M00.md\n\n"
            "```markdown\n# 妯″潡 M00 路 鏁版嵁缁撴瀯\n\n> 绫诲埆\n```\n\n"
            "## 5. 资产（0 文件）\n\n零资产\n",
            encoding="utf-8")
        return root, art

    def test_drift_detected_then_repaired_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, art = self._fixture(tmp)
            before = art.read_text(encoding="utf-8")
            lines, changes = sc.rebuild(before.splitlines(),
                                        str(root / "src" / "P06.md"), str(root))
            self.assertNotEqual(lines, before.splitlines(), "漂移样本应被判为有漂移")
            # 重嵌后：内嵌正文 == 源文件逐字
            src = (root / "src" / "M00.md").read_text(encoding="utf-8").splitlines()
            idx = lines.index("**4.1 M00_数据结构** · 归属：官方核心 · 溯源：src/M00.md")
            # 标记行 → 空行 → ```markdown 包裹 → 正文
            self.assertEqual(lines[idx + 3:idx + 3 + len(src)], src)
            # 幂等
            lines2, _ = sc.rebuild(lines, str(root / "src" / "P06.md"), str(root))
            self.assertEqual(lines, lines2)

    def test_real_artifacts_are_clean(self):
        """真产物：重嵌后应无漂移（本工具的输出就是仓库现存形态）。"""
        for rel in ("library/NF-TECHDOC-Monyeah777-1.md",
                    "docs/examples/state-front/techdoc_front.md"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            lines, _ = sc.rebuild(text.splitlines(),
                                  str(ROOT / "community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md"),
                                  str(ROOT))
            self.assertEqual(lines, text.splitlines(), "%s 应无编码漂移" % rel)


if __name__ == "__main__":
    unittest.main()
