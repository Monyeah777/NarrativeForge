#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编排面命令行入口：能力目录 / 计划编译 / 机检（core.orchestration 的 agent 入口）。

为什么单独成脚本（而不是 core 模块里的 __main__）：core.orchestration 是**叶子**——它不 import
工具面，工具面由调用方注入。可证的理由（2026-10-03 实测）：编排层 import mcp_runtime 会让
mcp_runtime 的 Ca 5→6、I 0.5→0.4545，直接造出两条 SDP 违例（→ knowledge / → trust_boundary）。
本脚本落在 core 之外，承担「取工具面」这件事，包内耦合度量因此不受影响。

用法：
  python scripts/orchestrate.py --catalog
  python scripts/orchestrate.py --plan <计划.json>
  python scripts/orchestrate.py --check

退出码：0 = 通过；1 = 计划有问题或机检发现问题；2 = 用法错误。
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import mcp_runtime as mrt      # noqa: E402
from core import orchestration as orch   # noqa: E402


def tool_face():
    """运行时工具面（{name: tool_def}）——注入给编排层，模块自己不 import。"""
    return {t["name"]: t for t in mrt.TOOL_DEFS}


def read_plan(path):
    """读计划 JSON（只读；落点合法性由调用方决定，本入口不写盘）。"""
    with open(path, encoding="utf-8") as fh:
        return json.loads(fh.read())


def main(argv):
    ap = argparse.ArgumentParser(description="NF 智能体工具编排：能力目录 / 计划编译 / 机检")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--catalog", action="store_true", help="打印能力目录（JSON）")
    ap.add_argument("--plan", default="", help="计划 JSON 文件；给了就编译并打印顺序与问题")
    ap.add_argument("--check", action="store_true", help="机检工作流映射 ⇄ 运行时工具面")
    args = ap.parse_args(argv)
    tools = tool_face()
    rc = 0
    if args.catalog:
        print(json.dumps(orch.catalog(args.root, tools), ensure_ascii=False,
                         indent=2, sort_keys=True))
    if args.plan:
        res = orch.compile_plan(args.root, read_plan(args.plan), tools)
        print(json.dumps(res, ensure_ascii=False, indent=2, sort_keys=True))
        rc = 0 if res["ok"] else 1
    if args.check:
        issues, stats = orch.scan(args.root, tools)
        for i in issues:
            print("[FAIL] %s" % i, file=sys.stderr)
        print("编排面：工作流 %d · 工具 %d · 映射 %d"
              % (stats["workflows"], stats["tools"], stats["mapped"]))
        if issues:
            rc = 1
    if not (args.catalog or args.plan or args.check):
        issues, stats = orch.scan(args.root, tools)
        print("编排面：工作流 %d · 工具 %d · 映射 %d · 问题 %d"
              % (stats["workflows"], stats["tools"], stats["mapped"], len(issues)))
        rc = 1 if issues else 0
    return rc


if __name__ == "__main__":
    # stdio 钉 UTF-8（同 scripts/nf.py / scripts/verify_run.py 纪律）：中文结论行不该依赖宿主控制台编码。
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
