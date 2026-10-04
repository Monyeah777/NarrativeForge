//! 协议件子集校验（`schema_lint` / check28）—— 与真源 `desktop/src/core/schema_lint.py` 对账。
//!
//! 真源是**自实现的 JSON-Schema 子集校验器**：`SUBSET_ALLOWED_KEYS` 之外的关字一律 FAIL
//! （防止「校验器声称子集却静默忽略语义」的假绿），再用它校五张面——模块契约围栏 /
//! registry 投影 / 管线声明 / community 协议声明 / 资产台账。
//!
//! **未移植的近似（如实标注）**：真源在读取/解析失败时把**底层异常文本**拼进 issue；
//! 本线的错误措辞是自拟的。正常仓库上不会走到这两条分支（真源当前 0 issues）。
//! 真源的 `_csc.yaml is None`（PyYAML 缺席）分支在本线不存在——`miniyaml` 恒在场。

use crate::jsonread;
use crate::miniyaml;
use crate::pyfloat;
use crate::pyjson::Json;
use crate::pyval::{get, plain_str, py_repr, py_str};
use std::path::Path;

pub const SCHEMA_DIR: &str = "protocol/schema";
pub const DIALECT: &str = "https://json-schema.org/draft/2020-12/schema";
const PLACEHOLDER: &str = "\u{0}NFDOC\u{0}";

/// 校验器已实现的关键字白名单（子集边界显式化）。
pub const SUBSET_ALLOWED_KEYS: [&str; 16] = [
    "$schema",
    "$id",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "propertyNames",
    "additionalProperties",
    "items",
    "enum",
    "pattern",
    "minLength",
    "minimum",
    "minItems",
    "maxItems",
];

/// 真源 `type(instance).__name__` —— 进错误消息，必须逐字一致。
fn py_type_name(j: &Json) -> &'static str {
    match j {
        Json::Object(_) => "dict",
        Json::Array(_) => "list",
        Json::Str(_) => "str",
        Json::Int(_) => "int",
        Json::Float(_) => "float",
        Json::Bool(_) => "bool",
        Json::Null => "NoneType",
    }
}

/// 真源 `subset_key_violations`：递归扫描未实现的关键字。
pub fn subset_key_violations(schema: &Json, path: &str) -> Vec<String> {
    let Json::Object(pairs) = schema else { return Vec::new() };
    let mut out: Vec<String> = pairs
        .iter()
        .filter(|(k, _)| !SUBSET_ALLOWED_KEYS.contains(&k.as_str()))
        .map(|(k, _)| {
            format!(
                "{}: 使用了校验器未实现的关键字 {}（JSON-schema 子集越界——check28 无法兑现该语义；须扩展校验器或删除该关键字）",
                path, k
            )
        })
        .collect();
    if let Some(Json::Object(props)) = get(schema, "properties") {
        for (pname, sub) in props {
            out.extend(subset_key_violations(sub, &format!("{}/properties/{}", path, pname)));
        }
    }
    if let Some(items) = get(schema, "items") {
        if matches!(items, Json::Object(_)) {
            out.extend(subset_key_violations(items, &format!("{}/items", path)));
        }
    }
    if let Some(Json::Object(extra)) = get(schema, "additionalProperties") {
        let extra = Json::Object(extra.clone());
        out.extend(subset_key_violations(&extra, &format!("{}/additionalProperties", path)));
    }
    if let Some(pn) = get(schema, "propertyNames") {
        if matches!(pn, Json::Object(_)) {
            out.extend(subset_key_violations(pn, &format!("{}/propertyNames", path)));
        }
    }
    out
}

/// 已编译正则的缓存 —— **性能关键**。
///
/// 实测教训：`pattern` 分支起初每次校验都 `Regex::new(pat)`，而 Python 的 `re` 自带编译缓存
/// （512 条）⇒ 同一批 schema 在 248 份件上反复校验时，Rust 侧把编译成本乘了几千倍，
/// 整条 `schema-lint` 慢到 Python 的 **3 倍**（606 ms vs 200 ms）。修好后才回到应有水平。
fn cached_regex(pat: &str) -> Option<regex::Regex> {
    thread_local! {
        static CACHE: std::cell::RefCell<std::collections::HashMap<String, Option<regex::Regex>>> =
            std::cell::RefCell::new(std::collections::HashMap::new());
    }
    CACHE.with(|c| {
        let mut m = c.borrow_mut();
        m.entry(pat.to_string())
            .or_insert_with(|| regex::Regex::new(pat).ok())
            .clone()
    })
}

/// 真源 `subset_validate`：JSON-schema 子集校验（空 = 通过）。
pub fn subset_validate(instance: &Json, schema: &Json, path: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    if matches!(schema, Json::Null) {
        return out;
    }
    let Json::Object(_) = schema else {
        return vec![format!("{}: schema 段非对象", path)];
    };
    let stype = get(schema, "type");
    match stype {
        None => return out,
        Some(Json::Null) => return out,
        _ => {}
    }
    let name = plain_str(stype.unwrap());
    match name.as_str() {
        "object" => {
            let Json::Object(inst) = instance else {
                return vec![format!("{}: 应为 object，实为 {}", path, py_type_name(instance))];
            };
            let props: Vec<(String, Json)> = match get(schema, "properties") {
                Some(Json::Object(p)) => p.clone(),
                _ => Vec::new(),
            };
            for req in crate::pyval::arr_items(get(schema, "required")) {
                let key = plain_str(req);
                if !inst.iter().any(|(k, _)| *k == key) {
                    out.push(format!("{}: 缺必填字段 {}", path, key));
                }
            }
            if let Some(pn) = get(schema, "propertyNames") {
                if matches!(pn, Json::Object(_)) {
                    for (key, _) in inst {
                        out.extend(subset_validate(
                            &Json::Str(key.clone()),
                            pn,
                            &format!("{}/{}（键名）", path, key),
                        ));
                    }
                }
            }
            for (key, sub) in &props {
                if let Some((_, v)) = inst.iter().find(|(k, _)| k == key) {
                    out.extend(subset_validate(v, sub, &format!("{}/{}", path, key)));
                }
            }
            let extra = get(schema, "additionalProperties");
            for (key, v) in inst {
                if props.iter().any(|(k, _)| k == key) {
                    continue;
                }
                match extra {
                    Some(Json::Bool(false)) => out.push(format!(
                        "{}: 未知字段 {}（不在该 schema 词表内）",
                        path, key
                    )),
                    Some(e) if matches!(e, Json::Object(_)) => {
                        out.extend(subset_validate(v, e, &format!("{}/{}", path, key)));
                    }
                    _ => {}
                }
            }
            out
        }
        "array" => {
            let Json::Array(items) = instance else {
                return vec![format!("{}: 应为 array，实为 {}", path, py_type_name(instance))];
            };
            if let Some(m) = get(schema, "minItems") {
                if let Some(n) = as_int(m) {
                    if (items.len() as i64) < n {
                        out.push(format!("{}: 数组长度 {} < minItems {}", path, items.len(), n));
                    }
                }
            }
            if let Some(m) = get(schema, "maxItems") {
                if let Some(n) = as_int(m) {
                    if (items.len() as i64) > n {
                        out.push(format!("{}: 数组长度 {} > maxItems {}", path, items.len(), n));
                    }
                }
            }
            let sub = get(schema, "items");
            for (i, item) in items.iter().enumerate() {
                if let Some(s) = sub {
                    out.extend(subset_validate(item, s, &format!("{}[{}]", path, i)));
                } else {
                    out.extend(subset_validate(item, &Json::Null, &format!("{}[{}]", path, i)));
                }
            }
            out
        }
        "string" => {
            let Json::Str(s) = instance else {
                return vec![format!("{}: 应为 string，实为 {}", path, py_type_name(instance))];
            };
            if let Some(m) = get(schema, "minLength") {
                if let Some(n) = as_int(m) {
                    let len = s.chars().count() as i64;
                    if len < n {
                        out.push(format!("{}: 字符串过短 {} < minLength {}", path, len, n));
                    }
                }
            }
            if let Some(Json::Array(en)) = get(schema, "enum") {
                if !en.iter().any(|e| e == instance) {
                    out.push(format!(
                        "{}: 值 {} 不在枚举 {}",
                        path,
                        py_repr(instance),
                        py_repr(&Json::Array(en.clone()))
                    ));
                }
            }
            if let Some(Json::Str(pat)) = get(schema, "pattern") {
                match cached_regex(pat) {
                    Some(re) => {
                        if !re.is_match(s) {
                            out.push(format!(
                                "{}: 值 {} 不匹配 pattern {}",
                                path,
                                py_repr(instance),
                                pat
                            ));
                        }
                    }
                    None => out.push(format!(
                        "{}: 值 {} 不匹配 pattern {}",
                        path,
                        py_repr(instance),
                        pat
                    )),
                }
            }
            out
        }
        "integer" => {
            let ok = matches!(instance, Json::Int(_));
            if !ok {
                return vec![format!(
                    "{}: 应为 integer，实为 {}",
                    path,
                    py_type_name(instance)
                )];
            }
            if let Some(m) = get(schema, "minimum") {
                if let (Some(v), Some(n)) = (as_f64(instance), as_f64(m)) {
                    if v < n {
                        out.push(format!("{}: 值 {} < minimum {}", path, plain_str(instance), plain_str(m)));
                    }
                }
            }
            out
        }
        "number" => {
            let ok = matches!(instance, Json::Int(_) | Json::Float(_));
            if !ok {
                return vec![format!("{}: 应为 number，实为 {}", path, py_type_name(instance))];
            }
            if let Some(m) = get(schema, "minimum") {
                if let (Some(v), Some(n)) = (as_f64(instance), as_f64(m)) {
                    if v < n {
                        out.push(format!("{}: 值 {} < minimum {}", path, plain_str(instance), plain_str(m)));
                    }
                }
            }
            out
        }
        "boolean" => {
            if !matches!(instance, Json::Bool(_)) {
                return vec![format!(
                    "{}: 应为 boolean，实为 {}",
                    path,
                    py_type_name(instance)
                )];
            }
            out
        }
        _ => vec![format!(
            "{}: 校验器不支持的 type {}",
            path,
            py_repr(stype.unwrap())
        )],
    }
}

fn as_int(j: &Json) -> Option<i64> {
    match j {
        Json::Int(i) => Some(*i),
        _ => None,
    }
}

fn as_f64(j: &Json) -> Option<f64> {
    match j {
        Json::Int(i) => Some(*i as f64),
        Json::Float(f) => Some(*f),
        _ => None,
    }
}

/// 真源 `check_schema_files` → `(issues, schemas)`。
pub fn check_schema_files(root: &Path) -> (Vec<String>, Vec<Json>) {
    let mut issues: Vec<String> = Vec::new();
    let mut schemas: Vec<Json> = Vec::new();
    if !root.join(SCHEMA_DIR).is_dir() {
        return (vec![format!("{}/ 缺失（协议层 IDL 未落盘）", SCHEMA_DIR)], schemas);
    }
    for rel in crate::glob::expand(root, "protocol/schema/*.json") {
        let name = rel.rsplit('/').next().unwrap_or(&rel).to_string();
        let Some(data) = jsonread::read_file(root, &rel) else {
            issues.push(format!("{}: JSON 解析失败（本线不复制 Python 异常文本）", name));
            continue;
        };
        if !matches!(data, Json::Object(_)) {
            issues.push(format!("{}: schema 顶层非对象", name));
            continue;
        }
        for key in ["$id", "title", "type"] {
            if get(&data, key).is_none() {
                issues.push(format!("{}: schema 缺 {}", name, key));
            }
        }
        if py_str(get(&data, "$schema")) != DIALECT {
            issues.push(format!(
                "{}: $schema={} 与校验器实现的方言不一致（预期 {}；修复指引：改声明或先扩展校验器再改声明）",
                name,
                py_repr(get(&data, "$schema").unwrap_or(&Json::Null)),
                DIALECT
            ));
        }
        if py_str(get(&data, "type")) != "object" {
            issues.push(format!("{}: schema.type 应为 object", name));
        }
        if !matches!(get(&data, "properties"), Some(Json::Object(_))) {
            issues.push(format!("{}: schema.properties 缺失/非对象", name));
        }
        if let Some(req) = get(&data, "required") {
            if !matches!(req, Json::Array(_)) {
                issues.push(format!("{}: schema.required 非数组", name));
            }
        }
        issues.extend(subset_key_violations(&data, &name));
        schemas.push(data);
    }
    (issues, schemas)
}

/// 一张面的展开（共用子树清单缓存——见 [`discover`] 的性能注记）。
fn face(root: &Path, pats: &[&str], cache: &mut crate::glob::Cache) -> Vec<String> {
    let mut out = Vec::new();
    for p in pats {
        out.extend(cache.expand(root, p));
    }
    out
}

/// 真源 `discover` 的三张面（模式逐条展开，次序即真源次序）。
///
/// **性能**：三条模式的前缀都是 `community/`，若各走一遍文件系统，那棵最大的树要递归三遍。
/// 实测教训：不共用子树清单时 `schema-lint` 冷跑 396 ms，而真源未缓存冷算只要 142 ms。
/// 共用后一遍即可（`expand_with` 的 `trees` 按前缀记账）。
pub fn discover(
    root: &Path,
    cache: &mut crate::glob::Cache,
) -> (Vec<String>, Vec<String>, Vec<String>) {
    let module_docs = face(root, &["04_模块库/**/*.md", "community/*/modules/*.md"], cache);
    let pipeline_docs = face(root, &["03_管线库/**/*.md", "community/*/pipelines/*.md"], cache);
    let protocol_files = face(root, &["community/*/protocol.yaml"], cache);
    (module_docs, pipeline_docs, protocol_files)
}

#[derive(Default, Clone, Debug, PartialEq)]
pub struct LintStats {
    pub schema_files: usize,
    pub module_docs: usize,
    pub contract_covered: usize,
    pub pipelines: usize,
    pub protocols: usize,
    pub asset_entries: usize,
}

impl LintStats {
    /// 进 `verify_report` / CLI 的 stats 字典（键序由 JSON 出口排序）。
    pub fn to_json(&self) -> Json {
        Json::Object(vec![
            ("schema_files".to_string(), Json::Int(self.schema_files as i64)),
            ("module_docs".to_string(), Json::Int(self.module_docs as i64)),
            (
                "contract_covered".to_string(),
                Json::Int(self.contract_covered as i64),
            ),
            ("pipelines".to_string(), Json::Int(self.pipelines as i64)),
            ("protocols".to_string(), Json::Int(self.protocols as i64)),
            (
                "asset_entries".to_string(),
                Json::Int(self.asset_entries as i64),
            ),
        ])
    }
}

/// 真源 `_lint_doc_cached` 的**无缓存实现**（缓存是纯函数优化，不改语义）。
fn lint_doc(text: &str, marker: &str, schema: Option<&Json>, prefix: &str, obj_key: &str) -> Option<Vec<String>> {
    let parsed = miniyaml::fence_yaml(text, marker)?;
    let want = if obj_key.is_empty() { marker } else { obj_key };
    let obj = match get(&parsed, want) {
        Some(v) => v.clone(),
        None => parsed,
    };
    let errs = match schema {
        Some(s) => subset_validate(&obj, s, PLACEHOLDER),
        None => Vec::new(),
    };
    Some(errs.into_iter().map(|m| m.replace(PLACEHOLDER, prefix)).collect())
}

/// 真源 `_lint_obj_cached` 的**无缓存实现**。
fn lint_obj(obj: &Json, schema: Option<&Json>, prefix: &str) -> Vec<String> {
    let Some(s) = schema else { return Vec::new() };
    subset_validate(obj, s, PLACEHOLDER)
        .into_iter()
        .map(|m| m.replace(PLACEHOLDER, prefix))
        .collect()
}

fn read_text(root: &Path, rel: &str) -> Result<String, String> {
    std::fs::read_to_string(root.join(rel)).map_err(|e| e.to_string())
}

/// 真源 `scan`（＝ `_scan_impl`；派生缓存是纯函数优化，本线不实现）。
pub fn scan(root: &Path) -> (Vec<String>, LintStats) {
    let mut issues: Vec<String> = Vec::new();
    let (schema_issues, schemas) = check_schema_files(root);
    issues.extend(schema_issues);
    let by_name: Vec<(String, Json)> = schemas
        .iter()
        .filter_map(|s| get(s, "$id").map(|id| (plain_str(id).rsplit('/').next().unwrap_or("").to_string(), s.clone())))
        .collect();
    let pick = |n: &str| by_name.iter().find(|(k, _)| k == n).map(|(_, v)| v.clone());

    let mut cache = crate::glob::Cache::new();
    let (module_docs, pipeline_docs, protocol_files) = discover(root, &mut cache);
    let contract_schema = pick("contract.schema.json");
    let module_schema = pick("module.schema.json");
    let pipeline_schema = pick("pipeline.schema.json");
    let protocol_schema = pick("protocol.schema.json");
    let asset_schema = pick("asset.schema.json");

    let mut contract_covered = 0usize;
    for rel in &module_docs {
        let Ok(text) = read_text(root, rel) else {
            issues.push(format!("{}: 读取失败（本线不复制 Python 异常文本）", rel));
            continue;
        };
        let msgs = lint_doc(
            &text,
            "machine_contract",
            contract_schema.as_ref(),
            &format!("{} machine_contract", rel),
            "",
        );
        let Some(msgs) = msgs else { continue };
        contract_covered += 1;
        issues.extend(msgs);
    }

    let reg_modules: Vec<Json> = match jsonread::read_file(root, "desktop/src/core/registry.json") {
        Some(reg) => crate::pyval::arr_items(get(&reg, "modules")).into_iter().cloned().collect(),
        None => {
            issues.push("registry.json 读取/解析失败（本线不复制 Python 异常文本）".to_string());
            Vec::new()
        }
    };
    if module_schema.is_some() {
        for entry in &reg_modules {
            issues.extend(lint_obj(entry, module_schema.as_ref(), "registry.modules"));
        }
    }

    for rel in &pipeline_docs {
        let Ok(text) = read_text(root, rel) else {
            issues.push(format!("{}: 读取失败（本线不复制 Python 异常文本）", rel));
            continue;
        };
        let msgs = lint_doc(
            &text,
            "Pipeline:",
            pipeline_schema.as_ref(),
            &format!("{} Pipeline", rel),
            "Pipeline",
        );
        match msgs {
            Some(m) => issues.extend(m),
            None => issues.push(format!("{}: Pipeline yaml 缺失/解析失败", rel)),
        }
    }

    for rel in &protocol_files {
        let text = match read_text(root, rel) {
            Ok(t) => t,
            Err(_) => {
                issues.push(format!("{}: protocol.yaml 解析失败（本线不复制 Python 异常文本）", rel));
                continue;
            }
        };
        match miniyaml::parse(&text) {
            Ok(data) => issues.extend(lint_obj(&data, protocol_schema.as_ref(), rel)),
            Err(_) => {
                issues.push(format!("{}: protocol.yaml 解析失败（本线不复制 Python 异常文本）", rel))
            }
        }
    }

    let prov_entries: Vec<Json> = match jsonread::read_file(root, "05_资产库/provenance.json") {
        Some(prov) => crate::pyval::arr_items(get(&prov, "assets")).into_iter().cloned().collect(),
        None => {
            issues.push("provenance.json 读取/解析失败（本线不复制 Python 异常文本）".to_string());
            Vec::new()
        }
    };
    if asset_schema.is_some() {
        for (i, entry) in prov_entries.iter().enumerate() {
            issues.extend(lint_obj(
                entry,
                asset_schema.as_ref(),
                &format!("provenance.assets[{}]", i),
            ));
        }
    }

    (
        issues,
        LintStats {
            schema_files: schemas.len(),
            module_docs: module_docs.len(),
            contract_covered,
            pipelines: pipeline_docs.len(),
            protocols: protocol_files.len(),
            asset_entries: prov_entries.len(),
        },
    )
}

// `protocol.yaml` 是**整份** YAML（不是围栏块）——真源走 `load_yaml_cached`，本线走 `miniyaml::parse`。
// 真源语料里这些文件以 `#` 注释开头、无 `---` 前导块，故可直接整份解析。

/// 供 `nf score` 用的信号：`schema_clean` = issues 条数。
pub fn issue_count(root: &Path) -> usize {
    scan(root).0.len()
}

/// 浮点辅助（供未来扩展；当前 stats 无浮点）。
#[allow(dead_code)]
fn round2(x: f64) -> f64 {
    pyfloat::round_to(x, 2)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::jsonread;

    fn j(v: serde_json::Value) -> Json {
        jsonread::convert(&v).unwrap()
    }

    #[test]
    fn object_required_and_additional_properties() {
        let schema = j(serde_json::json!({
            "type": "object",
            "required": ["a"],
            "properties": {"a": {"type": "string"}},
            "additionalProperties": false
        }));
        let inst = j(serde_json::json!({"a": "x", "b": 1}));
        let got = subset_validate(&inst, &schema, "p");
        assert_eq!(got.len(), 1);
        assert!(got[0].contains("未知字段 b"), "{:?}", got);
        // 缺必填
        let got2 = subset_validate(&j(serde_json::json!({"b": 1})), &schema, "p");
        assert!(got2.iter().any(|m| m.contains("缺必填字段 a")), "{:?}", got2);
    }

    #[test]
    fn type_names_match_python_type_dunder_name() {
        let schema = j(serde_json::json!({"type": "object"}));
        for (v, want) in [
            (serde_json::json!([1]), "list"),
            (serde_json::json!("s"), "str"),
            (serde_json::json!(1), "int"),
            (serde_json::json!(1.5), "float"),
            (serde_json::json!(true), "bool"),
            (serde_json::json!(null), "NoneType"),
        ] {
            let got = subset_validate(&j(v), &schema, "p");
            assert_eq!(got.len(), 1);
            assert!(got[0].ends_with(want), "期望 {} 收尾，实得 {:?}", want, got[0]);
        }
    }

    #[test]
    fn bool_is_not_integer_like_python() {
        // Python: isinstance(True, int) 为真，故真源显式排 bool
        let schema = j(serde_json::json!({"type": "integer"}));
        let got = subset_validate(&j(serde_json::json!(true)), &schema, "p");
        assert_eq!(got.len(), 1);
        assert!(got[0].contains("实为 bool"), "{:?}", got);
    }

    #[test]
    fn enum_and_pattern_messages_use_python_repr() {
        let schema = j(serde_json::json!({"type": "string", "enum": ["a", "b"]}));
        let got = subset_validate(&j(serde_json::json!("z")), &schema, "p");
        assert_eq!(got.len(), 1);
        // Python: 值 'z' 不在枚举 ['a', 'b']
        assert!(got[0].contains("值 'z' 不在枚举 ['a', 'b']"), "{:?}", got);
    }

    #[test]
    fn subset_key_violations_flags_unimplemented_keywords() {
        let schema = j(serde_json::json!({"type": "object", "oneOf": [{"type": "string"}]}));
        let got = subset_key_violations(&schema, "s");
        assert_eq!(got.len(), 1);
        assert!(got[0].contains("oneOf"), "{:?}", got);
    }

    #[test]
    fn unsupported_type_is_reported_not_silently_ignored() {
        let schema = j(serde_json::json!({"type": "null"}));
        let got = subset_validate(&j(serde_json::json!(1)), &schema, "p");
        assert_eq!(got.len(), 1);
        assert!(got[0].contains("校验器不支持的 type"), "{:?}", got);
    }
}
