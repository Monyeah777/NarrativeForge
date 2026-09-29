#!/usr/bin/env python3
"""资产质量五面差分探针（第 68 片）。

覆盖面：`nf asset` 的**只读五面**
  基础面 = `baseline`（行数/外形基线 · check8 同源）
  质量三面 = `density` / `usage` / `thickness`（45 W2 资产键语义体检）
  投影面 = `ledger`（键表机读投影校验）

**为什么要有这枚探针**：正向语料只证明「仓库恰好长这样时两边一样」。真正要证的是
**判据在违规语料上真的会红，而且两边红法一致**——基线的「未登记 / 漂移 / 缺件 / schema 不匹配 / 缺包跳过」、
密度的「空档」、引用度的「零引用」（含 `--strict` 与非 strict 的退出码分野）、厚度的「低信息候选」、
投影的「过期 / 缺失」。全部在**同一棵合成树**上用两侧同参数跑，比 stdout + stderr + 退出码。

纪律（历次踩坑入册）：
  · 子进程一律 `subprocess.run`（内部 communicate，不会管道死锁）；
  · 两侧读**同一棵树**（Python 用 `--root <树>`，引擎用 `--root <树>`）；
  · 环境钉 `PYTHONIOENCODING=utf-8`（宿主 GBK 下中文报错会自崩吞结论）；
  · 基准件（行数基线 / 键表投影）一律由**真源** `--write` / `--refresh` 生成后落地到合成树，
    不自造格式——否则探针会去迁就我的实现，而不是迁就真源。

退出码：0 = 全部一致 · 1 = 存在不一致。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# baseline 无 `--json` 面（真源 argparse 里没有该 flag），故 JSON 只对质量三面 + 投影面跑。
SUBS = ("baseline", "density", "usage", "thickness", "ledger")
JSON_SUBS = ("density", "usage", "thickness", "ledger")

# 合格档都写到 ≥200 字符（每份垫两段），好让"低信息候选 / 短档"只在专门造的档上出现
_PAD = ("这一句是刻意补长的正文，用来把合成档顶过 200 字符的短档阈值，"
        "从而让密度与厚度的低信息分支只在专门构造的那一份语料上被触发，"
        "避免整棵合成树因为档太小而全被标成低信息候选，"
        "同时也让引用度语料里每个键都有实际落点，不产生偶然的零引用。")
PAD = _PAD + _PAD

ASSET_A = ("# 测试资产 A\n\n`KEY_ALPHA` 与 `KEY_BETA` 定义如下。\n\n## KEY_ALPHA\n\n"
           "A 的正文。%s\n\n## KEY_BETA\n\nB 的正文。%s\n" % (PAD, PAD))
ASSET_B = "# 测试资产 B\n\n`KEY_GAMMA` 定义如下。\n\n## KEY_GAMMA\n\nG 的正文。%s\n" % PAD
USER_CUSTOM = "# 用户自定义\n\n`KEY_USER` 定义如下。\n\n## KEY_USER\n\n用户档正文。%s\n" % PAD
MODULE_DOC = "# 合成模块\n\n引用 `KEY_ALPHA` 与 `KEY_BETA` 与 `KEY_GAMMA` 与 `KEY_USER`。\n"
# 零引用键的构造要点（一开始想错了）：`usage` 的语料含 `community/**` —— **资产档自身也算语料**，
# 所以"正文里声明过的键"永远至少被自己引用一次（真仓 1499 键零引用 0 正是这个原因）。
# 唯一能造出零引用的键是**只来自文件名令牌、且正文不出现该串**的键：文件名 ORPHANKEY.md 即一例。
ORPHAN_ASSET = "# 孤键档\n\n正文刻意不提那个只写在文件名上的键。%s\n" % PAD
# 低信息档：<200 字、无键、无小节
LOW_INFO_ASSET = "太短。\n"


def build_tree(root: Path) -> None:
    """合成一棵最小但结构齐全的树（community 两包 + 05 用户自定义 + 语料）。"""
    (root / "community" / "合成甲包" / "assets").mkdir(parents=True)
    (root / "community" / "合成乙包" / "assets").mkdir(parents=True)
    (root / "community" / "合成甲包" / "assets" / "ALPHA.md").write_text(ASSET_A, encoding="utf-8", newline="\n")
    (root / "community" / "合成甲包" / "assets" / "BETA.md").write_text(ASSET_B, encoding="utf-8", newline="\n")
    (root / "community" / "合成甲包" / "assets" / "README.md").write_text("# 键表（人读）\n", encoding="utf-8")
    (root / "community" / "合成乙包" / "assets" / "GAMMA.md").write_text(ASSET_B, encoding="utf-8", newline="\n")
    (root / "05_资产库" / "用户自定义").mkdir(parents=True)
    (root / "05_资产库" / "用户自定义" / "USER.md").write_text(USER_CUSTOM, encoding="utf-8", newline="\n")
    (root / "04_模块库").mkdir(parents=True)
    (root / "04_模块库" / "M01合成.md").write_text(MODULE_DOC, encoding="utf-8", newline="\n")
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "note.md").write_text("# 说明\n\n无键。\n", encoding="utf-8", newline="\n")
    (root / "protocol").mkdir(parents=True)


def run(argv) -> tuple[int, bytes, bytes]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(argv, capture_output=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def py(snap: Path, scenario: Path, sub: str, *extra: str):
    return run([sys.executable, str(snap / "scripts" / "nf.py"), "asset", sub,
                "--root", str(scenario), *extra])


def engine(cli: Path, scenario: Path, sub: str, *extra: str):
    return run([str(cli), "--root", str(scenario), "asset", sub, *extra])


class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, name: str, ok: bool, detail: str) -> None:
        if ok:
            self.passed += 1
            print(f"  ✓ {name}")
        else:
            self.failed += 1
            print(f"  ✗ {name} —— {detail}")


def parity(rep: Report, name: str, snap: Path, cli: Path, scenario: Path,
           sub: str, *extra: str, expect_rc: int | None = None,
           must_contain: str | None = None) -> tuple[int, bytes, bytes]:
    pe, po, pex = py(snap, scenario, sub, *extra)
    de, do, dex = engine(cli, scenario, sub, *extra)
    same = (pe == de and po == do and pex == dex)
    detail = f"py_rc={pe} dotnet_rc={de}"
    ok = same
    if expect_rc is not None and pe != expect_rc:
        ok = False
        detail += f" · 期望真源 rc={expect_rc}"
    if must_contain is not None and must_contain not in po.decode("utf-8", "replace"):
        ok = False
        detail += f" · 真源输出缺「{must_contain}」"
    if not same:
        detail += ("\n--- PY stdout ---\n" + po.decode("utf-8", "replace")
                   + "\n--- DOTNET stdout ---\n" + do.decode("utf-8", "replace")
                   + "\n--- PY stderr ---\n" + pex.decode("utf-8", "replace")
                   + "\n--- DOTNET stderr ---\n" + dex.decode("utf-8", "replace"))
    rep.check(name, ok, detail)
    return pe, po, pex


def new_scenario(work: Path, name: str) -> Path:
    d = work / name
    if d.exists():
        shutil.rmtree(d)
    build_tree(d)
    return d


def freeze(snap: Path, scenario: Path) -> None:
    """用真源把行数基线与键表投影冻结到合成树（不自造格式）。"""
    for cmd in (["asset", "baseline", "--write", "--root", str(scenario)],
                ["asset", "ledger", "--refresh", "--root", str(scenario)]):
        rc, out, err = run([sys.executable, str(snap / "scripts" / "nf.py"), *cmd])
        if rc != 0:
            raise SystemExit("真源冻结失败 %s：rc=%s\n%s\n%s" % (
                cmd, rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", required=True, help="隔离快照（真源 nf.py 所在仓库）")
    ap.add_argument("--cli", required=True, help="nf-dotnet 可执行文件")
    ap.add_argument("--keep", action="store_true", help="保留合成树（排障用）")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    cli = Path(args.cli).resolve()
    rep = Report()
    work = Path(tempfile.mkdtemp(prefix="nf-asset-quality-"))

    print("== 资产质量五面差分（合成树 · 两侧同树同参数）==")
    try:
        # ⓪ 干净对照：五个面全绿，且两侧逐字节同
        clean = new_scenario(work, "clean")
        freeze(snap, clean)
        for sub in SUBS:
            parity(rep, "干净语料 · " + sub, snap, cli, clean, sub, expect_rc=0)
        for sub in JSON_SUBS:
            parity(rep, "干净语料 · " + sub + " --json", snap, cli, clean, sub, "--json", expect_rc=0)

        # ① 行数基线漂移：内容改动（行数变）→ FAIL 且两边同判
        drift = new_scenario(work, "baseline-drift")
        freeze(snap, drift)
        (drift / "community" / "合成甲包" / "assets" / "ALPHA.md").write_text(
            ASSET_A + "\n新增一行。\n", encoding="utf-8", newline="\n")
        parity(rep, "行数基线 · 内容改动即漂移（FAIL）", snap, cli, drift, "baseline",
               expect_rc=1, must_contain="资产行数与基线不一致")

        # ② 新增包未登记
        newpkg = new_scenario(work, "baseline-newpkg")
        freeze(snap, newpkg)
        (newpkg / "community" / "合成丙包" / "assets").mkdir(parents=True)
        (newpkg / "community" / "合成丙包" / "assets" / "DELTA.md").write_text(
            ASSET_B, encoding="utf-8", newline="\n")
        parity(rep, "行数基线 · 新包未登记（FAIL）", snap, cli, newpkg, "baseline",
               expect_rc=1, must_contain="社区包资产未登记基线")

        # ③ 基线件缺失
        missing = new_scenario(work, "baseline-missing")
        parity(rep, "行数基线 · 缺件（FAIL）", snap, cli, missing, "baseline",
               expect_rc=1, must_contain="缺资产行数基线")

        # ④ schema 不匹配
        bad = new_scenario(work, "baseline-schema")
        freeze(snap, bad)
        bl = bad / "protocol" / "asset_line_baseline.json"
        bl.write_text(bl.read_text(encoding="utf-8").replace("nf-asset-line-baseline/1", "bogus/9"),
                      encoding="utf-8", newline="\n")
        parity(rep, "行数基线 · schema 不匹配（FAIL）", snap, cli, bad, "baseline",
               expect_rc=1, must_contain="schema 不匹配")

        # ⑤ 在册包不在场 → WARN 跳过（不是 FAIL）
        absent = new_scenario(work, "baseline-absent")
        freeze(snap, absent)
        shutil.rmtree(absent / "community" / "合成乙包")
        parity(rep, "行数基线 · 缺包只记 WARN（不翻红）", snap, cli, absent, "baseline",
               expect_rc=0, must_contain="不在场")

        # ⑥ 密度：空档 = FAIL
        empty = new_scenario(work, "density-empty")
        freeze(snap, empty)
        (empty / "community" / "合成甲包" / "assets" / "EMPTY.md").write_text("", encoding="utf-8")
        parity(rep, "密度 · 空档（FAIL）", snap, cli, empty, "density",
               expect_rc=1, must_contain="为空档（0 字符）")
        parity(rep, "密度 · 空档 --json（ok=false）", snap, cli, empty, "density", "--json", expect_rc=1)

        # ⑦ 引用度：零引用键（非 strict 放行、strict 翻红）
        orphan = new_scenario(work, "usage-orphan")
        freeze(snap, orphan)
        (orphan / "community" / "合成甲包" / "assets" / "ORPHANKEY.md").write_text(
            ORPHAN_ASSET, encoding="utf-8", newline="\n")
        parity(rep, "引用度 · 零引用键报告（非 strict 仍 exit 0）", snap, cli, orphan,
               "usage", expect_rc=0, must_contain="ORPHANKEY")
        parity(rep, "引用度 · --strict 零引用即翻红", snap, cli, orphan, "usage", "--strict",
               expect_rc=1, must_contain="零引用 1")
        parity(rep, "引用度 · --strict --json（两侧同判）", snap, cli, orphan, "usage",
               "--strict", "--json", expect_rc=1)

        # ⑧ 厚度：低信息候选（<200 字且无键无小节）
        thin = new_scenario(work, "thickness-low")
        freeze(snap, thin)
        (thin / "community" / "合成甲包" / "assets" / "THIN.md").write_text(
            LOW_INFO_ASSET, encoding="utf-8", newline="\n")
        parity(rep, "厚度 · 低信息候选被列出", snap, cli, thin, "thickness",
               expect_rc=0, must_contain="低信息候选 1")
        parity(rep, "厚度 · --json（low_files 逐条）", snap, cli, thin, "thickness", "--json", expect_rc=0)

        # ⑨ 键表投影：过期（新增键）与缺失
        stale = new_scenario(work, "ledger-stale")
        freeze(snap, stale)
        (stale / "community" / "合成甲包" / "assets" / "ALPHA.md").write_text(
            ASSET_A + "\n新增键 `KEY_NEW` 一行。\n", encoding="utf-8", newline="\n")
        parity(rep, "键表投影 · 过期（FAIL）", snap, cli, stale, "ledger",
               expect_rc=1, must_contain="与资产扫描不一致")
        gone = new_scenario(work, "ledger-missing")
        parity(rep, "键表投影 · 缺件（FAIL）", snap, cli, gone, "ledger",
               expect_rc=1, must_contain="缺失（refresh 生成）")

        # ⑩ 平台口径：`*.md` 大小写不敏感（Windows）/ 点文件不过滤 —— 都必须在面内
        casey = new_scenario(work, "glob-case")
        freeze(snap, casey)
        (casey / "community" / "合成甲包" / "assets" / "UPPER.MD").write_text(
            ASSET_B, encoding="utf-8", newline="\n")
        (casey / "community" / "合成甲包" / "assets" / ".hidden.md").write_text(
            ASSET_B, encoding="utf-8", newline="\n")
        if os.name == "nt":
            parity(rep, "glob · Windows 后缀不分大小写 + 点文件在面内", snap, cli, casey, "density", expect_rc=0)
            _, out, _ = py(snap, casey, "density", "--json")
            files = json.loads(out.decode("utf-8"))["stats"]["files"]
            rep.check("glob · 大小写/点文件确实进了计数（不是静默丢面）", files == 6,
                      "真源计入 %d 档（期望 6：ALPHA/BETA/UPPER.MD/.hidden.md + GAMMA + USER）" % files)
        else:
            rep.check("glob · 非 Windows 走区分大小写分支（本机不适用）", True, "os.name != nt")

        # ⑪ 写面必须明确拒绝（不许半个写面）
        rc, _, _ = engine(cli, clean, "baseline", "--write")
        rep.check("写面 · baseline --write 明确拒绝", rc != 0, "rc=%d" % rc)
        rc, _, _ = engine(cli, clean, "ledger", "--refresh")
        rep.check("写面 · ledger --refresh 明确拒绝", rc != 0, "rc=%d" % rc)
        rc, _, _ = engine(cli, clean, "add", "--key", "X")
        rep.check("写面 · add 明确拒绝", rc != 0, "rc=%d" % rc)
    finally:
        if args.keep:
            print("（合成树保留：%s）" % work)
        else:
            shutil.rmtree(work, ignore_errors=True)

    print("== 汇总：通过 %d · 失败 %d ==" % (rep.passed, rep.failed))
    return 0 if rep.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
