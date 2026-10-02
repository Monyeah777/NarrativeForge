# -*- coding: utf-8 -*-
"""公开面泄漏门禁：仓库文本产物不得含**机器绝对路径**或**凭据形状**。

依据（本轮取证）：金标注据 15 件、`protocol/instruction_evidence.json` 2 条输出摘要、
`results/interop-thirdparty-status.md`、`engine/dotnet/tools/nf-dotnet/Program.cs` 曾把
作者机器路径（`C:\\Users\\<user>\\...`）写进公开仓——既是隐私泄漏，也让证据换台机器就不可解释
（`engine/dotnet/probes/_paths.py` 开篇即写明「可移植，无作者机器路径」，这些是它的漏网面）。

口径：扫全部文本产物；**探针源码**（`engine/dotnet/probes/*.py`）豁免——那里允许出现
合成负例路径（如 `C:\\Users\\x`）用于测试拦截本身，非真实机器路径。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SKIP_PARTS = {".git", ".rivet", "__pycache__", ".ruff_cache", ".mypy_cache", "node_modules"}
EXTS = (".md", ".json", ".yaml", ".yml", ".txt", ".csv", ".cs", ".cmd", ".sh", ".py")
#: 合成负例路径允许存在的仪器源码（测试「拦截本身」，非真实机器路径）
EXEMPT_PREFIX = "engine/dotnet/probes/"

MACHINE_PATH = re.compile(r"C:[\\/]Users[\\/]|/Users/[A-Za-z]|/home/[a-z]")
#: 探针把**绝对快照路径**写进金标的老写法（写侧口径：须走 `_paths.portable`）
ABS_SNAPSHOT_WRITE = re.compile(r'"snapshot"\s*:\s*str\(')
SECRET_SHAPE = re.compile(
    r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_-]{20,}"
    r"|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY")


def _public_files() -> list:
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in SKIP_PARTS for part in p.parts):
            continue
        if p.suffix not in EXTS:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(EXEMPT_PREFIX) and p.suffix == ".py":
            continue
        out.append(rel)
    return sorted(out)


class PublicSurfaceLeakTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = _public_files()

    def test_scan_face_is_not_collapsed(self):
        self.assertGreater(len(self.files), 1500, "公开面文件集塌缩（判定可能已失效）")

    def test_no_machine_paths(self):
        bad = [rel for rel in self.files
               if MACHINE_PATH.search((ROOT / rel).read_text(encoding="utf-8", errors="replace"))]
        self.assertEqual([], bad, "公开产物含机器绝对路径（作者隐私 + 证据不可移植）")

    def test_no_secret_shapes(self):
        bad = [rel for rel in self.files
               if SECRET_SHAPE.search((ROOT / rel).read_text(encoding="utf-8", errors="replace"))]
        self.assertEqual([], bad, "公开产物含凭据形状字符串")

    def test_patterns_have_catch_power(self):
        """变异自证：合成样本必须被两条判据抓到（否则门禁是空转）。"""
        # 样本**拼接构造**：门禁文件自身不落真实形态串，否则会自己命中自己。
        win_user = "C:" + "\\Users" + "\\" + "alice" + "\\repo"
        posix_user = "/Users/" + "alice/repo"
        self.assertTrue(MACHINE_PATH.search("-Root " + win_user))
        self.assertTrue(MACHINE_PATH.search(posix_user))
        self.assertTrue(SECRET_SHAPE.search("ghp_" + "A" * 24))
        self.assertIsNone(MACHINE_PATH.search("-Root " + "<仓库根>（如 . 或你的检出目录）"))

    def test_engine_fixture_writers_use_portable_labels(self):
        """**写侧**判据：探针写金标时必须走 `_paths.portable`（否则机器路径又进公开仓）。

        为什么补这条：`test_no_machine_paths` 只挡**结果**——若有人把某条探针改回
        `str(snap)`，要等下一次重生成夹具才发现（可能已提交）。本判据把口径钉在写侧。
        """
        probes = sorted((ROOT / "engine" / "dotnet" / "probes").glob("*.py"))
        self.assertTrue(probes, "探针目录不在场（判定可能已失效）")
        bad = [p.name for p in probes
               if ABS_SNAPSHOT_WRITE.search(p.read_text(encoding="utf-8", errors="replace"))]
        self.assertEqual([], bad, "这些探针把绝对快照路径写进金标：%s" % bad)


if __name__ == "__main__":
    unittest.main()
