#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""云端代收站（.github/scripts）加固回归测试 —— 2026-09-24 渗透发现的「check 的 check」。

对应两项渗透确认缺陷：
  F-02 危险 sink 门禁作用域漏掉 `.github/scripts`（唯一处理远程不可信输入、且持有写权限
       令牌的代码）→ 同一份含 os.system / subprocess(shell=True) 的文件放 scripts/ 被拦、
       放 .github/scripts/ 隐身。本测试断言作用域覆盖 + 变异样本能被捕获。
  F-03 两个入库机器人写的 frontmatter 缺 `rating` → 声明件写明「缺字段即 FAIL」，
       于是**每次成功入库都会把 verify check34 判红**（Gitee 通道 mode=open 时任何匿名
       用户一条正常投稿即可远程触发）。本测试真跑一次入库（DRY_RUN，落临时目录），
       断言产物带 rating 且过 rating_gate / library.verify。
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import purity_scan as ps  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])
BOT = os.path.join(ROOT, ".github", "scripts", "library_ingest.py")


def bot_module():
    """导入入库机器人模块（断言其常量 / 纯函数；导入无副作用，仅读环境变量默认值）。"""
    scripts_dir = os.path.join(ROOT, ".github", "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import library_ingest  # noqa: PLC0415
    return library_ingest


#: Linux 内核对**单条** argv/env 字符串的硬限（32 页 = 131072 字节）。`getconf ARG_MAX`
#: 是总量上限，不是单串上限；超限时 execve 直接 E2BIG（Errno 7），子进程起不来。
#: 判据在此**本地就生效**（Windows 无此限制，故必须显式设限，否则回归只在 CI 上炸）。
MAX_EXEC_STRLEN = 131072


def run_bot(tmp, body=None, number="991", body_file=None):
    """在临时副本里真跑一次 GitHub 前端入库（DRY_RUN，不提交/不调 API）。

    正文传输：小载荷走 `ISSUE_BODY`（历史通道）；大载荷走 `ISSUE_BODY_FILE`（见下）。
    """
    shutil.copytree(os.path.join(ROOT, "library"), os.path.join(tmp, "library"))
    shutil.copytree(os.path.join(ROOT, "desktop", "src"),
                    os.path.join(tmp, "desktop", "src"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    env = dict(os.environ)
    env.pop("ISSUE_BODY", None)
    env.pop("ISSUE_BODY_FILE", None)
    env.update({"DRY_RUN": "1", "REPO": "Monyeah777/NarrativeForge",
                "ISSUE_NUMBER": number, "ISSUE_AUTHOR": "monyeah777",
                "ISSUE_TITLE": "【NF投稿】回归测试投稿"})
    if body_file is not None:
        env["ISSUE_BODY_FILE"] = str(body_file)
    else:
        payload = body.encode("utf-8")
        if len(payload) >= MAX_EXEC_STRLEN:
            raise AssertionError(
                "环境变量单串 %d 字节 ≥ 内核单串上限 %d：Linux 上 execve 会 E2BIG（Errno 7），"
                "子进程根本起不来——请改用 body_file 通道（2026-09 事故即由此而来）"
                % (len(payload), MAX_EXEC_STRLEN))
        env["ISSUE_BODY"] = body
    return subprocess.run([sys.executable, BOT], cwd=tmp, env=env,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=180)


def new_entries(tmp):
    """本次入库新产出的条目文件名。"""
    before = set(os.listdir(os.path.join(ROOT, "library")))
    return [p for p in os.listdir(os.path.join(tmp, "library"))
            if p.startswith("NF-") and p.endswith(".md") and p not in before]


class GateScopeTest(unittest.TestCase):
    """F-02：门禁作用域必须含 .github/scripts。"""

    def test_import_scan_covers_github_scripts(self):
        joined = " ".join(ps.IMPORT_SCAN)
        self.assertIn(".github/scripts", joined,
                      "危险 sink / import 门禁作用域漏掉 .github/scripts（最高风险入口）")

    def test_mutation_sink_under_github_scripts_captured(self):
        """变异注入：把危险 sink 放进 .github/scripts → 必须被捕获。"""
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".github", "scripts"))
            with open(os.path.join(tmp, ".github", "scripts", "ghost.py"), "w",
                      encoding="utf-8") as fh:
                fh.write("import os\n\n\ndef run(v):\n    return os.system('echo ' + v)\n")
            issues, _ = ps.scan(tmp)
        hits = [i for i in issues if ".github/scripts/ghost.py" in i.replace("\\", "/")]
        self.assertTrue(hits, "放到 .github/scripts 的危险 sink 应被 R6 捕获：%s" % issues)

    def test_repo_ingest_bots_are_clean_under_gate(self):
        """本仓库两个机器人本身须过 R5/R6（作用域扩容后不得引入新 FAIL）。"""
        issues, _ = ps.scan(ROOT)
        hits = [i for i in issues
                if "/.github/scripts/" in i.replace("\\", "/")]
        self.assertFalse(hits, "入库机器人自身触发门禁：%s" % hits)


class IngestRatingTest(unittest.TestCase):
    """F-03：入库产物必须自带 frontmatter `rating`，否则自伤 check34。"""

    def _run_bot(self, tmp, body, number="991"):
        return run_bot(tmp, body, number)

    def test_entry_carries_rating_and_passes_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self._run_bot(tmp, "标题: 回归测试条目\n一句话: 演示\n\n---\n\n# 正文\n\n普通投稿。\n")
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            made = new_entries(tmp)
            self.assertTrue(made, "机器人未产出新条目：%s" % proc.stdout)
            with open(os.path.join(tmp, "library", made[0]), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("rating:", text,
                          "入库产物缺 frontmatter rating → rating_gate 会判 FAIL（自伤门禁）")

            from core import rating_gate as rg
            issues, _ = rg.scan(tmp)
            self.assertEqual([], issues, "入库产物未过分级门：%s" % issues)

    def test_declared_rating_is_honored(self):
        """投稿显式声明词表内分级时，机器人须照写（而不是一律 unrated）。"""
        with tempfile.TemporaryDirectory() as tmp:
            proc = self._run_bot(
                tmp, "标题: 声明分级条目\n分级: mature\n一句话: 演示\n\n---\n\n# 正文\n\n普通投稿。\n")
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            made = new_entries(tmp)
            with open(os.path.join(tmp, "library", made[0]), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("rating: mature", text, text[:400])


class IngestSecretRefusalTest(unittest.TestCase):
    """F-07：疑似明文密钥不得入库（既不二次分发，也不让零门槛通道把 CI 打红）。"""

    def test_secret_shaped_submission_is_refused(self):
        fake = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_bot(tmp, "标题: 示例条目\n一句话: 演示\n\n---\n\n# 正文\n\n占位：" + fake + "\n")
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertEqual([], new_entries(tmp),
                             "含密钥形状的投稿不应入库（会二次公开分发密钥并把 CI 打红）")

    def test_secret_hint_does_not_echo_full_secret(self):
        """拒绝说明只能回显形状前缀——否则等于用提示把密钥第二次抄出来。"""
        li = bot_module()
        secret = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
        hit = li.secret_shape_hit("前缀 " + secret + " 后缀")
        self.assertTrue(hit, "形状串未被检出")
        self.assertNotIn(secret, hit, "回显内容不得含完整密钥")

    def test_normal_submission_still_ingests(self):
        """反例护栏：普通投稿不得被密钥拒收误伤。"""
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_bot(tmp, "标题: 普通条目\n一句话: 演示\n\n---\n\n# 正文\n\n普通正文。\n")
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertEqual(1, len(new_entries(tmp)), proc.stdout)


class BodyChannelTest(unittest.TestCase):
    """正文通道优先级：文件 > env > **议题 API**（生产真源）。

    2026-09 事故的根因修法：生产不再经 env 传正文（Linux 单条 env 字符串上限 131072 字节，
    超限时步骤 E2BIG 起不来），改由机器人经 API 取——本类离线锁住这条决策链与 fail-closed。
    """

    def _patched(self):
        """临时替换模块全局（本模块在导入时读环境，故只能在模块属性上打桩）。"""
        m = bot_module()
        saved = (m.BODY, m.REPO, m.TOKEN, m.N, m.api)
        return m, saved

    def test_api_channel_is_used_when_no_file_or_env(self):
        m, saved = self._patched()
        try:
            m.BODY = ""
            m.REPO, m.TOKEN, m.N = "Monyeah777/NarrativeForge", "tk", "7"
            m.api = lambda path, *a, **k: {"body": "来自议题 API 的正文"}
            self.assertEqual("来自议题 API 的正文", m.resolve_body())
        finally:
            m.BODY, m.REPO, m.TOKEN, m.N, m.api = saved

    def test_env_channel_wins_over_api(self):
        m, saved = self._patched()
        try:
            m.BODY = "来自 env 的正文"
            m.REPO, m.TOKEN, m.N = "Monyeah777/NarrativeForge", "tk", "7"
            m.api = lambda path, *a, **k: {"body": "不该被取到"}
            self.assertEqual("来自 env 的正文", m.resolve_body())
        finally:
            m.BODY, m.REPO, m.TOKEN, m.N, m.api = saved

    def test_no_credentials_yields_empty_not_fabricated(self):
        """没有文件/env/凭据时返回空串（由 main 的「正文为空」分支礼貌拒收），不得凭空造正文。"""
        m, saved = self._patched()
        try:
            m.BODY = ""
            m.REPO = ""
            self.assertEqual("", m.resolve_body())
        finally:
            m.BODY, m.REPO, m.TOKEN, m.N, m.api = saved

    def test_guard_refuses_oversized_payload_over_env(self):
        """护栏：想把 ≥128 KiB 载荷经 env 塞给子进程的用例，在**任何 OS**上都当场判死。

        这正是 2026-09 事故的教训——Windows 无 MAX_ARG_STRLEN 限制，故旧写法在本机静默通过、
        在 Linux CI 上 E2BIG；把内核限制写进断言，回归就不再依赖「跑在哪个 OS」。
        """
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(AssertionError) as ctx:
                run_bot(tmp, body="标题: 超长\n\n---\n\n" + ("填充" * (MAX_EXEC_STRLEN // 2)))
        self.assertIn("E2BIG", str(ctx.exception))
        self.assertIn("body_file", str(ctx.exception))


class IngestSizeCapTest(unittest.TestCase):
    """F-08：超长正文不得入库（零门槛通道下否则可远程拖垮检出与门禁）。"""

    def test_oversized_submission_is_refused(self):
        """超长正文不得入库（F-08；2026-09 事故：这条用例曾让云端 CI 连红 21 次）。

        载荷 ≈ 262k 字符（≈786 KB）——**远超** Linux 单条 env 字符串 131072 字节硬限，故必须
        走文件通道：经 env 传时子进程在 execve 就 E2BIG（Errno 7），「超长拒收」逻辑根本没
        机会执行，而 Windows 本机却一路绿。CI 从 2026-09-24 起全红即由此而来。
        """
        MAX_BODY_CHARS = bot_module().MAX_BODY_CHARS
        body = "标题: 超长条目\n一句话: 演示\n\n---\n\n# 正文\n\n" + ("填充" * (MAX_BODY_CHARS // 2 + 100))
        self.assertGreater(len(body.encode("utf-8")), MAX_EXEC_STRLEN * 2,
                           "该用例的载荷必须真的越过内核单串上限（否则这条判据守不住）")
        with tempfile.TemporaryDirectory() as tmp:
            body_path = os.path.join(tmp, "_issue_body.txt")
            with open(body_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
            proc = run_bot(tmp, body_file=body_path)
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertEqual([], new_entries(tmp), "超长正文不应入库")

    def test_normal_sized_submission_still_ingests(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_bot(tmp, "标题: 常规条目\n一句话: 演示\n\n---\n\n# 正文\n\n" + ("正常内容。" * 500) + "\n")
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertEqual(1, len(new_entries(tmp)), proc.stdout)


if __name__ == "__main__":
    unittest.main()
