# -*- coding: utf-8 -*-
"""入口 stdio 编码门禁（`scripts/*.py` 的可达性 ↔ Windows 默认控制台）。

动机（2026-09-30 真跑取证）：仓库自带的修复指引一律写「python scripts/<件> --write」，
而 Windows 默认控制台是 GBK。凡打印 `✓/✗/⚠/⇄` 等**非 GBK** 字符的入口，都会在**产物
已经写好之后**抛 `UnicodeEncodeError`——进程 exit 1、回溯刷屏，调用方把「成功」读成
「失败」，指引本身成了死路（实测：`build_verification_cards.py --write` 写盘正确、
退出码 1；`verify.sh` 内部因 export `PYTHONUTF8=1` 而看不见这一面，只有**照指引手跑**
才踩得到）。本件把「入口自钉 UTF-8 stdio」立成判据。

判据（三面）：① 含非 GBK 字符的入口必须真钉（文本面，逐件点名）；
② 钉法必须真跑出来（行为面：`PYTHONIOENCODING=gbk` 下跑，不许出 `UnicodeEncodeError`）；
③ 变异自证——同一判据喂「有字形、没钉」的合成件必判红（判据不是空转）。
"""
import os
import re
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ("scripts", ".github/scripts")

# 运行时生效的钉法：`__main__` 里的内联 reconfigure（本仓约定）/ nf.py、e2e 的直连写法。
_PINNED = re.compile(r"\.reconfigure\(encoding=\"utf-8\"\)")
_GBK = "gbk"
#: `print(...)` 行里带中文（第二档口径，见 `unpinned_cjk`）
_CJK_PRINT = re.compile(r"print\([^\n]*[\u4e00-\u9fff]")


def _non_gbk(text: str) -> str:
    """本件里**编码不出 GBK** 的字符（升序去重）。"""
    out = set()
    for ch in text:
        try:
            ch.encode(_GBK)
        except UnicodeEncodeError:
            out.add(ch)
    return "".join(sorted(out))


def unpinned(text: str) -> bool:
    """判据本体：有非 GBK 字形却没钉 stdio ⇒ True（纯函数，变异自证直接喂它）。"""
    return bool(_non_gbk(text)) and _PINNED.search(text) is None


def unpinned_cjk(text: str) -> bool:
    """第二档判据：**print 里带中文**却没钉 stdio ⇒ True。

    为什么补这一档（2026-10-01）：第一档只认「GBK 编不出的字形」（✓/✗/⚠…）——中文本身
    编得出 GBK，于是「打印中文、不钉 stdio」的入口一路绿灯，但它们写给**管道消费者**
    （CI 日志 / agent / 本仓测试）的是 **GBK 字节**，按 UTF-8 读就是乱码。实证：本轮给
    `scripts/interop_thirdparty_kit.py` 加中文修复指引后，新写的判据按 UTF-8 读它的输出，
    断言直接读成乱码而失败——乱码不是「谁看错了」，是**输出编码没有契约**。
    """
    return bool(_CJK_PRINT.search(text)) and _PINNED.search(text) is None


def _entries():
    for d in SCAN_DIRS:
        base = ROOT / d
        if base.is_dir():
            yield from sorted(p for p in base.glob("*.py") if p.name != "__init__.py")


def _pin_block(rel: str) -> str:
    """从真件里取出 `__main__` 分支的钉法原文（判据喂的是仓库真实写法，不是抄一遍）。"""
    lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
    i = max(j for j, ln in enumerate(lines) if ln.startswith("if __name__ =="))
    out = []
    for ln in lines[i + 1:]:
        if ln.strip() and not ln.startswith((" ", "\t")):   # 守卫分支结束
            break
        out.append(ln)
        if "reconfigure(encoding=" in ln:                   # 钉法到此为止（后面是 main()）
            break
    return textwrap.dedent("\n".join(out)) + "\n"


class StdioEncodingTest(unittest.TestCase):
    def test_every_entry_printing_cjk_pins_stdio(self):
        bad = []
        for path in _entries():
            if unpinned_cjk(path.read_text(encoding="utf-8")):
                bad.append(path.relative_to(ROOT).as_posix())
        self.assertEqual([], bad, "入口打印中文却没钉 UTF-8 stdio（修复指引：照 scripts/nf.py "
                                  "的写法，把 reconfigure(encoding=\"utf-8\") 放进 __main__ 分支）：%s"
                         % bad)

    def test_every_entry_printing_non_gbk_pins_stdio(self):
        bad = []
        for path in _entries():
            text = path.read_text(encoding="utf-8")
            if unpinned(text):
                bad.append("%s（非 GBK 字形：%s）" % (path.relative_to(ROOT).as_posix(),
                                                  _non_gbk(text)))
        self.assertEqual([], bad, "入口未钉 UTF-8 stdio（修复指引：照 scripts/nf.py 的写法，"
                                  "把 reconfigure(encoding=\"utf-8\") 放进 __main__ 分支）")

    def test_pin_survives_forced_gbk_stdio(self):
        """行为面：`PYTHONIOENCODING=gbk` 强行把子进程 stdio 钉成 GBK，真钉过的入口不受影响。

        两腿：① 真入口跑一遍（结论行 `✓/✗` 必须打得出来）；
        ② 把**该件 `__main__` 分支里的钉法原文**取出来 + 一个 `✗` 结论行，专打「失败也照打」。
        """
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = _GBK
        env.pop("PYTHONUTF8", None)
        rel = "scripts/build_verification_cards.py"
        p = subprocess.run([sys.executable, rel, "--check"], cwd=str(ROOT), capture_output=True,
                           env=env, timeout=600)
        out = p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        self.assertIn(p.returncode, (0, 1), "%s 在 GBK stdio 下异常退出：%s" % (rel, err))
        self.assertNotIn("UnicodeEncodeError", out + err, "%s 在 GBK stdio 下崩了" % rel)
        self.assertTrue(("✓" in out) or ("✗" in out), "%s 没打出结论行（判据无从生效）" % rel)

        src = "import sys\n" + _pin_block(rel) + "print('\u2717 boom')\n"
        q = subprocess.run([sys.executable, "-c", src], cwd=str(ROOT), capture_output=True,
                           env=env, timeout=120)
        self.assertEqual(0, q.returncode, q.stderr.decode("utf-8", "replace"))
        self.assertIn("✗", q.stdout.decode("utf-8", "replace"))

    def test_env_forced_gbk_really_breaks_an_unpinned_script(self):
        """自证：同一环境下**没钉**的小脚本确实崩——上面那条断言不是恒真。"""
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = _GBK
        env.pop("PYTHONUTF8", None)
        p = subprocess.run([sys.executable, "-c", "print('\\u2713 ok')"],
                           capture_output=True, env=env, timeout=120)
        self.assertNotEqual(0, p.returncode)
        self.assertIn("UnicodeEncodeError", p.stderr.decode("utf-8", "replace"))

    def test_predicate_catches_the_mutation(self):
        """变异自证：合成「有字形、没钉」的入口必须被判红，钉过的不许误报。"""
        self.assertTrue(unpinned("print('\u2713 done')\n"))
        self.assertFalse(unpinned("for _stream in (sys.stdout, sys.stderr):\n"
                                  "    _stream.reconfigure(encoding=\"utf-8\")\n"
                                  "print('\u2713 done')\n"))
        self.assertFalse(unpinned("print('plain ascii')\n"))

    def test_cjk_predicate_catches_the_mutation(self):
        """第二档变异自证：打印中文不钉必判红；钉过、纯 ASCII 不许误报。"""
        self.assertTrue(unpinned_cjk("print('结论：通过')\n"))
        self.assertFalse(unpinned_cjk("import sys\n"
                                      "sys.stdout.reconfigure(encoding=\"utf-8\")\n"
                                      "print('结论：通过')\n"))
        self.assertFalse(unpinned_cjk("print('all good')\n"))


class DocumentedModuleEntryTest(unittest.TestCase):
    """**文档里可照抄的模块入口**（`python -m core.X`）必须钉 UTF-8 stdio。

    依据（2026-10-01 实测，本判据的补面）：`SCAN_DIRS` 只扫 `scripts/` 与 `.github/scripts`，
    于是文档里那几条 `python -m core.X` 入口不在面内——实测 `core.text_hygiene`
    （`docs/text-hygiene.md`）与 `core.execution_drill`（`docs/42_M1_协议可执行性自测规范.md`）
    都没钉输出编码，Windows 管道下摘要/逐例结果以 **GBK 字节**吐出（`�ı� 3079 …`、
    `== execution_drill��… ==`），按 UTF-8 读全是乱码。两条已补钉法；本件保证「文档里点名的
    模块入口」都不会再漏。
    """

    #: 有意不钉的模块入口 → 理由（当前为空）
    EXEMPT: dict = {}
    REF = re.compile(r"python -m (core\.[a-z_][a-z0-9_]*)")
    #: 本件比 `_PINNED` 略宽：不要求前面有点号——`core.mcp_runtime` 是在 `serve_stdio()` 里
    #: 用 `reconfigure = getattr(stream, "reconfigure", None)` 再调用（等价钉法），
    #: 旧正则按 `.reconfigure(...)` 取面会把它误判成「没钉」。
    PIN = re.compile(r"reconfigure\(\s*encoding\s*=\s*[\"']utf-8[\"']")

    def _documented_entries(self):
        files = ([ROOT / "README.md", ROOT / "llms.txt"]
                 + sorted((ROOT / "docs").glob("*.md"))
                 + sorted((ROOT / "skills").rglob("*.md")))
        out = set()
        for p in files:
            if not p.is_file():
                continue
            for m in self.REF.finditer(p.read_text(encoding="utf-8", errors="replace")):
                out.add(m.group(1))
        return sorted(out)

    def test_documented_module_entries_pin_utf8_stdio(self):
        entries = self._documented_entries()
        self.assertGreaterEqual(len(entries), 2,
                                "没抽到文档里的模块入口（判据可能已失效）：%s" % entries)
        bad = []
        for dotted in entries:
            rel = "desktop/src/" + dotted.replace(".", "/") + ".py"
            p = ROOT / rel
            if not p.is_file():
                bad.append("%s（文档点名但文件不在场：%s）" % (dotted, rel))
                continue
            if dotted in self.EXEMPT:
                continue
            if not self.PIN.search(p.read_text(encoding="utf-8", errors="replace")):
                bad.append("%s（未钉 UTF-8 stdio）" % rel)
        self.assertEqual([], bad,
                         "文档里可照抄的模块入口没钉 UTF-8 stdio（Windows 管道下会是 GBK 乱码）：%s"
                         % bad)


if __name__ == "__main__":
    unittest.main()
