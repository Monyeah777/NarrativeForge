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


@unittest.skipUnless(BASH, "启动器是 POSIX sh 脚本，需 bash 执行快路")
class AutostartTest(unittest.TestCase):
    """`NF_AUTOSTART` 开关（**默认关**）：守护不在时先拉起带 `--watch` 的守护，再服务这条命令。

    依据：毫秒级链路的最后一段是「守护得在跑」——而守护默认 1 小时空闲自退，忘了重启就跌回秒级。
    实测账（本机）：首条命令要付 **~0.65 s 起守护**（含机制自检）+ 本身计算（**比直跑慢**），
    **从第二条起才 10 ms**——所以这是个"赌重复调用"的开关，**默认关**，是否默认化由作者裁决。
    与 `nf daemon exec` 的语义一致（那条默认就会拉起，且可 `--no-start` 拒绝）。
    """

    def _home(self):
        home = tempfile.mkdtemp(prefix="nf_autostart_")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        return home

    def _run(self, home, *argv, autostart=None):
        env = dict(os.environ)
        env["NARRATIVE_FORGE_HOME"] = home
        env.pop("NF_AUTOSTART", None)
        if autostart is not None:
            env["NF_AUTOSTART"] = autostart
        return subprocess.run([BASH, "scripts/nf", *argv], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=300)

    def _stop(self, home):
        env = dict(os.environ)
        env["NARRATIVE_FORGE_HOME"] = home
        subprocess.run([sys.executable, "scripts/nf.py", "daemon", "stop"], cwd=ROOT,
                       env=env, capture_output=True, timeout=120)

    def test_disabled_by_default_and_for_falsey_values(self):
        for value in (None, "0", "false", "no", "off"):
            home = self._home()
            self.addCleanup(self._stop, home)
            p = self._run(home, "--version", autostart=value)
            self.assertEqual(0, p.returncode, p.stderr or p.stdout)
            self.assertIn("nf ", p.stdout)
            self.assertFalse(os.path.exists(os.path.join(home, "daemon.json")),
                             "NF_AUTOSTART=%r 不得拉起守护" % value)

    def test_enabled_starts_the_daemon_then_serves(self):
        home = self._home()
        self.addCleanup(self._stop, home)
        p = self._run(home, "--version", autostart="1")
        self.assertEqual(0, p.returncode, p.stderr or p.stdout)
        self.assertIn("nf ", p.stdout)
        self.assertTrue(os.path.exists(os.path.join(home, "daemon.json")),
                        "设了开关就必须真把守护拉起来（否则毫秒级拿不到）")
        q = self._run(home, "--version", autostart="1")
        self.assertEqual(0, q.returncode)
        self.assertEqual(p.stdout, q.stdout, "拉起前后输出必须一致（只加速不改语义）")

    def test_long_running_and_self_referential_commands_do_not_autostart(self):
        """`daemon` / `shell` / `serve` 本来就不走守护——不该为它们把守护拉起来。"""
        for argv in (["daemon", "status"],):
            home = self._home()
            self.addCleanup(self._stop, home)
            p = self._run(home, *argv, autostart="1")
            self.assertIn(p.returncode, (0, 1), p.stderr or p.stdout)
            self.assertFalse(os.path.exists(os.path.join(home, "daemon.json")),
                             "`nf %s` 不该触发自动拉起" % " ".join(argv))


@unittest.skipUnless(BASH, "启动器是 POSIX sh 脚本，需 bash 执行快路")
class InterpreterLaunchBudgetTest(unittest.TestCase):
    """启动器的**解释器启动次数**（确定性判据——本机计时噪声 ±10%，计时判据撑不住）。

    依据（2026-09-29 实测，min of 5）：`bash scripts/nf --version` 比 `python scripts/nf.py
    --version` 多花 **164 ms**，三笔固定成本都按**每条命令**计——外部 `dirname` + 子 shell ≈58 ms、
    一次命令替换（Store 桩路径判据）≈30 ms、「真起一次解释器」的终判 ≈60 ms（真撞上 Store 桩要
    ~300 ms）。修法：参数展开替 `dirname`、按平台择一（Windows 先要 `python`）、终判按「解释器名 +
    平台」**缓存**，并把解释器选择整个挪到快路**之后**。

    判据用 PATH 上的 shim（先记一笔再转发真解释器）**数启动次数**：快路命中必须 **0 次**；回退
    **稳态恰好 1 次**（修前每条 2 次）；回退首条（缓存冷）2 次＝一次确诊 + 一次真跑，属设计。
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="nf_interp_")
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.addCleanup(self._stop)

    def _stop(self):
        subprocess.run([sys.executable, "scripts/nf.py", "daemon", "stop"], cwd=ROOT,
                       env={**os.environ, "NARRATIVE_FORGE_HOME": self.home},
                       capture_output=True, timeout=120)

    def _real_py(self):
        """真解释器（MSYS 形态路径）——由 bash 自己解析，避免 Windows 路径形态的坑。"""
        r = subprocess.run([BASH, "-c", "command -v python || command -v python3"],
                           capture_output=True, text=True, encoding="utf-8")
        return r.stdout.strip()

    def _shim_env(self, stub_python3=False):
        """PATH 最前挂一个只放 shim 的目录：`python`/`python3` 先记一笔再 `exec` 真解释器。

        `stub_python3=True` 时 `python3` 换成**永远 rc=49、零输出**的桩——这是 Microsoft Store
        应用别名桩实测的形状（起一次 ~300 ms 且跑不了仓库脚本），用来钉住「选错解释器」那类缺陷。
        """
        bin_dir = os.path.join(self.home, "shim")
        os.makedirs(bin_dir, exist_ok=True)
        log = os.path.join(self.home, "starts.log")
        head = ('#!/bin/sh\n'
                'printf "%s\\n" "$0" >> "' + log.replace("\\", "/") + '"\n')
        body = head + 'exec "' + self._real_py() + '" "$@"\n'
        stub = head + "exit 49\n"
        for name in ("python", "python3"):
            path = os.path.join(bin_dir, name)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(stub if (stub_python3 and name == "python3") else body)
            os.chmod(path, 0o755)
        env = dict(os.environ)
        env["NARRATIVE_FORGE_HOME"] = self.home
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
        env.pop("NF_AUTOSTART", None)
        return env, log

    @staticmethod
    def _starts(log):
        if not os.path.exists(log):
            return 0
        with open(log, encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())

    def _run(self, *argv, env, timeout=300):
        return subprocess.run([BASH, "scripts/nf", *argv], cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)

    def test_fast_path_starts_no_interpreter(self):
        """守护在跑时启动器**一次解释器都不许起**——起一次就是 50–300 ms 的固定成本。"""
        start = subprocess.run([sys.executable, "scripts/nf.py", "daemon", "start", "--watch"],
                               cwd=ROOT,
                               env={**os.environ, "NARRATIVE_FORGE_HOME": self.home},
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=300)
        self.assertEqual(0, start.returncode, start.stderr or start.stdout)
        env, log = self._shim_env()
        p = self._run("stats", "--check", env=env)
        self.assertEqual(0, p.returncode, p.stderr or p.stdout)
        self.assertEqual(0, self._starts(log),
                         "快路命中却起了解释器：选解释器（含终判）的代码跑到快路前面去了")

    def test_fallback_starts_one_interpreter_in_steady_state(self):
        """回退稳态**恰好一次**解释器启动（修前每条两次：探针 + 真跑）。"""
        env, log = self._shim_env()                 # 没有守护状态文件 → 必走回退
        first = self._run("--version", env=env)
        self.assertEqual(0, first.returncode,
                         "回退必须可用（rc=127 + 零输出 = 回退被 set -e 杀了）\n%s"
                         % (first.stderr or first.stdout))
        self.assertIn("nf ", first.stdout)
        self.assertEqual(2, self._starts(log),
                         "缓存冷的那一条＝一次确诊 + 一次真跑（设计如此，不是回归）")
        for i in (2, 3):
            if os.path.exists(log):
                os.remove(log)                      # 每轮清零：数的是**这一条命令**起了几次
            p = self._run("--version", env=env)
            self.assertEqual(0, p.returncode, p.stderr or p.stdout)
            self.assertEqual(first.stdout, p.stdout, "只加速不改语义")
            self.assertEqual(1, self._starts(log),
                             "第 %d 次回退仍应恰好一次解释器启动（终判必须走缓存）" % i)

    def test_store_stub_like_python3_is_avoided(self):
        """`python3` 是「存在但跑不了」的桩时，启动器必须**仍可用**（Windows Store 桩的真实形状）。

        这是启动器最贵的那条缺陷（2026-09 实测：`nf <任何命令>` 变 rc=49 / 零输出）。修法有两道：
        路径判据（Windows 上先要 `python`）与**真起一次**的终判。这里把两道都逼到墙角——`python3`
        桩永远 rc=49 且零输出，只剩「换 `python`」这一条活路。
        """
        env, _log = self._shim_env(stub_python3=True)
        p = self._run("--version", env=env)
        self.assertEqual(0, p.returncode,
                         "选了跑不了的 python3 就必须换一个（不得 rc=49 + 零输出）\n%s"
                         % (p.stderr or p.stdout))
        self.assertIn("nf ", p.stdout)


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
