#!/usr/bin/env python3
"""图书馆许可证门（check33 第 6 面 · `core/license_gate.py`）双跑对账探针。

做法与 `text_hygiene_probe.py` 同构：**真源模块原文**（从快照 `desktop/src/core/` 导入，不改一个字节）
在**真仓快照**与**合成树**上各跑一遍，按**统一渲染规则**落日志，再与引擎侧 `LicenseGate` 的同式摘要比对。

渲染规则（两侧同一套，本探针是规则的唯一出处）：
    [FAIL] <issue>          ← 真源 issues（本面真源 stdout 里只有这一档）
    [WARN] <warning>        ← 真源 stats['warnings']（check33 只打印 FAIL，WARN 仍在台账里）
    [STAT] entries=N declared=N undeclared=<repr> unknown=<repr> no_inline=<repr> mismatched=<repr>

用法：
    python probes/license_gate_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                        [--expect-embedded <SelfTest.cs>]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

# 本探针**导入**真源模块（`from core import license_gate`）——关掉字节码写入，
# 免得测量快照里多出 `__pycache__/*.pyc`（第八十四片发现：那是测量噪声，不是真源改动）。
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_license_gate_golden.json")
_INDEX = """# 云端图书馆索引（探针合成语料）

| 编号 | 标题 | 形态/领域 | 投稿人 | 入库日期 | 许可 | 分级 | 状态 | 一句话 |
|---|---|---|---|---|---|---|---|---|
| NF-OK-1 | 样例一 | 世界 | a | 2026-01-01 | MIT | teen | active | 合规 |
| NF-EXPR-1 | 样例二 | 世界 | b | 2026-01-02 | MIT OR Apache-2.0 | teen | active | 表达式 |
| NF-REF-1 | 样例三 | 世界 | c | 2026-01-03 | LicenseRef-Custom-1 | teen | active | 自造 id |
| NF-UNDECL-1 | 样例四 | 世界 | d | 2026-01-04 | 未声明 | general | active | 未声明 |
| NF-MISMATCH-1 | 样例五 | 世界 | e | 2026-01-05 | MIT | general | active | 双源不一致 |
| NF-BADID-1 | 样例六 | 世界 | f | 2026-01-06 | GPL-3.0-only | general | active | 越词表 |
| NF-EMPTY-1 | 样例七 | 世界 | g | 2026-01-07 | x |
| NF-BADOP-1 | 样例八 | 世界 | h | 2026-01-08 | MIT AND AND Apache-2.0 | general | active | 运算符缺操作数 |
| NF-PAREN-1 | 样例九 | 世界 | i | 2026-01-09 | (MIT OR Apache-2.0 | general | active | 括号不配平 |
| NF-CHAR-1 | 样例十 | 世界 | j | 2026-01-10 | MIT © | general | active | 非法字符 |
"""

# 合成树：10 条登记行覆盖全部分支（合规 / 表达式 / 自造 id / 未声明 / 双源不一致 / 越词表 /
# 无许可列 / 运算符缺操作数 / 括号不配平 / 非法字符），条目文件覆盖内联声明的三种情形。
SYNTH_FILES = {
    "library/INDEX.md": _INDEX.encode("utf-8"),
    "library/NF-OK-1.md": "# 样例一\n\n> 许可：MIT\n".encode("utf-8"),
    "library/NF-EXPR-1.md": "# 样例二\n\n> 许可：MIT OR Apache-2.0\n".encode("utf-8"),
    "library/NF-REF-1.md": "# 样例三\n\n（无内联许可声明——应记 WARN）\n".encode("utf-8"),
    "library/NF-UNDECL-1.md": "# 样例四\n\n> 许可：未声明\n".encode("utf-8"),
    "library/NF-MISMATCH-1.md": "# 样例五\n\n> 许可：Apache-2.0\n".encode("utf-8"),
}


def load_source(snap: Path, module_name: str = "license_gate"):
    """导入**快照里那份**真源模块（原文，不复制不改写）。"""
    src = str(snap / "desktop" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return importlib.import_module(f"core.{module_name}")


def render(issues, stats) -> list:
    lines = ["[FAIL] %s" % i for i in issues]
    lines += ["[WARN] %s" % w for w in stats.get("warnings", [])]
    lines.append("[STAT] entries=%s declared=%s undeclared=%r unknown=%r no_inline=%r mismatched=%r"
                 % (stats["entries"], stats["declared"], stats["undeclared"], stats["unknown"],
                    stats["no_inline"], stats["mismatched"]))
    return lines


def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def write_tree(base: Path, files: dict) -> None:
    for rel, blob in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)


def decode_console(raw: bytes) -> str:
    for enc in ("utf-8", "gbk", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    lg = load_source(snap)
    results = {}

    iss, st = lg.scan(str(snap))
    real_log = render(iss, st)
    results["real"] = {"log": real_log, "digest32": digest32(real_log),
                       "fails": len(iss), "warns": len(st.get("warnings", []))}
    print(f"  真仓：FAIL {results['real']['fails']} · WARN {results['real']['warns']} "
          f"· 摘要 {results['real']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-lic-") as tmp:
        tree = Path(tmp)
        write_tree(tree, SYNTH_FILES)
        iss, st = lg.scan(str(tree))
    synth_log = render(iss, st)
    results["synthetic_mixed"] = {
        "log": synth_log, "digest32": digest32(synth_log),
        "fails": len(iss), "warns": len(st.get("warnings", [])),
        "files_b64": {rel: base64.b64encode(b).decode("ascii") for rel, b in SYNTH_FILES.items()},
    }
    print(f"  合成：FAIL {results['synthetic_mixed']['fails']} · WARN {results['synthetic_mixed']['warns']} "
          f"· 摘要 {results['synthetic_mixed']['digest32']}")

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-license-gate-golden/1",
            "generated": "2026-09-27",
            "source": "desktop/src/core/license_gate.py 原文导入执行（快照内那份），统一渲染规则见探针头",
            "snapshot": str(snap),
            "digest_rule": 'sha256("\\n".join(render(issues, stats)))[:32]  ← 与引擎 Result.LogDigest 同式',
            "cases": results,
        }
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"已写金标向量：{fixture_path}")
    else:
        if not fixture_path.exists():
            print(f"FAIL: 缺金标向量 {fixture_path}（用 --write-fixture 生成）")
            return 1
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        drift = []
        for key in ("real", "synthetic_mixed"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}（先看是否换了 HEAD，再决定是否重签金标）")
            return 1
        print("OK: 金标向量与真源本轮输出一致（两条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [rel for rel, b64 in results["synthetic_mixed"]["files_b64"].items() if b64 not in cs]
        for key in ("real", "synthetic_mixed"):
            if results[key]["digest32"] not in cs:
                missing.append(f"<{key} 摘要>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 合成树 base64 与两条摘要均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        rows = json.loads(decode_console(proc.stdout))["rows"]
        docs = [r for r in rows if r["name"].startswith("许可证门")]
        if len(docs) != 2:
            print(f"FAIL: 引擎侧许可证门钉应为 2 条，实得 {len(docs)}")
            return 1
        bad = []
        for row in docs:
            case = "real" if "真仓" in row["name"] else "synthetic_mixed"
            m = re.search(r"摘要 (\w{32})", row["detail"])
            got = m.group(1) if m else None
            want = results[case]["digest32"]
            print(f"  [{'OK ' if got == want else '不一致'}] 引擎 {case}: {got} / 真源 {want}")
            if got != want:
                bad.append(case)
        if bad:
            print(f"FAIL: 引擎侧与真源输出不一致：{bad}")
            return 1
        print("OK: 引擎侧许可证门输出与真源逐字节同摘要（真材料 + 合成树）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
