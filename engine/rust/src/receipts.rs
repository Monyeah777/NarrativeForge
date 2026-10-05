//! 协议层回执单根 —— **与 Python 真源 `desktop/src/core/receipts.py::build_scope` 逐字节对账**。
//!
//! 叶载荷 = `{"digest":<文件 sha256>,"id":<仓库相对路径>}`（紧凑无空格、键序 digest→id）；
//! 叶 = `SHA-256(0x00 ‖ 载荷)`；根 = RFC 6962 折叠。产物形态与真源 `write_scope` 落盘一致：
//! `json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"`，以 LF 写出、无 BOM。
//!
//! 只读：本模块**不写盘**，只把字节交回调用方。

use crate::merkle::{self, Hash};
use crate::pyjson::Json;
use std::path::Path;

pub const SCHEMA: &str = "nf-receipts/1";
pub const ALGORITHM: &str = "RFC6962-style sha256 domain-separated";

/// 真源 `protocol_subjects()` 的固定段——**顺序敏感**，真源按此序取件、不排序。
/// 改动本表即改变根：任何增删都必须同步 `desktop/src/core/receipts.py`。
const FIXED: [&str; 44] = [
    "STRATEGY.md",
    "01_核心协议.md",
    "02_联动注册表.md",
    "06_Agent执行协议.md",
    "07_官方核心出厂与社区预设导航.md",
    "llms.txt",
    "library/INDEX.md",
    "library/ALIAS.md",
    "protocol/event_registry.json",
    "protocol/world_slots.json",
    "protocol/export_conformance.json",
    "protocol/community_asset_ledger.json",
    "protocol/external_events.json",
    "protocol/type_backlog.json",
    "protocol/pipeline_advisory.json",
    "protocol/score_baseline.json",
    "protocol/module_signatures.json",
    "protocol/conformance_report.json",
    "protocol/asset_line_baseline.json",
    "protocol/CONFORMANCE.md",
    "protocol/driver.json",
    "protocol/rfc_index.json",
    "protocol/endpoint_contract.json",
    "protocol/knowledge_sources.json",
    "protocol/transform_log.json",
    "protocol/knowledge_usage.json",
    "protocol/assertions.json",
    "protocol/LAYERS.json",
    "protocol/locales.json",
    "protocol/release_policy.json",
    "protocol/vocabularies.json",
    "protocol/normative.json",
    "protocol/data_contracts.json",
    "decisions/INDEX.md",
    "protocol/handover.json",
    "protocol/postmortem.json",
    "protocol/audit.json",
    "protocol/glossary.json",
    "protocol/execution_modes.json",
    "protocol/st_quality.json",
    "protocol/mcp_package.json",
    "protocol/state_front.json",
    "protocol/decision_layer.json",
    "desktop/src/core/registry.json",
];

/// 目录内按名排序的匹配件 → 仓库相对 POSIX 路径。
/// 真源用 `sorted(Path.glob(...))`；因同目录前缀相同，按文件名排序与按路径排序同解。
fn glob_sorted(root: &Path, rel_dir: &str, prefix: &str, suffix: &str) -> Vec<String> {
    let mut names: Vec<String> = Vec::new();
    if let Ok(rd) = std::fs::read_dir(root.join(rel_dir)) {
        for entry in rd.flatten() {
            let name = entry.file_name().to_string_lossy().into_owned();
            if name.starts_with(prefix) && name.ends_with(suffix) {
                names.push(name);
            }
        }
    }
    names.sort();
    names
        .into_iter()
        .map(|n| format!("{}/{}", rel_dir, n))
        .collect()
}

/// 真源 `protocol_subjects(root)`：固定段（原序）→ `protocol/schema/*.json`（排序）
/// → `decisions/ADR-*.md`（排序）→ 过滤掉不存在的件。
pub fn protocol_subjects(root: &Path) -> Vec<String> {
    let mut subs: Vec<String> = FIXED.iter().map(|s| (*s).to_string()).collect();
    subs.extend(glob_sorted(root, "protocol/schema", "", ".json"));
    subs.extend(glob_sorted(root, "decisions", "ADR-", ".md"));
    subs.retain(|rel| root.join(rel).is_file());
    subs
}

/// 叶载荷字节：`{"digest":"…","id":"…"}`（紧凑、键序）。
fn payload_bytes(rel: &str, digest_hex: &str) -> Vec<u8> {
    Json::Object(vec![
        ("digest".to_string(), Json::Str(digest_hex.to_string())),
        ("id".to_string(), Json::Str(rel.to_string())),
    ])
    .dumps_compact()
    .into_bytes()
}

/// 真源 `build_scope(root, scope="protocol")` 的等价物（以 `Json` 值形态返回）。
pub fn build_scope(root: &Path, scope: &str) -> Json {
    let rels = protocol_subjects(root);

    struct Row {
        rel: String,
        digest: String,
        payload: Vec<u8>,
    }

    let mut rows: Vec<Row> = Vec::with_capacity(rels.len());
    let mut leaves: Vec<Hash> = Vec::with_capacity(rels.len());

    for rel in rels {
        let bytes = match std::fs::read(root.join(&rel)) {
            Ok(b) => b,
            Err(_) => continue, // 真源在此亦跳过；subjects 已按 is_file 过滤，此处为兜底
        };
        let digest = merkle::hex(&merkle::sha256(&bytes));
        let payload = payload_bytes(&rel, &digest);
        leaves.push(merkle::leaf_hash(&payload));
        rows.push(Row { rel, digest, payload });
    }

    let root_hash = merkle::merkle_root(&leaves);
    let entries: Vec<Json> = rows
        .iter()
        .enumerate()
        .map(|(i, row)| {
            let leaf = merkle::leaf_hash(&row.payload);
            let proof: Vec<Json> = merkle::inclusion_proof(&leaves, i)
                .iter()
                .map(|step| {
                    Json::Object(vec![
                        ("hash".to_string(), Json::Str(merkle::hex(&step.hash))),
                        (
                            "side".to_string(),
                            Json::Str(
                                if step.sibling_is_left { "left" } else { "right" }.to_string(),
                            ),
                        ),
                    ])
                })
                .collect();
            Json::Object(vec![
                ("id".to_string(), Json::Str(row.rel.clone())),
                ("path".to_string(), Json::Str(row.rel.clone())),
                ("digest".to_string(), Json::Str(row.digest.clone())),
                ("leaf".to_string(), Json::Str(merkle::hex(&leaf))),
                ("proof".to_string(), Json::Array(proof)),
            ])
        })
        .collect();

    Json::Object(vec![
        ("schema".to_string(), Json::Str(SCHEMA.to_string())),
        ("scope".to_string(), Json::Str(scope.to_string())),
        (
            "root".to_string(),
            Json::Str(root_hash.map(|h| merkle::hex(&h)).unwrap_or_default()),
        ),
        ("count".to_string(), Json::Int(entries.len() as i64)),
        ("algorithm".to_string(), Json::Str(ALGORITHM.to_string())),
        ("entries".to_string(), Json::Array(entries)),
    ])
}

/// 真源 `write_scope` 的**落盘字节**（LF、末尾换行、无 BOM）。只返回字节，不写盘。
pub fn build_scope_bytes(root: &Path, scope: &str) -> Vec<u8> {
    build_scope(root, scope).dumps_file().into_bytes()
}

/// 自校验：每条回执的审计路径必须折叠回根（真源 `verify_scope` 的自洽判据）。
pub fn self_check(root: &Path, scope: &str) -> Vec<String> {
    let doc = build_scope(root, scope);
    let mut issues = Vec::new();
    let Json::Object(pairs) = &doc else {
        return vec!["内部错误：回执非对象".to_string()];
    };
    let get = |k: &str| pairs.iter().find(|(n, _)| n == k).map(|(_, v)| v);
    let root_hex = match get("root") {
        Some(Json::Str(s)) => s.clone(),
        _ => return vec!["内部错误：缺根".to_string()],
    };
    if let Some(Json::Array(entries)) = get("entries") {
        for e in entries {
            let Json::Object(ep) = e else { continue };
            let g = |k: &str| ep.iter().find(|(n, _)| n == k).map(|(_, v)| v);
            let (Some(Json::Str(id)), Some(Json::Str(leaf_hex)), Some(Json::Array(proof))) =
                (g("id"), g("leaf"), g("proof"))
            else {
                continue;
            };
            let mut leaf = [0u8; 32];
            if !unhex_into(leaf_hex, &mut leaf) {
                issues.push(format!("回执 leaf 非法：{}", id));
                continue;
            }
            let mut steps = Vec::with_capacity(proof.len());
            for st in proof {
                let Json::Object(sp) = st else { continue };
                let gs = |k: &str| sp.iter().find(|(n, _)| n == k).map(|(_, v)| v);
                let (Some(Json::Str(h)), Some(Json::Str(side))) = (gs("hash"), gs("side")) else {
                    continue;
                };
                let mut hb = [0u8; 32];
                if !unhex_into(h, &mut hb) {
                    continue;
                }
                steps.push(merkle::ProofStep { sibling_is_left: side == "left", hash: hb });
            }
            if merkle::hex(&merkle::fold_proof(&leaf, &steps)) != root_hex {
                issues.push(format!("包含证明不折叠到根：{}", id));
            }
        }
    }
    issues
}

fn unhex_into(s: &str, out: &mut [u8; 32]) -> bool {
    if s.len() != 64 {
        return false;
    }
    let b = s.as_bytes();
    for i in 0..32 {
        let hi = (b[i * 2] as char).to_digit(16);
        let lo = (b[i * 2 + 1] as char).to_digit(16);
        match (hi, lo) {
            (Some(h), Some(l)) => out[i] = ((h << 4) | l) as u8,
            _ => return false,
        }
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixed_table_matches_python_source() {
        assert_eq!(FIXED.len(), 42, "固定段条数必须与 receipts.py 同步");
        assert_eq!(FIXED[0], "STRATEGY.md");
        assert_eq!(FIXED[41], "desktop/src/core/registry.json");
    }

    #[test]
    fn payload_shape_is_compact_and_sorted() {
        let p = payload_bytes("a.md", "00ff");
        assert_eq!(
            String::from_utf8(p).unwrap(),
            "{\"digest\":\"00ff\",\"id\":\"a.md\"}"
        );
    }

    #[test]
    fn non_ascii_id_is_raw_utf8() {
        let p = payload_bytes("decisions/ADR-0005-新增NET引擎线.md", "ab");
        assert_eq!(
            String::from_utf8(p).unwrap(),
            "{\"digest\":\"ab\",\"id\":\"decisions/ADR-0005-新增NET引擎线.md\"}"
        );
    }
}
