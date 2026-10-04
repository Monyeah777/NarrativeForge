//! 社区领域包 conformance 分级（`conformance_scan.scan`）—— 与真源
//! `desktop/src/core/conformance_scan.py` 的 `_scan_impl` 对账。
//!
//! 三张面：① 每份模块文档的 `machine_contract` 须有合法 `conformance` 声明（L1/L2/L3），
//! 且**不得虚标**（声明级 > 可证级 = FAIL；可证级看该 id 是否在「装配在册证据」里）；
//! 另补**文件级 mc.id 唯一**判据（运行时索引 first-wins 会静默择一，编号会指向不确定的模块）。
//! ② 每个社区包的 `protocol.yaml` 同理，可证级看包 id 是否在 `registry.protocols[]`。
//! ③ 导出契约面 manifest：每项须 `conformance: L3`、证据文件在场、门禁名出现在 `verify.sh`。
//!
//! **未移植的近似（如实标注）**：真源把底层异常文本（YAML/JSON 解析失败）拼进 issue，
//! 本线的措辞是自拟的；真源 `_lyaml.module() is None`（PyYAML 缺席）与派生的
//! `memo_pair` / `disk_cache` 持久缓存层本线不实现——缓存是纯函数优化，不改结论。
//!
//! 本模块是 `nf verify-report` 的 `conformance` 判据，同时供 `nf score` 的
//! `conformance_clean` 信号使用，**不单独开 CLI 面**。

use crate::jsonread;
use crate::miniyaml;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, py_str};
use std::collections::BTreeSet;
use std::path::Path;

/// 真源 `_read_json` → `(值, 错误文本)`；缺失/解析失败一律 `(None, 文本)`。
fn read_json(root: &Path, rel: &str) -> (Option<Json>, String) {
    if !root.join(rel).is_file() {
        return (None, "文件不在场".to_string());
    }
    match jsonread::read_file(root, rel) {
        Some(v) => (Some(v), String::new()),
        None => (None, "JSON 解析失败".to_string()),
    }
}

/// 真源 `_evidence_ids`：官方 `registry.modules[].id` + 社区 `registry.protocols[].module_ids`。
fn evidence_ids(reg: Option<&Json>) -> Vec<String> {
    let mut ids: Vec<String> = Vec::new();
    if let Some(r) = reg {
        for m in arr_items(get(r, "modules")) {
            if matches!(m, Json::Object(_)) && matches!(get(m, "id"), Some(Json::Str(_))) {
                ids.push(py_str(get(m, "id")));
            }
        }
        for p in arr_items(get(r, "protocols")) {
            for mid in arr_items(get(p, "module_ids")) {
                if matches!(mid, Json::Str(_)) {
                    ids.push(py_str(Some(mid)));
                }
            }
        }
    }
    ids
}

pub struct ScanResult {
    pub issues: Vec<String>,
    pub stats: Json,
}

fn order_of(level: &str) -> i64 {
    match level {
        "L1" => 1,
        "L2" => 2,
        "L3" => 3,
        _ => 0,
    }
}

/// 真源 `_scan_impl`。
pub fn scan(root: &Path) -> ScanResult {
    let mut issues: Vec<String> = Vec::new();

    let (reg, _err) = read_json(root, "desktop/src/core/registry.json");
    let evidence: BTreeSet<String> = evidence_ids(reg.as_ref()).into_iter().collect();
    let reg_ids: BTreeSet<String> = arr_items(reg.as_ref().and_then(|r| get(r, "protocols")))
        .iter()
        .map(|p| py_str(get(p, "id")))
        .collect();

    let mut modules_mc = 0i64;
    let mut seen_mc_id: Vec<(String, String)> = Vec::new();
    for rel in crate::module_signature::module_docs(root) {
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
            issues.push(format!("{}: 读取失败（本线不复制 Python 异常文本）", rel));
            continue;
        };
        let parsed = miniyaml::fence_yaml(&text, "machine_contract")
            .unwrap_or_else(|| Json::Object(Vec::new()));
        if get(&parsed, "machine_contract").is_none() {
            continue;
        }
        let mc = get(&parsed, "machine_contract").cloned().unwrap_or(Json::Null);
        let mid = py_str(get(&mc, "id"));
        if !mid.is_empty() {
            if let Some((_, prev)) = seen_mc_id.iter().find(|(m, _)| *m == mid) {
                issues.push(format!(
                    "{}: 模块 id 与 {} 重复（mc.id={}）——编号是全局寻址面，运行时索引会静默择一，须改号（修复指引：按 01 §1.6.11 换类内段号或 M91-M99 段号）",
                    rel, prev, mid
                ));
            } else {
                seen_mc_id.push((mid.clone(), rel.clone()));
            }
        }
        modules_mc += 1;
        let declared = py_str(get(&mc, "conformance"));
        if !matches!(declared.as_str(), "L1" | "L2" | "L3") {
            issues.push(format!(
                "{}: machine_contract 缺/非法 conformance 声明 {}",
                rel,
                crate::pyval::py_repr(get(&mc, "conformance").unwrap_or(&Json::Null))
            ));
            continue;
        }
        let provable = if matches!(get(&mc, "id"), Some(Json::Str(_)))
            && evidence.contains(&mid)
        {
            2
        } else {
            1
        };
        if order_of(&declared) > provable {
            issues.push(format!(
                "{}: conformance 虚标 {} > 可证 L{}（{} 不在装配在册证据）",
                rel,
                declared,
                provable,
                crate::pyval::py_repr(get(&mc, "id").unwrap_or(&Json::Null))
            ));
        }
    }

    let mut packages = 0i64;
    for rel in crate::glob::expand(root, "community/*/protocol.yaml") {
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
            issues.push(format!("{}: protocol.yaml 解析失败（本线不复制 Python 异常文本）", rel));
            continue;
        };
        let data = match miniyaml::parse(&text) {
            Ok(d) => d,
            Err(_) => {
                issues.push(format!(
                    "{}: protocol.yaml 解析失败（本线不复制 Python 异常文本）",
                    rel
                ));
                continue;
            }
        };
        packages += 1;
        let pkg = get(&data, "package").cloned().unwrap_or(Json::Null);
        let declared = py_str(get(&pkg, "conformance"));
        let pid = py_str(get(&pkg, "id"));
        if !matches!(declared.as_str(), "L1" | "L2" | "L3") {
            issues.push(format!(
                "{}: package 缺/非法 conformance 声明 {}",
                rel,
                crate::pyval::py_repr(get(&pkg, "conformance").unwrap_or(&Json::Null))
            ));
            continue;
        }
        let provable = if matches!(get(&pkg, "id"), Some(Json::Str(_))) && reg_ids.contains(&pid) {
            2
        } else {
            1
        };
        if order_of(&declared) > provable {
            issues.push(format!(
                "{}: conformance 虚标 {} > 可证 L{}（包不在 registry protocols[]）",
                rel, declared, provable
            ));
        }
    }

    let (manifest, err) = read_json(root, "protocol/export_conformance.json");
    let mut export_items = 0i64;
    match manifest {
        None => issues.push(format!(
            "protocol/export_conformance.json 缺失/解析失败：{}",
            err
        )),
        Some(manifest) if !matches!(manifest, Json::Object(_)) => issues.push(format!(
            "protocol/export_conformance.json 缺失/解析失败：{}",
            err
        )),
        Some(manifest) => {
            let verify_txt = std::fs::read_to_string(root.join("verify.sh")).unwrap_or_default();
            for item in arr_items(get(&manifest, "items")) {
                export_items += 1;
                if !matches!(item, Json::Object(_)) {
                    issues.push("export manifest item 非对象".to_string());
                    continue;
                }
                if py_str(get(item, "conformance")) != "L3" {
                    issues.push(format!(
                        "导出面 {}: conformance 应为 L3（导出门禁锁定面）",
                        py_str(get(item, "id"))
                    ));
                }
                for ev in arr_items(get(item, "evidence")) {
                    let e = py_str(Some(ev));
                    if !root.join(&e).is_file() {
                        issues.push(format!(
                            "导出面 {}: 证据文件缺失 {}",
                            py_str(get(item, "id")),
                            e
                        ));
                    }
                }
                for gate in arr_items(get(item, "gates")) {
                    let g = py_str(Some(gate));
                    if !verify_txt.contains(&g) {
                        issues.push(format!(
                            "导出面 {}: 证据门禁 {} 不在 verify.sh",
                            py_str(get(item, "id")),
                            g
                        ));
                    }
                }
            }
        }
    }

    let stats = Json::Object(vec![
        ("modules_mc".to_string(), Json::Int(modules_mc)),
        ("packages".to_string(), Json::Int(packages)),
        ("export_items".to_string(), Json::Int(export_items)),
    ]);
    ScanResult { issues, stats }
}

/// 供 `nf score` 的 `conformance_clean` 信号使用（真源 `_count(root,"conformance_scan","scan")`）。
pub fn issue_count(root: &Path) -> usize {
    scan(root).issues.len()
}
