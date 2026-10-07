//! 已移植的一致性契约（逐条与 Python 真源 `conformance_report.CONTRACTS` 对账）。
//!
//! **移植纪律**：每条契约必须能**单独**跑出与真源同形的 `(ok, detail)` 与内容摘要；
//! 未移植的 id 一律返回 `None`（**显式缺席**，不伪造空结论——见 ADR-0005「不伪造」）。
//!
//! 已移植：`st-quality`（真源 `core/st_quality.py`，纯 JSON，无 Python 运行时依赖）。
//! 未移植：其余 26 条（多数依赖 AST / 重型扫描器，见 `engine/rust/README.md`「覆盖现状」）。

use crate::jsonread;
use crate::pyjson::Json;
use crate::pyval::{
    arr_is_empty, arr_items, get, obj_is_empty, plain_str, plain_str_opt, py_eq, py_int_or,
    py_str, py_truthy, str_list,
};
use std::path::Path;

/// **已移植契约 id 清单**（对账门据此逐条比对，不硬编码在脚本里）。
/// 新增契约时：先在此登记，再补 `run` 的分派与判据。
pub const PORTED: [&str; 27] = [
    "audit",
    "canonical-digest-determinism",
    "decisions",
    "declaration",
    "doc-kinds",
    "endpoint-contract",
    "event-backing",
    "handover",
    "io-types",
    "knowledge-sources",
    "library-projection",
    "library-verify",
    "modeling",
    "postmortem",
    "module-signature",
    "patterns",
    "public-surface",
    "schema-clean",
    "state-front",
    "st-quality",
    "rfc-heads",
    "cognition",
    "assertions",
    "type-backlog",
    "mcp-package",
    "pipeline-dryrun",
    "purity-clean",
];

/// `CONTRACTS` 表里该 id 的说明（真源 `conformance_report.py` 逐字）。
pub fn description(id: &str) -> Option<&'static str> {
    match id {
        "audit" => Some("审计/验收（结论绑定对象 digest + 签收双要素）"),
        "canonical-digest-determinism" => Some("规范化摘要可复现"),
        "decisions" => Some("决策记录（ADR：不可改 + 取代链）"),
        "declaration" => Some("一致性声明"),
        "doc-kinds" => Some("文档四型覆盖"),
        "endpoint-contract" => Some("服务端点契约指向真实性"),
        "event-backing" => Some("全仓事件背书"),
        "handover" => Some("接力协议（SBAR 五段 + 未决带判据）"),
        "io-types" => Some("I/O 类型面（可证不匹配）"),
        "knowledge-sources" => Some("双源知识层（权威分层/查询有序/时效/溯源）"),
        "library-projection" => Some("INDEX/ALIAS 投影一致"),
        "library-verify" => Some("馆藏 frontmatter 真源"),
        "modeling" => Some("内容建模三件（词表/规范说明件/数据契约）"),
        "pipeline-dryrun" => Some("管线抽象执行零 hard 缺陷"),
        "postmortem" => Some("复盘（无指责 + 根因指向机制 + 行动项闭环）"),
        "module-signature" => Some("模块边界冻结"),
        "patterns" => Some("实践包品类"),
        "public-surface" => Some("公开导出面零泄漏"),
        "purity-clean" => Some("架构纯度零违规"),
        "schema-clean" => Some("IDL 单一真相零漂移"),
        "state-front" => Some("条件先行（登记件须通过排布判据）"),
        "type-backlog" => Some("类型积压显式化"),
        "mcp-package" => Some("B 线包装声明（工具面与运行时一致）"),
        "st-quality" => Some("ST 制卡质量规范（M/S/R 数据化 + 落产物判）"),
        "rfc-heads" => Some("协议件版本史头"),
        "cognition" => Some("认知族（术语表 + 执行分档）"),
        "assertions" => Some("数据化断言表（形状类断言数据化）"),
        _ => None,
    }
}

/// 跑一条已移植契约 → `(ok, detail)`；未移植 → `None`。
pub fn run(id: &str, root: &Path) -> Option<(bool, String)> {
    match id {
        "audit" => Some(audit_contract(root)),
        "canonical-digest-determinism" => Some(canonical_determinism()),
        "decisions" => Some(decisions(root)),
        "declaration" => Some(declaration(root)),
        "doc-kinds" => Some(doc_kinds(root)),
        "endpoint-contract" => Some(endpoint_contract(root)),
        "event-backing" => Some(event_backing(root)),
        "handover" => Some(handover(root)),
        "io-types" => Some(io_types_contract(root)),
        "knowledge-sources" => Some(knowledge_sources(root)),
        "library-projection" => Some(library_projection(root)),
        "library-verify" => Some(library_verify(root)),
        "modeling" => Some(modeling(root)),
        "pipeline-dryrun" => Some(pipeline_dryrun(root)),
        "postmortem" => Some(postmortem(root)),
        "module-signature" => Some(module_signature(root)),
        "patterns" => Some(patterns(root)),
        "public-surface" => Some(crate::public_surface::contract(root)),
        "purity-clean" => Some(purity_clean(root)),
        "schema-clean" => Some(schema_clean(root)),
        "state-front" => Some(state_front(root)),
        "type-backlog" => Some(type_backlog(root)),
        "mcp-package" => Some(mcp_package(root)),
        "st-quality" => Some(st_quality(root)),
        "rfc-heads" => Some(rfc_heads(root)),
        "cognition" => Some(cognition(root)),
        "assertions" => Some(assertions(root)),
        _ => None,
    }
}

/// 真源 `_c_declaration`：声明版本数 · scope 数 · 排除数。
fn declaration(root: &Path) -> (bool, String) {
    let s = crate::declaration::scan(root);
    let ok = s.issues.is_empty();
    let detail = if ok {
        format!("版本 {} · scope {} · 排除 {}", s.versions, s.scope, s.excluded)
    } else {
        s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_decisions`：决策条数 · accepted · 取代链 + 投影一致。
fn decisions(root: &Path) -> (bool, String) {
    let (mut issues, n, accepted, chains) = crate::decisions::scan(root);
    issues.extend(crate::decisions::check_projection(root));
    let ok = issues.is_empty();
    let detail = if ok {
        format!("决策 {} 条（accepted {} · 取代链 {}）", n, accepted, chains)
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_mcp_package`：工具数 · 提示数 · 类目 · 目标平台数。
fn mcp_package(root: &Path) -> (bool, String) {
    let s = crate::mcp_package::scan(root);
    let ok = s.issues.is_empty();
    let g = |k: &str| match crate::pyval::get(&s.stats, k) {
        Some(Json::Int(n)) => *n,
        _ => 0,
    };
    let detail = if ok {
        format!(
            "工具 {} · 提示 {} · 类目 {} · 目标平台 {}",
            g("tools"),
            g("prompts"),
            crate::mcp_package::category_or_unknown(&s.stats),
            g("targets")
        )
    } else {
        s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_pipeline_dryrun`：管线条数 · advisory 数。
///
/// ⚠️ 真源 `sweep` **不接** `graph` 抛的 `ValueError`，异常由契约跑者包成
/// `契约执行异常：<exc>`（`ok=false`）；本线让 `sweep` 返回 `Err(消息)` 并拼成**同一句**——
/// 这条可逐字复刻，故不当作"已知偏差"。
fn pipeline_dryrun(root: &Path) -> (bool, String) {
    match crate::pipelinerun::sweep(root) {
        Ok(s) => {
            let ok = s.issues.is_empty();
            let detail = if ok {
                format!("管线 {} 条零 hard 缺陷（advisory {}）", s.pipelines, s.notes)
            } else {
                s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
            };
            (ok, detail)
        }
        Err(e) => (false, format!("契约执行异常：{}", e)),
    }
}

/// 真源 `_c_type_backlog`：不可推断 untyped 项数（台账同步）。
fn type_backlog(root: &Path) -> (bool, String) {
    let (issues, stats) = crate::payload_harvest::verify_backlog(root);
    let ok = issues.is_empty();
    let n = match crate::pyval::get(&stats, "untyped") {
        Some(Json::Int(v)) => *v,
        _ => 0,
    };
    let detail = if ok {
        format!("不可推断 untyped {} 项（台账同步）", n)
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_purity`：纯度零违规。
fn purity_clean(root: &Path) -> (bool, String) {
    let (issues, _stats) = crate::purity::scan(root);
    let ok = issues.is_empty();
    let detail = if ok {
        "纯度零违规".to_string()
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_io_types`：可证不匹配数 · 类型覆盖率（一位小数）。
///
/// 真源分别调 `scan` 与 `coverage`（后者内部**再跑一遍 scan**）；本线一次扫描供两处用。
fn io_types_contract(root: &Path) -> (bool, String) {
    let (s, cov) = crate::io_types::coverage(root);
    let ok = s.issues.is_empty();
    let g = |k: &str| match crate::pyval::get(&s.stats, k) {
        Some(Json::Int(n)) => *n,
        _ => 0,
    };
    let typed = g("typed_fields");
    let untyped = g("untyped_fields");
    let detail = if ok {
        // Python `%.1f`：一位小数、正确舍入（出口与真源逐字节比对守住这一条）
        format!(
            "可证不匹配 {} · 类型覆盖 {:.1}%（{}/{} 字段）",
            s.issues.len(),
            cov,
            typed,
            typed + untyped
        )
    } else {
        s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_endpoint`：端点条数 · status。
fn endpoint_contract(root: &Path) -> (bool, String) {
    let e = crate::endpoint::scan(root);
    let ok = e.issues.is_empty();
    let gs = |k: &str, dflt: &str| match crate::pyval::get(&e.stats, k) {
        Some(crate::pyjson::Json::Str(s)) => s.clone(),
        _ => dflt.to_string(),
    };
    let gn = |k: &str| match crate::pyval::get(&e.stats, k) {
        Some(crate::pyjson::Json::Int(n)) => *n,
        _ => 0,
    };
    let detail = if ok {
        format!("端点 {}（status={}）", gn("endpoints"), gs("status", "?"))
    } else {
        e.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_knowledge`：源（合同/参考）· 消化记录 · 频次事件。
///
/// 真源把**三条**判据的 issues 合并：`scan` + `verify_transform` + `verify_usage`；
/// 而 detail 只取 `scan` 的 stats + `verify_usage` 的 `events`。
fn knowledge_sources(root: &Path) -> (bool, String) {
    let k = crate::knowledge::scan(root);
    let mut issues = k.issues;
    issues.extend(crate::knowledge::verify_transform(root).issues);
    let usage = crate::knowledge::verify_usage(root);
    issues.extend(usage.issues.clone());
    let gi = |j: &Json, key: &str| match crate::pyval::get(j, key) {
        Some(Json::Int(n)) => *n,
        _ => 0,
    };
    let detail = if issues.is_empty() {
        format!(
            "源 {}（合同 {} / 参考 {}）· 消化记录 {} · 频次事件 {}",
            gi(&k.stats, "sources"),
            gi(&k.stats, "contract"),
            gi(&k.stats, "reference"),
            gi(&k.stats, "transforms"),
            gi(&usage.stats, "events")
        )
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (issues.is_empty(), detail)
}

/// 真源 `_c_audit`：审计件数 · 带审计头 · legacy · 绑定对象数。
fn audit_contract(root: &Path) -> (bool, String) {
    let a = crate::audit::scan(root);
    let ok = a.issues.is_empty();
    let g = |k: &str| match crate::pyval::get(&a.stats, k) {
        Some(Json::Int(n)) => *n,
        _ => 0,
    };
    let detail = if ok {
        format!(
            "审计 {} 件（带审计头 {} · legacy {}）· 绑定对象 {}",
            g("audits"), g("with_header"), g("legacy"), g("subjects_ok")
        )
    } else {
        a.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_library_projection`：投影一致（只看 issues）。
fn library_projection(root: &Path) -> (bool, String) {
    let issues = crate::library::check_projection(root);
    let ok = issues.is_empty();
    let detail = if ok {
        "投影一致".to_string()
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_library_verify`：馆藏 frontmatter 真源零 FAIL（只看 issues）。
fn library_verify(root: &Path) -> (bool, String) {
    let issues = crate::library::verify(root).issues;
    let ok = issues.is_empty();
    let detail = if ok {
        "馆藏 frontmatter 真源零 FAIL".to_string()
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_schema`：IDL 单一真相零漂移。
fn schema_clean(root: &Path) -> (bool, String) {
    let (issues, stats) = crate::schema_lint::scan(root);
    let ok = issues.is_empty();
    let detail = if ok {
        // 真源 `len(stats)` 取的是 stats 字典的**键数**（恒为 6），不是某个计数
        format!("schema 零漂移（{} 类件）", 6)
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    let _ = stats;
    (ok, detail)
}

/// 真源 `_c_patterns`：格式 + 可证 + 投影一致。
fn patterns(root: &Path) -> (bool, String) {
    let (mut issues, n) = crate::patterns::scan_issues(root);
    issues.extend(crate::patterns::check_projection(root));
    let ok = issues.is_empty();
    let detail = if ok {
        format!("实践包 {} 条（格式/可证/投影）", n)
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_handover`：交接件数 · 未决条数。
fn handover(root: &Path) -> (bool, String) {
    let s = crate::handover::scan(root);
    let ok = s.issues.is_empty();
    let detail = if ok {
        format!("交接件 {} 件 · 未决 {} 条", s.handovers, s.pending)
    } else {
        s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_postmortem`：复盘件数 · 行动项条数。
fn postmortem(root: &Path) -> (bool, String) {
    let s = crate::postmortem::scan(root);
    let ok = s.issues.is_empty();
    let detail = if ok {
        format!("复盘 {} 件 · 行动项 {} 条", s.postmortems, s.actions)
    } else {
        s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_modeling`：词表 · 规范/说明件 · 数据契约。
fn modeling(root: &Path) -> (bool, String) {
    let s = crate::modeling::scan(root);
    let ok = s.issues.is_empty();
    let detail = if ok {
        format!(
            "词表 {} · 规范件 {} / 说明件 {} · 数据契约 {}",
            s.schemes, s.normative, s.informative_files, s.contracts
        )
    } else {
        s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_event_backing`：事件数 · 跨包数 · 挂账数（挂账 = 已登记为外部通道、无仓内发布方）。
fn event_backing(root: &Path) -> (bool, String) {
    let s = crate::registry_cross::scan(root);
    let ok = s.issues.is_empty();
    let detail = if ok {
        format!("事件 {} · 跨包 {} · 挂账 {}", s.events, s.cross_pkg, s.allowlisted)
    } else {
        s.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_module_signature`：模块边界零漂移。
fn module_signature(root: &Path) -> (bool, String) {
    let issues = crate::module_signature::verify_issues(root);
    let ok = issues.is_empty();
    let detail = if ok {
        "模块边界零漂移".to_string()
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_doc_kinds`：四型覆盖（issues）+ 写法（warns 只计数进 detail）。
fn doc_kinds(root: &Path) -> (bool, String) {
    let issues = crate::doc_hygiene::kind_coverage();
    let warns = crate::doc_hygiene::kind_rules(root);
    let ok = issues.is_empty();
    let detail = if ok {
        format!("四型全覆盖 · 写法 WARN {}", warns.len())
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

/// 真源 `_c_canonical`：同一对象**换键序**后规范摘要必须一致。
///
/// 真源口径 = `attest.canonical` = `json.dumps(sort_keys=True, ensure_ascii=False,
/// separators=(",",":"))` —— 与 `pyjson::dumps_compact` **同式**，故本线直接复用它。
/// 这条判据是"所有溯源的地基"：键序若渗进摘要，整个证据链就不可复现。
fn canonical_determinism() -> (bool, String) {
    let a = Json::Object(vec![
        ("b".to_string(), Json::Int(2)),
        ("a".to_string(), Json::Int(1)),
    ])
    .dumps_compact();
    let b = Json::Object(vec![
        ("a".to_string(), Json::Int(1)),
        ("b".to_string(), Json::Int(2)),
    ])
    .dumps_compact();
    if a == b {
        (true, "canonical digest 两遍一致".to_string())
    } else {
        (false, "不一致".to_string())
    }
}

// ---------------------------------------------------------------- st-quality

const ST_REL: &str = "protocol/st_quality.json";
const ST_SCHEMA: &str = "nf-st-quality/1";
const ST_ARTIFACT_REL: &str = "docs/examples/mvu-output/mvu_variables.json";

/// 真源 `_c_st_quality`：把 `st_quality.scan` 的三元组压成契约裁决。
fn st_quality(root: &Path) -> (bool, String) {
    match st_quality_scan(root) {
        Ok((issues, _warns, stats)) => {
            let ok = issues.is_empty();
            let detail = if ok {
                let lv = |k: &str| stats.by_level.iter().find(|(n, _)| n == k).map(|(_, v)| *v).unwrap_or(0);
                format!(
                    "规则 {} 条（M {} / S {} / R {}）· 落产物判 {}",
                    stats.rules,
                    lv("M"),
                    lv("S"),
                    lv("R"),
                    stats.artifact_checked
                )
            } else {
                issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
            };
            (ok, detail)
        }
        // 真源此处由 `_run_impl` 的 except 兜住。**错误路径的措辞不做逐字节承诺**：
        // 只在输入损坏（非法 JSON / 非对象）时可达，当前语料走不到。
        Err(e) => (false, format!("契约执行异常：{}", e)),
    }
}

#[derive(Default, Clone, Debug)]
struct StStats {
    rules: usize,
    by_level: Vec<(String, i64)>,
    artifact_checked: usize,
}

/// 真源 `st_quality.scan` 的等价物。
fn st_quality_scan(root: &Path) -> Result<(Vec<String>, Vec<String>, StStats), String> {
    let mut issues: Vec<String> = Vec::new();
    let mut warns: Vec<String> = Vec::new();
    let mut stats = StStats::default();

    let path = root.join(ST_REL);
    if !path.is_file() {
        return Ok((vec![format!("缺 ST 制卡质量规范 {}", ST_REL)], warns, stats));
    }
    let d = jsonread::read_file(root, ST_REL).ok_or_else(|| format!("{} 不是合法 JSON", ST_REL))?;
    let Json::Object(_) = &d else { return Err(format!("{} 不是对象", ST_REL)) };
    if obj_is_empty(&d) {
        // 真源 `if not d:` —— 空对象与缺件同判
        return Ok((vec![format!("缺 ST 制卡质量规范 {}", ST_REL)], warns, stats));
    }

    if py_str(get(&d, "schema")) != ST_SCHEMA {
        issues.push(format!("规范 schema 不匹配（期望 {}）", ST_SCHEMA));
    }

    let levels = str_list(get(&d, "level_vocabulary"));
    let scopes = str_list(get(&d, "scope_vocabulary"));
    let checks = str_list(get(&d, "check_vocabulary"));
    if levels != ["M", "S", "R"] {
        issues.push("level 词表必须为 M/S/R".into());
    }
    if scopes != ["C", "W", "V", "X"] {
        issues.push("scope 词表必须为 C/W/V/X".into());
    }
    if checks != ["declaration", "artifact"] {
        issues.push("check 词表必须为 declaration/artifact".into());
    }
    if py_str(get(&d, "status")) == "draft" && arr_is_empty(get(&d, "pending")) {
        issues.push("status=draft 但 pending 为空——草案必须写明还差什么".into());
    }

    let mut seen: Vec<String> = Vec::new();
    for k in &levels {
        if !stats.by_level.iter().any(|(n, _)| n == k) {
            stats.by_level.push((k.clone(), 0));
        }
    }
    let mut arts: Vec<String> = Vec::new();
    for r in arr_items(get(&d, "rules")) {
        let rid = py_str(get(r, "id"));
        let tag = if rid.is_empty() { "(无名)".to_string() } else { rid.clone() };
        if seen.contains(&rid) {
            issues.push(format!("规则 id 重复：{}", rid));
        }
        seen.push(rid.clone());
        let scope = py_str(get(r, "scope"));
        if !scopes.contains(&scope) {
            issues.push(format!("{} scope 越词表：{}", tag, scope));
        } else if !rid.is_empty() && !rid.starts_with(&scope) {
            issues.push(format!("{} 的 id 前缀与 scope 不一致（应 {} 开头）", tag, scope));
        }
        let lv = py_str(get(r, "level"));
        if !levels.contains(&lv) {
            issues.push(format!("{} level 越词表：{}", tag, lv));
        } else if let Some(slot) = stats.by_level.iter_mut().find(|(n, _)| *n == lv) {
            slot.1 += 1;
        }
        for k in ["rule", "basis", "check"] {
            if py_str(get(r, k)).trim().is_empty() {
                issues.push(format!("{} 缺必填字段：{}", tag, k));
            }
        }
        if py_str(get(r, "check")) == "artifact" {
            arts.push(rid);
        }
    }
    for rid in &arts {
        if rid == "V2" {
            issues.extend(check_v2(root));
        }
    }
    issues.extend(check_checklist(root, &d));
    if !arr_is_empty(get(&d, "pending")) {
        let p = arr_items(get(&d, "pending"));
        let head: Vec<String> = p.iter().take(2).map(|v| py_str(Some(v))).collect();
        warns.push(format!("规范为草案：{} 项待补（{}）", p.len(), head.join("；")));
    }
    stats.rules = seen.len();
    stats.artifact_checked = arts.len();
    Ok((issues, warns, stats))
}

/// 真源 `_check_v2`：`initial` 键集合必须 ⊆ 变量名集合。
fn check_v2(root: &Path) -> Vec<String> {
    let path = root.join(ST_ARTIFACT_REL);
    if !path.is_file() {
        return Vec::new();
    }
    let Some(doc) = jsonread::read_file(root, ST_ARTIFACT_REL) else {
        return Vec::new();
    };
    // 真源 `str(v.get("name"))` **没有** `or ""` 兜底 ⇒ 缺 name 时是字面量 "None"
    let names: Vec<String> = arr_items(get(&doc, "variables"))
        .iter()
        .map(|v| match get(v, "name") {
            Some(Json::Str(s)) => s.clone(),
            Some(Json::Null) | None => "None".to_string(),
            Some(other) => py_str(Some(other)),
        })
        .collect();
    let init = match get(&doc, "initial") {
        Some(Json::Object(p)) => p.clone(),
        _ => Vec::new(),
    };
    let mut extra: Vec<String> = init
        .iter()
        .map(|(k, _)| k.clone())
        .filter(|k| !names.contains(k))
        .collect();
    extra.sort();
    if extra.is_empty() {
        Vec::new()
    } else {
        vec![format!("V2：初始值含未声明变量 {}（initial 与变量表不一一对应）", extra.join("、"))]
    }
}

/// 真源 `_check_checklist`：清单必须覆盖全部规则 id。
fn check_checklist(root: &Path, d: &Json) -> Vec<String> {
    let rel = py_str(get(d, "checklist"));
    if rel.is_empty() {
        return vec!["缺 checklist 字段——人工自查清单必须登记（否则 S 级规则无处落地）".into()];
    }
    let path = root.join(&rel);
    if !path.is_file() {
        return vec![format!("自查清单不存在：{}", rel)];
    }
    let Ok(text) = std::fs::read_to_string(&path) else {
        return vec![format!("自查清单不存在：{}", rel)];
    };
    let mut miss: Vec<String> = Vec::new();
    for r in arr_items(get(d, "rules")) {
        // 真源 `str(r.get("id"))`：缺 id → "None"（真值）⇒ 会去找 "| None |"
        let rid = match get(r, "id") {
            Some(Json::Str(s)) => s.clone(),
            Some(Json::Null) | None => "None".to_string(),
            Some(other) => py_str(Some(other)),
        };
        if !rid.is_empty() && !text.contains(&format!("| {} |", rid)) {
            miss.push(rid);
        }
    }
    if miss.is_empty() {
        Vec::new()
    } else {
        vec![format!("自查清单未覆盖规则：{}", miss.join("、"))]
    }
}

// ---------------------------------------------------------------- rfc-heads

const RFC_INDEX_REL: &str = "protocol/rfc_index.json";
const RFC_CATEGORIES: [&str; 4] =
    ["Standards Track", "Informational", "Experimental", "Process"];
/// 真源头格式用的分隔符与占位符（`—` 是 U+2014，不是 `-`）。
const DASHES: [&str; 2] = ["—", "-"];

/// 真源 `_c_rfc_heads`：协议件 RFC 头 + supersede 链。
fn rfc_heads(root: &Path) -> (bool, String) {
    let (issues, stats) = rfc_scan(root);
    let ok = issues.is_empty();
    let detail = if ok {
        format!("RFC 件 {} · 链 {}", stats.docs, stats.chains)
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

#[derive(Default, Clone, Debug)]
struct RfcStats {
    docs: usize,
    chains: usize,
}

struct RfcHead {
    rfc: String,
    cat: String,
    date: String,
    status: String,
    supby: String,
    last_updated: String,
}

fn rfc_head_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(concat!(
            r"\*\*RFC\*\*:\s*(?P<rfc>NF-\d{4})\s*·\s*\*\*Category\*\*:\s*(?P<cat>[^·]+?)\s*·\s*",
            r"\*\*Date\*\*:\s*(?P<date>[\d-]+)\s*·\s*\*\*Status\*\*:\s*(?P<status>[^·]+?)\s*·\s*",
            r"\*\*Supersedes\*\*:\s*(?P<sup>[^·]+?)\s*·\s*\*\*Superseded by\*\*:\s*(?P<supby>[^·\n]+)"
        ))
        .expect("RFC 头正则固定合法")
    })
}

fn rfc_updated_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r">\s*最后更新：\s*([\d-]+)").expect("「最后更新」正则固定合法")
    })
}

/// 真源 `parse_head`：只取文档头 8 行内的 RFC 头。
fn parse_head(text: &str) -> Option<RfcHead> {
    let head = text.lines().take(8).collect::<Vec<_>>().join("\n");
    let caps = rfc_head_re().captures(&head)?;
    let g = |n: &str| {
        caps.name(n).map(|m| m.as_str().trim().to_string()).unwrap_or_default()
    };
    Some(RfcHead {
        rfc: g("rfc"),
        cat: g("cat"),
        date: g("date"),
        status: g("status"),
        supby: g("supby"),
        last_updated: rfc_updated_re()
            .captures(&head)
            .map(|c| c[1].to_string())
            .unwrap_or_default(),
    })
}

/// 真源 `rfc.scan` 的等价物。
///
/// **未计算 `stats["statuses"]`**：真源算了它，但**全仓无消费者**，且对本契约的
/// `(ok, detail)` 与内容摘要均无影响。若日后他面要用，需在此补回。
fn rfc_scan(root: &Path) -> (Vec<String>, RfcStats) {
    let mut issues: Vec<String> = Vec::new();
    let mut stats = RfcStats::default();
    let missing = || format!("缺 RFC 索引 {}（修复指引：见 protocol/rfc_index.json）", RFC_INDEX_REL);

    if !root.join(RFC_INDEX_REL).is_file() {
        return (vec![missing()], stats);
    }
    let Some(idx) = jsonread::read_file(root, RFC_INDEX_REL) else {
        return (vec![missing()], stats);
    };
    if obj_is_empty(&idx) {
        return (vec![missing()], stats);
    }

    let mut vocab = str_list(get(&idx, "status_vocabulary"));
    if vocab.is_empty() {
        vocab.push("Active".to_string());
    }

    let mut seen: Vec<(String, String)> = Vec::new(); // rfc → rel（真源 dict：按 rfc 去重）
    let mut supby: Vec<(String, String)> = Vec::new(); // rfc → 被取代者

    for item in arr_items(get(&idx, "docs")) {
        let rel = py_str(get(item, "path"));
        let rfc = py_str(get(item, "rfc"));
        let p = root.join(&rel);
        if !p.is_file() {
            issues.push(format!("RFC 索引指向不存在的文档：{}", rel));
            continue;
        }
        if let Some(slot) = seen.iter_mut().find(|(r, _)| *r == rfc) {
            issues.push(format!("RFC 编号重复：{}（{} 与 {}）", rfc, slot.1, rel));
            slot.1 = rel.clone(); // 真源 `seen[rfc] = rel` 覆盖
        } else {
            seen.push((rfc.clone(), rel.clone()));
        }

        let text = std::fs::read_to_string(&p).unwrap_or_default();
        let Some(head) = parse_head(&text) else {
            issues.push(format!("{} 缺 RFC 头（修复指引：见 docs 或 core/rfc.py 头格式）", rel));
            continue;
        };
        if head.rfc != rfc {
            issues.push(format!("{} 头部 RFC 与索引不一致：头={} 索引={}", rel, head.rfc, rfc));
        }
        if !RFC_CATEGORIES.contains(&head.cat.as_str()) {
            issues.push(format!(
                "{} Category 越词表：{}（{}）",
                rel,
                head.cat,
                RFC_CATEGORIES.join("/")
            ));
        }
        if !vocab.contains(&head.status) {
            issues.push(format!("{} Status 越词表：{}（{}）", rel, head.status, vocab.join("/")));
        }
        if !head.last_updated.is_empty() && head.date != head.last_updated {
            issues.push(format!(
                "{} Date 与「最后更新」不一致：RFC={} 最后更新={}",
                rel, head.date, head.last_updated
            ));
        }
        let cat_idx = py_str(get(item, "category"));
        if !cat_idx.is_empty() && cat_idx != head.cat {
            issues.push(format!(
                "{} Category 索引与头部不一致：索引={} 头={}",
                rel, cat_idx, head.cat
            ));
        }
        let is_blank = DASHES.contains(&head.supby.as_str()) || head.supby.is_empty();
        if head.status == "Superseded" && is_blank {
            issues.push(format!("{} 标记 Superseded 但缺 Superseded by", rel));
        }
        if !is_blank {
            if let Some(slot) = supby.iter_mut().find(|(r, _)| *r == rfc) {
                slot.1 = head.supby.clone();
            } else {
                supby.push((rfc.clone(), head.supby.clone()));
            }
        }
    }

    for (rfc, target) in &supby {
        if !seen.iter().any(|(r, _)| r == target) {
            issues.push(format!("{} 的 Superseded by 指向不在册的编号：{}", rfc, target));
            continue;
        }
        let mut cur = target.clone();
        let mut hops = 0usize;
        while let Some((_, next)) = supby.iter().find(|(r, _)| r == &cur) {
            if hops >= supby.len() + 1 {
                break;
            }
            cur = next.clone();
            hops += 1;
            if cur == *rfc {
                issues.push(format!("supersede 链成环：{} → … → {}", rfc, rfc));
                break;
            }
        }
    }

    stats.docs = seen.len();
    stats.chains = supby.len();
    (issues, stats)
}

// ---------------------------------------------------------------- cognition

const GLOSSARY_REL: &str = "protocol/glossary.json";
const MODES_REL: &str = "protocol/execution_modes.json";
const G_SCHEMA: &str = "nf-glossary/1";
const M_SCHEMA: &str = "nf-execution-modes/1";

/// 真源 `_c_cognition`：术语表 + 执行分档。
fn cognition(root: &Path) -> (bool, String) {
    let (issues, g, m) = cognition_scan(root);
    let ok = issues.is_empty();
    let detail = if ok {
        format!(
            "术语 {} 条（使用面 {}）· 执行档 {}（合格实例 {}）",
            g.terms, g.uses, m.modes, m.instances_ok
        )
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

#[derive(Default, Clone, Debug)]
struct GlossaryStats {
    terms: usize,
    uses: usize,
}

#[derive(Default, Clone, Debug)]
struct ModesStats {
    modes: usize,
    instances_ok: usize,
}

/// 真源 `cognition.scan`。真源里那条 `_BLOCK` 正则**从未被使用**（真源自身的死代码），
/// 本线不移植——移植死代码等于把噪声固化。
fn cognition_scan(root: &Path) -> (Vec<String>, GlossaryStats, ModesStats) {
    let (gi, _, gs) = verify_glossary(root);
    let (mi, _, ms) = verify_modes(root);
    let mut issues = gi;
    issues.extend(mi);
    (issues, gs, ms)
}

fn doc_or_missing(root: &Path, rel: &str, missing_msg: String) -> Result<Json, Vec<String>> {
    if !root.join(rel).is_file() {
        return Err(vec![missing_msg]);
    }
    match jsonread::read_file(root, rel) {
        Some(d) if !obj_is_empty(&d) => Ok(d),
        _ => Err(vec![missing_msg]),
    }
}

/// 真源 `verify_glossary`。
fn verify_glossary(root: &Path) -> (Vec<String>, Vec<String>, GlossaryStats) {
    let mut issues: Vec<String> = Vec::new();
    let mut stats = GlossaryStats::default();
    let Ok(doc) = doc_or_missing(root, GLOSSARY_REL, format!("缺术语表 {}", GLOSSARY_REL)) else {
        return (vec![format!("缺术语表 {}", GLOSSARY_REL)], Vec::new(), stats);
    };
    if py_str(get(&doc, "schema")) != G_SCHEMA {
        issues.push(format!("术语表 schema 不匹配（期望 {}）", G_SCHEMA));
    }
    if arr_items(get(&doc, "rules")).is_empty() {
        issues.push("术语表 rules 不得为空（登记纪律必须成文）".into());
    }
    let mut seen: Vec<String> = Vec::new();
    let mut uses = 0usize;
    for t in arr_items(get(&doc, "terms")) {
        let term = py_str(get(t, "term"));
        if term.is_empty() {
            issues.push("存在无 term 的条目".into());
            continue;
        }
        if seen.contains(&term) {
            issues.push(format!("术语重复：{}", term));
        }
        seen.push(term.clone());
        if py_str(get(t, "definition")).trim().is_empty() {
            issues.push(format!("术语 {} 缺 definition", term));
        }
        let src = py_str(get(t, "source"));
        if !root.join(&src).is_file() {
            issues.push(format!("术语 {} 的 source 不存在：{}", term, src));
        } else if !read_text(root, &src).contains(&term) {
            issues.push(format!(
                "术语 {} 未在其 source 中逐字出现：{}（定义必须落在真源里）",
                term, src
            ));
        }
        // 真源 `ui = t.get("used_in") or []` → 空串按假值落空表（不是「一项空路径」）
        let ui: Vec<String> = match get(t, "used_in") {
            Some(Json::Str(s)) if !s.is_empty() => vec![s.clone()],
            Some(Json::Array(a)) => a.iter().map(|v| plain_str(v)).collect(),
            _ => Vec::new(),
        };
        for rel in ui {
            if !root.join(&rel).is_file() {
                issues.push(format!("术语 {} 的 used_in 不存在：{}", term, rel));
            } else if !read_text(root, &rel).contains(&term) {
                issues.push(format!(
                    "术语 {} 的 used_in 未逐字出现该术语：{}（防登记没人用的行话）",
                    term, rel
                ));
            } else {
                uses += 1;
            }
        }
    }
    stats.terms = seen.len();
    stats.uses = uses;
    (issues, Vec::new(), stats)
}

/// 真源 `verify_modes`。
fn verify_modes(root: &Path) -> (Vec<String>, Vec<String>, ModesStats) {
    let mut issues: Vec<String> = Vec::new();
    let mut stats = ModesStats::default();
    let Ok(doc) = doc_or_missing(root, MODES_REL, format!("缺执行分档声明 {}", MODES_REL)) else {
        return (vec![format!("缺执行分档声明 {}", MODES_REL)], Vec::new(), stats);
    };
    if py_str(get(&doc, "schema")) != M_SCHEMA {
        issues.push(format!("执行分档 schema 不匹配（期望 {}）", M_SCHEMA));
    }
    let mut seen: Vec<String> = Vec::new();
    let mut insts = 0usize;
    for m in arr_items(get(&doc, "modes")) {
        let mid = py_str(get(m, "id"));
        if seen.contains(&mid) {
            issues.push(format!("mode id 重复：{}", mid));
        }
        seen.push(mid.clone());
        // 真源此处是 `str(b)`（无 falsy 兜底），故用 plain_str
        let blocks: Vec<String> = arr_items(get(m, "required_blocks"))
            .iter()
            .map(|b| plain_str(b))
            .collect();
        if blocks.is_empty() {
            issues.push(format!("mode {} 缺 required_blocks（该档必备结构必须成文）", mid));
        }
        let rows = arr_items(get(m, "instances"));
        if rows.is_empty() {
            issues.push(format!("mode {} 无实例（声明了档却没有件属于它）", mid));
        }
        for rel in rows.iter().map(|v| plain_str(v)) {
            if !root.join(&rel).is_file() {
                issues.push(format!("mode {} 的实例不存在：{}", mid, rel));
                continue;
            }
            let txt = read_text(root, &rel);
            let miss: Vec<String> = blocks.iter().filter(|b| !txt.contains(*b)).cloned().collect();
            if miss.is_empty() {
                insts += 1;
            } else {
                issues.push(format!(
                    "实例 {} 不属于 {} 档：缺结构块 {}",
                    rel,
                    mid,
                    miss.join("/")
                ));
            }
        }
    }
    stats.modes = seen.len();
    stats.instances_ok = insts;
    (issues, Vec::new(), stats)
}

fn read_text(root: &Path, rel: &str) -> String {
    std::fs::read_to_string(root.join(rel)).unwrap_or_default()
}

// ---------------------------------------------------------------- state-front

const STATE_FRONT_REL: &str = "protocol/state_front.json";
const STATE_FRONT_SCHEMA: &str = "nf-state-front/1";
const STATE_HEAD: &str = "## 状态块（条件先行摘要）";

/// 真源 `_c_state_front`：凡登记为 condition-first 的产物件，必须真的通过 `check_order`。
fn state_front(root: &Path) -> (bool, String) {
    let (issues, stats) = state_front_scan(root);
    let ok = issues.is_empty();
    let detail = if ok {
        format!(
            "单件 {} · 族规则 {} · 族成员 {}",
            stats.declared, stats.family_rules, stats.family_members
        )
    } else {
        issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

#[derive(Default, Clone, Debug)]
struct StateFrontStats {
    declared: usize,
    family_rules: usize,
    family_members: usize,
}

fn section_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    // 真源 `re.compile(r"^##\s+", re.M)` → Rust 的 (?m)
    RE.get_or_init(|| regex::Regex::new(r"(?m)^##\s+").expect("二级小节正则固定合法"))
}

/// 真源 `check_order`：状态块存在且位于**所有其它二级小节之前**。
fn check_order(text: &str) -> Vec<String> {
    let Some(pos) = text.find(STATE_HEAD) else {
        return vec!["缺状态块——无状态文本代理可前置".into()];
    };
    let before = section_re()
        .find_iter(text)
        .filter(|m| m.start() < pos && !text[m.start()..].starts_with("## 状态块"))
        .count();
    if before > 0 {
        vec![format!(
            "状态块未前置：它出现在 {} 个二级小节之后（条件先行要求置于资料之前）",
            before
        )]
    } else {
        Vec::new()
    }
}

/// 真源 `state_front.scan`（其 `warns` 无消费者，本线不计）。
fn state_front_scan(root: &Path) -> (Vec<String>, StateFrontStats) {
    let mut issues: Vec<String> = Vec::new();
    let mut stats = StateFrontStats::default();
    if !root.join(STATE_FRONT_REL).is_file() {
        return (vec![format!("缺条件先行声明 {}", STATE_FRONT_REL)], stats);
    }
    let Some(doc) = jsonread::read_file(root, STATE_FRONT_REL) else {
        return (vec![format!("缺条件先行声明 {}", STATE_FRONT_REL)], stats);
    };
    if py_str(get(&doc, "schema")) != STATE_FRONT_SCHEMA {
        issues.push("声明 schema 不匹配（期望 nf-state-front/1）".into());
    }
    let rows = arr_items(get(&doc, "declared"));
    let rules = arr_items(get(&doc, "family_rules"));

    let mut hits: Vec<String> = Vec::new();
    for r in &rules {
        let g = py_str(get(r, "glob"));
        if g.is_empty() {
            issues.push("族规则缺 glob".into());
            continue;
        }
        let matched = crate::glob::expand(root, &g);
        let low = py_int_or(get(r, "min_members"), 1).max(0) as usize;
        if matched.len() < low {
            issues.push(format!(
                "族 {} 成员不足：{} < {}（修复指引：按 sources 重新生成）",
                g,
                matched.len(),
                low
            ));
        }
        hits.extend(matched);
    }
    for rel in &hits {
        let bad = check_order(&read_text(root, rel));
        if !bad.is_empty() {
            issues.push(format!("族内件未通过 condition-first：{}（{}）", rel, bad[0]));
        }
    }
    for r in &rows {
        let rp = py_str(get(r, "path"));
        if rp.is_empty() {
            issues.push("声明条目缺 path".into());
            continue;
        }
        if !root.join(&rp).is_file() {
            issues.push(format!("登记件不存在：{}", rp));
            continue;
        }
        let bad = check_order(&read_text(root, &rp));
        if !bad.is_empty() {
            issues.push(format!("登记为 condition-first 但未通过：{}（{}）", rp, bad[0]));
        }
    }
    stats.declared = rows.len();
    stats.family_rules = rules.len();
    stats.family_members = hits.len();
    (issues, stats)
}

// ---------------------------------------------------------------- assertions

const ASSERTIONS_REL: &str = "protocol/assertions.json";
const ASSERTIONS_SCHEMA: &str = "nf-assertions/1";
const SEVERITIES: [&str; 2] = ["fail", "warn"];
const REQUIRED: [&str; 6] = ["id", "severity", "kind", "params", "message", "fix"];
/// `kind` 封闭集。真源是 **dict 字面量**（Python 3.7+ 保序，非 set）——
/// 故 `tuple(KINDS)` 的顺序是确定的，可与 `kind_vocabulary` 逐项比序（已实测六种 hash 种子下同序）。
const KINDS: [&str; 4] = ["regex_absent", "regex_present", "count_at_least", "json_value"];

/// 真源 `_c_assertions`：跑一遍断言表，fail 级不通过即 FAIL。
fn assertions(root: &Path) -> (bool, String) {
    let run = assertions_run(root);
    let ok = run.issues.is_empty();
    let detail = if ok {
        format!(
            "断言 {} 条（通过 {}）· kind 封闭集 {} 种",
            run.results,
            run.passed,
            KINDS.len()
        )
    } else {
        run.issues.iter().take(2).cloned().collect::<Vec<_>>().join("; ")
    };
    (ok, detail)
}

struct AssertionsRun {
    results: usize,
    passed: usize,
    issues: Vec<String>,
}

/// 真源 `assertions.run`。
fn assertions_run(root: &Path) -> AssertionsRun {
    let (decl_issues, _count) = assertions_scan(root);
    let mut issues = decl_issues;
    let mut results = 0usize;
    let mut passed = 0usize;

    let Some(doc) = jsonread::read_file(root, ASSERTIONS_REL) else {
        return AssertionsRun { results, passed, issues };
    };
    for a in arr_items(get(&doc, "assertions")) {
        let kind = plain_str_opt(get(a, "kind"));
        let params = get(a, "params").cloned().unwrap_or(Json::Object(Vec::new()));
        let outcome = match kind.as_str() {
            "regex_absent" => k_regex_absent(root, &params),
            "regex_present" => k_regex_present(root, &params),
            "count_at_least" => k_count_at_least(root, &params),
            "json_value" => k_json_value(root, &params),
            _ => {
                issues.push(format!(
                    "断言 {} 的 kind 不在封闭集：{}",
                    plain_str_opt(get(a, "id")),
                    kind
                ));
                continue;
            }
        };
        let (ok, detail) = outcome;
        results += 1;
        if ok {
            passed += 1;
        }
        if !ok && plain_str_opt(get(a, "severity")) == "fail" {
            issues.push(format!(
                "{} 不通过：{}（修复指引：{}）",
                plain_str_opt(get(a, "id")),
                detail,
                plain_str_opt(get(a, "fix"))
            ));
        }
    }
    AssertionsRun { results, passed, issues }
}

/// 真源 `assertions.scan`（断言表自身的合法性）。
fn assertions_scan(root: &Path) -> (Vec<String>, usize) {
    let mut issues: Vec<String> = Vec::new();
    if !root.join(ASSERTIONS_REL).is_file() {
        return (vec![format!("缺断言表 {}", ASSERTIONS_REL)], 0);
    }
    let Some(doc) = jsonread::read_file(root, ASSERTIONS_REL) else {
        return (vec![format!("缺断言表 {}", ASSERTIONS_REL)], 0);
    };
    if obj_is_empty(&doc) {
        return (vec![format!("缺断言表 {}", ASSERTIONS_REL)], 0);
    }
    if py_str(get(&doc, "schema")) != ASSERTIONS_SCHEMA {
        issues.push(format!("断言表 schema 不匹配（期望 {}）", ASSERTIONS_SCHEMA));
    }
    if str_list(get(&doc, "severity_vocabulary")) != SEVERITIES {
        issues.push(format!("severity 词表与判据不一致（期望 {}）", SEVERITIES.join("/")));
    }
    if str_list(get(&doc, "kind_vocabulary")) != KINDS {
        issues.push(format!(
            "kind 词表必须与 runner 封闭集逐项一致（{}）",
            KINDS.join("/")
        ));
    }
    let items = arr_items(get(&doc, "assertions"));
    let mut seen: Vec<String> = Vec::new();
    for a in &items {
        let aid = py_str(get(a, "id"));
        for k in REQUIRED {
            let v = get(a, k);
            // 真源 `if not a.get(k) and a.get(k) != {}` —— 空对象不算缺
            let falsy = !v.map(py_truthy).unwrap_or(false);
            let empty_obj = matches!(v, Some(Json::Object(p)) if p.is_empty());
            if falsy && !empty_obj {
                let tag = if aid.is_empty() { "(无名)" } else { aid.as_str() };
                issues.push(format!("断言 {} 缺必填字段：{}", tag, k));
            }
        }
        if seen.contains(&aid) {
            issues.push(format!("断言 id 重复：{}", aid));
        }
        seen.push(aid.clone());
        let sev = plain_str_opt(get(a, "severity"));
        if !SEVERITIES.contains(&sev.as_str()) {
            issues.push(format!("断言 {} severity 越词表：{}", aid, sev));
        }
        let kind = plain_str_opt(get(a, "kind"));
        if !KINDS.contains(&kind.as_str()) {
            issues.push(format!("断言 {} kind 不在封闭集：{}", aid, kind));
        }
        if py_str(get(a, "fix")).trim().is_empty() {
            issues.push(format!("断言 {} 缺 fix（无修复指引不许入表）", aid));
        }
    }
    (issues, items.len())
}

/// 真源 `assertions._glob`：结果形如 `str(Path(root)/p)`（含 root 前缀、平台分隔符）。
fn a_glob(root: &Path, pattern: &str) -> Vec<String> {
    if crate::glob::has_wildcard(pattern) {
        crate::glob::expand(root, pattern)
            .iter()
            .map(|rel| crate::glob::py_path_str(root, rel))
            .collect()
    } else if root.join(pattern).is_file() {
        vec![crate::glob::py_path_str(root, pattern)]
    } else {
        Vec::new()
    }
}

/// `regex_absent`：数据驱动模式——用 fancy-regex（支持后顾）。编译失败按真源「异常」口径。
fn k_regex_absent(root: &Path, params: &Json) -> (bool, String) {
    let pat = py_str(get(params, "pattern"));
    let Ok(re) = fancy_regex::Regex::new(&pat) else {
        // 真源此处由 run() 的 except 兜住；**错误措辞不做逐字节承诺**
        return (false, "断言执行异常：模式不可编译".to_string());
    };
    let mut hits: Vec<String> = Vec::new();
    for g in arr_items(get(params, "globs")) {
        for f in a_glob(root, &plain_str(g)) {
            let text = std::fs::read_to_string(&f).unwrap_or_default();
            if re.is_match(&text).unwrap_or(false) {
                hits.push(f);
            }
        }
    }
    if hits.is_empty() {
        (true, "零命中".to_string())
    } else {
        let head: Vec<&str> = hits.iter().take(2).map(|s| s.as_str()).collect();
        (false, format!("命中：{}", head.join(", ")))
    }
}

/// `regex_present`：目标件必须含全部锚点（纯子串判定，不涉及正则）。
fn k_regex_present(root: &Path, params: &Json) -> (bool, String) {
    let rel = plain_str_opt(get(params, "path"));
    if !root.join(&rel).is_file() {
        return (false, format!("目标件不存在：{}", rel));
    }
    let text = std::fs::read_to_string(root.join(&rel)).unwrap_or_default();
    let patterns = arr_items(get(params, "patterns"));
    let miss: Vec<String> = patterns
        .iter()
        .map(|p| plain_str(p))
        .filter(|p| !text.contains(p))
        .collect();
    if miss.is_empty() {
        (true, format!("{} 锚点齐", patterns.len()))
    } else {
        let head: Vec<&str> = miss.iter().take(3).map(|s| s.as_str()).collect();
        (false, format!("缺：{}", head.join(", ")))
    }
}

/// `count_at_least`：glob 命中数 ≥ min。
fn k_count_at_least(root: &Path, params: &Json) -> (bool, String) {
    let n = a_glob(root, &plain_str_opt(get(params, "glob"))).len();
    let want = py_int_or(get(params, "min"), 0);
    (n as i64 >= want, format!("{} ≥ {}", n, want))
}

/// `json_value`：按键路径取值后做封闭集算子判定。
fn k_json_value(root: &Path, params: &Json) -> (bool, String) {
    let rel = plain_str_opt(get(params, "path"));
    if !root.join(&rel).is_file() {
        return (false, format!("目标件不存在：{}", rel));
    }
    let text = std::fs::read_to_string(root.join(&rel)).unwrap_or_default();
    let Ok(raw) = serde_json::from_str::<serde_json::Value>(&text) else {
        // 真源把 json.JSONDecodeError 的文本拼进消息——**该措辞不做逐字节承诺**
        return (false, "JSON 不可解析：<解析失败>".to_string());
    };
    let Ok(mut cur) = jsonread::convert(&raw) else {
        return (false, "JSON 不可解析：<含不支持的值>".to_string());
    };
    let key = py_str(get(params, "key"));
    for part in key.split('.') {
        let Json::Object(pairs) = &cur else {
            return (false, format!("缺键：{}", plain_str_opt(get(params, "key"))));
        };
        match pairs.iter().find(|(k, _)| k == part) {
            Some((_, v)) => cur = v.clone(),
            None => return (false, format!("缺键：{}", plain_str_opt(get(params, "key")))),
        }
    }
    let op = py_str(get(params, "op"));
    let val = get(params, "value").cloned();
    match op.as_str() {
        "exists" => (true, "键在场".to_string()),
        "nonempty" => {
            let ok = py_truthy(&cur);
            (ok, if ok { "非空" } else { "空值" }.to_string())
        }
        "equals" => {
            let v = val.unwrap_or(Json::Null);
            (py_eq(&cur, &v), format!("= {}", plain_str(&v)))
        }
        "in_vocab" => {
            let ok = arr_items(val.as_ref()).iter().any(|v| py_eq(&cur, v));
            (
                ok,
                if ok {
                    format!("{} ∈ 词表", plain_str(&cur))
                } else {
                    format!("{} 越词表", plain_str(&cur))
                },
            )
        }
        "contains_keys" => {
            let want: Vec<String> = arr_items(val.as_ref()).iter().map(|v| plain_str(v)).collect();
            let miss: Vec<String> = want
                .iter()
                .filter(|k| match &cur {
                    Json::Object(pairs) => !pairs.iter().any(|(n, _)| n == *k),
                    Json::Array(items) => !items.iter().any(|v| plain_str(v) == **k),
                    _ => true,
                })
                .cloned()
                .collect();
            if miss.is_empty() {
                (true, "键齐".to_string())
            } else {
                (false, format!("缺：{}", miss.join(", ")))
            }
        }
        _ => (
            false,
            format!(
                "未知 op：{}（封闭集：exists/nonempty/equals/in_vocab/contains_keys）",
                op
            ),
        ),
    }
}

// ---------------------------------------------------------------- assertions
//
// 已抽到 `crate::pyval`（`contracts` 与 `layers` 共用唯一实现，避免两处 Python 语义漂移）。

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    /// 夹具目录**必须落在工作区内**：本机沙箱拒绝子进程写 `%TEMP%`（实测），
    /// 落 `target/`（已 gitignore）既在沙箱许可范围内，也不污染仓库。
    /// 路径隔离见 [`crate::testutil::fixture`]（并发跑 `cargo test` 时的互删问题）。
    fn fixture(name: &str) -> PathBuf {
        crate::testutil::fixture(name)
    }

    /// 原判据断言 `purity-clean` **未分派**（当时它是"显式缺席"的例子）。**2026-10-04：27/27
    /// 全部移植**，该断言自然失效——但 ADR-0005 的两半都要守，故改写成两个方向：
    /// ① **未知 id 必须显式缺席**（不许伪造结论）；② **在册的 27 条都必须真有分派**
    /// （防止"登记了却没接线"这种反方向的缺口）。
    ///
    /// 分派检查跑在**空夹具根**上：各判据在缺件时都快速返回，故这条判据是廉价的。
    #[test]
    fn unknown_contract_is_absent_and_every_registered_one_is_dispatched() {
        // ① 未知 id：显式缺席
        assert!(run("no-such-contract", Path::new(".")).is_none());
        assert!(description("no-such-contract").is_none());
        // ② 在册 27 条：有说明、且有分派
        let empty = fixture("all-ported");
        for id in PORTED {
            assert!(description(id).is_some(), "契约 {} 缺说明登记", id);
            assert!(run(id, &empty).is_some(), "契约 {} 登记了却缺分派", id);
        }
    }

    #[test]
    fn st_quality_on_missing_file_reports_missing_declaration() {
        let tmp = fixture("st-missing");
        let _ = std::fs::create_dir_all(&tmp);
        let (ok, detail) = run("st-quality", &tmp).unwrap();
        assert!(!ok);
        assert!(detail.contains("缺 ST 制卡质量规范"), "got: {}", detail);
    }

    #[test]
    fn py_str_mirrors_python_falsy_rule() {
        assert_eq!(py_str(None), "");
        assert_eq!(py_str(Some(&Json::Null)), "");
        assert_eq!(py_str(Some(&Json::Int(0))), "");
        assert_eq!(py_str(Some(&Json::Bool(false))), "");
        assert_eq!(py_str(Some(&Json::Bool(true))), "True");
        assert_eq!(py_str(Some(&Json::Str("x".into()))), "x");
        assert_eq!(py_str(Some(&Json::Int(7))), "7");
    }

    #[test]
    fn str_list_treats_missing_as_empty() {
        assert!(str_list(None).is_empty());
        assert_eq!(
            str_list(Some(&Json::Array(vec![Json::Str("M".into()), Json::Str("S".into())]))),
            vec!["M".to_string(), "S".to_string()]
        );
    }

    #[test]
    fn empty_object_is_treated_as_missing_declaration() {
        let tmp = fixture("st-empty");
        let _ = std::fs::remove_dir_all(&tmp);
        std::fs::create_dir_all(tmp.join("protocol")).expect("建夹具目录");
        std::fs::write(tmp.join(ST_REL), b"{}").expect("写夹具文件");
        let (ok, detail) = run("st-quality", &tmp).unwrap();
        assert!(!ok);
        assert!(detail.contains("缺 ST 制卡质量规范"), "got: {}", detail);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn ported_contracts_are_exactly_the_declared_list() {
        for id in PORTED {
            assert!(description(id).is_some(), "{} 缺 description 登记", id);
            assert!(run(id, Path::new(".")).is_some(), "{} 缺 run 分派", id);
        }
        // 冻结数：**故意**留的摩擦——新增契约时必须回来改这一行，顺带检查登记齐全。
        assert_eq!(PORTED.len(), 27);
    }

    #[test]
    fn assertion_kinds_discriminate() {
        // regex_absent：命中即不通过（判别力自证）
        let tmp = fixture("as-regex-absent");
        let _ = std::fs::remove_dir_all(&tmp);
        std::fs::create_dir_all(tmp.join("d")).unwrap();
        std::fs::write(tmp.join("d/x.md"), "C:\\tmp\\leak").unwrap();
        let params: Json = jsonread::convert(&serde_json::json!({
            "globs": ["d/*.md"], "pattern": "(?<![A-Za-z0-9])[A-Za-z]:[\\\\/]"
        }))
        .unwrap();
        let (ok, detail) = k_regex_absent(&tmp, &params);
        assert!(!ok, "命中绝对路径时必须判红");
        assert!(detail.starts_with("命中："), "got: {}", detail);

        // 该模式若用 Rust regex（不支持后顾）会编译失败——故必须走 fancy-regex。
        let clean = fixture("as-regex-clean");
        let _ = std::fs::remove_dir_all(&clean);
        std::fs::create_dir_all(clean.join("d")).unwrap();
        std::fs::write(clean.join("d/x.md"), "relative/path/only").unwrap();
        let (ok2, detail2) = k_regex_absent(&clean, &params);
        assert!(ok2, "零命中应通过；got: {}", detail2);
        assert_eq!(detail2, "零命中");

        // count_at_least：0 是假值 → min 落 0（真源 `int(x or 0)`）
        let p2: Json = jsonread::convert(&serde_json::json!({"glob": "d/*.md", "min": 0})).unwrap();
        assert!(k_count_at_least(&clean, &p2).0);
        let p3: Json = jsonread::convert(&serde_json::json!({"glob": "d/*.md", "min": 2})).unwrap();
        assert!(!k_count_at_least(&clean, &p3).0);

        // regex_present：缺锚点要指名
        std::fs::write(clean.join("t.txt"), "alpha beta").unwrap();
        let p4: Json =
            jsonread::convert(&serde_json::json!({"path": "t.txt", "patterns": ["alpha", "gamma"]})).unwrap();
        let (ok4, d4) = k_regex_present(&clean, &p4);
        assert!(!ok4);
        assert_eq!(d4, "缺：gamma");

        // json_value：equals / contains_keys / 未知 op
        std::fs::write(clean.join("j.json"), br#"{"a": {"b": 2}, "flags": {"f": false}}"#).unwrap();
        let p5: Json = jsonread::convert(
            &serde_json::json!({"path": "j.json", "key": "a.b", "op": "equals", "value": 2}),
        )
        .unwrap();
        assert!(k_json_value(&clean, &p5).0, "a.b 应等于 2");
        let p6: Json = jsonread::convert(
            &serde_json::json!({"path": "j.json", "key": "flags.f", "op": "equals", "value": false}),
        )
        .unwrap();
        assert!(k_json_value(&clean, &p6).0, "布尔 false 应相等");
        let p7: Json = jsonread::convert(
            &serde_json::json!({"path": "j.json", "key": "a", "op": "contains_keys", "value": ["b", "z"]}),
        )
        .unwrap();
        let (ok7, d7) = k_json_value(&clean, &p7);
        assert!(!ok7);
        assert_eq!(d7, "缺：z");
        let p8: Json =
            jsonread::convert(&serde_json::json!({"path": "j.json", "key": "a", "op": "nope"})).unwrap();
        assert!(!k_json_value(&clean, &p8).0);

        let _ = std::fs::remove_dir_all(&tmp);
        let _ = std::fs::remove_dir_all(&clean);
    }

    #[test]
    fn py_truthy_and_py_eq_follow_python_rules() {
        assert!(!py_truthy(&Json::Null));
        assert!(!py_truthy(&Json::Int(0)));
        assert!(!py_truthy(&Json::Str(String::new())));
        assert!(!py_truthy(&Json::Array(vec![])));
        assert!(py_truthy(&Json::Int(1)));
        assert!(py_eq(&Json::Bool(true), &Json::Int(1)), "Python True == 1");
        assert!(py_eq(&Json::Int(1), &Json::Bool(true)));
    }

    #[test]
    fn canonical_determinism_is_key_order_independent() {
        let (ok, detail) = run("canonical-digest-determinism", Path::new(".")).unwrap();
        assert!(ok);
        assert_eq!(detail, "canonical digest 两遍一致");
    }

    // ------------------------------------------------------------ rfc-heads

    const RFC_SAMPLE: &str = "> **RFC**: NF-0001 · **Category**: Standards Track · **Date**: 2026-09-08 ·\n  **Status**: Active · **Supersedes**: — · **Superseded by**: —\n\n> 最后更新：2026-09-08\n";

    #[test]
    fn rfc_head_parser_extracts_all_six_fields() {
        let h = parse_head(RFC_SAMPLE).expect("样例头应可解析");
        assert_eq!(h.rfc, "NF-0001");
        assert_eq!(h.cat, "Standards Track");
        assert_eq!(h.date, "2026-09-08");
        assert_eq!(h.status, "Active");
        assert_eq!(h.supby, "—");
        assert_eq!(h.last_updated, "2026-09-08");
    }

    #[test]
    fn rfc_head_parser_only_looks_at_first_eight_lines() {
        let mut text = String::new();
        for _ in 0..9 {
            text.push_str("填充行\n");
        }
        text.push_str(RFC_SAMPLE);
        assert!(parse_head(&text).is_none(), "第 9 行之后的头不得被采纳");
    }

    #[test]
    fn rfc_chain_cycle_is_detected() {
        let tmp = fixture("rfc-cycle");
        let _ = std::fs::remove_dir_all(&tmp);
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::create_dir_all(tmp.join("d")).unwrap();
        for (n, supby) in [("0001", "NF-0002"), ("0002", "NF-0001")] {
            std::fs::write(
                tmp.join(format!("d/{}.md", n)),
                format!(
                    "> **RFC**: NF-{} · **Category**: Process · **Date**: 2026-01-01 ·\n  **Status**: Active · **Supersedes**: — · **Superseded by**: {}\n",
                    n, supby
                ),
            )
            .unwrap();
        }
        std::fs::write(
            tmp.join(RFC_INDEX_REL),
            br#"{"status_vocabulary": ["Active"], "docs": [
                 {"path": "d/0001.md", "rfc": "NF-0001"},
                 {"path": "d/0002.md", "rfc": "NF-0002"}]}"#,
        )
        .unwrap();
        let (ok, detail) = run("rfc-heads", &tmp).unwrap();
        assert!(!ok);
        assert!(detail.contains("成环"), "got: {}", detail);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    // ------------------------------------------------------------ cognition

    #[test]
    fn plain_str_differs_from_py_str_on_falsy_values() {
        assert_eq!(plain_str(&Json::Null), "None");
        assert_eq!(plain_str(&Json::Bool(false)), "False");
        assert_eq!(plain_str(&Json::Int(0)), "0");
        assert_eq!(py_str(Some(&Json::Null)), "");
        assert_eq!(py_str(Some(&Json::Bool(false))), "");
        assert_eq!(py_str(Some(&Json::Int(0))), "");
    }

    /// cognition 契约**同时**扫术语表与执行分档；只给一半的夹具会被另一半判红。
    fn write_modes_fixture(tmp: &Path) {
        std::fs::write(
            tmp.join(MODES_REL),
            br#"{"schema": "nf-execution-modes/1", "modes": []}"#,
        )
        .unwrap();
    }

    #[test]
    fn cognition_flags_term_missing_from_its_source() {
        let tmp = fixture("cog-glossary");
        let _ = std::fs::remove_dir_all(&tmp);
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::write(tmp.join("src.md"), "这里没有那个术语\n").unwrap();
        std::fs::write(
            tmp.join(GLOSSARY_REL),
            br#"{"schema": "nf-glossary/1", "rules": ["r"],
                 "terms": [{"term": "X", "definition": "d", "source": "src.md"}]}"#,
        )
        .unwrap();
        write_modes_fixture(&tmp);
        let (ok, detail) = run("cognition", &tmp).unwrap();
        assert!(!ok, "术语不在其 source 中逐字出现时必须判红");
        assert!(detail.contains("未在其 source 中逐字出现"), "got: {}", detail);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn cognition_empty_string_used_in_is_falsy_not_a_path() {
        // 真源 `t.get("used_in") or []`：空串按假值落空表，**不得**当成「一项空路径」
        let tmp = fixture("cog-empty-usedin");
        let _ = std::fs::remove_dir_all(&tmp);
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::write(tmp.join("src.md"), "X 在此\n").unwrap();
        std::fs::write(
            tmp.join(GLOSSARY_REL),
            br#"{"schema": "nf-glossary/1", "rules": ["r"],
                 "terms": [{"term": "X", "definition": "d", "source": "src.md", "used_in": ""}]}"#,
        )
        .unwrap();
        write_modes_fixture(&tmp);
        let (ok, detail) = run("cognition", &tmp).unwrap();
        assert!(ok, "空串 used_in 应被当作空表；实际判红：{}", detail);
        let _ = std::fs::remove_dir_all(&tmp);
    }
#[cfg(test)]
mod state_front_tests {
    use super::*;
    // >>> GENERATED by tools/gen_state_front_branches.py（勿手改；重跑生成器覆盖本段）
    /// ===== 分支级差分判据（期望值由 `tools/gen_state_front_branches.py` 从真源生成）=====
    ///
    /// 三场景：kitchen（逐分支踩）/ 缺声明 / 空声明（门禁空转 warn）。
    /// 分支：schema / 族规则缺 glob / 族成员不足 / 族内件未过 condition-first /
    /// 声明条目缺 path / 登记件不存在 / 登记件未过 condition-first / 全绿。
    /// 注：真源 `scan` 的 warns 在本面无消费者（契约只看 issues），故本线未纳入移植面。
    const SF_GOOD: &str = r#"# 标题

> 适用条件：X 成立时。

## 正文
内容
"#;
    const SF_BAD: &str = r#"## 正文
内容
"#;

    fn build_sf_fixture(scenario: &str, decl: Option<&str>) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("state-front-branches-{}", scenario));
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        if let Some(d) = decl {
            std::fs::write(root.join("protocol/state_front.json"), d).unwrap();
        }
        if scenario != "empty" {
            for (rel, body) in [
                ("docs/fam/a.md", SF_GOOD),
                ("docs/fam/b.md", SF_BAD),
                ("docs/one.md", SF_BAD),
                ("docs/two.md", SF_GOOD),
            ] {
                let p = root.join(rel);
                std::fs::create_dir_all(p.parent().unwrap()).unwrap();
                std::fs::write(p, body).unwrap();
            }
        }
        root
    }

    #[test]
    fn the_contract_matches_the_truth_source_branch_by_branch() {
        for (scenario, decl, want) in [
            ("kitchen", Some(r#"{"schema": "wrong/1", "declared": [{"path": ""}, {"path": "docs/nope.md"}, {"path": "docs/one.md"}, {"path": "docs/two.md"}], "family_rules": [{"glob": ""}, {"glob": "docs/fam/*.md", "min_members": 5}, {"glob": "docs/fam/*.md"}, {"glob": "docs/none/*.md", "min_members": 1}]}"#), &["声明 schema 不匹配（期望 nf-state-front/1）", "族规则缺 glob", "族 docs/fam/*.md 成员不足：2 < 5（修复指引：按 sources 重新生成）", "族 docs/none/*.md 成员不足：0 < 1（修复指引：按 sources 重新生成）", "族内件未通过 condition-first：docs/fam/a.md（缺状态块——无状态文本代理可前置）", "族内件未通过 condition-first：docs/fam/b.md（缺状态块——无状态文本代理可前置）", "族内件未通过 condition-first：docs/fam/a.md（缺状态块——无状态文本代理可前置）", "族内件未通过 condition-first：docs/fam/b.md（缺状态块——无状态文本代理可前置）", "声明条目缺 path", "登记件不存在：docs/nope.md", "登记为 condition-first 但未通过：docs/one.md（缺状态块——无状态文本代理可前置）", "登记为 condition-first 但未通过：docs/two.md（缺状态块——无状态文本代理可前置）"] as &[&str]),
            ("nodecl", None, &["缺条件先行声明 protocol/state_front.json"] as &[&str]),
            ("empty", Some(r#"{"schema": "nf-state-front/1", "declared": [], "family_rules": []}"#), &[] as &[&str]),
        ] {
            let root = build_sf_fixture(scenario, decl);
            let (issues, _stats) = state_front_scan(&root);
            assert_eq!(issues, want, "场景 {} 的 issues", scenario);
        }
    }
    // <<< GENERATED
}

    // >>> GENERATED by tools/gen_cognition_branches.py（勿手改；重跑生成器覆盖本段）
    /// ===== 分支级差分判据（期望值由 `tools/gen_cognition_branches.py` 从真源生成）=====
    ///
    /// 真语料上该契约全绿 ⇒ 对账核不到错误分支。本夹具逐支踩：
    /// 术语表（schema / rules 空 / 无 term 条目 / 术语重复 / 缺 definition / source 不存在 /
    /// 未在 source 中逐字出现 / used_in 不存在 / used_in 未逐字出现 / 全绿计入 uses）
    /// + 执行分档（schema / id 重复 / 缺 required_blocks / 无实例 / 实例不存在 / 缺结构块）。
    const CG_GLOSSARY: &str = r#"{"schema": "wrong/1", "rules": [], "terms": [{"definition": "无 term"}, {"term": "甲", "definition": "定义甲", "source": "docs/s.md"}, {"term": "甲", "definition": "定义甲2", "source": "docs/s.md"}, {"term": "乙"}, {"term": "丙", "definition": "定义丙", "source": "no/such.md"}, {"term": "丁", "definition": "定义丁", "source": "docs/s.md"}, {"term": "戊", "definition": "定义戊", "used_in": ["no/such.md"]}, {"term": "己", "definition": "定义己", "used_in": ["docs/u.md"]}]}"#;
    const CG_MODES: &str = r###"{"schema": "wrong/1", "modes": [{"id": "m1", "required_blocks": ["## 块"], "instances": ["docs/inst-ok.md"]}, {"id": "m1", "required_blocks": [], "instances": []}, {"id": "m2", "required_blocks": ["## 块"], "instances": ["no/such.md"]}, {"id": "m3", "required_blocks": ["## 块"], "instances": ["docs/inst-bad.md"]}]}"###;
    const CG_DOCS: [(&str, &str); 4] = [
        ("docs/inst-bad.md", r#"# 实例
没有那个结构块
"#),
        ("docs/inst-ok.md", r#"# 实例
## 块
内容
"#),
        ("docs/s.md", r#"# 源
甲 在这里逐字出现
"#),
        ("docs/u.md", r#"# 使用面
（不含那个术语）
"#),
    ];

    fn build_cognition_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("cognition-branches");
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        std::fs::create_dir_all(root.join("docs")).unwrap();
        std::fs::write(root.join("protocol/glossary.json"), CG_GLOSSARY).unwrap();
        std::fs::write(root.join("protocol/execution_modes.json"), CG_MODES).unwrap();
        for (rel, body) in CG_DOCS {
            std::fs::write(root.join(rel), body).unwrap();
        }
        root
    }

    #[test]
    fn cognition_matches_truth_source_branch_by_branch() {
        let root = build_cognition_fixture();
        let (issues, _g, _m) = cognition_scan(&root);
        assert_eq!(issues, &["术语表 schema 不匹配（期望 nf-glossary/1）", "术语表 rules 不得为空（登记纪律必须成文）", "存在无 term 的条目", "术语重复：甲", "术语 乙 缺 definition", "术语 乙 的 source 不存在：", "术语 丙 的 source 不存在：no/such.md", "术语 丁 未在其 source 中逐字出现：docs/s.md（定义必须落在真源里）", "术语 戊 的 source 不存在：", "术语 戊 的 used_in 不存在：no/such.md", "术语 己 的 source 不存在：", "术语 己 的 used_in 未逐字出现该术语：docs/u.md（防登记没人用的行话）", "执行分档 schema 不匹配（期望 nf-execution-modes/1）", "mode id 重复：m1", "mode m1 缺 required_blocks（该档必备结构必须成文）", "mode m1 无实例（声明了档却没有件属于它）", "mode m2 的实例不存在：no/such.md", "实例 docs/inst-bad.md 不属于 m3 档：缺结构块 ## 块"] as &[&str], "issues 须逐字且同序");
        // 契约层：ok + detail（detail 里嵌了 terms/uses/modes/instances_ok 四项计数）
        let (ok, detail) = cognition(&root);
        assert_eq!(ok, false);
        assert_eq!(detail, "术语表 schema 不匹配（期望 nf-glossary/1）; 术语表 rules 不得为空（登记纪律必须成文）");
    }
    // <<< GENERATED

    // >>> GENERATED by tools/gen_doc_kinds_branches.py（勿手改；重跑生成器覆盖本段）
    /// ===== 分支级差分判据（期望值由 `tools/gen_doc_kinds_branches.py` 从真源生成）=====
    ///
    /// `_c_doc_kinds` 只调 `kind_coverage` + `kind_rules`（不涉日期）。
    /// 本判据钉两件事：
    /// ① **常量表一致性**：`kind_coverage` 忽略 `root`、只用真源里固定的 `REQUIRED_DOCS ∪
    ///    INSTRUCTION_DOCS` ——本线若漏转录某条，就会报出真源没有的 issue（合成夹具**触发不了**
    ///    它的分支，故只能这样核）；
    /// ② **`kind_rules` 的两个分支**：路径在场但写法不符该型 ⇒ WARN；在场且合规 ⇒ 不 WARN；
    ///    其余路径不在场 ⇒ 走「跳过」分支。
    const DK_FILES: [(&str, &str); 2] = [
        ("06_Agent执行协议.md", r#"# 章节
只有说明文字，没有命令块。
"#),
        ("docs/meta/DEEP_DIVE.md", r#"# 说明
这里解释**机制**与取舍。
"#),
    ];

    fn build_doc_kinds_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("doc-kinds-branches");
        for (rel, body) in DK_FILES {
            let p = root.join(rel);
            std::fs::create_dir_all(p.parent().unwrap()).unwrap();
            std::fs::write(p, body).unwrap();
        }
        root
    }

    #[test]
    fn doc_kinds_matches_truth_source() {
        let root = build_doc_kinds_fixture();
        // ① 常量表一致性（真源这两个函数里，只有 kind_coverage 与 root 无关）
        assert_eq!(crate::doc_hygiene::kind_coverage(), &[] as &[&str], "四型覆盖（常量表一致性）");
        // ② kind_rules 的两个分支
        assert_eq!(crate::doc_hygiene::kind_rules(&root), &["06_Agent执行协议.md 属 how-to 型但缺「可执行命令块」（写法未定型）"] as &[&str], "写法 WARN 须逐字且同序");
        // ③ 契约层 detail
        let (ok, detail) = doc_kinds(&root);
        assert_eq!(ok, true);
        assert_eq!(detail, "四型全覆盖 · 写法 WARN 1");
    }
    // <<< GENERATED

}
