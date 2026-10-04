#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AOT 快线的**模块接线**判据：每个 .rs 都参与编译、每个模块都真的被用上。

为什么单列这条（2026-10-04 取证）：
- 快线 engine/rust/src 现有 **50 件 / 49 模块**，且对方仍在按面扩件（今天新增 audit / license_gate /
  coupling_metrics / workflow_policy 等）。**加文件但不 mod 声明**，该文件根本不参与编译——静默失效。
- 反过来，**声明了却没人引用**的模块是墓碑。Rust 只给 dead_code **warning**，而整个 crate
  **没有任何 #![deny(warnings)] / #![deny(dead_code)]**（实测全仓零命中）⇒ 没人看就等于没有判据。
- 两条都不需要 cargo（纯文本 + 正则），故不落进「cargo 不接常驻」那条决定的范围（那条防的是
  mid-edit 瞬时抖动；本判据只读源码，与编译状态无关）。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "engine" / "rust" / "src"

MOD_DECL = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+([a-z_][a-z0-9_]*)\s*;", re.M)


def modules_of(text: str) -> set:
    """→ 声明为独立文件的模块名（mod x; 形式；内联 mod x { 不算）。"""
    return set(MOD_DECL.findall(text))


def references_to(name: str, texts: dict, exclude: str) -> int:
    """→ 除 exclude 外其他文件对 name 的引用次数（name:: 与 ::name 两种形态都算）。"""
    pat = re.compile(r"(?:\b" + re.escape(name) + r"\s*::)|(?:::\s*" + re.escape(name) + r"\b)")
    return sum(len(pat.findall(t)) for stem, t in texts.items() if stem != exclude)


def wiring(files: dict) -> dict:
    """纯函数：{stem: 源码} → {undeclared, orphans, declared}（便于变异自证）。"""
    declared = set()
    for t in files.values():
        declared |= modules_of(t)
    undeclared = sorted(s for s in files if s not in declared and s not in ("main", "lib"))
    # 注意：只排除**模块自身所在文件**，不排除「声明它的文件」——后者通常正是调用方（main.rs），
    # 早期写成排除声明方，导致 main.rs 里的调用被吃掉、所有面模块被误判为墓碑（变异自证当场抓到）。
    orphans = sorted(n for n in declared
                     if n not in files or references_to(n, files, n) == 0)
    return {"undeclared": undeclared, "orphans": orphans, "declared": len(declared)}


def real_files() -> dict:
    return {p.stem: p.read_text(encoding="utf-8", errors="replace") for p in sorted(SRC.glob("*.rs"))}


class RustModuleWiringTest(unittest.TestCase):
    def test_every_source_file_is_declared_and_every_module_is_used(self):
        files = real_files()
        # 防「解析塌缩」：目录/正则一旦取错，下面的断言会变成空转的假绿。
        self.assertGreaterEqual(len(files), 40, "解析面塌缩（源件数异常）：%d" % len(files))
        got = wiring(files)
        self.assertGreaterEqual(got["declared"], 40, "解析面塌缩（模块数异常）：%s" % got)
        self.assertEqual([], got["undeclared"],
                         "这些 .rs 文件没有任何 mod 声明 ⇒ 根本不参与编译：%s" % got["undeclared"])
        self.assertEqual([], got["orphans"],
                         "这些模块被声明但无人引用 ⇒ 墓碑（Rust 只给 warning，无人看）"
                         "（修复指引：接上调用，或删除该模块）：%s" % got["orphans"])

    def test_wiring_predicate_catches_the_mutations(self):
        """变异自证：未声明文件 / 无人引用模块必须判红；正常接线与内联 mod 不许误伤。"""
        wired = {"main": "mod alpha;\nmod beta;\nfn m() { alpha::go(); beta::go(); }",
                 "alpha": "pub fn go() {}", "beta": "pub fn go() {}"}
        self.assertEqual({"undeclared": [], "orphans": [], "declared": 2}, wiring(wired))
        missing = dict(wired); missing["gamma"] = "pub fn go() {}"
        self.assertEqual(["gamma"], wiring(missing)["undeclared"])
        dead = dict(wired); dead["delta"] = "pub fn unused() {}"
        dead["main"] = wired["main"] + "\nmod delta;"
        self.assertEqual(["delta"], wiring(dead)["orphans"])
        inline = {"main": "mod alpha;\nmod tests { fn t() {} }\nfn m() { alpha::go(); }",
                  "alpha": "pub fn go() {}"}
        self.assertEqual({"undeclared": [], "orphans": [], "declared": 1}, wiring(inline))


if __name__ == "__main__":
    unittest.main()
