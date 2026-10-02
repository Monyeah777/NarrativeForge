# -*- coding: utf-8 -*-
"""**指认判据必须在场**：代码与文档里点名 `test_x.py` / `test_x.test_y` 时，被判据要真的存在。

依据（2026-10-01）：`AGENTS.md` 记着一次「文档承诺由 `validatePath` 拦截、仓库里却根本没有该实现」
的**虚假保证**；同一类风险是指认一个**不存在或已改名**的判据——读者按图索骥找不到，更糟的是
以为某条纪律有常驻判据、其实没有（本轮就核出一次这类错位：`interp_diet` 说「由 test_launcher
钉住」确有其事，但覆盖窄到挡不住它要挡的回归）。

口径（**只认可解析的两种形式**，不认散文里偶然出现的 `test_` 词）：`test_<名>.py` 与
`test_<文件>.<成员>`（成员允许以 `*` 结尾表示一族，按前缀判定）。当前实盘：代码面 5 处、
文档面 56 处，全部解析到位。
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

TESTS = ROOT / "desktop" / "tests"
#: 已知的外部/历史指认 → 理由（当前为空；有例外必须逐条写明）。
KNOWN_EXTERNAL = {}

_FILE_REF = re.compile(r"\b(test_[a-z0-9_]+)\.py\b")
_MEMBER_REF = re.compile(r"\b(test_[a-z0-9_]+)\.(test_[a-z0-9_]+|Test[A-Za-z0-9_]*)\*?")
#: **元变量**（散文里举例用的占位名）：`test_x.py` / `test_foo.py` 这类不是指认，跳过。
#: 依据（2026-10-01，本判据自己抓到的）：CHANGELOG 里写「文档点名 `test_x.py` 时……」被当成真指认。
_PLACEHOLDER = re.compile(r"^test_(x|y|z|a|b|c|foo|bar|baz)$")


def _test_texts() -> dict:
    return {p.stem: p.read_text(encoding="utf-8", errors="replace")
            for p in TESTS.glob("*.py")}


def resolve(rel: str, member: str, texts: dict) -> str:
    """→ 问题描述（可解析返回空串）。"""
    if _PLACEHOLDER.match(rel):
        return ""
    if rel in KNOWN_EXTERNAL:
        return ""
    if rel not in texts:
        return "判据文件 %s.py 不在场" % rel
    if member:
        stem = member.rstrip("*")
        if stem and stem not in texts[rel]:
            return "%s.py 里没有 %s" % (rel, member)
    return ""


class JudgeReferenceTest(unittest.TestCase):
    def _code_files(self):
        return (sorted((ROOT / "desktop" / "src" / "core").glob("*.py"))
                + sorted((ROOT / "scripts").glob("*.py"))
                + sorted((ROOT / ".github" / "scripts").glob("*.py")))

    def _docs(self):
        out = []
        for pat in ("*.md", "docs/*.md", "skills/**/*.md", "community/**/*.md", "results/**/*.md"):
            out += sorted(ROOT.glob(pat))
        return out

    def test_code_side_judge_references_resolve(self):
        texts = _test_texts()
        bad, checked = [], 0
        for p in self._code_files():
            text = p.read_text(encoding="utf-8", errors="replace")
            for m in _FILE_REF.finditer(text):
                checked += 1
                issue = resolve(m.group(1), "", texts)
                if issue:
                    bad.append("%s → %s（%s）" % (p.name, m.group(0), issue))
            for m in _MEMBER_REF.finditer(text):
                checked += 1
                issue = resolve(m.group(1), m.group(2), texts)
                if issue:
                    bad.append("%s → %s（%s）" % (p.name, m.group(0), issue))
        self.assertGreaterEqual(checked, 3, "没扫到代码面的判据指认（判据可能已失效）")
        self.assertEqual([], bad, "指认的判据不存在（修复指引：改指认，或把文件/成员补回来）：%s" % bad)

    def test_doc_side_judge_references_resolve(self):
        texts = _test_texts()
        bad, checked = [], 0
        for p in self._docs():
            for m in _FILE_REF.finditer(p.read_text(encoding="utf-8", errors="replace")):
                checked += 1
                issue = resolve(m.group(1), "", texts)
                if issue:
                    bad.append("%s → %s（%s）" % (p.relative_to(ROOT).as_posix(), m.group(0), issue))
        self.assertGreaterEqual(checked, 30, "没扫到文档面的判据指认（判据可能已失效）")
        self.assertEqual([], bad, "文档指认的判据不存在：%s" % bad)

    def test_exemptions_are_not_stale(self):
        texts = _test_texts()
        stale = sorted(k for k in KNOWN_EXTERNAL if k in texts)
        self.assertEqual([], stale, "KNOWN_EXTERNAL 里有已在场的判据（该划掉了）：%s" % stale)


if __name__ == "__main__":
    unittest.main()
