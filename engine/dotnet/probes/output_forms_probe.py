#!/usr/bin/env python3
"""产出形态面差分探针（第 70 片）：`nf output list` / `nf output check`。

真仓的产出面**几乎全绿**，所以正向对账证不了"判据真的在判"。本探针造一棵合成语料树，
把**每个校验器的 FAIL 分支**都走一遍（JSON 重复键 / CSV 行长 / XML DTD / GraphML 悬空边 /
YAML Tab / Vega 通道未绑定 / Mermaid 图种 / DOT 括号 / quant-metrics 宣称≠实现 /
domain-spec 锚与 id 序 / domain-report 族在册 / combo-cert schema 与摘要），
两侧同参数跑同一批**绝对路径**文件，比 stdout + stderr + 退出码。

两处**已声明的不可比**（探针只断言"两边都判红"，不断言文案相同）：
  ① `toml` 形态：真源用 Python 3.11 `tomllib`，本引擎 BCL-only 无 TOML 解析器 →
     引擎明确报"不可判定"（**不静默放行**）。这是声明边界，不是等价。
  ② JSON/XML **解析失败**的具体文案随各自运行时（CPython 与 System.Text.Json 不同），
     与既有的「断言 regex 异常文案」「平台异常文案」同属不可约类。

用法：python probes/output_forms_probe.py --snap <快照> --cli <nf-dotnet>
退出码：0 = 全部符合预期 · 1 = 存在不一致。
"""
from __future__ import annotations

import argparse
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
    return run([sys.executable, str(snap / "scripts" / "nf.py"), *argv])


def engine(cli: Path, root: Path, *argv):
    return run([str(cli), "--root", str(root), *argv])


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


def declared(rep: Report, name: str, snap: Path, cli: Path, args_list, reason: str,
             py_rc: int | None = None) -> None:
    """已声明的不可比面：钉「引擎给出自己的可读理由且非零退出」；<paramref>py_rc</paramref> 给定时一并钉真源退出码。

    两类用法：① 引擎明确拒绝（Python 放行，如 toml）→ 两边退出码**本应不同**；
    ② 文案随运行时（两边都判红、只是理由文字不同）→ 两边退出码相同但 stdout 不同。
    """
    pe, _po, _ = py(snap, *args_list)
    de, do, _ = engine(cli, snap, *args_list)
    text = do.decode("utf-8", "replace")
    ok = de != 0 and reason in text and (py_rc is None or pe == py_rc)
    rep.check(name, ok, f"py_rc={pe} net_rc={de} · 引擎理由含「{reason}」={reason in text}")


def w(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return str(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()
    snap = Path(args.snap).resolve()
    cli = Path(args.cli).resolve()
    rep = Report()
    work = Path(tempfile.mkdtemp(prefix="nf-output-forms-"))
    print("== 产出形态面差分（合成语料 · 绝对路径 · 两侧同树）==")
    try:
        # ————— 正向对照：五个真实形态（含 T4 面）走一遍
        parity(rep, "正向 · output list", snap, cli, ["output", "list"], expect_rc=0, must_contain="共 116 条")
        parity(rep, "正向 · output list --json", snap, cli, ["output", "list", "--json"], expect_rc=0)
        parity(rep, "正向 · check 真实产出四类", snap, cli, ["output", "check",
               "community/组合包-受监管行业/outputs/COMBO_CERT.json",
               "community/量化金融域包/outputs/QUANT_METRICS.json",
               "community/AI系统域包/outputs/CONCEPT_CLOSURE.json"], expect_rc=0)
        parity(rep, "正向 · 缺件 → 文件不存在（exit 1）", snap, cli, ["output", "check", "不存在的文件.json"],
               expect_rc=1, must_contain="文件不存在")

        d = work / "synth"
        d.mkdir(parents=True, exist_ok=True)

        # ————— JSON：重复键 / 坏 JSON（不可约）
        dup = w(d / "dup.json", '{"a": 1, "b": 2, "a": 3}\n')
        parity(rep, "json · 重复键被抓", snap, cli, ["output", "check", dup], expect_rc=1, must_contain="JSON 重复键：a")
        bad_json = w(d / "bad.json", "{not json\n")

        # ————— JSONL：第 N 行非 JSON
        jsonl = w(d / "rows.jsonl", '{"a": 1}\n坏行\n')

        # ————— CSV：字段数不符 / 表头重名
        csv = w(d / "bad.csv", "a,b,c\n1,2\n")
        parity(rep, "csv · 行长≠表头", snap, cli, ["output", "check", csv], expect_rc=1, must_contain="字段数 2 ≠ 表头 3")
        csv2 = w(d / "duphead.csv", "a,a\n1,2\n")
        parity(rep, "csv · 表头重名列", snap, cli, ["output", "check", csv2], expect_rc=1, must_contain="表头有重名列")

        # ————— XML / SVG：DTD 守卫
        xml = w(d / "dtd.xml", '<?xml version="1.0"?>\n<!DOCTYPE r [<!ENTITY x "y">]>\n<r>&x;</r>\n')
        parity(rep, "xml · DTD/ENTITY 守卫（安全面）", snap, cli, ["output", "check", xml], expect_rc=1,
               must_contain="含 DTD/ENTITY 声明")
        svg = w(d / "dtd.svg", '<svg xmlns="http://www.w3.org/2000/svg"><!ENTITY a "b"></svg>\n')
        parity(rep, "svg · 同一守卫（svg 走 xml 校验器）", snap, cli, ["output", "check", svg], expect_rc=1)

        # ————— Markdown：空档 / 围栏未闭合
        parity(rep, "markdown · 空档", snap, cli, ["output", "check", w(d / "empty.md", "   \n")],
               expect_rc=1, must_contain="空档")
        parity(rep, "markdown · 围栏奇数", snap, cli, ["output", "check", w(d / "fence.md", "# t\n```\nx\n")],
               expect_rc=1, must_contain="代码围栏未闭合")

        # ————— YAML：Tab 缩进 / 非映射项
        parity(rep, "yaml · Tab 缩进", snap, cli, ["output", "check", w(d / "tab.yaml", "a:\n\tb: 1\n")],
               expect_rc=1, must_contain="Tab 缩进")
        parity(rep, "yaml · 非映射行", snap, cli, ["output", "check", w(d / "nomap.yaml", "a: 1\n散行\n")],
               expect_rc=1, must_contain="非映射项")

        # ————— Vega-Lite：缺主体 / 通道未绑定
        vega = w(d / "chart.vega.json", '{"$schema": "https://vega.github.io/schema/vega-lite/v5.json",'
                                        ' "data": {"values": []}, "encoding": {"x": {}}}\n')
        parity(rep, "vega-lite · 缺绘图主体 + 通道未绑定", snap, cli, ["output", "check", vega], expect_rc=1,
               must_contain="缺 mark/layer 等绘图主体")

        # ————— Mermaid：空图 / 未知图种
        parity(rep, "mermaid · 空图", snap, cli, ["output", "check", w(d / "empty.mmd", "%% 只有注释\n")],
               expect_rc=1, must_contain="空图")
        parity(rep, "mermaid · 未知图种", snap, cli, ["output", "check", w(d / "weird.mmd", "wat diagram\n")],
               expect_rc=1, must_contain="首行非已知图种")

        # ————— DOT：缺头 / 括号不配对
        parity(rep, "dot · 缺 digraph 头 + 括号不配对", snap, cli,
               ["output", "check", w(d / "x.dot", "a -> b {\n")], expect_rc=1, must_contain="缺 digraph/graph 头")

        # ————— GraphML：悬空边
        graphml = w(d / "dangling.graphml",
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'
                    '  <graph id="g" edgedefault="directed">\n'
                    '    <node id="a"/>\n    <edge source="a" target="幽灵"/>\n'
                    '  </graph>\n</graphml>\n')
        parity(rep, "graphml · 边端点悬空", snap, cli, ["output", "check", graphml], expect_rc=1,
               must_contain="边端点悬空：target=幽灵")

        # ————— quant-metrics：宣称≠实现 / T4 无 engine / 年化因子不齐 / 重复 id
        qm = w(d / "qm.json", '{"kind": "nf-quant-metrics/1", "metrics": ['
                              '{"id": "A", "engine": "quant_metrics:不存在函数", "required_params": []},'
                              '{"id": "B", "verifiable": "T4", "required_params": []},'
                              '{"id": "C", "annual_factor_required": true, "required_params": []},'
                              '{"id": "A"}],'
                              ' "annual_factors": {"daily": 252}}\n')
        parity(rep, "quant-metrics · 宣称≠实现 / T4 无 engine / 因子不齐 / 重复 id", snap, cli,
               ["output", "check", qm], expect_rc=1, must_contain="宣称≠实现")

        # ————— domain-spec / domain-report
        ds = w(d / "ds.json", '{"kind": "nf-domain-spec/1", "code": "TT", "subdivisions": ['
                              '{"id": "TT-99", "anchor": "ftp://x", "anchor_status": 0}]}\n')
        parity(rep, "domain-spec · 条数/id 序/锚非 URL/锚缺实测", snap, cli, ["output", "check", ds],
               expect_rc=1, must_contain="细分条目应为 12 条")
        dr = w(d / "dr.json", '{"kind": "nf-domain-report/1", "family": "不存在的族",'
                              ' "metrics": {"family": "另一个"}, "sample_rows": 0}\n')
        parity(rep, "domain-report · 族不在册 / family 不一致 / 样例为 0", snap, cli, ["output", "check", dr],
               expect_rc=1, must_contain="度量族未在本仓引擎登记")

        # ————— combo-cert：schema 不合 + 摘要不一致（复算输入含未知包 → 组合非法）
        cc = w(d / "cert.json", '{"schema": "nf-combo/1", "packs": ["不存在的包XYZ"], "digest": "deadbeef"}\n')
        parity(rep, "combo-cert · schema 不合 + 复算不一致 + 组合非法", snap, cli, ["output", "check", cc],
               expect_rc=1, must_contain="证书不合 schema")

        # ————— 两处已声明的不可比
        # 真源对 ruff.toml（合法 TOML）判绿 exit 0；引擎**明确拒绝** exit 1——这正是声明边界的形状：
        # 两边退出码**本应不同**，且引擎理由可读（不静默放行）。
        declared(rep, "已声明①· toml 形态引擎明确拒绝（真源放行 / 引擎拒绝）", snap, cli,
                 ["output", "check", "ruff.toml"], "未内建 TOML 解析器", py_rc=0)
        declared(rep, "已声明②· 坏 JSON 文案随运行时（两边都判红）", snap, cli,
                 ["output", "check", bad_json], "JSON 不可解析", py_rc=1)
        declared(rep, "已声明②· JSONL 坏行文案随运行时（两边都判红）", snap, cli,
                 ["output", "check", jsonl], "第 2 行非 JSON", py_rc=1)

        # ————— 第七十三片补齐的三面（真仓读面）：与真源逐字节同判
        parity(rep, "收口 · output meter", snap, cli, ["output", "meter"], expect_rc=0,
               must_contain="机验率")
        parity(rep, "收口 · output render", snap, cli, ["output", "render"], expect_rc=0)
        parity(rep, "收口 · output render --json", snap, cli, ["output", "render", "--json"], expect_rc=0)
        parity(rep, "收口 · output verify（check32 三合一）", snap, cli, ["output", "verify"], expect_rc=0,
               must_contain="产出形态面一致")
        parity(rep, "收口 · output verify --json", snap, cli, ["output", "verify", "--json"], expect_rc=0)

        # ————— 写面必须明确拒绝（只读门不提供写命令）
        for sub in ("render", "meter"):
            rc, out, err = engine(cli, snap, "output", sub, "--write")
            rep.check(f"写面 · output {sub} --write 明确拒绝",
                      rc != 0 and "不提供写命令" in (out + err).decode("utf-8", "replace"), f"rc={rc}")
    finally:
        if args.keep:
            print(f"（合成树保留：{work}）")
        else:
            shutil.rmtree(work, ignore_errors=True)
    print(f"== 汇总：通过 {rep.passed} · 失败 {rep.failed} ==")
    return 0 if rep.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
