#!/usr/bin/env python3
"""扩展策略 / bump 迁移门禁（`verify.sh check30`）双跑对账探针。

真源 check30 **没有 `nf` 子命令面**（只被 verify.sh 消费），故按本工程既有做法把 **verify.sh 里的
内联 Python 原文抽出来**执行，与引擎侧 `ExtensionPolicy` 同一棵树双跑、比同式摘要。

三条用例：
  1. `real`        —— 真仓**导出态**（无 `.git`）：真源 `git diff` 失败 → diff 面恒空，两侧应逐字节同判；
  2. `synthetic`   —— 合成树（EXTENSION.md 缺若干判据词 / 完全缺件）；
  3. `boundary`    —— **临时 git 仓库**里把一个版本字段 bump：真源立刻报 `bump 文件 1` + FAIL，
                       而引擎**明示不判**该面（BCL-only 不接 VCS）——本用例证明边界是真的，不是挡箭牌。

用法：
    python probes/extension_policy_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                            [--expect-embedded <SelfTest.cs>]
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

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_extension_policy_golden.json")
GOOD_EXT = """# 扩展策略

字段级新增与结构 bump 的区别；本档即「迁移记录」体例说明。

- additive：只增不删
- editorial：措辞与排版
- 结构 bump：结构性演进
- 派生三问：谁读、读什么、坏了怎么办
"""

PARTIAL_EXT = "# 扩展策略\n\n只写了 additive 与 editorial。\n"

SYNTH_FILES = {
    "protocol/EXTENSION.md": PARTIAL_EXT.encode("utf-8"),
}

BOUNDARY_FILES = {
    "protocol/EXTENSION.md": GOOD_EXT.encode("utf-8"),
}


def extract_check30(verify_sh: Path) -> str:
    text = verify_sh.read_text(encoding="utf-8")
    start = text.index("check30(){")
    m = re.search(r"<<'PYEOF'[^\n]*\n(.*?)\nPYEOF\n", text[start:], re.S)
    if not m:
        raise SystemExit("找不到 check30 的 PYEOF 片段")
    return m.group(1)


def digest32(text: str) -> str:
    return hashlib.sha256("\n".join(text.splitlines()).encode("utf-8")).hexdigest()[:32]


def run_source(body: str, tree: Path) -> tuple[int, str, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    proc = subprocess.run([sys.executable, "-c", body], cwd=str(tree), env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=300)
    return proc.returncode, proc.stdout, proc.stderr


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


def summarize(exit_code: int, stdout: str) -> dict:
    lines = stdout.splitlines()
    return {"python_exit": exit_code, "digest32": digest32(stdout),
            "fails": sum(1 for l in lines if l.startswith("[FAIL]")),
            "log": lines}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    body = extract_check30(snap / "verify.sh")
    print(f"check30 源码片段：{len(body.splitlines())} 行 · 快照有 .git：{(snap / '.git').is_dir()}")
    results = {}

    code, out, err = run_source(body, snap)
    results["real"] = summarize(code, out)
    print(f"  真材（导出态）：exit={code} · {results['real']['log'][0] if results['real']['log'] else ''} "
          f"· 摘要 {results['real']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-ext-syn-") as tmp:
        tree = Path(tmp)
        write_tree(tree, SYNTH_FILES)
        code, out, err = run_source(body, tree)
    results["synthetic"] = summarize(code, out)
    results["synthetic"]["files_b64"] = {
        rel: base64.b64encode(b).decode("ascii") for rel, b in SYNTH_FILES.items()
    }
    print(f"  合成（缺判据词）：exit={code} · {results['synthetic']['log'][0]} "
          f"· [FAIL] {results['synthetic']['fails']} · 摘要 {results['synthetic']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-ext-git-") as tmp:
        tree = Path(tmp)
        write_tree(tree, BOUNDARY_FILES)
        for rel in ("02_联动注册表.md", "desktop/src/core/registry.json"):
            dst = tree / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(snap / rel, dst)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")

        def git(*argv):
            return subprocess.run(["git", "-C", str(tree), "-c", "user.email=nf@probe",
                                   "-c", "user.name=nf-probe", *argv],
                                  capture_output=True, text=True, env=env)

        git("init", "-q")
        git("add", "-A")
        git("commit", "-qm", "base")
        doc = tree / "02_联动注册表.md"
        text = doc.read_text(encoding="utf-8")
        old = 'registry_schema_version: "2"'
        if old not in text:
            print("FAIL: 夹具里找不到预期的版本字段行")
            return 1
        doc.write_text(text.replace(old, 'registry_schema_version: "3"', 1), encoding="utf-8", newline="")
        code, out, err = run_source(body, tree)
    results["boundary"] = summarize(code, out)
    print(f"  边界（临时 git 仓 · bump 了版本字段）：真源 exit={code} · "
          f"{results['boundary']['log'][0] if results['boundary']['log'] else ''} "
          f"· [FAIL] {results['boundary']['fails']}（**引擎该态明示不判**）")

    # 第一百零五片：bump 面**可判**了——调用方把 `git diff HEAD` 的标准统一 diff 交给引擎
    # （引擎仍不接 VCS）。两条：bump 无四步记录（真源 FAIL）/ bump 带四步记录（真源通过）。
    for name, add_record in (("judged_no_record", False), ("judged_with_record", True)):
        with tempfile.TemporaryDirectory(prefix="nf-ext-judged-") as tmp:
            tree = Path(tmp)
            write_tree(tree, BOUNDARY_FILES)
            for rel in ("02_联动注册表.md", "desktop/src/core/registry.json"):
                dst = tree / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(snap / rel, dst)
            env = dict(os.environ, PYTHONIOENCODING="utf-8")

            def git(*argv):
                return subprocess.run(["git", "-C", str(tree), "-c", "user.email=nf@probe",
                                       "-c", "user.name=nf-probe", *argv],
                                      capture_output=True, text=True, env=env)

            git("init", "-q")
            git("add", "-A")
            git("commit", "-qm", "base")
            doc = tree / "02_联动注册表.md"
            text = doc.read_text(encoding="utf-8")
            doc.write_text(text.replace('registry_schema_version: "2"', 'registry_schema_version: "3"', 1),
                           encoding="utf-8", newline="")
            if add_record:
                doc.write_text(doc.read_text(encoding="utf-8")
                               + "\n> 现状快照 / bump 声明 / 迁移说明 / 校验回读\n",
                               encoding="utf-8", newline="")
            patch = git("diff", "HEAD").stdout
            patch_path = tree / "_diff.patch"
            patch_path.write_text(patch, encoding="utf-8", newline="")
            code, out, err = run_source(body, tree)
            results[name] = summarize(code, out)
            results[name]["patch_b64"] = base64.b64encode(patch.encode("utf-8")).decode("ascii")
            if args.cli:
                proc = subprocess.run([args.cli, "--root", str(tree), "extension", "--diff", str(patch_path)],
                                      capture_output=True, timeout=600)
                results[name]["engine_exit"] = proc.returncode
                results[name]["engine_stdout"] = decode_console(proc.stdout).replace("\r\n", "\n")
                results[name]["engine_digest32"] = digest32(results[name]["engine_stdout"])
            print(f"  {name}（调用方供 diff）：真源 exit={code} · "
                  f"{results[name]['log'][0] if results[name]['log'] else ''} · [FAIL] {results[name]['fails']}"
                  + (f" · 引擎摘要 {results[name]['engine_digest32']}" if args.cli else ""))

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-extension-policy-golden/1",
            "generated": "2026-09-27",
            "source": "verify.sh check30 内联 Python 原文（机械抽取后执行）",
            "snapshot": _paths.portable(snap),
            "digest_rule": 'sha256("\\n".join(stdout.splitlines()))[:32]  ← 与引擎 Result.LogDigest 同式',
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
        for key in ("real", "synthetic", "judged_no_record", "judged_with_record"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        want_b, got_b = fixture["cases"]["boundary"], results["boundary"]
        boundary_ok = (want_b["digest32"] == got_b["digest32"]
                       and want_b["fails"] == got_b["fails"] and got_b["fails"] >= 1)
        print(f"  [{'OK ' if boundary_ok else '漂移'}] boundary: 真源仍报 {got_b['fails']} 条 FAIL"
              f"（bump 面在这个态确实是活的）")
        if drift or not boundary_ok:
            print(f"FAIL: 真源输出已漂移 {drift or ['boundary']}")
            return 1
        print("OK: 金标向量与真源本轮输出一致（五条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [rel for rel, b64 in results["synthetic"]["files_b64"].items() if b64 not in cs]
        for key in ("real", "synthetic", "judged_no_record", "judged_with_record"):
            if results[key]["digest32"] not in cs:
                missing.append(f"<{key} 摘要>")
        for key in ("judged_no_record", "judged_with_record"):
            if results[key].get("patch_b64", "") not in cs:
                missing.append(f"<{key} patch>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 合成树 base64 + 四摘要 + 两份 diff 均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        rows = json.loads(decode_console(proc.stdout))["rows"]
        real_pin = [r for r in rows if r["name"].startswith("扩展策略面·真仓")]
        synth_pin = [r for r in rows if r["name"].startswith("扩展策略面·合成")]
        bound_pin = [r for r in rows if r["name"].startswith("扩展策略面·边界")]
        judged_pins = [r for r in rows if r["name"].startswith("扩展策略面·可判")]
        if len(real_pin) != 1 or len(synth_pin) != 1 or len(bound_pin) != 1 or len(judged_pins) != 2:
            print(f"FAIL: 引擎侧扩展策略面钉应为 5 条，实得 "
                  f"{len(real_pin)}/{len(synth_pin)}/{len(bound_pin)}/{len(judged_pins)}")
            return 1
        bad = []
        for pin, case in ((real_pin[0], "real"), (synth_pin[0], "synthetic")):
            m = re.search(r"摘要 (\w{32})", pin["detail"])
            got = m.group(1) if m else None
            want = results[case]["digest32"]
            print(f"  [{'OK ' if got == want else '不一致'}] 引擎 {case}: {got} / 真源 {want}")
            if got != want:
                bad.append(case)
        boundary_declared = "UNKNOWN" in bound_pin[0]["detail"] and "BumpFaceJudged=False" in bound_pin[0]["detail"]
        print(f"  [{'OK ' if boundary_declared else '不一致'}] 引擎 boundary: 明示 UNKNOWN/不判")
        if not boundary_declared:
            bad.append("boundary")
        # **按名字里的显式标记配对**，不要按 name 排序——中文排序里「带(5E26) < 无(65E0)」会把它俩顺序对调
        # （实测踩过：第一次跑就报「引擎 judged_no_record: <带记录摘要>」，是我配错而不是引擎算错）。
        no_record_pin = [r for r in judged_pins if "无四步记录" in r["name"]]
        with_record_pin = [r for r in judged_pins if "带四步记录" in r["name"]]
        for pin, case in ((no_record_pin[0] if no_record_pin else None, "judged_no_record"),
                          (with_record_pin[0] if with_record_pin else None, "judged_with_record")):
            if pin is None:
                print(f"FAIL: 找不到判据钉（{case}）")
                bad.append(case)
                continue
            m = re.search(r"摘要 (\w{32})", pin["detail"])
            got = m.group(1) if m else None
            want = results[case]["digest32"]
            print(f"  [{'OK ' if got == want else '不一致'}] 引擎 {case}: {got} / 真源 {want}")
            if got != want:
                bad.append(case)
        if bad:
            print(f"FAIL: 引擎侧与真源输出不一致：{bad}")
            return 1
        print("OK: 引擎侧扩展策略面与真源逐字节同摘要（导出态 + 合成 + **供 diff 的可判集**），且边界显式声明")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
