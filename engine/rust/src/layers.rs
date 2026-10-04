//! 抽象阶梯体检 —— **与 Python 真源 `desktop/src/core/layer_model.py` 逐字节对账**。
//!
//! 覆盖真源的 `load` + `scan`/`_scan_impl`/`_rule_issues`（L1–L10）与 `render_markdown`，
//! 以及 CLI 面 `nf layers --verify --json` 的输出字节。
//!
//! **只读**：`write_region`（刷新 `docs/layers.md` 生成区）**不实现**——真源仍在 Python 侧。
//!
//! **已知近似**：L6 需要 `ast` 判定「core 有没有反向 import 入口面」。本线用
//! [`crate::pysrc`] 做词法级提取（剥注释/字符串后按语句行取 import），**不宣称等价于 `ast`**；
//! 该近似只影响 L6 的 issue 文本与行号，且当前语料上 L6 零命中（详见 `pysrc` 模块文档）。

use crate::glob;
use crate::jsonread;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, plain_str, plain_str_opt, py_str, str_list};
use crate::pysrc;
use std::collections::{BTreeSet, HashMap, HashSet};
use std::path::Path;

pub const DECL_REL: &str = "protocol/LAYERS.json";
pub const SCHEMA: &str = "nf-layers/1";
pub const DOC_REL: &str = "docs/layers.md";
pub const VERIFY_REL: &str = "verify.sh";
pub const ASSERTIONS_REL: &str = "protocol/assertions.json";
pub const MARK_BEGIN: &str = "<!-- nf:layers:begin -->";
pub const MARK_END: &str = "<!-- nf:layers:end -->";

fn check_def_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"(?m)^check(\d+)\(\)\{").expect("check 定义正则固定合法"))
}

fn judge_check_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^check(\d+)$").expect("判据引用正则固定合法"))
}

/// 真源 `layer_model.load`：缺件/schema 不符 → 带修复指引的错误（不静默降级）。
pub fn load(root: &Path) -> Result<Json, String> {
    let path = root.join(DECL_REL);
    if !path.is_file() {
        return Err(format!(
            "缺阶梯真源 {}（修复指引：先落该件再跑 nf layers --verify）",
            DECL_REL
        ));
    }
    let text = std::fs::read_to_string(&path)
        .map_err(|e| format!("阶梯真源 {} 读取失败：{}", DECL_REL, e))?;
    let raw: serde_json::Value = serde_json::from_str(&text).map_err(|e| {
        // 真源把 json.JSONDecodeError 的文本拼进消息——**该措辞不做逐字节承诺**
        format!("阶梯真源 {} 不是合法 JSON：{}（修复指引：修 JSON 语法后重跑）", DECL_REL, e)
    })?;
    let doc = jsonread::convert(&raw).map_err(|e| {
        format!("阶梯真源 {} 含不支持的值：{}（修复指引：修 JSON 语法后重跑）", DECL_REL, e)
    })?;
    if py_str(get(&doc, "schema")) != SCHEMA {
        return Err(format!(
            "阶梯真源 schema 不匹配（期望 {}；修复指引：核对 schema 字段）",
            SCHEMA
        ));
    }
    Ok(doc)
}

/// 一次扫描内的 glob 展开上下文（**两层缓存**，与真源 `_expand_many` 同构）：
/// ① 每个子树只枚举一次文件清单；② 每个 pattern 的匹配结果复用。
///
/// **实测依据**（2026-10-03）：无缓存时本面反而比 Python 慢 1.5×（1280 ms vs 857 ms）——
/// `layers` 会对同一批 glob 反复展开（L1/L2/L3 各阶 + L6 + L9），`community/**/*` 那类大树
/// 被整棵重走多次。加缓存后同机复测见 README。
struct GlobCtx {
    root: std::path::PathBuf,
    patterns: HashMap<String, BTreeSet<String>>,
    cache: glob::Cache,
}

impl GlobCtx {
    fn new(root: &Path) -> Self {
        Self {
            root: root.to_path_buf(),
            patterns: HashMap::new(),
            cache: glob::Cache::new(),
        }
    }

    fn one(&mut self, pattern: &str) -> BTreeSet<String> {
        if let Some(hit) = self.patterns.get(pattern) {
            return hit.clone();
        }
        let got: BTreeSet<String> = self.cache.expand(&self.root, pattern).into_iter().collect();
        self.patterns.insert(pattern.to_string(), got.clone());
        got
    }

    fn many(&mut self, globs: Option<&Json>) -> BTreeSet<String> {
        let mut out = BTreeSet::new();
        for g in arr_items(globs) {
            out.extend(self.one(&plain_str(g)));
        }
        out
    }
}

/// 真源 `_exists`：`(Path(root)/str(rel)).exists()`（目录也算存在）。
fn exists(root: &Path, rel: Option<&Json>) -> bool {
    root.join(plain_str_opt(rel)).exists()
}

fn ids_of(items: &[&Json]) -> Vec<String> {
    items.iter().map(|t| plain_str_opt(get(t, "id"))).collect()
}

// ---------------------------------------------------------------- L1–L10

fn rule_issues(root: &Path, doc: &Json) -> Vec<String> {
    let mut issues: Vec<String> = Vec::new();
    let mut ctx = GlobCtx::new(root);
    let tiers = arr_items(get(doc, "tiers"));
    let tier_ids = ids_of(&tiers);

    // ---- L1 真源在位
    for tier in &tiers {
        let src = get(tier, "source");
        let globs = src.and_then(|s| get(s, "globs"));
        let face = ctx.many(globs);
        if arr_items(globs).is_empty() {
            issues.push(format!(
                "L1 阶 {} 未声明真源面（修复指引：在 source.globs 写明真源落点）",
                plain_str_opt(get(tier, "id"))
            ));
        } else if face.is_empty() {
            issues.push(format!(
                "L1 阶 {} 的真源面展开为空：{}（修复指引：核对 globs 与实况）",
                plain_str_opt(get(tier, "id")),
                plain_str_opt(globs)
            ));
        }
    }
    for lv in arr_items(get(doc, "asset_levels")) {
        if ctx.many(get(lv, "globs")).is_empty() {
            issues.push(format!(
                "L1 资产子级 {} 的真源面为空：{}（修复指引：核对 globs）",
                plain_str_opt(get(lv, "id")),
                plain_str_opt(get(lv, "globs"))
            ));
        }
        if !tier_ids.contains(&py_str(get(lv, "tier"))) {
            issues.push(format!(
                "L1 资产子级 {} 的 tier 不在阶名单：{}（修复指引：改成真实阶 id）",
                plain_str_opt(get(lv, "id")),
                plain_str_opt(get(lv, "tier"))
            ));
        }
    }
    for sf in arr_items(get(doc, "surfaces")) {
        for rel in arr_items(get(sf, "entries")) {
            if !exists(root, Some(rel)) {
                issues.push(format!(
                    "L1 入口面 {} 的入口件不存在：{}（修复指引：补件或改成真实路径）",
                    plain_str_opt(get(sf, "id")),
                    plain_str(rel)
                ));
            }
        }
    }
    for comp in arr_items(get(doc, "crosscut").and_then(|c| get(c, "components"))) {
        if !exists(root, get(comp, "artifact")) {
            issues.push(format!(
                "L1 纵切件 {} 不存在：{}（修复指引：补件或改成真实路径）",
                plain_str_opt(get(comp, "id")),
                plain_str_opt(get(comp, "artifact"))
            ));
        }
    }

    // ---- 派生物（L2/L3 已扣除）
    let derived = ctx.many(get(doc, "derived"));

    // ---- L2 归属互斥（派生物已扣除）
    let mut faces: HashMap<String, BTreeSet<String>> = HashMap::new();
    for tier in &tiers {
        let tid = plain_str_opt(get(tier, "id"));
        let face = ctx.many(get(tier, "source").and_then(|s| get(s, "globs")));
        let diff: BTreeSet<String> = face.difference(&derived).cloned().collect();
        faces.insert(tid, diff);
    }
    for i in 0..tier_ids.len() {
        for b in tier_ids.iter().skip(i + 1) {
            let a = &tier_ids[i];
            let empty = BTreeSet::new();
            let fa = faces.get(a).unwrap_or(&empty);
            let fb = faces.get(b).unwrap_or(&empty);
            let overlap: Vec<&String> = fa.intersection(fb).collect();
            if !overlap.is_empty() {
                let head: Vec<String> = overlap.iter().take(3).map(|s| (*s).clone()).collect();
                issues.push(format!(
                    "L2 阶 {} 与阶 {} 真源面重叠：{}（修复指引：把件归给唯一一阶，或把派生物登记进 derived）",
                    a,
                    b,
                    head.join("、")
                ));
            }
        }
    }

    // ---- L3 接口面 ⊆ 真源面
    for tier in &tiers {
        let tid = plain_str_opt(get(tier, "id"));
        let iface = ctx.many(get(tier, "interface").and_then(|s| get(s, "globs")));
        if iface.is_empty() {
            issues.push(format!(
                "L3 阶 {} 未声明接口面（修复指引：在 interface.globs 写明跨阶可依赖面）",
                tid
            ));
        }
        let empty = BTreeSet::new();
        let base = faces.get(&tid).unwrap_or(&empty);
        let stray: Vec<String> = iface
            .difference(base)
            .filter(|r| !derived.contains(*r))
            .take(3)
            .cloned()
            .collect();
        if !stray.is_empty() {
            issues.push(format!(
                "L3 阶 {} 接口面超出真源面：{}（修复指引：接口必须是真源面的子集）",
                tid,
                stray.join("、")
            ));
        }
    }

    // ---- L4 依赖向下无环
    let mut order: HashMap<String, i64> = HashMap::new();
    for t in &tiers {
        let o = match get(t, "order") {
            Some(Json::Int(i)) => *i,
            _ => 99,
        };
        order.insert(plain_str_opt(get(t, "id")), o);
    }
    for tier in &tiers {
        let tid = plain_str_opt(get(tier, "id"));
        for dep in arr_items(get(tier, "depends_on")) {
            let dep = plain_str(dep);
            match order.get(&dep) {
                None => issues.push(format!(
                    "L4 阶 {} 依赖了不存在的阶：{}（修复指引：改成真实阶 id）",
                    tid, dep
                )),
                Some(od) => {
                    let own = *order.get(&tid).unwrap_or(&99);
                    if *od >= own {
                        issues.push(format!(
                            "L4 阶 {} 依赖方向不向下：{}（order {} ≥ 自身 {}；修复指引：依赖只能指向更下位的阶）",
                            tid, dep, od, own
                        ));
                    }
                }
            }
        }
    }
    let mut graph: HashMap<String, Vec<String>> = HashMap::new();
    for t in &tiers {
        graph.insert(
            plain_str_opt(get(t, "id")),
            arr_items(get(t, "depends_on")).iter().map(|d| plain_str(d)).collect(),
        );
    }
    let mut walker = CycleWalker {
        order: &order,
        graph: &graph,
        walked: HashSet::new(),
        reported: HashSet::new(),
        issues: &mut issues,
    };
    for tid in &tier_ids {
        walker.walk(tid, &[]);
    }

    // ---- L5 入口面只登记角色
    for sf in arr_items(get(doc, "surfaces")) {
        if !matches!(get(sf, "is_source_of_truth"), Some(Json::Bool(false))) {
            issues.push(format!(
                "L5 入口面 {} 的 is_source_of_truth 必须为 false（修复指引：入口是角色，真源只能是四阶）",
                plain_str_opt(get(sf, "id"))
            ));
        }
        for served in arr_items(get(sf, "serves")) {
            if !tier_ids.contains(&plain_str(served)) {
                issues.push(format!(
                    "L5 入口面 {} 的 serves 指向不存在的阶：{}（修复指引：改成真实阶 id）",
                    plain_str_opt(get(sf, "id")),
                    plain_str(served)
                ));
            }
        }
    }

    // ---- L6 引擎不反向 import 入口面
    for rel in ctx.one("desktop/src/core/*.py")
    {
        let Ok(src) = std::fs::read_to_string(root.join(&rel)) else {
            continue;
        };
        for (lineno, name) in pysrc::entry_imports(&src) {
            issues.push(format!(
                "L6 引擎阶反向 import 入口面件：{}:{} import {}（修复指引：入口可替换，core 不得依赖它——改由 CLI 层注入）",
                rel, lineno, name
            ));
        }
    }

    // ---- L7 退役阶不被依赖
    let retired: HashSet<String> = tiers
        .iter()
        .filter(|t| plain_str_opt(get(t, "status")) == "retired")
        .map(|t| plain_str_opt(get(t, "id")))
        .collect();
    let status_vocab = str_list(get(doc, "vocabulary").and_then(|v| get(v, "status")));
    for tier in &tiers {
        let status = plain_str_opt(get(tier, "status"));
        if status == "retired" {
            continue;
        }
        for dep in arr_items(get(tier, "depends_on")) {
            if retired.contains(&plain_str(dep)) {
                issues.push(format!(
                    "L7 在役阶 {} 依赖了退役阶 {}（修复指引：把该能力改依赖重分派后的阶）",
                    plain_str_opt(get(tier, "id")),
                    plain_str(dep)
                ));
            }
        }
        if !status_vocab.contains(&status) {
            issues.push(format!("L7 阶 {} 的 status 越词表：{}", plain_str_opt(get(tier, "id")), status));
        }
    }

    // ---- L8 judged_by 可解析
    let checks: HashSet<String> = if root.join(VERIFY_REL).exists() {
        std::fs::read_to_string(root.join(VERIFY_REL))
            .map(|t| {
                check_def_re()
                    .captures_iter(&t)
                    .map(|c| c[1].to_string())
                    .collect()
            })
            .unwrap_or_default()
    } else {
        HashSet::new()
    };
    let assertion_ids: HashSet<String> = if root.join(ASSERTIONS_REL).is_file() {
        jsonread::read_file(root, ASSERTIONS_REL)
            .map(|d| {
                arr_items(get(&d, "assertions"))
                    .iter()
                    .map(|a| plain_str_opt(get(a, "id")))
                    .collect()
            })
            .unwrap_or_default()
    } else {
        HashSet::new()
    };
    let mut refs: Vec<(String, String)> = Vec::new();
    for tier in &tiers {
        for r in arr_items(get(tier, "judged_by")) {
            refs.push((plain_str_opt(get(tier, "id")), plain_str(r)));
        }
    }
    for lv in arr_items(get(doc, "asset_levels")) {
        for r in arr_items(get(lv, "judged_by")) {
            refs.push((plain_str_opt(get(lv, "id")), plain_str(r)));
        }
    }
    for comp in arr_items(get(doc, "crosscut").and_then(|c| get(c, "components"))) {
        for r in arr_items(get(comp, "judged_by")) {
            refs.push((plain_str_opt(get(comp, "id")), plain_str(r)));
        }
    }
    for (owner, reference) in refs {
        if let Some(c) = judge_check_re().captures(&reference) {
            if !checks.contains(&c[1]) {
                issues.push(format!(
                    "L8 {} 的判据 {} 在 {} 中不存在（修复指引：改指向真实 check）",
                    owner, reference, VERIFY_REL
                ));
            }
        } else if let Some(rest) = reference.strip_prefix("assertion:") {
            if !assertion_ids.contains(rest) {
                issues.push(format!(
                    "L8 {} 的判据 {} 未登记（修复指引：在 {} 补该断言）",
                    owner, reference, ASSERTIONS_REL
                ));
            }
        } else {
            issues.push(format!(
                "L8 {} 的判据形式不合法：{}（修复指引：写成 checkN 或 assertion:<id>）",
                owner, reference
            ));
        }
    }

    // ---- L9 豁免诚实
    for pattern in arr_items(get(doc, "derived")) {
        if ctx.one(&plain_str(pattern)).is_empty() {
            issues.push(format!(
                "L9 derived 条目命中零文件：{}（修复指引：删掉该豁免或修正 glob）",
                plain_str(pattern)
            ));
        }
    }

    // ---- L10 生成区 == 实时渲染
    if !root.join(DOC_REL).exists() {
        issues.push(format!("L10 缺阶梯文档 {}（修复指引：补件并跑 nf layers --write）", DOC_REL));
    } else {
        let body = std::fs::read_to_string(root.join(DOC_REL)).unwrap_or_default();
        let got = region_of(&body);
        let want = render_markdown(doc);
        match got {
            None => issues.push(format!(
                "L10 {} 缺生成区标记 {} / {}（修复指引：补标记后跑 nf layers --write）",
                DOC_REL, MARK_BEGIN, MARK_END
            )),
            Some(g) if g.trim() != want.trim() => issues.push(format!(
                "L10 {} 生成区与实时渲染不一致（修复指引：跑 nf layers --write 刷新）",
                DOC_REL
            )),
            Some(_) => {}
        }
    }

    issues
}

/// 真源 `_walk` 的等价物（含 `walked` / `reported_cycles` 两个集合与后序标脏）。
struct CycleWalker<'a> {
    order: &'a HashMap<String, i64>,
    graph: &'a HashMap<String, Vec<String>>,
    walked: HashSet<String>,
    reported: HashSet<String>,
    issues: &'a mut Vec<String>,
}

impl CycleWalker<'_> {
    fn walk(&mut self, tid: &str, stack: &[String]) {
        if stack.iter().any(|s| s == tid) {
            let mut path: Vec<String> = stack.to_vec();
            path.push(tid.to_string());
            let joined = path.join(" → ");
            if !self.reported.contains(&joined) {
                self.reported.insert(joined.clone());
                self.issues
                    .push(format!("L4 依赖图存在环：{}（修复指引：断开上行依赖）", joined));
            }
            return;
        }
        if self.walked.contains(tid) {
            return;
        }
        let deps = self.graph.get(tid).cloned().unwrap_or_default();
        for dep in deps {
            if self.order.contains_key(&dep) {
                let mut next: Vec<String> = stack.to_vec();
                next.push(tid.to_string());
                self.walk(&dep, &next);
            }
        }
        self.walked.insert(tid.to_string());
    }
}

/// 真源 `_region_of`：取生成区正文；缺标记 → `None`。
fn region_of(text: &str) -> Option<String> {
    if !text.contains(MARK_BEGIN) || !text.contains(MARK_END) {
        return None;
    }
    let after = text.splitn(2, MARK_BEGIN).nth(1)?;
    Some(after.splitn(2, MARK_END).next()?.to_string())
}

// ---------------------------------------------------------------- 渲染器

/// 真源 `_table`。
fn table(rows: &[Vec<String>], header: &[&str]) -> Vec<String> {
    let mut out = vec![
        format!("| {} |", header.join(" | ")),
        format!("|{}|", vec!["---"; header.len()].join("|")),
    ];
    for r in rows {
        out.push(format!("| {} |", r.join(" | ")));
    }
    out
}

fn backtick_join(items: &[&Json]) -> String {
    items
        .iter()
        .map(|g| format!("`{}`", plain_str(g)))
        .collect::<Vec<_>>()
        .join("、")
}

/// 真源 `render_markdown`：把阶梯真源渲染成 markdown 生成区（确定性）。
pub fn render_markdown(doc: &Json) -> String {
    let mut lines: Vec<String> = Vec::new();
    lines.push("### 抽象轴：四阶".into());
    lines.push(String::new());
    let mut rows: Vec<Vec<String>> = Vec::new();
    for t in arr_items(get(doc, "tiers")) {
        rows.push(vec![
            format!("**{}**", plain_str_opt(get(t, "name"))),
            backtick_join(&arr_items(get(t, "source").and_then(|s| get(s, "globs")))),
            backtick_join(&arr_items(get(t, "interface").and_then(|s| get(s, "globs")))),
            arr_items(get(t, "judged_by"))
                .iter()
                .map(|v| plain_str(v))
                .collect::<Vec<_>>()
                .join("、"),
            format!(
                "{}（{}）",
                plain_str_opt(get(t, "status")),
                plain_str_opt(get(t, "change_tier"))
            ),
        ]);
    }
    lines.extend(table(&rows, &["阶", "真源面", "接口面（跨阶唯一可依赖）", "既有判据", "状态 / 变更档"]));
    lines.push(String::new());
    lines.push("### 资产阶五子级（同一格内异质，分开看代价）".into());
    lines.push(String::new());
    let mut rows2: Vec<Vec<String>> = Vec::new();
    for lv in arr_items(get(doc, "asset_levels")) {
        rows2.push(vec![
            format!("**{}**", plain_str_opt(get(lv, "name"))),
            backtick_join(&arr_items(get(lv, "globs"))),
            arr_items(get(lv, "judged_by"))
                .iter()
                .map(|v| plain_str(v))
                .collect::<Vec<_>>()
                .join("、"),
            py_str(get(lv, "note")),
        ]);
    }
    lines.extend(table(&rows2, &["子级", "真源面", "既有判据", "口径"]));
    lines.push(String::new());
    lines.push("### 入口面（只登记角色，永不作为真源）".into());
    lines.push(String::new());
    let mut rows3: Vec<Vec<String>> = Vec::new();
    for sf in arr_items(get(doc, "surfaces")) {
        rows3.push(vec![
            format!("**{}**", plain_str_opt(get(sf, "name"))),
            backtick_join(&arr_items(get(sf, "entries"))),
            arr_items(get(sf, "serves"))
                .iter()
                .map(|v| plain_str(v))
                .collect::<Vec<_>>()
                .join("、"),
            py_str(get(sf, "note")),
        ]);
    }
    lines.extend(table(&rows3, &["面", "入口件", "服务阶", "口径"]));
    lines.push(String::new());
    lines.push("### 验证纵切（贯穿四阶，不是层）".into());
    lines.push(String::new());
    let mut rows4: Vec<Vec<String>> = Vec::new();
    for comp in arr_items(get(doc, "crosscut").and_then(|c| get(c, "components"))) {
        rows4.push(vec![
            format!("**{}**", plain_str_opt(get(comp, "id"))),
            format!("`{}`", plain_str_opt(get(comp, "artifact"))),
            arr_items(get(comp, "judged_by"))
                .iter()
                .map(|v| plain_str(v))
                .collect::<Vec<_>>()
                .join("、"),
        ]);
    }
    lines.extend(table(&rows4, &["件", "落点", "既有判据"]));
    lines.push(String::new());
    lines.push("> 本区由 `nf layers --write` 渲染，禁止手改；真源 = `protocol/LAYERS.json`。".into());
    lines.join("\n")
}

// ---------------------------------------------------------------- CLI 面

/// 真源 `scan`/`_scan_impl` → `(issues, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, Json) {
    let doc = match load(root) {
        Ok(d) => d,
        Err(e) => {
            return (
                vec![e],
                Json::Object(vec![
                    ("tiers".into(), Json::Int(0)),
                    ("asset_levels".into(), Json::Int(0)),
                    ("surfaces".into(), Json::Int(0)),
                ]),
            )
        }
    };
    let issues = rule_issues(root, &doc);
    let stats = Json::Object(vec![
        ("tiers".into(), Json::Int(arr_items(get(&doc, "tiers")).len() as i64)),
        (
            "asset_levels".into(),
            Json::Int(arr_items(get(&doc, "asset_levels")).len() as i64),
        ),
        (
            "surfaces".into(),
            Json::Int(arr_items(get(&doc, "surfaces")).len() as i64),
        ),
        (
            "crosscut".into(),
            Json::Int(arr_items(get(&doc, "crosscut").and_then(|c| get(c, "components"))).len() as i64),
        ),
        ("rules".into(), Json::Int(arr_items(get(&doc, "rules")).len() as i64)),
        ("derived".into(), Json::Int(arr_items(get(&doc, "derived")).len() as i64)),
    ]);
    (issues, stats)
}

/// `nf layers --verify --json` 的输出字节（`print` 的换行也含在内）。
pub fn verify_bytes(root: &Path) -> Vec<u8> {
    let (issues, stats) = scan(root);
    let doc = Json::Object(vec![
        ("kind".into(), Json::Str("layers-verify".into())),
        ("ok".into(), Json::Bool(issues.is_empty())),
        (
            "issues".into(),
            Json::Array(issues.iter().map(|s| Json::Str(s.clone())).collect()),
        ),
        ("stats".into(), stats),
    ]);
    doc.dumps_file().into_bytes()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn region_of_extracts_between_markers() {
        let t = format!("head\n{}\nBODY\n{}\ntail", MARK_BEGIN, MARK_END);
        assert_eq!(region_of(&t).unwrap().trim(), "BODY");
        assert!(region_of("no markers").is_none());
        assert!(region_of(MARK_BEGIN).is_none());
    }

    #[test]
    fn table_matches_truth_source_shape() {
        let rows = vec![vec!["a".to_string(), "b".to_string()]];
        let got = table(&rows, &["x", "y"]);
        assert_eq!(got[0], "| x | y |");
        assert_eq!(got[1], "|---|---|");
        assert_eq!(got[2], "| a | b |");
    }

    #[test]
    fn missing_declaration_reports_and_zeroes_stats() {
        let tmp = crate::testutil::fixture("layers-missing");
        let (issues, stats) = scan(&tmp);
        assert_eq!(issues.len(), 1);
        assert!(issues[0].contains("缺阶梯真源"), "got: {}", issues[0]);
        // 真源此处 stats 只有三个键
        let Json::Object(p) = &stats else { panic!() };
        assert_eq!(p.len(), 3);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn entry_import_detection_ignores_prose_and_strings() {
        // 真源本体就长这样：文档字符串里写「不许 import nf」，AST 不判、裸行扫描会假红
        let src = "\"\"\"core 不许出现 import nf / from scripts …\"\"\"\n# from scripts import x\nimport os\n";
        assert!(pysrc::entry_imports(src).is_empty(), "散文/注释不得被当成 import");
        let real = "import os\nimport nf\n";
        assert_eq!(pysrc::entry_imports(real), vec![(2usize, "nf".to_string())]);
        let rel = "from scripts.nf import y\n";
        assert_eq!(pysrc::entry_imports(rel), vec![(1usize, "scripts".to_string())]);
    }

    #[test]
    fn raw_prefix_and_triple_quotes_are_stripped() {
        let src = "x = r\"import nf\"\ny = '''\nimport scripts\n'''\nz = 1\n";
        let stripped = pysrc::strip_comments_and_strings(src);
        assert!(!stripped.contains("import nf"));
        assert!(!stripped.contains("import scripts"));
        assert!(stripped.contains("z = 1"));
        // 行结构（含换行）必须保留，否则 L6 行号会漂
        assert_eq!(stripped.lines().count(), src.lines().count());
    }
}
