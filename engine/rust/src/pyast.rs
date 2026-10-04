//! Python 解析桥（内置 `rustpython-parser`）—— 供 AST 类判据使用。
//!
//! ## 为什么需要它
//!
//! `purity_scan` / `code_metrics` / `asset_contract` 三条真源判据建立在 **Python 语法树**之上
//! （调用图、控制流、规模统计）。手写子集解析器复刻不了 CPython 的 AST 语义，故内置成熟 crate。
//! 实测（2026-10-04）：本机 `x86_64-pc-windows-gnu` 可构建可运行；依赖树**无** `windows-sys` /
//! `windows-link` / `iana-time` / `chrono` / `winapi` ⇒ 不触发 dlltool 陷阱。
//!
//! ## 一处必须小心的地方：**遍历顺序**
//!
//! CPython 的 `ast.walk` 是 **BFS**（`deque` + `extend(iter_child_nodes)`），而 `rustpython-ast`
//! 的 `Visitor` 是 **DFS**。真源把 `raises` / `modules` / `sinks` 的**列表顺序写进消息**，
//! 故顺序可观察、必须复刻。
//!
//! 本线的做法：用 `Visitor` 在**进入节点时**记录 `(深度, 前序序号)`，再按 `(深度, 前序序号)`
//! 排序——**对树而言，这与 BFS 序等价**（同层内按前序即左到右；各层按深度先后）。
//! 深度由「调用 `generic_visit_*` 前后自己压/弹」得到，故 `Visitor` 的 12 个顶层钩子都要覆盖，
//! 漏一个深度就会错。

use rustpython_ast as past;
use rustpython_ast::Ranged;
use rustpython_ast::Visitor as _;
use rustpython_parser::{parse, Mode};
use std::collections::BTreeSet;

/// R4：`raise` 里携带的消息（仅取字符串常量 / f-string 的常量段）。
pub struct RaiseFact {
    pub lineno: u32,
    pub msg: String,
}

/// R6：危险 sink 候选（行号 / 调用目标名 / 是否 `shell=True`）。
pub struct SinkFact {
    pub lineno: u32,
    pub call: String,
    pub shell_true: bool,
}

/// 真源 `_ast_facts` 的四元组。
pub struct PurityFacts {
    pub raises: Vec<RaiseFact>,
    pub guarded: BTreeSet<u32>,
    pub modules: Vec<(String, u32)>,
    pub sinks: Vec<SinkFact>,
}

/// 解析一份 Python 源码 → `Mod`（真源 `ast.parse` 的对应物）；语法坏 → `None`。
pub fn parse_module(text: &str) -> Option<rustpython_ast::Mod> {
    parse(text, Mode::Module, "<nf>").ok()
}

/// 行号表：源文本里每个 `\n` 之后的位置（用于把字节偏移换成 1-based 行号）。
///
/// **公开**：`asset_code`（代码面控制流分析）也要把 `n.lineno` 算出来。
pub struct LineStarts(pub Vec<u32>);

impl LineStarts {
    pub fn new(text: &str) -> Self {
        let mut v = vec![0u32];
        for (i, b) in text.bytes().enumerate() {
            if b == b'\n' {
                v.push(i as u32 + 1);
            }
        }
        LineStarts(v)
    }
    pub fn line_of(&self, offset: u32) -> u32 {
        // 最后一个 <= offset 的行起点
        match self.0.binary_search(&offset) {
            Ok(i) => i as u32 + 1,
            Err(i) => i as u32, // i>=1 因为 v[0]=0
        }
    }
}

/// 调用目标的渲染（真源用 `ast.unparse(node.func)`）。
///
/// 直接走 `rustpython-ast` 的 `impl Display for Expr`（它就是它的 unparser）。
///
/// **为什么不自己拼点号名**：那会**丢参数内容**——真源给出
/// `hashlib.sha256(p.read_bytes()).hexdigest` / `subject.replace('/', '__').replace`，
/// 自拼只给 `hashlib.sha256().hexdigest` / `subject.replace().replace`。
/// 逐文件对账当场暴露了 165 处差异（实测）。虽然这些差异**当时看**不影响判定
/// （判据只用「整串是否在 `DANGEROUS_CALLS`」与「末段是否在 `METHOD_SINKS`」），
/// 但"当时看"不是证据——**用真源同款的 unparse，才算把这段对齐**。
fn unparse_expr(e: &past::Expr) -> String {
    format!("{}", e)
}

/// 真源 `_try_guards_import`。
fn try_guards_import(t: &past::StmtTry) -> bool {
    for h in &t.handlers {
        let past::ExceptHandler::ExceptHandler(h) = h;
        // 裸 `except:` ⇒ 兜住了
        let Some(ty) = h.type_.as_deref() else { return true };
        let hit = |id: &str| {
            id == "ImportError" || id == "ModuleNotFoundError" || id == "Exception"
        };
        match ty {
            past::Expr::Name(n) if hit(n.id.as_str()) => return true,
            past::Expr::Tuple(tup) => {
                for e in &tup.elts {
                    if let past::Expr::Name(n) = e {
                        if hit(n.id.as_str()) {
                            return true;
                        }
                    }
                }
            }
            _ => {}
        }
    }
    false
}

/// 收集一段语句里（深度任意）所有 `Import` / `ImportFrom` 的行号——真源这里用 `ast.walk`，
/// 但只塞进**集合**，故顺序无关。
struct ImportLinenos<'a> {
    ls: &'a LineStarts,
    out: Vec<u32>,
}
impl past::Visitor for ImportLinenos<'_> {
    fn visit_stmt(&mut self, node: past::Stmt) {
        match &node {
            past::Stmt::Import(i) => {
                for _ in &i.names {
                    self.out.push(self.ls.line_of(u32::from(node.range().start())));
                }
            }
            past::Stmt::ImportFrom(_) => {
                self.out.push(self.ls.line_of(u32::from(node.range().start())));
            }
            _ => {}
        }
        self.generic_visit_stmt(node);
    }
}

enum Ev {
    Raise(u32, String),
    Import(Vec<(String, u32)>),
    ImportFrom(String, u32),
    Call(u32, String, bool),
}

/// ---- 共享的「补下钻」助手 ----
///
/// `rustpython-ast` 生成的 visitor 里这些 `generic_visit_*` 是**空实现**（见本文件顶部说明），
/// 故每个自写的 Visitor 都要补。**抽成函数是为了不让两份实现漂移**：
/// `Collector`（AST 事实）与 `MetricCollector`（规模/复杂度）共用同一套下钻。
pub(crate) fn d_comprehension<V: past::Visitor>(v: &mut V, node: past::Comprehension) {
    // CPython `comprehension._fields` = target, iter, ifs, is_async
    v.visit_expr(node.target.clone());
    v.visit_expr(node.iter.clone());
    for e in &node.ifs {
        v.visit_expr(e.clone());
    }
}

pub(crate) fn d_withitem<V: past::Visitor>(v: &mut V, node: past::WithItem) {
    // CPython `withitem._fields` = context_expr, optional_vars
    v.visit_expr(node.context_expr.clone());
    if let Some(x) = &node.optional_vars {
        v.visit_expr(x.as_ref().clone());
    }
}

pub(crate) fn d_keyword<V: past::Visitor>(v: &mut V, node: past::Keyword) {
    // CPython `keyword._fields` = arg, value（arg 只是名字）
    v.visit_expr(node.value.clone());
}

pub(crate) fn d_arg<V: past::Visitor>(v: &mut V, node: past::Arg) {
    // CPython `arg._fields` = arg, annotation, type_comment
    if let Some(a) = &node.annotation {
        v.visit_expr(a.as_ref().clone());
    }
}

pub(crate) fn d_arguments<V: past::Visitor>(v: &mut V, node: past::Arguments) {
    // CPython `arguments._fields` = posonlyargs, args, vararg, kwonlyargs,
    //                             kw_defaults, kwarg, defaults
    // rustpython 把 default 嵌在 `ArgWithDefault` 里、没有独立的 `defaults` 字段，
    // 故按 CPython 的字段顺序重排（先全部 annotation，再 kw_defaults，最后 defaults）。
    for a in &node.posonlyargs {
        v.visit_arg(a.def.clone());
    }
    for a in &node.args {
        v.visit_arg(a.def.clone());
    }
    if let Some(x) = &node.vararg {
        v.visit_arg(x.as_ref().clone());
    }
    for a in &node.kwonlyargs {
        v.visit_arg(a.def.clone());
    }
    for a in &node.kwonlyargs {
        if let Some(d) = &a.default {
            v.visit_expr(d.as_ref().clone());
        }
    }
    if let Some(k) = &node.kwarg {
        v.visit_arg(k.as_ref().clone());
    }
    for a in node.posonlyargs.iter().chain(node.args.iter()) {
        if let Some(d) = &a.default {
            v.visit_expr(d.as_ref().clone());
        }
    }
}

pub(crate) fn d_match_case<V: past::Visitor>(v: &mut V, node: past::MatchCase) {
    // CPython `match_case._fields` = pattern, guard, body
    v.visit_pattern(node.pattern.clone());
    if let Some(g) = &node.guard {
        v.visit_expr(g.as_ref().clone());
    }
    for st in &node.body {
        v.visit_stmt(st.clone());
    }
}

struct Collector<'a> {
    ls: &'a LineStarts,
    depth: usize,
    seq: usize,
    evs: Vec<(usize, usize, Ev)>,
    guarded: BTreeSet<u32>,
}

impl Collector<'_> {
    fn enter(&mut self) -> usize {
        let d = self.depth;
        self.depth += 1;
        d
    }
    fn exit(&mut self) {
        self.depth -= 1;
    }
    fn push(&mut self, d: usize, ev: Ev) {
        let s = self.seq;
        self.seq += 1;
        self.evs.push((d, s, ev));
    }
}

impl past::Visitor for Collector<'_> {
    fn visit_stmt(&mut self, node: past::Stmt) {
        let ln = self.ls.line_of(u32::from(node.range().start()));
        let d = self.depth;
        match &node {
            past::Stmt::Raise(r) => {
                if let Some(exc) = &r.exc {
                    if let past::Expr::Call(c) = exc.as_ref() {
                        if let Some(a0) = c.args.first() {
                            match a0 {
                                past::Expr::Constant(k) => {
                                    if let past::Constant::Str(s) = &k.value {
                                        self.push(d, Ev::Raise(ln, s.to_string()));
                                    }
                                }
                                past::Expr::JoinedStr(js) => {
                                    let parts: String = js
                                        .values
                                        .iter()
                                        .filter_map(|v| match v {
                                            past::Expr::Constant(k) => match &k.value {
                                                past::Constant::Str(s) => Some(s.to_string()),
                                                _ => None,
                                            },
                                            _ => None,
                                        })
                                        .collect();
                                    self.push(d, Ev::Raise(ln, parts));
                                }
                                _ => {}
                            }
                        }
                    }
                }
            }
            past::Stmt::Import(i) => {
                let mut v = Vec::new();
                for a in &i.names {
                    let head = a.name.split('.').next().unwrap_or("").to_string();
                    v.push((head, ln));
                }
                self.push(d, Ev::Import(v));
            }
            past::Stmt::ImportFrom(f) => {
                let level = f.level.map(|l| l.to_u32()).unwrap_or(0);
                if level == 0 {
                    if let Some(m) = &f.module {
                        let head = m.as_str().split('.').next().unwrap_or("").to_string();
                        self.push(d, Ev::ImportFrom(head, ln));
                    }
                }
            }
            past::Stmt::Try(t) => {
                if try_guards_import(t) {
                    for sub in &t.body {
                        let mut c = ImportLinenos { ls: self.ls, out: Vec::new() };
                        c.visit_stmt(sub.clone());
                        for l in c.out {
                            self.guarded.insert(l);
                        }
                    }
                }
            }
            _ => {}
        }
        let d2 = self.enter();
        debug_assert_eq!(d, d2);
        self.generic_visit_stmt(node);
        self.exit();
    }

    fn visit_expr(&mut self, node: past::Expr) {
        let d = self.depth;
        if let past::Expr::Call(c) = &node {
            let ln = self.ls.line_of(u32::from(node.range().start()));
            let shell = c.keywords.iter().any(|k| {
                k.arg.as_ref().map(|a| a.as_str() == "shell").unwrap_or(false)
                    && matches!(&k.value, past::Expr::Constant(kk)
                        if matches!(kk.value, past::Constant::Bool(true)))
            });
            self.push(d, Ev::Call(ln, unparse_expr(&c.func), shell));
        }
        self.enter();
        self.generic_visit_expr(node);
        self.exit();
    }

    // ---- 其余顶层钩子：既要**深度**、又要**自己下钻** ----
    //
    // ⚠️ 实测（2026-10-04，逐构造探针）：`rustpython-ast` 生成的 visitor 里，
    // 下列 `generic_visit_*` 是**空实现**（不下钻）：`comprehension` / `arguments` / `arg` /
    // `keyword` / `alias` / `withitem` / `match_case` / 若干 pattern·type_param。
    // 而 CPython 的 `ast.walk` 会遍历**全部** `_fields`——故这些路径上的 `Call` 会被漏收
    // （探针实测漏掉：`with ... as x:` 的 `context_expr`、关键字参数值、推导式的 `if`）。
    // 这里按 **CPython 的 `_fields` 顺序**补下钻，否则 (深度, 前序) 排序不再等于 BFS 序。

    fn visit_comprehension(&mut self, node: past::Comprehension) {
        self.enter();
        d_comprehension(self, node);
        self.exit();
    }
    fn visit_excepthandler(&mut self, node: past::ExceptHandler) {
        self.enter();
        self.generic_visit_excepthandler(node);
        self.exit();
    }
    fn visit_arguments(&mut self, node: past::Arguments) {
        self.enter();
        d_arguments(self, node);
        self.exit();
    }
    fn visit_arg(&mut self, node: past::Arg) {
        self.enter();
        d_arg(self, node);
        self.exit();
    }
    fn visit_keyword(&mut self, node: past::Keyword) {
        self.enter();
        d_keyword(self, node);
        self.exit();
    }
    fn visit_alias(&mut self, _node: past::Alias) {
        self.enter();
        // `alias` 无子节点
        self.exit();
    }
    fn visit_withitem(&mut self, node: past::WithItem) {
        self.enter();
        d_withitem(self, node);
        self.exit();
    }
    fn visit_match_case(&mut self, node: past::MatchCase) {
        self.enter();
        d_match_case(self, node);
        self.exit();
    }
    fn visit_pattern(&mut self, node: past::Pattern) {
        self.enter();
        self.generic_visit_pattern(node);
        self.exit();
    }
    fn visit_type_param(&mut self, node: past::TypeParam) {
        self.enter();
        self.generic_visit_type_param(node);
        self.exit();
    }
}

/// 真源 `_ast_facts`：解析失败 → `None`（对应真源 `except SyntaxError: got = None`）。
pub fn purity_facts(text: &str) -> Option<PurityFacts> {
    let suite = parse(text, Mode::Module, "<nf>").ok()?;
    let ls = LineStarts::new(text);
    let mut c = Collector { ls: &ls, depth: 0, seq: 0, evs: Vec::new(), guarded: BTreeSet::new() };
    match &suite {
        past::Mod::Module(m) => {
            for st in &m.body {
                c.visit_stmt(st.clone());
            }
        }
        past::Mod::Expression(e) => c.visit_expr(e.body.as_ref().clone()),
        // 本线只用 `Mode::Module` 解析；其余两种形态不产事实
        _ => {}
    }
    // 按 (深度, 前序) 排序 == BFS 序
    c.evs.sort_by_key(|(d, s, _)| (*d, *s));

    let mut out = PurityFacts {
        raises: Vec::new(),
        guarded: c.guarded,
        modules: Vec::new(),
        sinks: Vec::new(),
    };
    for (_, _, ev) in c.evs {
        match ev {
            Ev::Raise(l, m) => out.raises.push(RaiseFact { lineno: l, msg: m }),
            Ev::Import(v) => out.modules.extend(v),
            Ev::ImportFrom(m, l) => out.modules.push((m, l)),
            Ev::Call(l, c, s) => out.sinks.push(SinkFact { lineno: l, call: c, shell_true: s }),
        }
    }
    Some(out)
}

// ---------------------------------------------------------------- 差分对账入口

/// 真源 `purity_scan.IMPORT_SCAN` 的三条面。
pub const IMPORT_SCAN: [&str; 3] =
    ["desktop/src/core/*.py", "scripts/*.py", ".github/scripts/*.py"];

/// 把 `_ast_facts` 的事实导成 JSON（供与真源**逐文件**差分对账）。
///
/// 形状：`{ "<相对路径>": {"raises": [[行, 消息], …], "guarded": [行, …],
///                        "modules": [[模块, 行], …], "sinks": [[行, 调用, shell], …]} }`
pub fn facts_dump(root: &std::path::Path) -> crate::pyjson::Json {
    use crate::pyjson::Json;
    let mut out: Vec<(String, Json)> = Vec::new();
    let mut rels: Vec<String> = Vec::new();
    for pat in IMPORT_SCAN {
        rels.extend(crate::glob::expand(root, pat));
    }
    rels.sort();
    rels.dedup();
    for rel in rels {
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else { continue };
        let Some(f) = purity_facts(&text) else {
            out.push((rel, Json::Null));
            continue;
        };
        let raises = Json::Array(
            f.raises
                .iter()
                .map(|r| Json::Array(vec![Json::Int(r.lineno as i64), Json::Str(r.msg.clone())]))
                .collect(),
        );
        let guarded = Json::Array(f.guarded.iter().map(|l| Json::Int(*l as i64)).collect());
        let modules = Json::Array(
            f.modules
                .iter()
                .map(|(m, l)| Json::Array(vec![Json::Str(m.clone()), Json::Int(*l as i64)]))
                .collect(),
        );
        let sinks = Json::Array(
            f.sinks
                .iter()
                .map(|s| {
                    Json::Array(vec![
                        Json::Int(s.lineno as i64),
                        Json::Str(s.call.clone()),
                        Json::Bool(s.shell_true),
                    ])
                })
                .collect(),
        );
        out.push((
            rel,
            Json::Object(vec![
                ("raises".to_string(), raises),
                ("guarded".to_string(), guarded),
                ("modules".to_string(), modules),
                ("sinks".to_string(), sinks),
            ]),
        ));
    }
    Json::Object(out)
}

// ---------------------------------------------------------------- 规模/复杂度度量（code_metrics）

/// 一个函数的度量：`(名字, 起行, 止行, 圈复杂度)`。
pub struct FnMetric {
    pub name: String,
    pub lineno: u32,
    pub end_lineno: u32,
    pub cc: i64,
    /// BFS 序还原用（真源 `worst_fn` 是**严格大于**才更新 ⇒ 并列时 walk 序在前者赢）
    pub depth: usize,
    pub seq: usize,
}

/// 遍历完备的度量收集器。
///
/// **为什么要"遍历完备"**：真源 `_fn_cc(fn)` 用 `ast.walk(fn)` 数该函数**子树**里的判定点。
/// 若漏下钻（`rustpython-ast` 那些空 generic），嵌套在关键字参数 / 推导式里的 `BoolOp` 或
/// `IfExp` 就会漏计 ⇒ 圈复杂度偏小 ⇒ 与冻结基线比较时**假绿**。故这里与 `Collector` 共用
/// 同一套下钻助手。
///
/// **为什么用栈**：真源对**每个**函数各 walk 一次，故嵌套函数体里的判定点会**同时**计进
/// 内外两层函数（`ast.walk(outer)` 会下钻到 inner）。用栈即可一次遍历复刻这一语义。
pub struct MetricFacts {
    pub fns: Vec<FnMetric>,
}

struct MetricCollector<'a> {
    ls: &'a LineStarts,
    stack: Vec<(String, u32, u32, i64, usize, usize)>,
    out: Vec<FnMetric>,
    depth: usize,
    seq: usize,
}

impl MetricCollector<'_> {
    fn bump(&mut self, n: i64) {
        for e in self.stack.iter_mut() {
            e.3 += n;
        }
    }
    fn entering_fn(&mut self, name: &str, start: u32, end: u32) {
        let d = self.depth;
        let s = self.seq;
        self.seq += 1;
        self.stack.push((name.to_string(), start, end, 1, d, s));
        self.depth += 1;
    }
    fn leaving_fn(&mut self) {
        self.depth -= 1;
        if let Some((name, lineno, end_lineno, cc, depth, seq)) = self.stack.pop() {
            self.out.push(FnMetric { name, lineno, end_lineno, cc, depth, seq });
        }
    }
    /// 普通节点进出（只为**深度**正确）
    fn enter(&mut self) {
        self.seq += 1;
        self.depth += 1;
    }
    fn exit(&mut self) {
        self.depth -= 1;
    }
}

impl past::Visitor for MetricCollector<'_> {
    fn visit_stmt(&mut self, node: past::Stmt) {
        let r = node.range();
        let start = u32::from(r.start());
        // `end_lineno` 是**含**末字符的行；rustpython 的 range.end 是**排他**偏移 ⇒ 减一
        let end_off = u32::from(r.end()).saturating_sub(1);
        let start_line = self.ls.line_of(start);
        match &node {
            past::Stmt::FunctionDef(f) => {
                let end_line = self.ls.line_of(end_off);
                self.entering_fn(f.name.as_str(), start_line, end_line);
                self.generic_visit_stmt(node);
                self.leaving_fn();
                return;
            }
            past::Stmt::AsyncFunctionDef(f) => {
                let end_line = self.ls.line_of(end_off);
                self.entering_fn(f.name.as_str(), start_line, end_line);
                self.generic_visit_stmt(node);
                self.leaving_fn();
                return;
            }
            // 判定点（真源 `_fn_cc` 的集合里属 Stmt 的那些）
            past::Stmt::If(_)
            | past::Stmt::For(_)
            | past::Stmt::AsyncFor(_)
            | past::Stmt::While(_)
            | past::Stmt::With(_)
            | past::Stmt::AsyncWith(_)
            | past::Stmt::Assert(_) => self.bump(1),
            _ => {}
        }
        self.enter();
        self.generic_visit_stmt(node);
        self.exit();
    }

    fn visit_expr(&mut self, node: past::Expr) {
        match &node {
            past::Expr::IfExp(_) => self.bump(1),
            past::Expr::BoolOp(b) => {
                let extra = b.values.len() as i64 - 1;
                if extra > 0 {
                    self.bump(extra);
                }
            }
            _ => {}
        }
        self.enter();
        self.generic_visit_expr(node);
        self.exit();
    }

    fn visit_excepthandler(&mut self, node: past::ExceptHandler) {
        // 真源把 `ExceptHandler` 也算判定点
        self.bump(1);
        self.enter();
        self.generic_visit_excepthandler(node);
        self.exit();
    }

    fn visit_comprehension(&mut self, node: past::Comprehension) {
        self.enter();
        d_comprehension(self, node);
        self.exit();
    }
    fn visit_arguments(&mut self, node: past::Arguments) {
        self.enter();
        d_arguments(self, node);
        self.exit();
    }
    fn visit_arg(&mut self, node: past::Arg) {
        self.enter();
        d_arg(self, node);
        self.exit();
    }
    fn visit_keyword(&mut self, node: past::Keyword) {
        self.enter();
        d_keyword(self, node);
        self.exit();
    }
    fn visit_alias(&mut self, _node: past::Alias) {
        self.enter();
        self.exit();
    }
    fn visit_withitem(&mut self, node: past::WithItem) {
        self.enter();
        d_withitem(self, node);
        self.exit();
    }
    fn visit_match_case(&mut self, node: past::MatchCase) {
        self.enter();
        d_match_case(self, node);
        self.exit();
    }
    fn visit_pattern(&mut self, node: past::Pattern) {
        self.enter();
        self.generic_visit_pattern(node);
        self.exit();
    }
    fn visit_type_param(&mut self, node: past::TypeParam) {
        self.enter();
        self.generic_visit_type_param(node);
        self.exit();
    }
}

/// 真源 `code_metrics.metrics_of` 里与 AST 有关的部分：所有函数的 `(名, 起行, 止行, cc)`。
/// `None` = 语法不可解析（真源记 `syntax_error`）。
pub fn metric_facts(text: &str) -> Option<MetricFacts> {
    let suite = parse(text, Mode::Module, "<nf>").ok()?;
    let ls = LineStarts::new(text);
    let mut c = MetricCollector { ls: &ls, stack: Vec::new(), out: Vec::new(), depth: 0, seq: 0 };
    match &suite {
        past::Mod::Module(m) => {
            for st in &m.body {
                c.visit_stmt(st.clone());
            }
        }
        past::Mod::Expression(e) => c.visit_expr(e.body.as_ref().clone()),
        _ => {}
    }
    // (深度, 前序) 排序 == CPython `ast.walk` 的 BFS 序（真源 `worst_fn` 取严格大于，
    // 故并列时"谁先被 walk 到"决定 `worst_fn`）
    let mut fns = c.out;
    fns.sort_by_key(|f| (f.depth, f.seq));
    Some(MetricFacts { fns })
}

