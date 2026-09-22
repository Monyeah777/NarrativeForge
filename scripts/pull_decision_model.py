#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决策层候选模型的**拉取与启动脚手架**（非门禁 · 默认只打印，不擅自下载）。

为什么默认不下载：候选是 300M–9B 级权重（Open-Jev 还需 base 模型 + GPU），
下载动辄数 GB 到数十 GB 且依赖本机显存/磁盘——**这类不可逆的资源消耗由作者决定**。
本工具把「拉什么、从哪拉、许可是什么、怎么起服务」打印成可核对的命令，
`--run --yes` 才真的执行。

用法：
  python scripts/pull_decision_model.py --list
  python scripts/pull_decision_model.py --candidate laya-multilingual            # 打印命令
  python scripts/pull_decision_model.py --candidate open-jev-9b --serve          # 打印服务命令
  python scripts/pull_decision_model.py --candidate laya-multilingual --run --yes
退出码：0 正常 / 2 用法错误（缺 --yes 等）/ 1 执行失败。
纪律：只读仓库声明；不写 protocol/；不静默降级（缺依赖即报错并给修复指引）。
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

DECL_REL = "protocol/decision_layer.json"


def _render(argv: List[str]) -> str:
    """argv → 可复制的命令串（Windows 用 list2cmdline，POSIX 用 shlex.quote）。"""
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return " ".join(shlex.quote(part) for part in argv)

#: 每候选的拉取/启动命令（**argv 列表**，绝不经 shell——避免注入面；形态取自各模型卡实证）
PLANS: Dict[str, Dict[str, List[List[str]]]] = {
    "laya-typed-decisions": {
        "pull": [["hf", "download", "convaiinnovations/laya-typed-decisions",
                  "--local-dir", "{dir}"]],
        "serve": [["python", "-c",
                   "import laya; agent = laya.load('{dir}'); print('laya loaded:', agent)"]],
    },
    "laya-multilingual": {
        "pull": [["hf", "download", "convaiinnovations/laya-multilingual",
                  "--local-dir", "{dir}"]],
        "serve": [["python", "-c",
                   "import laya; agent = laya.load('{dir}'); print('laya loaded:', agent)"]],
    },
    "open-jev-9b": {
        "pull": [["git", "clone", "https://github.com/Zefan-Cai/Open-Jev.git"],
                 ["python", "-m", "pip", "install", "-e", "./Open-Jev[train]"],
                 ["hf", "download", "ZefanCai/Open-Jev-9B", "--local-dir", "{dir}"]],
        "serve": [["python", "-m", "jev.server", "--checkpoint",
                   "{dir}/package/checkpoint", "--device", "cuda:0",
                   "--max-length", "4096", "--batch-size", "1",
                   "--host", "127.0.0.1", "--port", "8791"]],
    },
}


def _decl(root: Path) -> Dict[str, Any]:
    p = root / DECL_REL
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _candidate(decl: Dict[str, Any], cid: str) -> Dict[str, Any]:
    for c in decl.get("candidates") or []:
        if str(c.get("id")) == cid:
            return c
    return {}


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="决策层候选模型拉取脚手架（默认只打印）")
    ap.add_argument("--root", default=".", help="仓库根（缺省当前目录）")
    ap.add_argument("--list", action="store_true", help="列出候选（来源/许可/实证要点/是否已拉取）")
    ap.add_argument("--candidate", default="", help="候选 id（见 --list）")
    ap.add_argument("--dir", default="", help="本地落盘目录（缺省 checkpoints/<id>）")
    ap.add_argument("--serve", action="store_true", help="同时打印服务启动命令与 NF 侧对接参数")
    ap.add_argument("--run", action="store_true", help="真的执行（须同时给 --yes）")
    ap.add_argument("--yes", action="store_true", help="确认承担下载与磁盘/显存消耗")
    args = ap.parse_args(argv)
    root = Path(args.root)
    decl = _decl(root)
    if not decl:
        print("  ✗ 缺声明件 %s（修复指引：先落协议层声明件）" % DECL_REL, file=sys.stderr)
        return 2

    if args.list or not args.candidate:
        print("== 决策层候选模型（声明真源：%s）==" % DECL_REL)
        for c in decl.get("candidates") or []:
            print("  %-22s %-42s 许可=%s 已拉取=%s"
                  % (c.get("id"), c.get("source"), c.get("license"), c.get("pulled")))
            print("      实证：%s" % str(c.get("evidence"))[:150])
        print("  打印命令：--candidate <id>[ --serve]；执行：--run --yes")
        return 0

    cand = _candidate(decl, args.candidate)
    if not cand:
        print("  ✗ 未登记的候选：%s（可选：%s）"
              % (args.candidate,
                 "、".join(str(c.get("id")) for c in decl.get("candidates") or [])),
              file=sys.stderr)
        return 2
    cid = str(cand.get("id"))
    dest = args.dir or ("checkpoints/%s" % cid)
    plan = PLANS.get(cid, {})
    if not plan:
        print("  ✗ 该候选尚无拉取计划（修复指引：在 scripts/pull_decision_model.py 的 PLANS 补命令）",
              file=sys.stderr)
        return 2
    cmds = [[part.format(dir=dest) for part in argv] for argv in plan.get("pull", [])]
    print("== 候选 %s ==" % cid)
    print("  来源：%s" % cand.get("source"))
    print("  许可：%s" % cand.get("license"))
    print("  落盘：%s" % dest)
    print("  实证要点：%s" % cand.get("evidence"))
    for argv in cmds:
        print("  $ %s" % _render(argv))
    if args.serve:
        for argv in plan.get("serve", []):
            print("  （服务）$ %s" % _render([p.format(dir=dest) for p in argv]))
        print("  NF 侧对接：python scripts/nf.py decide --adapter systemone-http "
              "--endpoint http://127.0.0.1:8791/v1/systemone --state <state.txt> "
              "--questions <questions.json>")

    if not args.run:
        print("  （未执行：加 --run --yes 才真的下载。NF 不替作者决定下载数 GB 权重）")
        return 0
    if not args.yes:
        print("  ✗ --run 需同时给 --yes（确认承担下载 + 磁盘/显存消耗）", file=sys.stderr)
        return 2
    exe = shutil.which("hf") or shutil.which("huggingface-cli")
    needs_hf = any(argv and argv[0] == "hf" for argv in cmds)
    if needs_hf and not exe:
        print("  ✗ 缺 hf CLI（修复指引：pip install -U huggingface_hub，或改用 git lfs 拉取）",
              file=sys.stderr)
        return 2
    for argv in cmds:
        real = list(argv)
        if real and real[0] == "hf" and exe:
            real[0] = exe
        print("  $ %s" % _render(real))
        rc = subprocess.run(real).returncode
        if rc != 0:
            print("  ✗ 命令失败（退出码 %d）——已如实中止，不静默降级" % rc, file=sys.stderr)
            return 1
    print("  ✓ 拉取完成：%s（记得回来把声明件里的 pulled 置 true）" % dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
