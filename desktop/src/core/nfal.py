"""NFA-L 中端/后端 · 符号面 + 静态检查 + 三值求值 + NFIR。

定位：声明层（YAML 围栏 + protocol/schema 的 JSON-Schema IDL）不变，本模块补命令层——
把 Pipeline.structure.flow[].condition 从自由字符串升为可静态检查、可执行、可复算的
guard 表达式（见 core.nf_expr）。

边缘全借（不新造第二份事实）：
- 世界状态符号 = protocol/world_slots.json 的 slots（登记全名 + kind）
- 事件符号   = protocol/event_registry.json 的 events
- token 面   = 模块 machine_contract 的 outputs + io_types（复用 core.pipelinerun 索引）
- 类型词表   = 01 第 7 节 io_types
- 判决三态   = core.decision_layer 的 pass/fail/abstain（abstain 永不折算 pass）
- 声明装载 / 形状校验 = core.conformance_scan / core.schema_lint（不重实现）

命令层是封闭小核：函数集见 FUNCS，无用户函数、无循环、无赋值、无 I/O。
纯标准库；只读无副作用（除 CLI 层的打印）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.nf_expr import LexError, ParseError, parse, strip_pos

SCHEMA = "nf-nfal/1"
#: 命令层进入记号：condition 以 '=' 开头即按 nf-expr 解析；否则视为既有散文（advisory）。
EXPR_PREFIX = "="
_KIND_MAP = {
    "string": "string", "integer": "int", "number": "number", "boolean": "bool",
    "array": "list", "object": "map", "event": "event", "state": "map", "untyped": "untyped",
}
_LIT_TYPES = {"bool": "bool", "int": "int", "float": "number", "str": "string", "null": "null"}
NUMERIC = ("int", "number")
#: 封闭函数集（借 CEL 的「标准函数 + 无用户函数」纪律）：名 → (参数类型表, 返回类型)
FUNCS: Dict[str, Tuple[Tuple[str, ...], str]] = {
    "size": (("list|map|string",), "int"),
    "contains": (("string|list", "any"), "bool"),
    "has": (("map", "string"), "bool"),
    "startsWith": (("string", "string"), "bool"),
    "int": (("any",), "int"),
    "string": (("any",), "string"),
}
_IMPLICIT_TRUE: Dict[str, Any] = {"k": "lit", "t": "bool", "v": True}


class _Unknown:
    """未知值哨兵（三值逻辑的第三值；与 None 区分）。"""

    def __repr__(self) -> str:
        return "UNKNOWN"


UNKNOWN = _Unknown()


def diag(code: str, severity: str, message: str, pos: int = 0) -> Dict[str, Any]:
    """诊断行（与 NF 既有 fail/warn 口径同形）。"""
    return {"code": code, "severity": severity, "message": message, "pos": pos}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):  # 读不到/坏件 ⇒ None（调用方如实少给符号，不臆造；失败语义同 docstring）
        return None


def _kind_to_type(kind: Optional[str]) -> str:
    return _KIND_MAP.get(str(kind or "untyped"), "untyped")


def _accepts(expected: str, actual: str) -> bool:
    if expected == "any" or actual in ("unknown", "untyped"):
        return True
    return actual in expected.split("|")


def _load_state_kinds(root: Path) -> Dict[str, str]:
    data = _read_json(root / "protocol" / "world_slots.json")
    slots = data.get("slots") if isinstance(data, dict) else None
    if not isinstance(slots, dict):
        return {}
    # 存 io_types 原始词（映射只在 SymbolTable.resolve 做一次，避免双重映射把 int 变 untyped）
    return {str(k): str((v or {}).get("kind") or "untyped") for k, v in slots.items()}


def _load_events(root: Path) -> set:
    data = _read_json(root / "protocol" / "event_registry.json")
    events = data.get("events") if isinstance(data, dict) else None
    return set(events.keys()) if isinstance(events, dict) else set()


def _io_kinds(text: str) -> Dict[str, str]:
    """模块 machine_contract 的 outputs 类型面（io_types 词表；缺件记 untyped）。"""
    try:
        from core import io_types as iot
        data = iot.parse_io_types(text) or {}
        return {str(k): str(v) for k, v in (data.get("outputs") or {}).items()}
    except Exception:  # noqa: BLE001 —— 词表不可用 ⇒ 类型记 untyped（合法值，不臆造）
        return {}


def _load_tokens(root: Path, module_refs: Optional[List[str]]) -> Dict[str, str]:
    """token 面 = 模块 machine_contract 的 outputs + io_types。

    借统一围栏解析 conformance_scan 与 io_types 词表；**不依赖 pipelinerun**——
    更稳的模块不得依赖更不稳的模块（SDP 不变量，见 coupling_metrics）。
    """
    try:
        from core import conformance_scan as csc
    except Exception:  # noqa: BLE001 —— 围栏解析不可用 ⇒ 无 token 面（如实缺口，不伪造）
        return {}
    wanted = {str(x) for x in (module_refs or [])}
    bare = {x.split(":")[-1] for x in wanted}
    tokens: Dict[str, str] = {}
    for doc in csc._module_docs(str(root)):
        try:
            text = Path(doc).read_text(encoding="utf-8")
        except OSError:  # 该模块文档读不到 ⇒ 跳过它（不臆造其 outputs；缺件如实少给 token）
            continue
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if not isinstance(mc, dict):
            continue
        mid = str(mc.get("id") or "")
        if wanted and mid not in wanted and mid.split(":")[-1] not in bare:
            continue
        kinds = _io_kinds(text)
        for tok in mc.get("outputs") or []:
            tokens.setdefault(str(tok), str(kinds.get(str(tok)) or "untyped"))
    return tokens


class SymbolTable:
    """guard 的名字/类型面（只读快照；未登记即缺，不臆造）。"""

    def __init__(self, state: Optional[Dict[str, str]] = None,
                 events: Optional[set] = None,
                 tokens: Optional[Dict[str, str]] = None,
                 inputs: Optional[Dict[str, str]] = None) -> None:
        self.state = dict(state or {})
        self.events = set(events or set())
        self.tokens = dict(tokens or {})
        self.inputs = dict(inputs or {})

    @classmethod
    def from_repo(cls, root: str = ".", module_refs: Optional[List[str]] = None,
                  with_tokens: bool = False) -> "SymbolTable":
        r = Path(root)
        tokens = _load_tokens(r, module_refs) if with_tokens else {}
        return cls(state=_load_state_kinds(r), events=_load_events(r), tokens=tokens)

    def resolve(self, path: List[str]) -> Optional[str]:
        """登记全名 → 类型；未登记返回 None（不猜、不模糊匹配）。"""
        full = ".".join(path)
        if full in self.state:
            return _kind_to_type(self.state[full])
        if full.startswith("state.") and full[6:] in self.state:   # 可选前缀：真源是登记全名
            return _kind_to_type(self.state[full[6:]])
        if len(path) == 2 and path[0] == "event" and path[1] in self.events:
            return "bool"
        if len(path) == 2 and path[0] == "token" and path[1] in self.tokens:
            return _kind_to_type(self.tokens[path[1]])
        if len(path) == 2 and path[0] == "input" and path[1] in self.inputs:
            return _kind_to_type(self.inputs[path[1]])
        return None


def _pos_of(node: Any) -> int:
    return node.get("pos", 0) if isinstance(node, dict) else 0


def _ref_type(node: Dict[str, Any], sym: SymbolTable, diags: List[Dict[str, Any]]) -> str:
    path = list(node["path"])
    kind = sym.resolve(path)
    if kind is None:
        diags.append(diag("E0301", "fail",
                          "未登记符号 %s（不在 world_slots / event_registry / token / input 面内）"
                          % ".".join(path), _pos_of(node)))
        return "unknown"
    return kind


def _require(expected: str, actual: str, pos: int, diags: List[Dict[str, Any]], what: str) -> None:
    if not _accepts(expected, actual):
        diags.append(diag("E0303", "fail", "%s 期望 %s，实为 %s" % (what, expected, actual), pos))


def _join(a: str, b: str) -> str:
    if "unknown" in (a, b):
        return "unknown"
    if "untyped" in (a, b):
        return "untyped"
    return "bool"


def _rel_result(lt: str, rt: str) -> str:
    """比较/成员运算的结果类型：unknown → unknown；untyped → untyped（不得冒充 bool）。"""
    if "unknown" in (lt, rt):
        return "unknown"
    if "untyped" in (lt, rt):
        return "untyped"
    return "bool"


def _infer(node: Any, sym: SymbolTable, diags: List[Dict[str, Any]]) -> str:
    if not isinstance(node, dict):
        return "unknown"
    k = node.get("k")
    if k == "lit":
        return _LIT_TYPES.get(str(node.get("t")), "unknown")
    if k == "ref":
        return _ref_type(node, sym, diags)
    if k in ("list", "map"):
        return _infer_coll(node, sym, diags)
    if k == "un":
        return _infer_un(node, sym, diags)
    if k == "cond":
        return _infer_cond(node, sym, diags)
    if k == "call":
        return _infer_call(node, sym, diags)
    if k == "bin":
        return _infer_bin(node, sym, diags)
    return "unknown"


def _infer_coll(node: Dict[str, Any], sym: SymbolTable, diags: List[Dict[str, Any]]) -> str:
    for it in node.get("items") or []:
        _infer(it, sym, diags)
    for key, val in node.get("entries") or []:
        _infer(key, sym, diags)
        _infer(val, sym, diags)
    return "list" if node.get("k") == "list" else "map"


def _infer_un(node: Dict[str, Any], sym: SymbolTable, diags: List[Dict[str, Any]]) -> str:
    t = _infer(node["x"], sym, diags)
    if node["op"] == "!":
        _require("bool", t, _pos_of(node), diags, "! 的操作数")
        return "unknown" if t == "unknown" else "bool"
    _require("int|number", t, _pos_of(node), diags, "一元 - 的操作数")
    if t == "unknown":
        return "unknown"
    return t if t in NUMERIC else "untyped"


def _infer_cond(node: Dict[str, Any], sym: SymbolTable, diags: List[Dict[str, Any]]) -> str:
    _infer(node["c"], sym, diags)
    a = _infer(node["t"], sym, diags)
    b = _infer(node["f"], sym, diags)
    return a if a == b else "untyped"


def _infer_call(node: Dict[str, Any], sym: SymbolTable, diags: List[Dict[str, Any]]) -> str:
    spec = FUNCS.get(str(node.get("fn")))
    if spec is None:
        diags.append(diag("E0304", "fail", "未登记函数 %s（函数集封闭）" % node.get("fn"), _pos_of(node)))
        for a in node.get("args") or []:
            _infer(a, sym, diags)
        return "unknown"
    wants, ret = spec
    args = node.get("args") or []
    if len(args) != len(wants):
        diags.append(diag("E0305", "fail", "%s 需要 %d 个参数，实为 %d"
                          % (node.get("fn"), len(wants), len(args)), _pos_of(node)))
    for i, a in enumerate(args):
        at = _infer(a, sym, diags)
        if i < len(wants):
            _require(wants[i], at, _pos_of(node), diags, "%s 第 %d 参数" % (node.get("fn"), i + 1))
    return ret


def _infer_bin(node: Dict[str, Any], sym: SymbolTable, diags: List[Dict[str, Any]]) -> str:
    op = node["op"]
    lt = _infer(node["l"], sym, diags)
    rt = _infer(node["r"], sym, diags)
    if op in ("&&", "||"):
        _require("bool", lt, _pos_of(node), diags, "%s 左操作数" % op)
        _require("bool", rt, _pos_of(node), diags, "%s 右操作数" % op)
        return _join(lt, rt)
    if op in ("==", "!=", "in"):
        return _rel_result(lt, rt)
    if op in ("<", "<=", ">", ">="):
        return _infer_cmp(node, lt, rt, diags)
    return _infer_arith(op, lt, rt, _pos_of(node), diags)


def _infer_cmp(node: Dict[str, Any], lt: str, rt: str, diags: List[Dict[str, Any]]) -> str:
    for side, t in (("左", lt), ("右", rt)):
        if t not in NUMERIC and t != "string" and t not in ("unknown", "untyped"):
            diags.append(diag("E0303", "fail", "%s 比较不支持 %s" % (side, t), _pos_of(node)))
    return _rel_result(lt, rt)


def _infer_arith(op: str, lt: str, rt: str, pos: int, diags: List[Dict[str, Any]]) -> str:
    if op == "+" and lt == "string" and rt == "string":
        return "string"
    if op == "+" and lt == "list" and rt == "list":
        return "list"
    if "unknown" in (lt, rt):
        return "unknown"
    if "untyped" in (lt, rt):
        return "untyped"
    for side, t in (("左", lt), ("右", rt)):
        if t not in NUMERIC:
            diags.append(diag("E0303", "fail", "%s %s 不支持" % (op, side), pos))
            return "unknown"
    return "number" if "number" in (lt, rt) else "int"


def infer_type(ast: Any, sym: SymbolTable) -> Tuple[str, List[Dict[str, Any]]]:
    """表达式 → (类型, 诊断)；类型词表见 _KIND_MAP（untyped 是合法值，不判死）。"""
    diags: List[Dict[str, Any]] = []
    return _infer(ast, sym, diags), diags


def check_condition(ast: Any, sym: SymbolTable) -> Tuple[str, List[Dict[str, Any]]]:
    """guard 判据：非 bool 即 fail；untyped 记 warn（后端 fail-closed 记 abstain）。"""
    t, diags = infer_type(ast, sym)
    if t == "untyped":
        diags.append(diag("E0310", "warn",
                          "guard 类型未收窄（untyped）：执行后端按 fail-closed 记 abstain", _pos_of(ast)))
    elif t not in ("bool", "unknown"):
        diags.append(diag("E0302", "fail", "guard 应为 bool，实为 %s" % t, _pos_of(ast)))
    return t, diags


def _exc_diag(exc: Exception) -> Dict[str, Any]:
    return diag("E0201", "fail", "表达式解析失败（pos %s）：%s"
                % (getattr(exc, "pos", 0), getattr(exc, "message", str(exc))), 0)


def check_expression(expr: str, sym: SymbolTable) -> Dict[str, Any]:
    """源码 → 检查报告（AST + 非 bool/untyped 判据 + 逐条诊断）。"""
    try:
        ast = parse(expr)
    except (ParseError, LexError) as exc:
        return {"schema": SCHEMA, "kind": "nfal-check", "expr": expr, "verdict": "fail",
                "diagnostics": [_exc_diag(exc)], "ast": None}
    t, diags = check_condition(ast, sym)
    verdict = "fail" if any(d["severity"] == "fail" for d in diags) else ("warn" if diags else "pass")
    return {"schema": SCHEMA, "kind": "nfal-check", "expr": expr, "verdict": verdict,
            "guard_type": t, "diagnostics": diags, "ast": strip_pos(ast)}


# ------------------------------------------------------------------ 三值求值（Kleene）
def _ed(message: str, node: Any) -> Dict[str, Any]:
    return diag("E0401", "fail", message, _pos_of(node))


def _walk(env: Dict[str, Any], path: List[str]) -> Any:
    cur: Any = env
    for seg in path:
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return UNKNOWN
    return cur


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _bool3(v: Any) -> Optional[bool]:
    return v if isinstance(v, bool) else None


def evaluate(node: Any, env: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    """表达式 → 具体值或 UNKNOWN（类型不符记诊断并回 UNKNOWN，绝不静默通过）。"""
    if not isinstance(node, dict):
        return UNKNOWN
    k = node.get("k")
    if k == "lit":
        return node.get("v")
    if k == "ref":
        return _walk(env, list(node["path"]))
    if k == "list":
        return [evaluate(x, env, diags) for x in node.get("items") or []]
    if k == "map":
        return {evaluate(a, env, diags): evaluate(b, env, diags) for a, b in node.get("entries") or []}
    if k == "un":
        return _eval_un(node, env, diags)
    if k == "cond":
        return _eval_cond(node, env, diags)
    if k == "call":
        return _eval_call(node, env, diags)
    if k == "bin":
        return _eval_bin(node, env, diags)
    return UNKNOWN


def _eval_un(node: Dict[str, Any], env: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    v = evaluate(node["x"], env, diags)
    if v is UNKNOWN:
        return UNKNOWN
    if node["op"] == "!":
        if not isinstance(v, bool):
            diags.append(_ed("! 需要 bool，实为 %s" % type(v).__name__, node))
            return UNKNOWN
        return not v
    if not _num(v):
        diags.append(_ed("一元 - 需要数值，实为 %s" % type(v).__name__, node))
        return UNKNOWN
    return -v


def _eval_cond(node: Dict[str, Any], env: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    c = evaluate(node["c"], env, diags)
    if c is UNKNOWN:
        return UNKNOWN
    if not isinstance(c, bool):
        diags.append(_ed("条件表达式分支需要 bool", node))
        return UNKNOWN
    return evaluate(node["t"] if c else node["f"], env, diags)


def _eval_logic(op: str, a: Any, b: Any, node: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    ba, bb = _bool3(a), _bool3(b)
    if a is UNKNOWN or b is UNKNOWN:
        other = bb if a is UNKNOWN else ba
        if other is False and op == "&&":
            return False
        if other is True and op == "||":
            return True
        return UNKNOWN
    if ba is None or bb is None:
        diags.append(_ed("%s 需要 bool 操作数" % op, node))
        return UNKNOWN
    return (ba and bb) if op == "&&" else (ba or bb)


def _eval_cmp(op: str, a: Any, b: Any, node: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    if not ((_num(a) and _num(b)) or (isinstance(a, str) and isinstance(b, str))):
        diags.append(_ed("%s 操作数不可比" % op, node))
        return UNKNOWN
    return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


def _eval_in(a: Any, b: Any, node: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    if isinstance(b, (list, tuple, str, dict)):
        return a in b
    diags.append(_ed("in 右侧应为 list/map/string", node))
    return UNKNOWN


def _div(a: Any, b: Any, node: Dict[str, Any], diags: List[Dict[str, Any]], true_div: bool) -> Any:
    if b == 0:
        diags.append(_ed("除数为零", node))
        return UNKNOWN
    return (a / b) if true_div else (a % b)


def _eval_arith(op: str, a: Any, b: Any, node: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    if op == "+" and isinstance(a, str) and isinstance(b, str):
        return a + b
    if op == "+" and isinstance(a, list) and isinstance(b, list):
        return a + b
    if not (_num(a) and _num(b)):
        diags.append(_ed("%s 需要数值，实为 %s / %s"
                         % (op, type(a).__name__, type(b).__name__), node))
        return UNKNOWN
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return _div(a, b, node, diags, True)
    if op == "%":
        return _div(a, b, node, diags, False)
    diags.append(_ed("未知运算符 %s" % op, node))
    return UNKNOWN


def _eval_bin(node: Dict[str, Any], env: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    op = node["op"]
    a = evaluate(node["l"], env, diags)
    b = evaluate(node["r"], env, diags)
    if op in ("&&", "||"):
        return _eval_logic(op, a, b, node, diags)
    if a is UNKNOWN or b is UNKNOWN:
        return UNKNOWN
    if op in ("==", "!="):
        return (a == b) if op == "==" else (a != b)
    if op in ("<", "<=", ">", ">="):
        return _eval_cmp(op, a, b, node, diags)
    if op == "in":
        return _eval_in(a, b, node, diags)
    return _eval_arith(op, a, b, node, diags)


def _apply(fn: str, args: List[Any]) -> Any:
    if fn == "size":
        return len(args[0])
    if fn == "contains":
        return args[1] in args[0]      # contains(容器, 元素)
    if fn == "has":
        return args[1] in args[0]
    if fn == "startsWith":
        return args[0].startswith(args[1])
    if fn == "int":
        return int(args[0])
    if fn == "string":
        return str(args[0])
    raise ValueError("未登记函数 %s（修复指引：函数集封闭，见 core.nfal.FUNCS）" % fn)


def _eval_call(node: Dict[str, Any], env: Dict[str, Any], diags: List[Dict[str, Any]]) -> Any:
    fn = str(node.get("fn"))
    if fn not in FUNCS:
        diags.append(_ed("未登记函数 %s（函数集封闭）" % fn, node))
        return UNKNOWN
    args = [evaluate(a, env, diags) for a in node.get("args") or []]
    if any(x is UNKNOWN for x in args):
        return UNKNOWN
    try:
        return _apply(fn, args)
    except (TypeError, ValueError, IndexError) as exc:
        diags.append(_ed("%s 参数不符：%s" % (fn, exc), node))
        return UNKNOWN


def verdict_of(value: Any) -> str:
    """三态判决：True→pass / False→fail / 其余→abstain（abstain 永不折算 pass）。"""
    if value is True:
        return "pass"
    if value is False:
        return "fail"
    return "abstain"


def eval_guard(ast: Any, env: Dict[str, Any]) -> Dict[str, Any]:
    """对单条 guard 求值 → {verdict, value, diagnostics}（确定性：同输入同结果）。"""
    diags: List[Dict[str, Any]] = []
    value = evaluate(ast, env, diags)
    return {"verdict": verdict_of(value), "value": None if value is UNKNOWN else value,
            "diagnostics": diags}


# ------------------------------------------------------------------ NFIR（规范 JSON 中间表示）
def _fence_pipeline(text: str) -> Any:
    """管线围栏 → dict。首选仓库统一 YAML 加载器；无 PyYAML 时回退管线加载器的零依赖子集解析
    （容器分发链路不装第三方依赖，降级如实、不静默改语义）。"""
    try:
        from core import conformance_scan as csc
        return csc._fence_yaml(text, "Pipeline")
    except Exception:  # noqa: BLE001 —— 无 PyYAML 等 ⇒ 走零依赖子集解析
        from core.pipeline_loader import YAML_FENCE_RE, _parse_yaml_block
        m = YAML_FENCE_RE.search(text)
        return _parse_yaml_block(m.group(1)) if m else None


def load_decl(root: str, pipeline_path: str) -> Dict[str, Any]:
    """管线声明（复用 conformance_scan 统一围栏解析；失败给修复指引）。"""
    r = Path(root)
    p = Path(pipeline_path)
    if not p.is_absolute():
        p = p if p.exists() else (r / pipeline_path)
    src = str(r / "desktop" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    data = _fence_pipeline(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("Pipeline"), dict):
        return data["Pipeline"]
    if isinstance(data, dict):
        return data
    raise ValueError("管线围栏解析失败：%s（修复指引：检查 frontmatter 与代码围栏闭合）" % pipeline_path)


def _module_refs(decl: Dict[str, Any]) -> List[str]:
    refs: List[str] = []
    for ly in decl.get("layers") or []:
        if not isinstance(ly, dict):
            continue
        for key in ("default_modules", "allowed_modules"):
            for m in ly.get(key) or []:
                if str(m) not in refs:
                    refs.append(str(m))
    return refs


def _layer_row(ly: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": ly.get("id"), "name": ly.get("name"),
            "optional": bool(ly.get("optional", False)),
            "modules": [str(x) for x in (ly.get("default_modules") or [])]}


def _edge_row(fl: Dict[str, Any], sym: SymbolTable, diags: List[Dict[str, Any]],
              strict: bool) -> Dict[str, Any]:
    edge: Dict[str, Any] = {"from": fl.get("from"), "to": fl.get("to")}
    cond = fl.get("condition")
    if cond is None:
        edge["guard"] = {"source": "implicit", "expr": None, "ast": _IMPLICIT_TRUE}
        edge["guard_types"] = {"guard": "bool"}
        return edge
    raw = str(cond).strip()
    if not raw.startswith(EXPR_PREFIX):
        sev = "fail" if strict else "warn"
        code = "E0202" if strict else "A0201"
        diags.append(diag(code, sev,
                          "condition 为散文（不可机验）；迁移为 '=<nf-expr>' 后即可静态检查+执行：%s"
                          % raw[:80], 0))
        edge["guard"] = {"source": "prose", "expr": raw, "ast": None}
        return edge
    expr = raw[len(EXPR_PREFIX):].strip()
    try:
        ast = parse(expr)
    except (ParseError, LexError) as exc:
        diags.append(_exc_diag(exc))
        edge["guard"] = {"source": "expr", "expr": expr, "ast": None}
        return edge
    gtype, gdiags = check_condition(ast, sym)
    diags.extend(gdiags)
    edge["guard"] = {"source": "expr", "expr": expr, "ast": strip_pos(ast)}
    edge["guard_types"] = {"guard": gtype}
    return edge


def _verdict(diags: List[Dict[str, Any]]) -> str:
    if any(d["severity"] == "fail" for d in diags):
        return "fail"
    if diags:
        return "warn"
    return "pass"


def build_ir(root: str = ".", pipeline_path: str = "", sym: Optional[SymbolTable] = None,
             with_tokens: bool = True, strict: bool = False) -> Dict[str, Any]:
    """管线声明 + guard 表达式 → NFIR（规范 JSON；同输入逐字节同输出）。"""
    decl = load_decl(root, pipeline_path)
    if sym is None:
        sym = SymbolTable.from_repo(root, module_refs=_module_refs(decl), with_tokens=with_tokens)
    diags: List[Dict[str, Any]] = []
    layers = [_layer_row(ly) for ly in decl.get("layers") or [] if isinstance(ly, dict)]
    struct = decl.get("structure") or {}
    edges = [_edge_row(fl, sym, diags, strict)
             for fl in struct.get("flow") or [] if isinstance(fl, dict)]
    return {
        "schema": SCHEMA, "kind": "nfal-ir",
        "pipeline": {"id": decl.get("id"), "name": decl.get("name"),
                     "structure_type": struct.get("type"), "source": str(pipeline_path)},
        "layers": layers, "edges": edges, "tokens": sorted(sym.tokens),
        "diagnostics": diags, "verdict": _verdict(diags),
    }


def canonical(ir: Dict[str, Any]) -> str:
    """NFIR → 规范 JSON 文本（键排序 + 2 空格缩进 + 末尾换行；可 diff/golden）。"""
    return json.dumps(ir, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
