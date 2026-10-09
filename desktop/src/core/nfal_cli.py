"""NFA-L · CLI 面（python -m core.nfal_cli；或经 nf nfal 透传）。

只做编排：解析参数 → 调 core.nfal 的前端/后端 → 打印 JSON 或人读摘要。
退出码沿用 argparse 约定：0 通过 · 1 判据失败 · 2 用法错误。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from core import nfal
from core.schema_lint import subset_key_violations, subset_validate


def _print(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2))


def _load_state(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="NF 仓库根（真源：world_slots / event_registry / schema）")
    ap = argparse.ArgumentParser(prog="nf nfal",
                                 description="NFA-L：NF 声明式(借 YAML/IDL) + 命令式(封闭 guard 表达式) 混合前端/后端")
    ap.add_argument("--root", default=".", help="NF 仓库根")
    sub = ap.add_subparsers(dest="nfal_cmd", required=True)

    p_parse = sub.add_parser("parse", parents=[common], help="表达式 → AST（规范 JSON）")
    p_parse.add_argument("expr")

    p_check = sub.add_parser("check", parents=[common], help="静态检查表达式（名字 + 类型）")
    p_check.add_argument("expr")
    p_check.add_argument("--tokens", action="store_true", help="附带模块产出 token 面（较慢）")

    p_build = sub.add_parser("build", parents=[common], help="管线 → NFIR（前端主链）")
    p_build.add_argument("pipeline")
    p_build.add_argument("--strict", action="store_true", help="散文 condition 记 fail（默认 advisory）")
    p_build.add_argument("--no-tokens", action="store_true", help="跳过模块索引（token 面为空）")

    p_eval = sub.add_parser("eval", parents=[common], help="后端：对各 guard 三值求值")
    p_eval.add_argument("pipeline")
    p_eval.add_argument("--state", required=True, help="抽象状态 JSON（按 world_slots 全名嵌套）")
    p_eval.add_argument("--no-tokens", action="store_true")

    p_schema = sub.add_parser("schema-check", parents=[common], help="用仓库自实现 JSON-Schema 子集校验管线声明")
    p_schema.add_argument("pipeline")
    return ap


def _cmd_parse(args: argparse.Namespace) -> int:
    from core.nf_expr import parse, strip_pos
    try:
        ast = parse(args.expr)
    except Exception as exc:  # noqa: BLE001 —— CLI 边界：任何解析失败都以诊断给出
        _print({"schema": nfal.SCHEMA, "kind": "nfal-parse", "verdict": "fail",
                "diagnostics": [{"code": "E0201", "severity": "fail", "message": str(exc), "pos": 0}]})
        return 1
    _print({"schema": nfal.SCHEMA, "kind": "nfal-parse", "verdict": "pass", "ast": strip_pos(ast)})
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    sym = nfal.SymbolTable.from_repo(args.root, with_tokens=args.tokens)
    res = nfal.check_expression(args.expr, sym)
    _print(res)
    return 1 if res["verdict"] == "fail" else 0


def _cmd_build(args: argparse.Namespace) -> int:
    ir = nfal.build_ir(args.root, args.pipeline, with_tokens=not args.no_tokens, strict=args.strict)
    from core.nfal import canonical
    print(canonical(ir), end="")
    return 1 if ir["verdict"] == "fail" else 0


def _cmd_eval(args: argparse.Namespace) -> int:
    ir = nfal.build_ir(args.root, args.pipeline, with_tokens=not args.no_tokens)
    env = _load_state(args.state)
    rows: List[Dict[str, Any]] = []
    any_fail = False
    for edge in ir["edges"]:
        guard = edge["guard"]
        if guard["source"] == "prose" or guard["ast"] is None:
            rows.append({"from": edge["from"], "to": edge["to"], "guard": guard["expr"],
                         "verdict": "abstain", "reason": "散文 guard 不可机验（fail-closed）"})
            continue
        res = nfal.eval_guard(guard["ast"], env)
        if res["verdict"] == "fail":
            any_fail = True
        rows.append({"from": edge["from"], "to": edge["to"], "guard": guard["expr"],
                     "verdict": res["verdict"], "value": res["value"],
                     "diagnostics": res["diagnostics"]})
    _print({"schema": nfal.SCHEMA, "kind": "nfal-eval", "pipeline": ir["pipeline"]["id"],
            "edges": rows, "verdict": "fail" if any_fail else "pass"})
    return 1 if any_fail else 0


def _cmd_schema_check(args: argparse.Namespace) -> int:
    root = Path(args.root)
    schema = json.loads((root / "protocol" / "schema" / "pipeline.schema.json").read_text(encoding="utf-8"))
    decl = nfal.load_decl(args.root, args.pipeline)
    issues = subset_key_violations(schema) + subset_validate(decl, schema)
    _print({"schema": nfal.SCHEMA, "kind": "nfal-schema", "artifact": args.pipeline,
            "verdict": "fail" if issues else "pass", "issues": issues})
    return 1 if issues else 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "help":        # nf nfal help：nf.py 用 REMAINDER 透传，help 到这里
        _parser().print_help()
        return 0
    args = _parser().parse_args(argv)
    if args.nfal_cmd == "parse":
        return _cmd_parse(args)
    if args.nfal_cmd == "check":
        return _cmd_check(args)
    if args.nfal_cmd == "build":
        return _cmd_build(args)
    if args.nfal_cmd == "eval":
        return _cmd_eval(args)
    if args.nfal_cmd == "schema-check":
        return _cmd_schema_check(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
