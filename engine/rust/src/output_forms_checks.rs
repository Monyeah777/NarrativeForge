//! `output_forms` 的**格式结构校验器**（真源 `_check_*` 一族 + `_FORM_CHECK` 分派表）。
//!
//! 拆成独立件只为可读：口径与真源逐条对应，判据面不拆。
//!
//! **两个解析器是本线自带的**（真源用标准库，本线不用 Python 运行时）：
//! `jsonmini`（`json.loads` 口径 + 重复键）、`toml` crate（`tomllib` 口径）。
//! 越出子集即 fail-closed。

use crate::output_forms::{read_text, rel_path};
use crate::pyjson::Json;
use crate::pyval;
use std::path::Path;

fn obj_get<'a>(v: &'a Json, k: &str) -> Option<&'a Json> {
    match v {
        Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv),
        _ => None,
    }
}

fn as_str(v: Option<&Json>) -> String {
    match v {
        None | Some(Json::Null) => String::new(),
        Some(x) => pyval::plain_str(x),
    }
}

/// 真源 `_read_json` 的**判据面**版本（用 `jsonmini`，与 `json.loads` 同接受面）。
pub fn read_json(root: &Path, rel: &str) -> (Json, String) {
    let p = rel_path(root, rel);
    match std::fs::read(&p) {
        Err(e) => (Json::Null, format!("不可读：{}", e)),
        Ok(b) => {
            let text = String::from_utf8_lossy(&b).into_owned();
            match crate::jsonmini::parse(&text) {
                Ok(parsed) => (parsed.value, String::new()),
                Err(e) => (Json::Null, format!("JSON 解析失败：{}", e)),
            }
        }
    }
}

/// 真源 `_check_json`（含**重复键**判据——`serde_json` 会静默覆盖，故走 `jsonmini`）。
pub fn check_json(root: &Path, rel: &str) -> Vec<String> {
    let p = rel_path(root, rel);
    let raw = std::fs::read(&p)
        .map(|b| String::from_utf8_lossy(&b).into_owned())
        .unwrap_or_default();
    match crate::jsonmini::parse(&raw) {
        Err(e) => vec![format!("JSON 不可解析：{}", e)],
        Ok(parsed) => {
            let mut uniq: Vec<String> = parsed.dups.clone();
            uniq.sort();
            uniq.dedup();
            uniq.into_iter().map(|d| format!("JSON 重复键：{}", d)).collect()
        }
    }
}

/// 真源 `_check_jsonl`。
pub fn check_jsonl(root: &Path, rel: &str) -> Vec<String> {
    let mut issues: Vec<String> = Vec::new();
    let text = read_text(root, rel);
    for (i, line) in text.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        if let Err(e) = crate::jsonmini::parse(line) {
            issues.push(format!("第 {} 行非 JSON：{}", i + 1, e));
        }
    }
    issues
}

/// 真源 `_check_csv`。
pub fn check_csv(root: &Path, rel: &str) -> Vec<String> {
    let text = read_text(root, rel);
    if text.contains('\u{0}') {
        return vec!["含 NUL 字节（非文本 CSV）".to_string()];
    }
    let rows: Vec<Vec<String>> = crate::asset_contract::csv_rows(&text)
        .into_iter()
        .filter(|r| !r.is_empty())
        .collect();
    if rows.is_empty() {
        return vec!["空表".to_string()];
    }
    let width = rows[0].len();
    let mut issues: Vec<String> = if width == 0 { vec!["表头为空".to_string()] } else { Vec::new() };
    for (i, r) in rows.iter().enumerate().skip(1) {
        if r.len() != width {
            issues.push(format!("第 {} 行字段数 {} ≠ 表头 {}", i + 1, r.len(), width));
        }
    }
    let mut hdr = rows[0].clone();
    hdr.sort();
    hdr.dedup();
    if hdr.len() != width {
        issues.push("表头有重名列".to_string());
    }
    issues
}

/// 真源 `_check_markdown`。
pub fn check_markdown(root: &Path, rel: &str) -> Vec<String> {
    let text = read_text(root, rel);
    let mut issues: Vec<String> = Vec::new();
    if text.trim().is_empty() {
        issues.push("空档".to_string());
    }
    if text.matches("```").count() % 2 == 1 {
        issues.push("代码围栏未闭合（``` 奇数个）".to_string());
    }
    issues
}

/// 真源 `_check_toml`（用 `toml` crate，对 `tomllib`）。
pub fn check_toml(root: &Path, rel: &str) -> Vec<String> {
    let text = read_text(root, rel);
    match toml::from_str::<toml::Value>(&text) {
        Ok(_) => Vec::new(),
        Err(e) => vec![format!("TOML 不可解析：{}", e)],
    }
}

/// 真源 `_check_yaml`（**收窄子集**良构判定：Tab 缩进 + 非映射项）。
pub fn check_yaml(root: &Path, rel: &str) -> Vec<String> {
    let text = read_text(root, rel);
    let mut issues: Vec<String> = Vec::new();
    for (i, line) in text.lines().enumerate() {
        let indent_len = line.len() - line.trim_start().len();
        if line[..indent_len].contains('\t') {
            issues.push(format!("第 {} 行用 Tab 缩进（YAML 禁 Tab）", i + 1));
        }
        let stripped = line.trim();
        if stripped.starts_with("- ") || stripped.is_empty() || stripped.starts_with('#') {
            continue;
        }
        if !line.contains(':') {
            let head: String = stripped.chars().take(40).collect();
            issues.push(format!(
                "第 {} 行非映射项（收窄子集要求 key: value）：{}",
                i + 1,
                head
            ));
        }
    }
    issues
}

/// 真源 `_check_vega_lite`。
pub fn check_vega_lite(root: &Path, rel: &str) -> Vec<String> {
    let (data, err) = read_json(root, rel);
    if !err.is_empty() {
        return vec![err];
    }
    let mut issues: Vec<String> = Vec::new();
    if !as_str(obj_get(&data, "$schema")).contains("vega-lite") {
        issues.push("缺 $schema（应为 vega-lite v5）".to_string());
    }
    let body_keys = ["mark", "layer", "hconcat", "vconcat", "concat", "facet", "spec", "repeat"];
    if !body_keys.iter().any(|k| obj_get(&data, k).is_some()) {
        issues.push("缺 mark/layer 等绘图主体".to_string());
    }
    if obj_get(&data, "data").is_none() {
        issues.push("缺 data（图不能没有数据源）".to_string());
    }
    match obj_get(&data, "encoding") {
        Some(Json::Object(enc)) => {
            for (ch, spec) in enc {
                if !matches!(spec, Json::Object(_)) {
                    issues.push(format!("encoding.{} 非对象", ch));
                    continue;
                }
                let ch_keys = ["field", "aggregate", "value", "datum", "timeUnit", "bin"];
                if !ch_keys.iter().any(|k| obj_get(spec, k).is_some()) {
                    issues.push(format!("encoding.{} 无 field/aggregate/value（通道未绑定）", ch));
                }
            }
        }
        Some(Json::Null) | None => {}
        _ => issues.push("encoding 非对象".to_string()),
    }
    issues
}

const MERMAID_KINDS: [&str; 10] = [
    "graph",
    "flowchart",
    "sequencediagram",
    "classdiagram",
    "erdiagram",
    "statediagram",
    "gantt",
    "pie",
    "journey",
    "mindmap",
];

/// 真源 `_check_mermaid`。
pub fn check_mermaid(root: &Path, rel: &str) -> Vec<String> {
    let text = read_text(root, rel);
    let lines: Vec<String> = text.lines().map(|l| l.trim_end().to_string()).collect();
    let body: Vec<&String> = lines
        .iter()
        .filter(|l| !l.trim().is_empty() && !l.trim().starts_with("%%"))
        .collect();
    if body.is_empty() {
        return vec!["空图".to_string()];
    }
    let head = body[0].trim().to_lowercase();
    if !MERMAID_KINDS.iter().any(|k| head.starts_with(k)) {
        let head40: String = body[0].trim().chars().take(40).collect();
        return vec![format!("首行非已知图种：{}", pyval::py_repr(&Json::Str(head40)))];
    }
    Vec::new()
}

/// 真源 `_check_dot`。
pub fn check_dot(root: &Path, rel: &str) -> Vec<String> {
    let text = read_text(root, rel);
    let mut issues: Vec<String> = Vec::new();
    let re = regex::Regex::new(r"(?m)^\s*(strict\s+)?(di)?graph\b").expect("固定合法");
    if !re.is_match(&text) {
        issues.push("缺 digraph/graph 头".to_string());
    }
    let open = text.matches('{').count();
    let close = text.matches('}').count();
    if open != close {
        issues.push(format!("花括号不配对（{{ {} / }} {}）", open, close));
    }
    issues
}

/// 真源 `_check_quant_metrics`：**宣称的引擎必须真实存在**（宣称≠实现）。
pub fn check_quant_metrics(root: &Path, rel: &str) -> Vec<String> {
    let mut issues = check_json(root, rel);
    let (data, err) = read_json(root, rel);
    if !err.is_empty() || !matches!(data, Json::Object(_)) {
        if !err.is_empty() {
            issues.push(err);
        }
        return issues;
    }
    let entries: Vec<Json> = match obj_get(&data, "metrics") {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    };
    let declared: Vec<Json> = match obj_get(&data, "declared_only") {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    };
    for m in entries.iter().chain(declared.iter()) {
        if !matches!(m, Json::Object(_)) {
            issues.push(format!("条目非对象：{}", pyval::py_repr(m)));
            continue;
        }
        let mid = match obj_get(m, "id") {
            Some(v) if pyval::py_truthy(v) => pyval::plain_str(v),
            _ => "?".to_string(),
        };
        let eng = as_str(obj_get(m, "engine"));
        if !eng.is_empty() {
            let (modname, fnname) = match eng.split_once(':') {
                Some((a, b)) => (a.to_string(), b.to_string()),
                None => (eng.clone(), String::new()),
            };
            if modname != "quant_metrics"
                || !crate::output_tables::QUANT_METRICS_NAMES.contains(&fnname.as_str())
            {
                issues.push(format!(
                    "{}: 宣称 engine={}，但 core/quant_metrics 无该实现（宣称≠实现）",
                    mid, eng
                ));
            }
        }
        if as_str(obj_get(m, "verifiable")) == "T4" && eng.is_empty() {
            issues.push(format!("{}: 标 T4（可复算）却无 engine", mid));
        }
        let params: Vec<String> = match obj_get(m, "required_params") {
            Some(Json::Array(a)) => a.iter().map(pyval::plain_str).collect(),
            _ => Vec::new(),
        };
        if pyval::py_truthy(&obj_get(m, "annual_factor_required").cloned().unwrap_or(Json::Null))
            && !params.iter().any(|p| p == "annual_factor")
        {
            issues.push(format!("{}: 需年化因子却未列入 required_params（口径四要素不全）", mid));
        }
    }
    let names: Vec<String> = entries
        .iter()
        .map(|m| match obj_get(m, "id") {
            Some(v) => pyval::plain_str(v),
            None => pyval::py_str(None),
        })
        .collect();
    let mut expected: Vec<String> = match obj_get(&data, "annual_factors") {
        Some(Json::Object(o)) => o.iter().map(|(k, _)| k.clone()).collect(),
        _ => Vec::new(),
    };
    expected.sort();
    let mut want = vec!["daily".to_string(), "monthly".to_string(), "weekly".to_string()];
    want.sort();
    if expected != want {
        issues.push(format!(
            "annual_factors 键集应为 daily/weekly/monthly，实为 {}",
            pyval::py_repr_list(&expected.iter().map(|s| Json::Str(s.clone())).collect::<Vec<_>>())
        ));
    }
    let mut uniq = names.clone();
    uniq.sort();
    uniq.dedup();
    if uniq.len() != entries.len() {
        issues.push("metrics 存在重复 id".to_string());
    }
    issues
}

/// 真源 `_check_domain_spec`。
pub fn check_domain_spec(root: &Path, rel: &str) -> Vec<String> {
    let mut issues = check_json(root, rel);
    let (data, err) = read_json(root, rel);
    if !err.is_empty() || !matches!(data, Json::Object(_)) {
        if !err.is_empty() {
            issues.push(err);
        }
        return issues;
    }
    let code = as_str(obj_get(&data, "code"));
    let subs: Vec<Json> = match obj_get(&data, "subdivisions") {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    };
    if subs.len() != 12 {
        issues.push(format!("细分条目应为 12 条，实为 {}", subs.len()));
    }
    for (i, s) in subs.iter().enumerate() {
        let want = format!("{}-{:02}", code, i + 1);
        let got = obj_get(s, "id").cloned().unwrap_or(Json::Null);
        if !pyval::py_eq(&got, &Json::Str(want.clone())) {
            issues.push(format!(
                "第 {} 条 id 应为 {}，实为 {}",
                i + 1,
                want,
                pyval::py_repr(&got)
            ));
        }
        let anchor = as_str(obj_get(s, "anchor"));
        if !anchor.starts_with("http://") && !anchor.starts_with("https://") {
            issues.push(format!("{} 锚非绝对 URL", pyval::py_str(obj_get(s, "id"))));
        }
        let status = match obj_get(s, "anchor_status") {
            Some(Json::Null) | None => 0,
            Some(v) => pyval::py_int_or(Some(v), 0),
        };
        if status == 0 {
            issues.push(format!(
                "{} 锚缺可达性实测值（不得假装可达：探不到记 0 并在锚表注明）",
                pyval::py_str(obj_get(s, "id"))
            ));
        }
    }
    issues
}

/// 真源 `_check_domain_report`。
pub fn check_domain_report(root: &Path, rel: &str) -> Vec<String> {
    let mut issues = check_json(root, rel);
    let (data, err) = read_json(root, rel);
    if !err.is_empty() || !matches!(data, Json::Object(_)) {
        if !err.is_empty() {
            issues.push(err);
        }
        return issues;
    }
    let fam = as_str(obj_get(&data, "family"));
    if !crate::output_tables::DOMAIN_FAMILIES.contains(&fam.as_str()) {
        issues.push(format!(
            "度量族未在本仓引擎登记：{}（不得宣称可复算）",
            pyval::py_repr(&Json::Str(fam.clone()))
        ));
    }
    let metrics = obj_get(&data, "metrics").cloned().unwrap_or(Json::Object(vec![]));
    if as_str(obj_get(&metrics, "family")) != fam {
        issues.push("metrics.family 与报告 family 不一致".to_string());
    }
    let rows = match obj_get(&data, "sample_rows") {
        Some(Json::Null) | None => 0,
        Some(v) => pyval::py_int_or(Some(v), 0),
    };
    if rows < 1 {
        issues.push("样例规模为 0（无样例即无口径值）".to_string());
    }
    issues
}

/// 真源 `_FORM_CHECK` 分派：按形态取校验器并跑。
///
/// `combo-cert` 走 `_check_combo_cert`：**先跑 JSON 形态校验**，再叠 schema + 五不变量 +
/// 「摘要与实时复算一致」（真源同序：`issues = _check_json(root, rel)` 之后才判证书）。
pub fn form_check(form: &str, root: &Path, rel: &str) -> Option<Vec<String>> {
    let r: Vec<String> = match form {
        "json" | "json-schema" | "vega" | "json-graph-format" | "performance-report"
        | "concept-closure" | "system-card" => check_json(root, rel),
        "jsonl" => check_jsonl(root, rel),
        "csv" => check_csv(root, rel),
        "xml" | "svg" => crate::output_forms::check_xml(root, rel),
        "markdown" => check_markdown(root, rel),
        "toml" => check_toml(root, rel),
        "yaml" => check_yaml(root, rel),
        "vega-lite" => check_vega_lite(root, rel),
        "mermaid" => check_mermaid(root, rel),
        "graphviz-dot" => check_dot(root, rel),
        "graphml" => crate::output_forms::check_graphml(root, rel),
        "quant-metrics" => check_quant_metrics(root, rel),
        "domain-spec" => check_domain_spec(root, rel),
        "domain-report" => check_domain_report(root, rel),
        "combo-cert" => {
            crate::output_forms_gen::check_combo_cert(root, rel, check_json(root, rel))
        }
        _ => return None,
    };
    Some(r)
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_output_forms_checks.py（勿手改；重跑生成器覆盖本段）
    /// ===== ① 真语料逐件（按 `detect` 选校验器，与真源 `_FORM_CHECK` 同款调用）=====
    ///
    /// 覆盖 outputs 下 1156 件（报 issue 的 0 件）。**含 `combo-cert`**（0 件）——
    /// 它对应的 `_check_combo_cert` 属 `pack_combo` 面，本轮未移植，`form_check` 对它返回
    /// `None`（**不静默当通过**）。
    #[test]
    fn output_forms_checkers_match_truth_source_over_corpus() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &str, &[&str])] = &[
        (r#"community/AI人力资源与招聘域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI人力资源与招聘域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI保险域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI保险域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI保险域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI保险域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI保险域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI保险域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI保险域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI保险域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI保险域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI保险域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI保险域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI农业域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI农业域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI农业域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI农业域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI农业域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI农业域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI农业域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI农业域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI农业域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI农业域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI农业域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI制药与生物域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI制药与生物域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI制药与生物域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI制药与生物域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI制药与生物域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI制药与生物域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI制药与生物域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI制药与生物域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI制药与生物域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI制药与生物域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI制药与生物域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI制造业域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI制造业域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI制造业域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI制造业域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI制造业域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI制造业域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI制造业域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI制造业域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI制造业域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI制造业域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI制造业域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI医疗健康域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI医疗健康域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI医疗健康域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI医疗健康域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI医疗健康域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI医疗健康域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI医疗健康域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI医疗健康域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI医疗健康域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI医疗健康域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI医疗健康域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI政务与公共事务域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI教育域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI教育域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI教育域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI教育域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI教育域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI教育域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI教育域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI教育域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI教育域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI教育域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI教育域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI法律与合规域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI法律与合规域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI法律与合规域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI法律与合规域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI法律与合规域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI法律与合规域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI法律与合规域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI法律与合规域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI法律与合规域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI法律与合规域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI法律与合规域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI系统域包/outputs/CONCEPT_CLOSURE.json"#, r#"concept-closure"#, &[]),
        (r#"community/AI系统域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI系统域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI系统域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI系统域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI系统域包/outputs/schemas/CONCEPT_CLOSURE.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI系统域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI能源与电力域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI能源与电力域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI能源与电力域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI能源与电力域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI能源与电力域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI能源与电力域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI能源与电力域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI能源与电力域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI能源与电力域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI能源与电力域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI能源与电力域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI金融投研与风控域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/AI食品与餐饮域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/三维与世界模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/三维与世界模型域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/三维与世界模型域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/三维与世界模型域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/三维与世界模型域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/三维与世界模型域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/三维与世界模型域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/三维与世界模型域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/三维与世界模型域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/三维与世界模型域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/三维与世界模型域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/上下文工程与长上下文域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/世界书与设定库域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/世界书与设定库域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/世界书与设定库域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/世界书与设定库域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/世界书与设定库域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/世界书与设定库域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/世界书与设定库域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/世界书与设定库域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/世界书与设定库域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/世界书与设定库域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/世界书与设定库域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/个人助理与日常生活域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/交通与出行域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/交通与出行域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/交通与出行域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/交通与出行域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/交通与出行域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/交通与出行域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/交通与出行域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/交通与出行域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/交通与出行域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/交通与出行域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/交通与出行域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/产业与商业落地域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/产业与商业落地域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/产业与商业落地域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/产业与商业落地域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/产业与商业落地域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/产业与商业落地域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/产业与商业落地域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/产业与商业落地域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/产业与商业落地域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/产业与商业落地域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/产业与商业落地域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码与软件工程域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/代码与软件工程域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/代码与软件工程域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/代码与软件工程域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/代码与软件工程域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/代码与软件工程域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/代码与软件工程域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/代码与软件工程域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/代码与软件工程域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码与软件工程域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码与软件工程域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码大模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/代码大模型域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/代码大模型域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/代码大模型域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/代码大模型域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/代码大模型域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/代码大模型域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/代码大模型域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/代码大模型域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码大模型域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码大模型域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码审查与缺陷检测域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码生成与补全域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/代码生成与补全域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/代码生成与补全域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/代码生成与补全域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/代码生成与补全域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/代码生成与补全域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/代码生成与补全域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/代码生成与补全域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/代码生成与补全域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码生成与补全域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/代码生成与补全域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/企业培训与组织学习域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/传媒与新闻域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/传媒与新闻域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/传媒与新闻域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/传媒与新闻域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/传媒与新闻域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/传媒与新闻域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/传媒与新闻域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/传媒与新闻域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/传媒与新闻域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/传媒与新闻域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/传媒与新闻域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/信息抽取与结构化域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/具身智能与机器人域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/内容分发与社区运营域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/内容改写与风格迁移域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/分类与情感分析域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/分类与情感分析域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/分类与情感分析域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/分类与情感分析域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/分类与情感分析域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/分类与情感分析域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/分类与情感分析域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/分类与情感分析域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/分类与情感分析域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/分类与情感分析域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/分类与情感分析域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/参数高效微调域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/参数高效微调域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/参数高效微调域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/参数高效微调域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/参数高效微调域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/参数高效微调域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/参数高效微调域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/参数高效微调域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/参数高效微调域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/参数高效微调域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/参数高效微调域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/可观测性成本与可靠性域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/可解释性与审计域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/可解释性与审计域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/可解释性与审计域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/可解释性与审计域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/可解释性与审计域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/可解释性与审计域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/可解释性与审计域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/可解释性与审计域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/可解释性与审计域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/可解释性与审计域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/可解释性与审计域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/合成数据生成域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/合成数据生成域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/合成数据生成域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/合成数据生成域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/合成数据生成域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/合成数据生成域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/合成数据生成域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/合成数据生成域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/合成数据生成域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/合成数据生成域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/合成数据生成域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/合规与监管域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/合规与监管域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/合规与监管域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/合规与监管域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/合规与监管域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/合规与监管域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/合规与监管域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/合规与监管域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/合规与监管域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/合规与监管域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/合规与监管域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/向量库与检索管线域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与编辑域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与视觉创作域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/图像生成与视觉设计域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多智能体协同域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/多智能体协同域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/多智能体协同域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/多智能体协同域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/多智能体协同域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/多智能体协同域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/多智能体协同域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/多智能体协同域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/多智能体协同域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多智能体协同域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多智能体协同域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多模态大模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/多模态大模型域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/多模态大模型域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/多模态大模型域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/多模态大模型域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/多模态大模型域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/多模态大模型域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/多模态大模型域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/多模态大模型域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多模态大模型域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多模态大模型域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多语翻译与本地化域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/多轮对话与角色扮演域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/大语言模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/大语言模型域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/大语言模型域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/大语言模型域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/大语言模型域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/大语言模型域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/大语言模型域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/大语言模型域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/大语言模型域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/大语言模型域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/大语言模型域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/安全与对齐域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/安全与对齐域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/安全与对齐域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/安全与对齐域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/安全与对齐域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/安全与对齐域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/安全与对齐域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/安全与对齐域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/安全与对齐域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/安全与对齐域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/安全与对齐域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/对话与客服域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/对话与客服域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/对话与客服域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/对话与客服域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/对话与客服域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/对话与客服域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/对话与客服域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/对话与客服域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/对话与客服域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/对话与客服域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/对话与客服域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/对齐与偏好优化域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/嵌入与检索表示域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/平台与基础设施域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/平台与基础设施域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/平台与基础设施域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/平台与基础设施域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/平台与基础设施域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/平台与基础设施域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/平台与基础设施域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/平台与基础设施域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/平台与基础设施域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/平台与基础设施域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/平台与基础设施域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/建筑与房地产域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/建筑与房地产域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/建筑与房地产域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/建筑与房地产域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/建筑与房地产域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/建筑与房地产域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/建筑与房地产域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/建筑与房地产域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/建筑与房地产域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/建筑与房地产域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/建筑与房地产域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/开源与开发者生态域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/强化学习与决策域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/强化学习与决策域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/强化学习与决策域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/强化学习与决策域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/强化学习与决策域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/强化学习与决策域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/强化学习与决策域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/强化学习与决策域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/强化学习与决策域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/强化学习与决策域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/强化学习与决策域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推理优化与加速域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/推理优化与加速域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/推理优化与加速域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/推理优化与加速域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/推理优化与加速域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/推理优化与加速域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/推理优化与加速域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/推理优化与加速域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/推理优化与加速域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推理优化与加速域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推理优化与加速域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推理服务与部署域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/推理服务与部署域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/推理服务与部署域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/推理服务与部署域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/推理服务与部署域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/推理服务与部署域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/推理服务与部署域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/推理服务与部署域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/推理服务与部署域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推理服务与部署域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推理服务与部署域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/推荐排序与广告域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/提示工程与指令设计域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/提示工程与提示模板域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/搜索与信息聚合域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/摘要与信息压缩域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数字人与虚拟形象域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数学与形式化推理域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据分析与决策支持域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据分析与表格理解域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据标注与标注质量域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/数据采集与清洗域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文旅与酒店域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/文旅与酒店域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/文旅与酒店域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/文旅与酒店域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/文旅与酒店域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/文旅与酒店域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/文旅与酒店域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/文旅与酒店域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/文旅与酒店域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文旅与酒店域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文旅与酒店域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文本生成与创作域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/文本生成与创作域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/文本生成与创作域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/文本生成与创作域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/文本生成与创作域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/文本生成与创作域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/文本生成与创作域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/文本生成与创作域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/文本生成与创作域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文本生成与创作域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文本生成与创作域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/文档解析与版面理解域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/智能体与工作流编排域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/智能体框架与工具调用域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/机器翻译与本地化域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/模型运营与成本域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/模型运营与成本域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/模型运营与成本域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/模型运营与成本域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/模型运营与成本域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/模型运营与成本域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/模型运营与成本域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/模型运营与成本域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/模型运营与成本域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/模型运营与成本域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/模型运营与成本域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/测试与用例生成域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/测试与用例生成域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/测试与用例生成域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/测试与用例生成域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/测试与用例生成域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/测试与用例生成域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/测试与用例生成域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/测试与用例生成域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/测试与用例生成域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/测试与用例生成域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/测试与用例生成域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/游戏与互动娱乐域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/版权与知识产权域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/版权与知识产权域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/版权与知识产权域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/版权与知识产权域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/版权与知识产权域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/版权与知识产权域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/版权与知识产权域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/版权与知识产权域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/版权与知识产权域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/版权与知识产权域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/版权与知识产权域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/物流与供应链域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/物流与供应链域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/物流与供应链域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/物流与供应链域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/物流与供应链域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/物流与供应链域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/物流与供应链域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/物流与供应链域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/物流与供应链域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/物流与供应链域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/物流与供应链域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/监督微调域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/监督微调域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/监督微调域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/监督微调域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/监督微调域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/监督微调域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/监督微调域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/监督微调域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/监督微调域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/监督微调域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/监督微调域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/知识管理与检索增强域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/知识问答与检索增强域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/科研与实验域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/科研与实验域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/科研与实验域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/科研与实验域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/科研与实验域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/科研与实验域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/科研与实验域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/科研与实验域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/科研与实验域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/科研与实验域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/科研与实验域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/端侧与边缘小模型域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/红队越狱与安全测试域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-受监管行业/outputs/BORROW_INDEX.json"#, r#"json"#, &[]),
        (r#"community/组合包-受监管行业/outputs/COMBO_CERT.json"#, r#"combo-cert"#, &[]),
        (r#"community/组合包-受监管行业/outputs/DEPENDENCY.graphml"#, r#"graphml"#, &[]),
        (r#"community/组合包-受监管行业/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/组合包-受监管行业/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/组合包-受监管行业/outputs/charts/LAYER_STACK.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/组合包-受监管行业/outputs/charts/LOAD_ORDER.mmd"#, r#"mermaid"#, &[]),
        (r#"community/组合包-受监管行业/outputs/schemas/BORROW_INDEX.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-受监管行业/outputs/schemas/COMBO_CERT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-受监管行业/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-数据管线/outputs/BORROW_INDEX.json"#, r#"json"#, &[]),
        (r#"community/组合包-数据管线/outputs/COMBO_CERT.json"#, r#"combo-cert"#, &[]),
        (r#"community/组合包-数据管线/outputs/DEPENDENCY.graphml"#, r#"graphml"#, &[]),
        (r#"community/组合包-数据管线/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/组合包-数据管线/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/组合包-数据管线/outputs/charts/LAYER_STACK.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/组合包-数据管线/outputs/charts/LOAD_ORDER.mmd"#, r#"mermaid"#, &[]),
        (r#"community/组合包-数据管线/outputs/schemas/BORROW_INDEX.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-数据管线/outputs/schemas/COMBO_CERT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-数据管线/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-检索栈/outputs/BORROW_INDEX.json"#, r#"json"#, &[]),
        (r#"community/组合包-检索栈/outputs/COMBO_CERT.json"#, r#"combo-cert"#, &[]),
        (r#"community/组合包-检索栈/outputs/DEPENDENCY.graphml"#, r#"graphml"#, &[]),
        (r#"community/组合包-检索栈/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/组合包-检索栈/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/组合包-检索栈/outputs/charts/LAYER_STACK.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/组合包-检索栈/outputs/charts/LOAD_ORDER.mmd"#, r#"mermaid"#, &[]),
        (r#"community/组合包-检索栈/outputs/schemas/BORROW_INDEX.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-检索栈/outputs/schemas/COMBO_CERT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-检索栈/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/BORROW_INDEX.json"#, r#"json"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/COMBO_CERT.json"#, r#"combo-cert"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/DEPENDENCY.graphml"#, r#"graphml"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/charts/LAYER_STACK.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/charts/LOAD_ORDER.mmd"#, r#"mermaid"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/schemas/BORROW_INDEX.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/schemas/COMBO_CERT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/组合包-轻混与保险/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/编辑校对与出版域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视觉模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/视觉模型域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/视觉模型域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/视觉模型域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/视觉模型域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/视觉模型域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/视觉模型域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/视觉模型域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/视觉模型域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视觉模型域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视觉模型域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与剪辑域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与理解域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/视频生成与理解域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/视频生成与理解域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/视频生成与理解域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/视频生成与理解域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/视频生成与理解域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/视频生成与理解域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/视频生成与理解域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/视频生成与理解域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与理解域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与理解域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/视频生成与自动剪辑域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/角色扮演与角色卡域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/记忆体与个性化域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/评测与基准域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/评测与基准域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/评测与基准域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/评测与基准域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/评测与基准域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/评测与基准域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/评测与基准域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/评测与基准域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/评测与基准域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/评测与基准域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/评测与基准域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/评测基准与排行榜域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音合成与配音域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/语音合成与配音域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/语音合成与配音域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/语音合成与配音域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/语音合成与配音域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/语音合成与配音域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/语音合成与配音域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/语音合成与配音域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/语音合成与配音域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音合成与配音域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音合成与配音域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音识别与合成域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/语音识别与合成域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/语音识别与合成域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/语音识别与合成域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/语音识别与合成域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/语音识别与合成域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/语音识别与合成域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/语音识别与合成域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/语音识别与合成域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音识别与合成域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音识别与合成域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/语音转写与会议记录域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/量化金融域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/量化金融域包/outputs/PERFORMANCE_REPORT.json"#, r#"performance-report"#, &[]),
        (r#"community/量化金融域包/outputs/QUANT_METRICS.json"#, r#"quant-metrics"#, &[]),
        (r#"community/量化金融域包/outputs/charts/DECLARATION_CHAIN.mmd"#, r#"mermaid"#, &[]),
        (r#"community/量化金融域包/outputs/charts/DRAWDOWN.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/量化金融域包/outputs/charts/EQUITY_CURVE.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/量化金融域包/outputs/samples/EQUITY_CURVE.csv"#, r#"csv"#, &[]),
        (r#"community/量化金融域包/outputs/schemas/PERFORMANCE_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/量化金融域包/outputs/schemas/QUANT_METRICS.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/长文本与小说创作域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/隐私与数据治理域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/零售与电商域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/零售与电商域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/零售与电商域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/零售与电商域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/零售与电商域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/零售与电商域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/零售与电商域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/零售与电商域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/零售与电商域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/零售与电商域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/零售与电商域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/音频与音乐生成域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/音频音乐与语音域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/预测异常与风险域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/预测异常与风险域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/预测异常与风险域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/预测异常与风险域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/预测异常与风险域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/预测异常与风险域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/预测异常与风险域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/预测异常与风险域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/预测异常与风险域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/预测异常与风险域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/预测异常与风险域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/DOMAIN_SPEC.json"#, r#"domain-spec"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/INDEX.json"#, r#"json"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/REPORT.json"#, r#"domain-report"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/SYSTEM_CARD.json"#, r#"system-card"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/charts/CONCEPT_DAG.mmd"#, r#"mermaid"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/charts/METRICS.vega.json"#, r#"vega-lite"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/samples/CASES.csv"#, r#"csv"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/schemas/DOMAIN_REPORT.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/schemas/DOMAIN_SPEC.schema.json"#, r#"json-schema"#, &[]),
        (r#"community/预训练与继续预训练域包/outputs/schemas/SYSTEM_CARD.schema.json"#, r#"json-schema"#, &[]),
        ];
        for (rel, form, want) in cases {
            let got = form_check(form, &root, rel)
                .unwrap_or_else(|| panic!("{} 的形态 {} 无校验器", rel, form));
            assert_eq!(got, want.to_vec(), "{} ({}) 的校验结论", rel, form);
        }
    }

    /// ===== ② 合成用例：真语料踩不到的 JSON 分支（重复键 / 非 RFC 常量 / 语法坏）=====
    const OF_JSON_FILES: [(&str, &str); 10] = [
        (r#"bad.json"#, r#"{"a": 
"#),
        (r#"ctrl.json"#, r#"{"a": "xy"}
"#),
        (r#"dup.json"#, r#"{"a": 1, "a": 2}
"#),
        (r#"dup_nested.json"#, r#"{"o": {"k": 1, "k": 2}, "arr": [{"z": 1, "z": 2}]}
"#),
        (r#"empty.json"#, r#""#),
        (r#"extra.json"#, r#"{} {}
"#),
        (r#"nan.json"#, r#"{"v": NaN, "w": Infinity, "x": -Infinity}
"#),
        (r#"ok.json"#, r#"{"a": [1, 2.5, "s", true, null], "b": {"c": "d"}}
"#),
        (r#"scalar.json"#, r#"42
"#),
        (r#"unicode.json"#, r#"{"\u4e2d": "\ud83d\ude00"}
"#),
    ];

    #[test]
    fn output_forms_json_branches_match_truth_source() {
        let root = crate::testutil::fixture("output-forms-json-src");
        for (rel, body) in OF_JSON_FILES {
            std::fs::write(root.join(rel), body).unwrap();
        }
        let cases: &[(&str, &[&str])] = &[
        (r#"bad.json"#, &[r#"JSON 不可解析：Expecting value: line 2 column 1 (char 7)"#]),
        (r#"ctrl.json"#, &[r#"JSON 不可解析：Invalid control character at: line 1 column 9 (char 8)"#]),
        (r#"dup.json"#, &[r#"JSON 重复键：a"#]),
        (r#"dup_nested.json"#, &[r#"JSON 重复键：k"#, r#"JSON 重复键：z"#]),
        (r#"empty.json"#, &[r#"JSON 不可解析：Expecting value: line 1 column 1 (char 0)"#]),
        (r#"extra.json"#, &[r#"JSON 不可解析：Extra data: line 1 column 4 (char 3)"#]),
        (r#"nan.json"#, &[]),
        (r#"ok.json"#, &[]),
        (r#"scalar.json"#, &[]),
        (r#"unicode.json"#, &[]),
        ];
        // ⚠️ **解析失败的文本不可比**（CPython `json` vs 本线 `jsonmini`）⇒ 归一到前缀后比较。
        // 归一**不削弱判据**：某例在一侧报错、另一侧不报，归一后仍会不同（那才是真结论差）。
        let norm = |v: &[String]| -> Vec<String> {
            v.iter()
                .map(|x| match x.find("JSON 不可解析：") {
                    Some(k) => format!("{}<TEXT>", &x[..k + "JSON 不可解析：".len()]),
                    None => x.clone(),
                })
                .collect()
        };
        for (rel, want) in cases {
            assert_eq!(
                norm(&check_json(&root, rel)),
                norm(&want.iter().map(|s| s.to_string()).collect::<Vec<_>>()),
                "{} 的 JSON 结论",
                rel
            );
        }
    }
    // <<< GENERATED
}
