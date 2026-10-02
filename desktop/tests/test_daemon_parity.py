# -*- coding: utf-8 -*-
"""守护快路 ⇄ 直跑 的等价门禁（默认路径可证等价 + 拒跑面闭合）。

背景（2026-10-01 取证）：`scripts/nf.py` 的 `daemon` 帮助面写着「热进程与新起进程结果一致
（等价性由 test_daemon 逐命令比对）」，而 `test_daemon.DaemonProtocolTest` 当时只比 **5 条
argv**——默认路径（`scripts/nf` / `eval "$(nf daemon shell-init bash)"` → 守护快路）是
agent 密集重复调用真正走的那条，它的等价性此前只有抽样证据。更糟的是**拒跑表漏了别名与
常驻面**：`nf terminal`（`shell` 的 argparse 别名）与 `nf lsp`（常驻 stdio 服务）会进守护
在进程内执行，而守护把 stdin 设成空串 ⇒ 两条都**以 0 退出、零输出**；直跑一个进交互终端、
一个真起 LSP 服务。「同一条命令两条路径两种结果」，且失败形态是**静默假成功**。

本件把两件事变成常驻判据：

1. **集合闭合**：`daemon.REFUSED_COMMANDS` == `terminal.BLOCKED_IN_SHELL` ∪ {`daemon`}
   == 启动器快路排除表 == 启动器自动拉起排除表 == `nf daemon shell-init bash` 模板里的排除表；
   且**别名闭合**（`shell` 的别名 `terminal` 必须在表里）；且表里每个名字都是真命令。
2. **行为等价**：经**真守护**（socket）跑出的 (exit, stdout, stderr) 与**真子进程直跑**
   逐字节一致——覆盖全部命令面的 `--help`，以及可无参运行的 `--json` 机器面（agent 反复敲的
   那批；写盘面与需参面除外，写盘面由 `terminal.needs_confirm` 单一出处过滤）。

口径分工：长驻/自指面走 1 的拒跑断言（**设计上的分叉**，不是等价面）；其余走 2。
改一处不改另一处、或漏一个别名/常驻面，本件即红。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import daemon as dm          # noqa: E402
from core import terminal as term      # noqa: E402

NF = str(ROOT / "scripts" / "nf.py")
LAUNCHER = ROOT / "scripts" / "nf"
NF_SOURCE = ROOT / "scripts" / "nf.py"

_CACHE: dict = {}


def _inventory() -> list:
    """命令面清单（与 `test_cli_json_face` 同一真源：`nf shell --commands --json`，由 argparse 派生）。"""
    if "rows" not in _CACHE:
        p = subprocess.run([sys.executable, NF, "shell", "--commands", "--json"], cwd=str(ROOT),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        doc = json.loads(p.stdout)
        _CACHE["rows"] = doc.get("commands") or doc.get("rows") or []
    return _CACHE["rows"]


def _case_lists(text: str, must_contain: str = "daemon") -> list:
    """抓出 `case` 分支里「含 `must_contain` 的列举表」（`a|b|c)` 形态）→ 名字元组列表。"""
    out = []
    for m in re.finditer(r"(?m)^\s*([a-z][a-z|]*)\)", text):
        names = m.group(1).split("|")
        if must_contain in names:
            out.append(tuple(names))
    return out


def _shell_init_case(text: str) -> tuple:
    """从 `SHELL_INIT_BASH` 模板里抓 `daemon|…|"")` 那条排除表（`""` 是无参分支，不算名字）。"""
    m = re.search(r'(?m)^\s*([a-z][a-z|]*)\|""\)', text)
    assert m, "shell-init 模板里没找到长驻/自指排除表（判据可能已失效）"
    return tuple(m.group(1).split("|"))


class RefusalSetClosureTest(unittest.TestCase):
    """拒跑面的**集合闭合**：一个真源，四处投影，别名不得漏网。"""

    def test_refused_set_is_blocked_in_shell_plus_self_referential(self):
        expect = set(term.BLOCKED_IN_SHELL) | {"daemon"}
        self.assertEqual(expect, set(dm.REFUSED_COMMANDS),
                         "守护拒跑表与终端长驻表分叉（漏别名/常驻面即静默假成功）")

    def test_every_refused_name_is_a_real_command(self):
        top = {r["path"].split()[0] for r in _inventory()}
        missing = sorted(n for n in dm.REFUSED_COMMANDS if n not in top)
        self.assertEqual([], missing, "拒跑表里有不存在的命令（改名后没同步）：%s" % missing)

    def test_aliases_of_refused_commands_are_refused(self):
        src = NF_SOURCE.read_text(encoding="utf-8")
        aliases = {}
        for m in re.finditer(r'add_parser\(\s*"([a-z0-9-]+)"\s*,\s*aliases\s*=\s*\[([^\]]*)\]',
                             src):
            aliases[m.group(1)] = re.findall(r'"([a-z0-9-]+)"', m.group(2))
        self.assertTrue(aliases, "没解析到任何 argparse 别名 —— 判据可能已失效")
        leaked = sorted(a for canon, al in aliases.items()
                        if canon in dm.REFUSED_COMMANDS
                        for a in al if a not in dm.REFUSED_COMMANDS)
        self.assertEqual([], leaked, "拒跑命令的别名漏网（`nf %s` 会被守护静默执行）" % leaked)

    def test_launcher_and_shell_init_agree_with_daemon(self):
        expect = set(dm.REFUSED_COMMANDS)
        lists = _case_lists(LAUNCHER.read_text(encoding="utf-8"))
        self.assertEqual(2, len(lists),
                         "启动器里应恰有两条含 daemon 的 case 表（快路 + 自动拉起）：%s" % (lists,))
        for names in lists:
            self.assertEqual(expect, set(names), "启动器排除表与守护拒跑表分叉：%s" % (names,))
        self.assertEqual(expect, set(_shell_init_case(dm.SHELL_INIT_BASH)),
                         "shell-init 模板排除表与守护拒跑表分叉")

    def test_windows_client_long_running_set_matches_daemon(self):
        """`scripts/nf_client.py` 的长驻/自指表必须与守护拒跑表逐项一致。

        客户端是**独立进程**（`python -S`，不 import 仓库模块，故不能直接引用常量）——
        表就是五个字符串，重复是必然的，靠本判据钉住一致性；漂了就红。
        """
        src = (ROOT / "scripts" / "nf_client.py").read_text(encoding="utf-8")
        m = re.search(r"LONG_RUNNING = \(([^)]*)\)", src)
        self.assertIsNotNone(m, "客户端里没找到 LONG_RUNNING 表（判据可能已失效）")
        names = tuple(re.findall(r'"([a-z-]+)"', m.group(1)))
        self.assertEqual(set(dm.REFUSED_COMMANDS), set(names),
                         "客户端长驻表与守护拒跑表分叉：%s" % (names,))

    def test_windows_launcher_wires_the_fast_path_with_fallback(self):
        """`scripts/nf.cmd` 必须真的调客户端、并认 111 回退（结构性——Windows 壳在 bash 门禁里跑不到）。"""
        cmd = (ROOT / "scripts" / "nf.cmd").read_text(encoding="utf-8")
        self.assertIn("nf_client.py", cmd, "Windows 启动器没接快路客户端")
        self.assertIn("-S", cmd, "快路客户端必须走解释器节食（-S）")
        self.assertIn("111", cmd, "Windows 启动器没认回退退出码 111")
        self.assertIn("nf.py", cmd, "Windows 启动器缺直跑回退")
        # 「探测式」启动在最前面会吃掉快路的全部收益：实测 `where python` 单次 ≈98 ms
        # （cmd 裸跑 15 ms / 带 where 113 ms），而整条快路才 ≈78 ms ⇒ 不许再放探测命令在前。
        # （注释行里提到这个词是允许的——注释里那句话正是解释「为什么没有它」。）
        live = "\n".join(ln for ln in cmd.splitlines() if not ln.strip().lower().startswith("rem"))
        self.assertNotIn("where ", live, "启动器又加了外部探测命令（≈98 ms，直接吃掉快路收益）")


class _DaemonFixture(unittest.TestCase):
    """共用夹具：隔离 `NF_HOME` + 起一个守护 + 钉死墙钟（`SOURCE_DATE_EPOCH`）。

    （夹具单列的理由：两个判据类都要它；此前 `ClientFastPathTest` 直接继承
    `DaemonParityTest`，于是把三条重判据又跑了一遍——套件平白多花 ~90 s。）
    """

    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="nf_parity_home_")
        cls._old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = cls.home
        # 墙钟面（`attest` 的 `issued_at`）按可复现惯例钉死：否则「跨秒的两次运行必然不同」
        # 会把等价/确定性判据变成偶发红（`core.attest.issue_stamp`）。
        cls._old_sde = os.environ.get("SOURCE_DATE_EPOCH")
        os.environ["SOURCE_DATE_EPOCH"] = "1700000000"
        cls._old_cwd = os.getcwd()
        os.chdir(ROOT)
        ok, msg = dm.start(ROOT, idle_timeout=600.0)
        assert ok, "守护启动失败：%s" % msg
        cls.doc = dm.read_state()
        assert cls.doc, "守护状态文件不可读"

    @classmethod
    def tearDownClass(cls):
        dm.stop()
        os.chdir(cls._old_cwd)
        if cls._old_home is None:
            os.environ.pop("NARRATIVE_FORGE_HOME", None)
        else:
            os.environ["NARRATIVE_FORGE_HOME"] = cls._old_home
        if cls._old_sde is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = cls._old_sde
        shutil.rmtree(cls.home, ignore_errors=True)

    def _daemon(self, argv, timeout: float = 120.0):
        return dm.run_request(self.doc, argv, cwd=str(ROOT), timeout=timeout)

    def _direct(self, argv, timeout: float = 300.0):
        # stdin 必须显式 DEVNULL：`nf terminal` 这类面会读 stdin，若随宿主（例如 git 的 pre-push
        # 钩子把 ref 列表喂进来）变形，逐字节比对就会红——2026-10-02 实测。
        r = subprocess.run([sys.executable, NF] + list(argv), cwd=str(ROOT),
                           capture_output=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout, r.stderr


class DaemonParityTest(_DaemonFixture):
    """**行为等价**：经真守护（socket）与真子进程直跑逐字节一致。"""

    def test_refused_commands_are_refused_with_guidance_and_daemon_survives(self):
        for name in dm.REFUSED_COMMANDS:
            code, out, err = self._daemon([name], timeout=30.0)
            self.assertEqual(2, code, "长驻/自指命令 %s 应被守护拒跑" % name)
            self.assertEqual(b"", out, "%s 被拒时不得回吐正文" % name)
            self.assertIn("修复指引", err.decode("utf-8", "replace"),
                          "%s 的拒跑消息必须带修复指引" % name)
            self.assertTrue(dm.ping(self.doc, timeout=5.0), "拒绝之后守护必须仍然活着")

    def test_every_command_help_is_byte_identical_through_daemon(self):
        bad, checked = [], 0
        for row in _inventory():
            path = row["path"]
            if path.split()[0] in dm.REFUSED_COMMANDS:
                continue
            argv = path.split() + ["--help"]
            direct = self._direct(argv)
            got = self._daemon(argv)
            if got == direct:
                checked += 1
            else:
                bad.append("%s：直跑 %s / 守护 %s"
                           % (path, (direct[0], len(direct[1]), len(direct[2])),
                              (got[0], len(got[1]), len(got[2]))))
        self.assertGreater(checked, 100, "命令面覆盖不足（%d）——判据形同虚设" % checked)
        self.assertEqual([], bad, "守护与直跑的 --help 面不一致：%s" % bad[:6])

    def test_machine_faces_are_byte_identical_through_daemon(self):
        bad, checked = [], 0
        for row in _inventory():
            if "--json" not in (row.get("flags") or []):
                continue
            path = row["path"]
            if path.split()[0] in dm.REFUSED_COMMANDS:
                continue
            argv = path.split() + ["--json"]
            if term.needs_confirm(argv):
                continue                    # 写盘面：会改仓库，另由各自的专件覆盖
            direct = self._direct(argv)
            if direct[0] == 2 and not direct[1].strip():
                continue                    # 需参面：无参形态跑不到（rc=2 且零输出）
            first = self._daemon(argv)
            # **再跑一次**：第二跑必是热路径（进程内记忆 / 响应缓存）。冷跑与热跑若换序
            # （`sort_keys` 往返那类缺陷），这里直接红——单跑一次是抓不到的。
            warm = self._daemon(argv)
            if first == warm == direct:
                checked += 1
            else:
                bad.append("%s：直跑 %s / 守护冷 %s / 守护热 %s"
                           % (path, (direct[0], len(direct[1]), len(direct[2])),
                              (first[0], len(first[1]), len(first[2])),
                              (warm[0], len(warm[1]), len(warm[2]))))
        self.assertGreater(checked, 30, "机器面覆盖不足（%d）——判据形同虚设" % checked)
        self.assertEqual([], bad, "守护与直跑的机器面不一致：%s" % bad[:6])


CLIENT = str(ROOT / "scripts" / "nf_client.py")


class ClientFastPathTest(_DaemonFixture):
    """`scripts/nf_client.py`（Windows 默认路径的毫秒级客户端）——等价 + 回退两条语义。

    为什么单列：`scripts/nf.cmd` 此前**没有**快路（用它的注释说：「cmd.exe 没有内建 socket，
    本包装器始终走 python 直跑」，实测 ≈358 ms/条），而同一条命令在 POSIX 侧只要 ≈132 ms——
    「稳态毫秒级」在 Windows 上是缺的。客户端是纯 stdlib（不 import 仓库模块，`python -S`
    只花 ~52 ms），但**它的正确性必须与守护/直跑同口径**：字节等价、以及「拿不到就回退」。
    """

    def _client(self, argv, env=None, timeout: float = 120.0):
        r = subprocess.run([sys.executable, "-S", CLIENT] + list(argv), cwd=str(ROOT),
                           capture_output=True, timeout=timeout,
                           env=env if env is not None else os.environ.copy())
        return r.returncode, r.stdout, r.stderr

    def test_client_is_byte_identical_to_direct(self):
        for argv in (["--version"], ["stats", "--check"], ["doctor", "--json"],
                     ["layers", "--json"], ["market", "--list"]):
            got = self._client(argv)
            want = self._direct(argv)
            self.assertEqual(want, got, "客户端与直跑不一致：%s" % argv)

    def test_client_hands_long_running_back_to_the_caller(self):
        """长驻/自指命令必须回退（111），不得被守护静默执行成「rc=0 零输出」。"""
        for argv in (["terminal"], ["lsp"], ["serve", "x.json"], ["daemon", "status"]):
            code, out, _err = self._client(argv)
            self.assertEqual(111, code, "%s 应回退直跑" % argv)
            self.assertEqual(b"", out, "%s 回退时不得先回吐半截输出" % argv)

    def test_client_falls_back_when_no_daemon_and_autostart_off(self):
        empty = tempfile.mkdtemp(prefix="nf_client_empty_")
        self.addCleanup(shutil.rmtree, empty, ignore_errors=True)
        env = dict(os.environ, NARRATIVE_FORGE_HOME=empty, NF_AUTOSTART="0")
        code, out, err = self._client(["--version"], env=env)
        self.assertEqual(111, code, "没有守护时必须回退（不改可用性）")
        self.assertEqual(b"", out)
        self.assertEqual(b"", err)
        self.assertFalse(os.path.exists(os.path.join(empty, "daemon.json")),
                         "NF_AUTOSTART=0 时不得拉起守护")

    def test_client_autostart_default_on_is_non_blocking(self):
        """默认路径开：没有守护时**非阻塞**后台拉起，本条命令照常回退（111）。"""
        home = tempfile.mkdtemp(prefix="nf_client_auto_")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        env = dict(os.environ, NARRATIVE_FORGE_HOME=home)
        env.pop("NF_AUTOSTART", None)
        code, out, _err = self._client(["--version"], env=env)
        self.assertEqual(111, code, "首条命令仍走回退（不等守护）")
        self.assertEqual(b"", out)
        marker = os.path.join(home, "daemon.starting")
        self.assertTrue(os.path.exists(marker), "默认开时必须记下拉起标记（连发命令防重复拉）")
        # 收尾：后台守护是**真起**的，必须停掉（否则留一个空转进程）
        old = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = home
        try:
            for _ in range(40):
                if os.path.exists(os.path.join(home, "daemon.json")):
                    break
                time.sleep(0.25)
            self.assertTrue(os.path.exists(os.path.join(home, "daemon.json")),
                            "后台拉起没落地（默认开这条口径就是假的）")
            # 收尾走**协议级 shutdown**，不调 `dm.stop()`：本进程的 `dm._CHILD` 指的是本类夹具
            # 那个守护，换过 NF_HOME 再调它会拿无关子进程去 wait（留下 GC 期的 ResourceWarning）。
            doc = dm.read_state()
            if doc:
                with socket.create_connection((dm.BIND_HOST, int(doc["port"])), timeout=5) as sock:
                    sock.sendall(json.dumps({"proto": dm.PROTO, "token": doc["token"],
                                             "op": "shutdown"}).encode("utf-8") + b"\n")
                    dm.read_framed(sock)
                for _ in range(40):
                    if not os.path.exists(os.path.join(home, "daemon.json")):
                        break
                    time.sleep(0.25)
        finally:
            if old is None:
                os.environ.pop("NARRATIVE_FORGE_HOME", None)
            else:
                os.environ["NARRATIVE_FORGE_HOME"] = old

    @unittest.skipUnless(os.name == "nt" and shutil.which("cmd"),
                         "Windows cmd 启动器只在 Windows 上真跑（跨平台那一半由结构性判据盯住）")
    def test_windows_cmd_launcher_is_byte_identical_to_direct(self):
        """真跑 `scripts\\nf.cmd`：快路（有守护）与回退（长驻命令）都必须与直跑逐字节一致。"""
        launcher = str(ROOT / "scripts" / "nf.cmd")

        def run_cmd(argv):
            r = subprocess.run(["cmd", "/c", launcher] + list(argv), cwd=str(ROOT),
                               capture_output=True, timeout=300, env=os.environ.copy(),
                               stdin=subprocess.DEVNULL)
            return r.returncode, r.stdout, r.stderr

        for argv in (["--version"], ["stats", "--check"], ["doctor", "--json"], ["terminal"]):
            self.assertEqual(self._direct(argv), run_cmd(argv),
                             "nf.cmd 与直跑不一致：%s" % argv)


def _render(pair) -> str:
    """把 `(issues, stats)` 渲染成**打印面真正会输出的那串**（键序按对象自身的顺序）。"""
    return json.dumps({"issues": pair[0], "stats": pair[1]}, ensure_ascii=False)


class CacheRoundTripByteEqualityTest(unittest.TestCase):
    """缓存往返**不得改变可见字节**：冷算那份与持久层命中那份必须逐字节一致。

    取证（2026-10-01）：`disk_cache.store` 落盘用 `sort_keys=True`，而未命中路径把内存里的
    值直接交回调用方 ⇒ `nf layers --json` 首跑按插入序、第二跑（命中）按字典序，实测
    sha `d265f466…` / `4acfa0a3…`；守护路径与直跑路径也随之分叉。修法是在两个派生缓存
    入口（`conformance_scan.scan` / `memo_pair`）统一过 `disk_cache.canonical`。

    本件**只清进程内记忆、保留落盘缓存**，逼出「冷算 ⇄ 持久命中」这一对——正是那次换序的
    两条路径；不修就红（变异自证见下）。
    """

    def _cold_then_hit(self, clear_memo, run):
        home = tempfile.mkdtemp(prefix="nf_memo_roundtrip_")
        old = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = home
        try:
            clear_memo()
            cold = run()
            self.assertTrue(list((Path(home) / "cache").glob("*/*.json")),
                            "冷跑没有落盘 —— 本判据只测到了内存，形同虚设")
            clear_memo()
            warm = run()
        finally:
            if old is None:
                os.environ.pop("NARRATIVE_FORGE_HOME", None)
            else:
                os.environ["NARRATIVE_FORGE_HOME"] = old
            shutil.rmtree(home, ignore_errors=True)
        return cold, warm

    def test_memo_pair_cold_and_persistent_hit_render_identically(self):
        from core import conformance_scan as csc
        from core import layer_model as lm
        cold, warm = self._cold_then_hit(lambda: csc._DERIVED_MEMO.clear(), lambda: lm.scan("."))
        self.assertEqual(_render(cold), _render(warm), "派生缓存往返改变了可见键序")

    def test_scan_cold_and_persistent_hit_render_identically(self):
        from core import conformance_scan as csc
        cold, warm = self._cold_then_hit(lambda: csc._SCAN_CACHE.clear(),
                                         lambda: csc.scan("."))
        self.assertEqual(json.dumps(cold, ensure_ascii=False), json.dumps(warm, ensure_ascii=False),
                         "扫描缓存往返改变了可见键序")


class AttestStampReproducibilityTest(unittest.TestCase):
    """`attest` 的时间戳可复现（`SOURCE_DATE_EPOCH`），否则机器面「两次运行逐字节一致」是假真。"""

    def test_issue_stamp_honors_source_date_epoch_and_explicit_now(self):
        from core import attest
        old = os.environ.get("SOURCE_DATE_EPOCH")
        os.environ["SOURCE_DATE_EPOCH"] = "1700000000"
        try:
            self.assertEqual("2023-11-14T22:13:20Z", attest.issue_stamp())
        finally:
            if old is None:
                os.environ.pop("SOURCE_DATE_EPOCH", None)
            else:
                os.environ["SOURCE_DATE_EPOCH"] = old
        self.assertRegex(attest.issue_stamp(), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual("2000-01-01T00:00:00Z",
                         attest.issue_stamp(datetime(2000, 1, 1, tzinfo=timezone.utc)))

    def test_attest_machine_face_is_byte_stable_when_pinned(self):
        home = tempfile.mkdtemp(prefix="nf_attest_pin_")
        env = dict(os.environ, NARRATIVE_FORGE_HOME=home, SOURCE_DATE_EPOCH="1700000000")
        try:
            outs = []
            for _ in range(2):
                r = subprocess.run([sys.executable, "-X", "utf8", NF, "attest", "--json"],
                                   cwd=str(ROOT), capture_output=True, env=env, timeout=300)
                outs.append(r.stdout)
        finally:
            shutil.rmtree(home, ignore_errors=True)
        self.assertTrue(outs[0].strip(), "attest --json 必须产出内容（否则判据空转）")
        self.assertEqual(outs[0], outs[1], "钉死时间戳后仍两次不同（缓存往返或时间戳没接上）")
