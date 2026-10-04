//! 双源知识层（`knowledge`）—— 与真源 `desktop/src/core/knowledge.py` 的 `scan` 对账。
//!
//! 判据：声明 schema / 三套词表逐项一致；每个源必填齐、id 唯一、词表在册、`locator` **真实存在**
//!（防纸面源）；**reference 级**须是 external-retrieval + 要求标注来源 + 时效策略取 `ttl`/`no-cache`
//!（且 `ttl` 时 `ttl_days` 为正整数）；**contract 级**须是 local-compiled + 不要求外部标注 + 时效取
//! `stale_after`；`query_order` 须与 sources 同集合且**合同级全部排在参考级之前**；晋升/审核/认知
//! 三段规则成文；`cognition.filter_module` 须指向在册模块；消化记录在场且 schema 匹配。
//!
//! **移植范围**：只做 `scan`。同模块的 `verify_transform` / `verify_usage` / `verify_reuse` /
//! `harvest_frequency` / `write_*` 是另几条判据与写面，不在 `verify_report` 的判据表里。
//!
//! **已知近似（fail-closed）**：真源 `_read_json` **不吞解析异常**——声明件坏 JSON 会让整条判据
//! 记 `error`。本线照样如实记 `error`（而不是当作空声明往下走，那会把 error 悄悄降级成一堆
//! 看起来正常的字段缺失 issue）。
//!
//! 本模块是 `nf verify-report` 的 `knowledge` 判据，**不单独开 CLI 面**。

use crate::jsonread;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, py_str, py_truthy};
use std::collections::BTreeSet;
use std::path::Path;

pub const DECL_REL: &str = "protocol/knowledge_sources.json";
pub const LOG_REL: &str = "protocol/transform_log.json";
pub const SCHEMA: &str = "nf-knowledge-sources/1";
pub const LOG_SCHEMA: &str = "nf-transform-log/1";
const AUTHORITIES: [&str; 2] = ["contract", "reference"];
const KINDS: [&str; 2] = ["local-compiled", "external-retrieval"];
const VISIBILITIES: [&str; 3] = ["public", "internal", "restricted"];
const TIERS: [&str; 3] = ["machine-checkable", "reproducible", "externally-attestable"];
const TRIGGERS: [&str; 3] = ["reuse-frequency", "author-mark", "machine-check-pass"];
const FRESH_CONTRACT: [&str; 1] = ["stale_after"];
const FRESH_REFERENCE: [&str; 2] = ["ttl", "no-cache"];
const REQUIRED_SRC: [&str; 6] = [
    "id",
    "authority",
    "kind",
    "locator",
    "requires_source_label",
    "visibility",
];

fn module_id_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"(?m)^\s*id:\s*(M\d+|事件:M\d+|通用:M\d+)\s*$")
            .expect("模块 id 正则固定合法")
    })
}

/// 真源 `_read_json`（**不吞解析异常**）。`Ok(None)` = 文件不在场。
fn read_json(root: &Path, rel: &str) -> Result<Option<Json>, String> {
    if !root.join(rel).is_file() {
        return Ok(None);
    }
    jsonread::read_file(root, rel)
        .map(Some)
        .ok_or_else(|| format!("{} 不是合法 JSON", rel))
}

/// 真源 `_module_ids`。
fn module_ids(root: &Path) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    for pat in ["04_模块库/*/*.md", "community/*/modules/*.md"] {
        for rel in crate::glob::expand(root, pat) {
            let Ok(text) = std::fs::read_to_string(root.join(&rel)) else { continue };
            for c in module_id_re().captures_iter(&text) {
                out.insert(c[1].to_string());
            }
        }
    }
    out
}

fn sources(decl: &Json) -> Vec<Json> {
    arr_items(get(decl, "sources")).into_iter().cloned().collect()
}

/// 真源 `_auth`。
fn auth_of(rows: &[Json], sid: &str) -> String {
    for s in rows {
        if py_str(get(s, "id")) == sid {
            return py_str(get(s, "authority"));
        }
    }
    String::new()
}

pub struct KnowledgeScan {
    /// 真源 `_read_json` 抛异常时整条判据记 error——本线同样如实上报
    pub status: Option<&'static str>,
    pub issues: Vec<String>,
    pub warns: Vec<String>,
    pub stats: Json,
}

fn empty_stats() -> Json {
    Json::Object(Vec::new())
}

/// 真源 `scan` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> KnowledgeScan {
    let mut issues: Vec<String> = Vec::new();
    let warns: Vec<String> = Vec::new();

    let decl = match read_json(root, DECL_REL) {
        Ok(Some(d)) => d,
        Ok(None) => {
            return KnowledgeScan {
                status: None,
                issues: vec![format!("缺知识源声明 {}（修复指引：见 docs/knowledge.md）", DECL_REL)],
                warns,
                stats: empty_stats(),
            }
        }
        Err(e) => {
            return KnowledgeScan {
                status: Some("error"),
                issues: vec![e],
                warns,
                stats: empty_stats(),
            }
        }
    };
    if py_str(get(&decl, "schema")) != SCHEMA {
        issues.push(format!("知识源声明 schema 不匹配（期望 {}）", SCHEMA));
    }
    for (key, vocab) in [
        ("authority_vocabulary", AUTHORITIES.to_vec()),
        ("kind_vocabulary", KINDS.to_vec()),
        ("visibility_vocabulary", VISIBILITIES.to_vec()),
    ] {
        let got: Vec<String> = crate::pyval::str_list(get(&decl, key));
        if got != vocab {
            issues.push(format!(
                "{} 词表与判据不一致（期望 {}）",
                key,
                vocab.join("/")
            ));
        }
    }

    let rows = sources(&decl);
    if rows.is_empty() {
        issues.push(format!("未声明任何知识源（{}.sources 为空）", DECL_REL));
    }
    let mut seen: BTreeSet<String> = BTreeSet::new();
    for s in &rows {
        let sid = py_str(get(s, "id"));
        for k in REQUIRED_SRC {
            if get(s, k).is_none() {
                issues.push(format!(
                    "源 {} 缺必填字段：{}",
                    if sid.is_empty() { "(无名)" } else { sid.as_str() },
                    k
                ));
            }
        }
        if seen.contains(&sid) {
            issues.push(format!("源 id 重复：{}", sid));
        }
        seen.insert(sid.clone());
        let auth = py_str(get(s, "authority"));
        let kind = py_str(get(s, "kind"));
        if !AUTHORITIES.contains(&auth.as_str()) {
            issues.push(format!("源 {} authority 越词表：{}", sid, auth));
        }
        if !KINDS.contains(&kind.as_str()) {
            issues.push(format!("源 {} kind 越词表：{}", sid, kind));
        }
        let vis = py_str(get(s, "visibility"));
        if !VISIBILITIES.contains(&vis.as_str()) {
            issues.push(format!("源 {} visibility 越词表：{}", sid, vis));
        }
        let loc = py_str(get(s, "locator"));
        if !loc.is_empty() && !root.join(&loc).exists() {
            issues.push(format!("源 {} 的 locator 不存在：{}（防纸面源）", sid, loc));
        }
        let fresh = get(s, "freshness")
            .filter(|f| matches!(f, Json::Object(_)))
            .cloned()
            .unwrap_or_else(empty_stats);
        let pol = py_str(get(&fresh, "policy"));
        let labelled = py_truthy(get(s, "requires_source_label").unwrap_or(&Json::Null));
        if auth == "reference" {
            if kind != "external-retrieval" {
                issues.push(format!("源 {} 为 reference 级但 kind 非 external-retrieval", sid));
            }
            if !labelled {
                issues.push(format!(
                    "源 {} 为 reference 级但未要求标注来源（外部数据不得写死；修复指引：requires_source_label: true）",
                    sid
                ));
            }
            if !FRESH_REFERENCE.contains(&pol.as_str()) {
                issues.push(format!(
                    "源 {} 为 reference 级但时效策略非法：{}（需 {}）",
                    sid,
                    if pol.is_empty() { "(缺)".to_string() } else { pol.clone() },
                    FRESH_REFERENCE.join(" / ")
                ));
            } else if pol == "ttl" {
                let ok = matches!(get(&fresh, "ttl_days"), Some(Json::Int(n)) if *n > 0);
                if !ok {
                    issues.push(format!("源 {} 声明 ttl 但 ttl_days 非正整数", sid));
                }
            }
        } else if auth == "contract" {
            if kind != "local-compiled" {
                issues.push(format!("源 {} 为 contract 级但 kind 非 local-compiled", sid));
            }
            if labelled {
                issues.push(format!(
                    "源 {} 为 contract 级却要求外部来源标注（合同级即本地真源）",
                    sid
                ));
            }
            if !FRESH_CONTRACT.contains(&pol.as_str()) {
                issues.push(format!(
                    "源 {} 为 contract 级但时效策略非法：{}（需 stale_after）",
                    sid,
                    if pol.is_empty() { "(缺)".to_string() } else { pol.clone() }
                ));
            }
        }
    }

    let order: Vec<String> = crate::pyval::str_list(get(&decl, "query_order"));
    let ids: Vec<String> = rows.iter().map(|s| py_str(get(s, "id"))).collect();
    let order_sorted: BTreeSet<String> = order.iter().cloned().collect();
    let ids_sorted: BTreeSet<String> = ids.iter().cloned().collect();
    if order_sorted != ids_sorted {
        let mut missing: Vec<String> = ids_sorted.difference(&order_sorted).cloned().collect();
        let mut extra: Vec<String> = order_sorted.difference(&ids_sorted).cloned().collect();
        missing.sort();
        extra.sort();
        issues.push(format!(
            "query_order 与 sources 不是同一集合（缺 {} / 多 {}）",
            py_list(&missing),
            py_list(&extra)
        ));
    } else {
        let pos: Vec<(String, usize)> =
            order.iter().cloned().enumerate().map(|(i, s)| (s, i)).collect();
        let at = |sid: &String| pos.iter().find(|(s, _)| s == sid).map(|(_, i)| *i).unwrap_or(0);
        let ref_idx: Vec<usize> = ids
            .iter()
            .filter(|i| auth_of(&rows, i) == "reference")
            .map(at)
            .collect();
        let con_idx: Vec<usize> = ids
            .iter()
            .filter(|i| auth_of(&rows, i) == "contract")
            .map(at)
            .collect();
        if !ref_idx.is_empty() && !con_idx.is_empty() {
            let max_con = con_idx.iter().copied().max().unwrap_or(0);
            let min_ref = ref_idx.iter().copied().min().unwrap_or(0);
            if max_con > min_ref {
                issues.push(
                    "query_order 未把全部合同级排在参考级之前（查询有序被破坏）".to_string(),
                );
            }
        }
    }

    let sub = |k: &str| -> Json {
        get(&decl, k)
            .filter(|v| matches!(v, Json::Object(_)))
            .cloned()
            .unwrap_or_else(empty_stats)
    };
    let prom = sub("promotion");
    if crate::pyval::str_list(get(&prom, "evidence_tiers")) != TIERS {
        issues.push(format!(
            "promotion.evidence_tiers 与判据不一致（期望 {}）",
            TIERS.join("/")
        ));
    }
    if crate::pyval::str_list(get(&prom, "triggers")) != TRIGGERS {
        issues.push(format!(
            "promotion.triggers 与判据不一致（期望 {}）",
            TRIGGERS.join("/")
        ));
    }
    if py_str(get(&prom, "rule")).trim().is_empty() {
        issues.push("promotion 缺 rule（晋升标准必须成文）".to_string());
    }
    if py_str(get(&prom, "on_missing_evidence")) != "stay-reference" {
        issues.push("promotion.on_missing_evidence 必须为 stay-reference（缺证据不得转正）".to_string());
    }
    let rev = sub("review");
    if arr_items(get(&rev, "machine_gates")).is_empty() {
        issues.push("review 缺 machine_gates（消化审核必须列机检项）".to_string());
    }
    if py_str(get(&rev, "rule")).trim().is_empty() {
        issues.push("review 缺 rule（消化审核规则必须成文）".to_string());
    }
    let cog = sub("cognition");
    let fid = py_str(get(&cog, "filter_module"));
    if fid.is_empty() {
        issues.push("cognition 缺 filter_module（认知裁剪须指定执行模块）".to_string());
    } else if !module_ids(root).contains(&fid) {
        issues.push(format!("cognition.filter_module 指向不在册模块：{}", fid));
    }

    let log = match read_json(root, LOG_REL) {
        Ok(Some(l)) => Some(l),
        Ok(None) => None,
        Err(e) => {
            return KnowledgeScan {
                status: Some("error"),
                issues: vec![e],
                warns,
                stats: empty_stats(),
            }
        }
    };
    let transforms = match &log {
        None => {
            issues.push(format!("缺消化记录 {}（修复指引：见 docs/knowledge.md）", LOG_REL));
            0
        }
        Some(l) => {
            if py_str(get(l, "schema")) != LOG_SCHEMA {
                issues.push(format!("消化记录 schema 不匹配（期望 {}）", LOG_SCHEMA));
            }
            arr_items(get(l, "entries")).len()
        }
    };

    let stats = Json::Object(vec![
        ("sources".to_string(), Json::Int(rows.len() as i64)),
        (
            "contract".to_string(),
            Json::Int(rows.iter().filter(|s| py_str(get(s, "authority")) == "contract").count() as i64),
        ),
        (
            "reference".to_string(),
            Json::Int(rows.iter().filter(|s| py_str(get(s, "authority")) == "reference").count() as i64),
        ),
        (
            "order".to_string(),
            Json::Array(order.into_iter().map(Json::Str).collect()),
        ),
        ("transforms".to_string(), Json::Int(transforms as i64)),
    ]);
    KnowledgeScan { status: None, issues, warns, stats }
}

/// Python `str(list[str])`。
fn py_list(v: &[String]) -> String {
    let inner: Vec<String> = v.iter().map(|s| format!("'{}'", s)).collect();
    format!("[{}]", inner.join(", "))
}


// ---------------------------------------------------------------- 消化记录 / 频率台账

pub const USAGE_REL: &str = "protocol/knowledge_usage.json";
pub const USAGE_SCHEMA: &str = "nf-knowledge-usage/1";
const REQUIRED_ENTRY: [&str; 6] = ["from", "to", "digest", "reviewed_by", "reviewed_at", "evidence"];

fn is_dated(s: &str) -> bool {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"^\d{4}-\d{2}-\d{2}$").expect("日期正则固定合法"));
    re.is_match(s)
}

/// Python `isinstance(v, int) and v >= 0` —— **`bool` 是 `int` 的子类**，故 `true`/`false` 都算通过。
fn is_nonneg_int(j: &Json) -> bool {
    match j {
        Json::Int(n) => *n >= 0,
        Json::Float(_) => false, // Python 的 isinstance(1.0, int) 为假
        Json::Bool(_) => true,   // 子类：True>=0 与 False>=0 都为真
        _ => false,
    }
}

/// 真源 `reference_ids`。
fn reference_ids(root: &Path) -> BTreeSet<String> {
    let decl = read_json(root, DECL_REL).ok().flatten();
    decl.map(|d| {
        sources(&d)
            .iter()
            .filter(|s| py_str(get(s, "authority")) == "reference")
            .map(|s| py_str(get(s, "id")))
            .collect()
    })
    .unwrap_or_default()
}

pub struct PairIssues {
    pub issues: Vec<String>,
    pub stats: Json,
}

/// 真源 `verify_transform` → `(issues, stats)`。
pub fn verify_transform(root: &Path) -> PairIssues {
    let log = match read_json(root, LOG_REL) {
        Ok(Some(l)) => l,
        Ok(None) => Json::Object(Vec::new()),
        Err(e) => {
            return PairIssues { issues: vec![e], stats: empty_stats() }
        }
    };
    let entries = arr_items(get(&log, "entries"));
    let refs = reference_ids(root);
    let mut issues: Vec<String> = Vec::new();
    for (i, e) in entries.iter().enumerate() {
        let tag = format!("记录 #{}", i + 1);
        if !matches!(e, Json::Object(_)) {
            issues.push(format!("{} 非对象", tag));
            continue;
        }
        for k in REQUIRED_ENTRY {
            if get(e, k).is_none() {
                issues.push(format!("{} 缺必填字段：{}", tag, k));
            }
        }
        let src = py_str(get(e, "from"));
        if !src.is_empty() && !refs.contains(&src) {
            issues.push(format!("{} 的 from 不是已声明的参考级源：{}", tag, src));
        }
        let to = py_str(get(e, "to"));
        if !to.is_empty() {
            let p = root.join(&to);
            if !p.is_file() {
                issues.push(format!("{} 的产物不存在：{}", tag, to));
            } else {
                let live = std::fs::read(&p)
                    .map(|b| crate::merkle::hex(&crate::merkle::sha256(&b)))
                    .unwrap_or_default();
                if py_str(get(e, "digest")) != live {
                    issues.push(format!(
                        "{} 的产物摘要与记录不一致：{}（产物已改，记录失效；修复指引：重新消化并更新 digest）",
                        tag, to
                    ));
                }
            }
        }
        let ev: Vec<String> = arr_items(get(e, "evidence")).iter().map(|v| py_str(Some(v))).collect();
        if py_truthy(get(e, "promoted").unwrap_or(&Json::Null)) {
            let missing: Vec<&str> = TIERS.iter().copied().filter(|t| !ev.contains(&t.to_string())).collect();
            if !missing.is_empty() {
                issues.push(format!("{} 声明转正但缺证据档：{}", tag, missing.join("/")));
            }
            if py_str(get(e, "reviewed_by")).trim().is_empty() {
                issues.push(format!("{} 声明转正但无复核人（消化审核未双签）", tag));
            }
        }
        if let Some(rc) = get(e, "reuse_count") {
            if !is_nonneg_int(rc) {
                issues.push(format!("{} 的 reuse_count 非非负整数（频次判据不可复算）", tag));
            }
        }
        let ra = py_str(get(e, "reviewed_at"));
        if !ra.is_empty() && !is_dated(&ra) {
            issues.push(format!("{} 的 reviewed_at 非 YYYY-MM-DD", tag));
        }
    }
    let promoted = entries
        .iter()
        .filter(|e| matches!(e, Json::Object(_)) && py_truthy(get(e, "promoted").unwrap_or(&Json::Null)))
        .count();
    let stats = Json::Object(vec![
        ("entries".to_string(), Json::Int(entries.len() as i64)),
        ("promoted".to_string(), Json::Int(promoted as i64)),
    ]);
    PairIssues { issues, stats }
}

/// 真源 `verify_usage` → `(issues, stats)`。
pub fn verify_usage(root: &Path) -> PairIssues {
    let doc = match read_json(root, USAGE_REL) {
        Ok(Some(d)) => d,
        Ok(None) => Json::Object(Vec::new()),
        Err(e) => {
            return PairIssues { issues: vec![e], stats: empty_stats() }
        }
    };
    if crate::pyval::obj_is_empty(&doc) {
        return PairIssues {
            issues: vec![format!(
                "缺频率台账 {}（修复指引：nf knowledge frequency --trace <file> --write）",
                USAGE_REL
            )],
            stats: empty_stats(),
        };
    }
    let mut issues: Vec<String> = Vec::new();
    if py_str(get(&doc, "schema")) != USAGE_SCHEMA {
        issues.push(format!("频率台账 schema 不匹配（期望 {}）", USAGE_SCHEMA));
    }
    let counts: Json = match get(&doc, "counts") {
        Some(c @ Json::Object(_)) => c.clone(),
        Some(_) => {
            issues.push("频率台账 counts 非对象".to_string());
            Json::Object(Vec::new())
        }
        None => {
            issues.push("频率台账 counts 非对象".to_string());
            Json::Object(Vec::new())
        }
    };
    let decl = read_json(root, DECL_REL).ok().flatten();
    let ids: BTreeSet<String> = decl
        .as_ref()
        .map(|d| sources(d).iter().map(|s| py_str(get(s, "id"))).collect())
        .unwrap_or_default();
    let mut int_sum = 0i64;
    if let Json::Object(pairs) = &counts {
        for (k, v) in pairs {
            if !ids.contains(k) {
                issues.push(format!("频率台账含未声明的源：{}（防幽灵频次）", k));
            }
            if !is_nonneg_int(v) {
                issues.push(format!("频率计数非非负整数：{}", k));
            }
            if let Json::Int(n) = v {
                int_sum += n;
            }
        }
    }
    if let Some(Json::Int(total)) = get(&doc, "total") {
        if *total != int_sum {
            issues.push("频率台账 total 与 counts 求和不一致（手改痕迹）".to_string());
        }
    }
    if let Ok(Some(log)) = read_json(root, LOG_REL) {
        for e in arr_items(get(&log, "entries")) {
            if !matches!(e, Json::Object(_)) || get(e, "reuse_count").is_none() {
                continue;
            }
            let from = py_str(get(e, "from"));
            let got = match &counts {
                Json::Object(p) => p.iter().find(|(k, _)| *k == from).map(|(_, v)| v.clone()),
                _ => None,
            };
            let want = get(e, "reuse_count").cloned().unwrap_or(Json::Null);
            if got.as_ref() != Some(&want) {
                issues.push(format!(
                    "频次不可复算：{} 的记录 reuse_count={}，频率台账={}（修复指引：按 trace 重算，不要手写频次）",
                    from,
                    crate::pyval::plain_str(&want),
                    got.as_ref().map(crate::pyval::plain_str).unwrap_or_else(|| "None".to_string())
                ));
            }
        }
    }
    let stats = Json::Object(vec![
        (
            "sources_with_usage".to_string(),
            Json::Int(match &counts {
                Json::Object(p) => p.len() as i64,
                _ => 0,
            }),
        ),
        ("events".to_string(), Json::Int(int_sum)),
    ]);
    PairIssues { issues, stats }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 真源在真语料上是**全绿**的（0 issues）⇒ 只靠契约对账**核不到错误路径**。
    /// 本判据构造一个逐条踩分支的夹具，期望值由 `tools/gen_knowledge_expected.py`
    /// 从真源生成（勿手改）——这样每条消息的措辞都真的被核过。
    /// 第 5 条是**全绿样本**：证明这套判据不是空转。
    const WANT_TRANSFORM: [&str; 14] = [
            "记录 #1 非对象",
            "记录 #2 缺必填字段：from",
            "记录 #2 缺必填字段：to",
            "记录 #2 缺必填字段：digest",
            "记录 #2 缺必填字段：reviewed_by",
            "记录 #2 缺必填字段：reviewed_at",
            "记录 #2 缺必填字段：evidence",
            "记录 #3 的 from 不是已声明的参考级源：ghost",
            "记录 #3 的产物不存在：no/such.md",
            "记录 #3 声明转正但缺证据档：machine-checkable/reproducible/externally-attestable",
            "记录 #3 的 reuse_count 非非负整数（频次判据不可复算）",
            "记录 #4 的产物摘要与记录不一致：protocol/LAYERS.json（产物已改，记录失效；修复指引：重新消化并更新 digest）",
            "记录 #4 声明转正但缺证据档：machine-checkable/reproducible/externally-attestable",
            "记录 #4 声明转正但无复核人（消化审核未双签）",
    ];
    const WANT_USAGE: [&str; 6] = [
            "频率台账 schema 不匹配（期望 nf-knowledge-usage/1）",
            "频率台账含未声明的源：ghost-source（防幽灵频次）",
            "频率计数非非负整数：ext-x",
            "频率台账 total 与 counts 求和不一致（手改痕迹）",
            "频次不可复算：ghost 的记录 reuse_count=-1，频率台账=None（修复指引：按 trace 重算，不要手写频次）",
            "频次不可复算：ext-x 的记录 reuse_count=4，频率台账=-1（修复指引：按 trace 重算，不要手写频次）",
    ];


    static LOG_HEAD: std::sync::OnceLock<serde_json::Value> = std::sync::OnceLock::new();
    fn log_head() -> &'static serde_json::Value {
        LOG_HEAD.get_or_init(|| serde_json::from_str(r#"{"schema": "nf-transform-log/1", "entries": ["不是对象", {}, {"from": "ghost", "to": "no/such.md", "digest": "x", "reviewed_by": "a", "reviewed_at": "2026-13-99", "evidence": [], "reuse_count": -1, "promoted": true}, {"from": "ext-x", "to": "protocol/LAYERS.json", "digest": "deadbeef", "reviewed_by": "  ", "reviewed_at": "2026-01-01", "evidence": [], "promoted": true}]}"#).unwrap())
    }

    fn build_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("knowledge-branches");
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        std::fs::write(root.join("protocol/LAYERS.json"), "{}").unwrap();
        let real = crate::merkle::hex(&crate::merkle::sha256(b"{}"));
        std::fs::write(root.join("protocol/knowledge_sources.json"), r#"{"schema": "nf-knowledge-sources/1", "authority_vocabulary": ["contract", "reference"], "kind_vocabulary": ["local-compiled", "external-retrieval"], "visibility_vocabulary": ["public", "internal", "restricted"], "sources": [{"id": "nf-protocol", "authority": "contract", "kind": "local-compiled", "locator": "protocol/LAYERS.json", "requires_source_label": false, "visibility": "public", "freshness": {"policy": "stale_after"}}, {"id": "ext-x", "authority": "reference", "kind": "external-retrieval", "locator": "protocol/LAYERS.json", "requires_source_label": true, "visibility": "public", "freshness": {"policy": "ttl", "ttl_days": 7}}], "query_order": ["nf-protocol", "ext-x"], "promotion": {"evidence_tiers": ["machine-checkable", "reproducible", "externally-attestable"], "triggers": ["reuse-frequency", "author-mark", "machine-check-pass"], "rule": "r", "on_missing_evidence": "stay-reference"}, "review": {"machine_gates": ["g"], "rule": "r"}, "cognition": {"filter_module": "M23"}}"#).unwrap();
        let mut log = log_head().clone();
        if let Some(serde_json::Value::Array(a)) = log.get_mut("entries") {
            a.push(serde_json::json!({
                "from": "ext-x", "to": "protocol/LAYERS.json", "digest": real,
                "reviewed_by": "张三", "reviewed_at": "2026-01-01",
                "evidence": ["machine-checkable", "reproducible", "externally-attestable"],
                "promoted": true, "reuse_count": 4
            }));
        }
        std::fs::write(root.join("protocol/transform_log.json"), log.to_string()).unwrap();
        std::fs::write(root.join("protocol/knowledge_usage.json"), r#"{"schema": "wrong/1", "counts": {"ghost-source": 3, "ext-x": -1, "nf-protocol": 4}, "total": 999}"#).unwrap();
        root
    }

    #[test]
    fn verify_transform_matches_truth_source_branch_by_branch() {
        let root = build_fixture();
        let got = verify_transform(&root);
        assert_eq!(got.issues, WANT_TRANSFORM, "逐条消息须与真源一致");
        // 比 JSON 语义（对象键序无关）——`Json::Object` 的 `assert_eq!` 比的是内部向量序，
        // 而出口 `pyjson` 本就会排序，用它比会得到**假失败**。
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({"entries": 5, "promoted": 3})).unwrap()
        ));
    }

    #[test]
    fn verify_usage_matches_truth_source_branch_by_branch() {
        let root = build_fixture();
        let got = verify_usage(&root);
        assert_eq!(got.issues, WANT_USAGE, "逐条消息须与真源一致");
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(
                &serde_json::json!({"events": 6, "sources_with_usage": 3})
            )
            .unwrap()
        ));
    }
}
