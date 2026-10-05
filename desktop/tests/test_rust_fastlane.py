#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rust 只读快线（engine/rust · nf-rs）与 Python 真源的逐字节对账门禁。

为什么（2026-10-03 取证）：crate 的 Cargo.toml 与 main.rs 都宣称「与 Python 真源逐字节对账」，
但全仓没有任何判据引用 nf-rs——即「AOT 快线输出与真源一致」是一句**无人核的声称**；一旦两侧
分叉（Python 改了 Merkle 域分隔或 JSON 序列化口径、Rust 没跟上），只有这条对账能抓到。
本判据把它做成常驻回归：

覆盖面（快线每加一个面，这里就得加一条 oracle——**不许有无人核的声称**）：
① receipts build / subjects / selfcheck：build 与 Python write_scope 落盘字节**逐字节相等**；
   subjects 逐行相对路径且**顺序即叶序**（顺序错，根就不一样）；selfcheck 退出码为 0；
② stats：与 nf stats --json **文档相等**，且除行尾外逐字节相等（真源经 Windows 控制台
   文本模式吐 CRLF，快线按仓内 LF 纪律输出——差异只在承载编码，不在内容）；
③ layers：与 nf layers --verify --json 同式（文档相等 + 除行尾外逐字节相等）；
④ conformance seal：真源报告对象喂入 → 封缄字节与 Python write 落盘字节**逐字节相等**；
⑤ conformance list + contract <id>：**每条已移植契约**的 (ok, detail, description, digest)
   与真源逐字段一致，且 list 里的 id 必须是真源在册契约（不许自造 id）；
⑥ density：stats / issues 与 nf asset density --json 文档相等（信封 kind/ok 尚未补齐）；
⑦ pyval reprf：IEEE-754 位模式 → CPython repr(float) 逐字节相等；
⑧ score：按真源口径喂「未移植扫描器的 issue 计数」→ 与 nf score --json 文档相等（除行尾外
   逐字节相等）。**口径坑留档**：`--signals` 喂的是**计数**不是布尔，喂 1 会得到 0.9 分/判成回归
   ——判据先断言前提（真源 4 项零 issue）再比文档，免得以错口径误判快线；
⑨ schema-lint：issues/stats 与 core.schema_lint.scan() 相等；schema-validate：messages 与
   core.schema_lint.subset_validate() 逐条相等（用多类违例的合成对，不只覆盖一条分支）；
⑩ 判别力自证：合成语料 / 改动裁决后输出必须变——否则这条比较是空转。

**面的来源（四取并，防「help 滞后」造成假全覆盖）**：① `--help` 的 usage 块；② 二进制的
**自述错误消息**（`conformance bogus` → `修复指引：seal | contract <id> | list`）；③ `PROBED_FACES`
探针表（help 未列但实测存在的面，删面即红）；④ **实现源码** `engine/rust/src/main.rs` 的顶层分派
（最可靠的一源：新增面一落源码即被看住）。实测 2026-10-03：`layers` / `conformance list` /
`conformance contract` / `pyval reprf` 均可跑却不在 usage 里——只靠 ① 会做成假全覆盖，
**`pyval` 正是靠 ④ 抓出来的**。

二进制不在场即跳过（crate 未构建不阻塞门禁；engine/rust/target 是忽略面，不入仓）。

与 engine/rust/check_parity.ps1 的关系：那边是**开发机仪器**（含 cargo build + 文件落盘 + sha256
逐项回显），这边是 **unittest discover 常驻面**（不依赖 pwsh/cargo，随 check12 自动跑）——同一判据
的两个面，判据实现同源于 core.receipts.write_scope 的落盘口径。
"""
import json
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import receipts  # noqa: E402

#: 已登记对账 oracle 的快线面（键 = 面路径，来源见 _all_faces）
COVERED_FACES = {
    "receipts build": "与 Python write_scope 落盘字节逐字节相等",
    "receipts subjects": "清单 + 顺序（即 Merkle 叶序）逐字节相等",
    "receipts selfcheck": "退出码 0（含逐条包含证明折叠回根）",
    "stats": "与 nf stats --json 文档相等（除行尾外逐字节相等）",
    "layers": "与 nf layers --verify --json 文档相等（除行尾外逐字节相等）",
    "conformance seal": "真源报告对象 → 封缄字节逐字节相等",
    "conformance list": "自描述清单；其 id 必须 ⊆ 真源在册契约（不许自造）",
    "conformance contract": "逐条 (ok, detail, description, digest) 与真源一致",
    "pyval reprf": "IEEE-754 位模式 → 与 CPython repr(float) 逐字节相等",
    "density": "stats/issues 与 nf asset density --json 文档相等（信封仍缺 kind/ok，见判据注）",
    "score": "按真源口径喂计数（4 个未移植扫描器各 0 issue）→ 与 nf score --json 文档相等",
    "schema-lint": "issues/stats 与 core.schema_lint.scan() 相等（核心层口径）",
    "schema-validate": "messages 与 core.schema_lint.subset_validate() 逐条相等",
    "verify-report": "28 条判据聚合 + 声明面 + root_digest + 渲染逐字节相等"
                     "（本线自算 20 条、其余 8 条喂子结果）",
    # 差分对账**入口**（不是判据面）：把内置 Python 解析器算出的 AST 事实导出，供与真源
    # `purity_scan._ast_facts` 逐文件比对。它的 oracle 在**本线自己的门禁**里——
    # `check_parity.ps1` 的**面 13e**（另见 `engine/rust/tools/check_ast_facts_inert.py`：
    # 对 23,489 条 sink 候选证明 unparser 括号差异不影响命中标志）。
    # 登记在此而非 `UNCOVERED_FACES`，是因为它**确有 oracle**，只是不在本文件内。
    "purity-facts": "差分对账入口；oracle = engine/rust/check_parity.ps1 面 13e "
                    "（raises/modules 逐字节一致；sinks 的 unparser 差异已证明无影响）",
    "purity-scan": "差分对账入口；oracle = engine/rust/check_parity.ps1 面 14 "
                   "（purity_scan.scan 的 issues + stats 逐字节一致）",
    "depth-scan": "差分对账入口；oracle = engine/rust/src/quality_depth_scan.rs 的 "
                  "tests::depth_scan_matches_truth_source（13 子扫描器 + 4 后置项，"
                  "规范 JSON 逐字节相同）",
    "code-metrics": "差分对账入口；oracle = engine/rust/check_parity.ps1 面 15 "
                    "（code_metrics.scan 的 issues + warns + stats 逐字节一致）",
}
#: 未登记对账的**例外**（逐条写明理由；表只许缩小，由 test_registry_is_not_stale 与
#: test_every_documented_face_has_an_oracle 两侧夹住）
UNCOVERED_FACES: dict = {}

CANDIDATES = (
    "engine/rust/target/release/nf-rs.exe",
    "engine/rust/target/release/nf-rs",
    "engine/rust/target/debug/nf-rs.exe",
    "engine/rust/target/debug/nf-rs",
)


def binary():
    """快线可执行件（release 优先，其次 debug）；未构建返回 None。"""
    for rel in CANDIDATES:
        p = ROOT / rel
        if p.is_file():
            return p
    return None


def python_bytes(root):
    """Python 真源的**落盘字节**（与 receipts.write_scope 同式，但不写盘）。"""
    doc = receipts.build_scope(str(root), scope="protocol")
    text = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def rust_run(bin_path, args):
    """跑一次快线子命令 → (CompletedProcess, 原始输出字节)。

    走**标准输出**（crate 文档：缺省写 stdout 的原始字节，不经换行转换）——不落中间文件，
    也就不受调用方临时目录写权限的影响。
    """
    proc = subprocess.run([str(bin_path)] + list(args), capture_output=True, timeout=600)
    return proc, proc.stdout


def rust_build(bin_path, root):
    """receipts build 面（逐字节对账用）。"""
    return rust_run(bin_path, ["receipts", "build", "--root", str(root)])


_REPORT: dict = {}


#: pyval reprf 的固定边界样本（±0 / 次正规 / 最大双精度 / ±inf / 规范 nan / 平局样本）
_REPRF_FIXED = (0x3FF0000000000000, 0x3FB999999999999A, 0x4005555555555555, 0x4341C37937E08000,
                0x3EE4F8B588E368F1, 0x0000000000000001, 0x7FEFFFFFFFFFFFFF, 0x8000000000000000,
                0x0000000000000000, 0x403B000000000000, 0x4330000000000001, 0x3FE0000000000000,
                0x7FF0000000000000, 0xFFF0000000000000, 0x7FF8000000000000, 0x3E112E0BE826D695,
                0x43E0000000000000, 0xC3E0000000000000, 0x41EFFFFFFFE00000)


def _reprf_cases(n_random=2000):
    """位模式样本 = 固定边界 + **定种子**伪随机（可复现）。

    随机集**排除指数全 1 的位模式**（NaN payload / inf 已由固定样本覆盖）：NaN 的 quiet 化与
    payload 保留在运行时/平台上有解释空间，不该拿来当逐字节判据。
    """
    rnd = random.Random(20261003)
    extra = []
    while len(extra) < n_random:
        b = rnd.getrandbits(64)
        if (b >> 52) & 0x7FF == 0x7FF:
            continue
        extra.append(b)
    return list(_REPRF_FIXED) + extra


def python_report():
    """真源一致性报告（**本进程内缓存**：cr.run 要跑 27 条契约，约 2.5 s；三个用例共用一份）。"""
    if "doc" not in _REPORT:
        from core import conformance_report as cr
        _REPORT["doc"] = cr.run(str(ROOT))
    return _REPORT["doc"]


def python_stats_bytes():
    """`nf stats --json` 的原始 stdout 字节（真源 CLI，不重写算法）。"""
    proc = subprocess.run([sys.executable, "scripts/nf.py", "stats", "--json"],
                          cwd=str(ROOT), capture_output=True, timeout=600)
    return proc, proc.stdout


def _documented_faces(bin_path):
    """`nf-rs --help` 里列出的面路径（**会滞后**，见模块头「已知盲区」）。"""
    proc = subprocess.run([str(bin_path), "--help"], capture_output=True, timeout=120)
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    return sorted(set(re.findall(r"(?m)^\s+nf-rs\s+([a-z]+(?:\s+[a-z]+)?)\s+--", text)))


def _self_declared_subfaces(bin_path):
    """从二进制的**自述错误消息**取子面——不依赖 help 文案，因此不会滞后。

    实测口径（2026-10-03）：`nf-rs conformance bogus` →
    `conformance 未知子命令：bogus（修复指引：seal | contract <id> | list）`。
    这正是 help 漏掉 `list` / `contract` 时补回覆盖面的来源。
    """
    out = set()
    proc = subprocess.run([str(bin_path), "conformance", "bogus"],
                          capture_output=True, timeout=120)
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    m = re.search(r"修复指引：([^）]+)）", text)
    if m:
        for part in m.group(1).split("|"):
            token = part.strip().split(" ")[0].strip("<>")
            if token:
                out.add("conformance " + token)
    return sorted(out)


#: help 未列、但**实测存在**的面（探针口径：`--help` 不报「未知命令」即在场；删掉即红）
PROBED_FACES = ("layers",)


def _probed_faces(bin_path):
    """探针面：`--help` 不报「未知命令」即在场（help 漏列时的兜底来源，删面即红）。"""
    out = []
    for face in PROBED_FACES:
        proc = subprocess.run([str(bin_path), face, "--help"], capture_output=True, timeout=120)
        text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
        if "未知命令" not in text:
            out.append(face)
    return out


def _source_faces(root=ROOT):
    """从 **实现源码** `engine/rust/src/main.rs` 的顶层分派取面名（不随 help 文案滞后）。

    口径：`fn run` 里 `match args[0].as_str() { … }` 的 8 空格缩进分支。
    实测价值（2026-10-03）：`pyval` 这个公开可用、但既不在 help、也没进探针表的面，
    就是这样被找出来的。源码不在场（例如只有 npm payload 的树）→ 返回空集（判据只做加法）。
    """
    p = Path(root) / "engine" / "rust" / "src" / "main.rs"
    if not p.is_file():
        return []
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"match args\[0\]\.as_str\(\)\s*\{(.*?)\n    \}", text, re.S)
    if not m:
        return []
    return sorted(set(re.findall(r'(?m)^\s{8}"([a-z][a-z0-9_-]*)"\s*=>', m.group(1))))


def _all_faces(bin_path, root=ROOT):
    """面集合 = help ∪ 自述子面 ∪ 探针 ∪ **实现源码**（四源取并，宁可多一枚也不漏）。"""
    return sorted(set(_documented_faces(bin_path))
                  | set(_self_declared_subfaces(bin_path))
                  | set(_probed_faces(bin_path))
                  | set(_source_faces(root)))


def _gated(face):
    """该面是否已登记 oracle／豁免（子面已登记也算——如 `conformance` 由 `conformance seal` 覆盖）。"""
    known = list(COVERED_FACES) + list(UNCOVERED_FACES)
    return face in known or any(k.startswith(face + " ") for k in known)


def _ungated_faces(faces):
    """未登记对账 oracle 的面（纯函数，便于变异自证）。"""
    return sorted(f for f in faces if not _gated(f))


class FaceCoverageRuleTest(unittest.TestCase):
    """变异自证：未登记面必判出来；已登记面不许误报。"""

    def test_predicate_flags_unregistered_and_spares_registered(self):
        self.assertEqual([], _ungated_faces(sorted(COVERED_FACES)))
        self.assertEqual(["conformance run"], _ungated_faces(["conformance run"]),
                         "新增面没被认出 —— 这条元判据是空转")


class FaceCoverageTest(unittest.TestCase):
    """**不许有无人核的面**：快线文档里列出的每个面都得有对账 oracle 或显式豁免。"""

    def setUp(self):
        self.bin = binary()
        if self.bin is None:
            self.skipTest("Rust 快线未构建")

    def test_every_documented_face_has_an_oracle(self):
        faces = _all_faces(self.bin)
        self.assertGreaterEqual(len(faces), 6, "面集合解析塌缩（判据可能已失效）：%s" % faces)
        self.assertGreaterEqual(len(faces), 4, "面清单解析塌缩（判据可能已失效）：%s" % faces)
        missing = _ungated_faces(faces)
        self.assertEqual([], missing,
                         "快线有面没有对账 oracle（修复指引：在 COVERED_FACES 登记并补判据，"
                         "或写进 UNCOVERED_FACES 说明理由）：%s" % missing)

    def test_source_parser_covers_every_documented_face(self):
        """源码面解析必须**覆盖 `--help` 里每一个文档面**——部分退化也要红，不只「解析全空」。

        为什么补这条：`test_source_face_parser_is_not_silently_broken` 只钉了下限（≥4），
        若对方改了排版让正则只匹配到一半，下限仍可能达标；而 `--help` ⊆ 源码解析这条关系式
        对**部分退化**同样敏感，且不依赖任何硬编码的数字。
        """
        if not (ROOT / "engine" / "rust" / "src" / "main.rs").is_file():
            self.skipTest("无 engine/rust 源码（例如只有 payload 的树）")
        documented = {f.split(" ")[0] for f in _documented_faces(self.bin)}
        missing = sorted(documented - set(_source_faces()))
        self.assertEqual([], missing, "源码面解析退化，漏掉文档面：%s" % missing)

    def test_source_face_parser_is_not_silently_broken(self):
        """源码面解析不得**静默失效**：`main.rs` 在场时至少要解析出 4 个面。

        为什么单列：解析靠的是「`match args[0].as_str()` + 8 空格缩进分支」这一形态；对方
        一旦换个排版，正则失配会返回空集——而空集**不会**让覆盖判据变红（它只会少看几个面）。
        这正是「判据悄悄失效」那一类，故用下限自己盯自己。
        """
        main_rs = ROOT / "engine" / "rust" / "src" / "main.rs"
        if not main_rs.is_file():
            self.skipTest("无 engine/rust 源码（例如只有 payload 的树）")
        faces = _source_faces()
        self.assertGreaterEqual(len(faces), 4, "源码面解析塌缩、判据已空转：%s" % faces)

    def test_registry_is_not_stale(self):
        faces = set(_all_faces(self.bin))
        stale = sorted(k for k in (list(COVERED_FACES) + list(UNCOVERED_FACES))
                       if k.split(" ")[0] not in faces)
        self.assertEqual([], stale, "登记表里有快线已不存在的面（表只许缩小）：%s" % stale)


class RustFastLaneParityTest(unittest.TestCase):
    def setUp(self):
        self.bin = binary()
        if self.bin is None:
            self.skipTest("Rust 快线未构建（engine/rust/target 是忽略面，先 cargo build --release）")

    def test_receipts_build_is_byte_identical_to_python(self):
        proc, got = rust_build(self.bin, ROOT)
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        self.assertEqual(python_bytes(ROOT), got,
                         "Rust 快线与 Python 真源的回执字节不一致（修复指引：对齐 "
                         "engine/rust 的 merkle / pyjson 口径，或改真源后重冻两侧）")

    def test_receipts_subjects_matches_python_list_and_order(self):
        """receipts subjects 面：逐行相对路径，**顺序即 Merkle 叶序**（顺序错了根就不一样）。"""
        proc, got = rust_run(self.bin, ["receipts", "subjects", "--root", str(ROOT)])
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        want = "".join("%s\n" % rel
                       for rel in receipts.protocol_subjects(str(ROOT))).encode("utf-8")
        self.assertEqual(want, got, "subjects 面与 Python 真源的清单/顺序不一致")

    def test_receipts_selfcheck_passes(self):
        proc = subprocess.run([str(self.bin), "receipts", "selfcheck", "--root", str(ROOT),
                               "--scope", "protocol"], capture_output=True, timeout=600)
        self.assertEqual(0, proc.returncode, proc.stdout.decode("utf-8", "replace")
                         + proc.stderr.decode("utf-8", "replace"))

    def test_layers_face_matches_python_document(self):
        """layers 面：与 nf layers --verify --json 文档相等，除行尾外逐字节相等。"""
        proc, got = rust_run(self.bin, ["layers", "--verify", "--json", "--root", str(ROOT)])
        if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
            self.skipTest("快线尚未实现 layers 面")
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        py = subprocess.run([sys.executable, "scripts/nf.py", "layers", "--verify", "--json"],
                            cwd=str(ROOT), capture_output=True, timeout=600)
        self.assertEqual(0, py.returncode, py.stderr.decode("utf-8", "replace"))
        self.assertEqual(json.loads(py.stdout.decode("utf-8")), json.loads(got.decode("utf-8")),
                         "layers 面与 Python 真源文档不等（值漂移）")
        self.assertEqual(py.stdout.replace(b"\r\n", b"\n"), got,
                         "layers 面除行尾外须逐字节相等")

    def test_stats_face_matches_python_document(self):
        """stats 面：与 `nf stats --json` **文档相等**，且除行尾外**逐字节相等**。

        行尾口径（实测 2026-10-03）：真源 CLI 经 Windows 控制台文本模式吐 CRLF（33 行全 CRLF），
        快线按仓内 LF 纪律输出；两者归一后逐字节相同、JSON 值全等——差异只在承载编码，不在内容。
        """
        proc, got = rust_run(self.bin, ["stats", "--root", str(ROOT), "--json"])
        if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
            self.skipTest("快线尚未实现 stats 面")
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        py, want = python_stats_bytes()
        self.assertEqual(0, py.returncode, py.stderr.decode("utf-8", "replace"))
        self.assertEqual(json.loads(want.decode("utf-8")), json.loads(got.decode("utf-8")),
                         "stats 面与 Python 真源文档不等（值漂移）")
        self.assertEqual(want.replace(b"\r\n", b"\n"), got,
                         "stats 面除行尾外须逐字节相等")

    def test_conformance_seal_is_byte_identical_to_python_report(self):
        """conformance seal 面：把**真源报告对象**喂进去，封缄字节须 == Python 落盘字节。

        真源侧不重写封缄公式：直接取 `conformance_report.run()` 的活报告，按 `write()` 的
        落盘口径（ensure_ascii=False / indent=2 / sort_keys=True / 末尾 LF）取字节。
        """
        rep = python_report()
        want = (json.dumps(rep, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "rows.json"
            inp.write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")
            proc, got = rust_run(self.bin, ["conformance", "seal", "--in", str(inp)])
            if proc.returncode == 2 and "未知" in proc.stderr.decode("utf-8", "replace"):
                self.skipTest("快线尚未实现 conformance 面")
            self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
            self.assertEqual(want, got, "conformance seal 与 Python 真源的封缄字节不一致")

            # 判别力自证：改一条裁决（并清掉它自带的摘要，避开差分核对分支）⇒ 字节必须变。
            rows = json.loads(json.dumps(rep))
            rows["contracts"][0]["ok"] = not rows["contracts"][0]["ok"]
            rows["contracts"][0].pop("digest", None)
            inp.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            proc2, got2 = rust_run(self.bin, ["conformance", "seal", "--in", str(inp)])
            self.assertEqual(0, proc2.returncode, proc2.stderr.decode("utf-8", "replace"))
            self.assertNotEqual(got, got2, "输入裁决变了输出却没变——这条对账是空转")

    def test_ported_contracts_match_python_rows(self):
        """已移植契约：逐条 (ok, detail, description, digest) 与真源一致；list 不许自造 id。"""
        proc, got = rust_run(self.bin, ["conformance", "list"])
        if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
            self.skipTest("快线尚未实现 conformance list 面")
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        ids = [ln.strip() for ln in got.decode("utf-8").splitlines() if ln.strip()]
        self.assertGreaterEqual(len(ids), 5, "已移植契约清单塌缩：%s" % ids)
        live = {c["id"]: c for c in python_report()["contracts"]}
        unknown = [i for i in ids if i not in live]
        self.assertEqual([], unknown, "快线自造了真源没有的契约 id：%s" % unknown)
        bad = []
        for cid in ids:
            p, out = rust_run(self.bin, ["conformance", "contract", cid, "--root", str(ROOT)])
            # ⚠️ **不能假设「已移植契约都该 rc=0」**：真源自己就会把某些契约判 ok=false
            # （实测 2026-10-03：`audit` 因并发会话改了 verify.sh 而正确报 FAIL）。
            # 早先写成「rc≠0 即不一致」，有两个后果：① 误报；② **判 false 的契约其行内容
            # 从未被比对过**——恰恰是这一侧没人核。现改为「rc 与真源 ok 对齐 + 行照比」。
            want_rc = 0 if live[cid].get("ok") else 1
            if p.returncode != want_rc:
                bad.append("%s rc=%d（真源 ok=%s，应 %d）%s"
                           % (cid, p.returncode, live[cid].get("ok"), want_rc,
                              p.stderr.decode("utf-8", "replace")[:80]))
                continue
            row = json.loads(out.decode("utf-8"))
            for key in ("ok", "detail", "description", "digest"):
                if row.get(key) != live[cid].get(key):
                    bad.append("%s.%s：快线=%r 真源=%r"
                               % (cid, key, row.get(key), live[cid].get(key)))
        self.assertEqual([], bad, "已移植契约与真源不一致：%s" % bad[:5])

    def test_unported_contract_fails_closed_with_guidance(self):
        """未移植契约必须**显式缺席**（rc≠0 + 修复指引），不许伪造空结论——ADR-0005 那条。"""
        proc, got = rust_run(self.bin, ["conformance", "list"])
        if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
            self.skipTest("快线尚未实现 conformance list 面")
        ported = {ln.strip() for ln in got.decode("utf-8").splitlines() if ln.strip()}
        live = {c["id"] for c in python_report()["contracts"]}
        unported = sorted(live - ported)
        if not unported:
            self.skipTest("真源契约已全部移植（本判据无需再跑）")
        p, out = rust_run(self.bin, ["conformance", "contract", unported[0], "--root", str(ROOT)])
        text = (p.stdout + p.stderr).decode("utf-8", "replace")
        self.assertNotEqual(0, p.returncode, "未移植契约竟返回成功（伪造了结论）：%s" % text[:120])
        self.assertIn("未移植", text, text[:160])
        self.assertIn("修复指引", text, text[:160])

    def test_schema_lint_face_matches_python_scan(self):
        """schema-lint 面：`issues`/`stats` 必须与 `core.schema_lint.scan()` 相等（核心层口径）。"""
        from core import schema_lint as sl
        proc, got = rust_run(self.bin, ["schema-lint", "--root", str(ROOT)])
        if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
            self.skipTest("快线尚未实现 schema-lint 面")
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        doc = json.loads(got.decode("utf-8"))
        extra = sorted(set(doc) - {"issues", "stats", "kind", "ok"})
        self.assertEqual([], extra, "schema-lint 面出现未预期的新键（口径漂移）：%s" % extra)
        issues, stats = sl.scan(str(ROOT))
        self.assertEqual(issues, doc.get("issues"), "schema-lint.issues 与真源不等")
        self.assertEqual(stats, doc.get("stats"), "schema-lint.stats 与真源不等")

    def test_schema_validate_face_matches_python_subset(self):
        """schema-validate 面：`messages` 必须与 `core.schema_lint.subset_validate()` **逐条相等**。

        用**多类违例**的合成对（缺必填 / 类型不符 / 不在枚举 / 未知字段），避免只覆盖一条分支。
        """
        from core import schema_lint as sl
        schema = {"type": "object",
                  "properties": {"a": {"type": "integer"},
                                 "b": {"type": "string", "enum": ["x", "y"]}},
                  "required": ["a", "c"], "additionalProperties": False}
        instance = {"a": "not-int", "b": "z", "d": 1}
        want = sl.subset_validate(instance, schema, "instance")
        self.assertEqual(4, len(want), "前提不成立：合成对应产生 4 条违例，实为 %s" % want)
        with tempfile.TemporaryDirectory() as tmp:
            sp, ip = Path(tmp) / "s.json", Path(tmp) / "i.json"
            sp.write_text(json.dumps(schema), encoding="utf-8")
            ip.write_text(json.dumps(instance), encoding="utf-8")
            proc, got = rust_run(self.bin, ["schema-validate", "--schema", str(sp),
                                            "--instance", str(ip)])
        if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
            self.skipTest("快线尚未实现 schema-validate 面")
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        self.assertEqual(want, json.loads(got.decode("utf-8")).get("messages"),
                         "schema-validate.messages 与真源逐条比对不一致")

    def test_score_face_matches_python_document(self):
        """score 面：按真源口径喂「计数」→ 输出必须与 `nf score --json` **文档相等**。

        **口径坑（2026-10-03 自证）**：`--signals` 喂的是**issue 计数**（`None`=扫描器不可用），
        不是「clean 布尔」——喂 `1` 等于喂「1 个 issue」，会得到 0.9 分/判成回归。本判据因此
        **先断言前提**（真源这 4 项确实零 issue），再比整篇文档 + 除行尾外逐字节。
        """
        py = subprocess.run([sys.executable, "scripts/nf.py", "score", "--json"],
                            cwd=str(ROOT), capture_output=True, timeout=600)
        self.assertEqual(0, py.returncode, py.stderr.decode("utf-8", "replace"))
        doc = json.loads(py.stdout.decode("utf-8"))
        names = ("purity_clean", "depth_clean")
        vals = {s["name"]: s["value"] for s in doc["current"]["signals"]}
        self.assertEqual({n: 1.0 for n in names}, {n: vals.get(n) for n in names},
                         "前提不成立：真源这 4 项并非零 issue，喂 0 计数会得到不同的分")
        with tempfile.TemporaryDirectory() as tmp:
            sig = Path(tmp) / "signals.json"
            sig.write_text(json.dumps({n: 0 for n in names}), encoding="utf-8")
            proc, got = rust_run(self.bin, ["score", "--root", str(ROOT), "--signals", str(sig)])
            if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
                self.skipTest("快线尚未实现 score 面")
            self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        self.assertEqual(doc, json.loads(got.decode("utf-8")), "score 面与真源文档不等")
        self.assertEqual(py.stdout.replace(b"\r\n", b"\n"), got, "score 面除行尾外须逐字节相等")

    def test_verify_report_face_matches_python_document(self):
        """verify-report 面：聚合/归一/摘要/渲染必须逐字节相等（含 `root_digest`）。

        口径：本线自算 `schema` / `doc_markers` / `baseline` / `self_stats` / `payload` / `assets_ledger` / `instruction` / `key_naming` / `intake` / `library` / `library_projection` / `rating` / `audit` / `workflow_policy` / `judgement_coverage` / `license` / `coupling` / `contract` / `knowledge` / `conformance` **二十条**，其余 8 条由
        `--results` 喂入真源的 `(issues, warns, stats)`——与 `score` 的 `--signals` 同一增量法
        （每移植一个扫描器，喂入面小一格，内核不动）。

        **`root_digest` 是这条判据的重点**：它的源串用 CPython `json.dumps` 的**默认分隔符**
        （`", "` / `": "`，**带空格**），既不是紧凑模式也不是 `indent=2`。差一个空格摘要就全变，
        而「摘要不同」这件事只有逐字节比对才抓得到。

        **成本（如实记录）**：基准侧要跑 `vr.build`，而它会跑全部 28 个扫描器——单这条判据约
        +14 s（整套从 ~6 s 到 ~20 s）。换来的是「门禁的机器可读出口」整篇逐字节受核，
        是全仓价值最高的一份产物；若嫌贵，可只在改 `engine/rust/src/verify_report.rs` 时跑。
        """
        from core import verify_report as vr  # noqa: PLC0415

        native = {"schema", "doc_markers", "baseline", "self_stats", "payload", "assets_ledger", "instruction", "key_naming", "intake", "library", "library_projection", "rating", "audit", "workflow_policy", "judgement_coverage", "license", "coupling", "contract", "knowledge", "conformance", "receipts", "drill_fidelity", "purity", "conformance_report", "code_metrics", "asset_contract"}
        # ⚠️ 这个集合**必须与快线的自算面同步**：`verify_report.call` 是 **native 优先**于 `--results`，
        # 所以少列一条不会立刻变红——但只要该条的分派将来断掉，就会静默回落到喂入值、**门禁照样全绿**。
        # 实测 2026-10-04：本集合停在 19 条（差 `conformance` / `receipts`），对账门里也是同一处陈旧。
        report = vr.build(str(ROOT))
        want = vr.render(report).encode("utf-8")
        # **只跑一遍真源**（早先 `_call` 一遍 + `build` 一遍 = 24 个扫描器跑两轮，判据从 5.6 s 涨到
        # 28.6 s）。内核拿 `issues` 做的只有两件事——**数长度**与**取前 3 条作样本**——故从报告
        # 反推等价的喂入值即可：样本照抄，余位补空串凑长度。
        res = {}
        for item in report["items"]:
            if item["id"] in native:
                continue
            pad = item["issues"] - len(item["sample"])
            entry = {"issues": list(item["sample"]) + [""] * pad,
                     "warns": [""] * item["warns"], "stats": item["stats"]}
            if item["status"] == "error":
                entry["status"] = "error"
            res[item["id"]] = entry
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "results.json"
            p.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
            proc, got = rust_run(self.bin, ["verify-report", "--root", str(ROOT),
                                            "--results", str(p), "--json"])
            if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
                self.skipTest("快线尚未实现 verify-report 面")
            self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        self.assertEqual(want.replace(b"\r\n", b"\n"), got.replace(b"\r\n", b"\n"),
                         "verify-report 面与真源报告不等（聚合/摘要/渲染，含 root_digest）")

    def test_density_face_matches_python_document(self):
        """density 面：`stats` 与 `issues` 必须与 `nf asset density --json` **文档相等**。

        **层差（2026-10-03 实测）**：`core.asset_density.scan()` 返回的是 `(issues, stats)` **元组**——
        `kind`/`ok` 是 **CLI 层**（`scripts/nf.py` 的 `asset density` 分支）加上的信封。快线该面
        对齐的是**核心层**，所以只有 issues/stats。本判据因此钉住已对齐的两个键，同时只放行
        `kind`/`ok` 这两种将来可能补齐的键——若出现**其它**新键即为口径漂移，当场叫停。
        """
        proc, got = rust_run(self.bin, ["density", "--root", str(ROOT)])
        if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
            self.skipTest("快线尚未实现 density 面")
        self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        py = subprocess.run([sys.executable, "scripts/nf.py", "asset", "density", "--json"],
                            cwd=str(ROOT), capture_output=True, timeout=600)
        self.assertEqual(0, py.returncode, py.stderr.decode("utf-8", "replace"))
        want = json.loads(py.stdout.decode("utf-8"))
        got_doc = json.loads(got.decode("utf-8"))
        allowed = {"issues", "stats", "kind", "ok"}
        extra = sorted(set(got_doc) - allowed)
        self.assertEqual([], extra, "density 面出现未预期的新键（口径漂移）：%s" % extra)
        self.assertEqual(want["stats"], got_doc.get("stats"), "density.stats 与真源不等")
        self.assertEqual(want["issues"], got_doc.get("issues"), "density.issues 与真源不等")

    def test_pyval_reprf_matches_cpython_repr(self):
        """pyval reprf：IEEE-754 位模式清单 → 与 CPython `repr(float)` **逐字节相等**。

        这是快线里**最不该自造**的一面：CPython 的浮点 repr 走最短往返算法（含正中平局）。
        判据直接拿 CPython 当真相：19 个固定边界（±0 / 次正规 / 最大双精度 / ±inf / nan / 平局）
        ＋ 2,000 个**定种子**伪随机位模式（排除 NaN payload），并断言输出行数等于样本数。
        """
        bits = _reprf_cases()
        self.assertGreaterEqual(len(bits), 2000, "样本塌缩（判据可能已失效）：%d" % len(bits))
        want = "".join(repr(struct.unpack("<d", struct.pack("<Q", b))[0]) + "\n" for b in bits)
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "bits.txt"
            inp.write_text("".join("%016x\n" % b for b in bits), encoding="utf-8")
            proc, got = rust_run(self.bin, ["pyval", "reprf", "--in", str(inp)])
            if proc.returncode != 0 and "未知" in proc.stderr.decode("utf-8", "replace"):
                self.skipTest("快线尚未实现 pyval 面")
            self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
        self.assertEqual(len(bits), len(got.splitlines()),
                         "快线输出行数与输入样本数不等（有样本被吞）")
        self.assertEqual(want.encode("utf-8"), got, "pyval reprf 与 CPython repr 不一致")

    def test_parity_holds_on_synthesized_corpus_and_detects_change(self):
        subs = receipts.protocol_subjects(str(ROOT))
        self.assertGreater(len(subs), 10, "协议回执语料面塌缩")
        with tempfile.TemporaryDirectory() as tmp:
            for rel in subs:
                dst = Path(tmp) / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, dst)
            proc, first = rust_build(self.bin, tmp)
            self.assertEqual(0, proc.returncode, proc.stderr.decode("utf-8", "replace"))
            self.assertEqual(python_bytes(tmp), first, "合成语料上两侧仍须逐字节一致")
            target = Path(tmp) / subs[0]
            target.write_bytes(target.read_bytes() + b"\n")
            proc2, second = rust_build(self.bin, tmp)
            self.assertEqual(0, proc2.returncode, proc2.stderr.decode("utf-8", "replace"))
            self.assertNotEqual(first, second, "改了语料输出却不变——这条对账是空转")
            self.assertEqual(python_bytes(tmp), second, "变异语料上两侧仍须逐字节一致")


if __name__ == "__main__":
    unittest.main()
