"""**可复现构建判据**：同一份源码 + 同一 RID ⇒ 交付件逐字节相同。

为什么值得单列一条判据（而不是写在记录件里）："工业级交付"里最容易被口头承诺、
最难被证伪的一条就是可复现构建。本工程此前的实测结论是 **`nf-dotnet.dll` 三处不同
（bin / win-x64 / linux-x64）· 二进制不可复现**——但那句话没有区分两种完全不同的原因：

  (a) **同输入但构建位置不同 ⇒ 不同字节** —— 这是真缺陷（源码绝对路径进了编译哈希）；
  (b) **不同 RID ⇒ 不同字节** —— 这是正当差异（RID 字符串本身被嵌进程序集）。

本探针把 (a) 钉成判据：把源码复制到**两个互不相干的临时根**，各自全新还原 + 发布，
逐文件比对；并跑一个**负对照**（关掉 `PathMap`）证明这条判据会红——否则"两次都一样"
可能只是因为构建被增量跳过、文件被原样复制。

用法：
    python probes/reproducible_build_probe.py [--engine <NF-NET-engine>] [--rid win-x64]
        [--dotnet <dotnet.exe>] [--cross-rid] [--keep]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
ENGINE = _paths.ENGINE
DEFAULT_DOTNET = _paths.DOTNET
SUFFIXES = {".cs", ".csproj", ".props"}


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def copy_sources(engine: Path, dest: Path) -> int:
    n = 0
    for p in engine.rglob("*"):
        if not p.is_file():
            continue
        if any(part in ("bin", "obj") for part in p.parts):
            continue
        if p.suffix.lower() not in SUFFIXES and p.name != "README.md":
            continue
        rel = p.relative_to(engine)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out)
        n += 1
    return n


def publish(dotnet: str, root: Path, out: Path, rid: str, extra: list[str], timeout: int) -> int:
    proj = root / "tools" / "nf-dotnet" / "nf-dotnet.csproj"
    cmd = [dotnet, "publish", str(proj), "-c", "Release", "-r", rid,
           "--self-contained", "true", "-o", str(out), "-v", "q", "--nologo"] + extra
    proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if proc.returncode != 0:
        tail = proc.stdout.decode("utf-8", "replace").strip().splitlines()[-6:]
        print("   publish 失败：" + " | ".join(tail))
    return proc.returncode


def compare(a: Path, b: Path) -> tuple[int, int, int, list[str]]:
    fa = {p.relative_to(a).as_posix(): p for p in a.rglob("*") if p.is_file()}
    fb = {p.relative_to(b).as_posix(): p for p in b.rglob("*") if p.is_file()}
    same = diff = 0
    diffs = []
    for rel, pa in fa.items():
        pb = fb.get(rel)
        if pb is None:
            diffs.append(rel + "（只在 A）")
            continue
        if sha256(pa) == sha256(pb):
            same += 1
        else:
            diff += 1
            diffs.append(rel)
    for rel in fb:
        if rel not in fa:
            diffs.append(rel + "（只在 B）")
    return same, diff, len(fa), diffs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=str(ENGINE))
    ap.add_argument("--rid", default="win-x64")
    ap.add_argument("--dotnet", default=DEFAULT_DOTNET)
    ap.add_argument("--cross-rid", action="store_true", help="额外构建 linux-x64 并报告跨 RID 差异数（信息面，不判失败）")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    engine = Path(args.engine)
    props = engine / "Directory.Build.props"
    problems = []

    # ① 机制在场：PathMap 归一（否则源码绝对路径进编译哈希）
    if not props.exists():
        problems.append("Directory.Build.props 不在场（可复现构建靠它把工程根映射到固定虚拟根）")
    else:
        text = props.read_text(encoding="utf-8-sig")
        if "PathMap" not in text:
            problems.append("Directory.Build.props 里没有 PathMap —— 同输入异地构建不可能逐字节相同")
        else:
            print("① 机制在场：Directory.Build.props 含 PathMap（工程根 → 固定虚拟根）")

    tmp = Path(tempfile.mkdtemp(prefix="nf-repro-"))
    try:
        roots = {}
        for tag in ("a", "b"):
            d = tmp / tag
            d.mkdir(parents=True, exist_ok=True)
            roots[tag] = (d, copy_sources(engine, d))
        print(f"② 两棵独立源码树：A {roots['a'][1]} 文件 · B {roots['b'][1]} 文件（临时根 {tmp.name}）")

        t0 = time.time()
        for tag in ("a", "b"):
            rc = publish(args.dotnet, roots[tag][0], roots[tag][0] / "pub", args.rid, [], args.timeout)
            if rc != 0:
                problems.append(f"{tag} 的 publish 失败（exit={rc}）")
        print(f"③ 两次异地发布完成（同 RID={args.rid} · {time.time()-t0:.1f}s）")

        if not problems:
            same, diff, total, diffs = compare(roots["a"][0] / "pub", roots["b"][0] / "pub")
            print(f"④ 逐文件比对：两侧各 {total} 件 · 相同 {same} · 不同 {diff}")
            if diff or len(diffs) > 0:
                problems.append(f"同一 RID 两次异地构建存在差异 {diff} 件：" + ", ".join(diffs[:6]))
            else:
                print("   ⇒ 同 RID 异地重建 = 逐字节全等（可复现构建成立）")

            # ⑤ 负对照：关掉 PathMap 再建一次（在 A 的源码树上），必须出现差异
            rc = publish(args.dotnet, roots["a"][0], roots["a"][0] / "pub-nomap", args.rid,
                         ["-p:PathMap="], args.timeout)
            if rc != 0:
                problems.append(f"负对照 publish 失败（exit={rc}）")
            else:
                _s, ndiff, _t, _d = compare(roots["a"][0] / "pub", roots["a"][0] / "pub-nomap")
                print(f"⑤ 负对照（-p:PathMap= 关掉归一）：与正例差异 {ndiff} 件")
                if ndiff == 0:
                    problems.append("负对照没有差异 —— 判据可能是恒绿（构建被增量跳过？）")

            if args.cross_rid:
                rid2 = "linux-x64" if args.rid == "win-x64" else "win-x64"
                rc = publish(args.dotnet, roots["b"][0], roots["b"][0] / f"pub-{rid2}", rid2, [], args.timeout)
                if rc != 0:
                    problems.append(f"跨 RID 构建失败（{rid2}，exit={rc}）")
                else:
                    _s, cdiff, ct, _d = compare(roots["a"][0] / "pub", roots["b"][0] / f"pub-{rid2}")
                    print(f"⑥ 跨 RID（{args.rid} ↔ {rid2}）信息面：两侧各 {ct} 件 · 不同 {cdiff} 件"
                          "（RID 字符串会被嵌进程序集，属正当差异，不判失败）")

        if problems:
            print("FAIL:")
            for p in problems:
                print("  -", p)
            return 1
        print("OK: 可复现构建成立（机制在场 · 同 RID 异地重建逐字节全等 · 负对照会红）")
        return 0
    finally:
        if args.keep:
            print(f"   临时目录保留：{tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
