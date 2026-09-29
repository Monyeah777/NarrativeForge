#!/usr/bin/env python3
"""YAML 子集解析等价探针：把**整份 YAML 图**（含标量定型）与 PyYAML 逐字节比对。

为什么单独一面：引擎的 YAML 是自实现的**最小子集**（BCL-only 红线），此前只在「111 包的 5 个字段」
与「模块契约的键」上比过——**值类型从未全量比过**。而 Python 侧一律用 PyYAML：`count: 3` 是 int、
`core_only: true` 是 bool、`010` 是八进制 8、`2026-09-08` 是 date。引擎若当字符串，JSON-Schema
的 `type: integer` / `enum: [True]` 就会判错。

比对口径：
- 两侧都输出 **canonical JSON**（sort_keys + ensure_ascii=False + 紧凑分隔符）后逐字节比对；
- 日期/时间只比**类型标记** `{"__pytype__": "date"|"datetime"}`（值本身不比——两侧 isoformat 形态不同，
  且语料里这三类面**零出现**，故如实收窄，不假装）；
- 引擎侧遇到子集外构造（锚点/块标量/TAB/流映射…）会 fail-closed 抛错 → 单列为「子集外」，
  不计入不一致，但要逐条列出**是什么构造**。

用法：
    python probes/yaml_typing_probe.py --root <快照> --cli <nfparity.exe> [--battery-only]

退出码：0 无不一致；1 有不一致。
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def normalize(node):
    if isinstance(node, (datetime.datetime, datetime.date)):
        return {"__pytype__": type(node).__name__}
    if isinstance(node, dict):
        return {str(k): normalize(v) for k, v in node.items()}
    if isinstance(node, list):
        return [normalize(v) for v in node]
    return node


def canonical(node) -> str:
    return json.dumps(node, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def py_parse(text: str):
    return normalize(yaml.safe_load(text))


def py_parse_fence(text: str, marker: str):
    import re
    for m in re.finditer(r"(?ms)```yaml\s*(.*?)```", text):
        body = m.group(1)
        if marker not in body:
            continue
        try:
            parsed = yaml.safe_load(body)
        except Exception:
            return None
        if isinstance(parsed, dict):
            return normalize(parsed)
    return None


#: 标量/结构电池——覆盖 PyYAML 隐式解析器的关键分叉
BATTERY = [
    "k: 3\n", "k: -3\n", "k: 010\n", "k: 0x1f\n", "k: 0b101\n", "k: 1_000\n",
    "k: 1:30\n", "k: 3.5\n", "k: -0.5\n", "k: .5\n", "k: 1.0e+5\n", "k: 1.0e5\n",
    "k: .inf\n", "k: -.inf\n", "k: .nan\n",
    "k: true\n", "k: True\n", "k: TRUE\n", "k: yes\n", "k: on\n", "k: false\n",
    "k: no\n", "k: off\n", "k: y\n", "k: n\n",
    "k:\n", "k: ~\n", "k: null\n", "k: Null\n", "k: NULL\n", "k: None\n",
    'k: "3"\n', "k: '3'\n", 'k: "true"\n', 'k: "~"\n', "k: 'yes'\n",
    "k: 2026-09-08\n", "k: 2026-9-8\n", 'k: "2026-09-08"\n',
    "k: P40\n", "k: M08\n", "k: 通用:M10\n", "k: v1.2.3\n", "k: ''\n", 'k: ""\n',
    "k: [a, b]\n", "k: []\n", "k: {}\n", "k: [1, true, 3.5]\n", "k: ['1', 1]\n",
    "a:\n  b:\n    c: 1\n", "list:\n  - 1\n  - true\n  - x\n",
    "k: 值 # 行尾注释\n", "k: 有 #井号\n",
]

#: 构造矩阵——**逐类**探边界：块标量 / 锚点别名 / 流式嵌套 / 引号边界 / 注释 / 空白 / 特殊值。
#: 目的不是"应支持"，而是把「引擎 fail-closed 而 PyYAML 接受」的构造**逐条列清楚**，
#: 使子集边界成为**实测结论**而不是注释里的推断。
CONSTRUCTS = [
    # --- 块标量（| 与 >）及其 chomping / indent 指示
    ("block-literal", "k: |\n  第一行\n  第二行\n"),
    ("block-literal-strip", "k: |-\n  第一行\n  第二行\n"),
    ("block-literal-keep", "k: |+\n  第一行\n"),
    ("block-folded", "k: >\n  第一行\n  第二行\n"),
    ("block-folded-strip", "k: >-\n  第一行\n  第二行\n"),
    ("block-literal-empty", "k: |\n"),
    ("block-literal-in-seq", "- |\n  内容\n"),
    ("block-literal-nested", "a:\n  b: |\n    x\n    y\n  c: 1\n"),
    # --- 锚点与别名
    ("anchor-scalar", "a: &x 1\nb: *x\n"),
    ("anchor-map", "a: &m\n  p: 1\nb: *m\n"),
    ("anchor-flow-map", "a: &m {p: 1}\nb: *m\n"),
    ("anchor-seq", "a: &s [1, 2]\nb: *s\n"),
    ("merge-key", "base: &b\n  p: 1\nderived:\n  <<: *b\n  q: 2\n"),
    ("anchor-in-seq", "- &x 1\n- *x\n"),
    # --- 流式嵌套
    ("flow-nested-list", "k: [[1, 2], [3]]\n"),
    ("flow-nested-map", "k: {a: {b: {c: 1}}}\n"),
    ("flow-mixed", "k: {a: [1, {b: 2}], c: []}\n"),
    ("flow-quoted-key", "k: {\"a b\": 1, 'c:d': 2}\n"),
    ("flow-empty-value", "k: {a: , b: 1}\n"),
    ("flow-trailing-comma", "k: [1, 2, ]\n"),
    # --- 引号边界
    ("single-quote-escape", "k: 'it''s'\n"),
    ("double-quote-escape", "k: \"a\\tb\\\\c\\\"d\"\n"),
    ("double-quote-unicode", "k: \"\\u4e2d\\u6587\"\n"),
    ("double-quote-hex", "k: \"\\x41\"\n"),
    ("quote-multiline-double", "k: \"第一行\n  第二行\"\n"),
    ("quote-with-colon", "k: 'a: b'\n"),
    # --- 注释与空白
    ("comment-line", "# 整行注释\nk: 1\n"),
    ("comment-after-flow", "k: [1, 2] # 注释\n"),
    ("comment-before-key", "k: 1\n# 注释\nj: 2\n"),
    ("trailing-spaces", "k: 1   \nj: 2\n"),
    ("blank-lines", "\n\nk: 1\n\n\nj: 2\n"),
    ("tab-indent", "k:\n\tj: 1\n"),
    ("crlf", "k: 1\r\nj: 2\r\n"),
    # --- 特殊值
    ("sexagesimal", "k: 1:30:30\n"),
    ("sexagesimal-float", "k: 1:30.5\n"),
    ("octal-old", "k: 0755\n"),
    ("hex", "k: 0xFF\n"),
    ("plus-int", "k: +7\n"),
    ("underscore-int", "k: 1_000_000\n"),
    ("negative-zero", "k: -0\n"),
    ("dot-nan", "k: .NaN\n"),
    ("datetime-tz", "k: 2026-09-08T10:20:30Z\n"),
    ("datetime-space", "k: 2026-09-08 10:20:30\n"),
    ("empty-value-null", "k:\nj: 1\n"),
    ("tilde-null", "k: ~\n"),
    # --- 序列形态
    ("seq-of-seq", "k:\n  - [1, 2]\n  - [3]\n"),
    ("seq-of-maps-nested", "k:\n  - a: 1\n    b:\n      - x\n"),
    ("nested-seq-in-map", "k:\n  a:\n    - 1\n    - 2\n"),
    ("empty-seq-items", "k:\n  -\n  - 1\n"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--battery-only", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="nf-yaml-probe-"))
    mismatches, outside, total = [], [], 0

    def compare(label: str, text: str, fence_marker: str = ""):
        nonlocal total
        total += 1
        path = tmp / ("case.yaml")
        path.write_text(text, encoding="utf-8", newline="\n")
        argv = [args.cli, "--yaml-fence", str(path), fence_marker] if fence_marker \
            else [args.cli, "--yaml-dump", str(path)]
        proc = subprocess.run(argv, capture_output=True)
        try:
            expected = canonical(py_parse_fence(text, fence_marker) if fence_marker
                                 else py_parse(text))
        except Exception as exc:                       # PyYAML 自己就拒（如非法日期）
            expected = "PY_ERROR:" + type(exc).__name__
        if proc.returncode != 0:
            outside.append((label, proc.stderr.decode("utf-8", "replace").strip()[:120]))
            return
        got = proc.stdout.decode("utf-8").strip()
        if got != expected:
            mismatches.append((label, expected, got))

    for i, sample in enumerate(BATTERY):
        compare("battery#%d %s" % (i, sample.strip()[:28]), sample)

    for name, sample in CONSTRUCTS:
        compare("construct:" + name, sample)

    if not args.battery_only:
        for f in sorted(glob.glob(os.path.join(root, "community", "*", "protocol.yaml"))):
            compare("protocol.yaml " + os.path.basename(os.path.dirname(f)),
                    Path(f).read_text(encoding="utf-8"))
        module_docs = [os.path.join(dp, f)
                       for dp, _d, fs in os.walk(root / "04_模块库") for f in fs if f.endswith(".md")]
        module_docs += sorted(glob.glob(os.path.join(root, "community", "*", "modules", "*.md")))
        pipe_docs = [os.path.join(dp, f)
                     for dp, _d, fs in os.walk(root / "03_管线库") for f in fs if f.endswith(".md")]
        pipe_docs += sorted(glob.glob(os.path.join(root, "community", "*", "pipelines", "*.md")))
        for f in module_docs:
            compare("machine_contract " + os.path.relpath(f, root),
                    Path(f).read_text(encoding="utf-8"), "machine_contract")
        for f in pipe_docs:
            compare("Pipeline " + os.path.relpath(f, root),
                    Path(f).read_text(encoding="utf-8"), "Pipeline:")

    print("YAML 等价：%d 面 · 不一致 %d · 子集外（引擎 fail-closed）%d"
          % (total, len(mismatches), len(outside)))
    if outside:
        # 子集边界**逐条列出**（按构造类别聚合），使"支持到哪"是实测结论而非注释里的推断
        print("  子集外构造（引擎 fail-closed，PyYAML 接受）——边界清单：")
        for label, err in outside:
            print("    · %-28s %s" % (label.replace("construct:", ""), err[:70]))
    for label, expected, got in mismatches[:15]:
        print("  [不一致] %s\n      期望 %s\n      实得 %s" % (label, expected[:150], got[:150]))
    for label, err in outside[:10]:
        print("  [子集外] %s → %s" % (label, err))
    if len(outside) > 10:
        print("  …另有 %d 条子集外（引擎明确 fail-closed，不静默误解析）" % (len(outside) - 10))
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
