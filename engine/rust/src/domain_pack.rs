//! 域包**名录机检** —— 与真源 `desktop/src/core/domain_pack.py` 的 `scan` 对账。
//!
//! ## 移植面按消费者界定（有工具，不是猜的）
//!
//! 真源文件 **2,067 行 / 50 个函数**，看着是大件；但用
//! [`tools/trace_call_closure.py`](../../tools/trace_call_closure.py) 从入口 `scan` 算调用闭包，
//! **判据面只有 6 个函数 / 约 121 行**：
//!
//! ```text
//! 闭包内：scan · _scan_impl · manifest_verify · standards_catalog · _read_json · _read_json_raw
//! ```
//!
//! 其余 44 个函数（`build` / `module_md` / `concept_graph_md` / `domain_spec_json` /
//! `_write_binding_table` / `allocate` …）全是**域包工厂的生成器与写面**——本线只读，不移植。
//!
//! `manifest_verify` 的判据：名录 ↔ 盘上实况一致（registry / protocol.yaml / INDEX 产出面数）+
//! 可机验占比 ≥ 门槛 + 有 T4 可复算面 + 标准绑定面（覆盖率 / 在册 / 概念密度 / 双锚 /
//! 数据真实性 / 可达率 / 绑定表证据齐备）。

use crate::pyjson::Json;
use crate::pyval;
use std::path::Path;

pub const SPEC_DIR: &str = ".rivet/private_archive/ai_packs/specs";
pub const MANIFEST_REL: &str = "protocol/domain_packs.json";
pub const REGISTRY_REL: &str = "desktop/src/core/registry.json";
pub const STANDARDS_REL: &str = "protocol/standards_catalog.json";
pub const BINDING_REL: &str = "protocol/standards_binding.json";
pub const AUTHENTICITY_THRESHOLD: f64 = 0.95;
pub const REACHABLE_RATIO_THRESHOLD: f64 = 0.9;

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

/// 真源 `p.get(k) or <default>` 的浮点版（Python 的 `or` 走**真值**判定）。
fn py_float_or(v: Option<&Json>, default: f64) -> f64 {
    match v {
        Some(x) if pyval::py_truthy(x) => match x {
            Json::Int(i) => *i as f64,
            Json::Float(f) => *f,
            Json::Str(s) => s.parse::<f64>().unwrap_or(default),
            Json::Bool(b) => {
                if *b {
                    1.0
                } else {
                    default
                }
            }
            _ => default,
        },
        _ => default,
    }
}

/// 真源 `_read_json_raw`：缺件/坏件 → `None`（不抛）。
pub fn read_json_opt(p: &Path) -> Option<Json> {
    let text = std::fs::read_to_string(p).ok()?;
    crate::jsonmini::parse(&text).ok().map(|r| r.value)
}

/// 真源 `_read_json`。
pub fn read_json(p: &Path) -> Option<Json> {
    read_json_opt(p)
}

fn read_text(p: &Path) -> String {
    std::fs::read(p).map(|b| String::from_utf8_lossy(&b).into_owned()).unwrap_or_default()
}

/// 真源 `standards_catalog` → `{标准 id: 条目}`。
pub fn standards_catalog(root: &Path) -> Vec<String> {
    let doc = read_json(&root.join(STANDARDS_REL)).unwrap_or(Json::Object(vec![]));
    arr_of(obj_get(&doc, "standards"))
        .iter()
        .filter_map(|s| obj_get(s, "id").map(pyval::plain_str))
        .collect()
}

/// 真源 `manifest_verify` → `(issues, stats)`。
pub fn manifest_verify(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let path = root.join(MANIFEST_REL);
    if !path.is_file() {
        return (
            Vec::new(),
            Json::Object(vec![
                ("packs".to_string(), Json::Int(0)),
                ("note".to_string(), Json::Str("无域包名录（域包工程未启用）".to_string())),
            ]),
        );
    }
    let doc = read_json(&path).unwrap_or(Json::Object(vec![]));
    let thr = py_float_or(obj_get(&doc, "machine_verifiable_threshold"), 0.95);
    let cat = standards_catalog(root);
    let dens_min = py_float_or(obj_get(&doc, "concept_density_threshold"), 1.0);
    let auth_min =
        py_float_or(obj_get(&doc, "data_authenticity_threshold"), AUTHENTICITY_THRESHOLD);
    let reach_min =
        py_float_or(obj_get(&doc, "reachable_ratio_threshold"), REACHABLE_RATIO_THRESHOLD);
    let (mut packs, mut faces_n, mut functional) = (0i64, 0i64, 0i64);
    let reg = read_json(&root.join(REGISTRY_REL)).unwrap_or(Json::Object(vec![]));
    let by_id: Vec<Json> = arr_of(obj_get(&reg, "protocols"));
    let binding = read_json(&root.join(BINDING_REL)).unwrap_or(Json::Object(vec![]));
    let bind_by: Vec<Json> = arr_of(obj_get(&binding, "packs"));

    for p in arr_of(obj_get(&doc, "packs")) {
        let pkg = match obj_get(&p, "package") {
            Some(Json::Null) | None => String::new(),
            Some(v) => pyval::plain_str(v),
        };
        let bp = bind_by
            .iter()
            .find(|b| match (obj_get(b, "code"), obj_get(&p, "code")) {
                (Some(x), Some(y)) => pyval::py_eq(x, y),
                _ => false,
            })
            .cloned()
            .unwrap_or(Json::Object(vec![]));
        packs += 1;
        faces_n += pyval::py_int_or(obj_get(&p, "output_faces"), 0);
        functional += pyval::py_int_or(obj_get(&p, "functional_faces"), 0);
        let regp = by_id.iter().find(|r| match obj_get(r, "id") {
            Some(Json::Str(s)) => *s == pkg,
            _ => false,
        });
        match regp {
            None => issues.push(format!(
                "{}：registry protocols[] 无该包（名录 ↔ 登记不一致）",
                pkg
            )),
            Some(regp) => {
                let a = obj_get(regp, "pipeline").map(pyval::plain_str).unwrap_or_default();
                let b = obj_get(&p, "pipeline").map(pyval::plain_str).unwrap_or_default();
                if a != b {
                    issues.push(format!(
                        "{}：管线不一致（名录 {} / registry {}）",
                        pkg,
                        pyval::py_str(obj_get(&p, "pipeline")),
                        pyval::py_str(obj_get(regp, "pipeline"))
                    ));
                }
                let ma: Vec<String> = arr_of(obj_get(regp, "module_ids"))
                    .iter()
                    .map(pyval::plain_str)
                    .collect();
                let mb: Vec<String> = arr_of(obj_get(&p, "module_ids"))
                    .iter()
                    .map(pyval::plain_str)
                    .collect();
                if ma != mb {
                    issues.push(format!("{}：模块 id 不一致（名录 ↔ registry）", pkg));
                }
            }
        }
        let proto = root.join("community").join(&pkg).join("protocol.yaml");
        if !proto.is_file() {
            issues.push(format!("{}：包目录或 protocol.yaml 缺失", pkg));
            continue;
        }
        let text = read_text(&proto);
        for tok in [obj_get(&p, "pipeline"), obj_get(&p, "category")] {
            let t = tok.map(pyval::plain_str).unwrap_or_default();
            if !text.contains(&t) {
                issues.push(format!("{}：protocol.yaml 缺名录声明 {}", pkg, t));
            }
        }
        let idx_path = root.join("community").join(&pkg).join("outputs").join("INDEX.json");
        if !idx_path.is_file() {
            issues.push(format!("{}：缺 outputs/INDEX.json", pkg));
            continue;
        }
        let faces: Vec<Json> = match read_json_opt(&idx_path) {
            Some(v) => arr_of(obj_get(&v, "outputs")),
            None => Vec::new(),
        };
        let t234 = faces
            .iter()
            .filter(|e| {
                matches!(obj_get(e, "tier"), Some(Json::Str(s)) if s == "T2" || s == "T3" || s == "T4")
            })
            .count() as f64;
        let denom = std::cmp::max(1, faces.len()) as f64;
        // 真源 `round(x, 4)`：Python 的银行家舍入
        let ratio = crate::pyfloat::round_to(t234 / denom, 4);
        if ratio < thr {
            issues.push(format!(
                "{}：可机验产出占比 {:.4} < 门槛 {:.2}（产出面必须 ≥95%% 可机验）",
                pkg, ratio, thr
            ));
        }
        if !faces
            .iter()
            .any(|e| matches!(obj_get(e, "tier"), Some(Json::Str(s)) if s == "T4"))
        {
            issues.push(format!("{}：无 T4 可复算面（域包必须有一个可重算产出）", pkg));
        }
        let of = pyval::py_int_or(obj_get(&p, "output_faces"), 0);
        if of != faces.len() as i64 {
            issues.push(format!(
                "{}：名录产出面数 {} ≠ INDEX 实况 {}",
                pkg,
                pyval::py_str(obj_get(&p, "output_faces")),
                faces.len()
            ));
        }
        let code = match obj_get(&p, "code") {
            Some(Json::Null) | None => String::new(),
            Some(v) => pyval::plain_str(v),
        };
        let spec_path = root.join(SPEC_DIR).join(format!("{}.json", code));
        if spec_path.is_file() {
            let payload = root
                .join("community")
                .join(&pkg)
                .join("outputs")
                .join("DOMAIN_SPEC.json");
            let payload = read_json_opt(&payload).unwrap_or(Json::Object(vec![]));
            let subs = arr_of(obj_get(&payload, "subdivisions"));
            let bad_ref: Vec<String> = subs
                .iter()
                .filter(|s| {
                    let r = match obj_get(s, "standard_ref") {
                        Some(Json::Null) | None => String::new(),
                        Some(v) => pyval::plain_str(v),
                    };
                    !cat.contains(&r)
                })
                .map(|s| pyval::py_str(obj_get(s, "id")))
                .collect();
            if !bad_ref.is_empty() {
                let head: Vec<Json> =
                    bad_ref.iter().take(4).map(|s| Json::Str(s.clone())).collect();
                issues.push(format!(
                    "{}：细分未绑可扩展标准或引用不在册：{}",
                    pkg,
                    pyval::py_repr_list(&head)
                ));
            }
            let cov = py_float_or(obj_get(&p, "standards_binding_coverage"), 0.0);
            if cov < 1.0 {
                issues.push(format!(
                    "{}：标准绑定覆盖率 {:.2} < 1.0（每条细分须绑一个目录内标准）",
                    pkg, cov
                ));
            }
            let dens = py_float_or(obj_get(&p, "concept_density"), 0.0);
            if dens < dens_min {
                issues.push(format!(
                    "{}：概念密度 {:.3} < 门槛 {:.3}（边/节点；含标准节点与绑定边）",
                    pkg, dens, dens_min
                ));
            }
            let bound = pyval::py_int_or(obj_get(&p, "standards_bound"), 0);
            if bound < 3 {
                issues.push(format!(
                    "{}：绑定标准数 {} < 3（单包至少要贴 3 条不同标准）",
                    pkg,
                    pyval::py_str(obj_get(&p, "standards_bound"))
                ));
            }
            let sup = py_float_or(obj_get(&p, "support_binding_coverage"), 0.0);
            if sup < 1.0 {
                issues.push(format!(
                    "{}：辅锚覆盖率 {:.2} < 1.0（每条细分须另绑一条产出承载标准）",
                    pkg, sup
                ));
            }
            let dep = pyval::py_int_or(obj_get(&p, "standards_dep_edges"), 0);
            if dep < 1 {
                issues.push(format!(
                    "{}：概念图无标准依赖边（绑定标准的 depends_on 未入图）",
                    pkg
                ));
            }
            let auth = py_float_or(obj_get(&p, "data_authenticity"), 0.0);
            if auth < auth_min {
                issues.push(format!(
                    "{}：数据真实性分 {:.4} < 门槛 {:.2}（在册 × 实测可达 × 证据齐备）",
                    pkg, auth, auth_min
                ));
            }
            let rr = py_float_or(obj_get(&p, "standards_reachable_ratio"), 0.0);
            if rr < reach_min {
                issues.push(format!(
                    "{}：绑定标准本机实测可达率 {:.4} < 门槛 {:.2}",
                    pkg, rr, reach_min
                ));
            }
            let bindings = arr_of(obj_get(&bp, "bindings"));
            let bad_binding: Vec<Json> = bindings
                .iter()
                .filter(|r| {
                    let st = obj_get(r, "standard").map(pyval::plain_str).unwrap_or_default();
                    let sup = obj_get(r, "support_standard")
                        .map(pyval::plain_str)
                        .unwrap_or_default();
                    let d1 = obj_get(r, "standard_probe_date")
                        .map(pyval::plain_str)
                        .unwrap_or_default();
                    let d2 = obj_get(r, "support_standard_probe_date")
                        .map(pyval::plain_str)
                        .unwrap_or_default();
                    !cat.contains(&st) || !cat.contains(&sup) || d1.is_empty() || d2.is_empty()
                })
                .cloned()
                .collect();
            if !bad_binding.is_empty() {
                let head: Vec<Json> = bad_binding
                    .iter()
                    .take(4)
                    .map(|r| obj_get(r, "subdivision").cloned().unwrap_or(Json::Null))
                    .collect();
                issues.push(format!(
                    "{}：绑定表缺在册证明或实测记录：{}",
                    pkg,
                    pyval::py_repr_list(&head)
                ));
            }
        }
    }
    (
        issues,
        Json::Object(vec![
            ("packs".to_string(), Json::Int(packs)),
            ("faces".to_string(), Json::Int(faces_n)),
            ("functional".to_string(), Json::Int(functional)),
        ]),
    )
}

/// 真源 `scan` → `(issues, stats)`（缓存层不移植：纯函数优化，不改结论）。
pub fn scan(root: &Path) -> (Vec<String>, Json) {
    manifest_verify(root)
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_domain_pack_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 真语料差分（期望值由生成器从真源取）=====
    #[test]
    fn domain_pack_matches_truth_source() {
        let root = crate::testutil::repo_root();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, &[] as &[&str], "issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"faces": 1000, "functional": 100, "packs": 100}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want),
                "stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
    }

    /// 缺名录时的**中性通过**支（真语料有名录，踩不到）。
    #[test]
    fn domain_pack_without_manifest_is_neutral() {
        let root = crate::testutil::fixture("domain-pack-empty");
        let (issues, stats) = scan(&root);
        assert_eq!(issues, &[] as &[&str]);
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"note": "无域包名录（域包工程未启用）", "packs": 0}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want), "缺名录 stats 不一致");
    }
    // <<< GENERATED
}
