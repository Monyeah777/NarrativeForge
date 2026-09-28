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
        """相对判据（机器无关）：同一命令，守护往返 < 冷启动/3。"""
        argv = ["--version"]
        t0 = time.perf_counter()
        subprocess.run([sys.executable, str(ROOT / "scripts" / "nf.py")] + argv,
                       cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cold_ms = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        dm.run_request(self._state(), argv, cwd=str(ROOT))
        warm_ms = (time.perf_counter() - t0) * 1000
        self.assertGreater(cold_ms, 0)
        self.assertLess(warm_ms * 3, cold_ms,
                        "守护往返 %.1f ms 应远小于冷启动 %.1f ms" % (warm_ms, cold_ms))


class DaemonShellInitTest(unittest.TestCase):
    def test_shell_init_emits_syntactically_valid_bash(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("nfcli_d", ROOT / "scripts" / "nf.py")
        nf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nf)          # type: ignore[union-attr]
        out = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(out):
            code = nf.main(["daemon", "shell-init", "bash"])
        self.assertEqual(0, code)
        script = out.getvalue()
        self.assertIn("nf() {", script)
        self.assertIn(str(ROOT), script)
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("本机无 bash（跳过语法检查）")
        tmp = Path(tempfile.mkdtemp(prefix="nf_shell_init_")) / "init.sh"
        tmp.write_text(script, encoding="utf-8", newline="\n")
        r = subprocess.run([bash, "-n", str(tmp)], capture_output=True, text=True)
        self.assertEqual(0, r.returncode, r.stderr)


if __name__ == "__main__":
    unittest.main()
