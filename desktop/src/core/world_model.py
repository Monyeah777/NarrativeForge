"""world_model 契约扫描器（machine_contract.world_model 可选确定性抽象状态层）。

定位：把 JEPA/H-JEPA 对“预测未来表征、而非生成像素/词元”的机制，收窄成 NF
协议层可无歧义机检的确定性契约：

- abstract_state：有限状态变量 + 初始值，变量名/类型/来源显式声明；
- transition：finite-state 相位图，每个相位显式声明 next/guard/writes；
- invariants：抽象状态必须长期成立的硬约束（如 tick 单调、相位有限）。

边界：本模块校验契约结构与语义，不训练/不运行神经网络，不对 JEPA 与生成式
路线的优劣作任何经验断言；外部有效性只来自用户实测，不由本扫描器伪造。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

KINDS = {"string", "integer", "number", "boolean", "array"}
ITEM_KINDS = {"string", "integer", "number", "boolean"}
_ROOT = Path(__file__).resolve().parents[3]
SLOT_REGISTRY_PATH = _ROOT / "protocol" / "world_slots.json"


def load_slots(root: str = ".") -> Dict[str, Dict[str, Any]]:
    """读取 M00 数据槽可绑定投影（protocol/world_slots.json）。"""
    path = Path(root) / "protocol" / "world_slots.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("slots") or {}


def _matches(value: Any, kind: str, item_kind: str | None = None) -> bool:
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "string":
        return isinstance(value, str)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "array":
        if not isinstance(value, list):
            return False
        return item_kind is None or all(_matches(v, item_kind) for v in value)
    return False


def _slot_parts(slot: str) -> List[str]:
    return [part for part in slot.split(".") if part]


def _get_slot(state: Dict[str, Any], slot: str) -> Any:
    cur: Any = state
    for part in _slot_parts(slot):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(slot)
        cur = cur[part]
    return cur


def _set_slot(state: Dict[str, Any], slot: str, value: Any) -> Dict[str, Any]:
    import copy

    out = copy.deepcopy(state)
    cur = out
    parts = _slot_parts(slot)
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
        if not isinstance(cur, dict):
            raise ValueError("slot 中段非对象：%s" % slot)
    cur[parts[-1]] = value
    return out


def validate_contract(wm: Any, label: str = "world_model",
                      slot_registry: Dict[str, Dict[str, Any]] | None = None) -> List[str]:
    """校验单个 world_model 契约；返回可读违例清单。"""
    issues: List[str] = []
    if not isinstance(wm, dict):
        return [f"{label}: 非对象"]

    abstract = wm.get("abstract_state")
    if not isinstance(abstract, dict):
        issues.append(f"{label}.abstract_state: 缺失或非对象")
        variables: List[Dict[str, Any]] = []
        initial: Any = None
    else:
        variables = abstract.get("variables")
        initial = abstract.get("initial")
        if not isinstance(variables, list) or not variables:
            issues.append(f"{label}.abstract_state.variables: 非空数组")
            variables = []
        if not isinstance(initial, dict):
            issues.append(f"{label}.abstract_state.initial: 缺失或非对象")
            initial = None

    names: List[str] = []
    slots: List[str] = []
    valid_vars: List[Dict[str, Any]] = []
    for idx, var in enumerate(variables):
        at = f"{label}.abstract_state.variables[{idx}]"
        if not isinstance(var, dict):
            issues.append(f"{at}: 非对象")
            continue
        name = var.get("name")
        kind = var.get("kind")
        source = var.get("source")
        slot = var.get("slot")
        item_kind = var.get("item_kind")
        if not isinstance(name, str) or not name.strip():
            issues.append(f"{at}.name: 非空字符串")
        else:
            if name in names:
                issues.append(f"{at}.name: 变量重名 {name!r}")
            names.append(name)
        if kind not in KINDS:
            issues.append(f"{at}.kind: 非法类型 {kind!r}")
        if kind == "array":
            if item_kind is not None and item_kind not in ITEM_KINDS:
                issues.append(f"{at}.item_kind: 非法元素类型 {item_kind!r}")
        elif item_kind is not None:
            issues.append(f"{at}.item_kind: 仅 kind=array 可用")
        if not isinstance(source, str) or not source.strip():
            issues.append(f"{at}.source: 非空字符串")
        if slot is not None:
            if not isinstance(slot, str) or not slot.strip():
                issues.append(f"{at}.slot: 非空字符串")
            elif slot in slots:
                issues.append(f"{at}.slot: 槽位重复 {slot!r}")
            else:
                slots.append(slot)
        valid_vars.append(var)

    if isinstance(initial, dict):
        declared = [v.get("name") for v in valid_vars if isinstance(v.get("name"), str)]
        for key in sorted(initial):
            if key not in declared:
                issues.append(f"{label}.abstract_state.initial: 未声明变量 {key!r}")
        for var in valid_vars:
            name = var.get("name")
            if not isinstance(name, str):
                continue
            if name not in initial:
                issues.append(f"{label}.abstract_state.initial: 缺变量 {name!r} 的初始值")
                continue
            kind = var.get("kind")
            item_kind = var.get("item_kind")
            if kind in KINDS and not _matches(initial[name], kind, item_kind):
                issues.append(
                    f"{label}.abstract_state.initial.{name}: 值 {initial[name]!r} "
                    f"不匹配 kind={kind!r}"
                )

    transition = wm.get("transition")
    if not isinstance(transition, dict):
        issues.append(f"{label}.transition: 缺失或非对象")
        initial_phase = None
        phases: List[Dict[str, Any]] = []
    else:
        initial_phase = transition.get("initial_phase")
        phases = transition.get("phases")
        if not isinstance(initial_phase, str) or not initial_phase.strip():
            issues.append(f"{label}.transition.initial_phase: 非空字符串")
            initial_phase = None
        if not isinstance(phases, list) or not phases:
            issues.append(f"{label}.transition.phases: 非空数组")
            phases = []

    phase_names: List[str] = []
    edges: Dict[str, str] = {}
    for idx, phase in enumerate(phases):
        at = f"{label}.transition.phases[{idx}]"
        if not isinstance(phase, dict):
            issues.append(f"{at}: 非对象")
            continue
        pname = phase.get("phase")
        nxt = phase.get("next")
        guard = phase.get("guard")
        writes = phase.get("writes")
        if not isinstance(pname, str) or not pname.strip():
            issues.append(f"{at}.phase: 非空字符串")
            continue
        if pname in phase_names:
            issues.append(f"{at}.phase: 相位重名 {pname!r}")
        phase_names.append(pname)
        if not isinstance(nxt, str) or not nxt.strip():
            issues.append(f"{at}.next: 非空字符串")
        if not isinstance(guard, str) or not guard.strip():
            issues.append(f"{at}.guard: 非空守卫说明")
        if not isinstance(writes, list) or any(
            not isinstance(w, str) or not w.strip() for w in writes
        ):
            issues.append(f"{at}.writes: 字符串数组（可为空）")
        if isinstance(pname, str) and isinstance(nxt, str):
            edges[pname] = nxt

    phase_set = set(phase_names)
    if initial_phase is not None and initial_phase not in phase_set:
        issues.append(
            f"{label}.transition.initial_phase: {initial_phase!r} 不在 phases 内"
        )
    for pname, nxt in edges.items():
        if nxt not in phase_set:
            issues.append(
                f"{label}.transition.phases[{pname!r}].next: {nxt!r} 无对应相位"
            )

    if initial_phase in phase_set and all(n in phase_set for n in edges.values()):
        seen = {initial_phase}
        frontier = [initial_phase]
        while frontier:
            current = frontier.pop(0)
            nxt = edges.get(current)
            if nxt is not None and nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
        unreachable = sorted(phase_set - seen)
        if unreachable:
            issues.append(
                f"{label}.transition: 从 initial_phase 不可达的相位 {unreachable}"
            )

    invariants = wm.get("invariants")
    if not isinstance(invariants, list) or not invariants:
        issues.append(f"{label}.invariants: 非空数组")
    else:
        for idx, inv in enumerate(invariants):
            if not isinstance(inv, str) or not inv.strip():
                issues.append(f"{label}.invariants[{idx}]: 非空字符串")

    declared_names = [v.get("name") for v in valid_vars if isinstance(v.get("name"), str)]
    declared_kinds = {v.get("name"): v.get("kind") for v in valid_vars
                      if isinstance(v.get("name"), str)}
    checks = wm.get("checks")
    if checks is not None:
        if not isinstance(checks, list) or not checks:
            issues.append(f"{label}.checks: 非空数组")
            checks = []
        for idx, check in enumerate(checks):
            at = f"{label}.checks[{idx}]"
            if not isinstance(check, dict):
                issues.append(f"{at}: 非对象")
                continue
            kind = check.get("kind")
            field = check.get("field")
            values = check.get("values")
            if kind not in ("finite_phase", "monotonic", "finite_sequence"):
                issues.append(f"{at}.kind: 非法检查类型 {kind!r}")
            if not isinstance(field, str) or not field.strip():
                issues.append(f"{at}.field: 非空字符串")
            elif field not in declared_names:
                issues.append(f"{at}.field: 未声明变量 {field!r}")
            if kind in ("finite_phase", "finite_sequence"):
                if not isinstance(values, list) or not values or any(
                    not isinstance(v, str) or not v.strip() for v in values
                ):
                    issues.append(f"{at}.values: {kind} 需非空字符串数组")
            elif kind == "monotonic" and declared_kinds.get(field) not in ("integer", "number"):
                issues.append(f"{at}.field: monotonic 只能用于 integer/number 变量")
            if kind == "finite_sequence":
                if declared_kinds.get(field) != "array":
                    issues.append(f"{at}.field: finite_sequence 只能用于 array 变量")
                else:
                    spec = next((v for v in valid_vars if v.get("name") == field), {})
                    if spec.get("item_kind") not in (None, "string"):
                        issues.append(
                            f"{at}.field: finite_sequence 的 array 元素应为 string"
                        )

    if slot_registry:
        for var in valid_vars:
            slot = var.get("slot")
            if not isinstance(slot, str) or not slot.strip():
                continue
            name = var.get("name")
            source = var.get("source")
            spec = slot_registry.get(slot)
            if not isinstance(spec, dict):
                issues.append(
                    f"{label}.abstract_state.variables[{name!r}].slot: "
                    f"未在 protocol/world_slots.json 注册 {slot!r}"
                )
                continue
            if spec.get("kind") != var.get("kind"):
                issues.append(
                    f"{label}.abstract_state.variables[{name!r}].slot: "
                    f"类型漂移 slot={spec.get('kind')!r} var={var.get('kind')!r}"
                )
            if var.get("kind") == "array" and var.get("item_kind") and (
                spec.get("item_kind") != var.get("item_kind")
            ):
                issues.append(
                    f"{label}.abstract_state.variables[{name!r}].slot: "
                    f"元素类型漂移 slot={spec.get('item_kind')!r} "
                    f"var={var.get('item_kind')!r}"
                )
            if spec.get("owner") and source != spec.get("owner"):
                issues.append(
                    f"{label}.abstract_state.variables[{name!r}].slot: "
                    f"owner 漂移 slot={spec.get('owner')!r} var.source={source!r}"
                )

    return issues


def build_graph(wm: Dict[str, Any]) -> Dict[str, Any]:
    """把 world_model.transition 投影成可执行的确定性相位图。"""
    transition = wm.get("transition") or {}
    phases = transition.get("phases") or []
    by_name = {}
    for item in phases:
        if isinstance(item, dict) and isinstance(item.get("phase"), str):
            by_name[item["phase"]] = {
                "next": item.get("next"),
                "guard": item.get("guard", ""),
                "writes": list(item.get("writes") or []),
            }
    return {
        "initial_phase": transition.get("initial_phase"),
        "phases": by_name,
    }


class WorldModelViolation(ValueError):
    """world_model 运行态违例；issues 为可读违例清单。"""

    def __init__(self, issues: List[str]):
        self.issues = list(issues)
        super().__init__("; ".join(self.issues))


def trace_digest(result: Dict[str, Any]) -> str:
    """对 replay 的 steps 做规范 JSON 摘要，作为确定性重放指纹。"""
    import hashlib

    payload = json.dumps(result.get("steps") or [], sort_keys=True,
                         ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class WorldModelRuntime:
    """可执行 world_model：状态校验 + 相位前进 + 确定性重放。"""

    def __init__(self, contract: Dict[str, Any]):
        issues = validate_contract(contract)
        if issues:
            raise WorldModelViolation(issues)
        self.contract = contract
        self.graph = build_graph(contract)
        abstract = contract.get("abstract_state") or {}
        self.variables = {
            item["name"]: item
            for item in (abstract.get("variables") or [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
        self.initial = initial_state(contract)

    def validate_state(self, state: Any,
                       previous: Dict[str, Any] | None = None) -> List[str]:
        """校验运行态：变量封闭、类型匹配、结构化 checks 全部成立。"""
        issues: List[str] = []
        if not isinstance(state, dict):
            return ["state 非对象"]
        declared = set(self.variables)
        unknown = sorted(set(state) - declared)
        missing = sorted(declared - set(state))
        if unknown:
            issues.append("state 含未声明变量 %s" % unknown)
        if missing:
            issues.append("state 缺声明变量 %s" % missing)
        for name, spec in self.variables.items():
            if name not in state:
                continue
            if not _matches(state[name], spec.get("kind"), spec.get("item_kind")):
                issues.append(
                    "state.%s 类型不匹配 kind=%r item_kind=%r"
                    % (name, spec.get("kind"), spec.get("item_kind"))
                )
        for check in self.contract.get("checks") or []:
            kind = check.get("kind")
            field = check.get("field")
            if kind == "finite_phase":
                values = set(check.get("values") or [])
                if field in state and state.get(field) not in values:
                    issues.append(
                        "check finite_phase：%s=%r 不在 %s"
                        % (field, state.get(field), sorted(values))
                    )
            elif kind == "monotonic":
                if field in state and previous is not None and field in previous:
                    if not _matches(state[field], "number") or not _matches(
                        previous[field], "number"
                    ):
                        issues.append("check monotonic：%s 非数值" % field)
                    elif state[field] < previous[field]:
                        issues.append(
                            "check monotonic：%s %s < 上一状态 %s"
                            % (field, state[field], previous[field])
                        )
            elif kind == "finite_sequence":
                values = set(check.get("values") or [])
                seq = state.get(field)
                if not isinstance(seq, list):
                    issues.append(
                        "check finite_sequence：%s 应为 array" % field
                    )
                else:
                    bad = [v for v in seq if v not in values]
                    if bad:
                        issues.append(
                            "check finite_sequence：%s 含非法相位 %s"
                            % (field, bad)
                        )
        return issues

    def extract_state(self, concrete: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """从 M00 具体 JSON 状态按 slot 路径抽取 world_model 抽象状态。"""
        issues: List[str] = []
        state: Dict[str, Any] = {}
        for name, spec in self.variables.items():
            slot = spec.get("slot")
            if not isinstance(slot, str) or not slot.strip():
                issues.append("变量 %s 缺 slot，无法从具体状态抽取" % name)
                continue
            try:
                state[name] = _get_slot(concrete, slot)
            except KeyError:
                issues.append("slot 路径缺失：%s（%s）" % (slot, name))
        return state, issues

    def validate_concrete(self, concrete: Dict[str, Any],
                          previous_concrete: Dict[str, Any] | None = None) -> List[str]:
        """先按 slot 抽取抽象状态，再校验状态类型与 checks。"""
        state, issues = self.extract_state(concrete)
        if issues:
            return issues
        previous = None
        if previous_concrete is not None:
            previous, prev_issues = self.extract_state(previous_concrete)
            if prev_issues:
                return prev_issues
        return self.validate_state(state, previous)

    def advance(self, state: Dict[str, Any],
                previous: Dict[str, Any] | None = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """前进一步；先验状态，再按相位图更新 phase 与 phase_trace（若声明）。"""
        issues = self.validate_state(state, previous)
        if issues:
            raise WorldModelViolation(issues)
        phase_from = state.get("phase")
        if phase_from not in self.graph["phases"]:
            raise WorldModelViolation(["当前相位未声明：%r" % phase_from])
        import copy

        before = copy.deepcopy(state)
        after = copy.deepcopy(state)
        transition = self.graph["phases"][phase_from]
        after["phase"] = transition["next"]
        phase_trace = self.variables.get("phase_trace")
        if phase_trace and phase_trace.get("kind") == "array":
            chain = list(state.get("phase_trace") or [])
            chain.append(phase_from)
            after["phase_trace"] = chain
        trace = {
            "phase_from": phase_from,
            "phase_to": transition["next"],
            "guard": transition.get("guard", ""),
            "writes": list(transition.get("writes") or []),
            "state_before": before,
            "state_after": after,
        }
        return after, trace

    def replay(self, state: Dict[str, Any] | None = None,
               max_steps: int = 100) -> Dict[str, Any]:
        """从 initial 重放相位迁移，直到回到已见相位或超限。"""
        import copy

        current = copy.deepcopy(state) if state is not None else copy.deepcopy(self.initial)
        steps: List[Dict[str, Any]] = []
        seen: set = set()
        last: Dict[str, Any] | None = None
        reason = "limit"
        repeat = None
        for _ in range(max(1, max_steps)):
            phase = current.get("phase")
            if phase in seen:
                reason = "cycle"
                repeat = phase
                break
            seen.add(phase)
            next_state, trace = self.advance(current, last)
            trace["step"] = len(steps) + 1
            steps.append(trace)
            last = current
            current = next_state
        result = {
            "reason": reason,
            "repeat": repeat,
            "steps": steps,
            "final_state": current,
        }
        result["digest"] = trace_digest(result)
        return result

    def advance_concrete(self, concrete: Dict[str, Any],
                         previous_concrete: Dict[str, Any] | None = None
                         ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """从具体 M00 状态前进一步；校验、抽取、推进并写回 slot。"""
        state, extract_issues = self.extract_state(concrete)
        if extract_issues:
            raise WorldModelViolation(extract_issues)
        previous = None
        if previous_concrete is not None:
            previous, prev_issues = self.extract_state(previous_concrete)
            if prev_issues:
                raise WorldModelViolation(prev_issues)
        abstract_next, trace = self.advance(state, previous)
        concrete_next = dict(concrete)
        for name, spec in self.variables.items():
            slot = spec.get("slot")
            if isinstance(slot, str) and name in abstract_next:
                concrete_next = _set_slot(concrete_next, slot, abstract_next[name])
        trace["concrete_before"] = concrete
        trace["concrete_after"] = concrete_next
        return concrete_next, trace

    def replay_concrete(self, concrete: Dict[str, Any] | None = None,
                        max_steps: int = 100) -> Dict[str, Any]:
        """从具体 M00 状态重放，直到回到已见相位或超限。"""
        import copy

        if concrete is None:
            current: Dict[str, Any] = {}
            for name, spec in self.variables.items():
                slot = spec.get("slot")
                if isinstance(slot, str):
                    current = _set_slot(current, slot, self.initial.get(name))
        else:
            current = copy.deepcopy(concrete)
        steps: List[Dict[str, Any]] = []
        seen: set = set()
        last: Dict[str, Any] | None = None
        reason = "limit"
        repeat = None
        for _ in range(max(1, max_steps)):
            abstract, extract_issues = self.extract_state(current)
            if extract_issues:
                raise WorldModelViolation(extract_issues)
            phase = abstract.get("phase")
            if phase in seen:
                reason = "cycle"
                repeat = phase
                break
            seen.add(phase)
            previous_current = current
            current, trace = self.advance_concrete(current, last)
            trace["step"] = len(steps) + 1
            steps.append(trace)
            last = previous_current
        result = {
            "reason": reason,
            "repeat": repeat,
            "steps": steps,
            "final_state": current,
        }
        result["digest"] = trace_digest(result)
        return result


def initial_state(wm: Dict[str, Any]) -> Dict[str, Any]:
    """返回 abstract_state.initial 的深拷贝，作为可重放的初始状态。"""
    import copy

    abstract = wm.get("abstract_state") or {}
    return copy.deepcopy(abstract.get("initial") or {})


def advance_phase(wm: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """按相位图前进一步；不解释 guard，只执行已声明的确定性 next。"""
    graph = build_graph(wm)
    phase = state.get("phase")
    if phase not in graph["phases"]:
        raise ValueError("当前相位未在 world_model.transition.phases 声明: %r" % phase)
    nxt = graph["phases"][phase]["next"]
    out = dict(state)
    out["phase"] = nxt
    return out


def phase_sequence(wm: Dict[str, Any], limit: int = 100) -> Tuple[List[str], str, str | None]:
    """从 initial_phase 重放相位序列；返回 (序列, 终止原因, 重复相位)。"""
    graph = build_graph(wm)
    current = graph["initial_phase"]
    if current is None:
        return [], "dangling", None
    sequence: List[str] = []
    seen = set()
    for _ in range(max(1, limit)):
        if current in seen:
            return sequence, "cycle", current
        sequence.append(current)
        seen.add(current)
        nxt = graph["phases"].get(current, {}).get("next")
        if nxt is None:
            return sequence, "dangling", current
        current = nxt
    return sequence, "limit", current


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """扫描全部模块文档中的 world_model 契约。"""
    r = Path(root)
    from core import conformance_scan as csc

    issues: List[str] = []
    slot_registry = load_slots(str(r))
    if not slot_registry:
        issues.append("protocol/world_slots.json 缺失或 slots 为空")
    modules = 0
    variables = 0
    phases = 0
    invariants = 0
    checks = 0
    slots = 0
    models: List[Dict[str, Any]] = []

    for doc in csc._module_docs(str(r)):
        rel = os.path.relpath(doc, str(r)).replace(os.sep, "/")
        try:
            text = Path(doc).read_text(encoding="utf-8")
        except Exception as exc:
            issues.append(f"{rel}: 读取失败 {exc}")
            continue
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if not isinstance(mc, dict) or "world_model" not in mc:
            continue
        wm = mc["world_model"]
        for issue in validate_contract(wm, f"{rel}.world_model",
                                       slot_registry=slot_registry):
            issues.append(issue)
        modules += 1
        abstract = wm.get("abstract_state") if isinstance(wm, dict) else {}
        transition = wm.get("transition") if isinstance(wm, dict) else {}
        invs = wm.get("invariants") if isinstance(wm, dict) else []
        check_list = wm.get("checks") if isinstance(wm, dict) else []
        if isinstance(abstract, dict):
            var_list = abstract.get("variables") or []
            variables += len(var_list)
            slots += sum(1 for v in var_list if isinstance(v, dict) and v.get("slot"))
        if isinstance(transition, dict):
            phases += len(transition.get("phases") or [])
        if isinstance(invs, list):
            invariants += len(invs)
        if isinstance(check_list, list):
            checks += len(check_list)
        models.append({
            "module": (mc.get("id") or rel),
            "source": rel,
            "initial_phase": (
                transition.get("initial_phase") if isinstance(transition, dict) else None
            ),
            "phases": len(transition.get("phases") or [])
            if isinstance(transition, dict) else 0,
            "invariants": len(invs) if isinstance(invs, list) else 0,
            "checks": len(check_list) if isinstance(check_list, list) else 0,
            "slots": sum(1 for v in (abstract.get("variables") or [])
                         if isinstance(v, dict) and v.get("slot"))
            if isinstance(abstract, dict) else 0,
        })

    stats = {
        "modules": modules,
        "variables": variables,
        "phases": phases,
        "invariants": invariants,
        "checks": checks,
        "slots": slots,
        "slot_registry": len(slot_registry),
        "models": models,
    }
    return issues, stats
