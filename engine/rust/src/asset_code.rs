//! `asset_contract` 的**代码面**：AST 规范符合性 + **可证**空指针 + 测试件在场。
//!
//! 口径见真源 `asset_contract.py` 代码面那段。三处要点：
//!
//! 1. **`_walk_scope` 不进入嵌套函数/lambda/类**（各自另算，避免跨作用域误判）——本线用
//!    Visitor 在这几类节点上**提前返回**实现同一语义。
//! 2. `_derefs` 的行号顺序：真源用 `ast.iter_child_nodes` + 栈（LIFO）⇒ 子节点**逆序**；
//!    但其结果最终进 `sorted(out, key=lineno)` + 去重，故**文档序与 LIFO 序等价**。
//!    本线用文档序，理由写在这里而不是"反正一样"。
//! 3. `_none_deref` 与 `_denied_calls` 的结果顺序**可观察**（前者稳定排序 + 去重，
//!    后者直接进 issues）⇒ 前者取 BFS 序函数种子、后者取 BFS 序调用序列。

use crate::pyast::{d_arguments, d_comprehension, d_keyword, d_match_case, d_withitem};
use rustpython_ast as past;
use rustpython_ast::Ranged;
use rustpython_ast::Visitor as _;
use std::collections::BTreeSet;

/// 真源 `_walk_scope` 的"不进"集合。
fn is_scope_boundary_stmt(s: &past::Stmt) -> bool {
    matches!(
        s,
        past::Stmt::FunctionDef(_) | past::Stmt::AsyncFunctionDef(_) | past::Stmt::ClassDef(_)
    )
}

// ---------------------------------------------------------------- 名字收集

/// 真源 `_assigned_names`（结果是无序集合，故遍历序无关）。
struct NameCollector {
    out: BTreeSet<String>,
}

impl past::Visitor for NameCollector {
    fn visit_stmt(&mut self, node: past::Stmt) {
        if is_scope_boundary_stmt(&node) {
            return; // 不进入嵌套作用域
        }
        match &node {
            past::Stmt::Assign(a) => {
                for t in &a.targets {
                    if let past::Expr::Name(n) = t {
                        self.out.insert(n.id.to_string());
                    }
                }
            }
            past::Stmt::AnnAssign(a) => {
                if let past::Expr::Name(n) = a.target.as_ref() {
                    self.out.insert(n.id.to_string());
                }
            }
            past::Stmt::AugAssign(a) => {
                if let past::Expr::Name(n) = a.target.as_ref() {
                    self.out.insert(n.id.to_string());
                }
            }
            past::Stmt::For(f) => {
                if let past::Expr::Name(n) = f.target.as_ref() {
                    self.out.insert(n.id.to_string());
                }
            }
            past::Stmt::AsyncFor(f) => {
                if let past::Expr::Name(n) = f.target.as_ref() {
                    self.out.insert(n.id.to_string());
                }
            }
            _ => {}
        }
        self.generic_visit_stmt(node);
    }

    fn visit_expr(&mut self, node: past::Expr) {
        if matches!(node, past::Expr::Lambda(_)) {
            return;
        }
        self.generic_visit_expr(node);
    }

    fn visit_withitem(&mut self, node: past::WithItem) {
        if let Some(v) = &node.optional_vars {
            if let past::Expr::Name(n) = v.as_ref() {
                self.out.insert(n.id.to_string());
            }
        }
        d_withitem(self, node);
    }

    // 其余钩子：既补下钻，又不跨作用域
    fn visit_comprehension(&mut self, node: past::Comprehension) {
        d_comprehension(self, node);
    }
    fn visit_arguments(&mut self, node: past::Arguments) {
        d_arguments(self, node);
    }
    fn visit_arg(&mut self, node: past::Arg) {
        if let Some(a) = &node.annotation {
            self.visit_expr(a.as_ref().clone());
        }
    }
    fn visit_keyword(&mut self, node: past::Keyword) {
        d_keyword(self, node);
    }
    fn visit_alias(&mut self, _n: past::Alias) {}
    fn visit_match_case(&mut self, node: past::MatchCase) {
        d_match_case(self, node);
    }
    fn visit_pattern(&mut self, node: past::Pattern) {
        self.generic_visit_pattern(node);
    }
    fn visit_type_param(&mut self, node: past::TypeParam) {
        self.generic_visit_type_param(node);
    }
    fn visit_excepthandler(&mut self, node: past::ExceptHandler) {
        self.generic_visit_excepthandler(node);
    }
}

pub fn assigned_names(stmt: &past::Stmt) -> BTreeSet<String> {
    let mut c = NameCollector { out: BTreeSet::new() };
    c.visit_stmt(stmt.clone());
    c.out
}

// ---------------------------------------------------------------- 判据

/// 真源 `_is_none`。
fn is_none(node: Option<&past::Expr>) -> bool {
    matches!(node, Some(past::Expr::Constant(c)) if matches!(c.value, past::Constant::None))
}

/// 真源 `_assigns_none`。
fn assigns_none(stmt: &past::Stmt, name: &str) -> bool {
    match stmt {
        past::Stmt::Assign(a) if a.targets.len() == 1 => match &a.targets[0] {
            past::Expr::Name(n) => n.id.as_str() == name && is_none(Some(a.value.as_ref())),
            _ => false,
        },
        past::Stmt::AnnAssign(a) => match a.target.as_ref() {
            past::Expr::Name(n) => n.id.as_str() == name && is_none(a.value.as_deref()),
            _ => false,
        },
        _ => false,
    }
}

/// 真源 `_guard` → `(名字, "is-none"|"is-not-none")`。
fn guard(stmt: &past::Stmt) -> Option<(String, &'static str)> {
    let test = match stmt {
        past::Stmt::If(i) => &i.test,
        past::Stmt::While(w) => &w.test,
        past::Stmt::Assert(a) => &a.test,
        _ => return None,
    };
    let past::Expr::Compare(c) = test.as_ref() else { return None };
    if c.ops.len() != 1 || c.comparators.len() != 1 {
        return None;
    }
    let past::Expr::Name(left) = c.left.as_ref() else {
        return None;
    };
    if !is_none(Some(&c.comparators[0])) {
        return None;
    }
    match &c.ops[0] {
        past::CmpOp::Is => Some((left.id.to_string(), "is-none")),
        past::CmpOp::IsNot => Some((left.id.to_string(), "is-not-none")),
        _ => None,
    }
}

/// 真源 `_always_exits`。
fn always_exits(stmts: &[past::Stmt]) -> bool {
    let Some(last) = stmts.last() else { return false };
    match last {
        past::Stmt::Return(_) | past::Stmt::Raise(_) | past::Stmt::Continue(_)
        | past::Stmt::Break(_) => true,
        past::Stmt::If(i) => {
            !i.orelse.is_empty() && always_exits(&i.body) && always_exits(&i.orelse)
        }
        _ => false,
    }
}

/// `_head_exprs` 的三种去向：若/循环的条件、with 的 context_expr、其余整条语句。
enum Head {
    Exprs(Vec<past::Expr>),
    Whole(past::Stmt),
}

/// 真源 `_head_exprs`。
fn head_exprs(stmt: &past::Stmt) -> Head {
    match stmt {
        past::Stmt::If(i) => Head::Exprs(vec![i.test.as_ref().clone()]),
        past::Stmt::While(w) => Head::Exprs(vec![w.test.as_ref().clone()]),
        past::Stmt::For(f) => Head::Exprs(vec![f.iter.as_ref().clone()]),
        past::Stmt::AsyncFor(f) => Head::Exprs(vec![f.iter.as_ref().clone()]),
        past::Stmt::With(w) => {
            Head::Exprs(w.items.iter().map(|i| i.context_expr.clone()).collect())
        }
        past::Stmt::AsyncWith(w) => {
            Head::Exprs(w.items.iter().map(|i| i.context_expr.clone()).collect())
        }
        past::Stmt::Try(_)
        | past::Stmt::FunctionDef(_)
        | past::Stmt::AsyncFunctionDef(_)
        | past::Stmt::ClassDef(_) => Head::Exprs(Vec::new()),
        _ => Head::Whole(stmt.clone()),
    }
}

/// 收集"对当前可证为 None 的名字的解引用"行号。
struct DerefCollector<'a> {
    names: &'a BTreeSet<String>,
    ls: &'a crate::pyast::LineStarts,
    out: Vec<u32>,
}

impl DerefCollector<'_> {
    fn look(&mut self, e: &past::Expr) {
        match e {
            past::Expr::Attribute(a) => {
                if let past::Expr::Name(n) = a.value.as_ref() {
                    if self.names.contains(n.id.as_str()) {
                        self.out.push(line_of(e, self.ls));
                    }
                }
            }
            past::Expr::Subscript(s) => {
                if let past::Expr::Name(n) = s.value.as_ref() {
                    if self.names.contains(n.id.as_str()) {
                        self.out.push(line_of(e, self.ls));
                    }
                }
            }
            past::Expr::Call(c) => {
                if let past::Expr::Name(n) = c.func.as_ref() {
                    if self.names.contains(n.id.as_str()) {
                        self.out.push(line_of(e, self.ls));
                    }
                }
            }
            _ => {}
        }
    }
}

/// 从节点取 1-based 行号（真源 `n.lineno`）。
fn line_of<T: Ranged>(n: &T, ls: &crate::pyast::LineStarts) -> u32 {
    ls.line_of(u32::from(n.range().start()))
}

impl past::Visitor for DerefCollector<'_> {
    fn visit_stmt(&mut self, node: past::Stmt) {
        if is_scope_boundary_stmt(&node) {
            return;
        }
        self.generic_visit_stmt(node);
    }
    fn visit_expr(&mut self, node: past::Expr) {
        if matches!(node, past::Expr::Lambda(_)) {
            return;
        }
        self.look(&node);
        self.generic_visit_expr(node);
    }
    fn visit_comprehension(&mut self, node: past::Comprehension) {
        d_comprehension(self, node);
    }
    fn visit_arguments(&mut self, node: past::Arguments) {
        d_arguments(self, node);
    }
    fn visit_arg(&mut self, node: past::Arg) {
        if let Some(a) = &node.annotation {
            self.visit_expr(a.as_ref().clone());
        }
    }
    fn visit_keyword(&mut self, node: past::Keyword) {
        d_keyword(self, node);
    }
    fn visit_alias(&mut self, _n: past::Alias) {}
    fn visit_withitem(&mut self, node: past::WithItem) {
        d_withitem(self, node);
    }
    fn visit_match_case(&mut self, node: past::MatchCase) {
        d_match_case(self, node);
    }
    fn visit_pattern(&mut self, node: past::Pattern) {
        self.generic_visit_pattern(node);
    }
    fn visit_type_param(&mut self, node: past::TypeParam) {
        self.generic_visit_type_param(node);
    }
    fn visit_excepthandler(&mut self, node: past::ExceptHandler) {
        self.generic_visit_excepthandler(node);
    }
}

/// 真源 `_derefs`。
fn derefs(stmt: &past::Stmt, names: &BTreeSet<String>, ls: &crate::pyast::LineStarts) -> Vec<u32> {
    let mut c = DerefCollector { names, ls, out: Vec::new() };
    match head_exprs(stmt) {
        Head::Exprs(v) => {
            for e in v {
                c.visit_expr(e);
            }
        }
        Head::Whole(s) => c.visit_stmt(s),
    }
    c.out
}

/// 真源 `_scan_block`。
fn scan_block(
    stmts: &[past::Stmt],
    cur: &BTreeSet<String>,
    rel: &str,
    ls: &crate::pyast::LineStarts,
    out: &mut Vec<(String, u32, String)>,
) -> BTreeSet<String> {
    let mut cur = cur.clone();
    for st in stmts {
        for lineno in derefs(st, &cur, ls) {
            out.push((rel.to_string(), lineno, cur.iter().cloned().collect::<Vec<_>>().join(",")));
        }
        match st {
            past::Stmt::Assign(_) | past::Stmt::AnnAssign(_) | past::Stmt::AugAssign(_) => {
                for name in assigned_names(st) {
                    if assigns_none(st, &name) {
                        cur.insert(name);
                    } else {
                        cur.remove(&name);
                    }
                }
            }
            past::Stmt::Assert(_) => {
                if let Some((n, kind)) = guard(st) {
                    if kind == "is-not-none" {
                        cur.remove(&n);
                    }
                }
            }
            past::Stmt::If(i) => {
                let g = guard(st);
                match &g {
                    Some((n, "is-not-none")) => {
                        let mut sub = cur.clone();
                        sub.remove(n);
                        scan_block(&i.body, &sub, rel, ls, out);
                        scan_block(&i.orelse, &cur, rel, ls, out);
                    }
                    Some((n, "is-none")) => {
                        scan_block(&i.body, &cur, rel, ls, out);
                        let mut sub = cur.clone();
                        sub.remove(n);
                        scan_block(&i.orelse, &sub, rel, ls, out);
                    }
                    _ => {
                        scan_block(&i.body, &cur, rel, ls, out);
                        scan_block(&i.orelse, &cur, rel, ls, out);
                    }
                }
                if let Some((n, "is-none")) = &g {
                    if always_exits(&i.body) {
                        cur.remove(n);
                    }
                }
                for name in assigned_names(st) {
                    cur.remove(&name);
                }
            }
            past::Stmt::For(f) => {
                scan_block(&f.body, &cur, rel, ls, out);
                for name in assigned_names(st) {
                    cur.remove(&name);
                }
            }
            past::Stmt::AsyncFor(f) => {
                scan_block(&f.body, &cur, rel, ls, out);
                for name in assigned_names(st) {
                    cur.remove(&name);
                }
            }
            past::Stmt::While(w) => {
                scan_block(&w.body, &cur, rel, ls, out);
                for name in assigned_names(st) {
                    cur.remove(&name);
                }
            }
            past::Stmt::With(w) => {
                scan_block(&w.body, &cur, rel, ls, out);
                for name in assigned_names(st) {
                    cur.remove(&name);
                }
            }
            past::Stmt::AsyncWith(w) => {
                scan_block(&w.body, &cur, rel, ls, out);
                for name in assigned_names(st) {
                    cur.remove(&name);
                }
            }
            past::Stmt::Try(t) => {
                scan_block(&t.body, &cur, rel, ls, out);
                for h in &t.handlers {
                    let past::ExceptHandler::ExceptHandler(h) = h;
                    scan_block(&h.body, &cur, rel, ls, out);
                }
                scan_block(&t.orelse, &cur, rel, ls, out);
                scan_block(&t.finalbody, &cur, rel, ls, out);
                for name in assigned_names(st) {
                    cur.remove(&name);
                }
            }
            _ => {}
        }
    }
    cur
}

/// BFS 序的函数种子（真源 `for fn in ast.walk(tree)` 收集 `FunctionDef/AsyncFunctionDef`）。
struct SeedCollector {
    depth: usize,
    seq: usize,
    out: Vec<(usize, usize, Vec<past::Stmt>, BTreeSet<String>)>,
}

impl past::Visitor for SeedCollector {
    fn visit_stmt(&mut self, node: past::Stmt) {
        let d = self.depth;
        let s = self.seq;
        self.seq += 1;
        match &node {
            past::Stmt::FunctionDef(f) => {
                let dn = default_none(&f.args);
                self.depth += 1;
                // 不进入嵌套函数体（各自另算），但 `<函数体>` 本身要收
                self.out.push((d, s, f.body.clone(), dn));
                self.depth -= 1;
                self.generic_visit_stmt(node);
                return;
            }
            past::Stmt::AsyncFunctionDef(f) => {
                let dn = default_none(&f.args);
                self.depth += 1;
                self.out.push((d, s, f.body.clone(), dn));
                self.depth -= 1;
                self.generic_visit_stmt(node);
                return;
            }
            _ => {}
        }
        self.depth += 1;
        self.generic_visit_stmt(node);
        self.depth -= 1;
    }
    fn visit_expr(&mut self, node: past::Expr) {
        // 真源只把 `FunctionDef` / `AsyncFunctionDef` 当种子（**不含 lambda**）
        self.seq += 1;
        self.depth += 1;
        self.generic_visit_expr(node);
        self.depth -= 1;
    }
    fn visit_comprehension(&mut self, node: past::Comprehension) {
        d_comprehension(self, node);
    }
    fn visit_arguments(&mut self, node: past::Arguments) {
        d_arguments(self, node);
    }
    fn visit_arg(&mut self, node: past::Arg) {
        if let Some(a) = &node.annotation {
            self.visit_expr(a.as_ref().clone());
        }
    }
    fn visit_keyword(&mut self, node: past::Keyword) {
        d_keyword(self, node);
    }
    fn visit_alias(&mut self, _n: past::Alias) {}
    fn visit_withitem(&mut self, node: past::WithItem) {
        d_withitem(self, node);
    }
    fn visit_match_case(&mut self, node: past::MatchCase) {
        d_match_case(self, node);
    }
    fn visit_pattern(&mut self, node: past::Pattern) {
        self.generic_visit_pattern(node);
    }
    fn visit_type_param(&mut self, node: past::TypeParam) {
        self.generic_visit_type_param(node);
    }
    fn visit_excepthandler(&mut self, node: past::ExceptHandler) {
        self.generic_visit_excepthandler(node);
    }
}

/// 真源 `default_none` 的推导（`pos` 的**尾部**参数配位置默认值 + kwonly 一一对应）。
fn default_none(args: &past::Arguments) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    for a in args.posonlyargs.iter().chain(args.args.iter()) {
        if is_none(a.default.as_deref()) {
            out.insert(a.def.arg.to_string());
        }
    }
    for a in &args.kwonlyargs {
        if is_none(a.default.as_deref()) {
            out.insert(a.def.arg.to_string());
        }
    }
    out
}

/// 真源 `_none_deref`。
pub fn none_deref(tree: &past::Mod, rel: &str, ls: &crate::pyast::LineStarts) -> Vec<String> {
    let mut out: Vec<(String, u32, String)> = Vec::new();
    let module_body: Vec<past::Stmt> = match tree {
        past::Mod::Module(m) => m.body.clone(),
        _ => Vec::new(),
    };
    let mut seeds: Vec<(Vec<past::Stmt>, BTreeSet<String>)> =
        vec![(module_body, BTreeSet::new())];
    let mut c = SeedCollector { depth: 0, seq: 0, out: Vec::new() };
    let empty: Vec<past::Stmt> = Vec::new();
    let body = match tree {
        past::Mod::Module(m) => &m.body,
        _ => &empty,
    };
    for st in body {
        c.visit_stmt(st.clone());
    }
    let mut fns = c.out;
    fns.sort_by_key(|(d, s, _, _)| (*d, *s));
    for (_, _, body, dn) in fns {
        seeds.push((body, dn));
    }
    for (body, seed) in seeds {
        scan_block(&body, &seed, rel, ls, &mut out);
    }
    out.sort_by_key(|(_, lineno, _)| *lineno);
    let mut seen: BTreeSet<(u32, String)> = BTreeSet::new();
    let mut msgs = Vec::new();
    for (rel_name, lineno, names) in out {
        if seen.contains(&(lineno, names.clone())) {
            continue;
        }
        seen.insert((lineno, names.clone()));
        msgs.push(format!(
            "代码件 {} 第 {} 行解引用可证为 None 的 {}（修复指引：解引用前判空，或把初始值改成真实对象——同一语句序列内没有任何重新赋值）",
            rel_name, lineno, names
        ));
    }
    msgs
}

/// 真源 `_dotted`。
pub fn dotted(node: &past::Expr) -> String {
    match node {
        past::Expr::Name(n) => n.id.to_string(),
        past::Expr::Attribute(a) => {
            let base = dotted(&a.value);
            if base.is_empty() {
                a.attr.to_string()
            } else {
                format!("{}.{}", base, a.attr)
            }
        }
        _ => String::new(),
    }
}

/// BFS 序收集调用（真源 `_denied_calls` 用 `ast.walk`，顺序进 issues）。
struct CallCollector<'a> {
    depth: usize,
    seq: usize,
    ls: &'a crate::pyast::LineStarts,
    out: Vec<(usize, usize, u32, String)>,
}

impl past::Visitor for CallCollector<'_> {
    fn visit_stmt(&mut self, node: past::Stmt) {
        self.depth += 1;
        self.generic_visit_stmt(node);
        self.depth -= 1;
    }
    fn visit_expr(&mut self, node: past::Expr) {
        let d = self.depth;
        let s = self.seq;
        self.seq += 1;
        if let past::Expr::Call(c) = &node {
            self.out.push((d, s, line_of(&node, self.ls), dotted(&c.func)));
        }
        self.depth += 1;
        self.generic_visit_expr(node);
        self.depth -= 1;
    }
    fn visit_comprehension(&mut self, node: past::Comprehension) {
        d_comprehension(self, node);
    }
    fn visit_arguments(&mut self, node: past::Arguments) {
        d_arguments(self, node);
    }
    fn visit_arg(&mut self, node: past::Arg) {
        if let Some(a) = &node.annotation {
            self.visit_expr(a.as_ref().clone());
        }
    }
    fn visit_keyword(&mut self, node: past::Keyword) {
        d_keyword(self, node);
    }
    fn visit_alias(&mut self, _n: past::Alias) {}
    fn visit_withitem(&mut self, node: past::WithItem) {
        d_withitem(self, node);
    }
    fn visit_match_case(&mut self, node: past::MatchCase) {
        d_match_case(self, node);
    }
    fn visit_pattern(&mut self, node: past::Pattern) {
        self.generic_visit_pattern(node);
    }
    fn visit_type_param(&mut self, node: past::TypeParam) {
        self.generic_visit_type_param(node);
    }
    fn visit_excepthandler(&mut self, node: past::ExceptHandler) {
        self.generic_visit_excepthandler(node);
    }
}

/// 真源 `_denied_calls`。
pub fn denied_calls(tree: &past::Mod, rel: &str, deny: &BTreeSet<String>, ls: &crate::pyast::LineStarts) -> Vec<String> {
    let mut c = CallCollector { depth: 0, seq: 0, ls, out: Vec::new() };
    let empty: Vec<past::Stmt> = Vec::new();
    let body = match tree {
        past::Mod::Module(m) => &m.body,
        _ => &empty,
    };
    for st in body {
        c.visit_stmt(st.clone());
    }
    let mut calls = c.out;
    calls.sort_by_key(|(d, s, _, _)| (*d, *s));
    calls
        .into_iter()
        .filter(|(_, _, _, name)| !name.is_empty() && deny.contains(name))
        .map(|(_, _, lineno, name)| {
            format!(
                "代码件 {} 第 {} 行调用了禁用面 {}（修复指引：换用不执行任意代码的等价实现；确需保留须改声明并写明理由）",
                rel, lineno, name
            )
        })
        .collect()
}

/// 供 observed_paths 用：BFS 序收集调用 → (depth, seq, lineno, 被调名, 每个实参若是字符串常量)
/// （真源 st.walk 里看 open / Path / pathlib.Path 的**字符串字面量**实参）。
pub fn calls_with_args(
    tree: &past::Mod,
    ls: &crate::pyast::LineStarts,
) -> Vec<(usize, usize, u32, String, Vec<Option<String>>)> {
    struct C<'a> {
        depth: usize,
        seq: usize,
        ls: &'a crate::pyast::LineStarts,
        out: Vec<(usize, usize, u32, String, Vec<Option<String>>)>,
    }
    impl past::Visitor for C<'_> {
        fn visit_stmt(&mut self, node: past::Stmt) {
            self.depth += 1;
            self.generic_visit_stmt(node);
            self.depth -= 1;
        }
        fn visit_expr(&mut self, node: past::Expr) {
            let (d, s) = (self.depth, self.seq);
            self.seq += 1;
            if let past::Expr::Call(c) = &node {
                let args = c
                    .args
                    .iter()
                    .map(|a| match a {
                        past::Expr::Constant(k) => match &k.value {
                            past::Constant::Str(v) => Some(v.to_string()),
                            _ => None,
                        },
                        _ => None,
                    })
                    .collect();
                self.out.push((d, s, line_of(&node, self.ls), dotted(&c.func), args));
            }
            self.depth += 1;
            self.generic_visit_expr(node);
            self.depth -= 1;
        }
        fn visit_comprehension(&mut self, n: past::Comprehension) {
            d_comprehension(self, n);
        }
        fn visit_arguments(&mut self, n: past::Arguments) {
            d_arguments(self, n);
        }
        fn visit_arg(&mut self, n: past::Arg) {
            if let Some(a) = &n.annotation {
                self.visit_expr(a.as_ref().clone());
            }
        }
        fn visit_keyword(&mut self, n: past::Keyword) {
            d_keyword(self, n);
        }
        fn visit_alias(&mut self, _n: past::Alias) {}
        fn visit_withitem(&mut self, n: past::WithItem) {
            d_withitem(self, n);
        }
        fn visit_match_case(&mut self, n: past::MatchCase) {
            d_match_case(self, n);
        }
        fn visit_pattern(&mut self, n: past::Pattern) {
            self.generic_visit_pattern(n);
        }
        fn visit_type_param(&mut self, n: past::TypeParam) {
            self.generic_visit_type_param(n);
        }
        fn visit_excepthandler(&mut self, n: past::ExceptHandler) {
            self.generic_visit_excepthandler(n);
        }
    }
    let empty: Vec<past::Stmt> = Vec::new();
    let body = match tree {
        past::Mod::Module(m) => &m.body,
        _ => &empty,
    };
    let mut c = C { depth: 0, seq: 0, ls, out: Vec::new() };
    for st in body {
        c.visit_stmt(st.clone());
    }
    let mut out = c.out;
    // 真源 st.walk 是 BFS 序；observed_paths 的结果进集合，但保持 BFS 序以免下游依赖漂移
    out.sort_by_key(|(d, s, _, _, _)| (*d, *s));
    out
}

