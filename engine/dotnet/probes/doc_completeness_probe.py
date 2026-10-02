#!/usr/bin/env python3
"""check20（文档完整性门禁）双跑对账探针：把 **verify.sh 里那段内联 Python 原文抽出来**，
在「真仓快照」和「合成树」上跑一遍，与 .NET 引擎侧 `DocCompleteness` 的输出做**逐字节**对账。

为什么需要它：check20 在真源里**只被 verify.sh 消费**（没有 `nf` 子命令面），所以引擎侧没有 CLI 面可比。
本探针给出第三种证据通道——**真源代码原文**（不是我的复述）在同一棵树上跑出的 stdout，与引擎侧同口径摘要比对。

用法：
    python probes/doc_completeness_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]

口径：
  * **摘要** = `sha256("\\n".join(stdout.splitlines()))[:32]`（与引擎 `Result.LogDigest` 同式）；
  * 真源片段按 `python -c <源码>` 执行（真源用 `python - <<PYEOF`，二者对**成功/失败路径的 stdout** 无差别）；
  * 合成树与引擎自检钉里的树**同一份规格**（写在 `_fixtures/_doc_completeness_golden.json`）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_doc_completeness_golden.json")
# 合成树规格（与 SelfTest.DocCompletenessCases 里构造的树**必须逐字节相同**）
SYNTH_FILES = {
    "04_模块库/通用类/M00_好.md":
        "# 模块 M00 · 数据结构\n> 类别：通用\n> 来源：核心\n> 挂载点：P00\n> 依赖：无\n\n## 职责\n正文\n\n"
        "```yaml\nmachine_contract:\n  id: M00\n```\n",
    "04_模块库/通用类/M99_坏.md": "# 坏标题\n正文没有元数据也没有章节\n",
    "community/示例包/modules/C01_完备但缺键.md":
        "# 模块 C01 · 示例\n\n```yaml\nmachine_contract:\n  id: C01\n```\n\n## 职责\n正文\n",
    "community/示例包/modules/C02_未完备.md": "not a module doc\n",
}


def extract_check20(verify_sh: Path) -> str:
    """从 verify.sh 抽出 check20 里 heredoc 的 Python 原文（逐字节，不改写）。"""
    text = verify_sh.read_text(encoding="utf-8")
    start = text.index("check20(){")
    m = re.search(r"<<'PYEOF'[^\n]*\n(.*?)\nPYEOF\n", text[start:], re.S)
    if not m:
        raise SystemExit("找不到 check20 的 PYEOF 片段")
    return m.group(1)


def digest32(stdout_text: str) -> str:
    lines = stdout_text.splitlines()
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def run_source(body: str, tree: Path) -> tuple[int, str, str]:
    """跑真源片段。**强制子进程按 UTF-8 出口**（PYTHONIOENCODING）——否则 Windows 控制台码页（GBK）
    会把中文以 cp936 写进管道，两边字符相同但传输编码不同。真源在 UTF-8 locale 的 bash 下即本口径。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    proc = subprocess.run([sys.executable, "-c", body], cwd=str(tree), env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=300)
    return proc.returncode, proc.stdout, proc.stderr


def decode_console(raw: bytes) -> str:
    """引擎 CLI 的 stdout：先按 UTF-8 试，失败退回 GBK（.NET Console 走控制台码页）。"""
    for enc in ("utf-8", "gbk", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def write_tree(base: Path, files: dict) -> None:
    for rel, content in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def summarize(exit_code: int, stdout: str) -> dict:
    lines = stdout.splitlines()
    fails = sum(1 for l in lines if l.startswith(" [FAIL]"))
    warns = sum(1 for l in lines if l.startswith(" [WARN]"))
    head = lines[0] if lines else ""
    m = re.match(r"文档完整性扫描：官方 (\d+) 件 \+ 社区 (\d+) 件（.*WARN 统计 (\d+) 件）", head)
    return {
        "python_exit": exit_code,
        "digest32": digest32(stdout),
        "core": int(m.group(1)) if m else None,
        "community": int(m.group(2)) if m else None,
        "incomplete": int(m.group(3)) if m else None,
        "fails": fails,
        "warn_lines": warns,
        "log": lines,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP, help="真源快照（读 verify.sh 与 04_模块库/community）")
    ap.add_argument("--cli", default="", help="nf-dotnet（给了才读引擎侧自检钉的摘要做比对）")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true", help="按真源重算并覆写金标向量")
    args = ap.parse_args()

    snap = Path(args.snap)
    body = extract_check20(snap / "verify.sh")
    print(f"check20 源码片段：{len(body.splitlines())} 行（从 verify.sh 抽自 {snap}）")

    results = {}

    # ① 真材料：真仓快照本身
    code, out, err = run_source(body, snap)
    if err.strip():
        print("  真源 stderr：" + err.strip().splitlines()[-1][:200])

    results["real"] = summarize(code, out)
    print(f"  真仓：exit={code} · 官方 {results['real']['core']} · 社区 {results['real']['community']} · "
          f"未完备 {results['real']['incomplete']} · FAIL {results['real']['fails']} · 摘要 {results['real']['digest32']}")

    # ② 合成树：官方 2 件（1 合规 / 1 四类问题）+ 社区 2 件（1 有契约缺键 / 1 未完备只 WARN）
    with tempfile.TemporaryDirectory(prefix="nf-docprobe-") as tmp:
        tree = Path(tmp)
        write_tree(tree, SYNTH_FILES)
        code, out, err = run_source(body, tree)
        if err.strip():
            print("  真源 stderr：" + err.strip().splitlines()[-1][:200])

        results["synthetic_mixed"] = summarize(code, out)
    results["synthetic_mixed"]["files"] = SYNTH_FILES
    print(f"  合成：exit={code} · 官方 {results['synthetic_mixed']['core']} · 社区 "
          f"{results['synthetic_mixed']['community']} · 未完备 {results['synthetic_mixed']['incomplete']} · "
          f"FAIL {results['synthetic_mixed']['fails']} · 摘要 {results['synthetic_mixed']['digest32']}")

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-doc-completeness-golden/1",
            "generated": "2026-09-27",
            "source": "verify.sh check20 内联 Python 原文（探针机械抽取后执行，逐字节 stdout）",
            "snapshot": _paths.portable(snap),
            "digest_rule": 'sha256("\\n".join(stdout.splitlines()))[:32]  ← 与引擎 Result.LogDigest 同式',
            "cases": results,
        }
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"已写金标向量：{fixture_path}")
    else:
        if not fixture_path.exists():
            print(f"缺金标向量 {fixture_path}（用 --write-fixture 生成）")
            return 1
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        drift = []
        for key in ("real", "synthetic_mixed"):
            want = fixture["cases"][key]["digest32"]
            got = results[key]["digest32"]
            flag = "OK " if want == got else "漂移"
            print(f"  [{flag}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移：{drift}（先看是不是快照换了 HEAD，再决定是否重签金标）")
            return 1
        print("OK: 金标向量与真源本轮输出一致（两条用例）")

    if args.cli:
        # 引擎侧：跑一次自检，读 check20 两行的 detail（含引擎侧摘要），与真源摘要比对
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        try:
            rows = json.loads(decode_console(proc.stdout))["rows"]
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: 读不出引擎自检 JSON：{exc}")
            return 1
        docs = [r for r in rows if r["name"].startswith("check20")]
        if len(docs) != 2:
            print(f"FAIL: 引擎侧 check20 钉应为 2 条，实得 {len(docs)}")
            return 1
        bad = []
        for row in docs:
            m = re.search(r"摘要 (\w{32})", row["detail"])
            case = "real" if "真仓" in row["name"] else "synthetic_mixed"
            engine_digest = m.group(1) if m else None
            want = results[case]["digest32"]
            flag = "OK " if engine_digest == want else "不一致"
            print(f"  [{flag}] 引擎 {case}: {engine_digest} / 真源 {want} · {row['name'][:12]}…")
            if engine_digest != want:
                bad.append(case)
        if bad:
            print(f"FAIL: 引擎侧与真源输出不一致：{bad}")
            return 1
        print("OK: 引擎侧 check20 输出与真源逐字节同摘要（真材料 + 合成树）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
