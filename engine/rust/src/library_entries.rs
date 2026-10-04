//! 馆藏条目读取（**叶子件**）—— 与真源 `desktop/src/core/library_entries.py` 对账。
//!
//! 真源 2026-09-29 把它从 `library` 拆出来，专为断 `receipts ↔ library` 的双向依赖：
//! 条目读取（frontmatter 解析 + 摘要）本就是纯数据面。本线同样只留一份。
//!
//! 编码纪律（真源注释里记着的实测事故）：馆藏是**外来内容**，一个非 UTF-8 文件曾让整面瘫痪。
//! 现为**降级读取 + 如实登记**——不静默丢条目，也不让单个坏文件拖垮整面。
//!
//! **已知近似**：真源在降级读取时把 Python 的 `UnicodeDecodeError` 文本拼进 `decode_issue`；
//! 本线的措辞是自拟的（真源语料无此情形）。

use crate::mdblocks::parse_frontmatter;
use crate::pyjson::Json;
use crate::pyval::get;
use std::path::Path;

pub const ENTRY_GLOB: &str = "library/NF-*.md";

pub struct Entry {
    /// 仓库相对 POSIX 路径
    pub path: String,
    pub id: String,
    pub fm: Json,
    /// 真源 `read_entry` 的返回里带正文与全文（`audit`/`steelman` 那条线要用）。
    /// 本线当前消费者只读 `fm`/`id`，但**刻意保留**：删掉会让下一个移植者去改结构。
    #[allow(dead_code)]
    pub body: String,
    #[allow(dead_code)]
    pub text: String,
    pub decode_issue: String,
}

/// 真源 `entries`：按编号排序。
pub fn entries(root: &Path) -> Vec<Entry> {
    let mut out: Vec<Entry> = crate::glob::expand(root, ENTRY_GLOB)
        .into_iter()
        .map(|rel| read_entry(root, &rel))
        .collect();
    out.sort_by(|a, b| a.id.cmp(&b.id));
    out
}

/// 真源 `read_entry`：降级读取 + 如实登记（`rel` 为仓库相对路径）。
pub fn read_entry(root: &Path, rel: &str) -> Entry {
    let stem = Path::new(rel)
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    let mut decode_issue = String::new();
    let text = match std::fs::read(root.join(rel)) {
        Ok(raw) => match String::from_utf8(raw) {
            Ok(t) => t,
            Err(e) => {
                decode_issue = format!(
                    "{} 非合法 UTF-8（{}）；已按替换字符降级读取（修复指引：把该文件另存为 UTF-8 后重跑 nf library verify）",
                    stem,
                    e.utf8_error()
                );
                String::from_utf8_lossy(e.as_bytes()).to_string()
            }
        },
        Err(_) => String::new(),
    };
    let (fm, body) = parse_frontmatter(&text);
    Entry {
        path: rel.to_string(),
        id: stem,
        fm,
        body,
        text,
        decode_issue,
    }
}

/// 真源 `entry_digest`：剔除签名/锚字段行后的整文件 sha256。
///
/// **自指避免**：签名值与锚字段不能参与自身摘要，否则每次落签都会自我失效。
/// 注意「剔行」的口径——真源是 `"\n".join(去行后的 split("\n"))`，
/// 故签名行的增删**不改变**摘要（留下的空行正好抵消），而正文任何改动都会改。
pub fn entry_digest(root: &Path, rel: &str) -> String {
    let text = std::fs::read_to_string(root.join(rel))
        .unwrap_or_default()
        .replace("\r\n", "\n");
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| {
        regex::Regex::new(r"^(attestation|attested_at|anchor_[a-z_]+)\s*:")
            .expect("签名行正则固定合法")
    });
    let kept: Vec<&str> = text.split('\n').filter(|ln| !re.is_match(ln)).collect();
    crate::merkle::hex(&crate::merkle::sha256(kept.join("\n").as_bytes()))
}


/// 真源 `k not in fm` 是**键在场**判断，不是真值判断。
pub fn has_key(fm: &Json, k: &str) -> bool {
    get(fm, k).is_some()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn digest_is_invariant_to_signature_lines_but_not_to_body() {
        let tmp = crate::testutil::fixture("lib-digest");
        std::fs::create_dir_all(tmp.join("library")).unwrap();
        let base = "---\nid: NF-1\ntitle: t\n---\nbody\n";
        std::fs::write(tmp.join("library/NF-1.md"), base).unwrap();
        let a = entry_digest(&tmp, "library/NF-1.md");

        // 加上签名行：**摘要必须不变**（自指避免 —— 否则每次落签都自我失效）
        std::fs::write(
            tmp.join("library/NF-1.md"),
            format!("{}attestation: {}\nanchor_mac: x\n", base, "0".repeat(64)),
        )
        .unwrap();
        let b = entry_digest(&tmp, "library/NF-1.md");
        assert_eq!(a, b, "签名行的增删不得改变摘要");

        // 只改签名**值**：仍不变
        std::fs::write(
            tmp.join("library/NF-1.md"),
            format!("{}attestation: {}\nanchor_mac: x\n", base, "f".repeat(64)),
        )
        .unwrap();
        assert_eq!(b, entry_digest(&tmp, "library/NF-1.md"), "签名值不得进摘要");

        // 改正文：必须变
        std::fs::write(
            tmp.join("library/NF-1.md"),
            format!("{}attestation: {}\nanchor_mac: x\n", "---\nid: NF-1\ntitle: t\n---\nBODY2\n", "f".repeat(64)),
        )
        .unwrap();
        assert_ne!(b, entry_digest(&tmp, "library/NF-1.md"), "正文改动必须改摘要");
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn has_key_is_presence_not_truthiness() {
        let fm = crate::jsonread::convert(&serde_json::json!({"status": [], "x": ""})).unwrap();
        assert!(has_key(&fm, "status"), "空列表也算在场");
        assert!(has_key(&fm, "x"));
        assert!(!has_key(&fm, "absent"));
    }
}
