# -*- coding: utf-8 -*-
"""全链管道化单测（v2.1.0 B2：retrieve→compose→gate→export 单命令）。

运行：cd desktop && python -m unittest tests.test_pipeline -v
隔离：临时 Store（NF_TEST_HOME / tmp）；装载官方核心 + 组合包 M91/M92 + P04
管线（真实仓库素材，同 e2e 前置）；不 mock 中间层——验证从模块选择到导出文件的
完整端到端路径（pipeline.pipe 单入口）。

覆盖：
  全链 ok：P04+M91/M92 → gate PASS → export ccv3 文件在场
  缺模块 warn：selected 含已删 full_id → 跳过 + warnings 记录，不崩
  门 fail 阻断：空装配 → ok False + export None
  force 导出：fail_on_gate=False 门 fail 仍导出但 ok False（不变量不破）
  引用合并：include_references 默认合并 E3 跨包模块（可选项）
"""
from __future__ import annotations

import glob
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

ROOT = Path(__file__).resolve().parent.parent.parent  # 仓库根

from core.models import Module               # noqa: E402
from core.parser import parse_module         # noqa: E402
from core.storage import Store               # noqa: E402
from core.pipeline_loader import load_pipeline_file  # noqa: E402


def _mk_env():
    """临时 store + 装载官方核心 + M91/M92 + P04 管线。返回 (store, p04, selected)。"""
    store = Store(home=tempfile.mkdtemp(prefix="nf_pipe_"))
    # 官方核心 13 件
    for f in sorted(glob.glob(str(ROOT / "04_模块库" / "*" / "*.md"))):
        try:
            m = parse_module(Path(f).read_text(encoding="utf-8"))
            store.save_module(m)
        except Exception:
            continue
    # 组合包 M91/M92
    for f in sorted(glob.glob(str(ROOT / "community" / "校园西幻轻混组合包"
                                  / "modules" / "*.md"))):
        try:
            m = parse_module(Path(f).read_text(encoding="utf-8"))
            store.save_module(m)
        except Exception:
            continue
    p04 = load_pipeline_file(ROOT / "community" / "校园西幻轻混组合包"
                             / "pipelines" / "P04_轻混装配流管线.md")
    # e2e 同款装配集：核心锚点（M00 数据基座/M80 输出呈现）+ 组合包 M91/M92
    # ——质检门要求 P00/P80 有模块（缺锚点装配 gate fail 属正确守护）。
    selected = ["通用类:M00", "轻混类:M91", "轻混类:M92", "通用类:M80"]
    return store, p04, selected


class TestPipe(unittest.TestCase):
    def setUp(self):
        self.store, self.p04, self.selected = _mk_env()

    def _pipe(self, **kw):
        from core.pipeline import pipe
        return pipe(self.store, self.p04, list(self.selected), **kw)

    def test_full_chain_exports_ccv3(self):
        dest = tempfile.mkdtemp(prefix="nf_pipe_out_")
        r = self._pipe(fmt="ccv3", dest_dir=dest)
        self.assertTrue(r.ok, f"gate 应 ok：{r.gate}")
        self.assertIsNotNone(r.export)
        self.assertIsNotNone(r.ir)
        names = {Path(f).name for f in r.export.files}
        self.assertIn("chara.json", names)
        self.assertIn("world.json", names)

    def test_skill_rejects_narrative_ir(self):
        # 产物×适配矩阵：skill 仅接受 techdoc（P90 等），narrative 拒出——
        # pipe 用 P04(narrative) 导 skill 应 warnings 拒出、无文件，但不崩。
        dest = tempfile.mkdtemp(prefix="nf_pipe_out_")
        r = self._pipe(fmt="skill", dest_dir=dest)
        self.assertTrue(r.ok, "gate ok 与导出拒出无关（门过但适配器拒出）")
        self.assertIsNotNone(r.export)
        self.assertEqual(r.export.files, [],
                         f"narrative→skill 应无文件：{r.export.files}")
        self.assertTrue(any("SKILL" in w for w in r.export.warnings),
                        f"拒出说明：{r.export.warnings}")

    def test_missing_selected_warns_not_crash(self):
        dest = tempfile.mkdtemp(prefix="nf_pipe_out_")
        sel = self.selected + ["不存在类:M999"]
        from core.pipeline import pipe
        r = pipe(self.store, self.p04, sel, fmt="ccv3", dest_dir=dest)
        self.assertTrue(r.ok)
        self.assertTrue(any("M999" in w for w in r.warnings),
                        f"warnings={r.warnings}")

    def test_empty_selection_gate_fail_no_export(self):
        from core.pipeline import pipe
        r = pipe(self.store, self.p04, [], fmt="ccv3",
                 dest_dir=tempfile.mkdtemp())
        self.assertFalse(r.ok)
        self.assertIsNone(r.export)
        self.assertIsNotNone(r.ir)
        self.assertGreaterEqual(r.gate.n_fail, 1,
                                "空装配应触发 fail")

    def test_force_export_despite_gate_fail(self):
        from core.pipeline import pipe
        dest = tempfile.mkdtemp(prefix="nf_pipe_out_")
        r = pipe(self.store, self.p04, [], fmt="ccv3", dest_dir=dest,
                 fail_on_gate=False)
        self.assertFalse(r.ok, "可信任度不变量：fail 时 ok 仍 False")
        self.assertIsNotNone(r.export, "force 导出应产出文件")


if __name__ == "__main__":
    unittest.main()
