# -*- coding: utf-8 -*-
"""写盘闸门的**旗标级机械普查**：不让「不带 `--write` 却写仓库」的旗标再漏网。

为什么（2026-10-01 取证）：闸门此前两轮都是**按名字**清的——先按已知的写旗标名（`--write*`
/ `--re-sign` / `--fix`），再按**动词**（deprecate/reindex/new…）。两轮都没做「把 argparse
面里的**每个**旗标拿去对写 sink」这一步，于是漏了三个**名字里没有写语义**却直接改仓库的旗标：

- `nf module types --harvest` → `protocol/event_registry.json`
- `nf pipeline dryrun --write-advisory` → `protocol/pipeline_advisory.json`
- `nf combine plan --certify` → `protocol/combo_certificates.json`

外加一个与已入闸 `--out` 同类的「写你自己命名的文件」旗标 `nf assemble --save`（可给仓库相对
路径 ⇒ 在 `nf shell --exec` 的**粘贴面**里能落仓）。本件把「旗标 → 写 sink」这一步做成常驻
判据：新增一个写旗标而不入闸，本判据就红。

口径（防误杀）：只把**该旗标自己的语句块**（按缩进界定）里的 sink 算它的；块内若还有
`if args.write:` / `--write-advisory` / `--trace` 这类**内层守卫**，或该命令本身在
`CONFIRM_VERBS` 里（动词已入闸），就不算它——这些是**已复核的假阳性**，逐条列在
`REVIEWED_FALSE_POSITIVES` 里，集合必须**恰好相等**（既不许新漏，也不许 allowlist 腐烂）。
"""
import ast
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NF = ROOT / "scripts" / "nf.py"
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import terminal as term  # noqa: E402

#: 写 sink（与旗标语义无关的**行为**证据）
SINKS = re.compile(
    r"write\s*=\s*True|atomic_write\.|open\([^)]*['\"]w|write_text\(|write_bytes\("
    r"|os\.replace\(|os\.remove\(|os\.unlink\(|shutil\.move\(|makedirs\(|os\.mkdir\("
    r"|save_module\(|save_asset|save_cache\(|_write_|write_projection\(|write_region\("
    r"|save_baseline\(|write_log\(|write_usage\(|write_order\(|write_scope\("
    r"|write_state\(|set_status\(|register\(|apply\(ROOT, write"
)

#: 已复核的**假阳性**（旗标本身不写；写者另有其人）。集合必须与实测**恰好相等**。
REVIEWED_FALSE_POSITIVES = {
    "--backlog": "写调用嵌套在 `if args.write:` 之下（真守卫是 --write）",
    "--scope": "同上（receipts --write 才写）",
    "--by": "位于 CONFIRM_VERBS 的 `library supersede` 动词里",
    "--entry": "同上（library deprecate/restore/supersede 动词已入闸）",
    "--key": "位于 CONFIRM_VERBS 的 `asset deprecate/rm` 动词里",
    "--label": "只是 `--certify` 的实参；写者是 --certify（已入闸）",
    "--note": "同上",
    "--pipeline": "块内写调用由 `--write-advisory` 守卫（已入闸）",
    "--check": "块内写调用由 `--trace` 守卫（assemble；已入闸）",
}


def _long_opts(node: ast.Call) -> list:
    return [a.value for a in node.args
            if isinstance(a, ast.Constant) and isinstance(a.value, str)
            and a.value.startswith("--")]


def flags_with_write_sinks(src: str) -> dict:
    """→ `{旗标: [命中行]}`：把每个 argparse 旗标拿去对**它自己的语句块**里的写 sink。"""
    tree = ast.parse(src)
    lines = src.splitlines()
    indents = [len(x) - len(x.lstrip()) for x in lines]

    def block(i: int) -> str:
        base = indents[i]
        out = [lines[i]]
        for j in range(i + 1, len(lines)):
            if lines[j].strip() and indents[j] <= base:
                break
            out.append(lines[j])
        return "\n".join(out)

    dests = {}
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "add_argument"):
            continue
        opts = _long_opts(n)
        if not opts:
            continue
        dest = opts[0][2:].replace("-", "_")
        for kw in n.keywords:
            if kw.arg == "dest" and isinstance(kw.value, ast.Constant):
                dest = kw.value.value
        dests.setdefault(dest, set()).update(opts)

    out = {}
    for dest, opts in sorted(dests.items()):
        pat = re.compile(r"args\.%s\b|getattr\(args,\s*['\"]%s['\"]"
                         % (re.escape(dest), re.escape(dest)))
        for i, ln in enumerate(lines):
            if pat.search(ln) and SINKS.search(block(i)):
                for o in sorted(opts):
                    out.setdefault(o, []).append(i + 1)
    return out


class WriteFlagGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = NF.read_text(encoding="utf-8")
        cls.hits = flags_with_write_sinks(cls.src)
        cls.gated = set(term.CONFIRM_FLAGS) | {f for _c, f in term.CONFIRM_FLAG_PAIRS}

    def test_scanner_is_not_vacuous(self):
        self.assertGreater(len(self.hits), 5, "写 sink 普查没扫到东西（判据可能已失效）")

    def test_no_ungated_writer_flag(self):
        ungated = sorted(set(self.hits) - self.gated)
        self.assertEqual(sorted(REVIEWED_FALSE_POSITIVES), ungated,
                         "出现**未复核**的写旗标（要么入闸，要么写进 REVIEWED_FALSE_POSITIVES "
                         "并说明为什么它不写）：%s"
                         % sorted(set(ungated) - set(REVIEWED_FALSE_POSITIVES)))

    def test_gate_tables_still_cover_the_known_writers(self):
        for flag in ("--write", "--write-baseline", "--fix",
                     "--harvest", "--write-advisory", "--certify", "--save"):
            self.assertIn(flag, term.CONFIRM_FLAGS, "%s 掉出闸门表" % flag)
        for pair in (("interop", "--all"), ("assemble", "--trace"), ("assemble", "--session")):
            self.assertIn(pair, term.CONFIRM_FLAG_PAIRS, "%s 掉出组合表" % (pair,))

    def test_every_gate_entry_exists_in_the_cli_surface(self):
        """闸门三表的每一条都必须是**真实命令面**的条目（2026-10-01 清死条目时补的判据）。

        取证：清出 5 条死条目——`--tag` / `--push` / `--delete` / `--rm` / `--re-sign`（`nf` 的
        argparse 面里根本没有；`nf release` 只有 `--fast`，`nf asset baseline` 的重签旗标是
        `--write`）。死条目不会漏拦，但会让**文档口径**与真实面分叉：读者按文档敲 `--re-sign`
        只会得到用法错误。本件把「表里有的必须真存在」钉住——将来再写错旗标名会当场红。
        """
        src = (ROOT / "scripts" / "nf.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        flags, parsers = set(), set()
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
                continue
            if n.func.attr == "add_argument":
                flags |= {a.value for a in n.args if isinstance(a, ast.Constant)
                          and isinstance(a.value, str) and a.value.startswith("--")}
            elif n.func.attr == "add_parser" and n.args:
                first = n.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    parsers.add(first.value)
        bad = [f for f in term.CONFIRM_FLAGS if f not in flags]
        self.assertEqual([], bad, "闸门旗标表含 argparse 面里没有的旗标（死条目）：%s" % bad)
        for cmd, flag in term.CONFIRM_FLAG_PAIRS:
            self.assertIn(flag, flags, "组合表旗标不存在：%s" % flag)
            self.assertIn(cmd, parsers, "组合表命令不存在：%s" % cmd)
        for cmd, _sub in term.CONFIRM_VERBS:
            self.assertIn(cmd, parsers, "动词表命令不存在：%s" % cmd)

    def test_every_verb_pair_is_a_real_subcommand_face(self):
        """动词表里的 **(命令, 子命令)** 必须真是可跑的命令面——**用 CLI 自己当裁判**。

        为什么不用静态解析（2026-10-01 实测）：`nf.py` 里 `add_subparsers()` 的容器变量名会被
        复用（`dsub` 既是 design 也是 decisions 的容器、`asset` 的字面量子命令表也不完整），
        首版静态映射把 `asset rm|deprecate|restore`、`decisions reindex|verify` 全判成「不存在」
        ——**全是假红**。改用 `--help` 退出码当裁判（0 = 这条命令面真的在），既短又不会因 AST
        花样而误判。
        """
        for cmd, sub in term.CONFIRM_VERBS:
            argv = [cmd, sub, "--help"] if sub else [cmd, "--help"]
            p = subprocess.run([sys.executable, str(ROOT / "scripts" / "nf.py"), *argv],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=str(ROOT), timeout=120)
            self.assertEqual(0, p.returncode,
                             "动词表条目不是真实命令面：nf %s（修复指引：改成真命令，"
                             "或从 CONFIRM_VERBS 删掉）\n%s" % (" ".join(argv),
                                                              (p.stderr or "")[:200]))


if __name__ == "__main__":
    unittest.main()
