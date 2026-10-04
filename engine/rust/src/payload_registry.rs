//! 事件载荷注册表（`payload_registry`）—— 与真源 `desktop/src/core/payload_registry.py` 对账。
//!
//! 三件事：① `protocol/event_registry.json` 用 `event_payload.schema.json` **自校验**
//! （复用 [`crate::schema_lint::subset_validate`]，零第三方）；② 交叉断言：已登记事件名必须
//! 出现在任一 `machine_contract` 的 publish/subscribe 或 `registry.subscriptions`（防死注册 /
//! 名字漂移）；③ 未登记事件**不 FAIL**（社区包载荷逐批 retro-fit，登记是渐进扩展）。
//!
//! 本模块是 `nf verify-report` 的 `payload` 判据，**不单独开 CLI 面**——对账走面 12 的整篇报告比对。

use crate::jsonread;
use crate::miniyaml;
use crate::pyjson::Json;
use crate::pyval::{get, plain_str, py_truthy};
use std::collections::BTreeSet;
use std::path::Path;

#[derive(Debug, Clone, PartialEq)]
pub struct PayloadStats {
    pub registered: usize,
    pub used: usize,
    pub declared: usize,
    pub pending: usize,
}

impl PayloadStats {
    pub fn to_json(&self) -> Json {
        Json::Object(vec![
            ("registered".to_string(), Json::Int(self.registered as i64)),
            ("used".to_string(), Json::Int(self.used as i64)),
            ("declared".to_string(), Json::Int(self.declared as i64)),
            ("pending".to_string(), Json::Int(self.pending as i64)),
        ])
    }
}

/// 真源 `scan` → `(issues, stats)`；`stats = None` 对应真源返回的空字典。
pub fn scan(root: &Path) -> (Vec<String>, Option<PayloadStats>) {
    const NEEDED: [&str; 2] = [
        "protocol/event_payload.schema.json",
        "protocol/event_registry.json",
    ];
    let missing: Vec<&str> = NEEDED
        .iter()
        .copied()
        .filter(|rel| !root.join(rel).is_file())
        .collect();
    if !missing.is_empty() {
        return (
            vec![format!(
                "缺 {}（修复指引：在 NF 仓库根运行本扫描，或先补齐该协议件）",
                missing.join("、")
            )],
            None,
        );
    }
    let Some(schema) = jsonread::read_file(root, "protocol/event_payload.schema.json") else {
        return (vec!["protocol/event_payload.schema.json 不是合法 JSON".to_string()], None);
    };
    let Some(registry) = jsonread::read_file(root, "protocol/event_registry.json") else {
        return (vec!["protocol/event_registry.json 不是合法 JSON".to_string()], None);
    };
    let mut issues = crate::schema_lint::subset_validate(&registry, &schema, "event_registry");

    let mut used: BTreeSet<String> = BTreeSet::new();
    for rel in crate::module_signature::module_docs(root) {
        let Ok(txt) = std::fs::read_to_string(root.join(&rel)) else { continue };
        let Some(parsed) = miniyaml::fence_yaml(&txt, "machine_contract") else { continue };
        let mc = get(&parsed, "machine_contract").cloned().unwrap_or_else(|| Json::Object(Vec::new()));
        let ev = get(&mc, "events").cloned().unwrap_or_else(|| Json::Object(Vec::new()));
        for k in ["publish", "subscribe"] {
            for v in crate::pyval::arr_items(get(&ev, k)) {
                used.insert(plain_str(v));
            }
        }
    }
    if let Some(reg) = jsonread::read_file(root, "desktop/src/core/registry.json") {
        if let Some(Json::Object(subs)) = get(&reg, "subscriptions") {
            for (k, _) in subs {
                used.insert(k.clone());
            }
        }
    }

    let registered_pairs: Vec<(String, Json)> = match get(&registry, "events") {
        Some(Json::Object(p)) => p.clone(),
        _ => Vec::new(),
    };
    let registered: BTreeSet<String> = registered_pairs.iter().map(|(k, _)| k.clone()).collect();

    let mut dead: Vec<String> = registered.difference(&used).cloned().collect();
    dead.sort();
    if !dead.is_empty() {
        issues.push(format!("已登记事件无 machine 引用（死注册）：{}", dead.join(", ")));
    }
    let mut unregistered: Vec<String> = used.difference(&registered).cloned().collect();
    unregistered.sort();
    if !unregistered.is_empty() {
        issues.push(format!("机器事件未登记载荷（漏登）：{}", unregistered.join(", ")));
    }

    let declared = registered_pairs
        .iter()
        .filter(|(_, v)| py_truthy(get(v, "fields").unwrap_or(&Json::Null)))
        .count();
    (
        issues,
        Some(PayloadStats {
            registered: registered.len(),
            used: used.len(),
            declared,
            pending: registered.len() - declared,
        }),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    /// ===== 分支级差分判据（期望值由 `tools/gen_payload_branches.py` 从真源生成）=====
    ///
    /// 真语料上该面只有固定的几条 ⇒ 错误分支须合成夹具核。本夹具踩：
    /// schema 自校验不过 / 死注册（登记了没人引用）/ 漏登（引用未登记）/ `fields` 缺失计入 pending /
    /// `registry.subscriptions` 也计入 used。
    const WANT_PL_ISSUES: [&str; 3] = [
        "event_registry/schema: 值 'wrong/1' 不在枚举 ['community-event-registry/1']",
        "已登记事件无 machine 引用（死注册）：dead_ev",
        "机器事件未登记载荷（漏登）：sub_ev, unregistered_ev",
    ];

    fn build_payload_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("payload-branches");
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        std::fs::create_dir_all(root.join("desktop/src/core")).unwrap();
        std::fs::create_dir_all(root.join("04_模块库/通用类")).unwrap();
        std::fs::write(root.join("protocol/event_payload.schema.json"), r#"{"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "required": ["schema", "events"], "properties": {"schema": {"type": "string", "enum": ["community-event-registry/1"]}, "events": {"type": "object"}}}"#).unwrap();
        std::fs::write(root.join("protocol/event_registry.json"), r#"{"schema": "wrong/1", "events": {"a": {"fields": ["f1"]}, "b": {}, "dead_ev": {"fields": ["f2"]}}}"#).unwrap();
        std::fs::write(root.join("04_模块库/通用类/M01_x.md"), r#"```yaml
machine_contract:
  id: M01
  events:
    publish: [a]
    subscribe: [b, unregistered_ev]
```
"#).unwrap();
        std::fs::write(root.join("desktop/src/core/registry.json"), r#"{"subscriptions": {"sub_ev": {}}}"#).unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_payload_fixture();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, WANT_PL_ISSUES, "逐条消息与次序都须与真源一致");
        assert!(crate::jsonread::json_eq(
            &stats.map(|s| s.to_json()).unwrap_or_else(|| Json::Object(Vec::new())),
            &crate::jsonread::convert(&serde_json::json!({
                "registered": 3, "used": 4,
                "declared": 2, "pending": 1
            }))
            .unwrap()
        ));
    }
}
