#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`scripts/nf` 启动器的**回退路径**判据：没有守护时必须静默回退 python 直跑。

依据（2026-09 实测缺陷，两处叠加）：① `daemon_try` 用 `return 127` 表示「快路不接手」，
而它在 `if` 的**分支体**里（不是条件位），`set -e` 下非零返回会**直接终止脚本**——
后面那行 `exec python 直跑` 永远到不了；后果是**守护没在跑时 `nf <任何命令>` 一律 rc=127 且
零输出**（连 `nf shell` / `nf serve` 这种本来就必须回退的也一样）。② `NF_PY=python3` 在
Windows 上可能解析到 Microsoft Store 的应用别名桩（`…/WindowsApps/python3`），它跑不了仓库
脚本。两处修好后，本判据把「回退可用」钉住——此前的测试只覆盖了「守护开着」的快路。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[2])
if str(Path(ROOT) / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(Path(ROOT) / "desktop" / "src"))
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "本环境没有 bash（启动器是 POSIX sh 脚本，需 bash 执行快路）")
class LauncherFallbackTest(unittest.TestCase):
    """隔离 NF_HOME（没有守护状态文件）跑启动器：必须落到 python 直跑，而不是静默 127。"""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="nf_launcher_")
        self.env = dict(os.environ)
        self.env["NARRATIVE_FORGE_HOME"] = self.home

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def _run(self, *argv, timeout=180):
        return subprocess.run([BASH, "scripts/nf", *argv], cwd=ROOT, env=self.env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)

    def test_fallback_runs_without_daemon(self):
        p = self._run("--version")
        self.assertEqual(0, p.returncode,
                         "回退路径必须可用（rc=127 + 零输出 = set -e 把回退杀了）\n%s"
                         % (p.stderr or p.stdout))
        self.assertIn("nf ", p.stdout, "回退路径必须产出正常输出")

    def test_refused_commands_also_fall_back(self):
        """`daemon` / `shell` / `serve` 快路一律不接手（与守护拒绝面一致）——它们**更**依赖回退。"""
        p = self._run("daemon", "status")
        self.assertIn(p.returncode, (0, 1), "daemon status 有输出即可（未运行 = 1）\n%s" % p.stderr)
        self.assertIn("守护", p.stdout, "daemon status 应打到人读输出")

    def test_real_command_falls_back_and_runs(self):
        p = self._run("toolface", "--json")
        self.assertEqual(0, p.returncode, "真实命令经回退也必须跑通\n%s" % p.stderr)
        self.assertIn("{", p.stdout)


@unittest.skipUnless(BASH, "需 bash 跑 POSIX 启动器形态")
class DocumentedCommandsTest(unittest.TestCase):
    """**文档里写出来的终端命令必须真能跑**——门禁只有「文档提及 ↔ CLI 注册表」的静态对照
    （`prose_lint.command_face`），从没执行过它们。

    依据：连续三处缺陷都发生在**文档承诺的入口/形态**上（POSIX 启动器回退 / shell-init 函数回退 /
    `nf.cmd` 编码），它们的共同盲点是——判据只验证「能解析 / 语法合法 / 在册」，不验证「能跑」。
    本判据把 `docs/terminal.md` 的 ```sh 代码块命令逐条执行（只读形态；隔离 `NF_HOME`；
    结束时确保不留下守护），并**自证有效**（真跑到的条数不得少于阈值，否则这条判据是空的）。
    """

    #: 会落盘 / 需要外部文件的形态：不在这里执行（它们是写路径，另有各命令自己的判据）
    WRITE_TOKENS = ("--write", "--out", "--save", "--file", ">", "|", "--fix", "--yes")
    MIN_RUNS = 5

    def _documented(self):
        import re
        text = (Path(ROOT) / "docs" / "terminal.md").read_text(encoding="utf-8")
        cmds = []
        for block in re.findall(r"```sh\n(.*?)```", text, re.S):
            for line in block.splitlines():
                line = line.split("  #")[0].strip()
                if line and not line.startswith("#") and line.startswith(
                        ("nf ", "python scripts/nf.py ", "python3 scripts/nf.py ")):
                    cmds.append(line)
        return list(dict.fromkeys(cmds))              # 去重保序

    def test_documented_commands_actually_run(self):
        import shlex
        cmds = self._documented()
        self.assertGreaterEqual(len(cmds), self.MIN_RUNS,
                                "文档里可执行命令太少，判据形同虚设：%s" % cmds)
        home = tempfile.mkdtemp(prefix="nf_doccmd_")
        env = dict(os.environ, NARRATIVE_FORGE_HOME=home)
        ran, failures, skipped = 0, [], []
        try:
            for cmd in cmds:
                if any(tok in cmd for tok in self.WRITE_TOKENS):
                    skipped.append(cmd)
                    continue
                parts = shlex.split(cmd)
                argv = ([BASH, "scripts/nf"] + parts[1:]) if parts[0] == "nf" \
                    else ([sys.executable, "scripts/nf.py"] + parts[2:])
                try:
                    p = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True,
                                       text=True, encoding="utf-8", errors="replace",
                                       timeout=300, stdin=subprocess.DEVNULL)
                    rc = p.returncode
                except subprocess.TimeoutExpired:
                    rc = "TIMEOUT"
                ran += 1
                if rc != 0:
                    failures.append("%s → rc=%s" % (cmd, rc))
        finally:
            # 收干净：文档里的示例会起守护，别把临时 NF_HOME 的守护留下
            old = os.environ.get("NARRATIVE_FORGE_HOME")
            try:
                from core import daemon as dm
                os.environ["NARRATIVE_FORGE_HOME"] = home
                dm.stop()
            except Exception:                      # noqa: BLE001 - 收尾失败不影响判定
                pass
            finally:
                if old is None:
                    os.environ.pop("NARRATIVE_FORGE_HOME", None)
                else:
                    os.environ["NARRATIVE_FORGE_HOME"] = old
            shutil.rmtree(home, ignore_errors=True)
        self.assertGreaterEqual(ran, self.MIN_RUNS,
                                "真跑到的条数不足（跳过 %d 条）：判据自身要有效" % len(skipped))
        self.assertEqual([], failures, "文档承诺的命令跑不通：%s" % failures)


class WindowsCmdLauncherTest(unittest.TestCase):
    """Windows 原生启动器 `scripts/nf.cmd`：**静态规则**（必须纯 ASCII）+ 行为级（能跑）。

    依据（2026-09 实测缺陷）：该文件曾是 UTF-8 无 BOM + 中文注释，而 **cmd.exe 按 OEM 码页读
    .cmd 源码**——注释被误解码后会**裂出可执行垃圾**，于是 `scripts\\nf.cmd <任何参数>` 在
    python 之前就挂了（实测 rc=255，报错 `'…' is not recognized as an internal or external
    command`）。这条规则**静态可判**、且与平台无关，所以常驻在单测里；行为级那条只在 Windows 跑。
    （同一条教训仓库里早有先例：`.github/requirements-ci.txt` 明写 "deliberately ASCII-only"。）
    """

    def test_windows_launchers_are_ascii_only(self):
        offenders = []
        for path in Path(ROOT).rglob("*"):
            if path.suffix.lower() not in (".cmd", ".bat"):
                continue
            if any(part in (".git", ".rivet", "__pycache__") for part in path.parts):
                continue
            raw = path.read_bytes()
            if any(b > 0x7F for b in raw):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders,
                         "cmd/bat 源码必须纯 ASCII——cmd.exe 按 OEM 码页读它，非 ASCII 注释会裂成"
                         "可执行垃圾（实测导致启动器完全不可用）")

    @unittest.skipUnless(os.name == "nt", "仅 Windows 有 cmd.exe")
    def test_nf_cmd_actually_runs(self):
        cmd = os.environ.get("COMSPEC") or shutil.which("cmd")
        if not cmd:
            self.skipTest("找不到 cmd.exe")
        p = subprocess.run([cmd, "/c", r"scripts\nf.cmd --version"], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        self.assertEqual(0, p.returncode,
                         "nf.cmd 必须能跑（非 ASCII 注释会让它在 python 之前就挂）\n%s"
                         % (p.stdout + p.stderr))
        self.assertIn("nf ", p.stdout)


if __name__ == "__main__":
    unittest.main()
