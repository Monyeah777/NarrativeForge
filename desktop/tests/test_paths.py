#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`core.paths.validate_path` 单测 —— 2026-09-24 渗透发现 F-09 的判据。

背景：AGENTS.md / CONTRIBUTING.md 把「路径逃逸被 validatePath 拦截」写成事实，
而仓库此前**没有任何 validatePath**（唯一判据是 asset_ledger 的私有 _safe_join）。
本测试把「该控制真实存在且能拦住逃逸」钉死，并覆盖变异样本（`..`、绝对路径、越根绝对路径）。
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import asset_ledger as al  # noqa: E402
from core import paths  # noqa: E402
from core.storage import Store  # noqa: E402


class ValidatePathTest(unittest.TestCase):
    def test_relative_inside_root_is_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            got = paths.validate_path(root, "assets/A1.md")
            self.assertTrue(got.startswith(os.path.realpath(root)))
            self.assertTrue(got.endswith(os.path.join("assets", "A1.md")))

    def test_dotdot_segment_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            for bad in ("../evil.md", "a/../../evil.md", "..\\evil.md"):
                with self.assertRaises(paths.PathEscapeError, msg=bad):
                    paths.validate_path(root, bad)

    def test_absolute_path_is_rejected_by_default(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(paths.PathEscapeError):
                paths.validate_path(root, os.path.join(root, "A1.md"))

    def test_absolute_outside_root_is_rejected_even_when_allowed(self):
        """allow_absolute 只放行写法，不放行落点——包含性判据在任何写法下成立。"""
        with tempfile.TemporaryDirectory() as root:
            outside = os.path.join(tempfile.gettempdir(), "nf_outside_probe.md")
            with self.assertRaises(paths.PathEscapeError):
                paths.validate_path(root, outside, allow_absolute=True)

    def test_absolute_inside_root_is_accepted_when_allowed(self):
        with tempfile.TemporaryDirectory() as root:
            inside = os.path.join(root, "A1.md")
            self.assertEqual(os.path.realpath(inside),
                             paths.validate_path(root, inside, allow_absolute=True))

    def test_empty_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            for bad in ("", "   "):
                with self.assertRaises(paths.PathEscapeError):
                    paths.validate_path(root, bad)

    def test_message_carries_fix_guidance(self):
        with tempfile.TemporaryDirectory() as root:
            try:
                paths.validate_path(root, "../x.md")
            except paths.PathEscapeError as exc:
                self.assertIn("修复指引", str(exc))
            else:
                self.fail("应抛 PathEscapeError")

    def test_symlink_escape_is_rejected_when_creatable(self):
        """软链指向根外时须拒（Windows 无权限建链则跳过，不算失败）。"""
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as out:
            link = os.path.join(root, "link")
            try:
                os.symlink(out, link)
            except (OSError, NotImplementedError, AttributeError):
                self.skipTest("当前环境无法创建符号链接")
            with self.assertRaises(paths.PathEscapeError):
                paths.validate_path(root, "link/escape.md")


class GuardRecursiveDeleteTargetTest(unittest.TestCase):
    """F-10：递归删除目标的落点闸门（灾难性落点必须拒）。

    `NF_TEST_HOME` 曾被原样当 `shutil.rmtree` 目标。本测试**只调判据、不删任何东西**，
    覆盖 `~` / 仓库根 / 仓库根的上级 / 系统临时目录本身 / 盘根五类灾难性落点。
    """

    def _default(self):
        return os.path.join(tempfile.gettempdir(), "nf_e2e_home")

    def test_empty_uses_default(self):
        self.assertEqual(self._default(),
                         paths.guard_recursive_delete_target("", root=tempfile.gettempdir(),
                                                             default=self._default()))

    def test_home_dir_is_refused(self):
        with self.assertRaises(paths.PathEscapeError):
            paths.guard_recursive_delete_target(os.path.expanduser("~"),
                                                root=tempfile.gettempdir(),
                                                default=self._default())

    def test_repo_root_and_its_parent_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = os.path.join(tmp, "repo")
            os.makedirs(repo)
            for bad in (repo, tmp):          # 仓库根 + 仓库根的上级
                with self.assertRaises(paths.PathEscapeError, msg=bad):
                    paths.guard_recursive_delete_target(bad, root=repo,
                                                        default=self._default())

    def test_system_temp_dir_itself_is_refused(self):
        with self.assertRaises(paths.PathEscapeError):
            paths.guard_recursive_delete_target(tempfile.gettempdir(),
                                                root=tempfile.gettempdir(),
                                                default=self._default())

    def test_filesystem_root_is_refused(self):
        with self.assertRaises(paths.PathEscapeError):
            paths.guard_recursive_delete_target(os.path.abspath(os.sep),
                                                root=tempfile.gettempdir(),
                                                default=self._default())

    def test_dedicated_scratch_dir_is_accepted(self):
        safe = os.path.join(tempfile.gettempdir(), "nf_e2e_guard_ok")
        self.assertEqual(os.path.realpath(safe),
                         paths.guard_recursive_delete_target(safe,
                                                             root=tempfile.gettempdir(),
                                                             default=self._default()))

    def test_refusal_message_carries_fix_guidance(self):
        try:
            paths.guard_recursive_delete_target(os.path.expanduser("~"),
                                                root=tempfile.gettempdir(),
                                                default=self._default(),
                                                label="NF_TEST_HOME")
        except paths.PathEscapeError as exc:
            self.assertIn("修复指引", str(exc))
            self.assertIn("NF_TEST_HOME", str(exc))
        else:
            self.fail("应抛 PathEscapeError")


class AssetLedgerDelegationTest(unittest.TestCase):
    """资产台账的逃逸判据须与 paths 同源（单一真相源）。"""

    def test_asset_ledger_rejects_escape_via_shared_primitive(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(al.AssetLedgerError):
                al.add_asset(root, "../evil.md", "K", source="s")
            with self.assertRaises(al.AssetLedgerError):
                al.add_asset(root, os.path.join(root, "abs.md"), "K", source="s")


class StoreHomeGuardTest(unittest.TestCase):
    """F-11：NF_HOME（--store / NARRATIVE_FORGE_HOME）不得指向灾难性落点。

    Store 会在 home 下建 modules/assets/presets/cache，且 remove_module 会做递归删除——
    落点指错就会把 `~/modules` 之类建到不该在的地方。
    """

    def test_safe_temp_home_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = os.path.join(tmp, "nf_store")
            s = Store(home=home)
            self.assertTrue(s.modules_root.is_dir())

    def test_catastrophic_homes_are_refused(self):
        for bad in (os.path.expanduser("~"), os.path.abspath(os.sep),
                    tempfile.gettempdir()):
            with self.assertRaises(paths.PathEscapeError, msg=bad):
                Store(home=bad)

    def test_env_var_home_is_guarded_too(self):
        """环境变量路径与 --store 同等对待（两者都会成为 Store.home）。"""
        old = os.environ.get("NARRATIVE_FORGE_HOME")
        try:
            os.environ["NARRATIVE_FORGE_HOME"] = os.path.expanduser("~")
            with self.assertRaises(paths.PathEscapeError):
                Store()
        finally:
            if old is None:
                os.environ.pop("NARRATIVE_FORGE_HOME", None)
            else:
                os.environ["NARRATIVE_FORGE_HOME"] = old


if __name__ == "__main__":
    unittest.main()
