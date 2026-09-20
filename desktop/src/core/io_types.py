"""模块 I/O 类型面（`machine_contract.io_types`，字段级新增 · 01 §7 V1）。

NF 的 `inputs`/`outputs` 一直是**裸字符串**：能查"谁连谁"，查不了"连的是什么类型"。
本模块给机读契约加一层**可选类型面**（机制借鉴 Pipelex 的 typed concepts），
并给出**可证**的类型检查——只判可证的不匹配，不给未收窄的字段编类型。

字段形状（干净 YAML，自带行解析器，不引第三方）：

```yaml
machine_contract:
  io_types:
    outputs:
      tick: number          # token → 类型
    inputs:
      M00: state            # 依赖模块 → 期望产物类型
```

词表：`string|integer|number|boolean|array|object|event|state|untyped`。
`untyped` 是**合法值**（显式标注「尚未收窄」），与 `protocol/event_registry.json`
的既有措辞一致；**不得**为省事编造具体类型。

retro-fit 取值规则（确定性、有据可依，非人工猜测）：
1. `outputs[token]` = `event_registry.json` 里同名事件字段的类型（**证据来源**）；
   未命中 → `untyped`。
2. `inputs[M00]` = `state`（数据槽基座）；其余依赖 → `untyped`。
3. 无机读契约（L0）的模块**无法承载**本字段——计入覆盖缺口，不假装已标。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

KINDS = ("string", "integer", "number", "boolean", "array", "object",
         "event", "state", "untyped")
EVENT_REGISTRY = "protocol/event_registry.json"
_IO_RE = re.compile(r"^(\s*)io_types:\s*$")
_SUB_RE = re.compile(r"^(\s*)(outputs|inputs):\s*(\{\})?\s*$")
_PAIR_RE = re.compile(r"^(\s*)([^:\s]+):\s*(\S+)\s*$")


def event_field_types(root: str = ".") -> Dict[str, str]:
    """事件载荷字段 → 类型（跨事件取首个声明；NF 既有类型证据源）。"""
    p = Path(root) / EVENT_REGISTRY
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    out: Dict[str, str] = {}
    for body in (data.get("events") or {}).values():
        for field, spec in (body.get("fields") or {}).items():
            kind = spec.get("type") if isinstance(spec, dict) else None
            if kind in KINDS:
                out.setdefault(field, kind)
    return out


def derive(outputs: List[str], inputs: List[str],
           ev_types: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, str]]:
    """按上文规则确定性推导 io_types（未命中一律 `untyped`，不编造）。"""
    ev = ev_types or {}
    return {
        "outputs": {str(t): ev.get(str(t), "untyped") for t in outputs},
        "inputs": {str(m): ("state" if str(m) in ("M00", "通用:M00") else "untyped")
                   for m in inputs},
    }


def parse_io_types(text: str) -> Optional[Dict[str, Dict[str, str]]]:
    """从 machine_contract 围栏里读 io_types（行式解析；无则 None）。"""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if _IO_RE.match(ln):
            start = i
            base = len(_IO_RE.match(ln).group(1))
            break
    if start is None:
        return None
    out: Dict[str, Dict[str, str]] = {"outputs": {}, "inputs": {}}
    sub = None
    for ln in lines[start + 1:]:
        if not ln.strip():
            continue
        indent = len(ln) - len(ln.lstrip())
        if indent <= base:
            break
        sm = _SUB_RE.match(ln)
        if sm:
            sub = sm.group(2)
            if sm.group(3):          # `outputs: {}` / `inputs: {}` —— 显式空段
                out[sub] = {}
            continue
        pm = _PAIR_RE.match(ln)
        if pm and sub in out:
            out[sub][pm.group(2)] = pm.group(3)
    return out


def render_io_types(io: Dict[str, Dict[str, str]], indent: str = "  ") -> str:
    body = ["%sio_types:" % indent]
    for sec in ("outputs", "inputs"):
        pairs = io.get(sec, {})
        if not pairs:
            body.append("%s  %s: {}" % (indent, sec))   # 空段写 {} —— 避免解析成 None
            continue
        body.append("%s  %s:" % (indent, sec))
        for k, v in io.get(sec, {}).items():
            body.append("%s    %s: %s" % (indent, k, v))
    return "\n".join(body)


def inject(text: str, io: Dict[str, Dict[str, str]]) -> str:
    """把 io_types 写进第一个 machine_contract 围栏（幂等：已有则整体替换）。"""
    lines = text.splitlines()
    io_start = next((i for i, ln in enumerate(lines) if _IO_RE.match(ln)), None)
    if io_start is not None:
        base = len(_IO_RE.match(lines[io_start]).group(1))
        end = io_start + 1
        while end < len(lines):
            ln = lines[end]
            if ln.strip() and (len(ln) - len(ln.lstrip())) <= base:
                break
            end += 1
        block = render_io_types(io).splitlines()
        lines[io_start:end] = block
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    # 插在 interfaces: 行之后（机读块尾部）；找不到就插在围栏闭合前
    fence_open = fence_close = None
    for i, ln in enumerate(lines):
        if ln.strip() == "```yaml" and fence_open is None:
            fence_open = i
        elif fence_open is not None and ln.strip().startswith("```"):
            fence_close = i
            break
    if fence_open is None or fence_close is None:
        return text
    anchor = fence_close
    block = render_io_types(io)
    lines[anchor:anchor] = block.splitlines()
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _modules(root: str = ".") -> List[Tuple[str, str, Dict[str, Any], Any]]:
    from core import conformance_scan as csc

    rows = []
    for doc in csc._module_docs(root):
        text = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        rows.append((Path(doc).relative_to(root).as_posix(), text, mc or {}, doc))
    return rows


def apply(root: str = ".", write: bool = False) -> List[Dict[str, Any]]:
    """给全部**有机读契约**的模块补 io_types（幂等）→ 变更清单。"""
    ev = event_field_types(root)
    out = []
    for rel, text, mc, doc in _modules(root):
        if not mc or not mc.get("id"):
            continue
        io = derive([str(x) for x in (mc.get("outputs") or [])],
                    [str(x) for x in (mc.get("inputs") or [])], ev)
        new = inject(text, io)
        changed = new != text
        if changed and write:
            Path(doc).write_text(new, encoding="utf-8", newline="\n")
        out.append({"path": rel, "id": str(mc.get("id")), "changed": changed,
                    "io_types": io})
    return out


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：可证不匹配/越词表 = FAIL；未收窄/L0 = WARN。"""
    issues: List[str] = []
    warns: List[str] = []
    rows = _modules(root)
    typed = untyped = 0
    provided: Dict[str, Dict[str, str]] = {}
    l0 = []
    for rel, text, mc, _doc in rows:
        mid = str(mc.get("id") or "")
        if not mid:
            l0.append(rel)
            continue
        io = parse_io_types(text)
        if io is None:
            warns.append("%s 未标 io_types（修复指引：nf module types --write）" % mid)
            continue
        for sec in ("outputs", "inputs"):
            for key, kind in (io.get(sec) or {}).items():
                if kind not in KINDS:
                    issues.append("%s io_types.%s.%s 类型越词表：%s（%s）"
                                  % (mid, sec, key, kind, "/".join(KINDS)))
                if kind == "untyped":
                    untyped += 1
                else:
                    typed += 1
        declared = {str(x) for x in (mc.get("outputs") or [])}
        marked = set((io.get("outputs") or {}).keys())
        if declared != marked:
            warns.append("%s io_types.outputs 与 outputs 键集不一致（缺 %s / 多 %s）"
                         % (mid, sorted(declared - marked), sorted(marked - declared)))
        provided[mid] = io.get("outputs") or {}
    # 可证不匹配：消费方声明期望类型，提供方有类型声明但无一匹配
    for rel, text, mc, _doc in rows:
        mid = str(mc.get("id") or "")
        io = parse_io_types(text) if mid else None
        if not io:
            continue
        for dep, want in (io.get("inputs") or {}).items():
            if want in ("untyped", "state"):
                continue
            got = provided.get(dep)
            if got and want not in set(got.values()):
                issues.append("类型不匹配：%s 期望 %s 提供 %s，但 %s 声明输出类型为 %s"
                              "（修复指引：对齐 io_types 或改依赖）"
                              % (mid, dep, want, dep, sorted(set(got.values()))))
    stats = {"modules_with_contract": len(rows) - len(l0), "l0_modules": len(l0),
             "typed_fields": typed, "untyped_fields": untyped}
    if l0:
        warns.append("无机读契约（L0，无法承载 io_types）共 %d 件：%s"
                     % (len(l0), "、".join(l0[:3])))
    return issues, warns, stats


def coverage(root: str = ".") -> Dict[str, Any]:
    """类型面覆盖率（供报告/门禁展示，不用来判死）。"""
    _i, _w, stats = scan(root)
    total = stats["typed_fields"] + stats["untyped_fields"]
    stats["coverage"] = round(100.0 * stats["typed_fields"] / total, 1) if total else 0.0
    return stats
