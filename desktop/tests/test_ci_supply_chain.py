#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI 供应链固定回归测试 —— 2026-09-24 渗透发现 F-05 的「check 的 check」。

背景（渗透实证）：`verify.sh` 与 core/scripts 的任何 check **都不读 `.github/`**，
所以 workflow 面此前零判据——`uses: actions/x@v4` 这类可移动 tag 等于把 CI 执行权
交给上游标签（tag 重指即换代码）。本测试把「一律按提交 SHA 引用」这条钉住，
同时要求 dependabot 在场，避免「固定」退化成「冻结」。
"""
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"

#: 第三方 action 引用：<owner>/<repo>@<40 位十六进制 SHA>（可选 `# vX` 注释）
_PINNED = re.compile(r"^[^@/\s]+/[^@\s]+@[0-9a-f]{40}$")
_USES = re.compile(r"(?m)^\s*-?\s*uses:\s*(\S+)\s*(?:#.*)?$")


def _uses_refs():
    refs = []
    for f in sorted(WORKFLOWS.glob("*.yml")):
        with open(f, encoding="utf-8") as fh:
            for m in _USES.finditer(fh.read()):
                refs.append((f.name, m.group(1)))
    return refs


class WorkflowActionPinningTest(unittest.TestCase):
    def test_every_action_is_pinned_to_commit_sha(self):
        refs = _uses_refs()
        self.assertTrue(refs, "未在 .github/workflows 下找到任何 uses: 引用")
        unpinned = []
        for name, ref in refs:
            if ref.startswith("./") or ref.startswith("docker://"):
                continue                      # 本地 action / 容器镜像：不是标签引用面
            if not _PINNED.match(ref):
                unpinned.append("%s -> %s" % (name, ref))
        self.assertEqual([], unpinned,
                         "action 必须固定到 40 位提交 SHA（可移动 tag = 把 CI 执行权交给上游）")

    def test_pins_are_kept_fresh_by_dependabot(self):
        self.assertTrue(DEPENDABOT.is_file(),
                        "缺 .github/dependabot.yml：固定 SHA 后须有自动跟进，否则等于冻结上游")
        with open(DEPENDABOT, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("github-actions", text,
                      "dependabot 须覆盖 github-actions 生态才能跟进固定值")


class CiRequirementsPinTest(unittest.TestCase):
    """F-05 余项：CI 依赖固定（requirements 清单）必须在场、可解析、且被 workflow 引用。"""

    CI_REQ = ROOT / ".github" / "requirements-ci.txt"
    LINT_REQ = ROOT / ".github" / "requirements-lint.txt"
    #: 允许的清单形态：`包名==版本`（允许 extras/连字符/下划线/点）
    _PIN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9._,-]+\])?==[0-9][^#\s]*$")

    def _pins(self, path):
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()]
        return [ln for ln in lines if ln and not ln.startswith("#")]

    def test_requirements_files_exist_and_pin_exact_versions(self):
        for path in (self.CI_REQ, self.LINT_REQ):
            self.assertTrue(path.is_file(), "缺 %s（依赖不可复现，pip-audit 也无可审对象）" % path)
            pins = self._pins(path)
            self.assertTrue(pins, "%s 无任何依赖行" % path)
            for line in pins:
                self.assertRegex(line, self._PIN,
                                 "%s 的依赖未固定到精确版本：%s" % (path.name, line))

    def test_requirements_files_are_ascii_only(self):
        """pip 按**locale** 编码解析 requirements（不认 coding cookie）。

        非 UTF-8 locale（如 Windows/GBK）下，非 ASCII 注释会让 `pip install -r` 直接抛
        UnicodeDecodeError —— 本波实测踩到过。故这两个文件必须保持 ASCII。
        """
        for path in (self.CI_REQ, self.LINT_REQ):
            with open(path, "rb") as fh:
                raw = fh.read()
            bad = [b for b in raw if b > 127]
            self.assertEqual([], bad, "%s 含非 ASCII 字节（会破坏非 UTF-8 locale 下的 pip）"
                             % path.name)

    def test_workflows_install_from_requirements_not_bare_versions(self):
        """workflow 不得再出现裸 `pip install <包>`——版本只能来自固定清单。"""
        offenders = []
        for f in sorted(WORKFLOWS.glob("*.yml")):
            with open(f, encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if line.lstrip().startswith("#"):
                        continue          # 注释里出现 `pip install` 字样不算安装动作
                    low = line.lower()
                    if "pip install" in low and "-r .github/requirements" not in low:
                        offenders.append("%s:%d %s" % (f.name, i, line.strip()))
        self.assertEqual([], offenders,
                         "pip 安装须走固定清单（否则版本随上游漂移）：%s" % offenders)

    def test_dependency_audit_job_exists_and_targets_the_pins(self):
        """依赖审计必须真的跑起来（本机出网受限跑不了，就交给 CI）——且审的是固定集。"""
        wf = WORKFLOWS / "dependency-audit.yml"
        self.assertTrue(wf.is_file(), "缺 dependency-audit 工作流：依赖面又回到零审计")
        text = wf.read_text(encoding="utf-8")
        self.assertIn("requirements-ci.txt", text,
                      "审计须指向固定后的 CI 依赖集（requirements-ci.txt）")
        self.assertIn("pip_audit", text, "审计步骤须真的调用 pip-audit")
        self.assertIn("requirements-audit.txt", text,
                      "审计器自身版本也须固定（否则审计器随上游漂移）")

    def test_audit_requirements_file_is_pinned(self):
        audit_req = ROOT / ".github" / "requirements-audit.txt"
        self.assertTrue(audit_req.is_file())
        for line in self._pins(audit_req):
            self.assertRegex(line, self._PIN, "审计器未固定版本：%s" % line)


if __name__ == "__main__":
    unittest.main()
