//! `nf stats` 只读面 —— **与 Python 真源 `desktop/src/core/repo_stats.py` 逐字节对账**。
//!
//! 覆盖真源的 `compute` + `check`（两者皆只读）：口径表见 `repo_stats.py` 模块头。
//! 输出字节与 `nf stats --json` 同形（`json.dumps(ensure_ascii=False, indent=2, sort_keys=True)` + `\n`）；
//! **退出码同真源**：`check` 有 issue ⇔ 退出码 1。
//!
//! 写面（`write`：重写 README/README.en/llms.txt 生成区 + `protocol/repo_stats.json`）**不实现**
//! ——真源仍是 Python 侧，本线只读。

use crate::jsonread;
use crate::pyjson::Json;
use std::path::Path;

pub const STATS_REL: &str = "protocol/repo_stats.json";
pub const BEGIN: &str = "<!-- nf:stats:begin -->";
pub const END: &str = "<!-- nf:stats:end -->";
/// 生成区所在入口件（真源 `BLOCK_FILES` 口径：README 中英 + llms.txt）。
pub const BLOCK_FILES: [&str; 3] = ["README.md", "README.en.md", "llms.txt"];

/// 自述数字集合（真源 `stats` 字典的等价物）。
#[derive(Default, Clone, Debug)]
pub struct Stats {
    pub core_modules: i64,
    pub registered_packs: i64,
    pub core_pipelines: Vec<String>,
    pub pack_dirs: i64,
    pub pack_assets: i64,
    pub concept_graphs: i64,
    pub standards_total: i64,
    pub standards_reachable: i64,
    pub standards_unreachable: i64,
    pub standards_bodies: i64,
    pub standards_edges: i64,
    pub standards_by_layer: Vec<(String, i64)>,
    pub standard_bindings: i64,
    pub domain_packs: i64,
    pub subdivisions_total: i64,
    pub library_items: i64,
    pub verify_checks: i64,
    pub verify_version: String,
    pub baseline_checks: i64,
    pub baseline_pass: i64,
}

impl Stats {
    /// 与真源 `stats` 字典同字段、同值（键序在 `pyjson` 发射时统一排序）。
    pub fn to_json(&self) -> Json {
        Json::Object(vec![
            ("schema".into(), Json::Str("nf-repo-stats/1".into())),
            ("core_modules".into(), Json::Int(self.core_modules)),
            ("registered_packs".into(), Json::Int(self.registered_packs)),
            (
                "core_pipelines".into(),
                Json::Array(self.core_pipelines.iter().map(|s| Json::Str(s.clone())).collect()),
            ),
            ("pack_dirs".into(), Json::Int(self.pack_dirs)),
            ("pack_assets".into(), Json::Int(self.pack_assets)),
            ("concept_graphs".into(), Json::Int(self.concept_graphs)),
            ("standards_total".into(), Json::Int(self.standards_total)),
            ("standards_reachable".into(), Json::Int(self.standards_reachable)),
            ("standards_unreachable".into(), Json::Int(self.standards_unreachable)),
            ("standards_bodies".into(), Json::Int(self.standards_bodies)),
            ("standards_edges".into(), Json::Int(self.standards_edges)),
            (
                "standards_by_layer".into(),
                Json::Object(
                    self.standards_by_layer
                        .iter()
                        .map(|(k, v)| (k.clone(), Json::Int(*v)))
                        .collect(),
                ),
            ),
            ("standard_bindings".into(), Json::Int(self.standard_bindings)),
            ("domain_packs".into(), Json::Int(self.domain_packs)),
            ("subdivisions_total".into(), Json::Int(self.subdivisions_total)),
            ("library_items".into(), Json::Int(self.library_items)),
            ("verify_checks".into(), Json::Int(self.verify_checks)),
            ("verify_version".into(), Json::Str(self.verify_version.clone())),
            ("baseline_checks".into(), Json::Int(self.baseline_checks)),
            ("baseline_pass".into(), Json::Int(self.baseline_pass)),
        ])
    }
}

// ---------------------------------------------------------------- JSON 取值助手

fn obj_get<'a>(j: &'a Json, k: &str) -> Option<&'a Json> {
    match j {
        Json::Object(pairs) => pairs.iter().find(|(n, _)| n == k).map(|(_, v)| v),
        _ => None,
    }
}

fn int_of(j: Option<&Json>) -> i64 {
    match j {
        Some(Json::Int(i)) => *i,
        _ => 0,
    }
}

fn len_of(j: Option<&Json>) -> i64 {
    match j {
        Some(Json::Array(a)) => a.len() as i64,
        _ => 0,
    }
}

fn layer_of(j: Option<&Json>) -> Vec<(String, i64)> {
    match j {
        Some(Json::Object(pairs)) => pairs
            .iter()
            .map(|(k, v)| (k.clone(), match v { Json::Int(i) => *i, _ => 0 }))
            .collect(),
        _ => Vec::new(),
    }
}

// ---------------------------------------------------------------- 目录扫描（glob 等价物）

fn names_in(dir: &Path) -> Vec<String> {
    let mut out = Vec::new();
    if let Ok(rd) = std::fs::read_dir(dir) {
        for e in rd.flatten() {
            out.push(e.file_name().to_string_lossy().into_owned());
        }
    }
    out
}

fn subdirs_in(dir: &Path) -> Vec<String> {
    let mut out = Vec::new();
    if let Ok(rd) = std::fs::read_dir(dir) {
        for e in rd.flatten() {
            if e.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                out.push(e.file_name().to_string_lossy().into_owned());
            }
        }
    }
    out
}

/// `glob("dir/*.md")` 的计数等价物（Python glob 不筛类型，故按名匹配即可）。
fn count_suffix(dir: &Path, suffix: &str) -> i64 {
    names_in(dir).iter().filter(|n| n.ends_with(suffix)).count() as i64
}

/// `glob("parent/*/sub/name")` 的计数等价物（`sub` 为空表示直接在 `parent/*/` 下找）。
fn count_in_subdirs(parent: &Path, sub: &str, name: &str) -> i64 {
    subdirs_in(parent)
        .iter()
        .filter(|p| {
            let mut d = parent.join(p.as_str());
            if !sub.is_empty() {
                d = d.join(sub);
            }
            d.join(name).exists()
        })
        .count() as i64
}

/// `glob("parent/*/sub/*suffix")` 的计数等价物。
fn count_suffix_in_subdirs(parent: &Path, sub: &str, suffix: &str) -> i64 {
    subdirs_in(parent)
        .iter()
        .map(|p| count_suffix(&parent.join(p.as_str()).join(sub), suffix))
        .sum()
}

// ---------------------------------------------------------------- verify.sh / quality_baseline

/// `^check[0-9]+\(\)` 定义数（真源 `re.findall(..., re.M)`）。
fn count_checks(text: &str) -> i64 {
    let mut n = 0i64;
    for line in text.lines() {
        if let Some(rest) = line.strip_prefix("check") {
            let digits: String = rest.chars().take_while(|c| c.is_ascii_digit()).collect();
            if !digits.is_empty() && rest[digits.len()..].starts_with("()") {
                n += 1;
            }
        }
    }
    n
}

/// `^# 版本\s*:\s*v([0-9][0-9.]*)` 的首个捕获组（无匹配 → 空串，与真源同语义）。
fn parse_version(text: &str) -> String {
    for line in text.lines() {
        let Some(rest) = line.strip_prefix("# 版本") else { continue };
        let mut it = rest.chars().peekable();
        while it.peek().map(|c| c.is_whitespace()).unwrap_or(false) {
            it.next();
        }
        if it.next() != Some(':') {
            continue;
        }
        while it.peek().map(|c| c.is_whitespace()).unwrap_or(false) {
            it.next();
        }
        if it.next() != Some('v') {
            continue;
        }
        let mut v = String::new();
        while let Some(&c) = it.peek() {
            if c.is_ascii_digit() {
                v.push(c);
                it.next();
            } else if c == '.' && !v.is_empty() {
                v.push(c);
                it.next();
            } else {
                break;
            }
        }
        if !v.is_empty() {
            return v;
        }
    }
    String::new()
}

/// 读 Python 模块级整数常量（真源 `getattr(qb, "EXPECTED_*", …)`）。
///
/// **已知耦合**：本线以源码文本取这两个常量——`quality_baseline` 是 Python 模块，
/// 非 Python 实现没有别的稳定入口。若该文件改成运行时计算，本处须同步改判。
pub(crate) fn py_int_const(text: &str, name: &str) -> Option<i64> {
    for line in text.lines() {
        let t = line.trim_start();
        let Some(rest) = t.strip_prefix(name) else { continue };
        // 防前缀误伤（EXPECTED_CHECKS_SOMETHING）
        if rest.chars().next().map(|c| c == '_' || c.is_alphanumeric()).unwrap_or(false) {
            continue;
        }
        let rest = rest.trim_start();
        let Some(rest) = rest.strip_prefix('=') else { continue };
        let digits: String = rest.trim_start().chars().take_while(|c| c.is_ascii_digit()).collect();
        if !digits.is_empty() {
            return digits.parse().ok();
        }
    }
    None
}

// ---------------------------------------------------------------- compute / check

/// 真源 `compute`：实算全部自述数字 + 收集 issue（issue 顺序与真源逐条对齐）。
pub fn compute(root: &Path) -> (Stats, Vec<String>) {
    let mut issues: Vec<String> = Vec::new();
    let mut s = Stats::default();

    let reg = jsonread::read_file(root, "desktop/src/core/registry.json");
    match &reg {
        Some(v) if matches!(v, Json::Object(_)) => {}
        _ => {
            issues.push("取不到 registry.json（官方核心模块/登记包口径缺失）".into());
        }
    }
    let reg = match reg {
        Some(v) if matches!(v, Json::Object(_)) => v,
        _ => Json::Object(Vec::new()),
    };
    s.core_modules = len_of(obj_get(&reg, "modules"));
    s.registered_packs = len_of(obj_get(&reg, "protocols"));

    // 03_管线库/P*.md → 文件名前 3 字符，排序
    let mut pipes: Vec<String> = names_in(&root.join("03_管线库"))
        .into_iter()
        .filter(|n| n.starts_with('P') && n.ends_with(".md"))
        .map(|n| n.chars().take(3).collect::<String>())
        .collect();
    pipes.sort();
    s.core_pipelines = pipes;

    s.pack_dirs = count_in_subdirs(&root.join("community"), "", "protocol.yaml");
    if s.pack_dirs > 0 && s.pack_dirs != s.registered_packs {
        issues.push(format!(
            "盘上包目录 {} ≠ registry 登记 {}（登记三要件与盘上实况不一致）",
            s.pack_dirs, s.registered_packs
        ));
    }

    s.pack_assets = count_suffix_in_subdirs(&root.join("community"), "assets", ".md");
    s.concept_graphs = count_in_subdirs(&root.join("community"), "assets", "CONCEPT_GRAPH.md");

    let cat = jsonread::read_file(root, "protocol/standards_catalog.json").unwrap_or(Json::Object(Vec::new()));
    let cov = obj_get(&cat, "coverage").cloned().unwrap_or(Json::Object(Vec::new()));
    for key in ["standards", "reachable", "unreachable", "bodies", "depends_edges", "by_layer"] {
        if obj_get(&cov, key).is_none() {
            issues.push(format!("标准目录 coverage 缺 {}（口径不完整）", key));
        }
    }
    s.standards_total = int_of(obj_get(&cov, "standards"));
    s.standards_reachable = int_of(obj_get(&cov, "reachable"));
    s.standards_unreachable = int_of(obj_get(&cov, "unreachable"));
    s.standards_bodies = int_of(obj_get(&cov, "bodies"));
    s.standards_edges = int_of(obj_get(&cov, "depends_edges"));
    s.standards_by_layer = layer_of(obj_get(&cov, "by_layer"));

    let bind = jsonread::read_file(root, "protocol/standards_binding.json").unwrap_or(Json::Object(Vec::new()));
    s.standard_bindings = int_of(obj_get(&bind, "bindings_total"));

    let manifest = jsonread::read_file(root, "protocol/domain_packs.json").unwrap_or(Json::Object(Vec::new()));
    s.domain_packs = int_of(obj_get(&manifest, "count"));
    s.subdivisions_total = int_of(obj_get(&manifest, "subdivisions_total"));

    let lib = names_in(&root.join("library"));
    s.library_items = lib
        .iter()
        .filter(|f| f.ends_with(".md") && *f != "INDEX.md" && *f != "ALIAS.md")
        .count() as i64;

    let vtext = match std::fs::read_to_string(root.join("verify.sh")) {
        Ok(t) => t,
        Err(_) => {
            issues.push("取不到 verify.sh（质量凭证口径缺失）".into());
            String::new()
        }
    };
    s.verify_checks = count_checks(&vtext);
    s.verify_version = parse_version(&vtext);
    if s.verify_version.is_empty() {
        issues.push("verify.sh 头部缺「# 版本 : vX」版本行".into());
    }
    if s.verify_checks < 1 {
        issues.push("verify.sh 未扫到任何 checkN() 定义".into());
    }

    match std::fs::read_to_string(root.join("desktop/src/core/quality_baseline.py")) {
        Ok(qb) => {
            s.baseline_checks = py_int_const(&qb, "EXPECTED_CHECKS").unwrap_or(s.verify_checks);
            s.baseline_pass = py_int_const(&qb, "EXPECTED_PASS").unwrap_or(0);
        }
        Err(e) => {
            s.baseline_checks = s.verify_checks;
            s.baseline_pass = 0;
            issues.push(format!("取不到 quality_baseline.EXPECTED_*：{}（基线句无法生成）", e));
        }
    }
    if s.baseline_checks != s.verify_checks {
        issues.push(format!(
            "基线 check 数 {} ≠ verify.sh 实扫 {}（同步 quality_baseline.EXPECTED_CHECKS）",
            s.baseline_checks, s.verify_checks
        ));
    }

    (s, issues)
}

/// 真源 `check`：compute + 生成区比对 + 在盘记录比对（**全只读**）。
pub fn check(root: &Path) -> (Vec<String>, Stats) {
    let (stats, mut issues) = compute(root);
    let blocks = render(&stats);
    for (rel, block) in blocks.iter() {
        let path = root.join(rel);
        let Ok(text) = std::fs::read_to_string(&path) else {
            issues.push(format!("缺入口文件 {}", rel));
            continue;
        };
        match replace_block(&text, block) {
            None => issues.push(format!("{} 缺 marker 区", rel)),
            Some(new) if new != text => {
                issues.push(format!("{} 的生成区与实算不一致（跑 `nf stats --write` 重写）", rel))
            }
            Some(_) => {}
        }
    }
    let recorded = jsonread::read_file(root, STATS_REL);
    let live = stats.to_json();
    match recorded {
        Some(r) if jsonread::json_eq(&r, &live) => {}
        _ => issues.push(format!(
            "{} 与实算不一致（跑 `nf stats --write` 重写）",
            STATS_REL
        )),
    }
    (issues, stats)
}

/// 真源 `_replace_block`：marker 包围区整体替换；缺 marker → `None`。
fn replace_block(text: &str, block: &str) -> Option<String> {
    let i = text.find(BEGIN)?;
    let j = text.find(END)?;
    if j < i {
        return None;
    }
    let mut out = String::with_capacity(text.len() + block.len());
    out.push_str(&text[..i]);
    out.push_str(block);
    out.push_str(&text[j + END.len()..]);
    Some(out)
}

// ---------------------------------------------------------------- 生成区渲染（三入口件）

/// 真源 `render`：入口件 → 生成区块（顺序 = README.md / README.en.md / llms.txt）。
pub fn render(stats: &Stats) -> Vec<(&'static str, String)> {
    vec![
        (BLOCK_FILES[0], zh(stats)),
        (BLOCK_FILES[1], en(stats)),
        (BLOCK_FILES[2], llms(stats)),
    ]
}

fn layer_txt(stats: &Stats) -> String {
    if stats.standards_by_layer.is_empty() {
        return "—".into();
    }
    let mut ls = stats.standards_by_layer.clone();
    ls.sort_by(|a, b| a.0.as_bytes().cmp(b.0.as_bytes()));
    ls.iter().map(|(k, v)| format!("{} {}", k, v)).collect::<Vec<_>>().join(" · ")
}

fn pipes_txt(stats: &Stats) -> String {
    if stats.core_pipelines.is_empty() {
        "—".into()
    } else {
        stats.core_pipelines.join(" / ")
    }
}

fn zh(s: &Stats) -> String {
    [
        BEGIN.to_string(),
        format!(
            "**官方核心**：{} 模块 · {} 管线（{}） · 核心协议件 01–07",
            s.core_modules,
            s.core_pipelines.len(),
            pipes_txt(s)
        ),
        format!(
            "**社区规模**：{} 登记包 · {} 资产档 · {} 概念图 · {} 域包/{} 细分 · 标准目录 {} 条（可达 {} / 不可达 {} · 机构 {} · {} 条依赖边） · 标准绑定 {} 条",
            s.registered_packs, s.pack_assets, s.concept_graphs,
            s.domain_packs, s.subdivisions_total,
            s.standards_total, s.standards_reachable, s.standards_unreachable,
            s.standards_bodies, s.standards_edges, s.standard_bindings
        ),
        format!(
            "**质量凭证**：verify v{} · check1-{} · PASS={}（`bash verify.sh` 单入口；期望基线取自 `quality_baseline.EXPECTED_*`） · 馆藏 {} 件",
            s.verify_version, s.baseline_checks, s.baseline_pass, s.library_items
        ),
        String::new(),
        format!("分层：{} （按标准目录 layer）", layer_txt(s)),
        String::new(),
        "> 本区由 `python scripts/nf.py stats --write` 生成，禁止手改；口径与实算真源见 `protocol/repo_stats.json`。".to_string(),
        END.to_string(),
    ]
    .join("\n")
}

fn en(s: &Stats) -> String {
    [
        BEGIN.to_string(),
        format!(
            "**Official core**: {} modules · {} pipelines ({}) · protocol files 01-07",
            s.core_modules,
            s.core_pipelines.len(),
            pipes_txt(s)
        ),
        format!(
            "**Community scale**: {} registered packs · {} asset files · {} concept graphs · {} domain packs / {} subdivisions · standards catalog {} (reachable {} / unreachable {} · {} bodies · {} dependency edges) · standard bindings {}",
            s.registered_packs, s.pack_assets, s.concept_graphs,
            s.domain_packs, s.subdivisions_total,
            s.standards_total, s.standards_reachable, s.standards_unreachable,
            s.standards_bodies, s.standards_edges, s.standard_bindings
        ),
        format!(
            "**Quality evidence**: verify v{} · check1-{} · PASS={} (`bash verify.sh`; expectations from `quality_baseline.EXPECTED_*`) · library {} items",
            s.verify_version, s.baseline_checks, s.baseline_pass, s.library_items
        ),
        String::new(),
        "> Generated by `python scripts/nf.py stats --write`. Do not edit by hand; sources in `protocol/repo_stats.json`.".to_string(),
        END.to_string(),
    ]
    .join("\n")
}

fn llms(s: &Stats) -> String {
    [
        BEGIN.to_string(),
        format!(
            "- 质量凭证（可静态实算）：verify v{} · check1-{} · PASS={}（`bash verify.sh` 单入口；期望基线取自 `quality_baseline.EXPECTED_*`，本行由生成器写入）。",
            s.verify_version, s.baseline_checks, s.baseline_pass
        ),
        format!(
            "- 规模（实算真源 `protocol/repo_stats.json`）：{} 登记包 · {} 资产档 · {} 概念图 · 标准目录 {} 条（可达 {}） · 标准绑定 {} 条 · 馆藏 {} 件。",
            s.registered_packs, s.pack_assets, s.concept_graphs,
            s.standards_total, s.standards_reachable, s.standard_bindings, s.library_items
        ),
        "- 标准目录 GEO 出口（可引用）：`docs/standards/index.md` · 机读 `protocol/geo_export.json`。".to_string(),
        END.to_string(),
    ]
    .join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn check_counter_matches_python_regex() {
        let t = "check1() {\n}\ncheck22() {\n}\n# check3()\ncheck()\ncheckX()\n";
        // 真源 `^check[0-9]+\(\)`：只数行首且紧跟数字与 ()
        assert_eq!(count_checks(t), 2);
    }

    #[test]
    fn version_parser_takes_first_match() {
        assert_eq!(parse_version("# 版本 : v2.30  配套 : x\n"), "2.30");
        assert_eq!(parse_version("no version here\n"), "");
        assert_eq!(parse_version("# 版本: v1.0\n# 版本 : v9.9\n"), "1.0");
    }

    #[test]
    fn py_int_const_reads_module_level_only() {
        let src = "EXPECTED_CHECKS = 40\nEXPECTED_PASS = 70\nOTHER = 1\n";
        assert_eq!(py_int_const(src, "EXPECTED_CHECKS"), Some(40));
        assert_eq!(py_int_const(src, "EXPECTED_PASS"), Some(70));
        assert_eq!(py_int_const(src, "EXPECTED_MISSING"), None);
    }

    #[test]
    fn py_int_const_not_fooled_by_longer_name() {
        assert_eq!(py_int_const("EXPECTED_CHECKS_EXTRA = 9\n", "EXPECTED_CHECKS"), None);
    }

    #[test]
    fn replace_block_swaps_inner_region() {
        let text = format!("head\n{}\nOLD\n{}\ntail\n", BEGIN, END);
        let got = replace_block(&text, &format!("{}\nNEW\n{}", BEGIN, END)).unwrap();
        assert_eq!(got, format!("head\n{}\nNEW\n{}\ntail\n", BEGIN, END));
        assert!(replace_block("no markers", "x").is_none());
    }

    #[test]
    fn render_has_three_blocks_in_source_order() {
        let r = render(&Stats::default());
        assert_eq!(r.len(), 3);
        assert_eq!(r[0].0, "README.md");
        assert_eq!(r[2].0, "llms.txt");
        assert!(r[0].1.starts_with(BEGIN));
    }
}
