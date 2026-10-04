//! `world_model` 契约扫描器 —— 与真源 `desktop/src/core/world_model.py` 的 `scan` 对账。
//!
//! **移植面按消费者界定**：只移植判据面（`load_slots` / `_matches` / `validate_contract` /
//! `scan`）。真源里的 `WorldModelRuntime` / `build_graph` / `initial_state` / `advance_phase` /
//! `phase_sequence` / `trace_digest` / `_get_slot` / `_set_slot` 是**可执行运行时**（跑到状态
//! 前进与重放），不属判据面 ⇒ 不移植。
//!
//! **一处已知偏差**：真源 `load_slots` 用 `json.loads` 裸解析——`protocol/world_slots.json`
//! 若是坏 JSON 会**抛异常**并沿 `scan → quality_depth_scan` 冒泡。本线不复制这个崩溃行为：
//! 解析失败按**空注册表**处理（与"缺件"同路），并由 `world_slots_scan` 那侧另行报出结构问题。

use crate::pyjson::Json;
use crate::pyval;
use std::path::Path;

const KINDS: [&str; 5] = ["string", "integer", "number", "boolean", "array"];
const ITEM_KINDS: [&str; 4] = ["string", "integer", "number", "boolean"];

fn obj_get<'a>(v: &'a Json, k: &str) -> Option<&'a Json> {
    match v {
        Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv),
        _ => None,
    }
}

/// 真源 `v.get(k)`：**区分"缺键"与"显式 null"**（判据里 `checks is not None` 依赖这一点）。
fn get(v: &Json, k: &str) -> Option<Json> {
    obj_get(v, k).cloned()
}

/// 该键是否**在场**（真源 `k in dict`）。
fn has(v: &Json, k: &str) -> bool {
    matches!(v, Json::Object(o) if o.iter().any(|(kk, _)| kk == k))
}

fn arr_of(v: Option<&Json>) -> Vec<Json> {
    match v {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    }
}

/// 真源 `load_slots`：`protocol/world_slots.json` 的 `slots` 段。
pub fn load_slots(root: &Path) -> Vec<(String, Json)> {
    let rel = "protocol/world_slots.json";
    if !root.join(rel).is_file() {
        return Vec::new();
    }
    let Ok(text) = std::fs::read_to_string(root.join(rel)) else { return Vec::new() };
    let Ok(data) = crate::asset_contract::strict_json(&text) else { return Vec::new() };
    match obj_get(&data, "slots") {
        Some(Json::Object(o)) => o.clone(),
        _ => Vec::new(),
    }
}

fn slot_lookup(reg: &[(String, Json)], slot: &str) -> Option<Json> {
    reg.iter().find(|(k, _)| k == slot).map(|(_, v)| v.clone())
}

/// 真源 `_matches`。
pub fn matches(value: &Json, kind: &str, item_kind: Option<&str>) -> bool {
    match kind {
        "integer" => matches!(value, Json::Int(_)),
        "number" => matches!(value, Json::Int(_) | Json::Float(_)),
        "string" => matches!(value, Json::Str(_)),
        "boolean" => matches!(value, Json::Bool(_)),
        "array" => match value {
            Json::Array(a) => match item_kind {
                None => true,
                Some(ik) => a.iter().all(|v| matches(v, ik, None)),
            },
            _ => false,
        },
        _ => false,
    }
}

/// 真源 `validate_contract`。
pub fn validate_contract(
    wm: &Json,
    label: &str,
    slot_registry: &[(String, Json)],
) -> Vec<String> {
    let mut issues: Vec<String> = Vec::new();
    if !matches!(wm, Json::Object(_)) {
        return vec![format!("{}: 非对象", label)];
    }

    let abstract_v = get(wm, "abstract_state");
    let mut variables: Vec<Json> = Vec::new();
    let mut initial: Option<Json> = None;
    match &abstract_v {
        Some(a @ Json::Object(_)) => {
            let vars = get(a, "variables");
            initial = get(a, "initial");
            match &vars {
                Some(Json::Array(v)) if !v.is_empty() => variables = v.clone(),
                _ => {
                    issues.push(format!("{}.abstract_state.variables: 非空数组", label));
                }
            }
            if !matches!(initial, Some(Json::Object(_))) {
                issues.push(format!("{}.abstract_state.initial: 缺失或非对象", label));
                initial = None;
            }
        }
        _ => {
            issues.push(format!("{}.abstract_state: 缺失或非对象", label));
        }
    }

    let mut names: Vec<String> = Vec::new();
    let mut slots: Vec<String> = Vec::new();
    let mut valid_vars: Vec<Json> = Vec::new();
    for (idx, var) in variables.iter().enumerate() {
        let at = format!("{}.abstract_state.variables[{}]", label, idx);
        if !matches!(var, Json::Object(_)) {
            issues.push(format!("{}: 非对象", at));
            continue;
        }
        let name_v = get(var, "name");
        let kind_v = get(var, "kind");
        let source_v = get(var, "source");
        let slot_v = get(var, "slot");
        let item_kind_v = get(var, "item_kind");
        let name = match &name_v {
            Some(Json::Str(s)) if !s.trim().is_empty() => Some(s.clone()),
            _ => {
                issues.push(format!("{}.name: 非空字符串", at));
                None
            }
        };
        if let Some(n) = &name {
            if names.contains(n) {
                issues.push(format!(
                    "{}.name: 变量重名 {}",
                    at,
                    pyval::py_repr(&Json::Str(n.clone()))
                ));
            }
            names.push(n.clone());
        }
        let kind = match &kind_v {
            Some(Json::Str(s)) => s.clone(),
            _ => String::new(),
        };
        if !KINDS.contains(&kind.as_str()) {
            issues.push(format!(
                "{}.kind: 非法类型 {}",
                at,
                pyval::py_repr(&kind_v.clone().unwrap_or(Json::Null))
            ));
        }
        let item_kind_str = match &item_kind_v {
            Some(Json::Str(s)) => Some(s.clone()),
            _ => None,
        };
        if kind == "array" {
            if let Some(ik) = &item_kind_str {
                if !ITEM_KINDS.contains(&ik.as_str()) {
                    issues.push(format!(
                        "{}.item_kind: 非法元素类型 {}",
                        at,
                        pyval::py_repr(&item_kind_v.clone().unwrap_or(Json::Null))
                    ));
                }
            }
        } else if !matches!(item_kind_v, None | Some(Json::Null)) {
            issues.push(format!("{}.item_kind: 仅 kind=array 可用", at));
        }
        let source_ok = matches!(&source_v, Some(Json::Str(s)) if !s.trim().is_empty());
        if !source_ok {
            issues.push(format!("{}.source: 非空字符串", at));
        }
        if !matches!(slot_v, None | Some(Json::Null)) {
            let slot_str = match &slot_v {
                Some(Json::Str(s)) => Some(s.clone()),
                _ => None,
            };
            match slot_str {
                None => issues.push(format!("{}.slot: 非空字符串", at)),
                Some(s) if s.trim().is_empty() => {
                    issues.push(format!("{}.slot: 非空字符串", at))
                }
                Some(s) => {
                    if slots.contains(&s) {
                        issues.push(format!(
                            "{}.slot: 槽位重复 {}",
                            at,
                            pyval::py_repr(&Json::Str(s))
                        ));
                    } else {
                        slots.push(s);
                    }
                }
            }
        }
        valid_vars.push(var.clone());
    }

    if let Some(init @ Json::Object(_)) = &initial {
        let declared: Vec<String> = valid_vars
            .iter()
            .filter_map(|v| match get(v, "name") {
                Some(Json::Str(s)) => Some(s),
                _ => None,
            })
            .collect();
        let mut keys: Vec<String> = match init {
            Json::Object(o) => o.iter().map(|(k, _)| k.clone()).collect(),
            _ => Vec::new(),
        };
        keys.sort();
        for key in keys {
            if !declared.contains(&key) {
                issues.push(format!(
                    "{}.abstract_state.initial: 未声明变量 {}",
                    label,
                    pyval::py_repr(&Json::Str(key))
                ));
            }
        }
        for var in &valid_vars {
            let name = match get(var, "name") {
                Some(Json::Str(s)) => s,
                _ => continue,
            };
            if !has(init, &name) {
                issues.push(format!(
                    "{}.abstract_state.initial: 缺变量 {} 的初始值",
                    label,
                    pyval::py_repr(&Json::Str(name))
                ));
                continue;
            }
            let kind = match get(var, "kind") {
                Some(Json::Str(s)) => s,
                _ => String::new(),
            };
            let item_kind = match get(var, "item_kind") {
                Some(Json::Str(s)) => Some(s),
                _ => None,
            };
            let value = obj_get(init, &name).cloned().unwrap_or(Json::Null);
            if KINDS.contains(&kind.as_str())
                && !matches(&value, &kind, item_kind.as_deref())
            {
                issues.push(format!(
                    "{}.abstract_state.initial.{}: 值 {} 不匹配 kind={}",
                    label,
                    name,
                    pyval::py_repr(&value),
                    pyval::py_repr(&Json::Str(kind))
                ));
            }
        }
    }

    let transition_v = get(wm, "transition");
    let mut initial_phase: Option<String> = None;
    let mut phases: Vec<Json> = Vec::new();
    match &transition_v {
        Some(t @ Json::Object(_)) => {
            let ip = get(t, "initial_phase");
            match &ip {
                Some(Json::Str(s)) if !s.trim().is_empty() => {
                    initial_phase = Some(s.clone())
                }
                _ => {
                    issues.push(format!("{}.transition.initial_phase: 非空字符串", label));
                }
            }
            match get(t, "phases") {
                Some(Json::Array(p)) if !p.is_empty() => phases = p,
                _ => issues.push(format!("{}.transition.phases: 非空数组", label)),
            }
        }
        _ => {
            issues.push(format!("{}.transition: 缺失或非对象", label));
        }
    }

    let mut phase_names: Vec<String> = Vec::new();
    let mut edges: Vec<(String, String)> = Vec::new();
    for (idx, phase) in phases.iter().enumerate() {
        let at = format!("{}.transition.phases[{}]", label, idx);
        if !matches!(phase, Json::Object(_)) {
            issues.push(format!("{}: 非对象", at));
            continue;
        }
        let pname_v = get(phase, "phase");
        let nxt_v = get(phase, "next");
        let guard_v = get(phase, "guard");
        let writes_v = get(phase, "writes");
        let pname = match &pname_v {
            Some(Json::Str(s)) if !s.trim().is_empty() => s.clone(),
            _ => {
                issues.push(format!("{}.phase: 非空字符串", at));
                continue;
            }
        };
        if phase_names.contains(&pname) {
            issues.push(format!(
                "{}.phase: 相位重名 {}",
                at,
                pyval::py_repr(&Json::Str(pname.clone()))
            ));
        }
        phase_names.push(pname.clone());
        let nxt_ok = matches!(&nxt_v, Some(Json::Str(s)) if !s.trim().is_empty());
        if !nxt_ok {
            issues.push(format!("{}.next: 非空字符串", at));
        }
        let guard_ok = matches!(&guard_v, Some(Json::Str(s)) if !s.trim().is_empty());
        if !guard_ok {
            issues.push(format!("{}.guard: 非空守卫说明", at));
        }
        let writes_ok = match &writes_v {
            Some(Json::Array(w)) => w
                .iter()
                .all(|x| matches!(x, Json::Str(s) if !s.trim().is_empty())),
            _ => false,
        };
        if !writes_ok {
            issues.push(format!("{}.writes: 字符串数组（可为空）", at));
        }
        if let (Json::Str(p), Json::Str(n)) = (&pname_v.clone().unwrap_or(Json::Null), &nxt_v.clone().unwrap_or(Json::Null)) {
            // ⚠️ 真源 `edges` 是 **dict**（`edges[pname] = nxt`）⇒ **后者覆盖前者**，且**保留首次
            // 插入的位置**。用 Vec 追加会同时改变两处结论：①「next 无对应相位」会报出已被覆盖
            // 的旧值；② `all(n in phase_set ...)` 会因旧值悬空而**整段跳过**，漏报不可达相位。
            // 实测（2026-10-04，合成夹具 M92）：`begin→ghost` 被 `begin→begin` 覆盖，两处结论相反。
            match edges.iter_mut().find(|(k, _)| *k == *p) {
                Some(slot) => slot.1 = n.clone(),
                None => edges.push((p.clone(), n.clone())),
            }
        }
    }

    if let Some(ip) = &initial_phase {
        if !phase_names.contains(ip) {
            issues.push(format!(
                "{}.transition.initial_phase: {} 不在 phases 内",
                label,
                pyval::py_repr(&Json::Str(ip.clone()))
            ));
        }
    }
    for (pname, nxt) in &edges {
        if !phase_names.contains(nxt) {
            issues.push(format!(
                "{}.transition.phases[{}].next: {} 无对应相位",
                label,
                pyval::py_repr(&Json::Str(pname.clone())),
                pyval::py_repr(&Json::Str(nxt.clone()))
            ));
        }
    }

    let all_next_ok = edges.iter().all(|(_, n)| phase_names.contains(n));
    if let Some(ip0) = &initial_phase {
        if phase_names.contains(ip0) && all_next_ok {
            let mut seen: Vec<String> = vec![ip0.clone()];
            let mut frontier: Vec<String> = vec![ip0.clone()];
            while !frontier.is_empty() {
                let current = frontier.remove(0);
                if let Some((_, nxt)) = edges.iter().find(|(p, _)| *p == current) {
                    if !seen.contains(nxt) {
                        seen.push(nxt.clone());
                        frontier.push(nxt.clone());
                    }
                }
            }
            let mut unreachable: Vec<String> = phase_names
                .iter()
                .filter(|n| !seen.contains(n))
                .cloned()
                .collect();
            unreachable.sort();
            unreachable.dedup();
            if !unreachable.is_empty() {
                issues.push(format!(
                    "{}.transition: 从 initial_phase 不可达的相位 {}",
                    label,
                    pyval::py_repr_list(
                        &unreachable.iter().map(|s| Json::Str(s.clone())).collect::<Vec<_>>()
                    )
                ));
            }
        }
    }

    let invariants_v = get(wm, "invariants");
    match &invariants_v {
        Some(Json::Array(inv)) if !inv.is_empty() => {
            for (idx, i) in inv.iter().enumerate() {
                if !matches!(i, Json::Str(s) if !s.trim().is_empty()) {
                    issues.push(format!("{}.invariants[{}]: 非空字符串", label, idx));
                }
            }
        }
        _ => issues.push(format!("{}.invariants: 非空数组", label)),
    }

    let declared_names: Vec<String> = valid_vars
        .iter()
        .filter_map(|v| match get(v, "name") {
            Some(Json::Str(s)) => Some(s),
            _ => None,
        })
        .collect();
    let declared_kinds: Vec<(String, String)> = valid_vars
        .iter()
        .filter_map(|v| match (get(v, "name"), get(v, "kind")) {
            (Some(Json::Str(n)), Some(Json::Str(k))) => Some((n, k)),
            _ => None,
        })
        .collect();
    if let Some(checks_v) = get(wm, "checks") {
        if !matches!(checks_v, Json::Null) {
            let checks = match &checks_v {
                Json::Array(c) if !c.is_empty() => c.clone(),
                _ => {
                    issues.push(format!("{}.checks: 非空数组", label));
                    Vec::new()
                }
            };
            for (idx, check) in checks.iter().enumerate() {
                let at = format!("{}.checks[{}]", label, idx);
                if !matches!(check, Json::Object(_)) {
                    issues.push(format!("{}: 非对象", at));
                    continue;
                }
                let kind = match get(check, "kind") {
                    Some(Json::Str(s)) => s,
                    _ => String::new(),
                };
                let field_v = get(check, "field");
                let values_v = get(check, "values");
                if !["finite_phase", "monotonic", "finite_sequence"].contains(&kind.as_str()) {
                    issues.push(format!(
                        "{}.kind: 非法检查类型 {}",
                        at,
                        pyval::py_repr(&get(check, "kind").unwrap_or(Json::Null))
                    ));
                }
                let field_ok = matches!(&field_v, Some(Json::Str(s)) if !s.trim().is_empty());
                if !field_ok {
                    issues.push(format!("{}.field: 非空字符串", at));
                } else if let Some(Json::Str(f)) = &field_v {
                    if !declared_names.contains(f) {
                        issues.push(format!(
                            "{}.field: 未声明变量 {}",
                            at,
                            pyval::py_repr(&Json::Str(f.clone()))
                        ));
                    }
                }
                let field = match &field_v {
                    Some(Json::Str(s)) => s.clone(),
                    _ => String::new(),
                };
                if kind == "finite_phase" || kind == "finite_sequence" {
                    let ok = match &values_v {
                        Some(Json::Array(v)) => {
                            !v.is_empty()
                                && v.iter().all(|x| matches!(x, Json::Str(s) if !s.trim().is_empty()))
                        }
                        _ => false,
                    };
                    if !ok {
                        issues.push(format!("{}.values: {} 需非空字符串数组", at, kind));
                    }
                } else if kind == "monotonic" {
                    let k = declared_kinds
                        .iter()
                        .find(|(n, _)| *n == field)
                        .map(|(_, k)| k.clone())
                        .unwrap_or_default();
                    if k != "integer" && k != "number" {
                        issues.push(format!("{}.field: monotonic 只能用于 integer/number 变量", at));
                    }
                }
                if kind == "finite_sequence" {
                    let k = declared_kinds
                        .iter()
                        .find(|(n, _)| *n == field)
                        .map(|(_, k)| k.clone())
                        .unwrap_or_default();
                    if k != "array" {
                        issues.push(format!("{}.field: finite_sequence 只能用于 array 变量", at));
                    } else {
                        let spec = valid_vars.iter().find(|v| {
                            matches!(get(v, "name"), Some(Json::Str(n)) if *n == field)
                        });
                        let ik = spec.and_then(|s| get(s, "item_kind"));
                        if !matches!(ik, None | Some(Json::Null))
                            && !matches!(&ik, Some(Json::Str(s)) if s == "string")
                        {
                            issues.push(format!(
                                "{}.field: finite_sequence 的 array 元素应为 string",
                                at
                            ));
                        }
                    }
                }
            }
        }
    }

    if !slot_registry.is_empty() {
        for var in &valid_vars {
            let slot = match get(var, "slot") {
                Some(Json::Str(s)) if !s.trim().is_empty() => s,
                _ => continue,
            };
            let name = get(var, "name").unwrap_or(Json::Null);
            let source = get(var, "source").unwrap_or(Json::Null);
            let spec = slot_lookup(slot_registry, &slot);
            let Some(spec) = spec else {
                issues.push(format!(
                    "{}.abstract_state.variables[{}].slot: 未在 protocol/world_slots.json 注册 {}",
                    label,
                    pyval::py_repr(&name),
                    pyval::py_repr(&Json::Str(slot))
                ));
                continue;
            };
            if !matches!(spec, Json::Object(_)) {
                issues.push(format!(
                    "{}.abstract_state.variables[{}].slot: 未在 protocol/world_slots.json 注册 {}",
                    label,
                    pyval::py_repr(&name),
                    pyval::py_repr(&Json::Str(slot))
                ));
                continue;
            }
            let kind_v = get(var, "kind").unwrap_or(Json::Null);
            let spec_kind = get(&spec, "kind").unwrap_or(Json::Null);
            if !pyval::py_eq(&spec_kind, &kind_v) {
                issues.push(format!(
                    "{}.abstract_state.variables[{}].slot: 类型漂移 slot={} var={}",
                    label,
                    pyval::py_repr(&name),
                    pyval::py_repr(&spec_kind),
                    pyval::py_repr(&kind_v)
                ));
            }
            let item_kind_v = get(var, "item_kind").unwrap_or(Json::Null);
            if kind_v == Json::Str("array".to_string()) && pyval::py_truthy(&item_kind_v) {
                let spec_ik = get(&spec, "item_kind").unwrap_or(Json::Null);
                if !pyval::py_eq(&spec_ik, &item_kind_v) {
                    issues.push(format!(
                        "{}.abstract_state.variables[{}].slot: 元素类型漂移 slot={} var={}",
                        label,
                        pyval::py_repr(&name),
                        pyval::py_repr(&spec_ik),
                        pyval::py_repr(&item_kind_v)
                    ));
                }
            }
            let spec_owner = get(&spec, "owner").unwrap_or(Json::Null);
            if pyval::py_truthy(&spec_owner) && !pyval::py_eq(&source, &spec_owner) {
                issues.push(format!(
                    "{}.abstract_state.variables[{}].slot: owner 漂移 slot={} var.source={}",
                    label,
                    pyval::py_repr(&name),
                    pyval::py_repr(&spec_owner),
                    pyval::py_repr(&source)
                ));
            }
        }
    }
    issues
}

/// 真源 `scan` → `(issues, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let slot_registry = load_slots(root);
    if slot_registry.is_empty() {
        issues.push("protocol/world_slots.json 缺失或 slots 为空".to_string());
    }
    let (mut modules, mut variables, mut phases, mut invariants, mut checks, mut slots) =
        (0i64, 0i64, 0i64, 0i64, 0i64, 0i64);
    let mut models: Vec<Json> = Vec::new();

    for rel in crate::depth_small::module_docs(root) {
        let text = std::fs::read(root.join(&rel))
            .map(|b| String::from_utf8_lossy(&b).into_owned());
        let text = match text {
            Ok(t) => t,
            Err(e) => {
                issues.push(format!("{}: 读取失败 {}", rel, e));
                continue;
            }
        };
        let parsed = match crate::miniyaml::fence_yaml(&text, "machine_contract") {
            Some(p) => p,
            None => continue,
        };
        let mc = match obj_get(&parsed, "machine_contract") {
            Some(m @ Json::Object(_)) => m.clone(),
            _ => continue,
        };
        let Some(wm) = obj_get(&mc, "world_model").cloned() else { continue };
        for issue in validate_contract(&wm, &format!("{}.world_model", rel), &slot_registry) {
            issues.push(issue);
        }
        modules += 1;
        let abstract_v = get(&wm, "abstract_state").unwrap_or(Json::Null);
        let transition_v = get(&wm, "transition").unwrap_or(Json::Null);
        let invs = get(&wm, "invariants").unwrap_or(Json::Null);
        let check_list = get(&wm, "checks").unwrap_or(Json::Null);
        let mut model_slots = 0i64;
        if matches!(abstract_v, Json::Object(_)) {
            let var_list = arr_of(obj_get(&abstract_v, "variables"));
            variables += var_list.len() as i64;
            model_slots = var_list
                .iter()
                .filter(|v| pyval::py_truthy(&get(v, "slot").unwrap_or(Json::Null)))
                .count() as i64;
            slots += model_slots;
        }
        let mut model_phases = 0i64;
        let mut initial_phase = Json::Null;
        if matches!(transition_v, Json::Object(_)) {
            let ps = arr_of(obj_get(&transition_v, "phases"));
            model_phases = ps.len() as i64;
            phases += model_phases;
            initial_phase = get(&transition_v, "initial_phase").unwrap_or(Json::Null);
        }
        let model_invs = if matches!(invs, Json::Array(_)) {
            arr_of(Some(&invs)).len() as i64
        } else {
            0
        };
        if matches!(invs, Json::Array(_)) {
            invariants += model_invs;
        }
        let model_checks = if matches!(check_list, Json::Array(_)) {
            arr_of(Some(&check_list)).len() as i64
        } else {
            0
        };
        if matches!(check_list, Json::Array(_)) {
            checks += model_checks;
        }
        let mid = match obj_get(&mc, "id") {
            Some(v) if pyval::py_truthy(v) => pyval::plain_str(v),
            _ => rel.clone(),
        };
        models.push(Json::Object(vec![
            ("module".to_string(), Json::Str(mid)),
            ("source".to_string(), Json::Str(rel)),
            ("initial_phase".to_string(), initial_phase),
            ("phases".to_string(), Json::Int(model_phases)),
            ("invariants".to_string(), Json::Int(model_invs)),
            ("checks".to_string(), Json::Int(model_checks)),
            ("slots".to_string(), Json::Int(model_slots)),
        ]));
    }

    (
        issues,
        Json::Object(vec![
            ("modules".to_string(), Json::Int(modules)),
            ("variables".to_string(), Json::Int(variables)),
            ("phases".to_string(), Json::Int(phases)),
            ("invariants".to_string(), Json::Int(invariants)),
            ("checks".to_string(), Json::Int(checks)),
            ("slots".to_string(), Json::Int(slots)),
            ("slot_registry".to_string(), Json::Int(slot_registry.len() as i64)),
            ("models".to_string(), Json::Array(models)),
        ]),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_world_model_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 真语料差分 =====
    #[test]
    fn world_model_matches_truth_source_on_real_corpus() {
        let root = crate::testutil::repo_root();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, &[] as &[&str], "真语料 issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"checks": 3, "invariants": 5, "models": [{"checks": 3, "initial_phase": "begin", "invariants": 5, "module": "M50", "phases": 5, "slots": 4, "source": "04_模块库/通用类/M50_主循环.md"}], "modules": 1, "phases": 5, "slot_registry": 10, "slots": 4, "variables": 4}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want),
                "真语料 stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
    }

    /// ===== 合成分支夹具（逐支踩 `validate_contract`）=====
    ///
    /// 真语料只有 1 个模块且全绿 ⇒ 30 多个错误分支一个都踩不到。本夹具用 4 份合成模块文档覆盖：
    /// 契约骨架缺失 / 变量面（空名·非法 kind·重名·item_kind 越界·source 空·槽位重复·未注册·
    /// 类型漂移·元素类型漂移·owner 漂移·非对象）/ initial 面（未声明变量·类型不符）/
    /// 相位面（空 initial_phase·空 phases·空 phase 名·next 悬空·guard 空·writes 非字符串数组·
    /// 相位重名·ghost next·不可达相位）/ invariants 面 / checks 面（非法 kind·未声明 field·
    /// values 非法·monotonic 用错类型·finite_sequence 用错类型与元素类型）。
    const WM_FILES: [(&str, &str); 5] = [
        (r#"04_模块库/通用类/M90_测试.md"#, r#"---
module: M90
---

# 测试模块

```yaml
machine_contract:
  id: "M90"
  world_model:
    abstract_state: "not-an-object"
    transition: "not-an-object"

```
"#),
        (r#"04_模块库/通用类/M91_测试.md"#, r#"---
module: M91
---

# 测试模块

```yaml
machine_contract:
  id: "M91"
  world_model:
    abstract_state:
      variables:
        - name: ""
          kind: "widget"
          source: ""
        - name: "v1"
          kind: "string"
          source: "M91"
          item_kind: "string"
        - name: "v1"
          kind: "array"
          source: "M91"
          item_kind: "widget"
        - name: "v2"
          kind: "array"
          source: "M91"
          item_kind: "string"
          slot: "s.ok"
        - name: "v3"
          kind: "integer"
          source: "M91"
          slot: "s.ok"
        - name: "v4"
          kind: "integer"
          source: "M91"
          slot: "s.nope"
        - name: "v5"
          kind: "string"
          source: "M91"
          slot: "s.driftkind"
        - name: "v6"
          kind: "integer"
          source: "M91"
          slot: "s.drifdowner"
        - "not-an-object"
      initial:
        undeclared: 1
        v1: 5
        v2: ["a"]
        v3: "x"
    transition:
      initial_phase: ""
      phases: []
    invariants: []

```
"#),
        (r#"04_模块库/通用类/M92_测试.md"#, r#"---
module: M92
---

# 测试模块

```yaml
machine_contract:
  id: "M92"
  world_model:
    abstract_state:
      variables:
        - name: "p"
          kind: "string"
          source: "M92"
      initial:
        p: "begin"
    transition:
      initial_phase: "begin"
      phases:
        - phase: ""
          next: "b"
          guard: "g"
          writes: []
        - phase: "begin"
          next: "ghost"
          guard: ""
          writes: ["ok", 1]
        - phase: "begin"
          next: "begin"
          guard: "g"
          writes: []
        - phase: "b"
          next: "b"
          guard: "g"
          writes: []
        - phase: "c"
          next: "b"
          guard: "g"
          writes: []
        - "not-an-object"
    invariants: ["", "ok"]

```
"#),
        (r#"04_模块库/通用类/M93_测试.md"#, r#"---
module: M93
---

# 测试模块

```yaml
machine_contract:
  id: "M93"
  world_model:
    abstract_state:
      variables:
        - name: "n"
          kind: "string"
          source: "M93"
        - name: "arr"
          kind: "array"
          item_kind: "integer"
          source: "M93"
      initial:
        n: "begin"
        arr: [1]
    transition:
      initial_phase: "begin"
      phases:
        - phase: "begin"
          next: "begin"
          guard: "g"
          writes: []
    invariants: ["ok"]
    checks:
      - kind: "widget"
        field: "nope"
        values: []
      - kind: "finite_phase"
        field: "n"
        values: ["begin"]
      - kind: "monotonic"
        field: "n"
      - kind: "finite_sequence"
        field: "n"
        values: ["a"]
      - kind: "finite_sequence"
        field: "arr"
        values: ["a"]
      - "not-an-object"

```
"#),
        (r#"protocol/world_slots.json"#, r#"{
  "schema_version": "1",
  "slots": {
    "s.drifdowner": {
      "kind": "integer",
      "owner": "M98"
    },
    "s.driftitem": {
      "item_kind": "integer",
      "kind": "array",
      "owner": "M99"
    },
    "s.driftkind": {
      "kind": "string",
      "owner": "M99"
    },
    "s.ok": {
      "kind": "integer",
      "owner": "M99"
    }
  }
}
"#),
    ];

    fn build_wm_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("world-model-cases");
        for (rel, body) in WM_FILES {
            let p = root.join(rel);
            std::fs::create_dir_all(p.parent().unwrap()).unwrap();
            std::fs::write(p, body).unwrap();
        }
        root
    }

    #[test]
    fn world_model_matches_truth_source_branch_by_branch() {
        let root = build_wm_fixture();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, &[r#"04_模块库/通用类/M90_测试.md.world_model.abstract_state: 缺失或非对象"#, r#"04_模块库/通用类/M90_测试.md.world_model.transition: 缺失或非对象"#, r#"04_模块库/通用类/M90_测试.md.world_model.invariants: 非空数组"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables[0].name: 非空字符串"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables[0].kind: 非法类型 'widget'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables[0].source: 非空字符串"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables[1].item_kind: 仅 kind=array 可用"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables[2].name: 变量重名 'v1'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables[2].item_kind: 非法元素类型 'widget'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables[4].slot: 槽位重复 's.ok'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables[8]: 非对象"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.initial: 未声明变量 'undeclared'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.initial: 缺变量 '' 的初始值"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.initial.v1: 值 5 不匹配 kind='string'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.initial.v1: 值 5 不匹配 kind='array'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.initial.v3: 值 'x' 不匹配 kind='integer'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.initial: 缺变量 'v4' 的初始值"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.initial: 缺变量 'v5' 的初始值"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.initial: 缺变量 'v6' 的初始值"#, r#"04_模块库/通用类/M91_测试.md.world_model.transition.initial_phase: 非空字符串"#, r#"04_模块库/通用类/M91_测试.md.world_model.transition.phases: 非空数组"#, r#"04_模块库/通用类/M91_测试.md.world_model.invariants: 非空数组"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables['v2'].slot: 类型漂移 slot='integer' var='array'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables['v2'].slot: 元素类型漂移 slot=None var='string'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables['v2'].slot: owner 漂移 slot='M99' var.source='M91'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables['v3'].slot: owner 漂移 slot='M99' var.source='M91'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables['v4'].slot: 未在 protocol/world_slots.json 注册 's.nope'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables['v5'].slot: owner 漂移 slot='M99' var.source='M91'"#, r#"04_模块库/通用类/M91_测试.md.world_model.abstract_state.variables['v6'].slot: owner 漂移 slot='M98' var.source='M91'"#, r#"04_模块库/通用类/M92_测试.md.world_model.transition.phases[0].phase: 非空字符串"#, r#"04_模块库/通用类/M92_测试.md.world_model.transition.phases[1].guard: 非空守卫说明"#, r#"04_模块库/通用类/M92_测试.md.world_model.transition.phases[1].writes: 字符串数组（可为空）"#, r#"04_模块库/通用类/M92_测试.md.world_model.transition.phases[2].phase: 相位重名 'begin'"#, r#"04_模块库/通用类/M92_测试.md.world_model.transition.phases[5]: 非对象"#, r#"04_模块库/通用类/M92_测试.md.world_model.transition: 从 initial_phase 不可达的相位 ['b', 'c']"#, r#"04_模块库/通用类/M92_测试.md.world_model.invariants[0]: 非空字符串"#, r#"04_模块库/通用类/M93_测试.md.world_model.checks[0].kind: 非法检查类型 'widget'"#, r#"04_模块库/通用类/M93_测试.md.world_model.checks[0].field: 未声明变量 'nope'"#, r#"04_模块库/通用类/M93_测试.md.world_model.checks[2].field: monotonic 只能用于 integer/number 变量"#, r#"04_模块库/通用类/M93_测试.md.world_model.checks[3].field: finite_sequence 只能用于 array 变量"#, r#"04_模块库/通用类/M93_测试.md.world_model.checks[4].field: finite_sequence 的 array 元素应为 string"#, r#"04_模块库/通用类/M93_测试.md.world_model.checks[5]: 非对象"#] as &[&str], "合成 issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"checks": 6, "invariants": 3, "models": [{"checks": 0, "initial_phase": null, "invariants": 0, "module": "M90", "phases": 0, "slots": 0, "source": "04_模块库/通用类/M90_测试.md"}, {"checks": 0, "initial_phase": "", "invariants": 0, "module": "M91", "phases": 0, "slots": 5, "source": "04_模块库/通用类/M91_测试.md"}, {"checks": 0, "initial_phase": "begin", "invariants": 2, "module": "M92", "phases": 6, "slots": 0, "source": "04_模块库/通用类/M92_测试.md"}, {"checks": 6, "initial_phase": "begin", "invariants": 1, "module": "M93", "phases": 1, "slots": 0, "source": "04_模块库/通用类/M93_测试.md"}], "modules": 4, "phases": 7, "slot_registry": 4, "slots": 5, "variables": 12}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want),
                "合成 stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
    }
    // <<< GENERATED
}
