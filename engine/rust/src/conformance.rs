//! `nf conformance` 封缄内核 —— **与 Python 真源 `desktop/src/core/conformance_report.py`
//! 的 `_run_impl` 逐字节对账**。
//!
//! 内核做什么：把 N 条契约裁决 `(id, ok, detail)` → 封缄成一份**防篡改报告**——
//! 每条契约一个内容摘要，全部摘要再折成一棵 RFC 6962 Merkle 根。改任何一个字符，
//! 该条摘要与整份根都会变。
//!
//! 真源的三处公式（逐字对照，任何一处抄错根就对不上）：
//! 1. 契约摘要载荷 = `json.dumps({"id","ok","detail"}, sort_keys, ensure_ascii=False,
//!    separators=(",",":"))` → `{"detail":…,"id":…,"ok":…}`
//! 2. 叶载荷 = `json.dumps({"id","digest"}, sort_keys, separators=(",",":"))`
//!    ——**注意真源此处未传 `ensure_ascii=False`**（默认 `ensure_ascii=True`）。因载荷只含
//!    ASCII 十六进制与 ASCII id，两种写法同形；本线按同形实现并在此注明，以免日后误判。
//! 3. 根 = `receipts.merkle_root`（与 `receipts.rs` 同一折叠规则）
//!
//! **边界**：本模块只做「裁决 → 封缄」。27 条契约各自的扫描实现**尚未移植**——
//! 裁决由调用方（当前是 Python 真源）给出。不得对外宣称本线能独立跑出一致性报告。

use crate::merkle;
use crate::pyjson::Json;
use std::path::Path;

pub const SCHEMA: &str = "nf-conformance/1";

/// 一条契约裁决（真源 `CONTRACTS` 三元组的运行结果）。
#[derive(Clone, Debug, PartialEq)]
pub struct Row {
    pub id: String,
    pub ok: bool,
    pub detail: String,
    pub description: String,
    /// 输入里若带摘要（真源 `run()` 的产物），用于**差分核对**；本线不信任它。
    pub recorded_digest: Option<String>,
}

/// 契约摘要载荷：`{"detail":…,"id":…,"ok":…}`（紧凑、键序）。
fn digest_payload(row: &Row) -> Vec<u8> {
    Json::Object(vec![
        ("id".to_string(), Json::Str(row.id.clone())),
        ("ok".to_string(), Json::Bool(row.ok)),
        ("detail".to_string(), Json::Str(row.detail.clone())),
    ])
    .dumps_compact()
    .into_bytes()
}

/// 叶载荷：`{"digest":…,"id":…}`（紧凑、键序）。
fn leaf_payload(id: &str, digest_hex: &str) -> Vec<u8> {
    Json::Object(vec![
        ("id".to_string(), Json::Str(id.to_string())),
        ("digest".to_string(), Json::Str(digest_hex.to_string())),
    ])
    .dumps_compact()
    .into_bytes()
}

/// 单条契约的内容摘要（sha256 十六进制）。
pub fn row_digest(row: &Row) -> String {
    merkle::hex(&merkle::sha256(&digest_payload(row)))
}

/// 真源 `_run_impl` 的等价物：裁决序列 → 封缄报告（`Json` 值形态）。
pub fn seal(rows: &[Row]) -> Json {
    let digests: Vec<String> = rows.iter().map(row_digest).collect();

    let leaves: Vec<merkle::Hash> = rows
        .iter()
        .zip(digests.iter())
        .map(|(r, d)| merkle::leaf_hash(&leaf_payload(&r.id, d)))
        .collect();
    let root = merkle::merkle_root(&leaves).map(|h| merkle::hex(&h)).unwrap_or_default();

    let contracts: Vec<Json> = rows
        .iter()
        .zip(digests.iter())
        .map(|(r, d)| {
            Json::Object(vec![
                ("id".to_string(), Json::Str(r.id.clone())),
                ("ok".to_string(), Json::Bool(r.ok)),
                ("detail".to_string(), Json::Str(r.detail.clone())),
                ("description".to_string(), Json::Str(r.description.clone())),
                ("digest".to_string(), Json::Str(d.clone())),
            ])
        })
        .collect();

    let passed = rows.iter().filter(|r| r.ok).count() as i64;
    Json::Object(vec![
        ("schema".to_string(), Json::Str(SCHEMA.to_string())),
        ("contracts".to_string(), Json::Array(contracts)),
        ("passed".to_string(), Json::Int(passed)),
        ("total".to_string(), Json::Int(rows.len() as i64)),
        ("root".to_string(), Json::Str(root)),
        (
            "verdict".to_string(),
            Json::Str(if rows.iter().all(|r| r.ok) { "conformant" } else { "non-conformant" }.to_string()),
        ),
    ])
}

/// 真源 `write` 的落盘字节（LF、末尾换行、无 BOM）。只返回字节，不写盘。
pub fn seal_bytes(rows: &[Row]) -> Vec<u8> {
    seal(rows).dumps_file().into_bytes()
}

/// 单条契约的行对象（真源 `_run_impl` 里 `rows.append({...})` 的同形物）。
pub fn row_json(row: &Row) -> Json {
    Json::Object(vec![
        ("id".to_string(), Json::Str(row.id.clone())),
        ("ok".to_string(), Json::Bool(row.ok)),
        ("detail".to_string(), Json::Str(row.detail.clone())),
        ("description".to_string(), Json::Str(row.description.clone())),
        ("digest".to_string(), Json::Str(row_digest(row))),
    ])
}

/// 差分核对：输入行若自带 `digest`，与本线重算值逐条比对（**不信任输入**）。
pub fn digest_mismatches(rows: &[Row]) -> Vec<String> {
    let mut out = Vec::new();
    for r in rows {
        if let Some(rec) = &r.recorded_digest {
            let mine = row_digest(r);
            if *rec != mine {
                out.push(format!(
                    "契约摘要不一致：{}（记录={} 实测={}）",
                    r.id,
                    &rec[..rec.len().min(16)],
                    &mine[..mine.len().min(16)]
                ));
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn row(id: &str, ok: bool, detail: &str) -> Row {
        Row {
            id: id.into(),
            ok,
            detail: detail.into(),
            description: "d".into(),
            recorded_digest: None,
        }
    }

    #[test]
    fn digest_payload_shape_matches_python_compact_dumps() {
        let r = row("a-b", true, "全绿");
        assert_eq!(
            String::from_utf8(digest_payload(&r)).unwrap(),
            "{\"detail\":\"全绿\",\"id\":\"a-b\",\"ok\":true}"
        );
    }

    #[test]
    fn leaf_payload_shape_is_digest_then_id() {
        assert_eq!(
            String::from_utf8(leaf_payload("x", "00ff")).unwrap(),
            "{\"digest\":\"00ff\",\"id\":\"x\"}"
        );
    }

    #[test]
    fn empty_rows_give_empty_root_and_conformant() {
        let doc = seal(&[]);
        let Json::Object(pairs) = &doc else { panic!() };
        let get = |k: &str| pairs.iter().find(|(n, _)| n == k).map(|(_, v)| v.clone());
        assert_eq!(get("root"), Some(Json::Str(String::new())));
        assert_eq!(get("total"), Some(Json::Int(0)));
        assert_eq!(get("verdict"), Some(Json::Str("conformant".into())));
    }

    #[test]
    fn one_contract_digest_is_stable_across_field_order() {
        let a = row("x", false, "boom");
        let b = Row { id: "x".into(), ok: false, detail: "boom".into(), description: "zzz".into(), recorded_digest: None };
        // description 不参与摘要 —— 只有 (id, ok, detail) 进载荷
        assert_eq!(row_digest(&a), row_digest(&b));
    }

    #[test]
    fn changing_one_byte_changes_digest_and_root() {
        let base = vec![row("a", true, "ok"), row("b", true, "ok")];
        let mutated = vec![row("a", true, "ok"), row("b", true, "oK")];
        let r1 = seal(&base);
        let r2 = seal(&mutated);
        assert_ne!(r1.dumps(), r2.dumps());
    }

    #[test]
    fn verdict_reflects_any_failure() {
        let doc = seal(&[row("a", true, "ok"), row("b", false, "bad")]);
        assert!(doc.dumps().contains("\"non-conformant\""));
    }

    #[test]
    fn recorded_digest_mismatch_is_reported() {
        let mut r = row("a", true, "ok");
        r.recorded_digest = Some("00".repeat(32));
        assert_eq!(digest_mismatches(&[r]).len(), 1);
        let mut r2 = row("a", true, "ok");
        r2.recorded_digest = Some(row_digest(&r2.clone()));
        assert!(digest_mismatches(&[r2]).is_empty());
    }

    #[test]
    fn order_matters_for_root() {
        let ab = seal(&[row("a", true, "1"), row("b", true, "2")]);
        let ba = seal(&[row("b", true, "2"), row("a", true, "1")]);
        assert_ne!(ab.dumps(), ba.dumps());
    }
}

// >>> GENERATED by tools/gen_contract_order.py（勿手改；重跑生成器覆盖本段）
/// 真源 `CONTRACTS` 的**定义顺序**——Merkle 叶序由它决定，顺序错了封缄根就错。
#[rustfmt::skip]
pub const CONTRACT_ORDER: [&str; 27] = [
    "canonical-digest-determinism",
    "schema-clean",
    "purity-clean",
    "doc-kinds",
    "library-verify",
    "library-projection",
    "pipeline-dryrun",
    "module-signature",
    "io-types",
    "type-backlog",
    "event-backing",
    "declaration",
    "rfc-heads",
    "patterns",
    "endpoint-contract",
    "knowledge-sources",
    "assertions",
    "modeling",
    "decisions",
    "handover",
    "postmortem",
    "audit",
    "cognition",
    "st-quality",
    "mcp-package",
    "state-front",
    "public-surface",
];
// <<< GENERATED

// ---------------------------------------------------------------- 全量实时重算 + 在盘报告核对

/// 真源 `conformance_report._run_impl` 的等价物：**按真源定义顺序**跑全部 27 条契约 → 封缄报告。
///
/// 顺序由 `CONTRACT_ORDER` 决定（真源转录）——Merkle 叶序依赖它，顺序错了根就错。
pub fn run_live(root: &Path) -> Json {
    let rows: Vec<Row> = CONTRACT_ORDER
        .iter()
        .map(|id| {
            let (ok, detail) = match crate::contracts::run(id, root) {
                Some(v) => v,
                // 真源把契约自身异常算不通过；本线把"未登记/未分派"也算不通过（不静默）
                None => (false, "契约未登记或未分派".to_string()),
            };
            Row {
                id: (*id).to_string(),
                ok,
                detail,
                description: crate::contracts::description(id).unwrap_or("").to_string(),
                recorded_digest: None,
            }
        })
        .collect();
    seal(&rows)
}

/// 真源 `conformance_report.verify_committed`：**在盘报告 == 实时重算**。
pub const REPORT_REL: &str = "protocol/conformance_report.json";

pub fn verify_committed(root: &Path) -> (Vec<String>, Json) {
    let p = root.join(REPORT_REL);
    if !p.is_file() {
        return (
            vec![format!("缺一致性报告 {}（修复指引：nf conformance --write）", REPORT_REL)],
            Json::Object(vec![]),
        );
    }
    let raw = match std::fs::read_to_string(&p) {
        Ok(s) => s,
        Err(e) => return (vec![format!("报告不可读：{}", e)], Json::Object(vec![])),
    };
    let committed = match crate::jsonread::convert(
        &serde_json::from_str::<serde_json::Value>(&raw).map_err(|e| e.to_string()).unwrap_or(
            serde_json::Value::Null,
        ),
    ) {
        Ok(v) => v,
        Err(e) => return (vec![format!("报告 JSON 不可解析：{}", e)], Json::Object(vec![])),
    };
    let live = run_live(root);
    let mut issues: Vec<String> = Vec::new();
    let g = |v: &Json, k: &str| -> Option<Json> {
        match v {
            Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv.clone()),
            _ => None,
        }
    };
    if g(&committed, "root") != g(&live, "root") {
        issues.push(format!(
            "报告过期或被改：root 记录={} 实测={}（修复指引：nf conformance --write）",
            crate::pyval::plain_str(&g(&committed, "root").unwrap_or(Json::Null))
                .chars()
                .take(16)
                .collect::<String>(),
            crate::pyval::plain_str(&g(&live, "root").unwrap_or(Json::Null))
                .chars()
                .take(16)
                .collect::<String>(),
        ));
    }
    if g(&committed, "verdict") != g(&live, "verdict") {
        issues.push(format!(
            "verdict 不一致：记录={} 实测={}",
            crate::pyval::py_str(Some(&g(&committed, "verdict").unwrap_or(Json::Null))),
            crate::pyval::py_str(Some(&g(&live, "verdict").unwrap_or(Json::Null))),
        ));
    }
    let stats = Json::Object(vec![
        ("contracts".to_string(), g(&live, "total").unwrap_or(Json::Int(0))),
        ("passed".to_string(), g(&live, "passed").unwrap_or(Json::Int(0))),
        ("verdict".to_string(), g(&live, "verdict").unwrap_or(Json::Null)),
        ("root".to_string(), g(&live, "root").unwrap_or(Json::Null)),
    ]);
    (issues, stats)
}

