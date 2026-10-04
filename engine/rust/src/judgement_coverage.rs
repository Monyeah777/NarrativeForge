//! 判据接线覆盖（`judgement_coverage`）—— 与真源 `desktop/src/core/judgement_coverage.py` 对账。
//!
//! 真源动机（一次全量审计的发现）：core 有 56 个模块暴露 `scan()`，其中 5 个**没有任何调用点**。
//! 这类「判据写好了但没接消费者」是 **"全 check PASS" 的盲区**——门禁全绿并不代表每条判据都在跑。
//!
//! 候选集 = `desktop/src/core/*.py` 中定义 `def scan(` 的模块；「被消费」= 模块名出现在任一消费者
//!（`verify.sh` / `scripts/nf.py` / `core/verify_report.py` / `core/quality_depth_scan.py`，
//! 或其它 core 模块）。未被消费且未登记 = FAIL；登记却已接线 = WARN（例外表不得虚挂）。
//!
//! **精度纪律**（真源自己踩过的坑，务必照抄）：只认「真消费」信号——`NAME.scan(...)` 属性调用、
//! `from core import NAME` 导入、注册表里的**带引号模块名**。**不认**「文件里提到过该名字」：
//! 注释、文档字符串、例外说明里出现模块名都不算消费——上一版按裸名字匹配，把例外表自己的
//! 说明文字当成了消费方，产生 5 条假「例外失效」。
//!
//! **本线的优化（不改语义）**：真源对每个候选名把所有 core 文件重读一遍（O(n²) 次读盘）；
//! 本线把文件文本读一次缓存复用。结果集相同，只少读盘。
//!
//! 本模块是 `nf verify-report` 的 `judgement_coverage` 判据，**不单独开 CLI 面**。

use crate::jsonread;
use crate::pyjson::Json;
use crate::pyval::{get, plain_str, py_str};
use std::collections::HashMap;
use std::path::Path;

pub const DECL_REL: &str = "protocol/judgement_coverage.json";
pub const SCHEMA: &str = "nf-judgement-coverage/1";
const CONSUMERS: [&str; 4] = [
    "verify.sh",
    "scripts/nf.py",
    "desktop/src/core/verify_report.py",
    "desktop/src/core/quality_depth_scan.py",
];
const REGISTRY_FILES: [&str; 2] = [
    "desktop/src/core/verify_report.py",
    "desktop/src/core/quality_depth_scan.py",
];

/// 一次调用内的文件文本缓存（真源每候选名重读全部 core 文件）。
struct TextCache {
    texts: HashMap<String, String>,
}

impl TextCache {
    fn new() -> Self {
        Self { texts: HashMap::new() }
    }
    fn get(&mut self, root: &Path, rel: &str) -> Option<&str> {
        if !self.texts.contains_key(rel) {
            let text = std::fs::read_to_string(root.join(rel)).unwrap_or_default();
            self.texts.insert(rel.to_string(), text);
        }
        self.texts.get(rel).map(|s| s.as_str())
    }
}

fn esc(name: &str) -> String {
    regex::escape(name)
}

/// 真源 `candidates`：定义了 `def scan(` 的 core 模块（按 stem 排序）。
pub fn candidates(root: &Path) -> Vec<String> {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"(?m)^def scan\(").expect("scan 定义正则固定合法"));
    let mut out: Vec<String> = crate::glob::expand(root, "desktop/src/core/*.py")
        .into_iter()
        .filter(|rel| {
            std::fs::read_to_string(root.join(rel))
                .map(|t| re.is_match(&t))
                .unwrap_or(false)
        })
        .map(|rel| {
            rel.rsplit('/')
                .next()
                .unwrap_or(&rel)
                .trim_end_matches(".py")
                .to_string()
        })
        .collect();
    out.sort();
    out
}

/// 真源 `consumers_of`。
fn consumers_of(name: &str, root: &Path, cache: &mut TextCache) -> Vec<String> {
    let call_re = regex::Regex::new(&format!(r"\b{}\s*\.\s*\w+\s*\(", esc(name))).ok();
    let import_re = regex::Regex::new(&format!(
        r"from\s+core(?:\.{})?\s+import\b[^\n]*\b{}\b",
        esc(name),
        esc(name)
    ))
    .ok();
    let quoted_re = regex::Regex::new(&format!(r#"["']{}["']"#, esc(name))).ok();

    let mut out: Vec<String> = Vec::new();
    for rel in CONSUMERS {
        let Some(text) = cache.get(root, rel) else { continue };
        let mut hit = call_re.as_ref().map(|r| r.is_match(text)).unwrap_or(false)
            || import_re.as_ref().map(|r| r.is_match(text)).unwrap_or(false);
        if !hit && REGISTRY_FILES.contains(&rel) {
            hit = quoted_re.as_ref().map(|r| r.is_match(text)).unwrap_or(false);
        }
        if hit {
            out.push(rel.to_string());
        }
    }
    let mut cores = crate::glob::expand(root, "desktop/src/core/*.py");
    cores.sort();
    for rel in cores {
        let stem = rel.rsplit('/').next().unwrap_or(&rel).trim_end_matches(".py");
        if stem == name {
            continue;
        }
        let Some(text) = cache.get(root, &rel) else { continue };
        if call_re.as_ref().map(|r| r.is_match(text)).unwrap_or(false)
            || import_re.as_ref().map(|r| r.is_match(text)).unwrap_or(false)
        {
            out.push(rel.clone());
        }
    }
    out.sort();
    out.dedup();
    out
}

/// 真源 `declaration` → `(doc, issues)`。
fn declaration(root: &Path) -> (Option<Json>, Vec<String>) {
    let p = root.join(DECL_REL);
    if !p.is_file() {
        return (
            None,
            vec![format!(
                "缺判据例外声明 {}（修复指引：新建并在 exceptions 写明未接线判据与理由）",
                DECL_REL
            )],
        );
    }
    let Some(doc) = jsonread::read_file(root, DECL_REL) else {
        return (
            None,
            vec![format!("{} 不是合法 JSON（修复指引：修好 JSON 语法）", DECL_REL)],
        );
    };
    if py_str(get(&doc, "schema")) != SCHEMA {
        return (
            None,
            vec![format!(
                "{} schema 不匹配（期望 {}）（修复指引：改为声明件当前形态）",
                DECL_REL, SCHEMA
            )],
        );
    }
    (Some(doc), Vec::new())
}

pub struct CoverageScan {
    pub issues: Vec<String>,
    pub warns: Vec<String>,
    pub stats: Json,
}

/// 真源 `scan` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> CoverageScan {
    let (doc, mut issues) = declaration(root);
    let mut warns: Vec<String> = Vec::new();
    if !issues.is_empty() {
        return CoverageScan {
            issues,
            warns,
            stats: Json::Object(vec![
                ("scanners".to_string(), Json::Int(0)),
                ("consumed".to_string(), Json::Int(0)),
                ("exceptions".to_string(), Json::Int(0)),
                ("orphans".to_string(), Json::Int(0)),
            ]),
        };
    }
    let exc: Vec<String> = match doc.as_ref().and_then(|d| get(d, "exceptions")) {
        Some(Json::Object(p)) => p.iter().map(|(k, _)| k.clone()).collect(),
        _ => Vec::new(),
    };
    let mut cache = TextCache::new();
    let cands = candidates(root);
    let mut orphans: Vec<String> = Vec::new();
    for name in &cands {
        let who = consumers_of(name, root, &mut cache);
        if who.is_empty() {
            orphans.push(name.clone());
            if !exc.contains(name) {
                issues.push(format!(
                    "判据未接线：core/{}.py 暴露 scan() 却没有任何消费者（修复指引：接进 verify.sh / nf.py / verify_report 判据表 / 其它 core 模块，或删除该死判据；确属设计用途须在 {} 的 exceptions 写明理由）",
                    name, DECL_REL
                ));
            }
        } else if exc.contains(name) {
            warns.push(format!(
                "例外已失效：core/{}.py 已被消费（{}）（修复指引：从 {} 的 exceptions 移除）",
                name, who[0], DECL_REL
            ));
        }
    }
    let stats = Json::Object(vec![
        ("scanners".to_string(), Json::Int(cands.len() as i64)),
        (
            "consumed".to_string(),
            Json::Int((cands.len() - orphans.len()) as i64),
        ),
        ("exceptions".to_string(), Json::Int(exc.len() as i64)),
        ("orphans".to_string(), Json::Int(orphans.len() as i64)),
    ]);
    let _ = plain_str(&Json::Null);
    CoverageScan { issues, warns, stats }
}