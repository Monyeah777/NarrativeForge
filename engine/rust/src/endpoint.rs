//! 服务端点契约（`endpoint-contract`）—— 与真源 `desktop/src/core/endpoint.py` 的 `scan` 对账。
//!
//! NF 不产服务，故本模块**不实现 HTTP**：它把"若要把 NF 能力暴露成服务，面长什么样"固定成
//! 机器可读契约，并**门禁**「每个端点的 `maps_to` 必须指向当下真实存在的 CLI 子命令或 MCP 工具」
//! ——契约不许指向空气（防纸面能力）。
//!
//! 判据：schema；status ∈ {proposed, implemented}；endpoint 的 id 与 method+path 各自唯一；
//! `maps_to` 可解析（`nf <cmd>` 在 CLI 注册表内，或 MCP 工具名在 `TOOL_DEFS` 内）；
//! `streaming: true` 须有 SSE 约定；弃用面（deprecated ⇒ implemented + 弃用约定 + RFC 8594 sunset +
//! 显式 replacement）；幂等声明面（RFC 9110 §9.2.2：默认幂等，例外须登记且非幂等端点须给幂等键策略）。
//!
//! **`TOOL_DEFS` 是代码常量**（真源 `from core.mcp_runtime import TOOL_DEFS`）——与 `root` 无关，
//! 故本线以**常量表**复刻其名字集（`scan` 只用到 `name`）。这张表由
//! `tools/gen_doc_tables.py` 同源的生成器从真源转录，**勿手改**：真源增删工具面，这里会红。

use crate::jsonread;
use crate::pyjson::Json;
use crate::pyval::{get, py_repr, py_str, py_truthy};
use std::collections::BTreeSet;
use std::path::Path;

pub const CONTRACT_REL: &str = "protocol/endpoint_contract.json";
pub const SCHEMA: &str = "nf-endpoint/1";
const STATUSES: [&str; 2] = ["proposed", "implemented"];
const METHODS: [&str; 5] = ["GET", "POST", "PUT", "PATCH", "DELETE"];
const IDEMPOTENCY_MODES: [&str; 2] = ["idempotent", "non-idempotent"];
const IDEMPOTENCY_KEY: [&str; 2] = ["required", "none"];

/// 运行时工具名表：见 [`crate::mcp_tables`]（真源 `core.mcp_runtime.TOOL_DEFS` 的 `name` 集）。
///
/// 本文件不再自持一份——两张表（工具/提示）统一收在 `mcp_tables.rs`，**覆盖缺口只留一处**。

fn mcp_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^([a-z_]+)（MCP 工具）$").expect("MCP 正则固定合法"))
}

fn cli_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^nf\s+([a-z-]+)").expect("CLI 正则固定合法"))
}

fn add_parser_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r#"sub\.add_parser\(\s*"([a-z-]+)""#).expect("注册表正则固定合法")
    })
}

fn dated_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^\d{4}-\d{2}-\d{2}$").expect("日期正则固定合法"))
}

/// 真源 `_cli_commands(root)`：从 `scripts/nf.py` 抽 CLI 子命令名。
fn cli_commands(root: &Path) -> BTreeSet<String> {
    let Ok(text) = std::fs::read_to_string(root.join("scripts/nf.py")) else {
        return BTreeSet::new();
    };
    add_parser_re()
        .captures_iter(&text)
        .map(|c| c[1].to_string())
        .collect()
}

/// Python `bool` 判定：`isinstance(x, bool)`。
fn is_bool(j: &Json) -> bool {
    matches!(j, Json::Bool(_))
}

/// **移植面按消费者界定**：真源 `scan` 还返回 `warns`（`status == proposed` 的提示），
/// 但契约 `_c_endpoint` **只看 issues**，故未纳入结构体——不写"没人核"的代码面
/// （与 `handover` / `state_front` / `postmortem` 同一取舍）。
pub struct EndpointScan {
    pub issues: Vec<String>,
    pub stats: Json,
}

/// 真源 `scan`。
pub fn scan(root: &Path) -> EndpointScan {
    let mut issues: Vec<String> = Vec::new();

    let doc = jsonread::read_file(root, CONTRACT_REL);
    let Some(doc) = doc else {
        return EndpointScan {
            issues: vec![format!(
                "缺端点契约 {}（修复指引：见 protocol/endpoint_contract.json）",
                CONTRACT_REL
            )],
            stats: Json::Object(Vec::new()),
        };
    };

    if py_str(get(&doc, "schema")) != SCHEMA {
        issues.push(format!("端点契约 schema 不匹配（期望 {}）", SCHEMA));
    }
    let status = py_str(get(&doc, "status"));
    if !STATUSES.contains(&status.as_str()) {
        issues.push(format!("status 越词表：{}（{}）", status, STATUSES.join("/")));
    }

    let conv = get(&doc, "conventions")
        .filter(|c| matches!(c, Json::Object(_)))
        .cloned()
        .unwrap_or_else(|| Json::Object(Vec::new()));
    let tools: BTreeSet<&str> = crate::mcp_tables::TOOL_NAMES.iter().copied().collect();
    let cmds = cli_commands(root);

    let endpoints: Vec<Json> = match get(&doc, "endpoints") {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    };
    let all_ids: Vec<String> = endpoints.iter().map(|e| py_str(get(e, "id"))).collect();

    let mut ids: BTreeSet<String> = BTreeSet::new();
    let mut paths: BTreeSet<String> = BTreeSet::new();
    for ep in &endpoints {
        let eid = py_str(get(ep, "id"));
        if ids.contains(&eid) {
            issues.push(format!("端点 id 重复：{}", eid));
        }
        ids.insert(eid.clone());
        let method = py_str(get(ep, "method"));
        let path = py_str(get(ep, "path"));
        if !METHODS.contains(&method.as_str()) {
            issues.push(format!("{} 的 method 越词表：{}", eid, method));
        }
        let key = format!("{} {}", method, path);
        if paths.contains(&key) {
            issues.push(format!("端点 method+path 重复：{}", key));
        }
        paths.insert(key);
        if py_truthy(get(ep, "streaming").unwrap_or(&Json::Null))
            && !py_truthy(get(&conv, "streaming").unwrap_or(&Json::Null))
        {
            issues.push(format!("{} 声明 streaming 但 conventions 未定义 SSE 约定", eid));
        }
        let maps = py_str(get(ep, "maps_to"));
        if let Some(c) = mcp_re().captures(&maps) {
            if !tools.contains(&c[1]) {
                issues.push(format!("{} 的 maps_to 指向不存在的 MCP 工具：{}", eid, &c[1]));
            }
        } else {
            match cli_re().captures(&maps) {
                Some(c) if cmds.contains(&c[1]) => {}
                _ => issues.push(format!(
                    "{} 的 maps_to 无法解析为现存 CLI 子命令或 MCP 工具：{}（修复指引：改正，或先实现该能力）",
                    eid, maps
                )),
            }
        }

        // 弃用/日落语义（OpenAPI deprecated + RFC 8594 Sunset）：有标志就必须有出口
        let dep = get(ep, "deprecated");
        if let Some(d) = dep {
            if !is_bool(d) {
                issues.push(format!("{} 的 deprecated 应为布尔：{}", eid, py_repr(d)));
            }
        }
        if py_truthy(dep.unwrap_or(&Json::Null)) {
            if status != "implemented" {
                issues.push(format!(
                    "{} 声明 deprecated 但契约 status={}——未实装的能力没有可弃用的东西（修复指引：先落 implemented 再谈弃用）",
                    eid, status
                ));
            }
            if !py_truthy(get(&conv, "deprecation").unwrap_or(&Json::Null)) {
                issues.push(format!("{} 声明 deprecated 但 conventions 未定义弃用约定", eid));
            }
            let sunset = py_str(get(ep, "sunset"));
            if !dated_re().is_match(&sunset) {
                issues.push(format!(
                    "{} 声明 deprecated 但缺合规 sunset（YYYY-MM-DD）：{}（修复指引：按 RFC 8594 给出日落日期）",
                    eid,
                    py_repr(get(ep, "sunset").unwrap_or(&Json::Null))
                ));
            }
            if get(ep, "replacement").is_none() {
                issues.push(format!(
                    "{} 声明 deprecated 但缺 replacement（无替代写 null，不许省略）",
                    eid
                ));
            } else {
                let rep = get(ep, "replacement").cloned().unwrap_or(Json::Null);
                if !matches!(rep, Json::Null) && !all_ids.contains(&crate::pyval::plain_str(&rep)) {
                    issues.push(format!(
                        "{} 的 replacement 指向契约内不存在的端点：{}（修复指引：改为契约内端点 id，或写 null 表示无替代）",
                        eid,
                        py_repr(&rep)
                    ));
                }
            }
        } else if get(ep, "sunset").is_some() || get(ep, "replacement").is_some() {
            issues.push(format!(
                "{} 未声明 deprecated 却带 sunset/replacement（悬空弃用字段）",
                eid
            ));
        }
    }

    // 幂等声明面（RFC 9110 §9.2.2）：默认幂等，例外须登记且非幂等端点须给幂等键策略
    if !py_truthy(get(&conv, "idempotency").unwrap_or(&Json::Null)) {
        issues.push(
            "conventions 未声明幂等语义（修复指引：按 RFC 9110 §9.2.2 写明默认幂等 + 例外登记规则——幂等性是重试安全的前提，不许沉默）"
                .to_string(),
        );
    }
    let exceptions: Vec<Json> = match get(&doc, "idempotency_exceptions") {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    };
    let mut seen_exc: BTreeSet<String> = BTreeSet::new();
    for exc in &exceptions {
        let xid = py_str(get(exc, "id"));
        if !ids.contains(&xid) {
            issues.push(format!(
                "幂等例外指向契约内不存在的端点：{}（修复指引：改为契约内端点 id，或删除该例外）",
                py_repr(&Json::Str(xid))
            ));
            continue;
        }
        if seen_exc.contains(&xid) {
            issues.push(format!("幂等例外重复登记端点：{}", xid));
        }
        seen_exc.insert(xid.clone());
        let mode = py_str(get(exc, "mode"));
        if !IDEMPOTENCY_MODES.contains(&mode.as_str()) {
            issues.push(format!(
                "幂等例外 mode 越词表：{} = {}（允许 {}）",
                xid,
                py_repr(&Json::Str(mode)),
                IDEMPOTENCY_MODES.join("/")
            ));
        } else if mode == "non-idempotent" {
            let key = py_str(get(exc, "key"));
            if !IDEMPOTENCY_KEY.contains(&key.as_str()) {
                issues.push(format!(
                    "非幂等端点 {} 缺幂等键策略（修复指引：key ∈ {}——required = 须幂等键去重；none = 明示不可重放并写 why）",
                    xid,
                    IDEMPOTENCY_KEY.join("/")
                ));
            } else if key == "required"
                && !py_truthy(get(&conv, "idempotency").unwrap_or(&Json::Null))
            {
                issues.push(format!(
                    "幂等例外要求幂等键但 conventions 未定义幂等语义：{}",
                    xid
                ));
            }
        }
        if py_str(get(exc, "why")).trim().is_empty() {
            issues.push("幂等例外缺 why（修复指引：写明为何非幂等、重放会发生什么）".to_string());
        }
    }

    let streaming = endpoints
        .iter()
        .filter(|e| py_truthy(get(e, "streaming").unwrap_or(&Json::Null)))
        .count();
    let stats = Json::Object(vec![
        ("status".to_string(), Json::Str(status)),
        ("endpoints".to_string(), Json::Int(endpoints.len() as i64)),
        ("streaming".to_string(), Json::Int(streaming as i64)),
        ("cli_commands".to_string(), Json::Int(cmds.len() as i64)),
        ("mcp_tools".to_string(), Json::Int(crate::mcp_tables::TOOL_NAMES.len() as i64)),
        (
            "idempotency_exceptions".to_string(),
            Json::Int(exceptions.len() as i64),
        ),
    ]);
    EndpointScan { issues, stats }
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_endpoint_branches.py（勿手改；重跑生成器覆盖本段）
    /// ===== 分支级差分判据（期望值由 `tools/gen_endpoint_branches.py` 从真源生成）=====
    ///
    /// 三场景：kitchen（逐分支）/ 全绿 / 缺契约。分支：schema / status 越词表 /
    /// endpoint id 重复 / method 越词表 / method+path 重复 / streaming 无 SSE 约定 /
    /// maps_to 的 MCP 工具不存在 / maps_to 无法解析为现存 CLI 子命令 /
    /// deprecated 非布尔 / deprecated 但 status≠implemented / 无弃用约定 / sunset 不合规 /
    /// 缺 replacement / replacement 指向不存在端点 / 未 deprecated 却带 sunset /
    /// conventions 未声明幂等 / 幂等例外指向不存在端点 / 重复登记 / mode 越词表 /
    /// key 越词表 / required 但无幂等语义 / 缺 why。
    ///
    /// **移植面**：真源 `scan` 还返回 warns（`status == proposed` 的提示），但契约只看 issues，
    /// 故本线结构体未纳入；`want_warns` 仅作记录。
    const EP_KITCHEN: &str = r#"{"schema": "wrong/1", "status": "越词表", "endpoints": [{"id": "e1", "method": "FETCH", "path": "/a", "maps_to": "nf nope"}, {"id": "e1", "method": "GET", "path": "/a", "streaming": true, "maps_to": "no_such_tool（MCP 工具）"}, {"id": "e3", "method": "GET", "path": "/a", "maps_to": "nf stats"}, {"id": "e4", "method": "POST", "path": "/b", "maps_to": "nf library", "deprecated": "yes", "sunset": "2026/01/01"}, {"id": "e5", "method": "POST", "path": "/c", "maps_to": "nf library", "sunset": "2026-01-01"}], "idempotency_exceptions": [{"id": "nope", "mode": "idempotent", "why": "w"}, {"id": "e3", "mode": "bogus", "why": "w"}, {"id": "e3", "mode": "idempotent", "why": "w"}, {"id": "e4", "mode": "non-idempotent", "key": "bogus", "why": ""}, {"id": "e5", "mode": "non-idempotent", "key": "required", "why": "w"}]}"#;
    const EP_GREEN: &str = r#"{"schema": "nf-endpoint/1", "status": "implemented", "conventions": {"idempotency": "默认幂等", "deprecation": "见 RFC 8594", "streaming": "SSE"}, "endpoints": [{"id": "g1", "method": "GET", "path": "/g", "maps_to": "nf stats"}, {"id": "g2", "method": "POST", "path": "/h", "maps_to": "library_read（MCP 工具）", "streaming": true}], "idempotency_exceptions": [{"id": "g2", "mode": "non-idempotent", "key": "required", "why": "重放会重复借阅"}]}"#;
    const EP_NF_PY: &str = r#"import argparse
sub = argparse.ArgumentParser().add_subparsers()
sub.add_parser("library")
sub.add_parser("stats")
"#;

    fn build_endpoint_fixture(scenario: &str, contract: Option<&str>) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("endpoint-branches-{}", scenario));
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        std::fs::create_dir_all(root.join("scripts")).unwrap();
        if let Some(c) = contract {
            std::fs::write(root.join("protocol/endpoint_contract.json"), c).unwrap();
        }
        std::fs::write(root.join("scripts/nf.py"), EP_NF_PY).unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_in_all_three_scenarios() {
        // 真源 `scan` 还返回 warns（`status == proposed` 的提示），但契约只看 issues，
        // 故本线结构体未纳入移植面——`want_warns` 仅作记录，不参与断言。
        for (scenario, contract, want_issues, want_warns, want_stats) in [
            (
                "kitchen",
                Some(EP_KITCHEN),
                &["端点契约 schema 不匹配（期望 nf-endpoint/1）", "status 越词表：越词表（proposed/implemented）", "e1 的 method 越词表：FETCH", "e1 的 maps_to 无法解析为现存 CLI 子命令或 MCP 工具：nf nope（修复指引：改正，或先实现该能力）", "端点 id 重复：e1", "e1 声明 streaming 但 conventions 未定义 SSE 约定", "e1 的 maps_to 指向不存在的 MCP 工具：no_such_tool", "端点 method+path 重复：GET /a", "e4 的 deprecated 应为布尔：'yes'", "e4 声明 deprecated 但契约 status=越词表——未实装的能力没有可弃用的东西（修复指引：先落 implemented 再谈弃用）", "e4 声明 deprecated 但 conventions 未定义弃用约定", "e4 声明 deprecated 但缺合规 sunset（YYYY-MM-DD）：'2026/01/01'（修复指引：按 RFC 8594 给出日落日期）", "e4 声明 deprecated 但缺 replacement（无替代写 null，不许省略）", "e5 未声明 deprecated 却带 sunset/replacement（悬空弃用字段）", "conventions 未声明幂等语义（修复指引：按 RFC 9110 §9.2.2 写明默认幂等 + 例外登记规则——幂等性是重试安全的前提，不许沉默）", "幂等例外指向契约内不存在的端点：'nope'（修复指引：改为契约内端点 id，或删除该例外）", "幂等例外 mode 越词表：e3 = 'bogus'（允许 idempotent/non-idempotent）", "幂等例外重复登记端点：e3", "非幂等端点 e4 缺幂等键策略（修复指引：key ∈ required/none——required = 须幂等键去重；none = 明示不可重放并写 why）", "幂等例外缺 why（修复指引：写明为何非幂等、重放会发生什么）", "幂等例外要求幂等键但 conventions 未定义幂等语义：e5"] as &[&str],
                &[] as &[&str],
                crate::pyjson::Json::Object(vec![("cli_commands".to_string(), crate::pyjson::Json::Int(2)), ("endpoints".to_string(), crate::pyjson::Json::Int(5)), ("idempotency_exceptions".to_string(), crate::pyjson::Json::Int(5)), ("mcp_tools".to_string(), crate::pyjson::Json::Int(10)), ("status".to_string(), crate::pyjson::Json::Str("越词表".to_string())), ("streaming".to_string(), crate::pyjson::Json::Int(1))]),
            ),
            ("green", Some(EP_GREEN), &[] as &[&str], &[] as &[&str], crate::pyjson::Json::Object(vec![("cli_commands".to_string(), crate::pyjson::Json::Int(2)), ("endpoints".to_string(), crate::pyjson::Json::Int(2)), ("idempotency_exceptions".to_string(), crate::pyjson::Json::Int(1)), ("mcp_tools".to_string(), crate::pyjson::Json::Int(10)), ("status".to_string(), crate::pyjson::Json::Str("implemented".to_string())), ("streaming".to_string(), crate::pyjson::Json::Int(1))])),
            ("nodecl", None, &["缺端点契约 protocol/endpoint_contract.json（修复指引：见 protocol/endpoint_contract.json）"] as &[&str], &[] as &[&str], crate::pyjson::Json::Object(vec![])),
        ] {
            let root = build_endpoint_fixture(scenario, contract);
            let got = scan(&root);
            assert_eq!(got.issues, want_issues, "场景 {} 的 issues", scenario);
            let _ = want_warns;
            // 比 JSON 语义（对象键序无关）——本线用真源字典的**插入序**，而生成器把期望值排了序，
            // 直接 `assert_eq!` 会得到**假失败**（值本就相同）。
            assert!(
                crate::jsonread::json_eq(&got.stats, &want_stats),
                "场景 {} 的 stats：实得 {:?}",
                scenario,
                got.stats
            );
        }
    }
    // <<< GENERATED
}
