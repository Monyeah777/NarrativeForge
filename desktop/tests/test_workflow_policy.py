#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作流供应链策略（`core/workflow_policy.py`）回归测试 —— 外部标准落地面。

标准出处：`ossf/scorecard` `docs/checks.md` §Pinned-Dependencies（构建/发布依赖须钉具体哈希）
与 §Token-Permissions（GITHUB_TOKEN 权限须显式且最小）。
"""
import sys
import tempfile
import unittest
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import workflow_policy as wp  # noqa: E402

SHA = "1" * 40


def _wf(tmp: str, name: str, body: str) -> None:
    d = Path(tmp) / wp.WORKFLOWS_REL
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(body, encoding="utf-8")


def _reqs(tmp: str, lines) -> None:
    d = Path(tmp) / ".github"
    d.mkdir(parents=True, exist_ok=True)
    (d / "requirements-ci.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


class WorkflowPolicyTest(unittest.TestCase):
    def test_pinned_uses_with_permissions_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "ok.yml", "name: ok\npermissions:\n  contents: read\n"
                               "timeout-minutes: 10\n"
                               "steps:\n  - uses: actions/checkout@%s  # v4\n" % SHA)
            issues, warns, stats = wp.scan(tmp)
        self.assertEqual([], issues)
        self.assertEqual([], warns)
        self.assertEqual({"workflows": 1, "pinned_uses": 1, "with_explicit_permissions": 1,
                          "requirements_files": 0}, stats)

    def test_mutable_ref_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "bad.yml", "permissions: read-all\nsteps:\n  - uses: actions/checkout@v4\n")
            issues, _w, _s = wp.scan(tmp)
        self.assertTrue(any("未钉提交 SHA" in i and "修复指引" in i for i in issues), issues)

    def test_missing_or_write_all_permissions_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "noperm.yml", "steps:\n  - uses: actions/checkout@%s  # v4\n" % SHA)
            missing, _w, _s = wp.scan(tmp)
            _wf(tmp, "wide.yml", "permissions: write-all\nsteps:\n"
                                 "  - uses: actions/checkout@%s  # v4\n" % SHA)
            wide, _w2, _s2 = wp.scan(tmp)
        self.assertTrue(any("缺显式 permissions" in i for i in missing), missing)
        self.assertTrue(any("write-all" in i for i in wide), wide)

    def test_local_action_is_exempt_and_missing_comment_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "local.yml", "permissions: read-all\ntimeout-minutes: 10\n"
                                  "steps:\n  - uses: ./.github/actions/x\n")
            issues, _w, _s = wp.scan(tmp)
            _wf(tmp, "nocomment.yml", "permissions: read-all\ntimeout-minutes: 10\n"
                                      "steps:\n  - uses: actions/checkout@%s\n" % SHA)
            _i2, warns, _s2 = wp.scan(tmp)
        self.assertEqual([], issues, "本地动作不该被判")
        self.assertTrue(any("版本注释" in w for w in warns), warns)

    def test_real_repo_workflows_are_all_pinned(self):
        """真仓：所有 `uses:` 都钉提交 SHA，且每个工作流都有显式 permissions。"""
        issues, _warns, stats = wp.scan(str(ROOT))
        self.assertEqual([], issues)
        self.assertGreaterEqual(stats["workflows"], 10, "工作流件数须有规模（判据自身要有效）")
        self.assertGreaterEqual(stats["pinned_uses"], 10)
        self.assertGreaterEqual(stats["requirements_files"], 3, "固定依赖清单须在场")
        self.assertEqual(stats["workflows"], stats["with_explicit_permissions"],
                         "每个工作流都须显式声明 permissions")

    def test_missing_timeout_is_rejected(self):
        """挂死有界（2026-10-01 补）：工作流不声明 `timeout-minutes` 即 FAIL。

        依据：GitHub 默认上限 **6h**——挂死的 job 会把 runner 占满、挤掉后续定时任务
        （`gitee-poll` 是每 10 分钟一轮的轮询入库线）。实测真仓 **8 件**缺此项，已补齐；
        本判据防回潮。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "noto.yml", "permissions: read-all\nsteps:\n  - uses: ./.local\n")
            issues, _w, _s = wp.scan(tmp)
        self.assertTrue(any("timeout-minutes" in i and "修复指引" in i for i in issues), issues)

    def test_unpinned_requirement_is_rejected(self):
        """FAIR4RS 的 R 面：依赖清单须钉 `==`（浮动的 `>=` 判 FAIL）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _wf(tmp, "ok.yml", "permissions: read-all\ntimeout-minutes: 10\n"
                               "steps:\n  - uses: ./.local\n")
            _reqs(tmp, ["# 注释行豁免", "pyyaml==6.0.1"])
            pinned, _w, _s = wp.scan(tmp)
            _reqs(tmp, ["pyyaml>=6"])
            floating, _w2, _s2 = wp.scan(tmp)
        self.assertEqual([], pinned, pinned)
        self.assertTrue(any("未钉版本" in i and "修复指引" in i for i in floating), floating)


class CiReferenceReachabilityTest(unittest.TestCase):
    """CI 工作流与 `verify.sh` 引用的**仓库内路径 / nf 子命令**必须真实可达。

    依据（2026-10-01 普查）：文档面早有 `test_doc_reachability`（入口文档里的路径与 `nf <cmd>`
    必须真在），但**执行面**没这条——工作流或闸门脚本里写错的脚本路径/子命令，要等那次 CI 真跑
    才会暴露（本地全绿、云端红）。本件把「执行面引用可达」也立成可核事实。
    """

    PATHISH = re.compile(r"(?<![\w./-])((?:scripts|desktop|engine|\.github|protocol)/"
                         r"[\w./\u4e00-\u9fff-]+\.(?:py|sh|ps1|json|md|yml|yaml|txt|cfg|toml))")
    NF_CMD = re.compile(r"nf(?:\.py)?\s+([a-z][a-z0-9-]*)")

    def _targets(self):
        wfs = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        return [(p.name, p) for p in wfs] + [("verify.sh", ROOT / "verify.sh")]

    def _nf_subcommands(self) -> set:
        src = (ROOT / "scripts" / "nf.py").read_text(encoding="utf-8")
        return set(re.findall(r'add_parser\(\s*"([a-z0-9-]+)"', src))

    def test_referenced_paths_exist(self):
        missing = []
        for label, p in self._targets():
            text = p.read_text(encoding="utf-8", errors="replace")
            for m in self.PATHISH.finditer(text):
                rel = m.group(1)
                if any(ch in rel for ch in "$*{"):
                    continue              # 变量/通配写法不判
                if not (ROOT / rel).exists():
                    missing.append("%s:%d %s" % (label, text[:m.start()].count("\n") + 1, rel))
        self.assertEqual([], missing, "CI/闸门引用了不存在的路径（改路径或补件）：%s" % missing)

    def test_referenced_nf_subcommands_exist(self):
        known = self._nf_subcommands()
        self.assertGreater(len(known), 40, "子命令集合没解出来（判据可能已失效）")
        missing = []
        for label, p in self._targets():
            text = p.read_text(encoding="utf-8", errors="replace")
            for m in self.NF_CMD.finditer(text):
                if m.group(1) not in known:
                    missing.append("%s:%d nf %s" % (label, text[:m.start()].count("\n") + 1,
                                                    m.group(1)))
        self.assertEqual([], missing, "CI/闸门引用了不存在的 nf 子命令：%s" % missing)


if __name__ == "__main__":
    unittest.main()
