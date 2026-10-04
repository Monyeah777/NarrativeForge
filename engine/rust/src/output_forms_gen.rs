//! `output_forms` 的**生成器面**：13 个确定性生成器 + 组合证书校验。
//!
//! 真源 `GENERATORS` 是**唯一入口**——渲染与复算共用同一函数（「不复算的渲染 = 手写，禁」）。
//! 本线照搬这一点：`_recompute_entry` 与形态校验都走 `dispatch`。
//!
//! **真语料只触发 4 个**（`domain-report` 100 · `combo-cert` 4 · `concept-closure` 1 ·
//! `performance-report` 1）；另外 9 个（vega / mermaid / graphml）真语料从不触发，但**同表可达**
//! ⇒ 一并移植，不留「可达但缺席」。

use crate::pyjson::Json;
use crate::pyval;
use std::path::Path;

/// 生成器产出的两种形态：JSON 文档 或 纯文本（Mermaid）。
#[derive(Clone, Debug)]
pub enum GenOut {
    Json(Json),
    Text(String),
}

fn obj_get<'a>(v: &'a Json, k: &str) -> Option<&'a Json> {
    match v {
        Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv),
        _ => None,
    }
}

fn arr_of(v: Option<&Json>) -> Vec<Json> {
    match v {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    }
}

fn s_of(v: Option<&Json>) -> String {
    match v {
        None | Some(Json::Null) => String::new(),
        Some(x) => pyval::plain_str(x),
    }
}

/// 真源 `_pkg_rel`：包内声明的相对路径 → 仓库相对路径。
///
/// ⚠️ 两道关键处理（我第一版只看了真源的**尾部**，漏了它们，实测当场红）：
/// 1. **先过形状判据** `_reject_escape_forms`（外来清单字段出自投稿者之手；真源注释记着
///    「把 `path` 写成 `../../../PWNED.mmd`，文件真的落到了仓库外」）——越界即 `Err`；
/// 2. `rel` 以 `community/` 开头、或 `_pkg` 为空时**原样返回**，不再拼包目录。
///    语料实况：`concept-closure` 的 `recompute.graph` 已是仓相对路径 ⇒ 再拼一层会变成
///    `community/<包>/community/<包>/…`，真源因此丢件。
pub fn pkg_rel(entry: &Json, rel: &str) -> Result<String, String> {
    crate::output_forms::reject_escape_forms(&Json::Str(rel.to_string()), "清单相对路径")?;
    let pkg = s_of(obj_get(entry, "_pkg"));
    if rel.starts_with("community/") || pkg.is_empty() {
        return Ok(rel.to_string());
    }
    Ok(format!("community/{}/{}", pkg, rel.trim_start_matches('/')))
}

/// `pkg_rel` 的早退糖：越界即让所在生成器返回该 issue（真源是异常，由复算层转成问题行）。
macro_rules! prel {
    ($entry:expr, $rel:expr) => {
        match pkg_rel($entry, $rel) {
            Ok(v) => v,
            Err(e) => return (None, vec![e]),
        }
    };
}

/// `recompute` / `render` 声明（真源 `entry.get("recompute") or entry.get("render")`）。
fn spec_of(entry: &Json) -> Json {
    match obj_get(entry, "recompute") {
        Some(v) if pyval::py_truthy(v) => v.clone(),
        _ => obj_get(entry, "render").cloned().unwrap_or(Json::Object(vec![])),
    }
}

fn spec_params(spec: &Json) -> Vec<(String, Json)> {
    match obj_get(spec, "params") {
        Some(Json::Object(o)) => o.clone(),
        _ => Vec::new(),
    }
}

fn spec_inputs(spec: &Json) -> Vec<String> {
    arr_of(obj_get(spec, "inputs")).iter().map(pyval::plain_str).collect()
}

fn read_json_rel(root: &Path, rel: &str) -> Result<Json, String> {
    let text = std::fs::read_to_string(root.join(rel)).map_err(|e| e.to_string())?;
    crate::jsonmini::parse(&text).map(|r| r.value).map_err(|e| e.to_string())
}

/// 真源 `_gen_performance_report`。
pub fn gen_performance_report(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let spec = spec_of(entry);
    let inputs = spec_inputs(&spec);
    if inputs.is_empty() {
        return (None, vec!["声明可复算/可渲染但缺 inputs（无源即无功能）".to_string()]);
    }
    let src = prel!(entry, &inputs[0]);
    let series = match crate::quant_metrics::load_equity_curve(&root.join(&src)) {
        Ok(v) => v,
        Err(e) => return (None, vec![format!("输入 {} {}", src, e)]),
    };
    let params = spec_params(&spec);
    match crate::quant_metrics::performance_report(&series, &params) {
        Ok(v) => (Some(GenOut::Json(v)), Vec::new()),
        Err(e) => (None, vec![format!("复算异常 ValueError: {}", e)]),
    }
}

/// 真源 `_gen_concept_closure`。
pub fn gen_concept_closure(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    use crate::concept_graph as cg;
    let spec = spec_of(entry);
    let graph_decl = match obj_get(&spec, "graph") {
        Some(v) if pyval::py_truthy(v) => pyval::plain_str(v),
        _ => cg::DEFAULT_ASSET.to_string(),
    };
    let graph_path = prel!(entry, &graph_decl);
    let target = s_of(obj_get(&spec, "target"));
    if target.is_empty() {
        return (None, vec!["声明可复算但缺 target".to_string()]);
    }
    let graph = match cg::load_graph(root, &graph_path) {
        Ok(g) => g,
        Err(_) => {
            return (None, vec![format!("概念图 {} 不可解析（无源）", graph_path)]);
        }
    };
    if matches!(&graph, Json::Object(o) if o.is_empty()) {
        return (None, vec![format!("概念图 {} 不可解析（无源）", graph_path)]);
    }
    let clos = match cg::closure(&graph, &target) {
        Ok(ids) => ids,
        Err(e) => return (None, vec![format!("复算异常 ClosureError: {}", e)]),
    };
    let mut closure: Vec<Json> = Vec::new();
    for x in &clos {
        match cg::resolve(&graph, x) {
            Ok(v) => closure.push(Json::Str(v)),
            Err(e) => return (None, vec![format!("复算异常 ClosureError: {}", e)]),
        }
    }
    let order = match cg::toposort(&graph) {
        Ok(v) => v,
        Err(e) => return (None, vec![format!("复算异常 ClosureError: {}", e)]),
    };
    let aliases = match cg::alias_map(&graph) {
        Ok(v) => {
            let mut a = v;
            a.sort();
            a
        }
        Err(e) => return (None, vec![format!("复算异常 ClosureError: {}", e)]),
    };
    (
        Some(GenOut::Json(Json::Object(vec![
            ("kind".to_string(), Json::Str("nf-concept-closure/1".to_string())),
            ("graph".to_string(), Json::Str(graph_path)),
            ("target".to_string(), Json::Str(target)),
            ("closure".to_string(), Json::Array(closure)),
            (
                "load_order".to_string(),
                Json::Array(order.into_iter().map(Json::Str).collect()),
            ),
            (
                "alias".to_string(),
                Json::Array(
                    aliases
                        .into_iter()
                        .map(|(k, v)| Json::Array(vec![Json::Str(k), Json::Str(v)]))
                        .collect(),
                ),
            ),
        ]))),
        Vec::new(),
    )
}

/// 真源 `_gen_vega`。
pub fn gen_vega(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let spec = spec_of(entry);
    let inputs = spec_inputs(&spec);
    if inputs.is_empty() {
        return (None, vec!["图表面缺 inputs".to_string()]);
    }
    let src = prel!(entry, &inputs[0]);
    let series = match crate::quant_metrics::load_equity_curve(&root.join(&src)) {
        Ok(v) => v,
        Err(e) => return (None, vec![format!("输入 {} {}", src, e)]),
    };
    let params = spec_params(&spec);
    let title = params
        .iter()
        .find(|(k, _)| k == "title")
        .map(|(_, v)| pyval::plain_str(v))
        .unwrap_or_else(|| {
            if s_of(obj_get(&spec, "id")) == "vega-drawdown" {
                "回撤曲线".to_string()
            } else {
                "净值曲线".to_string()
            }
        });
    let out = if s_of(obj_get(&spec, "id")) == "vega-drawdown" {
        crate::quant_metrics::vega_drawdown(&series, &title)
    } else {
        crate::quant_metrics::vega_equity_curve(&series, &title)
    };
    (Some(GenOut::Json(out)), Vec::new())
}

/// 真源 `_gen_mermaid`（返回**纯文本**）。
pub fn gen_mermaid(_root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let spec = spec_of(entry);
    if s_of(obj_get(&spec, "id")) == "mermaid-declaration-flow" {
        return (Some(GenOut::Text(crate::quant_metrics::mermaid_declaration_flow())), Vec::new());
    }
    (
        None,
        vec![format!(
            "未登记 Mermaid 生成器：{}",
            pyval::py_repr(&Json::Str(s_of(obj_get(&spec, "id"))))
        )],
    )
}

/// 真源 `_gen_domain_report`。
pub fn gen_domain_report(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let spec = spec_of(entry);
    let inputs = spec_inputs(&spec);
    let mut params = spec_params(&spec);
    let family = params
        .iter()
        .find(|(k, _)| k == "family")
        .map(|(_, v)| pyval::plain_str(v))
        .unwrap_or_default();
    params.retain(|(k, _)| k != "family");
    if inputs.is_empty() || family.is_empty() {
        return (None, vec!["域报告缺 inputs 或 family（无源/无族即无功能）".to_string()]);
    }
    let src = prel!(entry, &inputs[0]);
    let rows = match crate::domain_metrics::load_rows(&root.join(&src)) {
        Ok(r) => r,
        Err(e) => return (None, vec![format!("输入 {} {}", src, e)]),
    };
    let metrics = match crate::domain_metrics::evaluate(&family, &rows, &params) {
        Ok(m) => m,
        Err(e) => return (None, vec![format!("复算异常 ValueError: {}", e)]),
    };
    let code = params
        .iter()
        .find(|(k, _)| k == "code")
        .map(|(_, v)| pyval::plain_str(v))
        .unwrap_or_default();
    let domain = params
        .iter()
        .find(|(k, _)| k == "domain")
        .map(|(_, v)| pyval::plain_str(v))
        .unwrap_or_default();
    (
        Some(GenOut::Json(Json::Object(vec![
            ("kind".to_string(), Json::Str("nf-domain-report/1".to_string())),
            ("code".to_string(), Json::Str(code)),
            ("domain".to_string(), Json::Str(domain)),
            ("family".to_string(), Json::Str(family)),
            ("sample".to_string(), Json::Str(inputs[0].clone())),
            ("sample_rows".to_string(), Json::Int(rows.len() as i64)),
            ("metrics".to_string(), metrics),
        ]))),
        Vec::new(),
    )
}

/// 真源 `_gen_vega_metrics`。
pub fn gen_vega_metrics(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let spec = match obj_get(entry, "render") {
        Some(v) if pyval::py_truthy(v) => v.clone(),
        _ => spec_of(entry),
    };
    let inputs = spec_inputs(&spec);
    if inputs.is_empty() {
        return (None, vec!["图表面缺 inputs".to_string()]);
    }
    let rel = prel!(entry, &inputs[0]);
    let data = match read_json_rel(root, &rel) {
        Ok(d) => d,
        Err(e) => return (None, vec![format!("输入 {} {}", inputs[0], e)]),
    };
    let metrics = match obj_get(&data, "metrics") {
        Some(Json::Object(o)) => o.clone(),
        _ => Vec::new(),
    };
    let mut sorted = metrics.clone();
    sorted.sort_by(|a, b| a.0.cmp(&b.0));
    let vals: Vec<Json> = sorted
        .iter()
        .filter_map(|(k, v)| match v {
            Json::Float(f) => Some(Json::Object(vec![
                ("metric".to_string(), Json::Str(k.clone())),
                ("value".to_string(), Json::Float(*f)),
            ])),
            Json::Int(i) => Some(Json::Object(vec![
                ("metric".to_string(), Json::Str(k.clone())),
                ("value".to_string(), Json::Float(*i as f64)),
            ])),
            _ => None, // 真源 `isinstance(v, (int, float)) and not isinstance(v, bool)`
        })
        .collect();
    if vals.is_empty() {
        return (None, vec!["报告里没有可画的标量指标".to_string()]);
    }
    let title = spec_params(&spec)
        .iter()
        .find(|(k, _)| k == "title")
        .map(|(_, v)| pyval::plain_str(v))
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "域指标".to_string());
    (
        Some(GenOut::Json(Json::Object(vec![
            (
                "$schema".to_string(),
                Json::Str("https://vega.github.io/schema/vega-lite/v5.json".to_string()),
            ),
            ("description".to_string(), Json::Str(title)),
            (
                "data".to_string(),
                Json::Object(vec![("values".to_string(), Json::Array(vals))]),
            ),
            (
                "mark".to_string(),
                Json::Object(vec![("type".to_string(), Json::Str("bar".to_string()))]),
            ),
            (
                "encoding".to_string(),
                Json::Object(vec![
                    (
                        "x".to_string(),
                        Json::Object(vec![
                            ("field".to_string(), Json::Str("value".to_string())),
                            ("type".to_string(), Json::Str("quantitative".to_string())),
                            ("title".to_string(), Json::Str("口径值".to_string())),
                        ]),
                    ),
                    (
                        "y".to_string(),
                        Json::Object(vec![
                            ("field".to_string(), Json::Str("metric".to_string())),
                            ("type".to_string(), Json::Str("nominal".to_string())),
                            ("title".to_string(), Json::Str("指标".to_string())),
                            ("sort".to_string(), Json::Str("-x".to_string())),
                        ]),
                    ),
                ]),
            ),
        ]))),
        Vec::new(),
    )
}

/// 真源 `_gen_combo_cert`。
pub fn gen_combo_cert(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let spec = match obj_get(entry, "recompute") {
        Some(v) => v.clone(),
        None => Json::Object(vec![]),
    };
    let params = spec_params(&spec);
    let packs: Vec<String> = arr_of(
        params.iter().find(|(k, _)| k == "packs").map(|(_, v)| v),
    )
    .iter()
    .map(pyval::plain_str)
    .collect();
    let mods: Vec<String> = arr_of(
        params.iter().find(|(k, _)| k == "extra_modules").map(|(_, v)| v),
    )
    .iter()
    .map(pyval::plain_str)
    .collect();
    if packs.is_empty() && mods.is_empty() {
        return (None, vec!["组合证书缺 packs/extra_modules（无输入即无复算）".to_string()]);
    }
    let mut cert = crate::pack_combo_core::combine_fresh(root, &packs, &mods, &[]);
    if let Json::Object(o) = &mut cert {
        if let Some(l) = params.iter().find(|(k, _)| k == "label").map(|(_, v)| v) {
            if pyval::py_truthy(l) {
                o.push(("label".to_string(), l.clone()));
            }
        }
        if let Some(n) = params.iter().find(|(k, _)| k == "note").map(|(_, v)| v) {
            if pyval::py_truthy(n) {
                o.push(("note".to_string(), n.clone()));
            }
        }
    }
    (Some(GenOut::Json(cert)), Vec::new())
}

/// 真源 `_combo_doc`。
fn combo_doc(root: &Path, entry: &Json) -> (Option<Json>, String) {
    let spec = match obj_get(entry, "render") {
        Some(Json::Object(o)) => o.clone(),
        _ => Vec::new(),
    };
    let rel = {
        let ins = arr_of(spec.iter().find(|(k, _)| k == "inputs").map(|(_, v)| v));
        if ins.is_empty() {
            "outputs/COMBO_CERT.json".to_string()
        } else {
            pyval::plain_str(&ins[0])
        }
    };
    // `combo_doc` 的返回形状是 `(Option<Json>, String)` ⇒ 不能走 `prel!`（那是 `(_, Vec<String>)`）
    let full = match pkg_rel(entry, &rel) {
        Ok(v) => v,
        Err(e) => return (None, e),
    };
    match read_json_rel(root, &full) {
        Ok(d) => (Some(d), String::new()),
        Err(e) => (None, format!("输入 {} {}", rel, e)),
    }
}

/// 真源 `_stack_pairs`：层栈两种历史形态兼容。
pub fn stack_pairs(stacks: Option<&Json>) -> Vec<(String, Vec<String>)> {
    match stacks {
        Some(Json::Array(a)) => a
            .iter()
            .filter_map(|r| match r {
                Json::Object(o) => Some((
                    s_of(o.iter().find(|(k, _)| k == "layer").map(|(_, v)| v)),
                    arr_of(o.iter().find(|(k, _)| k == "modules").map(|(_, v)| v))
                        .iter()
                        .map(pyval::plain_str)
                        .collect(),
                )),
                _ => None,
            })
            .collect(),
        Some(Json::Object(o)) => {
            let mut items = o.clone();
            items.sort_by(|a, b| a.0.cmp(&b.0));
            items
                .into_iter()
                .map(|(k, v)| (k, arr_of(Some(&v)).iter().map(pyval::plain_str).collect()))
                .collect()
        }
        _ => Vec::new(),
    }
}

/// 真源 `_gen_vega_layer_stack`。
pub fn gen_vega_layer_stack(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let (data, err) = combo_doc(root, entry);
    if !err.is_empty() {
        return (None, vec![err]);
    }
    let data = data.unwrap_or(Json::Object(vec![]));
    let rows: Vec<Json> = stack_pairs(obj_get(&data, "layer_stacks"))
        .into_iter()
        .map(|(k, v)| {
            Json::Object(vec![
                ("layer".to_string(), Json::Str(k)),
                ("modules".to_string(), Json::Int(v.len() as i64)),
            ])
        })
        .collect();
    if rows.is_empty() {
        return (None, vec!["证书无 layer_stacks（无可画数据）".to_string()]);
    }
    let title = {
        let rspec = obj_get(entry, "render").cloned().unwrap_or(Json::Object(vec![]));
        let t = spec_params(&rspec)
            .iter()
            .find(|(k, _)| k == "title")
            .map(|(_, v)| pyval::plain_str(v))
            .unwrap_or_default();
        if t.is_empty() {
            "层位堆叠".to_string()
        } else {
            t
        }
    };
    (
        Some(GenOut::Json(Json::Object(vec![
            (
                "$schema".to_string(),
                Json::Str("https://vega.github.io/schema/vega-lite/v5.json".to_string()),
            ),
            ("description".to_string(), Json::Str(title)),
            (
                "data".to_string(),
                Json::Object(vec![("values".to_string(), Json::Array(rows))]),
            ),
            (
                "mark".to_string(),
                Json::Object(vec![("type".to_string(), Json::Str("bar".to_string()))]),
            ),
            (
                "encoding".to_string(),
                Json::Object(vec![
                    (
                        "x".to_string(),
                        Json::Object(vec![
                            ("field".to_string(), Json::Str("layer".to_string())),
                            ("type".to_string(), Json::Str("nominal".to_string())),
                            ("title".to_string(), Json::Str("层位".to_string())),
                            ("sort".to_string(), Json::Null),
                        ]),
                    ),
                    (
                        "y".to_string(),
                        Json::Object(vec![
                            ("field".to_string(), Json::Str("modules".to_string())),
                            ("type".to_string(), Json::Str("quantitative".to_string())),
                            ("title".to_string(), Json::Str("模块数".to_string())),
                        ]),
                    ),
                ]),
            ),
        ]))),
        Vec::new(),
    )
}

/// 真源 `_gen_mermaid_layer_load`（纯文本）。
pub fn gen_mermaid_layer_load(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let (data, err) = combo_doc(root, entry);
    if !err.is_empty() {
        return (None, vec![err]);
    }
    let data = data.unwrap_or(Json::Object(vec![]));
    let mut lines = vec![
        "%% 组合包装载序（由 COMBO_CERT.json 确定性派生）".to_string(),
        "flowchart LR".to_string(),
    ];
    for (lay, mods) in stack_pairs(obj_get(&data, "layer_stacks")) {
        let tag = lay.replace('-', "");
        lines.push(format!("  {}[\"{}\"]", tag, lay));
        for (i, m) in mods.iter().enumerate() {
            let node = format!("{}_{}", tag, i);
            lines.push(format!("  {}[\"{}\"]", node, m));
            lines.push(format!("  {} --> {}", tag, node));
        }
    }
    (Some(GenOut::Text(lines.join("\n") + "\n")), Vec::new())
}

/// 真源 `_gen_graphml_module_deps`（纯文本）。
pub fn gen_graphml_module_deps(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    let (data, err) = combo_doc(root, entry);
    if !err.is_empty() {
        return (None, vec![err]);
    }
    let data = data.unwrap_or(Json::Object(vec![]));
    let mods: Vec<String> = arr_of(obj_get(&data, "modules")).iter().map(pyval::plain_str).collect();
    let explicit: Vec<String> = arr_of(
        obj_get(&data, "dependency_closure").and_then(|d| obj_get(d, "explicit")),
    )
    .iter()
    .map(pyval::plain_str)
    .collect();
    let mut out = vec![
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>".to_string(),
        "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">".to_string(),
        "  <key id=\"layer\" for=\"node\" attr.name=\"layer\" attr.type=\"string\"/>".to_string(),
        "  <graph id=\"combo\" edgedefault=\"directed\">".to_string(),
    ];
    let pairs = stack_pairs(obj_get(&data, "layer_stacks"));
    for m in &mods {
        let mut lay = String::new();
        for (k, v) in &pairs {
            if v.contains(m) {
                lay = k.clone();
                break;
            }
        }
        out.push(format!("    <node id=\"{}\"><data key=\"layer\">{}</data></node>", m, lay));
    }
    for m in &mods {
        for dep in combo_module_inputs(root, m) {
            if explicit.contains(&dep) && dep != *m {
                out.push(format!("    <edge source=\"{}\" target=\"{}\"/>", m, dep));
            }
        }
    }
    out.push("  </graph>".to_string());
    out.push("</graphml>".to_string());
    (Some(GenOut::Text(out.join("\n") + "\n")), Vec::new())
}

/// 真源 `m_prov`。
pub fn m_prov(meta: &[(String, Json)], node: &str) -> String {
    let rec = meta.iter().find(|(k, _)| k == node).map(|(_, v)| v.clone()).unwrap_or(Json::Null);
    let p = s_of(obj_get(&rec, "provenance"));
    if p.is_empty() {
        "unknown".to_string()
    } else {
        p
    }
}

/// 真源 `_gen_mermaid_concept_dag`（纯文本）。
pub fn gen_mermaid_concept_dag(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    use crate::concept_graph as cg;
    let spec = spec_of(entry);
    let graph_decl = match obj_get(&spec, "graph") {
        Some(v) if pyval::py_truthy(v) => pyval::plain_str(v),
        _ => cg::DEFAULT_ASSET.to_string(),
    };
    let graph_path = prel!(entry, &graph_decl);
    let graph = match cg::load_graph(root, &graph_path) {
        Ok(g) if !matches!(&g, Json::Object(o) if o.is_empty()) => g,
        _ => return (None, vec![format!("概念图 {} 不可解析（无源）", graph_path)]),
    };
    let prereq = cg::prereqs_of(&graph);
    let layer: Vec<(String, String)> = cg::node_meta(&graph)
        .into_iter()
        .map(|(n, m)| {
            let l = s_of(obj_get(&m, "layer"));
            (n, if l.is_empty() { "P00".to_string() } else { l })
        })
        .collect();
    let mut lines = vec![
        format!(
            "%% 概念前置图（由 {} 确定性派生；唯一机读真相在资产 §4 围栏块）",
            graph_path
        ),
        "flowchart TD".to_string(),
    ];
    let ids = cg::in_package_ids(&graph);
    let mut seen_layers: Vec<String> = Vec::new();
    for node in &ids {
        let lay = layer
            .iter()
            .find(|(n, _)| n == node)
            .map(|(_, l)| l.clone())
            .unwrap_or_else(|| "P00".to_string());
        if !seen_layers.contains(&lay) {
            seen_layers.push(lay);
        }
    }
    let mut sorted_layers = seen_layers.clone();
    sorted_layers.sort();
    for lay in &sorted_layers {
        let group: Vec<&String> = ids
            .iter()
            .filter(|n| layer.iter().find(|(nn, _)| nn == *n).map(|(_, l)| l) == Some(lay))
            .collect();
        if group.is_empty() {
            continue;
        }
        lines.push(format!("  subgraph {}[{}]", lay, lay));
        for n in group {
            lines.push(format!("    {}", n));
        }
        lines.push("  end".to_string());
    }
    for node in &ids {
        if let Some((_, pres)) = prereq.iter().find(|(k, _)| k == node) {
            for pre in pres {
                if pre.starts_with("C0") && pre == "C00" {
                    continue;
                }
                lines.push(format!("  {} --> {}", pre, node));
            }
        }
    }
    (Some(GenOut::Text(lines.join("\n") + "\n")), Vec::new())
}

/// 真源 `_gen_graphml_concept_dag`（纯文本）。
pub fn gen_graphml_concept_dag(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    use crate::concept_graph as cg;
    let spec = spec_of(entry);
    let graph_decl = match obj_get(&spec, "graph") {
        Some(v) if pyval::py_truthy(v) => pyval::plain_str(v),
        _ => cg::DEFAULT_ASSET.to_string(),
    };
    let graph_path = prel!(entry, &graph_decl);
    let graph = match cg::load_graph(root, &graph_path) {
        Ok(g) if !matches!(&g, Json::Object(o) if o.is_empty()) => g,
        _ => return (None, vec![format!("概念图 {} 不可解析（无源）", graph_path)]),
    };
    let prereq = cg::prereqs_of(&graph);
    let meta = cg::node_meta(&graph);
    let mut out = vec![
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>".to_string(),
        "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">".to_string(),
        "  <key id=\"layer\" for=\"node\" attr.name=\"layer\" attr.type=\"string\"/>".to_string(),
        "  <key id=\"branch\" for=\"node\" attr.name=\"branch\" attr.type=\"string\"/>".to_string(),
        "  <key id=\"provenance\" for=\"edge\" attr.name=\"provenance\" attr.type=\"string\"/>"
            .to_string(),
        "  <graph id=\"concept-graph\" edgedefault=\"directed\">".to_string(),
    ];
    let mut nodes = cg::in_package_ids(&graph);
    let base = nodes.clone();
    for node in &base {
        if let Some((_, pres)) = prereq.iter().find(|(k, _)| k == node) {
            for pre in pres {
                if !nodes.contains(pre) {
                    nodes.push(pre.clone());
                }
            }
        }
    }
    for node in &nodes {
        let m = meta.iter().find(|(k, _)| k == node).map(|(_, v)| v.clone()).unwrap_or(Json::Null);
        out.push(format!("    <node id=\"{}\">", node));
        out.push(format!("      <data key=\"layer\">{}</data>", s_of(obj_get(&m, "layer"))));
        out.push(format!("      <data key=\"branch\">{}</data>", s_of(obj_get(&m, "branch"))));
        out.push("    </node>".to_string());
    }
    for node in &nodes {
        if let Some((_, pres)) = prereq.iter().find(|(k, _)| k == node) {
            for pre in pres {
                out.push(format!("    <edge source=\"{}\" target=\"{}\">", pre, node));
                out.push(format!(
                    "      <data key=\"provenance\">{}</data>",
                    m_prov(&meta, node)
                ));
                out.push("    </edge>".to_string());
            }
        }
    }
    out.push("  </graph>".to_string());
    out.push("</graphml>".to_string());
    (Some(GenOut::Text(out.join("\n") + "\n")), Vec::new())
}

/// 真源 `_gen_id`。
pub fn gen_id(entry: &Json) -> String {
    for key in ["recompute", "render"] {
        if let Some(spec) = obj_get(entry, key) {
            if let Json::Object(o) = spec {
                if let Some(v) = o.iter().find(|(k, _)| k == "id").map(|(_, v)| v) {
                    if pyval::py_truthy(v) {
                        return pyval::plain_str(v);
                    }
                }
            }
        }
    }
    String::new()
}

/// 真源 `GENERATORS` 登记表（**唯一入口**）。
pub fn dispatch(root: &Path, entry: &Json) -> (Option<GenOut>, Vec<String>) {
    match gen_id(entry).as_str() {
        "performance-report" => gen_performance_report(root, entry),
        "concept-closure" => gen_concept_closure(root, entry),
        "vega-equity-curve" | "vega-drawdown" => gen_vega(root, entry),
        "mermaid-declaration-flow" => gen_mermaid(root, entry),
        "mermaid-concept-dag" => gen_mermaid_concept_dag(root, entry),
        "graphml-concept-dag" => gen_graphml_concept_dag(root, entry),
        "domain-report" => gen_domain_report(root, entry),
        "vega-metrics" => gen_vega_metrics(root, entry),
        "combo-cert" => gen_combo_cert(root, entry),
        "vega-layer-stack" => gen_vega_layer_stack(root, entry),
        "mermaid-layer-load" => gen_mermaid_layer_load(root, entry),
        "graphml-module-deps" => gen_graphml_module_deps(root, entry),
        other => (None, vec![format!("未登记生成器：{}", other)]),
    }
}

/// 真源 `GENERATORS` 的键（13 个），供「登记齐全」判据用。
pub const GENERATOR_IDS: [&str; 13] = [
    "performance-report",
    "concept-closure",
    "vega-equity-curve",
    "vega-drawdown",
    "mermaid-declaration-flow",
    "mermaid-concept-dag",
    "graphml-concept-dag",
    "domain-report",
    "vega-metrics",
    "combo-cert",
    "vega-layer-stack",
    "mermaid-layer-load",
    "graphml-module-deps",
];

/// 真源 `_check_combo_cert`：schema + 五不变量（复算一致由 recompute 面判）。
pub fn check_combo_cert(root: &Path, rel: &str, json_issues: Vec<String>) -> Vec<String> {
    let mut issues = json_issues;
    let data = match read_json_rel(root, rel) {
        Ok(d) => d,
        Err(e) => {
            issues.push(e);
            return issues;
        }
    };
    if !matches!(data, Json::Object(_)) {
        return issues;
    }
    let schema = crate::jsonmini::parse(crate::output_tables::CERT_SCHEMA_JSON)
        .map(|r| r.value)
        .unwrap_or(Json::Object(vec![]));
    let (errs, unsup) = crate::json_schema::json_schema_check_unsup(&data, &schema);
    for e in errs.iter().take(4) {
        issues.push(format!("证书不合 schema：{}", e));
    }
    if !unsup.is_empty() {
        let mut u: Vec<String> = unsup.clone();
        u.sort();
        u.dedup();
        issues.push(format!(
            "证书校验器遇不支持关键字：{}",
            pyval::py_repr_list(
                &u.iter().take(2).map(|x| Json::Str(x.clone())).collect::<Vec<_>>()
            )
        ));
    }
    let entry = Json::Object(vec![(
        "recompute".to_string(),
        Json::Object(vec![(
            "params".to_string(),
            Json::Object(vec![
                ("packs".to_string(), obj_get(&data, "packs").cloned().unwrap_or(Json::Null)),
                (
                    "extra_modules".to_string(),
                    obj_get(&data, "extra_modules").cloned().unwrap_or(Json::Null),
                ),
            ]),
        )]),
    )]);
    let (fresh, perr) = gen_combo_cert(root, &entry);
    match fresh {
        None => {
            for e in perr {
                issues.push(format!("复算失败：{}", e));
            }
        }
        Some(GenOut::Json(fresh)) => {
            if !matches!(obj_get(&fresh, "legal"), Some(Json::Bool(true))) {
                issues.push("组合非法（五不变量未全成立）".to_string());
            }
            let a = obj_get(&fresh, "digest").cloned().unwrap_or(Json::Null);
            let b = obj_get(&data, "digest").cloned().unwrap_or(Json::Null);
            if !crate::jsonread::json_eq(&a, &b) {
                issues.push("证书摘要与实时复算不一致（组合输入已变）".to_string());
            }
        }
        Some(GenOut::Text(_)) => {}
    }
    issues
}

/// 便捷：`pc.prof_get_module` 的再导出（供 `_combo_module_inputs` 一类调用点）。
pub fn prof_get_module(root: &Path, module_id: &str) -> Json {
    crate::pack_combo_core::prof_get_module(root, module_id)
}

/// 便捷：组合证书里某模块的 inputs。
pub fn combo_module_inputs(root: &Path, module_id: &str) -> Vec<String> {
    arr_of(obj_get(&prof_get_module(root, module_id), "inputs"))
        .iter()
        .map(pyval::plain_str)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_output_forms_gen_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 13 个生成器：真语料 106 条 + 9 个未触发生成器的合成入口 =====
    ///
    /// 比对取**最严**口径：JSON 走 `dumps_default()` 字符串相等（含键序），纯文本走字符串相等。
    /// 真源返回 `None` 的（缺 inputs / 不可解析）断言本线也返回 `None` 且 issue 列表一致。
    #[test]
    fn generators_match_truth_source() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &str, &str, &str, &str, &str)] = &[
        (r#"AI人力资源与招聘域包"#, r#"domain-report"#, r#"{"_pkg": "AI人力资源与招聘域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D14", "domain": "AI+人力资源与招聘", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D14", "domain": "AI+人力资源与招聘", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.96, "field_precision": 0.923077, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 24}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"AI保险域包"#, r#"domain-report"#, r#"{"_pkg": "AI保险域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D05", "domain": "AI+保险", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D05", "domain": "AI+保险", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.956522, "field_precision": 0.916667, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 22}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"AI农业域包"#, r#"domain-report"#, r#"{"_pkg": "AI农业域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D10", "domain": "AI+农业", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D10", "domain": "AI+农业", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.122494, "mape": 0.686392, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.983902, "rmse": 0.142947}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"AI制药与生物域包"#, r#"domain-report"#, r#"{"_pkg": "AI制药与生物域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D02", "domain": "AI+制药与生物", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D02", "domain": "AI+制药与生物", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.958333, "field_precision": 0.92, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"AI制造业域包"#, r#"domain-report"#, r#"{"_pkg": "AI制造业域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D08", "domain": "AI+制造业", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D08", "domain": "AI+制造业", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.666667, "family": "extraction", "field_f1": 0.916667, "field_precision": 0.846154, "field_recall": 1.0, "fn": 0, "fp": 4, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 22}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"AI医疗健康域包"#, r#"domain-report"#, r#"{"_pkg": "AI医疗健康域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D01", "domain": "AI+医疗健康", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D01", "domain": "AI+医疗健康", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.122919, "mape": 1.681713, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.982311, "rmse": 0.141885}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"AI政务与公共事务域包"#, r#"domain-report"#, r#"{"_pkg": "AI政务与公共事务域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D07", "domain": "AI+政务与公共事务", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D07", "domain": "AI+政务与公共事务", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.124244, "mape": 0.876649, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.984448, "rmse": 0.139465}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"AI教育域包"#, r#"domain-report"#, r#"{"_pkg": "AI教育域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D06", "domain": "AI+教育", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D06", "domain": "AI+教育", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.708333, "confusion": {"neg": {"neg": 11, "pos": 4}, "pos": {"neg": 3, "pos": 6}}, "digits": 6, "family": "classification", "macro": {"f1": 0.6951, "precision": 0.692857, "recall": 0.7}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.758621, "precision": 0.785714, "recall": 0.733333, "support": 15}, "pos": {"f1": 0.631579, "precision": 0.6, "recall": 0.666667, "support": 9}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"AI法律与合规域包"#, r#"domain-report"#, r#"{"_pkg": "AI法律与合规域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D03", "domain": "AI+法律与合规", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D03", "domain": "AI+法律与合规", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.833333, "confusion": {"neg": {"neg": 11, "pos": 1}, "pos": {"neg": 3, "pos": 9}}, "digits": 6, "family": "classification", "macro": {"f1": 0.832168, "precision": 0.842857, "recall": 0.833333}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.846154, "precision": 0.785714, "recall": 0.916667, "support": 12}, "pos": {"f1": 0.818182, "precision": 0.9, "recall": 0.75, "support": 12}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"AI系统域包"#, r#"concept-closure"#, r#"{"_pkg": "AI系统域包", "form": "concept-closure", "note": "M25/M26 产物面：由概念图复算 C42（评价与可观测）的闭包与全图装载序；check32 重算比对", "path": "outputs/CONCEPT_CLOSURE.json", "recompute": {"graph": "community/AI系统域包/assets/CONCEPT_GRAPH.md", "id": "concept-closure", "target": "C42"}, "role": "functional", "schema": "outputs/schemas/CONCEPT_CLOSURE.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"alias": [["agent", "C32"], ["agentic rag", "C31"], ["agent安全", "C39"], ["ai系统全栈", "C01"], ["ai编译器", "C12"], ["ann", "C29"], ["autodiff", "C08"], ["colbert", "C30"], ["cot", "C25"], ["cuda", "C06"], ["dpo", "C46"], ["embeddings", "C27"], ["evaluation", "C40"], ["few-shot", "C25"], ["finops", "C42"], ["flashattention", "C21"], ["function calling", "C33"], ["gpu gemm", "C05"], ["graphrag", "C31"], ["guardrails", "C41"], ["hitl", "C38"], ["io感知注意力", "C21"], ["json模式", "C26"], ["kv cache", "C20"], ["kv分页", "C22"], ["lora", "C46"], ["mcp", "C33"], ["mega-kernel", "C23"], ["memory", "C35"], ["ml systems", "C01"], ["moe", "C17"], ["multi-agent", "C34"], ["observability", "C40"], ["ocr", "C43"], ["pagedattention", "C22"], ["peft", "C46"], ["prompt engineering", "C25"], ["rag", "C28"], ["react", "C32"], ["rerank", "C30"], ["rlhf", "C46"], ["roofline", "C05"], ["ssa", "C11"], ["transformer", "C20"], ["tvm", "C12"], ["vllm", "C22"], ["zero", "C16"], ["上下文工程", "C25"], ["上下文检索", "C30"], ["人在环路", "C38"], ["任务分解", "C36"], ["优化器状态分片", "C16"], ["传统编译原理", "C11"], ["分块", "C43"], ["分块注意力", "C21"], ["前端优化", "C13"], ["剪枝", "C19"], ["反向模式", "C08"], ["反模式", "C45"], ["可靠性模式", "C41"], ["合成数据", "C46"], ["合规", "C42"], ["后端优化", "C14"], ["向量库", "C29"], ["向量数据库", "C29"], ["向量表示", "C27"], ["吞吐延迟口径", "C24"], ["回归基线", "C24"], ["基准", "C40"], ["多智能体", "C34"], ["多模态", "C44"], ["多级ir", "C12"], ["多面体", "C14"], ["定价", "C47"], ["实时语音", "C44"], ["审批门", "C38"], ["嵌入", "C27"], ["工具使用", "C33"], ["工具面", "C33"], ["幻觉", "C24"], ["张量并行", "C17"], ["循环工程", "C37"], ["微调", "C46"], ["思维链", "C25"], ["成本优化", "C42"], ["护栏", "C41"], ["持久执行", "C37"], ["推理引擎", "C18"], ["推理循环", "C32"], ["推理系统", "C18"], ["提示工程", "C25"], ["提示注入", "C39"], ["数据工程", "C43"], ["数据并行", "C15"], ["数据管线", "C43"], ["文档处理", "C43"], ["智能体", "C32"], ["机器学习系统", "C01"], ["检索增强生成", "C28"], ["模型压缩", "C19"], ["模型版图", "C47"], ["模型路由", "C42"], ["模型选型", "C47"], ["沙箱", "C39"], ["治理", "C42"], ["注意力机制", "C20"], ["流水并行", "C17"], ["混合检索", "C29"], ["激活重算", "C16"], ["状态管理", "C35"], ["算子融合", "C13"], ["算术强度", "C05"], ["结构化生成", "C26"], ["编排", "C34"], ["能力评估", "C47"], ["自动微分", "C08"], ["自动调优", "C14"], ["蒸馏", "C19"], ["观测性", "C40"], ["规划", "C36"], ["计算图", "C09"], ["训练与适配", "C46"], ["记忆", "C35"], ["设计模式", "C45"], ["评测", "C40"], ["语音", "C44"], ["越权", "C39"], ["输出契约", "C26"], ["连续批处理", "C22"], ["迭代级调度", "C22"], ["重排", "C30"], ["量化", "C19"], ["错误恢复", "C37"], ["长期记忆", "C35"], ["集合通信", "C15"], ["集成冗余", "C41"], ["预训练", "C46"]], "closure": ["C00", "C01", "C07", "C08", "C09", "C10", "C11", "C12", "C15", "C16", "C18", "C20", "C22", "C24", "C25", "C27", "C28", "C32", "C40", "C41", "C42", "C43", "C47"], "graph": "community/AI系统域包/assets/CONCEPT_GRAPH.md", "kind": "nf-concept-closure/1", "load_order": ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18", "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C29", "C32", "C33", "C34", "C35", "C36", "C37", "C38", "C39", "C43", "C28", "C30", "C31", "C40", "C41", "C44", "C45", "C46", "C19", "C47", "C42"], "target": "C42"}"#, r#"[]"#),
        (r#"AI能源与电力域包"#, r#"domain-report"#, r#"{"_pkg": "AI能源与电力域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D09", "domain": "AI+能源与电力", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D09", "domain": "AI+能源与电力", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.833333, "confusion": {"neg": {"neg": 12, "pos": 4}, "pos": {"neg": 0, "pos": 8}}, "digits": 6, "family": "classification", "macro": {"f1": 0.828572, "precision": 0.833333, "recall": 0.875}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.857143, "precision": 1.0, "recall": 0.75, "support": 16}, "pos": {"f1": 0.8, "precision": 0.666667, "recall": 1.0, "support": 8}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"AI金融投研与风控域包"#, r#"domain-report"#, r#"{"_pkg": "AI金融投研与风控域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D04", "domain": "AI+金融投研与风控", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D04", "domain": "AI+金融投研与风控", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.097125, "mape": 0.103984, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.991556, "rmse": 0.119198}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"AI食品与餐饮域包"#, r#"domain-report"#, r#"{"_pkg": "AI食品与餐饮域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D16", "domain": "AI+食品与餐饮", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D16", "domain": "AI+食品与餐饮", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.142894, "mape": 0.478941, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.969999, "rmse": 0.161809}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"三维与世界模型域包"#, r#"domain-report"#, r#"{"_pkg": "三维与世界模型域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A08", "domain": "三维与世界模型", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A08", "domain": "三维与世界模型", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.142494, "mape": 0.350618, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.982738, "rmse": 0.159409}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"上下文工程与长上下文域包"#, r#"domain-report"#, r#"{"_pkg": "上下文工程与长上下文域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C12", "domain": "上下文工程与长上下文", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C12", "domain": "上下文工程与长上下文", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.95, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 1, "field": "available_ts"}, {"count": 1, "field": "currency"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 1}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"世界书与设定库域包"#, r#"domain-report"#, r#"{"_pkg": "世界书与设定库域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E03", "domain": "世界书与设定库", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E03", "domain": "世界书与设定库", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.707341, "digits": 6, "exact_match": 0.333333, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.333333}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"个人助理与日常生活域包"#, r#"domain-report"#, r#"{"_pkg": "个人助理与日常生活域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E16", "domain": "个人助理与日常生活", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E16", "domain": "个人助理与日常生活", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 0.625, "digits": 6, "family": "preference", "loss": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 4, "win": 8, "win_rate_excl_tie": 0.666667}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"交通与出行域包"#, r#"domain-report"#, r#"{"_pkg": "交通与出行域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D13", "domain": "交通与出行", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D13", "domain": "交通与出行", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.134219, "mape": 0.395085, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.977773, "rmse": 0.150285}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"产业与商业落地域包"#, r#"domain-report"#, r#"{"_pkg": "产业与商业落地域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F10", "domain": "产业与商业落地", "family": "agreement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F10", "domain": "产业与商业落地", "family": "agreement", "kind": "nf-domain-report/1", "metrics": {"cohen_kappa": 0.782609, "confusion": {"F": {"F": 6, "T": 0}, "T": {"F": 2, "T": 12}}, "digits": 6, "expected_agreement": 0.54, "family": "agreement", "labels": 2, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "observed_agreement": 0.9}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"代码与软件工程域包"#, r#"domain-report"#, r#"{"_pkg": "代码与软件工程域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E13", "domain": "代码与软件工程", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E13", "domain": "代码与软件工程", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 0.875, "digits": 6, "family": "preference", "loss": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 1, "win": 11, "win_rate_excl_tie": 0.733333}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"代码大模型域包"#, r#"domain-report"#, r#"{"_pkg": "代码大模型域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A09", "domain": "代码大模型", "family": "exact_judgement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A09", "domain": "代码大模型", "family": "exact_judgement", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.5, "pass_at_k": 0.75, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"代码审查与缺陷检测域包"#, r#"domain-report"#, r#"{"_pkg": "代码审查与缺陷检测域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B09", "domain": "代码审查与缺陷检测", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B09", "domain": "代码审查与缺陷检测", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.75, "confusion": {"neg": {"neg": 10, "pos": 2}, "pos": {"neg": 4, "pos": 8}}, "digits": 6, "family": "classification", "macro": {"f1": 0.748252, "precision": 0.757143, "recall": 0.75}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.769231, "precision": 0.714286, "recall": 0.833333, "support": 12}, "pos": {"f1": 0.727273, "precision": 0.8, "recall": 0.666667, "support": 12}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"代码生成与补全域包"#, r#"domain-report"#, r#"{"_pkg": "代码生成与补全域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B08", "domain": "代码生成与补全", "family": "exact_judgement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B08", "domain": "代码生成与补全", "family": "exact_judgement", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.625, "pass_at_k": 1.0, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"企业培训与组织学习域包"#, r#"domain-report"#, r#"{"_pkg": "企业培训与组织学习域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E15", "domain": "企业培训与组织学习", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E15", "domain": "企业培训与组织学习", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.750992, "digits": 6, "exact_match": 0.333333, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.333333}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"传媒与新闻域包"#, r#"domain-report"#, r#"{"_pkg": "传媒与新闻域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D17", "domain": "传媒与新闻", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D17", "domain": "传媒与新闻", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.916667, "family": "extraction", "field_f1": 0.978723, "field_precision": 0.958333, "field_recall": 1.0, "fn": 0, "fp": 1, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"信息抽取与结构化域包"#, r#"domain-report"#, r#"{"_pkg": "信息抽取与结构化域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B05", "domain": "信息抽取与结构化", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B05", "domain": "信息抽取与结构化", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.666667, "family": "extraction", "field_f1": 0.923077, "field_precision": 0.857143, "field_recall": 1.0, "fn": 0, "fp": 4, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 24}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"具身智能与机器人域包"#, r#"domain-report"#, r#"{"_pkg": "具身智能与机器人域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A13", "domain": "具身智能与机器人", "family": "exact_judgement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A13", "domain": "具身智能与机器人", "family": "exact_judgement", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.3125, "pass_at_k": 1.0, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"内容分发与社区运营域包"#, r#"domain-report"#, r#"{"_pkg": "内容分发与社区运营域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E19", "domain": "内容分发与社区运营", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E19", "domain": "内容分发与社区运营", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 0.75, "digits": 6, "family": "preference", "loss": 7, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 3, "win": 6, "win_rate_excl_tie": 0.461538}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"内容改写与风格迁移域包"#, r#"domain-report"#, r#"{"_pkg": "内容改写与风格迁移域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E05", "domain": "内容改写与风格迁移", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E05", "domain": "内容改写与风格迁移", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.75, "family": "extraction", "field_f1": 0.941176, "field_precision": 0.888889, "field_recall": 1.0, "fn": 0, "fp": 3, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 24}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"分类与情感分析域包"#, r#"domain-report"#, r#"{"_pkg": "分类与情感分析域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B04", "domain": "分类与情感分析", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B04", "domain": "分类与情感分析", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.916667, "confusion": {"neg": {"neg": 11, "pos": 2}, "pos": {"neg": 0, "pos": 11}}, "digits": 6, "family": "classification", "macro": {"f1": 0.916667, "precision": 0.923077, "recall": 0.923077}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.916667, "precision": 1.0, "recall": 0.846154, "support": 13}, "pos": {"f1": 0.916667, "precision": 0.846154, "recall": 1.0, "support": 11}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"参数高效微调域包"#, r#"domain-report"#, r#"{"_pkg": "参数高效微调域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C06", "domain": "参数高效微调", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C06", "domain": "参数高效微调", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.8, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 2, "field": "available_ts"}, {"count": 2, "field": "owner"}, {"count": 2, "field": "version"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"可观测性成本与可靠性域包"#, r#"domain-report"#, r#"{"_pkg": "可观测性成本与可靠性域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C18", "domain": "可观测性、成本与可靠性", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C18", "domain": "可观测性、成本与可靠性", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.9, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 1, "field": "currency"}, {"count": 1, "field": "owner"}, {"count": 1, "field": "unit"}, {"count": 1, "field": "version"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 2}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"可解释性与审计域包"#, r#"domain-report"#, r#"{"_pkg": "可解释性与审计域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F06", "domain": "可解释性与审计", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F06", "domain": "可解释性与审计", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.75, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 4, "field": "available_ts"}, {"count": 2, "field": "owner"}, {"count": 2, "field": "version"}, {"count": 1, "field": "currency"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 5}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"合成数据生成域包"#, r#"domain-report"#, r#"{"_pkg": "合成数据生成域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C03", "domain": "合成数据生成", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C03", "domain": "合成数据生成", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.9, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 1, "field": "available_ts"}, {"count": 1, "field": "currency"}, {"count": 1, "field": "owner"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 2}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"合规与监管域包"#, r#"domain-report"#, r#"{"_pkg": "合规与监管域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F02", "domain": "合规与监管", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F02", "domain": "合规与监管", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.875, "confusion": {"neg": {"neg": 8, "pos": 2}, "pos": {"neg": 1, "pos": 13}}, "digits": 6, "family": "classification", "macro": {"f1": 0.869328, "precision": 0.877778, "recall": 0.864286}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.842105, "precision": 0.888889, "recall": 0.8, "support": 10}, "pos": {"f1": 0.896552, "precision": 0.866667, "recall": 0.928571, "support": 14}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"向量库与检索管线域包"#, r#"domain-report"#, r#"{"_pkg": "向量库与检索管线域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C15", "domain": "向量库与检索管线", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C15", "domain": "向量库与检索管线", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.8, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 3, "field": "version"}, {"count": 2, "field": "currency"}, {"count": 1, "field": "owner"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"图像生成与编辑域包"#, r#"domain-report"#, r#"{"_pkg": "图像生成与编辑域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A07", "domain": "图像生成与编辑", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A07", "domain": "图像生成与编辑", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.833333, "confusion": {"neg": {"neg": 11, "pos": 2}, "pos": {"neg": 2, "pos": 9}}, "digits": 6, "family": "classification", "macro": {"f1": 0.832168, "precision": 0.832168, "recall": 0.832168}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.846154, "precision": 0.846154, "recall": 0.846154, "support": 13}, "pos": {"f1": 0.818182, "precision": 0.818182, "recall": 0.818182, "support": 11}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"图像生成与视觉创作域包"#, r#"domain-report"#, r#"{"_pkg": "图像生成与视觉创作域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E07", "domain": "图像生成与视觉创作", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E07", "domain": "图像生成与视觉创作", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 0.875, "digits": 6, "family": "preference", "loss": 6, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 2, "win": 8, "win_rate_excl_tie": 0.571429}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"图像生成与视觉设计域包"#, r#"domain-report"#, r#"{"_pkg": "图像生成与视觉设计域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B15", "domain": "图像生成与视觉设计", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B15", "domain": "图像生成与视觉设计", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.875, "confusion": {"neg": {"neg": 10, "pos": 1}, "pos": {"neg": 2, "pos": 11}}, "digits": 6, "family": "classification", "macro": {"f1": 0.874783, "precision": 0.875, "recall": 0.877622}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.869565, "precision": 0.833333, "recall": 0.909091, "support": 11}, "pos": {"f1": 0.88, "precision": 0.916667, "recall": 0.846154, "support": 13}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"多智能体协同域包"#, r#"domain-report"#, r#"{"_pkg": "多智能体协同域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C17", "domain": "多智能体协同", "family": "drift"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C17", "domain": "多智能体协同", "family": "drift", "kind": "nf-domain-report/1", "metrics": {"buckets": 8, "detail": [{"actual": 0.111401, "bucket": "b0", "expected": 0.093101, "term": 0.003284}, {"actual": 0.139901, "bucket": "b1", "expected": 0.113001, "term": 0.005744}, {"actual": 0.103201, "bucket": "b2", "expected": 0.091701, "term": 0.001359}, {"actual": 0.174401, "bucket": "b3", "expected": 0.150501, "term": 0.003523}, {"actual": 0.169101, "bucket": "b4", "expected": 0.169901, "term": 4e-06}, {"actual": 0.056001, "bucket": "b5", "expected": 0.057201, "term": 2.5e-05}, {"actual": 0.063601, "bucket": "b6", "expected": 0.062401, "term": 2.3e-05}, {"actual": 0.127001, "bucket": "b7", "expected": 0.151701, "term": 0.00439}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.018351, "smoothing_epsilon": 1e-06}, "sample": "outputs/samples/CASES.csv", "sample_rows": 8}"#, r#"[]"#),
        (r#"多模态大模型域包"#, r#"domain-report"#, r#"{"_pkg": "多模态大模型域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A02", "domain": "多模态大模型", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A02", "domain": "多模态大模型", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.956522, "field_precision": 0.916667, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 22}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"多语翻译与本地化域包"#, r#"domain-report"#, r#"{"_pkg": "多语翻译与本地化域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E06", "domain": "多语翻译与本地化", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E06", "domain": "多语翻译与本地化", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.691468, "digits": 6, "exact_match": 0.25, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.25}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"多轮对话与角色扮演域包"#, r#"domain-report"#, r#"{"_pkg": "多轮对话与角色扮演域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B07", "domain": "多轮对话与角色扮演", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B07", "domain": "多轮对话与角色扮演", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 0.8125, "digits": 6, "family": "preference", "loss": 7, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 3, "win": 6, "win_rate_excl_tie": 0.461538}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"大语言模型域包"#, r#"domain-report"#, r#"{"_pkg": "大语言模型域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A01", "domain": "大语言模型", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A01", "domain": "大语言模型", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.856349, "digits": 6, "exact_match": 0.666667, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.666667}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"安全与对齐域包"#, r#"domain-report"#, r#"{"_pkg": "安全与对齐域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F01", "domain": "安全与对齐", "family": "agreement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F01", "domain": "安全与对齐", "family": "agreement", "kind": "nf-domain-report/1", "metrics": {"cohen_kappa": 0.8, "confusion": {"F": {"F": 9, "T": 1}, "T": {"F": 1, "T": 9}}, "digits": 6, "expected_agreement": 0.5, "family": "agreement", "labels": 2, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "observed_agreement": 0.9}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"对话与客服域包"#, r#"domain-report"#, r#"{"_pkg": "对话与客服域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E18", "domain": "对话与客服", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E18", "domain": "对话与客服", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.76746, "digits": 6, "exact_match": 0.5, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.5}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"对齐与偏好优化域包"#, r#"domain-report"#, r#"{"_pkg": "对齐与偏好优化域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C07", "domain": "对齐与偏好优化", "family": "latency_cost"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C07", "domain": "对齐与偏好优化", "family": "latency_cost", "kind": "nf-domain-report/1", "metrics": {"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 874.4, "mean_ms": 434.745, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 452.0, "p95_ms": 758.9, "p99_ms": 874.4, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 20804, "tokens_out": 6744}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"嵌入与检索表示域包"#, r#"domain-report"#, r#"{"_pkg": "嵌入与检索表示域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A11", "domain": "嵌入与检索表示", "family": "retrieval"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A11", "domain": "嵌入与检索表示", "family": "retrieval", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "retrieval", "k": 5, "map": 0.805556, "mrr": 0.833333, "n": 18, "ndcg_at_k": 0.871049, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "precision_at_k": 0.4, "queries": 3, "recall_at_k": 1.0}, "sample": "outputs/samples/CASES.csv", "sample_rows": 18}"#, r#"[]"#),
        (r#"平台与基础设施域包"#, r#"domain-report"#, r#"{"_pkg": "平台与基础设施域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F08", "domain": "平台与基础设施", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F08", "domain": "平台与基础设施", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.708333, "confusion": {"neg": {"neg": 10, "pos": 4}, "pos": {"neg": 3, "pos": 7}}, "digits": 6, "family": "classification", "macro": {"f1": 0.703704, "precision": 0.702797, "recall": 0.707143}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.740741, "precision": 0.769231, "recall": 0.714286, "support": 14}, "pos": {"f1": 0.666667, "precision": 0.636364, "recall": 0.7, "support": 10}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"建筑与房地产域包"#, r#"domain-report"#, r#"{"_pkg": "建筑与房地产域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D15", "domain": "建筑与房地产", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D15", "domain": "建筑与房地产", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.75, "confusion": {"neg": {"neg": 8, "pos": 4}, "pos": {"neg": 2, "pos": 10}}, "digits": 6, "family": "classification", "macro": {"f1": 0.748252, "precision": 0.757143, "recall": 0.75}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.727273, "precision": 0.8, "recall": 0.666667, "support": 12}, "pos": {"f1": 0.769231, "precision": 0.714286, "recall": 0.833333, "support": 12}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"开源与开发者生态域包"#, r#"domain-report"#, r#"{"_pkg": "开源与开发者生态域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F09", "domain": "开源与开发者生态", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F09", "domain": "开源与开发者生态", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.75, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 3, "field": "available_ts"}, {"count": 2, "field": "currency"}, {"count": 2, "field": "version"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 5}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"强化学习与决策域包"#, r#"domain-report"#, r#"{"_pkg": "强化学习与决策域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A12", "domain": "强化学习与决策", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A12", "domain": "强化学习与决策", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.154794, "mape": 0.961293, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.980296, "rmse": 0.168791}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"推理优化与加速域包"#, r#"domain-report"#, r#"{"_pkg": "推理优化与加速域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C10", "domain": "推理优化与加速", "family": "latency_cost"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C10", "domain": "推理优化与加速", "family": "latency_cost", "kind": "nf-domain-report/1", "metrics": {"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 877.8, "mean_ms": 470.58, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 474.9, "p95_ms": 854.3, "p99_ms": 877.8, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 20871, "tokens_out": 6722}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"推理服务与部署域包"#, r#"domain-report"#, r#"{"_pkg": "推理服务与部署域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C11", "domain": "推理服务与部署", "family": "drift"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C11", "domain": "推理服务与部署", "family": "drift", "kind": "nf-domain-report/1", "metrics": {"buckets": 8, "detail": [{"actual": 0.185001, "bucket": "b0", "expected": 0.175501, "term": 0.000501}, {"actual": 0.162001, "bucket": "b1", "expected": 0.177901, "term": 0.001489}, {"actual": 0.124701, "bucket": "b2", "expected": 0.149101, "term": 0.00436}, {"actual": 0.091601, "bucket": "b3", "expected": 0.074101, "term": 0.00371}, {"actual": 0.133201, "bucket": "b4", "expected": 0.108201, "term": 0.005197}, {"actual": 0.083601, "bucket": "b5", "expected": 0.084801, "term": 1.7e-05}, {"actual": 0.117301, "bucket": "b6", "expected": 0.090501, "term": 0.006951}, {"actual": 0.075201, "bucket": "b7", "expected": 0.055301, "term": 0.006117}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.028342, "smoothing_epsilon": 1e-06}, "sample": "outputs/samples/CASES.csv", "sample_rows": 8}"#, r#"[]"#),
        (r#"推荐排序与广告域包"#, r#"domain-report"#, r#"{"_pkg": "推荐排序与广告域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B17", "domain": "推荐、排序与广告", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B17", "domain": "推荐、排序与广告", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.863095, "digits": 6, "exact_match": 0.75, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.75}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"提示工程与指令设计域包"#, r#"domain-report"#, r#"{"_pkg": "提示工程与指令设计域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E01", "domain": "提示工程与指令设计", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E01", "domain": "提示工程与指令设计", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 0.9375, "digits": 6, "family": "preference", "loss": 8, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 0, "win": 8, "win_rate_excl_tie": 0.5}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"提示工程与提示模板域包"#, r#"domain-report"#, r#"{"_pkg": "提示工程与提示模板域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C13", "domain": "提示工程与提示模板", "family": "latency_cost"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C13", "domain": "提示工程与提示模板", "family": "latency_cost", "kind": "nf-domain-report/1", "metrics": {"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 789.8, "mean_ms": 469.04, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 462.3, "p95_ms": 721.1, "p99_ms": 789.8, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 23392, "tokens_out": 7182}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"搜索与信息聚合域包"#, r#"domain-report"#, r#"{"_pkg": "搜索与信息聚合域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E17", "domain": "搜索与信息聚合", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E17", "domain": "搜索与信息聚合", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.916667, "family": "extraction", "field_f1": 0.978723, "field_precision": 0.958333, "field_recall": 1.0, "fn": 0, "fp": 1, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"摘要与信息压缩域包"#, r#"domain-report"#, r#"{"_pkg": "摘要与信息压缩域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B02", "domain": "摘要与信息压缩", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B02", "domain": "摘要与信息压缩", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.676587, "digits": 6, "exact_match": 0.166667, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.166667}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"数字人与虚拟形象域包"#, r#"domain-report"#, r#"{"_pkg": "数字人与虚拟形象域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E20", "domain": "数字人与虚拟形象", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E20", "domain": "数字人与虚拟形象", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.956522, "field_precision": 0.916667, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 22}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"数学与形式化推理域包"#, r#"domain-report"#, r#"{"_pkg": "数学与形式化推理域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A10", "domain": "数学与形式化推理", "family": "exact_judgement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A10", "domain": "数学与形式化推理", "family": "exact_judgement", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.6875, "pass_at_k": 1.0, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"数据分析与决策支持域包"#, r#"domain-report"#, r#"{"_pkg": "数据分析与决策支持域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E14", "domain": "数据分析与决策支持", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E14", "domain": "数据分析与决策支持", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.75, "family": "extraction", "field_f1": 0.938776, "field_precision": 0.884615, "field_recall": 1.0, "fn": 0, "fp": 3, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"数据分析与表格理解域包"#, r#"domain-report"#, r#"{"_pkg": "数据分析与表格理解域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B11", "domain": "数据分析与表格理解", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B11", "domain": "数据分析与表格理解", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.112225, "mape": 15.174802, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.98559, "rmse": 0.13578}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"数据标注与标注质量域包"#, r#"domain-report"#, r#"{"_pkg": "数据标注与标注质量域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C02", "domain": "数据标注与标注质量", "family": "drift"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C02", "domain": "数据标注与标注质量", "family": "drift", "kind": "nf-domain-report/1", "metrics": {"buckets": 8, "detail": [{"actual": 0.100301, "bucket": "b0", "expected": 0.085901, "term": 0.002232}, {"actual": 0.108501, "bucket": "b1", "expected": 0.088701, "term": 0.003989}, {"actual": 0.168501, "bucket": "b2", "expected": 0.164201, "term": 0.000111}, {"actual": 0.095201, "bucket": "b3", "expected": 0.092801, "term": 6.1e-05}, {"actual": 0.167201, "bucket": "b4", "expected": 0.165901, "term": 1e-05}, {"actual": 0.154801, "bucket": "b5", "expected": 0.132701, "term": 0.003404}, {"actual": 0.090901, "bucket": "b6", "expected": 0.083101, "term": 0.0007}, {"actual": 0.117201, "bucket": "b7", "expected": 0.091901, "term": 0.006152}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.01666, "smoothing_epsilon": 1e-06}, "sample": "outputs/samples/CASES.csv", "sample_rows": 8}"#, r#"[]"#),
        (r#"数据采集与清洗域包"#, r#"domain-report"#, r#"{"_pkg": "数据采集与清洗域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C01", "domain": "数据采集与清洗", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C01", "domain": "数据采集与清洗", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.9, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 1, "field": "available_ts"}, {"count": 1, "field": "currency"}, {"count": 1, "field": "owner"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 2}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"文旅与酒店域包"#, r#"domain-report"#, r#"{"_pkg": "文旅与酒店域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D19", "domain": "文旅与酒店", "family": "regression"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D19", "domain": "文旅与酒店", "family": "regression", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "regression", "mae": 0.102119, "mape": 1.068382, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.986676, "rmse": 0.128744}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"文本生成与创作域包"#, r#"domain-report"#, r#"{"_pkg": "文本生成与创作域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B01", "domain": "文本生成与创作", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B01", "domain": "文本生成与创作", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.734722, "digits": 6, "exact_match": 0.25, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.25}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"文档解析与版面理解域包"#, r#"domain-report"#, r#"{"_pkg": "文档解析与版面理解域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B12", "domain": "文档解析与版面理解", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B12", "domain": "文档解析与版面理解", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.916667, "family": "extraction", "field_f1": 0.97561, "field_precision": 0.952381, "field_recall": 1.0, "fn": 0, "fp": 1, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 20}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"智能体与工作流编排域包"#, r#"domain-report"#, r#"{"_pkg": "智能体与工作流编排域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E12", "domain": "智能体与工作流编排", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E12", "domain": "智能体与工作流编排", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.765873, "digits": 6, "exact_match": 0.416667, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.416667}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"智能体框架与工具调用域包"#, r#"domain-report"#, r#"{"_pkg": "智能体框架与工具调用域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C16", "domain": "智能体框架与工具调用", "family": "latency_cost"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C16", "domain": "智能体框架与工具调用", "family": "latency_cost", "kind": "nf-domain-report/1", "metrics": {"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 894.3, "mean_ms": 586.97, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 609.4, "p95_ms": 874.3, "p99_ms": 894.3, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 17340, "tokens_out": 5479}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"机器翻译与本地化域包"#, r#"domain-report"#, r#"{"_pkg": "机器翻译与本地化域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B03", "domain": "机器翻译与本地化", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B03", "domain": "机器翻译与本地化", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.725198, "digits": 6, "exact_match": 0.416667, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.416667}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"模型运营与成本域包"#, r#"domain-report"#, r#"{"_pkg": "模型运营与成本域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F07", "domain": "模型运营与成本", "family": "agreement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F07", "domain": "模型运营与成本", "family": "agreement", "kind": "nf-domain-report/1", "metrics": {"cohen_kappa": 0.7, "confusion": {"F": {"F": 8, "T": 2}, "T": {"F": 1, "T": 9}}, "digits": 6, "expected_agreement": 0.5, "family": "agreement", "labels": 2, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "observed_agreement": 0.85}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"测试与用例生成域包"#, r#"domain-report"#, r#"{"_pkg": "测试与用例生成域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B10", "domain": "测试与用例生成", "family": "exact_judgement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B10", "domain": "测试与用例生成", "family": "exact_judgement", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.5, "pass_at_k": 1.0, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"游戏与互动娱乐域包"#, r#"domain-report"#, r#"{"_pkg": "游戏与互动娱乐域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D18", "domain": "游戏与互动娱乐", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D18", "domain": "游戏与互动娱乐", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.791667, "confusion": {"neg": {"neg": 9, "pos": 1}, "pos": {"neg": 4, "pos": 10}}, "digits": 6, "family": "classification", "macro": {"f1": 0.791305, "precision": 0.8007, "recall": 0.807143}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.782609, "precision": 0.692308, "recall": 0.9, "support": 10}, "pos": {"f1": 0.8, "precision": 0.909091, "recall": 0.714286, "support": 14}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"版权与知识产权域包"#, r#"domain-report"#, r#"{"_pkg": "版权与知识产权域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F04", "domain": "版权与知识产权", "family": "agreement"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F04", "domain": "版权与知识产权", "family": "agreement", "kind": "nf-domain-report/1", "metrics": {"cohen_kappa": 0.6, "confusion": {"F": {"F": 6, "T": 0}, "T": {"F": 4, "T": 10}}, "digits": 6, "expected_agreement": 0.5, "family": "agreement", "labels": 2, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "observed_agreement": 0.8}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"物流与供应链域包"#, r#"domain-report"#, r#"{"_pkg": "物流与供应链域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D12", "domain": "物流与供应链", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D12", "domain": "物流与供应链", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.666667, "confusion": {"neg": {"neg": 8, "pos": 4}, "pos": {"neg": 4, "pos": 8}}, "digits": 6, "family": "classification", "macro": {"f1": 0.666667, "precision": 0.666667, "recall": 0.666667}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.666667, "precision": 0.666667, "recall": 0.666667, "support": 12}, "pos": {"f1": 0.666667, "precision": 0.666667, "recall": 0.666667, "support": 12}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"监督微调域包"#, r#"domain-report"#, r#"{"_pkg": "监督微调域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C05", "domain": "监督微调", "family": "drift"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C05", "domain": "监督微调", "family": "drift", "kind": "nf-domain-report/1", "metrics": {"buckets": 8, "detail": [{"actual": 0.164601, "bucket": "b0", "expected": 0.143601, "term": 0.002866}, {"actual": 0.101601, "bucket": "b1", "expected": 0.116201, "term": 0.00196}, {"actual": 0.054301, "bucket": "b2", "expected": 0.051101, "term": 0.000194}, {"actual": 0.102701, "bucket": "b3", "expected": 0.091401, "term": 0.001317}, {"actual": 0.133701, "bucket": "b4", "expected": 0.106701, "term": 0.006091}, {"actual": 0.168601, "bucket": "b5", "expected": 0.193201, "term": 0.00335}, {"actual": 0.103201, "bucket": "b6", "expected": 0.112401, "term": 0.000786}, {"actual": 0.110001, "bucket": "b7", "expected": 0.082501, "term": 0.007911}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.024476, "smoothing_epsilon": 1e-06}, "sample": "outputs/samples/CASES.csv", "sample_rows": 8}"#, r#"[]"#),
        (r#"知识管理与检索增强域包"#, r#"domain-report"#, r#"{"_pkg": "知识管理与检索增强域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E11", "domain": "知识管理与检索增强", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E11", "domain": "知识管理与检索增强", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.75, "family": "extraction", "field_f1": 0.938776, "field_precision": 0.884615, "field_recall": 1.0, "fn": 0, "fp": 3, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"知识问答与检索增强域包"#, r#"domain-report"#, r#"{"_pkg": "知识问答与检索增强域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B06", "domain": "知识问答与检索增强", "family": "retrieval"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B06", "domain": "知识问答与检索增强", "family": "retrieval", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "retrieval", "k": 5, "map": 0.388889, "mrr": 0.361111, "n": 18, "ndcg_at_k": 0.550746, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "precision_at_k": 0.333333, "queries": 3, "recall_at_k": 1.0}, "sample": "outputs/samples/CASES.csv", "sample_rows": 18}"#, r#"[]"#),
        (r#"科研与实验域包"#, r#"domain-report"#, r#"{"_pkg": "科研与实验域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D20", "domain": "科研与实验", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D20", "domain": "科研与实验", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.75, "family": "extraction", "field_f1": 0.933333, "field_precision": 0.875, "field_recall": 1.0, "fn": 0, "fp": 3, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 21}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"端侧与边缘小模型域包"#, r#"domain-report"#, r#"{"_pkg": "端侧与边缘小模型域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A14", "domain": "端侧与边缘小模型", "family": "latency_cost"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A14", "domain": "端侧与边缘小模型", "family": "latency_cost", "kind": "nf-domain-report/1", "metrics": {"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 878.4, "mean_ms": 576.265, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 539.1, "p95_ms": 833.5, "p99_ms": 878.4, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 16787, "tokens_out": 5116}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"红队越狱与安全测试域包"#, r#"domain-report"#, r#"{"_pkg": "红队越狱与安全测试域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C09", "domain": "红队、越狱与安全测试", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C09", "domain": "红队、越狱与安全测试", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.8, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 3, "field": "unit"}, {"count": 2, "field": "currency"}, {"count": 2, "field": "version"}, {"count": 1, "field": "owner"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"组合包-受监管行业"#, r#"combo-cert"#, r#"{"_pkg": "组合包-受监管行业", "form": "combo-cert", "note": "组合证书（T4：按 packs+extra_modules 重算逐字段比对）", "path": "outputs/COMBO_CERT.json", "recompute": {"id": "combo-cert", "params": {"extra_modules": [], "label": "组合包 组合包-受监管行业", "note": "由 nf combine materialize 产物化；组合合法性由五不变量给出", "packs": ["AI法律与合规域包", "AI金融投研与风控域包", "可解释性与审计域包", "隐私与数据治理域包"]}}, "role": "functional", "schema": "outputs/schemas/COMBO_CERT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"assets_borrowed": [], "assets_unresolved": [], "dependency_closure": {"core": ["M00", "M06", "M08", "M10", "M12", "M13", "M20", "M22", "M23", "M24", "M50", "M80", "M90", "事件:M22", "通用:M10"], "dangling": [], "explicit": ["AI法律与合规:M01", "AI金融投研与风控:M01", "可解释性与审计:M01", "隐私与数据治理:M01"]}, "digest": "1120685bc682a148f62c3a317596be2b", "event_closure": {"published": ["d03_report_conflict", "d03_report_ready", "d03_spec_conflict", "d03_spec_ready", "d04_report_conflict", "d04_report_ready", "d04_spec_conflict", "d04_spec_ready", "doc_delta_committed", "doc_structure_ready", "f03_report_conflict", "f03_report_ready", "f03_spec_conflict", "f03_spec_ready", "f06_report_conflict", "f06_report_ready", "f06_spec_conflict", "f06_spec_ready", "intent_received", "interaction_update", "minute_tick", "narrative_event", "quest_state", "tick_day", "weather_state"], "unbridged": []}, "events_unpublished": [], "extra_modules": [], "label": "组合包 组合包-受监管行业", "layer_stacks": [{"layer": "P40", "modules": ["AI法律与合规:M01", "AI金融投研与风控:M01", "可解释性与审计:M01", "隐私与数据治理:M01"]}, {"layer": "P60", "modules": ["AI法律与合规:M02", "AI金融投研与风控:M02", "可解释性与审计:M02", "隐私与数据治理:M02"]}], "legal": true, "module_count": 8, "module_missing_contract": [], "modules": ["AI法律与合规:M01", "AI法律与合规:M02", "AI金融投研与风控:M01", "AI金融投研与风控:M02", "可解释性与审计:M01", "可解释性与审计:M02", "隐私与数据治理:M01", "隐私与数据治理:M02"], "modules_borrowed": [], "note": "由 nf combine materialize 产物化；组合合法性由五不变量给出", "packs": ["AI法律与合规域包", "AI金融投研与风控域包", "可解释性与审计域包", "隐私与数据治理域包"], "references_unresolved": [], "schema": "nf-combo/1", "unknown_packs": []}"#, r#"[]"#),
        (r#"组合包-数据管线"#, r#"combo-cert"#, r#"{"_pkg": "组合包-数据管线", "form": "combo-cert", "note": "组合证书（T4：按 packs+extra_modules 重算逐字段比对）", "path": "outputs/COMBO_CERT.json", "recompute": {"id": "combo-cert", "params": {"extra_modules": [], "label": "组合包 组合包-数据管线", "note": "由 nf combine materialize 产物化；组合合法性由五不变量给出", "packs": ["合成数据生成域包", "数据采集与清洗域包", "评测基准与排行榜域包", "预训练与继续预训练域包"]}}, "role": "functional", "schema": "outputs/schemas/COMBO_CERT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"assets_borrowed": [], "assets_unresolved": [], "dependency_closure": {"core": ["M00", "M06", "M08", "M10", "M12", "M13", "M20", "M22", "M23", "M24", "M50", "M80", "M90", "事件:M22", "通用:M10"], "dangling": [], "explicit": ["合成数据生成:M01", "数据采集与清洗:M01", "评测基准与排行榜:M01", "预训练与继续预训练:M01"]}, "digest": "8ecf05526fdd73bd94ac23094b85e673", "event_closure": {"published": ["c01_report_conflict", "c01_report_ready", "c01_spec_conflict", "c01_spec_ready", "c03_report_conflict", "c03_report_ready", "c03_spec_conflict", "c03_spec_ready", "c04_report_conflict", "c04_report_ready", "c04_spec_conflict", "c04_spec_ready", "c08_report_conflict", "c08_report_ready", "c08_spec_conflict", "c08_spec_ready", "doc_delta_committed", "doc_structure_ready", "intent_received", "interaction_update", "minute_tick", "narrative_event", "quest_state", "tick_day", "weather_state"], "unbridged": []}, "events_unpublished": [], "extra_modules": [], "label": "组合包 组合包-数据管线", "layer_stacks": [{"layer": "P40", "modules": ["合成数据生成:M01", "数据采集与清洗:M01", "评测基准与排行榜:M01", "预训练与继续预训练:M01"]}, {"layer": "P60", "modules": ["合成数据生成:M02", "数据采集与清洗:M02", "评测基准与排行榜:M02", "预训练与继续预训练:M02"]}], "legal": true, "module_count": 8, "module_missing_contract": [], "modules": ["合成数据生成:M01", "合成数据生成:M02", "数据采集与清洗:M01", "数据采集与清洗:M02", "评测基准与排行榜:M01", "评测基准与排行榜:M02", "预训练与继续预训练:M01", "预训练与继续预训练:M02"], "modules_borrowed": [], "note": "由 nf combine materialize 产物化；组合合法性由五不变量给出", "packs": ["合成数据生成域包", "数据采集与清洗域包", "评测基准与排行榜域包", "预训练与继续预训练域包"], "references_unresolved": [], "schema": "nf-combo/1", "unknown_packs": []}"#, r#"[]"#),
        (r#"组合包-检索栈"#, r#"combo-cert"#, r#"{"_pkg": "组合包-检索栈", "form": "combo-cert", "note": "组合证书（T4：按 packs+extra_modules 重算逐字段比对）", "path": "outputs/COMBO_CERT.json", "recompute": {"id": "combo-cert", "params": {"extra_modules": [], "label": "组合包 组合包-检索栈", "note": "由 nf combine materialize 产物化；组合合法性由五不变量给出", "packs": ["向量库与检索管线域包", "大语言模型域包", "嵌入与检索表示域包"]}}, "role": "functional", "schema": "outputs/schemas/COMBO_CERT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"assets_borrowed": [], "assets_unresolved": [], "dependency_closure": {"core": ["M00", "M06", "M08", "M10", "M12", "M13", "M20", "M22", "M23", "M24", "M50", "M80", "M90", "事件:M22", "通用:M10"], "dangling": [], "explicit": ["向量库与检索管线:M01", "大语言模型:M01", "嵌入与检索表示:M01"]}, "digest": "47a64d4727b3bd3777bb488dd0e3c1f9", "event_closure": {"published": ["a01_report_conflict", "a01_report_ready", "a01_spec_conflict", "a01_spec_ready", "a11_report_conflict", "a11_report_ready", "a11_spec_conflict", "a11_spec_ready", "c15_report_conflict", "c15_report_ready", "c15_spec_conflict", "c15_spec_ready", "doc_delta_committed", "doc_structure_ready", "intent_received", "interaction_update", "minute_tick", "narrative_event", "quest_state", "tick_day", "weather_state"], "unbridged": []}, "events_unpublished": [], "extra_modules": [], "label": "组合包 组合包-检索栈", "layer_stacks": [{"layer": "P40", "modules": ["向量库与检索管线:M01", "大语言模型:M01", "嵌入与检索表示:M01"]}, {"layer": "P60", "modules": ["向量库与检索管线:M02", "大语言模型:M02", "嵌入与检索表示:M02"]}], "legal": true, "module_count": 6, "module_missing_contract": [], "modules": ["向量库与检索管线:M01", "向量库与检索管线:M02", "大语言模型:M01", "大语言模型:M02", "嵌入与检索表示:M01", "嵌入与检索表示:M02"], "modules_borrowed": [], "note": "由 nf combine materialize 产物化；组合合法性由五不变量给出", "packs": ["向量库与检索管线域包", "大语言模型域包", "嵌入与检索表示域包"], "references_unresolved": [], "schema": "nf-combo/1", "unknown_packs": []}"#, r#"[]"#),
        (r#"组合包-轻混与保险"#, r#"combo-cert"#, r#"{"_pkg": "组合包-轻混与保险", "form": "combo-cert", "note": "组合证书（T4：按 packs+extra_modules 重算逐字段比对）", "path": "outputs/COMBO_CERT.json", "recompute": {"id": "combo-cert", "params": {"extra_modules": [], "label": "组合包 组合包-轻混与保险", "note": "由 nf combine materialize 产物化；组合合法性由五不变量给出", "packs": ["AI保险域包", "校园西幻轻混组合包"]}}, "role": "functional", "schema": "outputs/schemas/COMBO_CERT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"assets_borrowed": [], "assets_unresolved": [], "dependency_closure": {"core": ["M00", "M06", "M08", "M10", "M12", "M13", "M20", "M22", "M23", "M24", "M50", "M80", "M90", "事件:M22", "通用:M10"], "dangling": [], "explicit": ["AI保险:M01", "M07", "M17", "M40", "M41"]}, "digest": "fbf479641c598552a6f44cb1438d7963", "event_closure": {"published": ["campus_anonymous_gift", "campus_gift_intent", "confession_event", "d05_report_conflict", "d05_report_ready", "d05_spec_conflict", "d05_spec_ready", "doc_delta_committed", "doc_structure_ready", "intent_received", "interaction_update", "market_event", "minute_tick", "narrative_event", "npc_action", "production_output", "quest_state", "relationship_change", "romance_state_change", "tick_day", "travel_event", "weather_state"], "unbridged": []}, "events_unpublished": [], "extra_modules": [], "label": "组合包 组合包-轻混与保险", "layer_stacks": [{"layer": "P40", "modules": ["AI保险:M01", "M91", "M22", "M40", "M41", "M43", "M55"]}, {"layer": "P50", "modules": ["M92", "M17"]}, {"layer": "P60", "modules": ["AI保险:M02", "M07", "M09"]}], "legal": true, "module_count": 12, "module_missing_contract": [], "modules": ["AI保险:M01", "AI保险:M02", "M07", "M09", "M17", "M22", "M40", "M41", "M43", "M55", "M91", "M92"], "modules_borrowed": [{"by": "M09", "from": "西幻生存领域包", "mode": "closure_pull", "module": "M07", "why": "依赖 M09 的 inputs 需要 M07"}, {"by": "M17", "from": "西幻生存领域包", "mode": "closure_pull", "module": "M09", "why": "事件 market_event 需要发布方（M17 订阅）"}, {"by": "M43", "from": "校园情感领域包", "mode": "closure_pull", "module": "M41", "why": "依赖 M43 的 inputs 需要 M41"}, {"by": "校园西幻轻混组合包", "from": "西幻生存领域包", "mode": "module_borrow", "module": "M17"}, {"by": "校园西幻轻混组合包", "from": "校园情感领域包", "mode": "module_borrow", "module": "M22"}, {"by": "校园西幻轻混组合包", "from": "校园情感领域包", "mode": "module_borrow", "module": "M40"}, {"by": "校园西幻轻混组合包", "from": "校园情感领域包", "mode": "module_borrow", "module": "M43"}, {"by": "校园西幻轻混组合包", "from": "校园情感领域包", "mode": "module_borrow", "module": "M55"}], "note": "由 nf combine materialize 产物化；组合合法性由五不变量给出", "packs": ["AI保险域包", "校园西幻轻混组合包"], "references_unresolved": [], "schema": "nf-combo/1", "unknown_packs": []}"#, r#"[]"#),
        (r#"编辑校对与出版域包"#, r#"domain-report"#, r#"{"_pkg": "编辑校对与出版域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E10", "domain": "编辑校对与出版", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E10", "domain": "编辑校对与出版", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 0.875, "digits": 6, "family": "preference", "loss": 6, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 1, "win": 9, "win_rate_excl_tie": 0.6}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"视觉模型域包"#, r#"domain-report"#, r#"{"_pkg": "视觉模型域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A03", "domain": "视觉模型", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A03", "domain": "视觉模型", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.958333, "confusion": {"neg": {"neg": 10, "pos": 0}, "pos": {"neg": 1, "pos": 13}}, "digits": 6, "family": "classification", "macro": {"f1": 0.957672, "precision": 0.954546, "recall": 0.964286}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.952381, "precision": 0.909091, "recall": 1.0, "support": 10}, "pos": {"f1": 0.962963, "precision": 1.0, "recall": 0.928571, "support": 14}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"视频生成与剪辑域包"#, r#"domain-report"#, r#"{"_pkg": "视频生成与剪辑域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E08", "domain": "视频生成与剪辑", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E08", "domain": "视频生成与剪辑", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.666667, "family": "extraction", "field_f1": 0.92, "field_precision": 0.851852, "field_recall": 1.0, "fn": 0, "fp": 4, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"视频生成与理解域包"#, r#"domain-report"#, r#"{"_pkg": "视频生成与理解域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A06", "domain": "视频生成与理解", "family": "retrieval"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A06", "domain": "视频生成与理解", "family": "retrieval", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "family": "retrieval", "k": 5, "map": 0.519444, "mrr": 0.483333, "n": 18, "ndcg_at_k": 0.500422, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "precision_at_k": 0.266667, "queries": 3, "recall_at_k": 0.666667}, "sample": "outputs/samples/CASES.csv", "sample_rows": 18}"#, r#"[]"#),
        (r#"视频生成与自动剪辑域包"#, r#"domain-report"#, r#"{"_pkg": "视频生成与自动剪辑域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B16", "domain": "视频生成与自动剪辑", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B16", "domain": "视频生成与自动剪辑", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.916667, "family": "extraction", "field_f1": 0.978723, "field_precision": 0.958333, "field_recall": 1.0, "fn": 0, "fp": 1, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"角色扮演与角色卡域包"#, r#"domain-report"#, r#"{"_pkg": "角色扮演与角色卡域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E02", "domain": "角色扮演与角色卡", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E02", "domain": "角色扮演与角色卡", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.954545, "field_precision": 0.913043, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 21}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"记忆体与个性化域包"#, r#"domain-report"#, r#"{"_pkg": "记忆体与个性化域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C14", "domain": "记忆体与个性化", "family": "drift"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C14", "domain": "记忆体与个性化", "family": "drift", "kind": "nf-domain-report/1", "metrics": {"buckets": 8, "detail": [{"actual": 0.052201, "bucket": "b0", "expected": 0.051201, "term": 1.9e-05}, {"actual": 0.122201, "bucket": "b1", "expected": 0.122801, "term": 3e-06}, {"actual": 0.172401, "bucket": "b2", "expected": 0.194401, "term": 0.002642}, {"actual": 0.184301, "bucket": "b3", "expected": 0.181201, "term": 5.3e-05}, {"actual": 0.060601, "bucket": "b4", "expected": 0.053701, "term": 0.000834}, {"actual": 0.073201, "bucket": "b5", "expected": 0.050901, "term": 0.008102}, {"actual": 0.087201, "bucket": "b6", "expected": 0.103301, "term": 0.002728}, {"actual": 0.083101, "bucket": "b7", "expected": 0.075301, "term": 0.000769}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.01515, "smoothing_epsilon": 1e-06}, "sample": "outputs/samples/CASES.csv", "sample_rows": 8}"#, r#"[]"#),
        (r#"评测与基准域包"#, r#"domain-report"#, r#"{"_pkg": "评测与基准域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F05", "domain": "评测与基准", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F05", "domain": "评测与基准", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.583333, "confusion": {"neg": {"neg": 8, "pos": 7}, "pos": {"neg": 3, "pos": 6}}, "digits": 6, "family": "classification", "macro": {"f1": 0.58042, "precision": 0.594405, "recall": 0.6}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.615385, "precision": 0.727273, "recall": 0.533333, "support": 15}, "pos": {"f1": 0.545455, "precision": 0.461538, "recall": 0.666667, "support": 9}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"评测基准与排行榜域包"#, r#"domain-report"#, r#"{"_pkg": "评测基准与排行榜域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C08", "domain": "评测、基准与排行榜", "family": "drift"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C08", "domain": "评测、基准与排行榜", "family": "drift", "kind": "nf-domain-report/1", "metrics": {"buckets": 8, "detail": [{"actual": 0.172001, "bucket": "b0", "expected": 0.190701, "term": 0.00193}, {"actual": 0.073301, "bucket": "b1", "expected": 0.091901, "term": 0.004206}, {"actual": 0.151501, "bucket": "b2", "expected": 0.148701, "term": 5.2e-05}, {"actual": 0.113201, "bucket": "b3", "expected": 0.086801, "term": 0.00701}, {"actual": 0.049201, "bucket": "b4", "expected": 0.075901, "term": 0.011575}, {"actual": 0.087401, "bucket": "b5", "expected": 0.058301, "term": 0.011782}, {"actual": 0.081001, "bucket": "b6", "expected": 0.067001, "term": 0.002657}, {"actual": 0.200901, "bucket": "b7", "expected": 0.189901, "term": 0.000619}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.039832, "smoothing_epsilon": 1e-06}, "sample": "outputs/samples/CASES.csv", "sample_rows": 8}"#, r#"[]"#),
        (r#"语音合成与配音域包"#, r#"domain-report"#, r#"{"_pkg": "语音合成与配音域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B14", "domain": "语音合成与配音", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B14", "domain": "语音合成与配音", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.871032, "digits": 6, "exact_match": 0.5, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.5}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"语音识别与合成域包"#, r#"domain-report"#, r#"{"_pkg": "语音识别与合成域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A04", "domain": "语音识别与合成", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A04", "domain": "语音识别与合成", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.71627, "digits": 6, "exact_match": 0.25, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.25}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"语音转写与会议记录域包"#, r#"domain-report"#, r#"{"_pkg": "语音转写与会议记录域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B13", "domain": "语音转写与会议记录", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B13", "domain": "语音转写与会议记录", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.958333, "field_precision": 0.92, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"量化金融域包"#, r#"performance-report"#, r#"{"_pkg": "量化金融域包", "form": "performance-report", "note": "由 quant_metrics.performance_report 从净值数据复算的绩效报告：check32 会重算并逐字段比对（口径漂移即 FAIL）", "path": "outputs/PERFORMANCE_REPORT.json", "recompute": {"id": "performance-report", "inputs": ["outputs/samples/EQUITY_CURVE.csv"], "params": {"as_of": "2026-08-21", "benchmark_id": "NF-SAMPLE-INDEX", "cost_bps_fee": 3.0, "cost_bps_slippage": 5.0, "currency": "CNY", "fill_rule": "next_open", "frequency": "daily", "period_end": "2026-08-21", "period_start": "2026-06-01", "return_basis": "simple", "risk_free_rate_annual": 0.015, "single_side_turnover": true}}, "role": "functional", "schema": "outputs/schemas/PERFORMANCE_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"annual_factor": 252, "as_of": "2026-08-21", "benchmark": {"annualized": 0.143635, "calmar": 8.516894, "cumulative": 0.031922, "id": "NF-SAMPLE-INDEX", "max_drawdown": 0.016865, "sharpe": 6.473536, "volatility_annualized": 0.018464}, "costs": {"fee_bps": 3.0, "fill_rule": "next_open", "slippage_bps": 5.0, "turnover_basis": "single_side"}, "currency": "CNY", "disclosures": ["收益口径 = simple；年化因子 = 252（daily）；无风险利率年化 = 0.015", "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=3.0 bps, slippage=5.0 bps）", "成交价假设 = next_open（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）", "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间", "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据"], "excess": {"annualized": 0.190837, "information_ratio": 8.40542, "tracking_error": 0.018409}, "frequency": "daily", "gross": {"annualized": 0.334472, "calmar": 15.541439, "cumulative": 0.069888, "max_drawdown": 0.021521, "sharpe": 9.049606, "volatility_annualized": 0.030307}, "kind": "nf-performance/1", "period": {"end": "2026-08-21", "observations": 60, "start": "2026-06-01"}, "return_basis": "simple", "risk_free_rate_annual": 0.015}"#, r#"[]"#),
        (r#"长文本与小说创作域包"#, r#"domain-report"#, r#"{"_pkg": "长文本与小说创作域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E04", "domain": "长文本与小说创作", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E04", "domain": "长文本与小说创作", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 0.875, "digits": 6, "family": "preference", "loss": 10, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 2, "win": 4, "win_rate_excl_tie": 0.285714}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"隐私与数据治理域包"#, r#"domain-report"#, r#"{"_pkg": "隐私与数据治理域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "F03", "domain": "隐私与数据治理", "family": "contract_compliance"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "F03", "domain": "隐私与数据治理", "family": "contract_compliance", "kind": "nf-domain-report/1", "metrics": {"compliance_rate": 0.8, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 3, "field": "currency"}, {"count": 3, "field": "version"}, {"count": 1, "field": "available_ts"}, {"count": 1, "field": "owner"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 4}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"零售与电商域包"#, r#"domain-report"#, r#"{"_pkg": "零售与电商域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "D11", "domain": "零售与电商", "family": "extraction"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "D11", "domain": "零售与电商", "family": "extraction", "kind": "nf-domain-report/1", "metrics": {"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.954545, "field_precision": 0.913043, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 21}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"音频与音乐生成域包"#, r#"domain-report"#, r#"{"_pkg": "音频与音乐生成域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "A05", "domain": "音频与音乐生成", "family": "preference"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "A05", "domain": "音频与音乐生成", "family": "preference", "kind": "nf-domain-report/1", "metrics": {"agreement": 1.0, "digits": 6, "family": "preference", "loss": 7, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 0, "win": 9, "win_rate_excl_tie": 0.5625}, "sample": "outputs/samples/CASES.csv", "sample_rows": 16}"#, r#"[]"#),
        (r#"音频音乐与语音域包"#, r#"domain-report"#, r#"{"_pkg": "音频音乐与语音域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "E09", "domain": "音频音乐与语音", "family": "generation"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "E09", "domain": "音频音乐与语音", "family": "generation", "kind": "nf-domain-report/1", "metrics": {"char_f1": 0.746032, "digits": 6, "exact_match": 0.333333, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.333333}, "sample": "outputs/samples/CASES.csv", "sample_rows": 12}"#, r#"[]"#),
        (r#"预测异常与风险域包"#, r#"domain-report"#, r#"{"_pkg": "预测异常与风险域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "B18", "domain": "预测、异常与风险", "family": "classification"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "B18", "domain": "预测、异常与风险", "family": "classification", "kind": "nf-domain-report/1", "metrics": {"accuracy": 0.916667, "confusion": {"neg": {"neg": 8, "pos": 1}, "pos": {"neg": 1, "pos": 14}}, "digits": 6, "family": "classification", "macro": {"f1": 0.911111, "precision": 0.911111, "recall": 0.911111}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.888889, "precision": 0.888889, "recall": 0.888889, "support": 9}, "pos": {"f1": 0.933333, "precision": 0.933333, "recall": 0.933333, "support": 15}}}, "sample": "outputs/samples/CASES.csv", "sample_rows": 24}"#, r#"[]"#),
        (r#"预训练与继续预训练域包"#, r#"domain-report"#, r#"{"_pkg": "预训练与继续预训练域包", "form": "domain-report", "note": "度量族复算报告（check32 重算比对）", "path": "outputs/REPORT.json", "recompute": {"id": "domain-report", "inputs": ["outputs/samples/CASES.csv"], "params": {"code": "C04", "domain": "预训练与继续预训练", "family": "latency_cost"}}, "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json", "tier": "T4"}"#, r#"json"#, r#"{"code": "C04", "domain": "预训练与继续预训练", "family": "latency_cost", "kind": "nf-domain-report/1", "metrics": {"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 854.5, "mean_ms": 526.545, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 526.5, "p95_ms": 844.6, "p99_ms": 854.5, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 21085, "tokens_out": 6690}, "sample": "outputs/samples/CASES.csv", "sample_rows": 20}"#, r#"[]"#),
        (r#"合成"#, r#"vega-equity-curve"#, r#"{"_pkg": "量化金融域包", "recompute": {"id": "vega-equity-curve", "inputs": ["outputs/samples/EQUITY_CURVE.csv"], "params": {"title": "自检净值"}}}"#, r#"json"#, r#"{"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "data": {"values": [{"date": "2026-06-01", "series": "策略", "value": 1.0}, {"date": "2026-06-02", "series": "策略", "value": 1.003747}, {"date": "2026-06-03", "series": "策略", "value": 1.007437}, {"date": "2026-06-04", "series": "策略", "value": 1.011011}, {"date": "2026-06-05", "series": "策略", "value": 1.014417}, {"date": "2026-06-08", "series": "策略", "value": 1.017602}, {"date": "2026-06-09", "series": "策略", "value": 1.02052}, {"date": "2026-06-10", "series": "策略", "value": 1.023129}, {"date": "2026-06-11", "series": "策略", "value": 1.025396}, {"date": "2026-06-12", "series": "策略", "value": 1.027293}, {"date": "2026-06-15", "series": "策略", "value": 1.028798}, {"date": "2026-06-16", "series": "策略", "value": 1.0299}, {"date": "2026-06-17", "series": "策略", "value": 1.030594}, {"date": "2026-06-18", "series": "策略", "value": 1.030886}, {"date": "2026-06-19", "series": "策略", "value": 1.030786}, {"date": "2026-06-22", "series": "策略", "value": 1.030316}, {"date": "2026-06-23", "series": "策略", "value": 1.029503}, {"date": "2026-06-24", "series": "策略", "value": 1.028382}, {"date": "2026-06-25", "series": "策略", "value": 1.026995}, {"date": "2026-06-26", "series": "策略", "value": 1.025388}, {"date": "2026-06-29", "series": "策略", "value": 1.023613}, {"date": "2026-06-30", "series": "策略", "value": 1.021722}, {"date": "2026-07-01", "series": "策略", "value": 1.019775}, {"date": "2026-07-02", "series": "策略", "value": 1.017828}, {"date": "2026-07-03", "series": "策略", "value": 1.015939}, {"date": "2026-07-06", "series": "策略", "value": 1.014166}, {"date": "2026-07-07", "series": "策略", "value": 1.012562}, {"date": "2026-07-08", "series": "策略", "value": 1.011179}, {"date": "2026-07-09", "series": "策略", "value": 1.010064}, {"date": "2026-07-10", "series": "策略", "value": 1.009257}, {"date": "2026-07-13", "series": "策略", "value": 1.008793}, {"date": "2026-07-14", "series": "策略", "value": 1.0087}, {"date": "2026-07-15", "series": "策略", "value": 1.008998}, {"date": "2026-07-16", "series": "策略", "value": 1.0097}, {"date": "2026-07-17", "series": "策略", "value": 1.010809}, {"date": "2026-07-20", "series": "策略", "value": 1.012322}, {"date": "2026-07-21", "series": "策略", "value": 1.014225}, {"date": "2026-07-22", "series": "策略", "value": 1.016498}, {"date": "2026-07-23", "series": "策略", "value": 1.019114}, {"date": "2026-07-24", "series": "策略", "value": 1.022037}, {"date": "2026-07-27", "series": "策略", "value": 1.025226}, {"date": "2026-07-28", "series": "策略", "value": 1.028635}, {"date": "2026-07-29", "series": "策略", "value": 1.032212}, {"date": "2026-07-30", "series": "策略", "value": 1.035903}, {"date": "2026-07-31", "series": "策略", "value": 1.039651}, {"date": "2026-08-03", "series": "策略", "value": 1.043397}, {"date": "2026-08-04", "series": "策略", "value": 1.047085}, {"date": "2026-08-05", "series": "策略", "value": 1.050657}, {"date": "2026-08-06", "series": "策略", "value": 1.054059}, {"date": "2026-08-07", "series": "策略", "value": 1.05724}, {"date": "2026-08-10", "series": "策略", "value": 1.060153}, {"date": "2026-08-11", "series": "策略", "value": 1.062757}, {"date": "2026-08-12", "series": "策略", "value": 1.065017}, {"date": "2026-08-13", "series": "策略", "value": 1.066907}, {"date": "2026-08-14", "series": "策略", "value": 1.068405}, {"date": "2026-08-17", "series": "策略", "value": 1.0695}, {"date": "2026-08-18", "series": "策略", "value": 1.070187}, {"date": "2026-08-19", "series": "策略", "value": 1.070471}, {"date": "2026-08-20", "series": "策略", "value": 1.070365}, {"date": "2026-08-21", "series": "策略", "value": 1.069888}, {"date": "2026-06-01", "series": "基准", "value": 1.009663}, {"date": "2026-06-02", "series": "基准", "value": 1.011376}, {"date": "2026-06-03", "series": "基准", "value": 1.012954}, {"date": "2026-06-04", "series": "基准", "value": 1.014385}, {"date": "2026-06-05", "series": "基准", "value": 1.015657}, {"date": "2026-06-08", "series": "基准", "value": 1.016761}, {"date": "2026-06-09", "series": "基准", "value": 1.017689}, {"date": "2026-06-10", "series": "基准", "value": 1.018435}, {"date": "2026-06-11", "series": "基准", "value": 1.018998}, {"date": "2026-06-12", "series": "基准", "value": 1.019375}, {"date": "2026-06-15", "series": "基准", "value": 1.019569}, {"date": "2026-06-16", "series": "基准", "value": 1.019583}, {"date": "2026-06-17", "series": "基准", "value": 1.019424}, {"date": "2026-06-18", "series": "基准", "value": 1.019099}, {"date": "2026-06-19", "series": "基准", "value": 1.018619}, {"date": "2026-06-22", "series": "基准", "value": 1.017995}, {"date": "2026-06-23", "series": "基准", "value": 1.017242}, {"date": "2026-06-24", "series": "基准", "value": 1.016375}, {"date": "2026-06-25", "series": "基准", "value": 1.015411}, {"date": "2026-06-26", "series": "基准", "value": 1.014367}, {"date": "2026-06-29", "series": "基准", "value": 1.013264}, {"date": "2026-06-30", "series": "基准", "value": 1.012121}, {"date": "2026-07-01", "series": "基准", "value": 1.010957}, {"date": "2026-07-02", "series": "基准", "value": 1.009794}, {"date": "2026-07-03", "series": "基准", "value": 1.008652}, {"date": "2026-07-06", "series": "基准", "value": 1.007552}, {"date": "2026-07-07", "series": "基准", "value": 1.006512}, {"date": "2026-07-08", "series": "基准", "value": 1.005552}, {"date": "2026-07-09", "series": "基准", "value": 1.004691}, {"date": "2026-07-10", "series": "基准", "value": 1.003944}, {"date": "2026-07-13", "series": "基准", "value": 1.003328}, {"date": "2026-07-14", "series": "基准", "value": 1.002855}, {"date": "2026-07-15", "series": "基准", "value": 1.002538}, {"date": "2026-07-16", "series": "基准", "value": 1.002388}, {"date": "2026-07-17", "series": "基准", "value": 1.002411}, {"date": "2026-07-20", "series": "基准", "value": 1.002614}, {"date": "2026-07-21", "series": "基准", "value": 1.003001}, {"date": "2026-07-22", "series": "基准", "value": 1.003573}, {"date": "2026-07-23", "series": "基准", "value": 1.004329}, {"date": "2026-07-24", "series": "基准", "value": 1.005266}, {"date": "2026-07-27", "series": "基准", "value": 1.006378}, {"date": "2026-07-28", "series": "基准", "value": 1.007659}, {"date": "2026-07-29", "series": "基准", "value": 1.009098}, {"date": "2026-07-30", "series": "基准", "value": 1.010683}, {"date": "2026-07-31", "series": "基准", "value": 1.012402}, {"date": "2026-08-03", "series": "基准", "value": 1.01424}, {"date": "2026-08-04", "series": "基准", "value": 1.016179}, {"date": "2026-08-05", "series": "基准", "value": 1.018202}, {"date": "2026-08-06", "series": "基准", "value": 1.020291}, {"date": "2026-08-07", "series": "基准", "value": 1.022426}, {"date": "2026-08-10", "series": "基准", "value": 1.024586}, {"date": "2026-08-11", "series": "基准", "value": 1.026751}, {"date": "2026-08-12", "series": "基准", "value": 1.028901}, {"date": "2026-08-13", "series": "基准", "value": 1.031014}, {"date": "2026-08-14", "series": "基准", "value": 1.033073}, {"date": "2026-08-17", "series": "基准", "value": 1.035056}, {"date": "2026-08-18", "series": "基准", "value": 1.036946}, {"date": "2026-08-19", "series": "基准", "value": 1.038726}, {"date": "2026-08-20", "series": "基准", "value": 1.04038}, {"date": "2026-08-21", "series": "基准", "value": 1.041893}]}, "description": "自检净值", "encoding": {"color": {"field": "series", "title": "", "type": "nominal"}, "x": {"field": "date", "title": "日期", "type": "temporal"}, "y": {"field": "value", "scale": {"zero": false}, "title": "净值", "type": "quantitative"}}, "mark": {"point": false, "type": "line"}}"#, r#"[]"#),
        (r#"合成"#, r#"vega-drawdown"#, r#"{"_pkg": "量化金融域包", "recompute": {"id": "vega-drawdown", "inputs": ["outputs/samples/EQUITY_CURVE.csv"]}}"#, r#"json"#, r#"{"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "data": {"values": [{"date": "2026-06-01", "value": -0.0}, {"date": "2026-06-02", "value": -0.0}, {"date": "2026-06-03", "value": -0.0}, {"date": "2026-06-04", "value": -0.0}, {"date": "2026-06-05", "value": -0.0}, {"date": "2026-06-08", "value": -0.0}, {"date": "2026-06-09", "value": -0.0}, {"date": "2026-06-10", "value": -0.0}, {"date": "2026-06-11", "value": -0.0}, {"date": "2026-06-12", "value": -0.0}, {"date": "2026-06-15", "value": -0.0}, {"date": "2026-06-16", "value": -0.0}, {"date": "2026-06-17", "value": -0.0}, {"date": "2026-06-18", "value": -0.0}, {"date": "2026-06-19", "value": -9.700393641972923e-05}, {"date": "2026-06-22", "value": -0.0005529224375924782}, {"date": "2026-06-23", "value": -0.0013415644406849178}, {"date": "2026-06-24", "value": -0.0024289785679503474}, {"date": "2026-06-25", "value": -0.003774423166091951}, {"date": "2026-06-26", "value": -0.005333276424357303}, {"date": "2026-06-29", "value": -0.0070550962958075515}, {"date": "2026-06-30", "value": -0.008889440733504917}, {"date": "2026-07-01", "value": -0.010778107375597177}, {"date": "2026-07-02", "value": -0.012666774017689652}, {"date": "2026-07-03", "value": -0.014499178376658567}, {"date": "2026-07-06", "value": -0.01621905816938058}, {"date": "2026-07-07", "value": -0.01777500130955315}, {"date": "2026-07-08", "value": -0.019116565750238068}, {"date": "2026-07-09", "value": -0.020198159641318145}, {"date": "2026-07-10", "value": -0.02098098140822545}, {"date": "2026-07-13", "value": -0.02143107967321306}, {"date": "2026-07-14", "value": -0.021521293334083536}, {"date": "2026-07-15", "value": -0.021232221603552582}, {"date": "2026-07-16", "value": -0.020551253969886028}, {"date": "2026-07-17", "value": -0.019475480314991085}, {"date": "2026-07-20", "value": -0.018007810756960542}, {"date": "2026-07-21", "value": -0.016161825846892904}, {"date": "2026-07-22", "value": -0.013956926372072244}, {"date": "2026-07-23", "value": -0.01141930339533168}, {"date": "2026-07-24", "value": -0.008583878333782673}, {"date": "2026-07-27", "value": -0.005490422801357277}, {"date": "2026-07-28", "value": -0.0021835586088083483}, {"date": "2026-07-29", "value": -0.0}, {"date": "2026-07-30", "value": -0.0}, {"date": "2026-07-31", "value": -0.0}, {"date": "2026-08-03", "value": -0.0}, {"date": "2026-08-04", "value": -0.0}, {"date": "2026-08-05", "value": -0.0}, {"date": "2026-08-06", "value": -0.0}, {"date": "2026-08-07", "value": -0.0}, {"date": "2026-08-10", "value": -0.0}, {"date": "2026-08-11", "value": -0.0}, {"date": "2026-08-12", "value": -0.0}, {"date": "2026-08-13", "value": -0.0}, {"date": "2026-08-14", "value": -0.0}, {"date": "2026-08-17", "value": -0.0}, {"date": "2026-08-18", "value": -0.0}, {"date": "2026-08-19", "value": -0.0}, {"date": "2026-08-20", "value": -9.902183244566128e-05}, {"date": "2026-08-21", "value": -0.0005446200784514482}]}, "description": "回撤曲线", "encoding": {"x": {"field": "date", "title": "日期", "type": "temporal"}, "y": {"field": "value", "scale": {"zero": true}, "title": "回撤", "type": "quantitative"}}, "mark": {"line": true, "type": "area"}}"#, r#"[]"#),
        (r#"合成"#, r#"mermaid-declaration-flow"#, r#"{"_pkg": "量化金融域包", "recompute": {"id": "mermaid-declaration-flow"}}"#, r#"text"#, r#"%% 口径声明链（QUANT_METRICS 口径纪律的可视化，非新增真源）
flowchart LR
  A[收益口径 simple/log] --> D[绩效报告]
  B[年化因子 252/52/12] --> D
  C[无风险利率 rf] --> D
  E[净值序列] --> D
  D --> F[披露面 disclosures]
  G[成本与滑点申报] --> F
  H[基准与成交价假设] --> F
"#, r#"[]"#),
        (r#"合成"#, r#"vega-metrics"#, r#"{"_pkg": "AI人力资源与招聘域包", "render": {"id": "vega-metrics", "inputs": ["outputs/REPORT.json"], "params": {"title": "域指标图"}}}"#, r#"json"#, r#"{"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "data": {"values": [{"metric": "digits", "value": 6.0}, {"metric": "exact_match", "value": 0.833333}, {"metric": "field_f1", "value": 0.96}, {"metric": "field_precision", "value": 0.923077}, {"metric": "field_recall", "value": 1.0}, {"metric": "fn", "value": 0.0}, {"metric": "fp", "value": 2.0}, {"metric": "n", "value": 12.0}, {"metric": "tp", "value": 24.0}]}, "description": "域指标图", "encoding": {"x": {"field": "value", "title": "口径值", "type": "quantitative"}, "y": {"field": "metric", "sort": "-x", "title": "指标", "type": "nominal"}}, "mark": {"type": "bar"}}"#, r#"[]"#),
        (r#"合成"#, r#"vega-layer-stack"#, r#"{"_pkg": "组合包-受监管行业", "render": {"id": "vega-layer-stack", "inputs": ["outputs/COMBO_CERT.json"], "params": {"title": "层位堆叠自检"}}}"#, r#"json"#, r#"{"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "data": {"values": [{"layer": "P40", "modules": 4}, {"layer": "P60", "modules": 4}]}, "description": "层位堆叠自检", "encoding": {"x": {"field": "layer", "sort": null, "title": "层位", "type": "nominal"}, "y": {"field": "modules", "title": "模块数", "type": "quantitative"}}, "mark": {"type": "bar"}}"#, r#"[]"#),
        (r#"合成"#, r#"mermaid-layer-load"#, r#"{"_pkg": "组合包-受监管行业", "render": {"id": "mermaid-layer-load", "inputs": ["outputs/COMBO_CERT.json"]}}"#, r#"text"#, r#"%% 组合包装载序（由 COMBO_CERT.json 确定性派生）
flowchart LR
  P40["P40"]
  P40_0["AI法律与合规:M01"]
  P40 --> P40_0
  P40_1["AI金融投研与风控:M01"]
  P40 --> P40_1
  P40_2["可解释性与审计:M01"]
  P40 --> P40_2
  P40_3["隐私与数据治理:M01"]
  P40 --> P40_3
  P60["P60"]
  P60_0["AI法律与合规:M02"]
  P60 --> P60_0
  P60_1["AI金融投研与风控:M02"]
  P60 --> P60_1
  P60_2["可解释性与审计:M02"]
  P60 --> P60_2
  P60_3["隐私与数据治理:M02"]
  P60 --> P60_3
"#, r#"[]"#),
        (r#"合成"#, r#"graphml-module-deps"#, r#"{"_pkg": "组合包-受监管行业", "render": {"id": "graphml-module-deps", "inputs": ["outputs/COMBO_CERT.json"]}}"#, r#"text"#, r#"<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="layer" for="node" attr.name="layer" attr.type="string"/>
  <graph id="combo" edgedefault="directed">
    <node id="AI法律与合规:M01"><data key="layer">P40</data></node>
    <node id="AI法律与合规:M02"><data key="layer">P60</data></node>
    <node id="AI金融投研与风控:M01"><data key="layer">P40</data></node>
    <node id="AI金融投研与风控:M02"><data key="layer">P60</data></node>
    <node id="可解释性与审计:M01"><data key="layer">P40</data></node>
    <node id="可解释性与审计:M02"><data key="layer">P60</data></node>
    <node id="隐私与数据治理:M01"><data key="layer">P40</data></node>
    <node id="隐私与数据治理:M02"><data key="layer">P60</data></node>
    <edge source="AI法律与合规:M02" target="AI法律与合规:M01"/>
    <edge source="AI金融投研与风控:M02" target="AI金融投研与风控:M01"/>
    <edge source="可解释性与审计:M02" target="可解释性与审计:M01"/>
    <edge source="隐私与数据治理:M02" target="隐私与数据治理:M01"/>
  </graph>
</graphml>
"#, r#"[]"#),
        (r#"合成"#, r#"mermaid-concept-dag"#, r#"{"_pkg": "AI系统域包", "recompute": {"graph": "community/AI系统域包/assets/CONCEPT_GRAPH.md", "id": "mermaid-concept-dag"}}"#, r#"text"#, r#"%% 概念前置图（由 community/AI系统域包/assets/CONCEPT_GRAPH.md 确定性派生；唯一机读真相在资产 §4 围栏块）
flowchart TD
  subgraph P00[P00]
    C01
    C02
    C03
  end
  subgraph P10[P10]
    C04
    C05
  end
  subgraph P30[P30]
    C06
    C11
  end
  subgraph P40[P40]
    C07
    C08
    C09
    C12
    C13
    C20
    C25
    C26
    C27
    C32
  end
  subgraph P50[P50]
    C10
    C14
    C15
    C18
    C21
    C22
    C23
    C28
    C29
    C30
    C31
    C33
    C34
    C36
    C37
    C43
    C44
  end
  subgraph P60[P60]
    C16
    C17
    C19
    C35
    C38
    C39
    C41
    C46
    C47
  end
  subgraph P80[P80]
    C24
    C40
    C42
    C45
  end
  C01 --> C02
  C02 --> C03
  C03 --> C04
  C04 --> C05
  C05 --> C06
  C01 --> C07
  C07 --> C08
  C08 --> C09
  C07 --> C10
  C09 --> C10
  C11 --> C12
  C09 --> C12
  C12 --> C13
  C13 --> C14
  C06 --> C14
  C07 --> C15
  C15 --> C16
  C08 --> C16
  C15 --> C17
  C16 --> C17
  C09 --> C18
  C12 --> C18
  C10 --> C19
  C18 --> C19
  C46 --> C19
  C08 --> C20
  C10 --> C20
  C20 --> C21
  C14 --> C21
  C18 --> C22
  C20 --> C22
  C16 --> C22
  C14 --> C23
  C18 --> C23
  C18 --> C24
  C22 --> C24
  C01 --> C25
  C20 --> C25
  C25 --> C26
  C20 --> C27
  C25 --> C28
  C27 --> C28
  C43 --> C28
  C27 --> C29
  C28 --> C30
  C29 --> C30
  C28 --> C31
  C30 --> C31
  C25 --> C32
  C18 --> C32
  C32 --> C33
  C32 --> C34
  C33 --> C34
  C32 --> C35
  C29 --> C35
  C32 --> C36
  C32 --> C37
  C36 --> C37
  C32 --> C38
  C37 --> C38
  C25 --> C39
  C32 --> C39
  C33 --> C39
  C24 --> C40
  C28 --> C40
  C32 --> C40
  C25 --> C41
  C32 --> C41
  C40 --> C41
  C22 --> C42
  C40 --> C42
  C41 --> C42
  C47 --> C42
  C27 --> C43
  C18 --> C44
  C20 --> C44
  C28 --> C45
  C32 --> C45
  C40 --> C45
  C15 --> C46
  C08 --> C46
  C01 --> C47
  C20 --> C47
  C24 --> C47
"#, r#"[]"#),
        (r#"合成"#, r#"graphml-concept-dag"#, r#"{"_pkg": "AI系统域包", "recompute": {"graph": "community/AI系统域包/assets/CONCEPT_GRAPH.md", "id": "graphml-concept-dag"}}"#, r#"text"#, r#"<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="layer" for="node" attr.name="layer" attr.type="string"/>
  <key id="branch" for="node" attr.name="branch" attr.type="string"/>
  <key id="provenance" for="edge" attr.name="provenance" attr.type="string"/>
  <graph id="concept-graph" edgedefault="directed">
    <node id="C01">
      <data key="layer">P00</data>
      <data key="branch">compute</data>
    </node>
    <node id="C02">
      <data key="layer">P00</data>
      <data key="branch">compute</data>
    </node>
    <node id="C03">
      <data key="layer">P00</data>
      <data key="branch">compute</data>
    </node>
    <node id="C04">
      <data key="layer">P10</data>
      <data key="branch">compute</data>
    </node>
    <node id="C05">
      <data key="layer">P10</data>
      <data key="branch">compute</data>
    </node>
    <node id="C06">
      <data key="layer">P30</data>
      <data key="branch">compute</data>
    </node>
    <node id="C07">
      <data key="layer">P40</data>
      <data key="branch">compute</data>
    </node>
    <node id="C08">
      <data key="layer">P40</data>
      <data key="branch">compute</data>
    </node>
    <node id="C09">
      <data key="layer">P40</data>
      <data key="branch">compute</data>
    </node>
    <node id="C10">
      <data key="layer">P50</data>
      <data key="branch">compute</data>
    </node>
    <node id="C11">
      <data key="layer">P30</data>
      <data key="branch">compute</data>
    </node>
    <node id="C12">
      <data key="layer">P40</data>
      <data key="branch">compute</data>
    </node>
    <node id="C13">
      <data key="layer">P40</data>
      <data key="branch">compute</data>
    </node>
    <node id="C14">
      <data key="layer">P50</data>
      <data key="branch">compute</data>
    </node>
    <node id="C15">
      <data key="layer">P50</data>
      <data key="branch">compute</data>
    </node>
    <node id="C16">
      <data key="layer">P60</data>
      <data key="branch">compute</data>
    </node>
    <node id="C17">
      <data key="layer">P60</data>
      <data key="branch">compute</data>
    </node>
    <node id="C18">
      <data key="layer">P50</data>
      <data key="branch">compute</data>
    </node>
    <node id="C19">
      <data key="layer">P60</data>
      <data key="branch">compute</data>
    </node>
    <node id="C20">
      <data key="layer">P40</data>
      <data key="branch">compute</data>
    </node>
    <node id="C21">
      <data key="layer">P50</data>
      <data key="branch">compute</data>
    </node>
    <node id="C22">
      <data key="layer">P50</data>
      <data key="branch">compute</data>
    </node>
    <node id="C23">
      <data key="layer">P50</data>
      <data key="branch">compute</data>
    </node>
    <node id="C24">
      <data key="layer">P80</data>
      <data key="branch">compute</data>
    </node>
    <node id="C25">
      <data key="layer">P40</data>
      <data key="branch">app</data>
    </node>
    <node id="C26">
      <data key="layer">P40</data>
      <data key="branch">app</data>
    </node>
    <node id="C27">
      <data key="layer">P40</data>
      <data key="branch">app</data>
    </node>
    <node id="C28">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C29">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C30">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C31">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C32">
      <data key="layer">P40</data>
      <data key="branch">app</data>
    </node>
    <node id="C33">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C34">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C35">
      <data key="layer">P60</data>
      <data key="branch">app</data>
    </node>
    <node id="C36">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C37">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C38">
      <data key="layer">P60</data>
      <data key="branch">app</data>
    </node>
    <node id="C39">
      <data key="layer">P60</data>
      <data key="branch">app</data>
    </node>
    <node id="C40">
      <data key="layer">P80</data>
      <data key="branch">app</data>
    </node>
    <node id="C41">
      <data key="layer">P60</data>
      <data key="branch">app</data>
    </node>
    <node id="C42">
      <data key="layer">P80</data>
      <data key="branch">app</data>
    </node>
    <node id="C43">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C44">
      <data key="layer">P50</data>
      <data key="branch">app</data>
    </node>
    <node id="C45">
      <data key="layer">P80</data>
      <data key="branch">app</data>
    </node>
    <node id="C46">
      <data key="layer">P60</data>
      <data key="branch">compute</data>
    </node>
    <node id="C47">
      <data key="layer">P60</data>
      <data key="branch">app</data>
    </node>
    <node id="C00">
      <data key="layer"></data>
      <data key="branch"></data>
    </node>
    <edge source="C00" target="C01">
      <data key="provenance">['aisystem', 'cmu-mlsys']</data>
    </edge>
    <edge source="C01" target="C02">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C02" target="C03">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C03" target="C04">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C04" target="C05">
      <data key="provenance">['cmu-mlsys']</data>
    </edge>
    <edge source="C05" target="C06">
      <data key="provenance">['cmu-mlsys']</data>
    </edge>
    <edge source="C01" target="C07">
      <data key="provenance">['cmu-mlsys']</data>
    </edge>
    <edge source="C07" target="C08">
      <data key="provenance">['cmu-mlsys', 'cmu-dlsys', 'aisystem']</data>
    </edge>
    <edge source="C08" target="C09">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C07" target="C10">
      <data key="provenance">['cmu-dlsys', 'aisystem']</data>
    </edge>
    <edge source="C09" target="C10">
      <data key="provenance">['cmu-dlsys', 'aisystem']</data>
    </edge>
    <edge source="C00" target="C11">
      <data key="provenance">['aisystem', 'mlir']</data>
    </edge>
    <edge source="C11" target="C12">
      <data key="provenance">['aisystem', 'tvm', 'mlir', 'dlc-survey']</data>
    </edge>
    <edge source="C09" target="C12">
      <data key="provenance">['aisystem', 'tvm', 'mlir', 'dlc-survey']</data>
    </edge>
    <edge source="C12" target="C13">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C13" target="C14">
      <data key="provenance">['aisystem', 'cmu-mlsys']</data>
    </edge>
    <edge source="C06" target="C14">
      <data key="provenance">['aisystem', 'cmu-mlsys']</data>
    </edge>
    <edge source="C07" target="C15">
      <data key="provenance">['cmu-mlsys']</data>
    </edge>
    <edge source="C00" target="C15">
      <data key="provenance">['cmu-mlsys']</data>
    </edge>
    <edge source="C15" target="C16">
      <data key="provenance">['zero', 'cmu-mlsys']</data>
    </edge>
    <edge source="C08" target="C16">
      <data key="provenance">['zero', 'cmu-mlsys']</data>
    </edge>
    <edge source="C15" target="C17">
      <data key="provenance">['cmu-mlsys']</data>
    </edge>
    <edge source="C16" target="C17">
      <data key="provenance">['cmu-mlsys']</data>
    </edge>
    <edge source="C09" target="C18">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C12" target="C18">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C10" target="C19">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C18" target="C19">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C46" target="C19">
      <data key="provenance">['aisystem']</data>
    </edge>
    <edge source="C08" target="C20">
      <data key="provenance">['cmu-mlsys', 'cmu-dlsys']</data>
    </edge>
    <edge source="C10" target="C20">
      <data key="provenance">['cmu-mlsys', 'cmu-dlsys']</data>
    </edge>
    <edge source="C20" target="C21">
      <data key="provenance">['flash-attention']</data>
    </edge>
    <edge source="C14" target="C21">
      <data key="provenance">['flash-attention']</data>
    </edge>
    <edge source="C18" target="C22">
      <data key="provenance">['orca', 'vllm']</data>
    </edge>
    <edge source="C20" target="C22">
      <data key="provenance">['orca', 'vllm']</data>
    </edge>
    <edge source="C16" target="C22">
      <data key="provenance">['orca', 'vllm']</data>
    </edge>
    <edge source="C14" target="C23">
      <data key="provenance">['aisystem', 'cmu-mlsys']</data>
    </edge>
    <edge source="C18" target="C23">
      <data key="provenance">['aisystem', 'cmu-mlsys']</data>
    </edge>
    <edge source="C18" target="C24">
      <data key="provenance">['cs2023', 'inferred']</data>
    </edge>
    <edge source="C22" target="C24">
      <data key="provenance">['cs2023', 'inferred']</data>
    </edge>
    <edge source="C01" target="C25">
      <data key="provenance">['guide-05', 'prompt-libs']</data>
    </edge>
    <edge source="C20" target="C25">
      <data key="provenance">['guide-05', 'prompt-libs']</data>
    </edge>
    <edge source="C25" target="C26">
      <data key="provenance">['guide-05']</data>
    </edge>
    <edge source="C20" target="C27">
      <data key="provenance">['guide-01', 'guide-06']</data>
    </edge>
    <edge source="C25" target="C28">
      <data key="provenance">['guide-06']</data>
    </edge>
    <edge source="C27" target="C28">
      <data key="provenance">['guide-06']</data>
    </edge>
    <edge source="C43" target="C28">
      <data key="provenance">['guide-06']</data>
    </edge>
    <edge source="C27" target="C29">
      <data key="provenance">['guide-06', 'iis-osint']</data>
    </edge>
    <edge source="C28" target="C30">
      <data key="provenance">['guide-06']</data>
    </edge>
    <edge source="C29" target="C30">
      <data key="provenance">['guide-06']</data>
    </edge>
    <edge source="C28" target="C31">
      <data key="provenance">['guide-06']</data>
    </edge>
    <edge source="C30" target="C31">
      <data key="provenance">['guide-06']</data>
    </edge>
    <edge source="C25" target="C32">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C18" target="C32">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C32" target="C33">
      <data key="provenance">['guide-07', 'guide-17']</data>
    </edge>
    <edge source="C32" target="C34">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C33" target="C34">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C32" target="C35">
      <data key="provenance">['guide-08']</data>
    </edge>
    <edge source="C29" target="C35">
      <data key="provenance">['guide-08']</data>
    </edge>
    <edge source="C32" target="C36">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C32" target="C37">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C36" target="C37">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C32" target="C38">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C37" target="C38">
      <data key="provenance">['guide-07']</data>
    </edge>
    <edge source="C25" target="C39">
      <data key="provenance">['guide-12', 'guide-07']</data>
    </edge>
    <edge source="C32" target="C39">
      <data key="provenance">['guide-12', 'guide-07']</data>
    </edge>
    <edge source="C33" target="C39">
      <data key="provenance">['guide-12', 'guide-07']</data>
    </edge>
    <edge source="C24" target="C40">
      <data key="provenance">['guide-14']</data>
    </edge>
    <edge source="C28" target="C40">
      <data key="provenance">['guide-14']</data>
    </edge>
    <edge source="C32" target="C40">
      <data key="provenance">['guide-14']</data>
    </edge>
    <edge source="C25" target="C41">
      <data key="provenance">['guide-13']</data>
    </edge>
    <edge source="C32" target="C41">
      <data key="provenance">['guide-13']</data>
    </edge>
    <edge source="C40" target="C41">
      <data key="provenance">['guide-13']</data>
    </edge>
    <edge source="C22" target="C42">
      <data key="provenance">['guide-11', 'guide-13']</data>
    </edge>
    <edge source="C40" target="C42">
      <data key="provenance">['guide-11', 'guide-13']</data>
    </edge>
    <edge source="C41" target="C42">
      <data key="provenance">['guide-11', 'guide-13']</data>
    </edge>
    <edge source="C47" target="C42">
      <data key="provenance">['guide-11', 'guide-13']</data>
    </edge>
    <edge source="C27" target="C43">
      <data key="provenance">['guide-06', 'guide-10', 'iis-osint']</data>
    </edge>
    <edge source="C18" target="C44">
      <data key="provenance">['guide-18', 'guide-19']</data>
    </edge>
    <edge source="C20" target="C44">
      <data key="provenance">['guide-18', 'guide-19']</data>
    </edge>
    <edge source="C28" target="C45">
      <data key="provenance">['guide-15', 'guide-16']</data>
    </edge>
    <edge source="C32" target="C45">
      <data key="provenance">['guide-15', 'guide-16']</data>
    </edge>
    <edge source="C40" target="C45">
      <data key="provenance">['guide-15', 'guide-16']</data>
    </edge>
    <edge source="C15" target="C46">
      <data key="provenance">['guide-03']</data>
    </edge>
    <edge source="C08" target="C46">
      <data key="provenance">['guide-03']</data>
    </edge>
    <edge source="C01" target="C47">
      <data key="provenance">['guide-02']</data>
    </edge>
    <edge source="C20" target="C47">
      <data key="provenance">['guide-02']</data>
    </edge>
    <edge source="C24" target="C47">
      <data key="provenance">['guide-02']</data>
    </edge>
  </graph>
</graphml>
"#, r#"[]"#),
        ];
        let mut json_ok = 0usize;
        let mut text_ok = 0usize;
        let mut none_ok = 0usize;
        for (pkg, gid, entry_s, kind, want_s, errs_s) in cases {
            let entry: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(entry_s).unwrap(),
            )
            .unwrap();
            let (got, errs) = dispatch(&root, &entry);
            let want_errs: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(errs_s).unwrap(),
            )
            .unwrap();
            if want_s.is_empty() {
                match got {
                    None => none_ok += 1,
                    Some(g) => panic!(
                        "{} {}：真源返回 None，本线给了 {:?}",
                        pkg, gid, g
                    ),
                }
                let want_list: Vec<String> =
                    match want_errs { Json::Array(a) => a.iter().map(crate::pyval::plain_str).collect(), _ => Vec::new() };
                assert_eq!(errs, want_list, "{} {} 的 issue 列表", pkg, gid);
                continue;
            }
            match got {
                None => panic!("{} {}：真源有值、本线返回 None（issue {}）", pkg, gid, errs.join("；")),
                Some(g) => match (kind, g) {
                    (&"text", GenOut::Text(t)) => {
                        assert_eq!(&t, want_s, "{} {} 的文本", pkg, gid);
                        text_ok += 1;
                    }
                    (&"json", GenOut::Json(v)) => {
                        assert_eq!(&v.dumps_default(), want_s, "{} {} 的 JSON", pkg, gid);
                        json_ok += 1;
                    }
                    (k, other) => panic!("{} {}：期望 {} 实得 {:?}", pkg, gid, k, other),
                },
            }
        }
        eprintln!(
            "生成器对账：JSON {} / 文本 {} / 中性 None {}",
            json_ok, text_ok, none_ok
        );
        assert!(json_ok > 0 && text_ok > 0, "两类都要真跑到，否则判据是空转");
    }

    /// 登记表齐全：13 个 id 全部在册且 `dispatch` 都认得（不得靠 `other` 兜底）。
    #[test]
    fn generator_registry_is_complete() {
        assert_eq!(GENERATOR_IDS.len(), 13);
        for gid in GENERATOR_IDS {
            let entry = Json::Object(vec![(
                "recompute".to_string(),
                Json::Object(vec![("id".to_string(), Json::Str(gid.to_string()))]),
            )]);
            let (_out, errs) = dispatch(&crate::testutil::repo_root(), &entry);
            for e in &errs {
                assert!(!e.starts_with("未登记生成器"), "{} 未被 dispatch 认领", gid);
            }
        }
    }
    // <<< GENERATED
}
