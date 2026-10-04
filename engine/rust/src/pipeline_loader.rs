//! 管线加载器 —— 与真源 `desktop/src/core/pipeline_loader.py` 的读面对账。
//!
//! 真源 `parse_pipeline_md` 有**两条路**：PyYAML 在场时走 `core.conformance_scan.load_yaml_cached`
//! （真 PyYAML），否则回落内置的固定缩进子集解析器（`_build_tree` / `_tree_to_dict` /
//! `_parse_scalar`）。**本机 PyYAML 在场**（实测 `csc.yaml is None → False`），故活路径是前者——
//! 本线用 [`crate::miniyaml`]（为 NF 语料写的 PyYAML 等价子集）复刻，**不移植那套兜底解析器**
//! （它只在无 PyYAML 的环境生效，移植了也没人能核）。
//!
//! ⚠️ **已知偏差（fail-closed）**：真源在围栏体 YAML **不可解析**时，PyYAML 抛 `YAMLError`
//! ⇒ 整条契约记 **ERROR**，消息里带 PyYAML 自己的英文诊断；本线 `miniyaml::parse` 失败即
//! 当作"解析不出管线"⇒ 走 `graph` 的 `ValueError` 分支（记「管线解析失败：…」）。
//! 两边**都是红的**，但消息文本不同——无法逐字复刻（那要复刻 PyYAML 的报错文本）。
//!
//! **移植面按消费者界定**：`graph` 只读 `Pipeline` 的 `id` / `name` / `structure_type` /
//! `layers[].{id,name,optional,default_modules}`；`description` / `tags` / `dependencies` /
//! `allowed_modules` 在本链上**无人读**，故不纳入（`discover_pipelines` 同理，`sweep` 不用它）。

use crate::miniyaml;
use crate::pyjson::Json;
use crate::pyval::{get, py_str};
use std::path::Path;

/// 真源 `YAML_FENCE_RE`（`re.S`）。
fn yaml_fence_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"(?s)```ya?ml\s*\n(.*?)\n```").expect("围栏正则固定合法")
    })
}

/// 真源 `PipelineLayer` 里**本链真正读到**的字段。
///
/// `name` / `optional` / `description` / `allowed_modules` 在 `sweep` 的消费面上**无人读**
/// （它们只进 `graph` 的 `steps[]` 明细，而 `steps` 不被 `sweep` 消费），故不收——
/// 收了就是"没人核的代码"。`id` 是例外：它进「模块未在仓库找到」的消息。
pub struct PipelineLayer {
    pub id: String,
    pub default_modules: Vec<String>,
}

/// 真源 `Pipeline` 里**本链真正读到**的字段（`name` / `structure_type` 只进 GraphSpec 头部，
/// 而 `sweep` 不读 GraphSpec 头部；`layers` 的 `id`/`default_modules` 才参与判决）。
pub struct Pipeline {
    pub id: String,
    pub layers: Vec<PipelineLayer>,
}

/// 真源 `_norm_module_ref`（`ref.strip()`；真源假定 str）。
fn norm_module_ref(j: &Json) -> String {
    crate::pyval::plain_str(j).trim().to_string()
}

/// 真源 `parse_pipeline_md`。失败返回 `None`。
pub fn parse_pipeline_md(text: &str) -> Option<Pipeline> {
    let body = yaml_fence_re().captures(text)?.get(1)?.as_str().to_string();
    // 真源活路径 = `_csc.load_yaml_cached(body) or {}`（真 PyYAML）；本线用 miniyaml。
    let data = match miniyaml::parse(&body) {
        Ok(d) => d,
        // `miniyaml` 解不动 ⇒ 当作"解析不出管线"（真源此处抛 YAMLError，见模块头）
        Err(_) => return None,
    };
    if !matches!(data, Json::Object(_)) {
        return None;
    }
    let pnode = match get(&data, "Pipeline") {
        Some(v) => v.clone(),
        None => data.clone(),
    };
    if !matches!(pnode, Json::Object(_)) {
        return None;
    }

    let raw_id = match get(&pnode, "id") {
        Some(v) => py_str(Some(v)),
        None => String::new(),
    };
    let pid = {
        let s = raw_id.trim().to_string();
        if s.is_empty() { "P00".to_string() } else { s }
    };
    let mut layers: Vec<PipelineLayer> = Vec::new();
    if let Some(Json::Array(lys)) = get(&pnode, "layers") {
        for ly in lys {
            if !matches!(ly, Json::Object(_)) {
                continue;
            }
            let lv = |k: &str| match get(ly, k) {
                Some(v) => py_str(Some(v)).trim().to_string(),
                None => String::new(),
            };
            let mods = |k: &str| -> Vec<String> {
                match get(ly, k) {
                    Some(Json::Array(a)) if !a.is_empty() => a.iter().map(norm_module_ref).collect(),
                    _ => Vec::new(),
                }
            };
            layers.push(PipelineLayer {
                id: lv("id"),
                default_modules: mods("default_modules"),
            });
        }
    }
    Some(Pipeline { id: pid, layers })
}

/// 真源 `load_pipeline_file`。
pub fn load_pipeline_file(path: &Path) -> Option<Pipeline> {
    if !path.exists() {
        return None;
    }
    let text = std::fs::read_to_string(path).ok()?;
    parse_pipeline_md(&text)
}
