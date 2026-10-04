#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仓库件判据（`core.paths.walk_repo_paths` / `ignored_paths`）单测。

为什么（2026-10-03 实证）：npm 一键包把受跟踪文件暂存成 `packaging/npm/payload/`（已 gitignore），
而各扫描面此前各持一份硬编码排除表、且**只看文件系统不看 `.gitignore`** ⇒ 同一份正文以第二份
身份进面，CoT 泄漏 / 文档路径可达 / 编码卫生三处同时假红。本判据把「什么算仓库件」钉住：
真仓零生成物在面 + 变异自证（临时 git 仓里被忽略的子树必须不在面，未忽略件必须在场）。
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import repo_face as paths  # noqa: E402


def _git(args, cwd):
    exe = shutil.which("git")
    if not exe:
        return None
    return subprocess.run([exe] + args, cwd=str(cwd), capture_output=True, text=True)


class RepoFaceGitAbsenceTest(unittest.TestCase):
    """git 不在场 / 调用失败 → 空集（`ignored_paths` 的文档承诺）。

    为什么用 mock：这两种情形**无法由文件系统夹具造出**（本机有 git，OSError 也只是偶发），
    而仓库既有做法正是用 `mock.patch.object(..., side_effect=...)` 触发错误分支（见 `test_atomic_write`）。
    判据做成**有区分度**的：先断言夹具本身能得到非空集，再断言降级路径必须给空集。
    """

    def _git_repo_with_ignored(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        if _git(["init", "-q"], root) is None:
            self.skipTest("无 git")
        (root / ".gitignore").write_text("gen/\n", encoding="utf-8")
        (root / "gen").mkdir()
        (root / "gen" / "x.md").write_text("x\n", encoding="utf-8")
        return root

    def test_git_absent_or_failing_falls_back_to_empty_set(self):
        from unittest import mock
        root = self._git_repo_with_ignored()
        self.assertTrue(paths.ignored_paths(str(root)),
                        "前提不成立：夹具里就应有被忽略路径（否则下面的断言不具区分度）")
        with mock.patch.object(paths, "_git_executable", return_value=""):
            self.assertEqual(set(), paths.ignored_paths(str(root)), "git 不在场应降级为空集")
        with mock.patch.object(paths.subprocess, "run", side_effect=OSError("boom")):
            self.assertEqual(set(), paths.ignored_paths(str(root)), "git 调用失败应降级为空集")


class RepoFacePredicateTest(unittest.TestCase):
    """纯函数面：前缀边界（子路径算、同前缀异名不算）。"""

    def test_is_ignored_is_prefix_bounded(self):
        ig = {"packaging/npm/payload", ".rivet"}
        self.assertTrue(paths.is_ignored("packaging/npm/payload", ig))
        self.assertTrue(paths.is_ignored("packaging/npm/payload/README.md", ig))
        self.assertTrue(paths.is_ignored(".rivet/scratch/x.py", ig))
        self.assertFalse(paths.is_ignored("packaging/npm/payloads/x.md", ig),
                         "同前缀但不同目录被误杀")
        self.assertFalse(paths.is_ignored("packaging/npm/lib/paths.mjs", ig))
        self.assertFalse(paths.is_ignored("", ig))

    def test_backslash_and_trailing_slash_are_normalized(self):
        ig = {"packaging/npm/payload"}
        self.assertTrue(paths.is_ignored("packaging\\npm\\payload\\a.md", ig))
        self.assertTrue(paths.is_ignored("/packaging/npm/payload/", ig))

    def test_static_skip_dir_names_cover_vcs_and_caches(self):
        for name in (".git", ".rivet", "__pycache__", ".ruff_cache", "node_modules"):
            self.assertIn(name, paths.SKIP_DIR_NAMES)


#: 已知的**全仓文本面**（必须走 `core.repo_face.walk_repo_paths`；本表只许缩小，新增面须登记）。
#: 依据（2026-10-03 实证）：这些面此前各持一份硬编码排除表且不看 `.gitignore`，npm 暂存副本
#: 一落树就让其中三处同时假红——收口只有一次是不够的，得让它**不能再长回去**。
ROOT_WIDE_FACES = {
    "desktop/src/core/text_hygiene.py": "编码卫生（check33）",
    "desktop/tests/test_cot_exposure.py": "思维链/对话转写泄漏面",
    "desktop/tests/test_doc_reachability.py": "在场文档路径/子命令可达面",
    "desktop/tests/test_leak_surface.py": "公开面泄漏（机器路径/凭据形状）",
    "desktop/tests/test_mcp_write_freedom.py": "MCP 写自由面（整树指纹）",
    "desktop/tests/test_launcher.py": "启动器 .cmd 纯 ASCII 静态规则",
    "desktop/tests/test_conformance_scan.py": "全仓 YAML/围栏文本块解析一致面",
}


class RootWideFacePolicyTest(unittest.TestCase):
    """**单一真相的常驻面**：全仓文本面只许经由 `repo_face` 取件（不许再自持排除表）。"""

    def test_registered_faces_use_the_shared_walker(self):
        missing = []
        for rel in sorted(ROOT_WIDE_FACES):
            text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
            if "repo_face" not in text:
                missing.append(rel)
        self.assertEqual([], missing,
                         "全仓文本面必须走 core.repo_face.walk_repo_paths"
                         "（否则生成物会以第二份正文的身份进面）")

    def test_registry_is_not_stale(self):
        for rel, why in sorted(ROOT_WIDE_FACES.items()):
            self.assertTrue((ROOT / rel).is_file(), "登记的面已不存在（%s）：%s" % (why, rel))


class RealRepoFaceTest(unittest.TestCase):
    """真仓：生成物不在面，且面没塌缩。"""

    def test_generated_payload_stays_out_of_scan_face(self):
        rels = {p.relative_to(ROOT).as_posix() for p in paths.walk_repo_paths(str(ROOT))}
        self.assertGreater(len(rels), 1000, "仓库件面塌缩（判定可能已失效）")
        leaked = sorted(r for r in rels if r.startswith("packaging/npm/payload/"))
        self.assertEqual([], leaked,
                         "被 .gitignore 覆盖的暂存面进了扫描面（修复指引：扫描面须走 "
                         "core.paths.walk_repo_paths）")
        payload = ROOT / "packaging" / "npm" / "payload"
        if payload.is_dir():
            exe = shutil.which("git")
            if exe:
                probe = subprocess.run([exe, "-C", str(ROOT), "check-ignore", "-q",
                                        "packaging/npm/payload"], capture_output=True)
                self.assertEqual(0, probe.returncode,
                                 "暂存面必须被 .gitignore 覆盖（否则它本就是仓库件）")

    def test_ignored_root_is_empty_outside_a_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(set(), paths.ignored_paths(tmp),
                             "非 git 目录不得猜出一份忽略面（闸门只做加法）")


class WalkRepoPathsMutationTest(unittest.TestCase):
    """变异自证：临时 git 仓里被忽略的子树必须被剪掉，未忽略件必须在场。"""

    def test_ignored_subtree_is_pruned_but_siblings_kept(self):
        if shutil.which("git") is None:
            self.skipTest("无 git，跳过仓库件面的变异自证")
        with tempfile.TemporaryDirectory() as tmp:
            r = _git(["init", "-q"], tmp)
            if r is None or r.returncode != 0:
                self.skipTest("git init 不可用")
            (Path(tmp) / ".gitignore").write_text("gen/\n", encoding="utf-8")
            (Path(tmp) / "gen").mkdir()
            (Path(tmp) / "gen" / "leak.md").write_text("x\n", encoding="utf-8")
            (Path(tmp) / "src").mkdir()
            (Path(tmp) / "src" / "ok.md").write_text("y\n", encoding="utf-8")
            rels = sorted(p.relative_to(tmp).as_posix() for p in paths.walk_repo_paths(tmp))
            self.assertIn("src/ok.md", rels, "未忽略件被误排除")
            self.assertNotIn("gen/leak.md", rels, "被忽略的子树没被剪掉（判据无判别力）")


if __name__ == "__main__":
    unittest.main()
