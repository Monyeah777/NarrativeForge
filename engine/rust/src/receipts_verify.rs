//! 馆藏回执校验（真源 `receipts.verify`）—— `nf verify-report` 的 `receipts` 判据。
//!
//! 判据：每条回执**折叠到根** + 根与**实时重算**一致（防挑单条伪造、防整体替换）+ 条数一致。
//!
//! **移植面按消费者界定**：真源 `build(root)` 还产出每条的 `anchor`（签收要素），但 `verify`
//! **只读** `root` / `count` / 每条 `id`·`digest`，故本模块只算这三样——
//! 不写「没人核」的代码面（与 `machine_contract` 只移植 `id` 那条路径同一取舍）。
//!
//! ⚠️ 真源 `verify` 在 `doc["entries"]` 里遇到**非对象**条目会抛 `AttributeError`
//! （整条判据记 ERROR）；本线跳过该条并继续。这条差异无法逐字比对，已在 README「已知偏差」记录。

use crate::jsonread;
use crate::merkle;
use crate::pyjson::Json;
use crate::pyval::{get, plain_str, py_str};
use std::path::Path;

/// 真源 `RECEIPTS_REL`（馆藏面）。
pub const LIBRARY_RECEIPTS_REL: &str = "library/RECEIPTS.json";

/// Python `str(x)[:16]`（**按字符**截断，不是字节）。
fn head16(j: Option<&Json>) -> String {
    let s = match j {
        Some(v) => plain_str(v),
        None => "None".to_string(),
    };
    s.chars().take(16).collect()
}

fn payload_bytes(id: &str, digest_hex: &str) -> Vec<u8> {
    Json::Object(vec![
        ("digest".to_string(), Json::Str(digest_hex.to_string())),
        ("id".to_string(), Json::Str(id.to_string())),
    ])
    .dumps_compact()
    .into_bytes()
}

/// 真源 `verify(doc, root)` → `(issues, stats)`。
pub fn verify(root: &Path) -> (Vec<String>, Json) {
    let empty = Json::Object(Vec::new());
    let doc = match jsonread::read_file(root, LIBRARY_RECEIPTS_REL) {
        Some(d) => d,
        None => {
            return (
                vec![format!("回执文件 schema 不匹配（期望 {}）", crate::receipts::SCHEMA)],
                empty,
            )
        }
    };
    if !matches!(doc, Json::Object(_)) || py_str(get(&doc, "schema")) != crate::receipts::SCHEMA {
        return (
            vec![format!("回执文件 schema 不匹配（期望 {}）", crate::receipts::SCHEMA)],
            empty,
        );
    }

    // 实时重算（只算 verify 要用的三样）
    let rows = crate::library_entries::entries(root);
    let mut leaves: Vec<merkle::Hash> = Vec::with_capacity(rows.len());
    let mut live_by_id: Vec<(String, String)> = Vec::with_capacity(rows.len());
    for e in &rows {
        let digest = crate::library_entries::entry_digest(root, &e.path);
        let payload = payload_bytes(&e.id, &digest);
        leaves.push(merkle::leaf_hash(&payload));
        live_by_id.push((e.id.clone(), digest));
    }
    let live_root = merkle::merkle_root(&leaves).map(|h| merkle::hex(&h)).unwrap_or_default();

    let mut issues: Vec<String> = Vec::new();
    if py_str(get(&doc, "root")) != live_root {
        issues.push(format!(
            "根不一致：记录={} 实测={}（修复指引：馆藏改动后跑 nf library receipts --write）",
            head16(get(&doc, "root")),
            live_root.chars().take(16).collect::<String>()
        ));
    }

    let entries = match get(&doc, "entries") {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    };
    for e in &entries {
        if !matches!(e, Json::Object(_)) {
            continue; // 真源在此抛异常（整条记 ERROR）；本线跳过，见模块头
        }
        let eid = py_str(get(e, "id"));
        let Some((_, live_digest)) = live_by_id.iter().find(|(i, _)| *i == eid) else {
            issues.push(format!("回执指向不存在的条目：{}", eid));
            continue;
        };
        if py_str(get(e, "digest")) != *live_digest {
            issues.push(format!("条目内容已变：{}（修复指引：重签该条并重建回执）", eid));
        }
        if fold_of(e) != live_root {
            issues.push(format!("包含证明不折叠到根：{}", eid));
        }
    }
    if entries.len() != rows.len() {
        issues.push(format!(
            "回执条数 {} ≠ 馆藏条数 {}",
            entries.len(),
            rows.len()
        ));
    }

    let stats = Json::Object(vec![
        ("entries".to_string(), Json::Int(rows.len() as i64)),
        ("root".to_string(), Json::Str(live_root)),
    ]);
    (issues, stats)
}

/// 从回执条目里取 `leaf`/`proof` 并折叠；形状非法即返回空（必不相等 → 判「不折叠到根」）。
fn fold_of(e: &Json) -> String {
    let Some(Json::Str(leaf_hex)) = get(e, "leaf") else {
        return String::new();
    };
    let mut leaf = [0u8; 32];
    if !unhex(leaf_hex, &mut leaf) {
        return String::new();
    }
    let mut steps: Vec<merkle::ProofStep> = Vec::new();
    if let Some(Json::Array(items)) = get(e, "proof") {
        for it in items {
            let (Some(Json::Str(h)), Some(Json::Str(side))) = (get(it, "hash"), get(it, "side"))
            else {
                return String::new();
            };
            let mut hb = [0u8; 32];
            if !unhex(h, &mut hb) {
                return String::new();
            }
            steps.push(merkle::ProofStep { sibling_is_left: side == "left", hash: hb });
        }
    }
    merkle::hex(&merkle::fold_proof(&leaf, &steps))
}

fn unhex(s: &str, out: &mut [u8; 32]) -> bool {
    if s.len() != 64 {
        return false;
    }
    for i in 0..32 {
        let Ok(b) = u8::from_str_radix(&s[i * 2..i * 2 + 2], 16) else {
            return false;
        };
        out[i] = b;
    }
    true
}
