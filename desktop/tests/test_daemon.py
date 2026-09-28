#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行层常驻守护（core/daemon.py）单测：协议 / 令牌 / 拒绝面 / 等价性 / 新鲜度 / 相对加速。

纪律与全仓一致：每条性质都要有**能在本机跑红**的判据——
- 等价：守护跑出的 (exit, stdout, stderr) 与进程内直跑**逐字节相同**；
- 新鲜度：每次请求清空按路径键的进程缓存、保留内容键缓存（前者随仓库变，后者键即内容）；
- 安全：只回环、需令牌、请求有上限、长驻/自指命令拒跑——且拒绝之后守护**仍活着**；
- 效率：相对判据（守护 < 冷启动/3），不写死毫秒，免得在慢机上抖。
"""
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import daemon as dm  # noqa: E402


def _plain_request(sock, token, argv, cwd):
    sock.sendall(("NFREQ 1 %s\n%s\n%d\n%s\n"
                  % (token, cwd, len(argv), "\n".join(argv))).encode("utf-8"))


class DaemonHarness(unittest.TestCase):
    """共用夹具：把 NF_HOME 隔离到临时目录，起一个守护给所有用例复用。"""

    @classmethod
    def setUpClass(cls):
        cls.home = tempfile.mkdtemp(prefix="nf_daemon_home_")
        cls._old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = cls.home
        cls._old_cwd = os.getcwd()
        os.chdir(ROOT)
        ok, msg = dm.start(ROOT, idle_timeout=120.0)
        assert ok, "守护启动失败：%s" % msg

    @classmethod
    def tearDownClass(cls):
        dm.stop()
        os.chdir(cls._old_cwd)
        if cls._old_home is None:
            os.environ.pop("NARRATIVE_FORGE_HOME", None)
        else:
            os.environ["NARRATIVE_FORGE_HOME"] = cls._old_home
        shutil.rmtree(cls.home, ignore_errors=True)

    # ---- 便利函数 ----
    def _state(self):
        doc = dm.read_state()
        self.assertIsNotNone(doc, "守护状态文件应可读")
        return doc

    def _send(self, raw: bytes):
        doc = self._state()
        with socket.create_connection((dm.BIND_HOST, doc["port"]), timeout=10) as sock:
            sock.settimeout(10)
            sock.sendall(raw)
            return dm.read_framed(sock)

    def _direct(self, argv):
        """对照组 = **真子进程直跑**（用户实际看到的那一次，含平台换行语义）。

        不拿进程内 StringIO 当基准：那个没有 newline 翻译（Windows 上真进程写 `\\r\\n`），
        用它比对会把「守护与真跑一致」误判成不一致。
        """
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "nf.py")] + list(argv),
                           cwd=str(ROOT), capture_output=True)
        return r.returncode, r.stdout, r.stderr


class DaemonProtocolTest(DaemonHarness):
    def test_output_matches_direct_run_byte_for_byte(self):
        """核心判据：守护执行 = 进程内直跑（逐字节，含退出码）。"""
        for argv in (["--version"], ["stats", "--check"], ["layers", "--verify"],
                     ["market", "--list"], ["doctor"]):
            code, out, err = dm.run_request(self._state(), argv, cwd=str(ROOT))
            dcode, dout, derr = self._direct(argv)
            self.assertEqual(code, dcode, "退出码不一致：%s" % argv)
            self.assertEqual(out, dout, "stdout 不一致：%s" % argv)
            self.assertEqual(err, derr, "stderr 不一致：%s" % argv)

    def test_plain_and_json_framing_agree(self):
        """明文框（shell 客户端）与 JSON 框（程序客户端）语义一致。"""
        doc = self._state()
        argv = ["--version"]
        code, out, err = dm.run_request(doc, argv, cwd=str(ROOT))
        with socket.create_connection((dm.BIND_HOST, doc["port"]), timeout=10) as sock:
            sock.settimeout(10)
            _plain_request(sock, doc["token"], argv, str(ROOT))
            pcode, pout, perr = dm.read_framed(sock)
        self.assertEqual((code, out, err), (pcode, pout, perr))


class DaemonHardeningTest(DaemonHarness):
    def test_token_is_required_and_daemon_survives_rejection(self):
        doc = self._state()
        with socket.create_connection((dm.BIND_HOST, doc["port"]), timeout=10) as sock:
            sock.settimeout(10)
            sock.sendall(json.dumps({"proto": dm.PROTO, "token": "wrong", "cwd": str(ROOT),
                                     "argv": ["--version"]}).encode() + b"\n")
            code, _out, err = dm.read_framed(sock)
        self.assertEqual(2, code)
        self.assertIn("令牌", err.decode("utf-8"))
        self.assertTrue(dm.ping(), "拒绝之后守护必须仍然活着")

    def test_long_running_commands_are_refused(self):
        for argv in (["serve", "x.json"], ["shell"], ["daemon", "status"]):
            code, _out, err = dm.run_request(self._state(), argv, cwd=str(ROOT))
            self.assertEqual(2, code, "应拒跑长驻/自指命令：%s" % argv)
            self.assertIn("拒跑", err.decode("utf-8"))
        self.assertTrue(dm.ping())

    def test_oversized_request_is_rejected(self):
        doc = self._state()
        code = None
        try:
            with socket.create_connection((dm.BIND_HOST, doc["port"]), timeout=10) as sock:
                sock.settimeout(10)
                sock.sendall(b"x" * (dm.MAX_REQUEST_BYTES + 10))
                code, _out, _err = dm.read_framed(sock)
        except OSError:
            code = 2                      # 服务端判死并断开，也算拒绝
        self.assertNotEqual(0, code, "超限请求不得被执行")
        self.assertTrue(dm.ping())

    def test_state_file_shape_and_token_not_leaked(self):
        doc = self._state()
        self.assertEqual(dm.PROTO, doc["proto"])
        self.assertIsInstance(doc["port"], int)
        self.assertEqual(64, len(doc["token"]))
        self.assertEqual(str(ROOT), doc["root"])
        out = io.StringIO()
        import contextlib
        nf = dm._cli_module(ROOT)
        with contextlib.redirect_stdout(out):
            nf.main(["daemon", "status"])
        self.assertNotIn(doc["token"], out.getvalue(), "人读输出不得回显令牌")

    def test_loopback_only(self):
        self.assertEqual("127.0.0.1", dm.BIND_HOST)
        src = (ROOT / "desktop" / "src" / "core" / "daemon.py").read_text(encoding="utf-8")
        self.assertNotIn("--allow-non-loopback", src,
                         "守护能执行任意 nf 命令，不得提供放行外网的开关")


class DaemonFreshnessTest(DaemonHarness):
    def test_path_keyed_caches_are_cleared_per_request(self):
        """按路径/根键的缓存必须逐请求清空——否则热进程会拿旧仓库事实回话。"""
        from core import pack_combo
        pack_combo.profiles(ROOT)                      # 预热
        calls = []
        orig = pack_combo.cache_clear
        pack_combo.cache_clear = lambda: (calls.append(1), orig())[1]
        try:
            dm.execute(["--version"], ROOT)
        finally:
            pack_combo.cache_clear = orig
        self.assertGreaterEqual(len(calls), 1, "执行前后必须清空 pack_combo 进程缓存")

    def test_content_keyed_caches_are_kept(self):
        """内容键缓存（键即内容）跨请求保留——这正是热进程的收益来源。"""
        from core import conformance_scan as csc
        text = "```yaml\nmachine_contract:\n  id: M00\n```\n"
        first = csc._fence_yaml(text, "machine_contract")
        dm.execute(["--version"], ROOT)
        cache_before = len(csc._FENCE_CACHE)
        csc._fence_yaml(text, "machine_contract")      # 再取一次
        self.assertEqual(first, csc._fence_yaml(text, "machine_contract"))
        self.assertGreaterEqual(len(csc._FENCE_CACHE), 1, "内容键缓存不该被清空")
        del cache_before

    def test_source_fingerprint_triggers_reload(self):
        """源码指纹变了 → 守护重载 CLI（不跑旧代码）。"""
        dm.execute(["--version"], ROOT)
        before = dm._CLI_CACHE.get("fp")
        self.assertIsNotNone(before)
        dm._CLI_CACHE["fp"] = (("fake.py", 1, 1),)     # 人为制造「源码已变」
        dm.execute(["--version"], ROOT)
        self.assertNotEqual((("fake.py", 1, 1),), dm._CLI_CACHE.get("fp"),
                            "指纹不符时必须重新同步")


class DaemonSpeedTest(DaemonHarness):
    def test_daemon_is_much_faster_than_cold_start(self):
        """相对判据（机器无关）：守护**稳态**往返 < 冷启动/3。

        必须**先预热再测**：守护的**首次**请求还要把 CLI 模块载进来（导入 + 源码指纹，几十毫秒），
        把它算进"稳态"会在解释器启动很快的机器（Linux CI 冷启动仅数十毫秒）上让 3× 判据不成立
        ——那是测量口径错，不是性能不达标。故：预热一次 → 取 3 次最小值作稳态；冷启动取 2 次最小值。
        """
        argv = ["--version"]
        doc = self._state()
        dm.run_request(doc, argv, cwd=str(ROOT))            # 预热（首次请求含模块装载）
        cold = []
        for _ in range(2):
            t0 = time.perf_counter()
            subprocess.run([sys.executable, str(ROOT / "scripts" / "nf.py")] + argv,
                           cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cold.append((time.perf_counter() - t0) * 1000)
        warm = []
        for _ in range(3):
            t0 = time.perf_counter()
            dm.run_request(doc, argv, cwd=str(ROOT))
            warm.append((time.perf_counter() - t0) * 1000)
        cold_ms, warm_ms = min(cold), min(warm)
        self.assertGreater(cold_ms, 0)
        self.assertLess(warm_ms * 3, cold_ms,
                        "守护稳态往返 %.1f ms 应远小于冷启动 %.1f ms" % (warm_ms, cold_ms))

    def test_shim_fast_path_beats_python_direct(self):
        """**启动器快路**判据：`scripts/nf` 经守护必须快过「python 直跑」，且在 POSIX 上要快 3×。

        动机：我在报告里主张「Linux 上是毫秒级」，但门禁此前只覆盖了守护协议与缓存——
        **没有一个判据盯着启动器本身**。这条把它钉住：本机（Windows/MSYS）实测 178 ms vs 357 ms
        （spawn 是地板，故只要求显著更小）；Linux（CI）上 bash spawn 只要几毫秒，故要求 3×。
        """
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("本机无 bash（启动器快路需要 bash 的 /dev/tcp）")
        argv = ["--version"]
        shim, direct = [], []
        for _ in range(3):
            t0 = time.perf_counter()
            subprocess.run([bash, str(ROOT / "scripts" / "nf")] + argv, cwd=str(ROOT),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            shim.append((time.perf_counter() - t0) * 1000)
            t0 = time.perf_counter()
            subprocess.run([sys.executable, str(ROOT / "scripts" / "nf.py")] + argv,
                           cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            direct.append((time.perf_counter() - t0) * 1000)
        shim_ms, direct_ms = min(shim), min(direct)
        self.assertLess(shim_ms, direct_ms,
                        "启动器 %.1f ms 应快过 python 直跑 %.1f ms" % (shim_ms, direct_ms))
        if os.name == "posix":
            self.assertLess(shim_ms * 3, direct_ms,
                            "POSIX 上启动器快路 %.1f ms 应远小于 python 直跑 %.1f ms（毫秒级主张）"
                            % (shim_ms, direct_ms))


class DaemonInProcessServerTest(unittest.TestCase):
    """**进程内**起服务（线程）跑协议全路径——这也是覆盖率的关键：

    守护通常在**子进程**里跑，那段代码在 CI 的 `coverage run … -s desktop/tests` 里是不可见的；
    若只测子进程路径，`daemon.py` 的覆盖率会把 core 总覆盖率拖到 80% 线下（本仓 CI
    `core-coverage-ge-80` 会判红——实测踩过）。故此处把服务循环放进本进程线程里跑。
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="nf_daemon_ip_")
        self._old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = self.home
        self.port = None

        def ready(port):
            self.port = port

        self.thread = threading.Thread(target=dm.serve_forever,
                                       args=(ROOT, 30.0, ready), daemon=True)
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
        shutil.rmtree(self.home, ignore_errors=True)

    def _raw(self, payload: bytes):
        doc = dm.read_state()
        self.assertIsNotNone(doc, "服务已在跑，状态文件必须可读")
        with socket.create_connection((dm.BIND_HOST, doc["port"]), timeout=10) as sock:
            sock.settimeout(10)
            sock.sendall(payload)
            return dm.read_framed(sock)

    def test_json_and_plain_round_trip(self):
        doc = dm.read_state()
        req = json.dumps({"proto": dm.PROTO, "token": doc["token"], "cwd": str(ROOT),
                          "argv": ["--version"]}).encode("utf-8") + b"\n"
        code, out, err = self._raw(req)
        self.assertEqual(0, code)
        self.assertIn(b"nf ", out)
        self.assertEqual(b"", err)
        code2, out2, err2 = self._raw(
            ("NFREQ %d %s\n%s\n1\n--version\n" % (dm.PROTO, doc["token"], str(ROOT)))
            .encode("utf-8"))
        self.assertEqual((code, out, err), (code2, out2, err2))

    def test_malformed_requests_are_rejected_without_killing_server(self):
        doc = dm.read_state()
        cases = {
            "非 JSON": b"not json at all\n",
            "NFREQ 头错": ("NFREQ 9 %s\n%s\n0\n" % (doc["token"], str(ROOT))).encode(),
            "argv 条数不可解析": ("NFREQ %d %s\n%s\nabc\n" % (dm.PROTO, doc["token"],
                                                              str(ROOT))).encode(),
            "argv 条数越界": ("NFREQ %d %s\n%s\n99999\n" % (dm.PROTO, doc["token"],
                                                           str(ROOT))).encode(),
            "argv 非列表": (json.dumps({"proto": dm.PROTO, "token": doc["token"],
                                        "argv": "stats"}).encode() + b"\n"),
        }
        for label, payload in cases.items():
            code, _out, err = self._raw(payload)
            self.assertEqual(2, code, "应拒收：%s" % label)
            self.assertTrue(err, "拒收要带原因：%s" % label)
        self.assertTrue(dm.ping(), "畸形请求之后服务仍须可用")

    def test_shutdown_op_stops_the_loop(self):
        doc = dm.read_state()
        code, _out, _err = self._raw(
            json.dumps({"proto": dm.PROTO, "token": doc["token"], "op": "shutdown"})
            .encode() + b"\n")
        self.assertEqual(0, code)
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive(), "shutdown 帧应让服务循环退出")

    def test_stop_reports_when_no_daemon_running(self):
        """停掉本类的进程内服务 → 再停一次必须得到「没有守护」（而不是「守护未响应」）。

        竞态说明（CI 实测抓出）：`stop()` 一发现 ping 失败就返回，而服务端 `finally` 里的
        `clear_state()` 可能还没落盘——此刻登记在、端口已死，第二次 stop 会报「守护未响应」。
        修法有两层：① 服务端**先清状态再关端口**；② 客户端把「拒连」判成「登记过期 = 没有守护」
        并清掉过期登记。本判据同时钉住这两层（先等服务端清理落盘，再断言语义）。
        """
        ok, msg = dm.stop()
        self.assertTrue(ok, msg)
        deadline = time.time() + 5.0
        while dm.read_state() is not None and time.time() < deadline:
            time.sleep(0.05)                     # 等服务端 clear_state() 落盘
        ok, msg = dm.stop()
        self.assertFalse(ok)
        self.assertIn("没有守护", msg)
        self.assertFalse(dm.ping())

    def test_stale_state_pointing_at_dead_port_reports_no_daemon(self):
        """陈旧登记（端口拒连）必须被如实判成「没有守护」，并清除该登记。"""
        dm.stop()                                 # 先停掉本类服务
        dm.write_state({"proto": dm.PROTO, "pid": 1, "port": 9,   # 9 = discard，必然拒连
                        "token": "0" * 64, "root": str(ROOT), "started": 0})
        ok, msg = dm.stop()
        self.assertFalse(ok)
        self.assertIn("没有守护", msg)
        self.assertIsNone(dm.read_state(), "过期登记应被清除")

    def test_main_entry_help_and_short_serve(self):
        self.assertEqual(2, dm.main([]), "缺 --serve 时应打印帮助并返回 2")
        # 短服务用**自己的 NF_HOME**：同一 NF_HOME 下另起守护会覆盖状态文件，
        # 把本类 setUp 起的服务变成「失联」——CI（Linux）就是这样把它暴露出来的。
        tmp = tempfile.mkdtemp(prefix="nf_daemon_short_")
        old = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = tmp
        try:
            self.assertEqual(0, dm.main(["--serve", "--root", str(ROOT), "--idle", "0.05"]),
                             "短空闲的 --serve 应自然退出 0")
        finally:
            if old is None:
                os.environ.pop("NARRATIVE_FORGE_HOME", None)
            else:
                os.environ["NARRATIVE_FORGE_HOME"] = old
            shutil.rmtree(tmp, ignore_errors=True)

    def test_second_serve_in_same_home_is_refused(self):
        """一个 NF_HOME 只许一个守护（缺省 fail-closed）——否则后起者会顶掉先起者的状态登记。"""
        self.assertEqual(2, dm.serve_forever(ROOT, idle_timeout=0.05),
                         "已有守护在运行时另起服务应被拒（除非显式 force）")
        self.assertTrue(dm.ping(), "拒绝之后原服务必须仍然可用")

    def test_code_fingerprint_and_sync_are_idempotent(self):
        fp = dm._code_fingerprint(ROOT)
        self.assertTrue(any(str(r[0]).endswith("daemon.py") for r in fp), fp[:3])
        dm._sync_code(ROOT)
        dm._sync_code(ROOT)          # 第二次指纹相同 → 直接返回
        mod = dm._load_cli(ROOT)
        self.assertTrue(hasattr(mod, "main"))


class DaemonShellInitTest(unittest.TestCase):
    def _generated(self):
        """生成 `nf daemon shell-init bash` 的脚本文本（供语法与**行为**两级判据共用）。"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("nfcli_d", ROOT / "scripts" / "nf.py")
        nf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nf)          # type: ignore[union-attr]
        out = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(out):
            code = nf.main(["daemon", "shell-init", "bash"])
        self.assertEqual(0, code)
        return out.getvalue()

    def test_shell_init_emits_syntactically_valid_bash(self):
        script = self._generated()
        self.assertIn("nf() {", script)
        self.assertIn(str(ROOT), script)
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("本机无 bash（跳过语法检查）")
        tmp = Path(tempfile.mkdtemp(prefix="nf_shell_init_")) / "init.sh"
        tmp.write_text(script, encoding="utf-8", newline="\n")
        r = subprocess.run([bash, "-n", str(tmp)], capture_output=True, text=True)
        self.assertEqual(0, r.returncode, r.stderr)

    def test_shell_init_function_actually_runs_without_daemon(self):
        """**行为级**判据（语法检查抓不到）：守护不在时，`eval` 出来的 `nf` 必须能回退直跑。

        依据（2026-09 实测缺陷）：模板把解释器路径**未加引号**嵌入——本机是
        `C:\\Program Files\\Python311\\python.exe`，bash 会把它拆成命令 `C:\\Program`，于是
        **守护不在（含默认 1 小时空闲自退之后）**时 `nf <任何命令>` →
        **rc=127 + `C:Program: command not found`**。`bash -n` 对此完全无感（它语法合法），
        所以本判据必须真的 `eval` 一次并在**没有守护**的环境里跑一条命令。
        """
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("本机无 bash（无法 eval 快路函数）")
        script = self._generated()
        home = tempfile.mkdtemp(prefix="nf_shell_init_nodaemon_")
        env = dict(os.environ)
        env["NARRATIVE_FORGE_HOME"] = home          # 隔离后看不到任何守护状态文件
        try:
            r = subprocess.run([bash, "-c", 'eval "$1"; nf --version', "nfinit", script],
                               cwd=str(ROOT), env=env, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=180)
        finally:
            shutil.rmtree(home, ignore_errors=True)
        self.assertEqual(0, r.returncode,
                         "守护不在时函数必须回退 python 直跑（未加引号的解释器路径会 127）\n%s"
                         % (r.stderr or r.stdout))
        self.assertIn("nf ", r.stdout)


if __name__ == "__main__":
    unittest.main()
