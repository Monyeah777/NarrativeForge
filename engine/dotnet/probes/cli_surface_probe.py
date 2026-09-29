"""**CLI 面可达判据**：`--help` 必须列全**真实存在的命令**。

起因（第一百二十片实测）：引擎的 `--help` 只列 **25** 条命令，而分派面有 **52** 条——
**27 条命令在帮助里查不到**（`assemble` / `conformance` / `corpus` / `doctor` / `spec` / `review` /
`score` / `license` / `model` / `module` / `workloop` …）。对第三方来说，"命令存在但没人知道"
等于不存在；仓内对 `nf` 也有同类判据（check39「命令面全策展可达」），本线此前没有。

判据三面：
  ① **静态面**：从 `tools/nf-dotnet/Program.cs` 的 `switch (cmd)` 里抽出全部命令词；
  ② **动态面**：跑 `nf-dotnet --help`，从「命令：」段抽出列出的命令词；
  断言：**静态 ⊆ 动态**（帮助表覆盖分派面）；并报告反向差（帮助里列了但分派不到 = 幽灵命令）。
  ③ **子命令面（行为判定）**：对每个在帮助里声明了子命令的父命令，跑一次 `<parent> zzz_不存在`，
     从**引擎自报的错误文案**里取「它认的子命令集」（`子命令须为 …` / `子命令只移植了 …` /
     `没有子命令：…（可选 …）` 三种实测形状），断言 **该集合 ⊆ 帮助表声明**。
     **为什么用行为判定而不是静态抽取**：`Program.cs` 里 `sub` 也承载 tier/状态取值
     （实测 `asset` 静态抽到 15 个词，真子命令只有 8 个）⇒ 静态面会误报；而报错文案就是权威声明。
     取不到枚举的父命令（如 `combine`）如实登记 **UNKNOWN**（不猜、不判红）。
     本条补的是一处真缺陷：`asset` 的 `baseline/density/usage/thickness/ledger` 五个子命令
     此前**能跑但帮助里查不到**（第一百二十二片 §16 实测），而 ①② 只看顶层、抓不到。

用法：
    python probes/cli_surface_probe.py [--engine <引擎>] [--cli <nf-dotnet>]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）


def dispatched(program_cs: Path) -> set[str]:
    """从 switch 分派里抽命令词（排除 `--xxx` 选项 case）。"""
    text = program_cs.read_text(encoding="utf-8")
    start = text.find("switch (cmd)")
    end = text.find("未知命令", start if start >= 0 else 0)
    body = text[start:end] if start >= 0 and end > start else text
    words = {m.group(1) for m in re.finditer(r'case\s+"([a-z][a-z0-9-]*)"', body)}
    return words


def helped(cli: str) -> tuple[set[str], str]:
    """跑 `--help`，抽「命令：」段里的命令词。注意：帮助走 **stderr**（实测）。"""
    p = subprocess.run([cli, "--help"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    text = p.stdout.decode("utf-8", "replace")
    words: set[str] = set()
    in_cmd = False
    for line in text.splitlines():
        if line.startswith("命令"):
            in_cmd = True
            continue
        if in_cmd:
            if not line.strip():
                break
            m = re.match(r"^\s{2}(\S+)", line)
            if m:
                words.add(m.group(1))
    return words, text


def help_subcommands(text: str) -> dict[str, set[str]]:
    """从帮助命令表里抽**父命令 → 已声明子命令**（首列形如 `asset verify|inventory|… [--opt]`）。"""
    out: dict[str, set[str]] = {}
    for line in text.splitlines():
        m = re.match(r"^\s{2}(\S.*?)\s{2,}\S", line)
        if not m:
            continue
        # 只剥**选项组**（含 `--` 的方括号，如 `[--json]`）；`[render|verify|…]` 这类是**子命令组**，必须保留
        col0 = re.sub(r"\[[^\]]*--[^\]]*\]", " ", m.group(1))
        col0 = col0.replace("[", " ").replace("]", " ")   # 保留其内容，只去掉括号字符本身
        toks = [t for t in re.split(r"[|\s]+", col0) if t]
        if len(toks) < 2:
            continue
        parent = toks[0]
        subs = {t for t in toks[1:] if re.fullmatch(r"[a-z][a-z0-9-]*", t)}
        if subs:
            out.setdefault(parent, set()).update(subs)
    return out


#: 未知子命令时引擎自报的三种枚举形状（实测文案；顺序即优先级）
_SUB_ORACLE_RES = (
    re.compile(r"子命令须为\s*(.+?)[（(：:]"),
    re.compile(r"子命令只移植了\s*(.+?)[；;]"),
    re.compile(r"没有子命令：.*?（可选\s*(.+?)[；;）)]"),
)


def oracle_subcommands(cli: str, parents) -> tuple[dict[str, set[str]], list[str]]:
    """行为判定：跑 `<parent> zzz_不存在`，从引擎自报文案取权威子命令集（无需语料）。"""
    oracle: dict[str, set[str]] = {}
    unknown: list[str] = []
    for parent in sorted(parents):
        p = subprocess.run([cli, parent, "zzz_不存在"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=120)
        text = p.stdout.decode("utf-8", "replace")
        subs: set[str] = set()
        for rx in _SUB_ORACLE_RES:
            m = rx.search(text)
            if not m:
                continue
            # 逐**斜杠分段**取「段首标识符」——因为枚举里常带注解（`` `types`（含 --backlog） ``），
            # 整段做 fullmatch 会把它连同合法子命令一起丢掉（实测：module 少认 `types`、
            # pipeline 整条判成 UNKNOWN）。
            for seg in m.group(1).split("/"):
                hit = re.match(r"[`\s]*([a-z][a-z0-9-]*)", seg)
                if hit:
                    subs.add(hit.group(1))
            break
        if subs:
            oracle[parent] = subs
        else:
            unknown.append(parent)
    return oracle, unknown


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=str(_paths.ENGINE))
    ap.add_argument("--cli", default=str(_paths.newest_dist("win-x64") / "nf-dotnet.exe"))
    args = ap.parse_args()

    engine = Path(args.engine)
    program = engine / "tools" / "nf-dotnet" / "Program.cs"
    problems: list[str] = []
    if not program.exists():
        print(f"FAIL: 找不到 {program}")
        return 1
    if not Path(args.cli).exists():
        print(f"FAIL: 找不到 CLI：{args.cli}")
        return 1

    static = dispatched(program)
    dynamic, help_text = helped(args.cli)
    missing = sorted(static - dynamic)
    ghost = sorted(dynamic - static)
    print(f"① 分派面（Program.cs switch）：{len(static)} 条命令")
    print(f"② 帮助面（`--help` 命令表）：{len(dynamic)} 条命令")
    print(f"   帮助表未列：{missing if missing else '（无）'}")
    print(f"   帮助里的幽灵命令（分派不到）：{ghost if ghost else '（无）'}")
    if missing:
        problems.append(f"`--help` 少列 {len(missing)} 条真实命令：{missing}")
    if ghost:
        problems.append(f"`--help` 列了 {len(ghost)} 条分派不到的命令：{ghost}")
    if not help_text.strip():
        problems.append("`--help` 无输出（CLI 或参数形状变了？）")

    # ③ 子命令面：行为判定（引擎自报的权威子命令集 ⊆ 帮助表声明）
    help_subs = help_subcommands(help_text)
    oracle, unknown = oracle_subcommands(args.cli, help_subs.keys())
    print(f"③ 子命令面：{len(oracle)} 个父命令可机检 · 无枚举（UNKNOWN）{len(unknown)} 个"
          + (f"：{unknown}" if unknown else ""))
    sub_gaps = 0
    for parent, subs in sorted(oracle.items()):
        gap = sorted(subs - help_subs.get(parent, set()))
        if gap:
            sub_gaps += 1
            print(f"   {parent:<10} 引擎认 {len(subs)} 个 · **帮助未列 {gap}**")
            problems.append(f"`--help` 的 `{parent}` 行未列出子命令：{gap}（引擎实际接受，第三方按帮助查不到）")
        else:
            print(f"   {parent:<10} 引擎认 {len(subs)} 个 · 帮助已列全")

    if problems:
        print("FAIL:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"OK: CLI 面可达（帮助表 {len(dynamic)} 条 ⊇ 分派面 {len(static)} 条 · 无幽灵命令 · "
          f"子命令面 {len(oracle)} 个父命令无缺口"
          + (f" · {len(unknown)} 个无枚举已标 UNKNOWN" if unknown else "") + "）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
