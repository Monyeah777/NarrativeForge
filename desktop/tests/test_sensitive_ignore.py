# -*- coding: utf-8 -*-
"""敏感文件忽略面门禁：AGENTS.md「敏感文件禁止」硬性闸门的**机器判据**。

为什么：该纪律此前只有正文（AGENTS.md 写「不 cat/read/commit .env、credentials.*、
*private*key*、*token*、*secret*」），**忽略侧零判据**——一个 `.env` 落在工作区就会被
无意识地 `git add`。本件把两件事钉死：
① `git check-ignore` 必须真的忽略高信号形态（`.env` / `credentials.*` / `*.pem` / `id_rsa*` …）；
② 已跟踪文件里**不得**出现这些形态（存在即 FAIL——命中就该撤凭据并重建，见 CONTRIBUTING Token 轮换 SOP）。

纪律：只读；`git check-ignore --stdin` 用**不存在的路径**探测规则（不必真造文件）。
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: 必须被忽略的高信号形态（与 .gitignore 的敏感段一一对应）
MUST_IGNORE = (".env", ".env.local", "credentials.json", "credentials.yaml",
               "server.pem", "private.key", "cert.p12", "bundle.pfx",
               "id_rsa", "id_ed25519", "vault.kdbx")
#: 已跟踪文件里不得出现的形态（大小写不敏感）
_TRACKED_BAD = (r"(^|/)(\.env(\..*)?|credentials\.[a-z0-9]+|id_(rsa|dsa|ecdsa|ed25519)(\..*)?)$"
                r"|\.(pem|key|p12|pfx|kdbx)$")
MUST_NOT_TRACK = re.compile(_TRACKED_BAD, re.I)


def _git(*args, stdin: str = "") -> str:
    """跑 git 并把 stdout 当文本返回。

    注意（实测踩过）：Windows 上 `text=True` 会把 stdin 的 `\\n` 翻成 `\\r\\n`，
    于是 `git check-ignore --stdin` 收到的是带 `\\r` 的路径、**一条都匹配不上**——
    判据会「静默全过」。这里一律走字节，杜绝换行翻译。
    """
    p = subprocess.run(["git", *args], cwd=str(ROOT), input=stdin.encode("utf-8"),
                       capture_output=True, timeout=120)
    return p.stdout.decode("utf-8", "replace")


class SensitiveIgnoreTest(unittest.TestCase):
    def test_required_shapes_are_ignored(self):
        out = _git("check-ignore", "--stdin", stdin="\n".join(MUST_IGNORE) + "\n")
        ignored = set(out.split())
        missing = sorted(set(MUST_IGNORE) - ignored)
        self.assertEqual([], missing, "这些敏感形态未被 .gitignore 覆盖：%s" % missing)

    def test_no_sensitive_file_is_tracked(self):
        # `-z` 是必须的：默认输出把**非 ASCII 路径**转义加引号（`"05_\346\265..."`），
        # 于是 `.pem` 变成 `.pem"`、正则 $ 锚点失配——中文名敏感件会被**静默放过**。
        listed = _git("ls-files", "-z").split("\0")
        bad = [f for f in listed if f and MUST_NOT_TRACK.search(f)]
        self.assertEqual([], bad, "已跟踪敏感文件（撤凭据 + 从历史移除后重建）")

    def test_check_ignore_has_catch_power(self):
        """变异自证：一个**非敏感**名字不应被忽略（否则判据只会无脑通过）。"""
        out = _git("check-ignore", "--stdin", stdin="docs/ordinary-note.md\n")
        self.assertEqual("", out.strip(), "普通文件名被误忽略")


if __name__ == "__main__":
    unittest.main()
