#!/usr/bin/env python3
"""编码卫生（check33 第 9 面 · `core/text_hygiene.py`）双跑对账探针。

做法与 `doc_completeness_probe.py` 同构：把真源模块**原文**复制到临时路径后当脚本执行
（`python <tmp>/text_hygiene.py <tree>`，与真源 `__main__` 完全同一段代码），在**真仓快照**与
**合成树**上各跑一遍，再与引擎侧 `TextHygiene` 的同式摘要比对。

用法：
    python probes/text_hygiene_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                        [--expect-embedded <TextHygiene.cs 或 SelfTest.cs>]

口径：
  * 摘要 = `sha256("\\n".join(stdout.splitlines()))[:32]`（与引擎 `Result.LogDigest` 同式）；
  * 合成树内容以 **base64** 记在 fixture 里（含非法 UTF-8 字节，纯文本表示不了）；
    引擎自检钉用同一批 base64 落盘 → 两侧比的是**同一棵树**。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import _paths  # 默认路径唯一出处（探针可移植）

try:  # 控制台默认可能是 GBK：日志含中文与符号，输出不能因编码崩掉
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_text_hygiene_golden.json")
SOURCE_REL = "desktop/src/core/text_hygiene.py"

BOM = b"\xef\xbb\xbf"

# 合成树：每条规则各命中一次（与 SelfTest.TextHygieneCases 里的 base64 常量必须逐字节相同）
SYNTH_FILES = {
    ".gitattributes": "* text=auto eol=crlf\n".encode("utf-8"),
    "a_bom.md": BOM + "正文\n".encode("utf-8"),
    "b_crlf.md": "行一\r\n行二\r\n".encode("utf-8"),
    "d_dup.json": '{"a":1,"a":2,"k":3}\n'.encode("utf-8"),
    "e_key.json": '{"好\u00a0键":1}\n'.encode("utf-8"),
    "f_non_nfc.json": '{"e\u0301":1}\n'.encode("utf-8"),
    "g_ok.json": '{"good_key":1}\n'.encode("utf-8"),
    "h_binary.bin": b"\x00\x01\x02binary-ish\n",
    "_cov_tmp.json": '{"excluded\u3000key":1}\n'.encode("utf-8"),
    ".git/inside.md": "排除目录里的件不该被扫\n".encode("utf-8"),
    "community/示例包/protocol.yaml": "id: 示例包\nversion: 1.0\n".encode("utf-8"),
    "community/示例包/modules/M01.md": "# 模块 M01 · 示例\n".encode("utf-8"),
}

# 单独的「不可约尾」用例：非法 UTF-8 的具体文案来自各自编解码器（Python 3.11 的
# `'utf-8' codec can't decode byte 0xff in position 0: invalid start byte`），判定一致、
# 文案不可约——故本用例只比「条数 + 摘要行 + 问题前缀」，不比整行摘要值。
BAD_UTF8_FILES = {
    ".gitattributes": "* text=auto eol=lf\n".encode("utf-8"),
    "c_bad.txt": b"\xff\xfeAB\n",
}
BAD_UTF8_PREFIX = "c_bad.txt 不是合法 UTF-8："


def digest32(stdout_text: str) -> str:
    return hashlib.sha256("\n".join(stdout_text.splitlines()).encode("utf-8")).hexdigest()[:32]


def write_tree(base: Path, files: dict) -> None:
    for rel, blob in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)


def run_source(snap: Path, tree: Path) -> tuple[int, str, str]:
    """把真源模块原文复制到临时路径后执行（不改一个字节），cwd = 被测树。"""
    with tempfile.TemporaryDirectory(prefix="nf-th-src-") as srcdir:
        copy = Path(srcdir) / "text_hygiene.py"
        shutil.copyfile(snap / SOURCE_REL, copy)
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        proc = subprocess.run([sys.executable, str(copy), str(tree)], cwd=str(tree), env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=900)
    return proc.returncode, proc.stdout, proc.stderr


def summarize(exit_code: int, stdout: str) -> dict:
    lines = stdout.splitlines()
    return {
        "python_exit": exit_code,
        "digest32": digest32(stdout),
        "fails": sum(1 for l in lines if l.startswith("[FAIL]")),
        "summary": lines[0] if lines else "",
        "log": lines,
    }


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
    ap.add_argument("--cli", default="", help="nf-dotnet：读引擎自检钉的摘要做比对")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="", help="机械导出纪律：校验这些 base64 已写进该 C# 文件")
    args = ap.parse_args()

    snap = Path(args.snap)
    if not (snap / SOURCE_REL).is_file():
        print(f"FAIL: 快照里没有 {SOURCE_REL}")
        return 1

    results = {}
    code, out, err = run_source(snap, snap)
    if err.strip():
        print("  真源 stderr：" + err.strip().splitlines()[-1][:200])
    results["real"] = summarize(code, out)
    print(f"  真仓：exit={code} · {results['real']['summary']} · [FAIL] {results['real']['fails']} "
          f"· 摘要 {results['real']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-th-tree-") as tmp:
        tree = Path(tmp)
        write_tree(tree, SYNTH_FILES)
        code, out, err = run_source(snap, tree)
    if err.strip():
        print("  真源 stderr：" + err.strip().splitlines()[-1][:200])
    results["synthetic_mixed"] = summarize(code, out)
    results["synthetic_mixed"]["files_b64"] = {
        rel: base64.b64encode(blob).decode("ascii") for rel, blob in SYNTH_FILES.items()
    }
    print(f"  合成：exit={code} · {results['synthetic_mixed']['summary']} "
          f"· [FAIL] {results['synthetic_mixed']['fails']} · 摘要 {results['synthetic_mixed']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-th-bad-") as tmp:
        tree = Path(tmp)
        write_tree(tree, BAD_UTF8_FILES)
        code, out, err = run_source(snap, tree)
    results["synthetic_bad_utf8"] = summarize(code, out)
    results["synthetic_bad_utf8"]["irreducible_tail"] = True
    results["synthetic_bad_utf8"]["prefix"] = BAD_UTF8_PREFIX
    results["synthetic_bad_utf8"]["files_b64"] = {
        rel: base64.b64encode(blob).decode("ascii") for rel, blob in BAD_UTF8_FILES.items()
    }
    print(f"  坏UTF8：exit={code} · {results['synthetic_bad_utf8']['summary']} "
          f"· [FAIL] {results['synthetic_bad_utf8']['fails']} · 前缀同判（尾不可约）")

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-text-hygiene-golden/1",
            "generated": "2026-09-27",
            "source": f"{SOURCE_REL} 原文复制后按脚本执行（真源 __main__ 同一段代码，逐字节 stdout）",
            "snapshot": _paths.portable(snap),
            "digest_rule": 'sha256("\\n".join(stdout.splitlines()))[:32]  ← 与引擎 Result.LogDigest 同式',
            "cases": results,
        }
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n"：**必须**——Path.write_text 在 Windows 上会把 \n 翻成 \r\n，
        # 于是复基线重生成的夹具变成 CRLF，入包即被「包内卫生」判红（第一百二十二片实测：
        # _prose_lint/_regression_score/_text_hygiene 三份夹具全 CRLF，58/502/64 行）。
        fixture_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8", newline="\n")
        print(f"已写金标向量：{fixture_path}")
    else:
        if not fixture_path.exists():
            print(f"FAIL: 缺金标向量 {fixture_path}（用 --write-fixture 生成）")
            return 1
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        drift = []
        for key in ("real", "synthetic_mixed", "synthetic_bad_utf8"):
            want, got = fixture["cases"][key], results[key]
            if want.get("irreducible_tail"):
                same = (want["python_exit"] == got["python_exit"]
                        and want["summary"] == got["summary"]
                        and want["fails"] == got["fails"]
                        and want["prefix"] == got["prefix"]
                        and sum(1 for l in got["log"] if l.startswith("[FAIL] " + want["prefix"])) == 1)
                print(f"  [{'OK ' if same else '漂移'}] {key}: 不可约尾——比较条数/摘要/前缀"
                      f"（真源 exit={want['python_exit']} FAIL={want['fails']}）")
            else:
                same = want["digest32"] == got["digest32"]
                print(f"  [{'OK ' if same else '漂移'}] {key}: 金标 {want['digest32']} / 本轮 {got['digest32']}")
            if not same:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}（先看是否换了 HEAD，再决定是否重签金标）")
            return 1
        print("OK: 金标向量与真源本轮输出一致（两条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [rel for rel, b64 in results["synthetic_mixed"]["files_b64"].items() if b64 not in cs]
        for key in ("synthetic_bad_utf8",):
            for rel, b64 in results[key]["files_b64"].items():
                if b64 not in cs:
                    missing.append(f"<{key}:{rel}>")
        for key in ("real", "synthetic_mixed"):
            if results[key]["digest32"] not in cs:
                missing.append(f"<{key} 摘要>")
        if BAD_UTF8_PREFIX not in cs:
            missing.append("<坏UTF8 前缀>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 合成树 base64 与两条摘要均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        try:
            rows = json.loads(decode_console(proc.stdout))["rows"]
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: 读不出引擎自检 JSON：{exc}")
            return 1
        docs = [r for r in rows if r["name"].startswith("编码卫生")]
        if len(docs) != 3:
            print(f"FAIL: 引擎侧编码卫生钉应为 3 条，实得 {len(docs)}")
            return 1
        bad = []
        for row in docs:
            case = ("real" if "真仓" in row["name"]
                    else "synthetic_bad_utf8" if "坏UTF8" in row["name"]
                    else "synthetic_mixed")
            if case == "synthetic_bad_utf8":
                ok = BAD_UTF8_PREFIX in row["detail"] and "1 条" in row["detail"]
                print(f"  [{'OK ' if ok else '不一致'}] 引擎 {case}: 前缀同判断言在场")
                if not ok:
                    bad.append(case)
                continue
            m = re.search(r"摘要 (\w{32})", row["detail"])
            engine_digest = m.group(1) if m else None
            want = results[case]["digest32"]
            print(f"  [{'OK ' if engine_digest == want else '不一致'}] 引擎 {case}: {engine_digest} / 真源 {want}")
            if engine_digest != want:
                bad.append(case)
        if bad:
            print(f"FAIL: 引擎侧与真源输出不一致：{bad}")
            return 1
        print("OK: 引擎侧编码卫生输出与真源逐字节同摘要（真材料 + 合成树）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
