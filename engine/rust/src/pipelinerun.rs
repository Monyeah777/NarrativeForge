//! 管线抽象执行（dry-run）—— 与真源 `desktop/src/core/pipelinerun.py` 的读面对账。
//!
//! 判据（`_c_pipeline_dryrun`）：全仓管线**跑一遍声明**，hard 缺陷为零。
//! 判决分层：**hard**= 模块在仓库找不到 / 依赖落在严格更后的层；**advisory**= 同层依赖序、
//! 跨包依赖、跨包事件（NF 的 I5 明确「最终执行顺序以注册表合并为准」，故不判死）。
//!
//! **移植面按消费者界定**：`sweep` 只读 `graph` 的 `pipeline.id` / `issues` / `notes` /
//! `stats.{notes,modules,core_base}`，故本线不构造完整 GraphSpec——`steps` / `edges` / `tokens`
//! 明细不落结构（只留计数），`stats.missing` 同样无人读故不计。`advisory_report` /
//! `verify_advisory` 是台账写面、`discover_pipelines` 不在链上，均不移植。
//!
//! ⚠️ **异常路径照搬**：真源 `graph` 在管线解析失败时抛 `ValueError`，`sweep` **不接**，
//! 由契约跑者包成 `契约执行异常：<exc>`（`ok=false`）。本线让 `sweep` 返回 `Err(消息)`，
//! 契约层拼成同一句——这条可**逐字**复刻（见 `contracts.rs`）。

use crate::jsonread;
use crate::miniyaml;
use crate::pipeline_loader::{load_pipeline_file, Pipeline};
use crate::pyjson::Json;
use crate::pyval::{get, py_str, py_truthy, str_list};
use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

/// 真源 `_MODULE_GLOBS`。
const MODULE_GLOBS: [&str; 2] = ["04_模块库/*/*.md", "community/*/modules/*.md"];

/// 真源 `core.models.fid_key`：把 full_id 归一为协议比较键（类别段去「类」字）。
pub fn fid_key(fid: &str) -> String {
    match fid.split_once(':') {
        Some((c, i)) => format!("{}:{}", c.trim_end_matches('类'), i),
        None => fid.to_string(),
    }
}

/// Python `str.split(":")[-1]`。
fn bare(s: &str) -> &str {
    s.rsplit(':').next().unwrap_or("")
}

/// 真源 `_module_files` 的一条记录。
#[derive(Clone)]
struct Rec {
    id: String,
    cat_id: String,
    has_contract: bool,
    inputs: Vec<String>,
    outputs: Vec<String>,
    publish: Vec<String>,
    subscribe: Vec<String>,
    io_types: Option<Json>,
}

/// 真源 `_module_files`：仓库模块索引（文件名即 id，机读契约在场则挂上）。
fn module_files(root: &Path) -> BTreeMap<String, Rec> {
    let mut out: BTreeMap<String, Rec> = BTreeMap::new();
    let mut seen: BTreeSet<String> = BTreeSet::new();
    for pat in MODULE_GLOBS {
        for rel in crate::glob::expand(root, pat) {
            if seen.contains(&rel) || rel.rsplit('/').next() == Some("README.md") {
                continue;
            }
            seen.insert(rel.clone());
            let name = rel.rsplit('/').next().unwrap_or("").to_string();
            let stem = name.split('_').next().unwrap_or("").to_string();
            let parent = rel.rsplit_once('/').map(|(p, _)| p).unwrap_or("");
            let cat = parent.rsplit('/').next().unwrap_or("").replace('类', "");
            let mut rec = Rec {
                id: stem.clone(),
                cat_id: format!("{}:{}", cat, stem),
                has_contract: false,
                inputs: Vec::new(),
                outputs: Vec::new(),
                publish: Vec::new(),
                subscribe: Vec::new(),
                io_types: None,
            };
            // 真源 `except OSError: pass`——件不可读 ⇒ 该模块无契约摘要（跳过，不伪造）
            if let Ok(text) = std::fs::read_to_string(root.join(&rel)) {
                let parsed = miniyaml::fence_yaml(&text, "machine_contract");
                let mc = parsed
                    .as_ref()
                    .and_then(|p| get(p, "machine_contract").cloned())
                    .unwrap_or(Json::Null);
                if matches!(mc, Json::Object(_)) {
                    rec.has_contract = true;
                    rec.inputs = str_list(get(&mc, "inputs"));
                    rec.outputs = str_list(get(&mc, "outputs"));
                    let ev = get(&mc, "events").cloned().unwrap_or(Json::Null);
                    rec.publish = str_list(get(&ev, "publish"));
                    rec.subscribe = str_list(get(&ev, "subscribe"));
                    if py_truthy(get(&mc, "id").unwrap_or(&Json::Null)) {
                        rec.cat_id = py_str(get(&mc, "id"));
                    }
                    rec.io_types = crate::io_types::parse_io_types(&text);
                }
            }
            for key in [stem, rec.cat_id.clone(), fid_key(&rec.cat_id)] {
                out.entry(key).or_insert_with(|| rec.clone());
            }
        }
    }
    out
}

/// 真源 `_core_ids`：官方核心基座 id（`registry.json` `modules[]`）。
fn core_ids(root: &Path) -> Vec<String> {
    let Some(reg) = jsonread::read_file(root, "desktop/src/core/registry.json") else {
        return Vec::new();
    };
    let mut out = Vec::new();
    if let Some(Json::Array(mods)) = get(&reg, "modules") {
        for m in mods {
            if py_truthy(get(m, "id").unwrap_or(&Json::Null)) {
                out.push(py_str(get(m, "id")));
            }
        }
    }
    out
}

/// 真源 `_resolve`。
fn resolve<'a>(r: &str, index: &'a BTreeMap<String, Rec>) -> Option<&'a Rec> {
    index
        .get(r)
        .or_else(|| index.get(&fid_key(r)))
        .or_else(|| index.get(bare(r)))
}

/// 真源 `published.setdefault(ev, mid)` —— **首个**发布方胜出。
fn set_default(published: &mut Vec<(String, String)>, ev: &str, mid: &str) {
    if !published.iter().any(|(e, _)| e == ev) {
        published.push((ev.to_string(), mid.to_string()));
    }
}

/// 真源 `subscribed.setdefault(ev, []).append(mid)`。
fn append_sub(subscribed: &mut Vec<(String, Vec<String>)>, ev: &str, mid: &str) {
    match subscribed.iter_mut().find(|(e, _)| e == ev) {
        Some((_, v)) => v.push(mid.to_string()),
        None => subscribed.push((ev.to_string(), vec![mid.to_string()])),
    }
}

/// `graph` 里 `sweep` **真正消费**的那几项。
///
/// 真源 `graph` 的 advisory 明细带 `category` / `detail`，但那两样只进 `sweep` 的
/// `advisory_buckets` / `advisory_items` —— 而契约 `_c_pipeline_dryrun` **只读**
/// `tot["pipelines"]` 与 `tot["notes"]`。故本线只留**计数**（分支结构一字未改，
/// 只是不再拼没人读的字符串）。同理 `steps` / `edges` / `tokens` 明细与
/// `stats.{missing,layers,typed_tokens}` 均不落结构。
pub struct Graph {
    pub pipeline_id: String,
    pub issues: Vec<String>,
    pub notes: usize,
}

// 真源的公开 `graph(pipeline_path, root, ...)` 单条入口不在契约消费面上（`sweep` 用
// `graph_with` 并复用同一份 index/core），故不移植——收了就是没人核的代码。

fn graph_with(
    pipeline_path: &str,
    root: &Path,
    index: &BTreeMap<String, Rec>,
    core: &[String],
) -> Result<Graph, String> {
    let pl: Pipeline = match load_pipeline_file(&root.join(pipeline_path)) {
        Some(p) => p,
        None => {
            return Err(format!(
                "管线解析失败：{}（修复指引：检查 frontmatter 与代码围栏闭合）",
                pipeline_path
            ))
        }
    };

    let mut issues: Vec<String> = Vec::new();
    let mut notes = 0usize;
    let mut modules_count = 0usize;
    let mut tokens: Vec<String> = Vec::new();
    let mut done: BTreeSet<String> = BTreeSet::new();
    for x in core {
        done.insert(x.clone());
        done.insert(fid_key(x));
        done.insert(bare(x).to_string());
    }
    let mut published: Vec<(String, String)> = Vec::new();
    let mut subscribed: Vec<(String, Vec<String>)> = Vec::new();
    let mut layer_of: BTreeMap<String, usize> = BTreeMap::new();
    let mut executed: Vec<String> = Vec::new();

    // 基座先跑：官方核心的产出/事件进入池
    for r in core {
        if let Some(rec) = resolve(r, index) {
            for tok in &rec.outputs {
                if !tokens.contains(tok) {
                    tokens.push(tok.clone());
                }
            }
            for ev in &rec.publish {
                set_default(&mut published, ev, &rec.cat_id);
            }
            for ev in &rec.subscribe {
                append_sub(&mut subscribed, ev, &rec.cat_id);
            }
        }
    }

    for (idx0, layer) in pl.layers.iter().enumerate() {
        let idx = idx0 + 1;
        // 真源 `overrides` 在 sweep 下恒为 None ⇒ 取 `layer.default_modules`
        let refs: Vec<String> = layer.default_modules.clone();
        let same_layer: BTreeSet<String> = refs.iter().cloned().collect();
        for r in &refs {
            let Some(rec) = resolve(r, index) else {
                issues.push(format!(
                    "模块未在仓库找到：{}（层 {}）（修复指引：核对 04_模块库/community/*/modules 的文件名与类别限定）",
                    r, layer.id
                ));
                continue;
            };
            let mid = rec.cat_id.clone();
            executed.push(mid.clone());
            modules_count += 1;
            layer_of.insert(mid.clone(), idx);
            for dep in &rec.inputs {
                let dep_id = match resolve(dep, index) {
                    Some(d) => d.cat_id.clone(),
                    None => dep.clone(),
                };
                let bare_dep = bare(&dep_id).to_string();
                let dep_layer = layer_of
                    .get(&dep_id)
                    .or_else(|| layer_of.get(&bare_dep))
                    .copied();
                if done.contains(&dep_id) || done.contains(dep) || done.contains(&bare_dep) {
                    // 真源在此记一条 edge；`sweep` 不消费 edge ⇒ 本线不计
                } else if same_layer.contains(dep)
                    || same_layer.contains(&dep_id)
                    || same_layer.contains(&bare_dep)
                {
                    notes += 1;   // 真源：category=同层依赖序
                } else if dep_layer.is_some_and(|dl| dl > idx) {
                    issues.push(format!(
                        "依赖序违约：{} 依赖 {}，但 {} 未在其之前执行（修复指引：前移提供方层位，或把该模块移出本层 default）",
                        mid, dep_id, dep_id
                    ));
                } else {
                    notes += 1;   // 真源：category=跨包/外部依赖
                }
            }
            done.insert(mid.clone());
            done.insert(fid_key(&mid));
            done.insert(bare(&mid).to_string());
            done.insert(rec.id.clone());
            for tok in &rec.outputs {
                if !tokens.contains(tok) {
                    tokens.push(tok.clone());
                }
            }
            for ev in &rec.publish {
                set_default(&mut published, ev, &mid);
            }
            for ev in &rec.subscribe {
                append_sub(&mut subscribed, ev, &mid);
            }
        }
    }

    // 事件面：订阅方在本执行集内无发布方 ⇒ advisory
    let mut subs_sorted: Vec<&(String, Vec<String>)> = subscribed.iter().collect();
    subs_sorted.sort_by(|a, b| a.0.cmp(&b.0));
    for (ev, subs) in subs_sorted {
        if !published.iter().any(|(e, _)| e == ev) {
            let mut uniq: Vec<String> = subs.clone();
            uniq.sort();
            uniq.dedup();
            notes += 1;   // 真源：category=跨包/外部事件
        }
    }

    // 类型面（io_types）：仅在本执行集内判**可证**事项（未收窄不判死）
    let mut kind_of_token: Vec<(String, String)> = Vec::new();
    for mid in &executed {
        let Some(rec) = resolve(mid, index) else { continue };
        let Some(Json::Object(outs)) = rec.io_types.as_ref().and_then(|io| get(io, "outputs"))
        else {
            continue;
        };
        for (tok, kind) in outs.clone() {
            let kind = py_str(Some(&kind));
            if kind == "untyped" {
                continue;
            }
            if let Some((_, prev)) = kind_of_token.iter().find(|(t, _)| *t == tok) {
                if *prev != kind {
                    issues.push(format!(
                        "类型冲突：token {} 同时被声明为 {} 与 {}（修复指引：对齐各模块 io_types.outputs）",
                        tok, prev, kind
                    ));
                }
            }
            if !kind_of_token.iter().any(|(t, _)| *t == tok) {
                kind_of_token.push((tok, kind));
            }
        }
    }
    for mid in &executed {
        let Some(rec) = resolve(mid, index) else { continue };
        let Some(Json::Object(ins)) = rec.io_types.as_ref().and_then(|io| get(io, "inputs")) else {
            continue;
        };
        for (dep, want) in ins.clone() {
            let want = py_str(Some(&want));
            if want == "untyped" || want == "state" {
                continue;
            }
            let Some(dep_rec) = resolve(&dep, index) else { continue };
            let mut got: Vec<String> = Vec::new();
            if let Some(Json::Object(outs)) =
                dep_rec.io_types.as_ref().and_then(|io| get(io, "outputs"))
            {
                for (_, v) in outs {
                    let v = py_str(Some(v));
                    if v != "untyped" && !got.contains(&v) {
                        got.push(v);
                    }
                }
            }
            got.sort();
            if !got.is_empty() && !got.contains(&want) {
                issues.push(format!(
                    "类型不匹配：{} 期望 {} 提供 {}，而 {} 声明输出类型 {}（修复指引：对齐 io_types 或调整依赖）",
                    mid,
                    dep,
                    want,
                    dep,
                    py_list(&got)
                ));
            }
        }
    }

    let _ = modules_count;   // 真源 stats.modules 只进 advisory 汇总，契约不读
    Ok(Graph {
        pipeline_id: pl.id.clone(),
        issues,
        notes,
    })
}

/// Python `sorted(list)` 的 `%s` 形态：`['a', 'b']`。
fn py_list(v: &[String]) -> String {
    format!(
        "[{}]",
        v.iter().map(|x| format!("'{}'", x)).collect::<Vec<_>>().join(", ")
    )
}

/// 真源 `discover`：仓库内全部管线文件（03_管线库 + community/*/pipelines）。
///
/// ⚠️ **前缀语义必须对齐**：真源是 `[Path(p).as_posix() for p in sorted(Path(root).glob(pat))]`
/// ——`root` 不是 `.` 时结果**带 root 前缀**（绝对 root ⇒ 绝对路径）。`glob::expand` 恒返回
/// root 相对路径，故这里补前缀。真语料上看不出差别（该契约全绿、无路径进消息），
/// 但**解析失败**时那句 `管线解析失败：<path>` 会带上它——实测过该分歧，故照搬。
pub fn discover(root: &Path) -> Vec<String> {
    let prefix = root.to_string_lossy().replace('\\', "/");
    let prefix = prefix.trim_end_matches('/').to_string();
    let mut hits: Vec<String> = Vec::new();
    for pat in ["03_管线库/*.md", "community/*/pipelines/*.md"] {
        for rel in crate::glob::expand(root, pat) {
            if prefix.is_empty() || prefix == "." {
                hits.push(rel);
            } else {
                hits.push(format!("{}/{}", prefix, rel));
            }
        }
    }
    hits
}

/// 真源 `sweep` 的返回（只留契约消费的字段）。
pub struct Sweep {
    pub issues: Vec<String>,
    pub pipelines: usize,
    pub notes: usize,
}

/// 真源 `sweep`。任一条管线 `graph` 抛错即整体 `Err`（真源不接异常，见模块头）。
pub fn sweep(root: &Path) -> Result<Sweep, String> {
    let index = module_files(root);
    let core = core_ids(root);
    let mut issues: Vec<String> = Vec::new();
    let mut pipelines = 0usize;
    let mut notes = 0usize;
    for p in discover(root) {
        let g = graph_with(&p, root, &index, &core)?;
        pipelines += 1;
        notes += g.notes;
        for i in &g.issues {
            issues.push(format!("{}：{}", g.pipeline_id, i));
        }
    }
    Ok(Sweep { issues, pipelines, notes })
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_pipeline_dryrun_branches.py（勿手改；重跑生成器覆盖本段）
    /// ===== 分支级差分判据（期望值由 `tools/gen_pipeline_dryrun_branches.py` 从真源生成）=====
    ///
    /// 真语料上该契约**全绿**（0 issues / 114 管线 / 1142 advisory）⇒ 对账核不到错误分支。
    /// 三场景：kitchen（逐分支）/ 管线解析失败 / 零管线。
    ///
    /// 覆盖：模块未在仓库找到（hard）/ 同层依赖序（advisory）/ 跨包外部依赖（advisory）/
    /// 跨包外部事件（advisory）/ 类型冲突 / 类型不匹配 / 基座模块进池 / `fid_key` 长短名归一 /
    /// `README.md` 跳过 / 解析失败 ⇒ 契约记「契约执行异常：…」。
    ///
    /// ⚠️ **一支刻意不覆盖**：真源 `graph` 的 hard 分支「依赖序违约」（`dep_layer > idx`）在
    /// `sweep` 路径上**不可达**——`layer_of` 只在处理当前层时写入，层按升序处理 ⇒ 任何值都
    /// ≤ 当前 idx，`>` 永不成立。**不编造夹具去"覆盖"死代码**。
    const PB_KITCHEN: [(&str, &str); 7] = [
        ("03_管线库/P01_测试.md", r#"```yaml
Pipeline:
  id: P01
  name: 测试
  structure:
    type: linear
  layers:
    - id: L1
      default_modules: [M00]
    - id: L2
      default_modules: [M10, M11, GhostMod]
    - id: L3
      default_modules: [情感:M22]
```
"#),
        ("04_模块库/情感类/M22_c.md", r#"```yaml
machine_contract:
  id: 情感类:M22
  outputs: [toke]
```
"#),
        ("04_模块库/通用类/M00_基座.md", r#"```yaml
machine_contract:
  id: M00
  outputs: [tok0]
  events:
    publish: [ev_base]
```
"#),
        ("04_模块库/通用类/M10_a.md", r#"```yaml
machine_contract:
  id: M10
  inputs: [M99, M11, Ghostx]
  outputs: [tokc]
  events:
    subscribe: [ev_orphan]
  io_types:
    outputs:
      tokc: number
    inputs:
      M11: object
```
"#),
        ("04_模块库/通用类/M11_b.md", r#"```yaml
machine_contract:
  id: M11
  outputs: [tokd]
  io_types:
    outputs:
      tokc: string
      tokd: number
```
"#),
        ("04_模块库/通用类/README.md", r#"# 说明，必须被跳过
"#),
        ("desktop/src/core/registry.json", r#"{"modules": [{"id": "M00"}, {"id": "M99"}]}"#),
    ];
    const PB_BAD: [(&str, &str); 7] = [
        ("03_管线库/P02_坏件.md", r#"没有围栏的正文
"#),
        ("04_模块库/情感类/M22_c.md", r#"```yaml
machine_contract:
  id: 情感类:M22
  outputs: [toke]
```
"#),
        ("04_模块库/通用类/M00_基座.md", r#"```yaml
machine_contract:
  id: M00
  outputs: [tok0]
  events:
    publish: [ev_base]
```
"#),
        ("04_模块库/通用类/M10_a.md", r#"```yaml
machine_contract:
  id: M10
  inputs: [M99, M11, Ghostx]
  outputs: [tokc]
  events:
    subscribe: [ev_orphan]
  io_types:
    outputs:
      tokc: number
    inputs:
      M11: object
```
"#),
        ("04_模块库/通用类/M11_b.md", r#"```yaml
machine_contract:
  id: M11
  outputs: [tokd]
  io_types:
    outputs:
      tokc: string
      tokd: number
```
"#),
        ("04_模块库/通用类/README.md", r#"# 说明，必须被跳过
"#),
        ("desktop/src/core/registry.json", r#"{"modules": [{"id": "M00"}, {"id": "M99"}]}"#),
    ];
    const PB_NONE: [(&str, &str); 6] = [
        ("04_模块库/情感类/M22_c.md", r#"```yaml
machine_contract:
  id: 情感类:M22
  outputs: [toke]
```
"#),
        ("04_模块库/通用类/M00_基座.md", r#"```yaml
machine_contract:
  id: M00
  outputs: [tok0]
  events:
    publish: [ev_base]
```
"#),
        ("04_模块库/通用类/M10_a.md", r#"```yaml
machine_contract:
  id: M10
  inputs: [M99, M11, Ghostx]
  outputs: [tokc]
  events:
    subscribe: [ev_orphan]
  io_types:
    outputs:
      tokc: number
    inputs:
      M11: object
```
"#),
        ("04_模块库/通用类/M11_b.md", r#"```yaml
machine_contract:
  id: M11
  outputs: [tokd]
  io_types:
    outputs:
      tokc: string
      tokd: number
```
"#),
        ("04_模块库/通用类/README.md", r#"# 说明，必须被跳过
"#),
        ("desktop/src/core/registry.json", r#"{"modules": [{"id": "M00"}, {"id": "M99"}]}"#),
    ];

    fn build_pb_fixture(scenario: &str, files: &[(&str, &str)]) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("pipeline-branches-{}", scenario));
        for (rel, body) in files {
            let p = root.join(rel);
            std::fs::create_dir_all(p.parent().unwrap()).unwrap();
            std::fs::write(p, body).unwrap();
        }
        root
    }

    #[test]
    fn sweep_matches_truth_source_branch_by_branch() {
        for (scenario, files, want_issues, want_pipelines, want_notes, want_err, want_detail) in [
            ("kitchen", &PB_KITCHEN[..], &["P01：模块未在仓库找到：GhostMod（层 L2）（修复指引：核对 04_模块库/community/*/modules 的文件名与类别限定）", "P01：类型冲突：token tokc 同时被声明为 number 与 string（修复指引：对齐各模块 io_types.outputs）", "P01：类型不匹配：M10 期望 M11 提供 object，而 M11 声明输出类型 ['number', 'string']（修复指引：对齐 io_types 或调整依赖）"] as &[&str], 1, 3, None, "P01：模块未在仓库找到：GhostMod（层 L2）（修复指引：核对 04_模块库/community/*/modules 的文件名与类别限定）; P01：类型冲突：token tokc 同时被声明为 number 与 string（修复指引：对齐各模块 io_types.outputs）"),
            ("parsefail", &PB_BAD[..], &[] as &[&str], 0, 0, Some(r#"管线解析失败：<ROOT>/03_管线库/P02_坏件.md（修复指引：检查 frontmatter 与代码围栏闭合）"#), "契约执行异常：管线解析失败：<ROOT>/03_管线库/P02_坏件.md（修复指引：检查 frontmatter 与代码围栏闭合）"),
            ("nopipelines", &PB_NONE[..], &[] as &[&str], 0, 0, None, "管线 0 条零 hard 缺陷（advisory 0）"),
        ] {
            let root = build_pb_fixture(scenario, files);
            match (sweep(&root), want_err) {
                (Ok(s), None) => {
                    assert_eq!(s.issues, want_issues, "场景 {} 的 issues", scenario);
                    assert_eq!(s.pipelines, want_pipelines, "场景 {} 的管线条数", scenario);
                    assert_eq!(s.notes, want_notes, "场景 {} 的 advisory 数", scenario);
                    let detail = if s.issues.is_empty() {
                        format!("管线 {} 条零 hard 缺陷（advisory {}）", s.pipelines, s.notes)
                    } else {
                        s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
                    };
                    assert_eq!(detail, want_detail, "场景 {} 的契约 detail", scenario);
                }
                (Err(msg), Some(want)) => {
                    // 夹具根归一：两侧目录名不同（Rust 侧带进程号隔离），消息里的绝对路径只差这一段
                    let root_posix = root.to_string_lossy().replace('\\', "/");
                    let norm = |s: &str| s.replace(&root_posix, "<ROOT>");
                    assert_eq!(norm(&msg), want, "场景 {} 的异常消息", scenario);
                    assert_eq!(
                        norm(&format!("契约执行异常：{}", msg)),
                        want_detail,
                        "场景 {} 的契约 detail", scenario
                    );
                }
                (got, _) => panic!("场景 {} 的成败不符：{:?}", scenario, got.is_ok()),
            }
        }
    }
    // <<< GENERATED
}
