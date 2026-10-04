//! 一致性**声明**门禁（`declaration`）—— 与真源 `desktop/src/core/conformance_decl.py` 对账。
//!
//! `protocol/CONFORMANCE.md` 三段（机器按标题解析）：`## 声明`（规范 × 版本 × 真源，版本值须与
//! 真源**逐条一致**）/ `## 范围`（scope 白名单，路径须存在）/ `## 排除`（显式排除清单）。
//! 硬约束：**scope ∩ 排除 = ∅**。反向也判：声明了真源里没有的规范项 = 无法核验的声明。
//!
//! 纪律：版本事实一律**从真源读**——声明里改数字改不动门禁。

use crate::jsonread;
use crate::pyval::{get, plain_str_opt};
use std::path::Path;

pub const DECL_REL: &str = "protocol/CONFORMANCE.md";

fn re_row() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"^\|\s*`?([^`|]+?)`?\s*\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|\s*$")
            .expect("三段行正则固定合法")
    })
}

fn re_row2() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"^\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|\s*$")
            .expect("两段行正则固定合法")
    })
}

fn re_bullet() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^\s*[-*]\s+`([^`]+)`").expect("bullet 正则固定合法"))
}

fn re_sep() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^[-: ]+$").expect("分隔行正则固定合法"))
}

/// 真源 `_section`：取 `## <title>` 到下一个同级标题之间的行。
fn section(text: &str, title: &str) -> Vec<String> {
    let lines: Vec<&str> = text.lines().collect();
    let want = format!("## {}", title);
    let mut start: Option<usize> = None;
    for (i, ln) in lines.iter().enumerate() {
        if ln.trim() == want {
            start = Some(i + 1);
            continue;
        }
        if start.is_some() && ln.starts_with("## ") {
            return lines[start.unwrap()..i].iter().map(|s| (*s).to_string()).collect();
        }
    }
    match start {
        Some(s) => lines[s..].iter().map(|x| (*x).to_string()).collect(),
        None => Vec::new(),
    }
}

/// 真源 `parse` → `(versions 顺序表, scope, excluded)`。
pub struct Decl {
    /// (name, version, source)，**同键覆盖**（真源是 dict）
    pub versions: Vec<(String, String, String)>,
    pub scope: Vec<String>,
    pub excluded: Vec<(String, String)>,
}

pub fn parse(root: &Path) -> Decl {
    let p = root.join(DECL_REL);
    let text = if p.is_file() {
        std::fs::read_to_string(&p).unwrap_or_default()
    } else {
        String::new()
    };

    let mut versions: Vec<(String, String, String)> = Vec::new();
    for ln in section(&text, "声明") {
        let Some(c) = re_row().captures(ln.trim()) else { continue };
        let name = c[1].trim().to_string();
        if name == "规范" || re_sep().is_match(&name) {
            continue;
        }
        let rec = (name.clone(), c[2].trim().to_string(), c[3].trim().to_string());
        match versions.iter_mut().find(|(n, _, _)| *n == name) {
            Some(slot) => *slot = rec,
            None => versions.push(rec),
        }
    }

    let mut scope: Vec<String> = Vec::new();
    for ln in section(&text, "范围") {
        if let Some(c) = re_bullet().captures(&ln) {
            scope.push(c[1].trim().to_string());
        }
    }

    let mut excluded: Vec<(String, String)> = Vec::new();
    for ln in section(&text, "排除") {
        let m = re_row2().captures(ln.trim());
        let cell = m.as_ref().map(|c| c[1].trim().to_string()).unwrap_or_default();
        if let Some(c) = m {
            if cell != "路径" && !re_sep().is_match(&cell) {
                excluded.push((c[1].trim().to_string(), c[2].trim().to_string()));
            }
        }
    }

    Decl { versions, scope, excluded }
}

/// 真源 `live_versions`：版本真源（声明必须与这里一致）。
pub fn live_versions(root: &Path) -> Vec<(String, String)> {
    let mut out: Vec<(String, String)> = Vec::new();

    let reg = root.join("desktop/src/core/registry.json");
    if reg.is_file() {
        let v = jsonread::read_file(root, "desktop/src/core/registry.json")
            .map(|d| plain_str_opt(get(&d, "registry_schema_version")))
            .unwrap_or_default();
        out.push(("registry schema".to_string(), v));
    }

    let contract = root.join("protocol/schema/contract.schema.json");
    if contract.is_file() {
        let enum_vals: Vec<String> = jsonread::read_file(root, "protocol/schema/contract.schema.json")
            .map(|d| {
                crate::pyval::arr_items(get(&d, "properties").and_then(|p| get(p, "schema")).and_then(|s| get(s, "enum")))
                    .iter()
                    .map(|v| plain_str_opt(Some(v)))
                    .collect()
            })
            .unwrap_or_default();
        out.push(("machine_contract schema".to_string(), enum_vals.join(",")));
    }

    let prot = crate::glob::expand(root, "community/*/protocol.yaml");
    if let Some(first) = prot.first() {
        let text = std::fs::read_to_string(root.join(first)).unwrap_or_default();
        static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
        let re = RE.get_or_init(|| {
            regex::Regex::new(r#"schema_version\s*:\s*"?([\w.]+)"?"#).expect("版本正则固定合法")
        });
        out.push((
            "protocol.yaml schema".to_string(),
            re.captures(&text).map(|c| c[1].to_string()).unwrap_or_default(),
        ));
    }

    let schemas = crate::glob::expand(root, "protocol/schema/*.json");
    out.push(("IDL schema 集".to_string(), format!("{} 件", schemas.len())));

    let verify_path = root.join("verify.sh");
    let verify = if verify_path.is_file() {
        std::fs::read_to_string(&verify_path).unwrap_or_default()
    } else {
        String::new()
    };
    static VRE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let vre = VRE.get_or_init(|| regex::Regex::new(r"# 版本 : (v[\d.]+)").expect("版本行正则固定合法"));
    let vm = vre.captures(&verify).map(|c| c[1].to_string());
    let qb_text = std::fs::read_to_string(root.join("desktop/src/core/quality_baseline.py"))
        .unwrap_or_default();
    let checks = crate::stats::py_int_const(&qb_text, "EXPECTED_CHECKS").unwrap_or(0);
    let pass = crate::stats::py_int_const(&qb_text, "EXPECTED_PASS").unwrap_or(0);
    out.push((
        "基线".to_string(),
        format!("{} · check1-{} · PASS={}", vm.unwrap_or_else(|| "?".to_string()), checks, pass),
    ));

    out
}

pub struct DeclScan {
    pub issues: Vec<String>,
    pub versions: usize,
    pub scope: usize,
    pub excluded: usize,
}

/// 真源 `scan`。
pub fn scan(root: &Path) -> DeclScan {
    let mut issues: Vec<String> = Vec::new();
    let decl = parse(root);
    let live = live_versions(root);

    if decl.versions.is_empty() {
        issues.push(format!(
            "声明文件缺 `## 声明` 版本表（修复指引：见 {}）",
            DECL_REL
        ));
    }
    for (name, want) in &live {
        let got = decl
            .versions
            .iter()
            .find(|(n, _, _)| n == name)
            .map(|(_, v, _)| v.clone())
            .unwrap_or_default();
        if got != *want {
            issues.push(format!(
                "声明与真源不一致：{} 声明={} 真源={}（修复指引：改声明对齐真源）",
                name,
                if got.is_empty() { "(缺)" } else { got.as_str() },
                want
            ));
        }
    }
    for (name, _, _) in &decl.versions {
        if !live.iter().any(|(n, _)| n == name) {
            issues.push(format!(
                "声明了无法核验的规范项：{}（真源缺失；修复指引：补真源或删该行）",
                name
            ));
        }
    }
    if decl.scope.is_empty() {
        issues.push("声明文件缺 `## 范围` 白名单".to_string());
    }
    for rel in &decl.scope {
        if !root.join(rel).exists() {
            issues.push(format!("范围里的路径不存在：{}（修复指引：删掉或改正）", rel));
        }
    }
    if decl.excluded.is_empty() {
        issues.push("声明文件缺 `## 排除` 清单（显式排除是声明的核心价值）".to_string());
    }
    for (rel, reason) in &decl.excluded {
        if rel.is_empty() {
            continue;
        }
        let optional = reason.contains("允许不存在");
        if rel.chars().any(|c| c == '*' || c == '?' || c == '[') {
            if !optional && crate::glob::expand(root, rel).is_empty() {
                issues.push(format!("排除项 glob 无匹配：{}", rel));
            }
        } else if !optional && !root.join(rel).exists() {
            issues.push(format!("排除项路径不存在：{}（修复指引：删除该条或修正路径）", rel));
        }
    }
    let scope_set: Vec<String> = decl.scope.iter().map(|s| s.trim_end_matches('/').to_string()).collect();
    for (rel_raw, _) in &decl.excluded {
        let rel = rel_raw.trim_end_matches('/').to_string();
        for s in &scope_set {
            if rel == *s || rel.starts_with(&format!("{}/", s)) || s.starts_with(&format!("{}/", rel)) {
                issues.push(format!(
                    "scope 与排除重叠：{} ↔ {}（同一条不能既在范围又排除）",
                    s, rel
                ));
            }
        }
    }

    DeclScan {
        issues,
        versions: decl.versions.len(),
        scope: decl.scope.len(),
        excluded: decl.excluded.len(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn section_stops_at_next_heading() {
        let text = "## 声明\n| a | b | c |\n## 范围\n- `x/`\n## 排除\n| y | z |\n";
        assert_eq!(section(text, "声明").len(), 1);
        assert_eq!(section(text, "范围").len(), 1);
        assert_eq!(section(text, "排除").len(), 1);
        assert!(section(text, "不存在").is_empty());
    }

    #[test]
    fn header_and_separator_rows_are_skipped() {
        let decl_text = "## 声明\n| 规范 | 版本 | 真源 |\n|---|---|---|\n| `A` | `1` | `s` |\n";
        let tmp = crate::testutil::fixture("decl-parse");
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::write(tmp.join(DECL_REL), decl_text.as_bytes()).unwrap();
        let d = parse(&tmp);
        assert_eq!(d.versions.len(), 1);
        assert_eq!(d.versions[0].0, "A");
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn scope_and_exclusion_overlap_is_flagged() {
        let text = "## 声明\n| s | v | src |\n## 范围\n- `docs/a/`\n## 排除\n| docs/a/x.md | 理由 |\n";
        let tmp = crate::testutil::fixture("decl-overlap");
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::create_dir_all(tmp.join("docs/a")).unwrap();
        std::fs::write(tmp.join("docs/a/x.md"), "x").unwrap();
        std::fs::write(tmp.join(DECL_REL), text.as_bytes()).unwrap();
        let got = scan(&tmp);
        assert!(
            got.issues.iter().any(|i| i.contains("scope 与排除重叠")),
            "重叠必须判红：{:?}",
            got.issues
        );
        let _ = std::fs::remove_dir_all(&tmp);
    }    // >>> GENERATED by tools/gen_declaration_branches.py（勿手改；重跑生成器覆盖本段）

    /// ===== 分支级差分判据（期望值由 `tools/gen_declaration_branches.py` 从真源生成）=====
    ///
    /// 本夹具同时踩：五路版本真源**全部在场**（registry / contract.schema / protocol.yaml /
    /// schema 计数 / 基线常量）、声明与真源不一致、声明了无法核验的规范项、范围里路径不存在、
    /// 排除项 glob 无匹配、排除项「允许不存在」豁免、scope ∩ 排除重叠。
    const WANT_DECL_ISSUES: [&str; 9] = [
        "声明与真源不一致：machine_contract schema 声明=9 真源=1（修复指引：改声明对齐真源）",
        "声明与真源不一致：protocol.yaml schema 声明=(缺) 真源=2（修复指引：改声明对齐真源）",
        "声明与真源不一致：IDL schema 集 声明=(缺) 真源=2 件（修复指引：改声明对齐真源）",
        "声明与真源不一致：基线 声明=(缺) 真源=? · check1-40 · PASS=70（修复指引：改声明对齐真源）",
        "声明了无法核验的规范项：无法核验的规范（真源缺失；修复指引：补真源或删该行）",
        "范围里的路径不存在：no/such/dir/（修复指引：删掉或改正）",
        "排除项 glob 无匹配：zzz/**",
        "scope 与排除重叠：docs ↔ docs/a.md（同一条不能既在范围又排除）",
        "scope 与排除重叠：docs ↔ docs/b.md（同一条不能既在范围又排除）",
    ];

    /// 真仓库那份 `quality_baseline.py`（真源 `from core import quality_baseline` 读的就是它）。
    fn real_baseline_source() -> String {
        std::fs::read_to_string(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../desktop/src/core/quality_baseline.py"
        ))
        .expect("真仓库的 quality_baseline.py 须在场")
    }

    /// 从真仓库源码里取一个 `NAME = <整数>` 常量。
    fn baseline_const(name: &str) -> i64 {
        let src = real_baseline_source();
        for line in src.lines() {
            let line = line.trim();
            if let Some(rest) = line.strip_prefix(name) {
                let rest = rest.trim_start();
                if let Some(rest) = rest.strip_prefix('=') {
                    let digits: String =
                        rest.trim().chars().take_while(|c| c.is_ascii_digit()).collect();
                    if let Ok(n) = digits.parse() {
                        return n;
                    }
                }
            }
        }
        panic!("真仓库源码里找不到常量 {}", name);
    }

    /// 「基线」那一条把真源当时的两个常量拼进消息——期望串也得按**同一份**常量构造，
    /// 否则真源一改就假红（并发会话正在改它）。
    fn want_for(s: &str) -> String {
        if s.starts_with("声明与真源不一致：基线 ") {
            return format!(
                "声明与真源不一致：基线 声明=(缺) 真源=? · check1-{} · PASS={}（修复指引：改声明对齐真源）",
                baseline_const("EXPECTED_CHECKS"),
                baseline_const("EXPECTED_PASS")
            );
        }
        s.to_string()
    }

    fn build_declaration_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("declaration-branches");
        for rel in ["protocol/schema", "community/p1", "desktop/src/core", "docs"] {
            std::fs::create_dir_all(root.join(rel)).unwrap();
        }
        for (rel, body) in [
            ("community/p1/protocol.yaml", r#"protocol:
  schema_version: "2"
"#),
            ("desktop/src/core/quality_baseline.py", r#"# 由判据在测试时以真仓库那份覆盖
"#),
            ("desktop/src/core/registry.json", r#"{"registry_schema_version": 2}"#),
            ("docs/a.md", r#"# a
"#),
            ("protocol/CONFORMANCE.md", r#"# 一致性声明

## 声明

| 规范 | 版本 | 真源 |
|---|---|---|
| `registry schema` | `2` | `registry.json` |
| `machine_contract schema` | `9` | `contract.schema.json` |
| `无法核验的规范` | `1` | `x` |

## 范围

- `docs/`
- `no/such/dir/`

## 排除

| 路径 | 理由 |
|---|---|
| `docs/a.md` | 存量 |
| `docs/b.md` | 允许不存在 |
| `zzz/**` | 存量 |
"#),
            ("protocol/schema/contract.schema.json", r#"{"properties": {"schema": {"enum": ["1"]}}}"#),
            ("protocol/schema/other.schema.json", r#"{"$id": "other"}"#),
            ("verify.sh", r#"#!/bin/bash
# 版本 : (v9.9)
check1(){
  true
}
check2(){
  true
}
"#),
        ] {
            std::fs::write(root.join(rel), body).unwrap();
        }
        // ⚠️ `quality_baseline.py` 一路**必须用真仓库那份**：真源是
        // `from core import quality_baseline as qb`——读**安装态模块**、与 `root` 无关。
        // 本线是从 `root` 读的（更纯），故这里现拷一份，让两侧在该路上可比；
        // 期望串也按真仓库当时的常量构造（见 `want_for`），否则真源一改就假红。
        std::fs::write(
            root.join("desktop/src/core/quality_baseline.py"),
            real_baseline_source(),
        )
        .unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_declaration_fixture();
        let got = scan(&root);
        let want: Vec<String> = WANT_DECL_ISSUES.iter().map(|s| want_for(s)).collect();
        assert_eq!(got.issues, want, "逐条消息与次序都须与真源一致");
        assert_eq!(got.versions, 3, "声明版本条数");
        assert_eq!(got.scope, 2, "scope 条数");
        assert_eq!(got.excluded, 3, "排除条数");
    }
    // <<< GENERATED

}
