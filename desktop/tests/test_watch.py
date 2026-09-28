#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""目录监听 + 守护响应缓存单测（毫秒级执行层的「**不重算**」判据）。

分层：
- 响应缓存的准入/失效逻辑**与平台无关**（注入假监听件测），任何平台都跑；
- `watch.DirWatcher` 本身只在有实现的本平台跑（本波仅 Windows），其余平台跳过并检查降级面。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
BASH = shutil.which("bash")            # 两条 shell 客户端都是 POSIX sh/bash 形态

from core import daemon as dm  # noqa: E402
from core import conformance_scan as csc  # noqa: E402
from core import watch  # noqa: E402


def _wait_generation(w, before: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if w.generation > before:
            return True
        time.sleep(0.02)
    return False


class _FakeWatcher:
    """假监听件：单测据此判「命中 / 未命中 / 失效」，不受平台与真实通知时序影响。"""

    def __init__(self, generation: int = 1, healthy: bool = True) -> None:
        self.generation = generation
        self.healthy = healthy
        self.overflowed = False


class ResponseCacheTest(unittest.TestCase):
    """响应缓存：准入表 + 「同代际命中 / 代际一变重算」+ 不可用时 fail-closed。"""

    def setUp(self):
        self._old = dm._WATCHER
        dm.reset_response_cache()
        for k in dm._CACHE_STATS:
            dm._CACHE_STATS[k] = 0

    def tearDown(self):
        dm._WATCHER = self._old
        dm.reset_response_cache()

    def test_cacheable_truth_table(self):
        """准入表：纯读形态 → 可缓存；**写子命令 / 写盘开关 / 表外命令** → 一律不缓存。

        表项是 argv **前缀**，所以「同一顶层命令的读子命令进表、写子命令不进表」必须逐条钉住
        （`module` / `decisions` / `patterns` 三个命令都同时有读写形态）。
        """
        yes = (["--version"], ["score"], ["score", "--json"], ["conformance"],
               ["layers"], ["stats", "--check"], ["stats", "--json"], ["doctor"],
               ["interop", "--check"], ["toolface", "--json"], ["assertions"],
               ["cognition", "glossary"], ["patterns", "ls"], ["patterns", "verify"],
               ["module", "ls"], ["module", "status", "M00"], ["module", "verify"],
               ["decisions", "verify"], ["decisions", "show", "ADR-0004"])
        no = ([], ["conformance", "--write"], ["score", "--write-baseline"],
              ["stats", "--write"], ["serve"], ["layers", "--out", "x.json"],
              ["layers", "--fix"], ["conformance", "--write", "--json"],
              # 写子命令：顶层名相同也必须挡住
              ["module", "deprecate", "M10"], ["module", "restore", "M10"],
              ["module", "signature", "--write"], ["module", "contract", "--write"],
              ["decisions", "reindex"], ["patterns", "reindex"],
              ["domain", "build", "--write"], ["daemon", "start"])
        for argv in yes:
            self.assertTrue(dm.cacheable(argv), argv)
        for argv in no:
            self.assertFalse(dm.cacheable(argv), argv)

    def test_unchanged_tree_hits_cache_and_generation_bump_invalidates(self):
        dm._WATCHER = _FakeWatcher(generation=7)
        first = dm.execute(["--version"], Path(ROOT))
        second = dm.execute(["--version"], Path(ROOT))
        self.assertEqual(first, second)
        self.assertEqual(1, dm.cache_stats()["hits"], "同代际第二次必须命中缓存")
        dm._WATCHER.generation = 8                    # 树变了：监听件报新代际
        third = dm.execute(["--version"], Path(ROOT))
        self.assertEqual(first, third)
        self.assertEqual(1, dm.cache_stats()["hits"], "代际一变必须重算（不得复用旧响应）")

    def test_unhealthy_watcher_never_serves_cache(self):
        """监听不可信（未启动 / 失效）→ 缓存整体停用：不命中、也不留旧条目。"""
        dm._WATCHER = _FakeWatcher(generation=3, healthy=False)
        dm.execute(["--version"], Path(ROOT))
        dm.execute(["--version"], Path(ROOT))
        st = dm.cache_stats()
        self.assertFalse(st["enabled"])
        self.assertEqual(0, st["hits"])
        self.assertEqual(0, st["entries"])

    def test_non_allowlisted_command_is_not_cached(self):
        dm._WATCHER = _FakeWatcher(generation=1)
        dm.execute(["help"], Path(ROOT))
        dm.execute(["help"], Path(ROOT))
        st = dm.cache_stats()
        self.assertEqual(0, st["entries"], "非准入命令不得进缓存")
        self.assertEqual(0, st["hits"])

    def test_unknown_command_invalidates_previously_cached_responses(self):
        """守护自己执行过「可能写」的命令后，先前缓存的响应必须**立刻**作废。

        依据（竞态）：响应缓存的作废原本只靠监听线程**异步**察觉变更——那中间有一个几毫秒窗口。
        脚本里 `nf conformance --write; nf score` 这种连跑就可能落在窗口里，**吃到写之前的旧响应**。
        判据是确定性的、不靠计时：把假监听件的代际**按住不动**（模拟"监听还没察觉"），
        中间跑一条**非准入**命令（= 可能写），再看先前那条缓存还能不能命中。
        """
        dm._WATCHER = _FakeWatcher(generation=1)
        dm.execute(["--version"], Path(ROOT))          # 真算并落缓存
        dm.execute(["--version"], Path(ROOT))          # 命中
        self.assertEqual(1, dm.cache_stats()["hits"])
        dm.execute(["help"], Path(ROOT))               # 非准入（无法证明只读）→ 必须立刻作废
        dm.execute(["--version"], Path(ROOT))          # 因此必须重算
        self.assertEqual(1, dm.cache_stats()["hits"],
                         "非准入命令执行后不得再命中旧响应（否则落进几毫秒的监听窗口）")

    def test_colour_env_is_part_of_the_key(self):
        """配色环境会改变**输出文本**，故必须进键：否则无色环境会回放带 ANSI 的旧响应。"""
        dm._WATCHER = _FakeWatcher(generation=1)
        old = {k: os.environ.get(k) for k in ("NO_COLOR", "CLICOLOR_FORCE")}
        try:
            os.environ.pop("NO_COLOR", None)
            os.environ.pop("CLICOLOR_FORCE", None)
            dm.execute(["--version"], Path(ROOT))
            os.environ["NO_COLOR"] = "1"
            dm.execute(["--version"], Path(ROOT))
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        st = dm.cache_stats()
        self.assertEqual(0, st["hits"], "环境不同不得命中同一条缓存")
        self.assertEqual(2, st["entries"], "两种环境各占一条")

    def test_allowlisted_commands_are_byte_reproducible(self):
        """**准入判据本身**：同树连跑两次，退出码 / stdout / stderr 必须逐字节相同。

        缓存把「旧输出」当「新输出」的前提，是这些命令对同一棵树是**纯函数**——一旦某条命令
        的输出里混进时间戳 / 耗时 / 随机序，本判据当场红，逼着把它从 `CACHEABLE_COMMANDS` 删掉。
        """
        dm._WATCHER = None                            # 关缓存：这里测的是命令自身
        for argv in (["--version"], ["layers", "--json"], ["stats", "--json"],
                     ["doctor", "--json"], ["interop", "--check"], ["toolface", "--json"],
                     ["assertions"], ["cognition", "glossary"], ["patterns", "ls"],
                     ["module", "verify"], ["decisions", "verify"],
                     ["score", "--json"], ["conformance", "--json"]):
            a = dm.execute(list(argv), Path(ROOT))
            b = dm.execute(list(argv), Path(ROOT))
            self.assertEqual(a, b,
                             "输出不可复现，不得进 CACHEABLE_COMMANDS：nf %s" % " ".join(argv))


class WatchDaemonIntegrationTest(unittest.TestCase):
    """端到端（进程内起真服务）：带监听的守护「树没变 → 整条复用；代际一变 → 重算」。

    进程内起服务是**覆盖率要点**：守护通常在子进程里跑，那段代码在 `coverage run` 里不可见
    （见 test_daemon.DaemonInProcessServerTest 的同款说明）。本用例**不往仓库写任何文件**：
    「树变了」由真监听件的代际推进来模拟，真通知面由 DirWatcherTest 在临时目录里测。
    """

    def setUp(self):
        if not watch.available():
            self.skipTest("本平台没有目录监听实现（本波仅 Windows）")
        # 测试卫生（本文件里每个用例各起一个**进程内**服务）：响应缓存与计数是**模块级**的，
        # 不清就会跨用例泄漏——表现为「单跑过、整跑挂」的顺序依赖（实测踩过）。
        dm.reset_response_cache()
        for k in dm._CACHE_STATS:
            dm._CACHE_STATS[k] = 0
        self.home = tempfile.mkdtemp(prefix="nf_watch_ip_")
        self._old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = self.home
        self.port = None

        def ready(port):
            self.port = port

        self.thread = threading.Thread(target=dm.serve_forever,
                                       args=(ROOT, 30.0, ready),
                                       kwargs={"watch": True}, daemon=True)
        self.thread.start()
        for _ in range(300):
            if self.port:
                break
            time.sleep(0.01)
        self.assertIsNotNone(self.port, "进程内服务未能就绪")

    def tearDown(self):
        dm.stop()
        self.thread.join(timeout=5)
        if self._old_home is None:
            os.environ.pop("NARRATIVE_FORGE_HOME", None)
        else:
            os.environ["NARRATIVE_FORGE_HOME"] = self._old_home
        import shutil
        shutil.rmtree(self.home, ignore_errors=True)

    def _call(self, argv):
        doc = dm.read_state()
        self.assertIsNotNone(doc, "服务在跑，状态文件必须可读")
        return dm.run_request(doc, argv, cwd=ROOT)

    def test_cache_enabled_and_hit_then_invalidated_by_generation(self):
        st = dm.query_stats()
        self.assertIsNotNone(st, "守护必须能回答 stats（观测面在守护进程内）")
        self.assertTrue(st["enabled"], "带 --watch 起的守护必须启用响应缓存")
        self.assertEqual(0, st["generation"])

        first = self._call(["--version"])
        second = self._call(["--version"])
        self.assertEqual(first, second)
        st2 = dm.query_stats()
        self.assertEqual(1, st2["hits"], "同代际第二次必须命中响应缓存")
        self.assertEqual(1, st2["entries"])

        dm._WATCHER._bump()                       # 模拟「真监听件收到一批变更通知」
        third = self._call(["--version"])
        self.assertEqual(first, third)
        st3 = dm.query_stats()
        self.assertEqual(1, st3["hits"], "代际一变不得复用旧响应")
        self.assertGreaterEqual(st3["generation"], 1)

    def test_readonly_commands_are_cached_and_write_flags_bypass(self):
        """两条只读命令各占一条缓存；带写盘开关的一律**绕过**（绝不进表）。

        口径要**确定性**：先清缓存与计数，再跑两条互不相同的只读命令 → 条目/未命中都必须是 2。
        （早先写成「只有 --version 该被缓存」是错的：`conformance` 本来就在准入表里。）
        """
        dm.reset_response_cache()
        for k in dm._CACHE_STATS:
            dm._CACHE_STATS[k] = 0
        self._call(["--version"])
        self._call(["layers", "--json"])
        st = dm.query_stats()
        self.assertEqual(2, st["entries"], "两条只读命令应各占一条响应缓存")
        self.assertEqual(2, st["misses"], "两条都该是未命中（缓存刚清）")
        for argv in (["conformance", "--write"], ["stats", "--write"],
                     ["score", "--write-baseline"], ["layers", "--out", "x"]):
            self.assertFalse(dm.cacheable(argv), argv)

    def test_zero_subprocess_client_really_talks_to_the_daemon(self):
        """**快路**必须有判据：函数坏掉只表现为"变慢"（输出一模一样），所以不能只看输出。

        证据用**守护侧**的响应缓存命中计数——只有守护的 `execute` 才会让它涨，回退到 python 直跑
        不会。这条同时钉住"生成函数里的解释器路径/引号没问题"（未加引号时函数直接 127）。
        """
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("本机无 bash（无法 eval 快路函数）")
        gen = subprocess.run([sys.executable, "scripts/nf.py", "daemon", "shell-init", "bash"],
                             cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(0, gen.returncode, gen.stderr)
        def served():
            """守护侧「真的执行过这条命令」的计数：命中与未命中**都只由守护的 execute 推动**。

            只数 `hits` 会在「同类里别的用例刚推进代际、这条正好是 miss」时误报，所以两者相加。
            """
            st = dm.query_stats()
            return st["hits"] + st["misses"]

        before = served()
        env = dict(os.environ)
        env["NARRATIVE_FORGE_HOME"] = self.home          # 让函数看见本用例起的守护
        r = subprocess.run([bash, "-c", 'eval "$1"; nf --version', "nfinit", gen.stdout],
                           cwd=ROOT, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
        self.assertEqual(0, r.returncode, r.stderr or r.stdout)
        self.assertIn("nf ", r.stdout)
        self.assertGreaterEqual(served(), before + 1,
                                "函数没走守护快路——回退也能出正确输出，所以必须用守护侧计数当证据")

    def test_cached_response_is_byte_identical_to_a_direct_run(self):
        """**响应缓存不改语义**：命中缓存那一次的输出，必须与真子进程直跑逐字节相同。

        依据：仓库的头号不变式是「守护的 (exit, stdout, stderr) 与真子进程直跑逐字节相同」，
        由 `test_daemon.DaemonProtocolTest` 守着——但那条跑的是**未命中**路径（守护默认没开
        `--watch`）。开了响应缓存之后，**命中那一次是整条回放、根本没有执行**，所以这一半必须单独钉：
        用一条**重**命令（`conformance --json`，约 2.5 KB 载荷）同时覆盖"大载荷走同一套帧"。
        """
        argv = ["conformance", "--json"]
        first = self._call(argv)              # 未命中：真算，并落缓存
        second = self._call(argv)             # 命中：整条回放
        self.assertEqual(first, second, "命中缓存的那一次与首算不一致")
        direct = subprocess.run([sys.executable, "scripts/nf.py"] + argv, cwd=ROOT,
                                capture_output=True)
        self.assertEqual((direct.returncode, direct.stdout, direct.stderr), second,
                         "缓存回放的 (exit, stdout, stderr) 必须与真子进程直跑逐字节相同")

    def test_resident_layer_is_wired_and_unknown_change_clears_it(self):
        """守护**接线**判据：带 `--watch` 的守护必须装上常驻语料层；说不清的变更必须整批作废。

        为什么这条必须有：常驻层的收益是「不重读」，而它的风险是「读旧值」——两者的分界全在
        `execute()` 开头那一句 `_sync_resident`。判据用**内容计数**（不看墙钟）：读一件真语料 →
        常驻里应当有它；`_bump()`（说不清）之后下一条请求必须把常驻层整批换掉（计数归零重建）。

        观测走**守护自己**（`query_stats`）而不是本模块早先 import 的那份 `conformance_scan`：
        `_sync_code` 在代码面变化时会把 `core.*` 从 `sys.modules` 里摘掉重载（保证守护不跑旧代码），
        于是「早先 import 的那个对象」与「守护/CLI 正在用的那个对象」可能不是同一个——拿前者当
        观测面会得到**看着像 bug 的读数**（本波实测踩过）。
        """
        self._call(["--version"])
        self.assertTrue(sys.modules["core.conformance_scan"].resident_active(),
                        "带监听的守护必须安装常驻语料层")
        sys.modules["core.conformance_scan"].read_text_cached(
            os.path.join(ROOT, "protocol", "LAYERS.json"))
        self.assertGreater(dm.query_stats()["resident"]["text"], 0, "读过的件应被常驻")

        dm._WATCHER._bump()                      # 只跳代际、没给路径 = 说不清
        self._call(["--version"])
        self.assertTrue(sys.modules["core.conformance_scan"].resident_active())
        self.assertEqual(0, dm.query_stats()["resident"]["text"],
                         "说不清的变更必须整批作废（宁可全废重算，不可留着陈旧件错答）")

    def test_newline_in_argv_never_enters_the_line_framed_protocol(self):
        """**协议边界**：明文框（NFREQ）逐行送 argv——含换行的参数会被拆成两个、**静默改参数个数**。

        契约（本判据钉的就是它）：含换行的 argv **一律不接快路**，客户端退回 python 入口
        （协议本就写明「要精确传递请走 JSON 框」）。证据用守护侧计数——只有守护的 `execute`
        才会让 `hits+misses` 涨；正向对照见上一条用例（`--version` 走快路时它**会**涨）。
        参数取 `layers` 前缀（在响应缓存准入表里）：若守卫失效，守护不但会执行，还会缓存这条
        被拆过的 argv——那正是「静默错答」的形状。

        新行一律在 **bash 内部**合成（`"$(printf 'line1\\nline2')"` / `set --`），不经宿主命令行，
        所以参数到客户端手里是完整的。

        后半段另判「两条客户端与 python 直跑逐字节相同」，但**先探测本机 exec 边界的能力**：
        从别的进程 exec 一个 bash 脚本时，argv 要先拼成宿主命令行再解析回来——本机（Git
        Bash/MSYS）走 **Win32 命令行**，而 Python 的 `list2cmdline` **不给含换行的参数加引号**
        （实测），裸换行被当空白 → **参数在 NF 的代码跑起来之前就已经分成两个了**（实测：
        launcher 里 `$#` 直接是 3，与本守护无关）。这是宿主环境的性质，POSIX 上 execve 原样
        传 argv。故该断言只在边界真能原样传参时判——否则跳过并说明，避免写出「只在 CI 上炸」
        的判据（2026-09 的教训）。
        """
        if not BASH:
            self.skipTest("本环境没有 bash（shell 客户端需 bash 执行快路）")
        gen = subprocess.run([sys.executable, "scripts/nf.py", "daemon", "shell-init", "bash"],
                             cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(0, gen.returncode, gen.stderr)
        env = dict(os.environ)
        env["NARRATIVE_FORGE_HOME"] = self.home          # 让两条客户端都看得见本用例的守护

        def served():
            st = dm.query_stats()
            return st["hits"] + st["misses"]

        # ① 快路函数（`eval "$(nf daemon shell-init bash)"`）的守卫
        before = served()
        subprocess.run([BASH, "-c", 'eval "$1"; nf layers "$(printf "line1\\nline2")"',
                        "nfinit", gen.stdout],
                       cwd=ROOT, env=env, capture_output=True, timeout=180)
        self.assertEqual(before, served(),
                         "含换行的 argv 进了逐行协议（会被拆开并静默改个数）——必须退回 python 入口")

        # ② 启动器 `scripts/nf` 的守卫：`set --` 在 bash 内部合成 argv，再 **source** 启动器
        #    （source 不经宿主命令行，参数原样进 `$@`）。
        before = served()
        subprocess.run([BASH, "-c", 'set -- layers "$(printf "line1\\nline2")"; . scripts/nf'],
                       cwd=ROOT, env=env, capture_output=True, timeout=180)
        self.assertEqual(before, served(),
                         "启动器把含换行的 argv 交给了逐行协议")

        # ③ 边界能力探测：本机能不能把含换行的参数**无损**交给 bash？
        probe = subprocess.run([BASH, "-c", 'printf %s "$1"', "p", "line1\nline2"],
                               capture_output=True)
        if probe.stdout != b"line1\nline2":
            self.skipTest("本机 exec 边界（Git Bash 的 Win32 命令行解析）在参数抵达 NF 之前就把它拆开了"
                          "——「客户端输出 == 直跑输出」这一半在本平台无从判；协议契约已由 ①② 判过")

        argv = ["help", "line1\nline2"]
        direct = subprocess.run([sys.executable, "scripts/nf.py"] + argv, cwd=ROOT,
                                capture_output=True)
        launch = subprocess.run([BASH, "scripts/nf", *argv], cwd=ROOT, env=env,
                                capture_output=True)
        self.assertEqual((direct.returncode, direct.stdout, direct.stderr),
                         (launch.returncode, launch.stdout, launch.stderr),
                         "启动器快路不得把含换行的参数拆开")
        func_run = subprocess.run([BASH, "-c", 'eval "$1"; nf help "$(printf "line1\\nline2")"',
                                   "nfinit", gen.stdout],
                                  cwd=ROOT, env=env, capture_output=True)
        self.assertEqual((direct.returncode, direct.stdout, direct.stderr),
                         (func_run.returncode, func_run.stdout, func_run.stderr),
                         "快路函数不得把含换行的参数拆开")


class ResidentLayerTest(unittest.TestCase):
    """常驻语料层：**只按确知变更失效**、说不清就整批作废、只收录监听根之下的件。

    它是「数据结构跃迁」的主角（2026-09-29）：把「每次请求重读整棵语料 + 重列 1484 个目录」
    换成「常驻 + 按变更事件精确失效」。**实测**（同机、各 3 轮中位）：改一个文件之后守护里的
    第一条 `nf score` **1591 → 872 ms**（无关变更）、**1625 → 951 ms**（相关变更）。

    判据全部是确定性内容/计数（不看墙钟）：失效是**调用方的责任**，所以这里同时钉住契约的两面——
    没给失效信号时常驻值照旧（陈旧由调用方负责），给了就必须立刻看到新内容。
    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="nf_resident_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.addCleanup(csc.clear_resident)          # 不把常驻层漏给别的用例
        self.outside = tempfile.mkdtemp(prefix="nf_outside_")
        self.addCleanup(shutil.rmtree, self.outside, ignore_errors=True)
        self._write("sub/a.md", "A")
        self._write("b.md", "B", base=self.outside)

    def _write(self, rel, text, base=None):
        path = os.path.join(base or self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return path

    def test_only_files_under_the_watched_root_are_kept(self):
        """根外的件**不许**收录：根外没有变更通知，无从失效（收了就等于埋一颗陈旧地雷）。"""
        csc.install_resident(self.root)
        self.assertTrue(csc.resident_active())
        own = os.path.join(self.root, "sub", "a.md")
        self.assertEqual("A", csc.read_text_cached(own))
        self.assertEqual("B", csc.read_text_cached(os.path.join(self.outside, "b.md")))
        self.assertEqual(1, csc.resident_stats()["text"], "只该收录监听根之下的那一件")

    def test_listing_is_served_then_invalidated_by_declared_path(self):
        csc.install_resident(self.root)
        sub = os.path.join(self.root, "sub")
        self.assertIn("a.md", [e.name for e in csc._scandir_list(sub)])
        self.assertGreaterEqual(csc.resident_stats()["dirs"], 1, "列目录结果必须被常驻下来")
        self._write("sub/c.md", "C")
        self.assertNotIn("c.md", [e.name for e in csc._scandir_list(sub)],
                         "没有失效信号时常驻值照旧——**失效是调用方的责任**（契约的另一面）")
        csc.drop_resident(["sub/c.md"])
        self.assertIn("c.md", [e.name for e in csc._scandir_list(sub)], "给了确知路径就必须失效")
        self.assertEqual("C", csc.read_text_cached(os.path.join(sub, "c.md")))

    def test_text_change_is_invalidated_by_declared_path(self):
        csc.install_resident(self.root)
        path = os.path.join(self.root, "sub", "a.md")
        self.assertEqual("A", csc.read_text_cached(path))
        self._write("sub/a.md", "A2")
        csc.drop_resident(["sub/a.md"])
        self.assertEqual("A2", csc.read_text_cached(path))

    def test_clear_resident_drops_everything(self):
        csc.install_resident(self.root)
        csc.read_text_cached(os.path.join(self.root, "sub", "a.md"))
        self.assertGreater(csc.resident_stats()["text"], 0)
        csc.clear_resident()
        self.assertFalse(csc.resident_active())
        self.assertEqual({"dirs": 0, "text": 0, "bytes": 0}, csc.resident_stats())


class DirWatcherTest(unittest.TestCase):
    """真实监听件（有实现的平台才跑）+ 无实现平台的降级面。"""

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_take_changes_reports_known_paths_and_flags_unknown(self):
        """变更面：**确知**的路径要报出来；说不清（只跳代际 / 溢出）必须标 `unknown`。

        用途（见 `daemon._sync_resident`）：守护据此**按路径**精确失效常驻语料层；说不清就整批
        作废。判据只盯这两件事——「报得出」与「不敢装懂」。
        """
        with tempfile.TemporaryDirectory() as tmp:
            w = watch.DirWatcher(tmp)
            self.assertTrue(w.start())
            try:
                before = w.generation
                (Path(tmp) / "a.txt").write_text("一", encoding="utf-8")
                self.assertTrue(_wait_generation(w, before))
                deadline = time.time() + 3
                paths, unknown = set(), False
                while time.time() < deadline:
                    paths, unknown = w.take_changes()
                    if paths or unknown:
                        break
                    time.sleep(0.02)
                self.assertIn("a.txt", paths, "确知变更必须报出路径")
                self.assertFalse(unknown, "报得出路径就不该标说不清")
                self.assertEqual((set(), False), w.take_changes(), "取走后必须清空")

                sub = Path(tmp) / "sub"
                sub.mkdir()
                (sub / "b.md").write_text("二", encoding="utf-8")
                deadline = time.time() + 3
                paths = set()
                while time.time() < deadline:
                    paths, _unknown = w.take_changes()
                    if any("b.md" in p for p in paths):
                        break
                    time.sleep(0.02)
                self.assertTrue(any("b.md" in p for p in paths), "子树里的变更也要报出路径")

                w._bump()                                  # 只跳代际、没给路径 = 说不清
                self.assertEqual((set(), True), w.take_changes(),
                                 "说不清的变更必须标 unknown（调用方据此整批作废）")
                w._bump(overflow=True)
                _paths, unknown2 = w.take_changes()
                self.assertTrue(unknown2, "缓冲溢出属于说不清")
            finally:
                w.stop()

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_detects_create_modify_and_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = watch.DirWatcher(tmp)
            self.assertTrue(w.start(), "监听启动失败（拿不到目录句柄？）")
            try:
                for action in ("create", "modify", "delete"):
                    before = w.generation
                    p = Path(tmp) / "probe.txt"
                    if action == "create":
                        p.write_text("一", encoding="utf-8")
                    elif action == "modify":
                        p.write_text("二", encoding="utf-8")
                    else:
                        p.unlink()
                    self.assertTrue(_wait_generation(w, before), "%s 未被监听到" % action)
            finally:
                w.stop()
            self.assertFalse(w.healthy, "stop() 之后不得再声称健康")
            self.assertFalse(w.start() and not w.healthy)

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_subdirectory_changes_are_recursive(self):
        """子树递归：本仓的语料大多在子目录里（漏了递归就等于漏判）。"""
        with tempfile.TemporaryDirectory() as tmp:
            w = watch.DirWatcher(tmp)
            self.assertTrue(w.start())
            try:
                before = w.generation
                sub = Path(tmp) / "community" / "包" / "modules"
                sub.mkdir(parents=True)
                (sub / "m.md").write_text("一", encoding="utf-8")
                self.assertTrue(_wait_generation(w, before), "子目录变更未被监听到")
            finally:
                w.stop()

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_git_only_change_does_not_bump_the_generation(self):
        """`.git/` 下的变更**不得**推进代际：否则日常 git 工作流会把响应缓存整批作废
        （每跑一次 `git status/add/commit`，下一个 `nf score` 就要退回 ~2.2 s 重算）。

        安全前提由下面的 `NfReadFaceTest` 守着：NF 的读面根本不碰 `.git`。
        """
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".git").mkdir()               # 先建好：目录创建本身也是一条通知
            w = watch.DirWatcher(tmp)
            self.assertTrue(w.start())
            try:
                before = w.generation
                (Path(tmp) / ".git" / "HEAD").write_text("ref: refs/heads/main\n",
                                                         encoding="utf-8")   # 改已存在件
                deadline = time.time() + 5
                while time.time() < deadline and w.ignored_batches == 0:
                    time.sleep(0.02)
                self.assertGreaterEqual(w.ignored_batches, 1, "`.git` 变更未被识别为可忽略批次")
                self.assertEqual(before, w.generation, "`.git`-only 变更不得推进代际")
                # 创建/删除会额外触发「目录本身」的通知（Windows 实测），同样必须被忽略
                probe = Path(tmp) / ".git" / "index.lock"
                probe.write_text("x", encoding="utf-8")
                probe.unlink()
                deadline = time.time() + 5
                while time.time() < deadline and w.ignored_batches < 2:
                    time.sleep(0.02)
                self.assertGreaterEqual(w.ignored_batches, 2, "`.git` 下增删未被视为可忽略")
                self.assertEqual(before, w.generation,
                                 "`.git` 下增删（含目录自身通知）不得推进代际")
                (Path(tmp) / "正常件.md").write_text("一", encoding="utf-8")
                self.assertTrue(_wait_generation(w, before), "非 .git 变更必须推进代际")
            finally:
                w.stop()

    def test_overflow_is_reported_and_bumps_generation(self):
        """缓冲溢出必须**如实上报**（调用方据此作废全部缓存），且代际继续单调。"""
        w = watch.DirWatcher(ROOT)
        before = w.generation
        w._bump(overflow=True)
        self.assertTrue(w.overflowed)
        self.assertEqual(before + 1, w.generation)

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_volume_gate_accepts_local_and_rejects_remote_like_paths(self):
        """**卷类型闸门**：网络盘（SMB/UNC）的通知语义不可靠、会静默漏事件 → 一律不启用。

        （`GetDriveTypeW` 要的是**卷根**：给完整路径它会回 DRIVE_NO_ROOT_DIR —— 本波实测踩过，
         所以这里连同"完整路径也能判对"一起钉住。）
        """
        self.assertTrue(watch._volume_supports_notifications(ROOT), "本地固定盘必须放行")
        self.assertFalse(watch._volume_supports_notifications(r"\\srv\share\repo"),
                         "UNC / 网络盘必须拒绝")
        self.assertFalse(watch._volume_supports_notifications("Z:\\不存在的盘\\repo"),
                         "不存在的卷必须拒绝（判不出来就当不支持）")

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_mechanism_selfcheck_passes_and_gates_start(self):
        """**机制自检**：打开句柄成功 ≠ 通知会到；自检不过必须判不可用（fail-closed）。

        自检自身在本机必须过（真跑 create/modify/delete 三类）；把卷闸门或自检按成"不支持"时，
        `start()` 必须返回 False——**绝不**出现"自称健康但代际永不推进"的假绿。
        """
        self.assertTrue(watch.selfcheck(), "本机机制自检必须通过（三类通知都到）")
        with tempfile.TemporaryDirectory() as tmp:
            real_vol, real_self = watch._volume_supports_notifications, watch.selfcheck
            try:
                watch._volume_supports_notifications = lambda _p: False
                self.assertFalse(watch.DirWatcher(tmp).start(), "卷闸门否决时不得启动")
                watch._volume_supports_notifications = real_vol
                watch.selfcheck = lambda: False
                self.assertFalse(watch.DirWatcher(tmp).start(), "自检不过时不得启动")
            finally:
                watch._volume_supports_notifications = real_vol
                watch.selfcheck = real_self
            w = watch.DirWatcher(tmp)
            try:
                self.assertTrue(w.start(), "闸门恢复后必须能正常启动")
            finally:
                w.stop()          # 必须停掉：它持有该目录句柄，否则临时目录在 Windows 上删不掉

    @unittest.skipIf(watch.available(), "仅在「无实现平台」检查降级面")
    def test_unavailable_platform_degrades_without_raising(self):
        w = watch.DirWatcher(ROOT)
        self.assertFalse(w.start())
        self.assertFalse(w.healthy)
        w.stop()                                      # 幂等、不抛


class NfReadFaceTest(unittest.TestCase):
    """**安全前提**：NF 的读面不碰 `.git`——这是「守护可以忽略 `.git` 变更」的全部依据。

    判据可执行：追踪一次 `regression_score.evaluate` 的全部打开与尝试打开，断言仓内**没有任何**
    `.git/` 路径。哪天有人让某个扫描器去读 `.git`，这条**先红**——而不是让守护悄悄回放旧响应。
    （代码面另有事实支撑：`.git` 只出现在 `asset_ledger`/`text_hygiene` 的**排除**集合与
    写 hooks 的安装脚本里。）
    """

    def test_evaluate_never_reads_git_paths(self):
        import builtins
        import io

        from core import regression_score as rs

        rs.evaluate(ROOT)                             # 预热（热态的读面不会更小）
        opened, tried = set(), set()
        real_io, real_b = io.open, builtins.open

        def spy(file, *a, **k):
            try:
                key = os.path.normcase(os.path.abspath(str(file)))
            except Exception:                         # noqa: BLE001 - 计数失败不影响被测逻辑
                key = None
            if key:
                tried.add(key)
            handle = real_io(file, *a, **k)
            if key:
                opened.add(key)
            return handle

        io.open = builtins.open = spy
        try:
            rs.evaluate(ROOT)
        finally:
            io.open, builtins.open = real_io, real_b
        root = os.path.normcase(os.path.abspath(ROOT))
        mark = os.sep + ".git" + os.sep
        hit = sorted(p for p in (opened | tried)
                     if p.startswith(root) and mark in p)
        self.assertEqual([], [os.path.relpath(p, root) for p in hit],
                         "NF 读面碰了 .git —— 守护忽略 .git 变更的前提不再成立")


if __name__ == "__main__":
    unittest.main()
