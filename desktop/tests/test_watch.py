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

from core import daemon as dm  # noqa: E402
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


class DirWatcherTest(unittest.TestCase):
    """真实监听件（有实现的平台才跑）+ 无实现平台的降级面。"""

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
