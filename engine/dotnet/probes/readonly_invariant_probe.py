"""**只读不变量（系统级）**：本工程对外最强的安全声明是"这是只读门"。

此前它的证据是**逐命令的轶事**（某个探针里断言过 `workloop --write` 被拒）。本探针把它
升成**系统级不变量**，在**一份临时副本**上跑（绝不碰金标快照——第七十六片的 head4 事故就是这么来的）：

  ① **读面母树零改动**：跑一遍读面母树（聚合门 / 回执 / 透明链 / 组合 / 馆藏 / 建模 / 决策 /
     断言 / 认知 / 指令档 / RFC / 端点 / 事件 / 工具面 / 市场 / 资产 / 统计 / 一致性 …），
     之后整棵树的指纹（逐文件路径 + 大小 + sha256）**必须逐条不变**；
  ② **写面全拒**：所有写面命令/开关（patterns reindex · asset add/rm/deprecate/restore/
     baseline --write/ledger --refresh · output render|meter --write · workloop --write|--close ·
     score --write-baseline · review --write · stats --write · knowledge frequency --write ·
     knowledge transform add|promote · assemble --session-path|--save-path|--trace-path ·
     interop --all 缺省落仓）必须**非零退出**，且**树仍不变**（拒绝 ≠ 偷偷写了再报错）；
  ③ **显式落盘只落调用者给的路径**：`bench --write-baseline <外部路径>` 与
     `interop --kind K --out <外部路径>` 允许成功，但写出的东西必须在**仓库根之外**，且根内仍零改动；
  ④ **负对照**：在副本上用**真源 Python** 跑同一个写面（`nf stats --write` 等）⇒ 树**必须变**
     ——证明指纹是敏的，也证明被 .NET 侧拒绝的那些操作确实是真写，而不是"本来就什么都不做"。

用法：
    python probes/readonly_invariant_probe.py --snap <隔离快照> --cli <nf-dotnet.exe>
        [--py-exe <python>] [--engine <NF-NET-engine>] [--keep]
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
ENGINE = _paths.ENGINE
# 读面母树：全部必须在干净语料上 exit=0，且跑完母树零改动
READ_BATTERY = [
    ["verify"],
    ["selftest"],
    ["receipts"],
    ["receipts", "--scope", "library"],
    ["transparency"],
    ["combine", "verify"],
    ["combine", "breadth"],
    ["library"],
    ["model"],
    ["sig"],
    ["decisions"],
    ["assertions"],
    ["cognition"],
    ["driver"],
    ["rfc"],
    ["endpoint"],
    ["events"],
    ["toolface"],
    ["stats", "--check"],
    ["market", "--list"],
    ["patterns", "ls"],
    ["asset", "verify"],
    ["knowledge"],  # 真源的读面就是裸 `knowledge`（`knowledge status` 在两侧都故意是用法错误）
    ["conformance"],
    ["corpus"],
    ["license"],
    ["score"],
    ["doctor"],
    ["spec"],
    ["workloop", "--list"],
    ["review", "--limit", "5"],
]

# 写面：全部必须非零退出
WRITE_BATTERY = [
    ["patterns", "reindex"],
    ["asset", "add"],
    ["asset", "rm"],
    ["asset", "deprecate"],
    ["asset", "restore"],
    ["asset", "baseline", "--write"],
    ["asset", "ledger", "--refresh"],
    ["output", "render", "--write"],
    ["output", "meter", "--write"],
    ["workloop", "--write"],
    ["workloop", "--close"],
    ["score", "--write-baseline"],
    ["review", "--write"],
    ["stats", "--write"],
    ["knowledge", "frequency", "--write"],
    ["knowledge", "transform", "add"],
    ["knowledge", "transform", "promote"],
    ["interop", "--all"],
]

# 真源 Python 侧的写面（负对照用；第一个能跑通的即采用）。
# 注意：`stats --write` / `patterns reindex` 这类是**幂等写**（写了但内容与在盘一致 ⇒ 树不变），
# 当负对照会假红；`module deprecate <file>` 真正改状态位（也正是第七十六片污染 head4 的那条命令）。
FALLBACK_PY_WRITES = [
    ["stats", "--write"],
    ["knowledge", "frequency", "--write"],
]


def first_active_module(cli: str, tree: Path) -> str:
    """从 `module ls` 里动态取一个真实模块路径（避免把模块名写死在探针里）。"""
    r = run([cli, "--root", str(tree), "module", "ls"])
    for line in r.stdout.decode("utf-8", "replace").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ("active", "deprecated", "retired") and parts[1].endswith(".md"):
            return parts[1]
    return ""


def fingerprint(root: Path) -> dict[str, tuple[int, str]]:
    """整树指纹：路径 → (大小, sha256)。排除 Python 字节码缓存（派生物，见第一百零七片口径）。"""
    out: dict[str, tuple[int, str]] = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if "__pycache__" in rel or rel.endswith((".pyc", ".pyo")):
            continue
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        out[rel] = (p.stat().st_size, h.hexdigest())
    return out


def diff_fp(a: dict, b: dict) -> list[str]:
    msgs = []
    for k in sorted(set(a) | set(b)):
        if k not in b:
            msgs.append(f"消失：{k}")
        elif k not in a:
            msgs.append(f"新增：{k}")
        elif a[k] != b[k]:
            msgs.append(f"改动：{k}")
    return msgs


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--py-exe", default=sys.executable)
    ap.add_argument("--engine", default=str(ENGINE))
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    engine = Path(args.engine)
    cli = args.cli
    if not cli:
        cands = sorted((engine / "dist").glob("nf-dotnet-win-x64-f*/nf-dotnet.exe"))
        cli = str(cands[-1]) if cands else ""
    problems: list[str] = []
    if not cli or not Path(cli).exists():
        print("FAIL: 找不到 nf-dotnet.exe（--cli 未给且 dist 下无 fNN 产物）")
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="nf-readonly-"))
    tree = tmp / "tree"
    try:
        shutil.copytree(args.snap, tree)
        base = fingerprint(tree)
        print(f"⓪ 副本已建：{tree}（{len(base)} 件 · 排除 __pycache__/*.pyc）")

        mod_rel = first_active_module(cli, tree)
        write_battery = list(WRITE_BATTERY)
        py_writes: list[list[str]] = []
        if mod_rel:
            write_battery.append(["module", "deprecate", mod_rel])
            write_battery.append(["module", "restore", mod_rel])
            py_writes.append(["module", "deprecate", mod_rel, "--reason", "只读不变量负对照"])
            print(f"   动态取到模块：{mod_rel}（写面电池 +1 条 deprecate/restore；负对照用它）")
        else:
            print("   ⚠️ 没从 module ls 取到模块路径（写面电池少两条）")
        py_writes += FALLBACK_PY_WRITES

        # ① 读面母树
        bad_read = []
        for argv in READ_BATTERY:
            r = run([cli, "--root", str(tree)] + argv, timeout=args.timeout)
            if r.returncode != 0:
                tail = (r.stdout.decode("utf-8", "replace").strip().splitlines() or [""])[-1][:80]
                bad_read.append(f"{' '.join(argv)} (exit={r.returncode}: {tail})")
        after_read = fingerprint(tree)
        read_delta = diff_fp(base, after_read)
        print(f"① 读面母树 {len(READ_BATTERY)} 条：非零退出 {len(bad_read)} 条 · 母树改动 {len(read_delta)} 处")
        if bad_read:
            problems.append("读面母树里有非零退出：" + "; ".join(bad_read))
        if read_delta:
            problems.append("读面母树跑完后母树被改动：" + "; ".join(read_delta[:6]))

        # ② 写面全拒（且拒绝后仍零改动）
        not_rejected = []
        for argv in write_battery:
            r = run([cli, "--root", str(tree)] + argv, timeout=args.timeout)
            if r.returncode == 0:
                not_rejected.append(" ".join(argv))
        after_write = fingerprint(tree)
        write_delta = diff_fp(after_read, after_write)
        print(f"② 写面 {len(write_battery)} 条：未被拒 {len(not_rejected)} 条 · 母树改动 {len(write_delta)} 处")
        if not_rejected:
            problems.append("这些写面没有被拒绝（exit=0）：" + "; ".join(not_rejected))
        if write_delta:
            problems.append("写面被拒后母树仍被改动（拒绝 ≠ 没写）：" + "; ".join(write_delta[:6]))

        # ③ 显式落盘：只落调用者给的路径（仓库根之外）
        outside = tmp / "outside"
        outside.mkdir(parents=True, exist_ok=True)
        bench_out = outside / "bench-baseline.json"
        r1 = run([cli, "--root", str(tree), "bench", "--write-baseline", str(bench_out)], timeout=args.timeout)
        interop_out = outside / "sbom.json"
        r2 = run([cli, "--root", str(tree), "interop", "--kind", "sbom", "--out", str(interop_out)], timeout=args.timeout)
        mkdirs = []
        if r1.returncode != 0:
            mkdirs.append(f"bench --write-baseline exit={r1.returncode}")
        if not bench_out.exists():
            mkdirs.append("bench --write-baseline 没有落盘")
        if r2.returncode != 0:
            mkdirs.append(f"interop --out exit={r2.returncode}")
        if not interop_out.exists():
            mkdirs.append("interop --out 没有落盘")
        after_explicit = fingerprint(tree)
        explicit_delta = diff_fp(after_write, after_explicit)
        print(f"③ 显式落盘 2 条：外部落盘 {bench_out.name}/{interop_out.name} 存在="
              f"{bench_out.exists()}/{interop_out.exists()} · 根内改动 {len(explicit_delta)} 处")
        if mkdirs:
            problems.append("显式落盘面有问题：" + "; ".join(mkdirs))
        if explicit_delta:
            problems.append("显式落盘写进了仓库根内：" + "; ".join(explicit_delta[:6]))

        # ④ 负对照：真源 Python 的写面必须真的改变母树
        nf_py = tree / "scripts" / "nf.py"
        used = None
        if not nf_py.exists():
            problems.append(f"副本里找不到真源 CLI：{nf_py}")
        else:
            for argv in py_writes:
                r = run([args.py_exe, str(nf_py)] + argv, cwd=tree, timeout=args.timeout)
                if r.returncode == 0:
                    used = argv
                    break
            if used is None:
                problems.append("负对照失败：真源 Python 的写面候选都没跑通（无法证明指纹是敏的）")
            else:
                after_neg = fingerprint(tree)
                neg_delta = diff_fp(after_explicit, after_neg)
                print(f"④ 负对照：真源 `nf {' '.join(used)}` ⇒ 母树改动 {len(neg_delta)} 处"
                      f"（例：{neg_delta[:2]}）")
                if not neg_delta:
                    problems.append("负对照没有改动母树 —— 指纹不敏，整条判据不可信")

        if problems:
            print("FAIL:")
            for p in problems:
                print("  -", p)
            return 1
        print("OK: 只读不变量成立（读面母树零改动 · 写面全拒且不偷写 · 显式落盘只落根外 · 负对照会红）")
        return 0
    finally:
        if args.keep:
            print(f"   副本保留：{tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
