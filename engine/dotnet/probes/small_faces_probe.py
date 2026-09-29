#!/usr/bin/env python3
"""判据面小口三件差分探针（第 69 片）：`explain` / `who-refers` / `diff`。

**为什么要合成语料**：真仓的 registry 里被引声明恰好都是**裸号**，于是「类别感知匹配」与「裸号归一」
两种口径在真语料上**给出同样结果**——正向对账看不出差别。差别只在自己造的 registry 上显形：
声明 `情感:M55` 与 `法律:M55` 时，查 `情感:M55` **不许**命中 `法律:M55`。
这正是本探针存在的理由：**差分证"两边一样"，语料要证"判据真的在判"**。

覆盖：
  · `explain`：all / 编号 / `check<N>` / 未知编号（exit 2）/ 大小写与空白归一；
  · `who-refers`：合成 registry 的类别语义（含裸号声明）/ 裸号查询 / 自定义 `--registry` / 缺件 /
    `asset_readonly` 三态（true / false / 缺键 —— 注意真源末尾那个**尾随空格**）；
  · `diff`：同文档（无差异）/ 只增（additive）/ 移除 refs（需评审）/ 文档编号变更（破坏）/
    缺件（exit 1）/ `--json` 机读面。

纪律：两侧读**同一棵树**；子进程 `subprocess.run`；环境钉 `PYTHONIOENCODING=utf-8`。
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


def run(argv):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(argv, capture_output=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def py(snap: Path, *argv):
    # 这三个面在真源里**没有 `--root`**：`explain` 是静态表，`who-refers` 走 `--registry`，
    # `diff` 的相对路径以 nf.py 所在仓库（ROOT）为基准。故 Python 侧的 ROOT 只能是快照本身。
    return run([sys.executable, str(snap / "scripts" / "nf.py"), *argv])


def engine(cli: Path, engine_root: Path, *argv):
    # 引擎侧同理把 `--root` 钉成**同一个快照**，否则 `diff` 的 `path` 字段两条路不一致。
    return run([str(cli), "--root", str(engine_root), *argv])


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


def parity(rep: Report, name: str, snap: Path, cli: Path, argv,
           *,
           expect_rc: int | None = None, must_contain: str | None = None) -> bytes:
    pe, po, pex = py(snap, *argv)
    de, do, dex = engine(cli, snap, *argv)
    same = (pe == de and po == do and pex == dex)
    detail = f"py_rc={pe} net_rc={de}"
    ok = same
    if expect_rc is not None and pe != expect_rc:
        ok = False
        detail += f" · 期望真源 rc={expect_rc}"
    if must_contain is not None and must_contain not in po.decode("utf-8", "replace"):
        ok = False
        detail += f" · 真源输出缺「{must_contain}」"
    if not same:
        detail += ("\n--- PY stdout ---\n" + po.decode("utf-8", "replace")
                   + "\n--- NET stdout ---\n" + do.decode("utf-8", "replace")
                   + "\n--- PY stderr ---\n" + pex.decode("utf-8", "replace")
                   + "\n--- NET stderr ---\n" + dex.decode("utf-8", "replace"))
    rep.check(name, ok, detail)
    return po


DOC_HEAD = """# 合成文档 {n}

> 元信息行一
> 元信息行二

```yaml
id: M{n}
layer: P0{n}
category: 事件
```

## 章节甲

正文甲，引用 M01。
"""


def write_doc(path: Path, n: int, extra_ref: str = "", drop_ref: bool = False) -> None:
    text = DOC_HEAD.format(n=n)
    if drop_ref:
        text = text.replace("引用 M01。", "不再引用任何模块。")
    if extra_ref:
        text += f"\n## 章节乙\n\n补充引用 {extra_ref}。\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", required=True, help="隔离快照（真源 nf.py 所在仓库）")
    ap.add_argument("--cli", required=True, help="nf-dotnet 可执行文件")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    cli = Path(args.cli).resolve()
    rep = Report()
    work = Path(tempfile.mkdtemp(prefix="nf-small-faces-"))
    print("== 判据面小口三件差分（合成树 · 两侧同树同参数）==")
    try:
        # ---------- explain（静态表：与仓库语料无关，另加归一化用例）
        root = work / "root"
        root.mkdir(parents=True)
        parity(rep, "explain · all（32 条全量）", snap, cli, ["explain", "all"],
               expect_rc=0, must_contain="check32：")
        parity(rep, "explain · 编号", snap, cli, ["explain", "8"], expect_rc=0, must_contain="check8 ==")
        parity(rep, "explain · check 前缀 + 大写 + 空白归一", snap, cli, ["explain", "  Check25  "],
               expect_rc=0, must_contain="check25 ==")
        parity(rep, "explain · 未知编号 → exit 2", snap, cli, ["explain", "99"], expect_rc=2)
        parity(rep, "explain · 非数字 → exit 2", snap, cli, ["explain", "abc"], expect_rc=2)

        # ---------- who-refers（合成 registry：类别语义只在合成语料上显形）
        reg = root / "synth_registry.json"
        reg.write_text(json.dumps({
            "registry_schema_version": "2",
            "protocols": [
                {"id": "包甲", "references": [
                    {"module_id": "情感:M55", "source_package": "源甲", "source_schema_version": "2",
                     "asset_readonly": True},
                    {"module_id": "法律:M55", "source_package": "源乙", "source_schema_version": "2",
                     "asset_readonly": False},
                    {"module_id": "M55", "source_package": "源丙", "source_schema_version": "2"},
                ]},
                {"id": "包乙", "references": [
                    {"module_id": "情感:M55", "source_package": "源丁"},
                ]},
            ],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

        out = parity(rep, "who-refers · 类别查询不越界（情感:M55 不命中 法律:M55）", snap, cli,
                     ["who-refers", "情感:M55", "--registry", str(reg)],
                     expect_rc=0, must_contain="源甲.情感:M55")
        text = out.decode("utf-8", "replace")
        rep.check("who-refers · 类别语义确实生效（合成语料证判据在判，不是空过）",
                  "法律:M55" not in text and "源丙.M55" in text and text.count("→") == 3,
                  f"命中行数={text.count('→')}（期望 3：包甲同类别 + 包乙同类别 + 包甲裸号；不含 法律:M55）")
        out = parity(rep, "who-refers · 裸号查询命中全部同号声明", snap, cli,
                     ["who-refers", "M55", "--registry", str(reg)], expect_rc=0)
        rep.check("who-refers · 裸号查询命中 4 条（裸号查询不看类别）",
                  out.decode("utf-8", "replace").count("→") == 4,
                  f"命中行数={out.decode('utf-8','replace').count('→')}（期望 4：包甲 3 条 + 包乙 1 条）")
        out = parity(rep, "who-refers · asset_readonly 缺键 → 末尾仍带一个空格", snap, cli,
                     ["who-refers", "M55", "--registry", str(reg)], expect_rc=0)
        lines = out.decode("utf-8", "replace").splitlines()
        bare_line = [ln for ln in lines if "源丙.M55" in ln][0]
        rep.check("who-refers · 空 只读 标记时行尾保留一个空格（真源 f-string 口径）",
                  bare_line.endswith("源丙.M55 ") and not bare_line.endswith("源丙.M55  "),
                  f"该行={bare_line!r}")
        parity(rep, "who-refers · registry 缺件 → 无引用（exit 0，不报错）", snap, cli,
               ["who-refers", "M55", "--registry", str(root / "不存在.json")],
               expect_rc=0, must_contain="无（registry")
        parity(rep, "who-refers · 无命中目标", snap, cli,
               ["who-refers", "M99", "--registry", str(reg)], expect_rc=0, must_contain="无（registry")

        # ---------- diff（合成文档对：四条判定分支各走一次）
        docs = root / "docs"
        docs.mkdir()
        write_doc(docs / "01_甲.md", 1)
        write_doc(docs / "01_甲同.md", 1)            # 与 甲 同内容不同文件名 → doc_id 同为 01
        write_doc(docs / "01_甲增.md", 1, extra_ref="M02")
        write_doc(docs / "01_甲减.md", 1, drop_ref=True)
        write_doc(docs / "02_乙.md", 2)

        a = str(docs / "01_甲.md")
        parity(rep, "diff · 同内容 → 兼容 / editorial", snap, cli,
               ["diff", a, str(docs / "01_甲同.md")], expect_rc=0, must_contain="影响度：editorial")
        parity(rep, "diff · 只增引用 → additive", snap, cli,
               ["diff", a, str(docs / "01_甲增.md")], expect_rc=0, must_contain="影响度：additive")
        parity(rep, "diff · 移除引用 → 需评审 / bump", snap, cli,
               ["diff", a, str(docs / "01_甲减.md")], expect_rc=0, must_contain="影响度：bump")
        parity(rep, "diff · 文档编号变更 → 破坏 / bump", snap, cli,
               ["diff", a, str(docs / "02_乙.md")], expect_rc=0, must_contain="影响度：bump")
        parity(rep, "diff · --json 机读面", snap, cli,
               ["diff", a, str(docs / "01_甲增.md"), "--json"], expect_rc=0)
        # 真源把受控报错写 **stderr**（`_cmd_diff` 的 except 分支），故只钉退出码与两侧一致；
        # stderr 的逐字节一致已由 parity 的 stderr 比对覆盖。
        parity(rep, "diff · 缺件 → exit 1（受控报错走 stderr）", snap, cli,
               ["diff", a, str(docs / "不存在.md")], expect_rc=1)
    finally:
        if args.keep:
            print(f"（合成树保留：{work}）")
        else:
            shutil.rmtree(work, ignore_errors=True)

    print(f"== 汇总：通过 {rep.passed} · 失败 {rep.failed} ==")
    return 0 if rep.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
