//! 模块级耦合度量与**只许收敛**的债务闸门（`coupling_metrics`）—— 与真源
//! `desktop/src/core/coupling_metrics.py` 对账。
//!
//! 外部标准只作机制借鉴（Martin 包度量 + 稳定依赖原则 SDP）：**Ca** = 有多少同包模块依赖我；
//! **Ce** = 我依赖多少同包模块；**I = Ce/(Ca+Ce)**（0 = 最稳）。SDP：依赖应指向更稳的一侧。
//!
//! 真源为什么是「登记债 + 棘轮」而非一律判死（实测口径）：首日实测 core 122 个模块 →
//! 3 个模块级环 + 5 处 SDP 违例，都是存量设计债；一次性判死会立刻红门禁且要求重构正被
//! 并发会话改写的文件。故**登记在册的债放行**，判据只拦**新增**环/新增 SDP 违例；
//! 债务被消掉时记 WARN（债务表不得虚挂）。
//!
//! **移植口径（重要）**：真源用 `ast` 抽 import；本线用**词法抽取**（先剥注释与字符串，
//! 再解析 `import` / `from … import …` 语句，含相对导入与括号多行）。这是**近似**——
//! 但它不是"悄悄近似"：任何分歧都会改变环/SDP 集合，而环/SDP 是与基线**逐条**比对的，
//! 故分歧必然以「新增环/新增 SDP 违例」的形式在对账面上暴露出来。
//!
//! 本模块是 `nf verify-report` 的 `coupling` 判据，**不单独开 CLI 面**。

use crate::jsonread;
use crate::pyjson::Json;
use crate::pyfloat;
use crate::pysrc;
use crate::pyval::{arr_items, get, plain_str, py_str};
use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

pub const BASELINE_REL: &str = "protocol/coupling_baseline.json";

/// 从（已剥注释与字符串的）源码抽同包模块依赖。
///
/// 分支次序**照抄真源**——`n.module == "core"` 在 `level` 判断**之前**，
/// 故 `from .core import x`（level=1, module="core"）走的是第一支。
fn module_deps(src: &str, stem: &str, known: &BTreeSet<String>) -> BTreeSet<String> {
    let stripped = pysrc::strip_comments_and_strings(src);
    let lines: Vec<&str> = stripped.lines().collect();
    let mut out: BTreeSet<String> = BTreeSet::new();
    let mut i = 0usize;
    while i < lines.len() {
        let t = lines[i].trim_start();
        if let Some(rest) = t.strip_prefix("import ") {
            for alias in rest.split(',') {
                let name = alias.trim().split_whitespace().next().unwrap_or("");
                if let Some(post) = name.strip_prefix("core.") {
                    out.insert(post.split('.').next().unwrap_or("").to_string());
                }
            }
        } else if let Some(rest) = t.strip_prefix("from ") {
            // 括号多行：`from core import (\n a,\n b,\n)` —— 拼到右括号为止
            let mut stmt = rest.to_string();
            if stmt.contains('(') && !stmt.contains(')') {
                i += 1;
                while i < lines.len() {
                    stmt.push(' ');
                    stmt.push_str(lines[i]);
                    if lines[i].contains(')') {
                        break;
                    }
                    i += 1;
                }
            }
            let stmt = stmt.replace(['(', ')'], " ");
            let stmt = stmt.trim();
            let Some((module_part, names_part)) = stmt.split_once(" import") else {
                i += 1;
                continue;
            };
            let module_part = module_part.trim();
            let level = module_part.chars().take_while(|c| *c == '.').count();
            let module = &module_part[level..];
            let names: Vec<String> = names_part
                .split(',')
                .map(|n| n.trim().split_whitespace().next().unwrap_or("").to_string())
                .filter(|n| !n.is_empty() && n != "*")
                .collect();
            if module == "core" {
                for n in &names {
                    out.insert(n.split('.').next().unwrap_or("").to_string());
                }
            } else if module.starts_with("core.") {
                out.insert(module.split('.').nth(1).unwrap_or("").to_string());
            } else if level > 0 && !module.is_empty() {
                out.insert(module.split('.').next().unwrap_or("").to_string());
            } else if level > 0 && module.is_empty() {
                for n in &names {
                    out.insert(n.split('.').next().unwrap_or("").to_string());
                }
            }
        }
        i += 1;
    }
    out.retain(|d| known.contains(d) && d != stem);
    out
}

pub struct Graph {
    pub deps: BTreeMap<String, BTreeSet<String>>,
    /// 模块 → I（Ce/(Ca+Ce)，4 位舍入）
    pub i_of: BTreeMap<String, f64>,
    /// Ca / Ce 是包度量的原始量（当前消费者只用 `i_of`；`write()` 那条线要用它们）。
    #[allow(dead_code)]
    pub ca: BTreeMap<String, i64>,
    #[allow(dead_code)]
    pub ce: BTreeMap<String, i64>,
}

/// 真源 `graph`。
pub fn graph(root: &Path) -> Graph {
    let mut files = crate::glob::expand(root, "desktop/src/core/*.py");
    files.sort();
    let known: BTreeSet<String> = files
        .iter()
        .map(|rel| rel.rsplit('/').next().unwrap_or(rel).trim_end_matches(".py").to_string())
        .filter(|s| s != "__init__")
        .collect();

    let mut deps: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for rel in &files {
        let stem = rel.rsplit('/').next().unwrap_or(rel).trim_end_matches(".py").to_string();
        if stem == "__init__" {
            continue;
        }
        let src = std::fs::read_to_string(root.join(rel)).unwrap_or_default();
        deps.insert(stem.clone(), module_deps(&src, &stem, &known));
    }

    let mut ca: BTreeMap<String, i64> = BTreeMap::new();
    let mut ce: BTreeMap<String, i64> = BTreeMap::new();
    let mut i_of: BTreeMap<String, f64> = BTreeMap::new();
    for m in deps.keys() {
        let c = deps.values().filter(|ds| ds.contains(m)).count() as i64;
        ca.insert(m.clone(), c);
    }
    for (m, ds) in &deps {
        ce.insert(m.clone(), ds.len() as i64);
    }
    for m in deps.keys() {
        let a = *ca.get(m).unwrap_or(&0);
        let e = *ce.get(m).unwrap_or(&0);
        let v = if a + e != 0 {
            pyfloat::round_to(e as f64 / (a + e) as f64, 4)
        } else {
            0.0
        };
        i_of.insert(m.clone(), v);
    }
    Graph { deps, i_of, ca, ce }
}

/// 真源 `cycles`：模块级环（去重、成员排序后返回）。
pub fn cycles(deps: &BTreeMap<String, BTreeSet<String>>) -> Vec<Vec<String>> {
    fn dfs(
        u: &str,
        deps: &BTreeMap<String, BTreeSet<String>>,
        color: &mut BTreeMap<String, i32>,
        stack: &mut Vec<String>,
        found: &mut BTreeSet<Vec<String>>,
    ) {
        color.insert(u.to_string(), 1);
        stack.push(u.to_string());
        if let Some(vs) = deps.get(u) {
            for v in vs {
                match color.get(v).copied().unwrap_or(0) {
                    1 => {
                        if let Some(pos) = stack.iter().position(|x| x == v) {
                            let cyc: BTreeSet<String> = stack[pos..].iter().cloned().collect();
                            found.insert(cyc.into_iter().collect());
                        }
                    }
                    0 => dfs(v, deps, color, stack, found),
                    _ => {}
                }
            }
        }
        stack.pop();
        color.insert(u.to_string(), 2);
    }
    let mut color: BTreeMap<String, i32> = BTreeMap::new();
    let mut found: BTreeSet<Vec<String>> = BTreeSet::new();
    for m in deps.keys() {
        if color.get(m).copied().unwrap_or(0) == 0 {
            let mut stack: Vec<String> = Vec::new();
            dfs(m, deps, &mut color, &mut stack, &mut found);
        }
    }
    let mut out: Vec<Vec<String>> = found.into_iter().collect();
    out.sort();
    out
}

/// 真源 `sdp_violations`：A 依赖 B 而 B 比 A 更不稳（I 更大）→ `(A, B)`。
pub fn sdp_violations(g: &Graph) -> Vec<(String, String)> {
    let mut out: Vec<(String, String)> = Vec::new();
    for (m, ds) in &g.deps {
        for d in ds {
            let di = g.i_of.get(d).copied().unwrap_or(0.0);
            let mi = g.i_of.get(m).copied().unwrap_or(0.0);
            if di > mi + 1e-9 {
                out.push((m.clone(), d.clone()));
            }
        }
    }
    out.sort();
    out
}

fn load_baseline(root: &Path) -> Option<Json> {
    if !root.join(BASELINE_REL).is_file() {
        return None;
    }
    jsonread::read_file(root, BASELINE_REL)
}

pub struct CouplingScan {
    pub issues: Vec<String>,
    pub warns: Vec<String>,
    pub stats: Json,
}

/// 真源 `scan` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> CouplingScan {
    let g = graph(root);
    let cyc = cycles(&g.deps);
    let sdp = sdp_violations(&g);
    let base = load_baseline(root);
    let base_present = base.as_ref().map(|b| !crate::pyval::obj_is_empty(b)).unwrap_or(false);

    let mut known_cyc: BTreeSet<Vec<String>> = BTreeSet::new();
    let mut known_sdp: BTreeSet<(String, String)> = BTreeSet::new();
    if base_present {
        let b = base.as_ref().unwrap();
        for c in arr_items(get(b, "cycles")) {
            let mut v: Vec<String> = arr_items(Some(c)).iter().map(|x| plain_str(x)).collect();
            v.sort();
            known_cyc.insert(v);
        }
        // SDP 有**方向**——不排序，按 (依赖方, 被依赖方) 精确比对
        for p in arr_items(get(b, "sdp")) {
            let pair: Vec<String> = arr_items(Some(p)).iter().map(|x| plain_str(x)).collect();
            if pair.len() == 2 {
                known_sdp.insert((pair[0].clone(), pair[1].clone()));
            }
        }
    }

    let mut issues: Vec<String> = Vec::new();
    let mut warns: Vec<String> = Vec::new();
    if !base_present {
        warns.push(format!(
            "无耦合基线 {}（本次按「零容忍」判：修复指引 python scripts/coupling_metrics.py --write 登记存量债）",
            BASELINE_REL
        ));
        known_cyc.clear();
        known_sdp.clear();
    }
    for c in &cyc {
        if !known_cyc.contains(c) {
            let mut chain = c.clone();
            chain.push(c[0].clone());
            issues.push(format!(
                "新增模块级环：{}（修复指引：断开其中一条依赖——常是惰性 import 循环；确属设计债须评审后 python scripts/coupling_metrics.py --write 登记）",
                chain.join(" → ")
            ));
        }
    }
    for (a, b) in &sdp {
        if !known_sdp.contains(&(a.clone(), b.clone())) {
            issues.push(format!(
                "新增 SDP 违例：{}(I={:.2}) 依赖了更不稳的 {}(I={:.2})（修复指引：把依赖反向——让稳定侧定义接口、由不稳侧实现；确属存量债须评审后 --write 登记）",
                a,
                g.i_of.get(a).copied().unwrap_or(0.0),
                b,
                g.i_of.get(b).copied().unwrap_or(0.0)
            ));
        }
    }
    let cur_cyc: BTreeSet<Vec<String>> = cyc.iter().cloned().collect();
    let cur_sdp: BTreeSet<(String, String)> = sdp.iter().cloned().collect();
    for c in known_cyc.difference(&cur_cyc) {
        let mut chain = c.clone();
        chain.push(c[0].clone());
        warns.push(format!(
            "登记环已消除：{}（修复指引：从 {} 的 cycles 移除）",
            chain.join(" → "),
            BASELINE_REL
        ));
    }
    for (a, b) in known_sdp.difference(&cur_sdp) {
        warns.push(format!(
            "登记 SDP 违例已消除：{} → {}（修复指引：从 {} 的 sdp 移除）",
            a, b, BASELINE_REL
        ));
    }

    let stats = Json::Object(vec![
        ("modules".to_string(), Json::Int(g.deps.len() as i64)),
        ("cycles".to_string(), Json::Int(cyc.len() as i64)),
        ("sdp".to_string(), Json::Int(sdp.len() as i64)),
        (
            "registered_cycles".to_string(),
            Json::Int(known_cyc.len() as i64),
        ),
        (
            "registered_sdp".to_string(),
            Json::Int(known_sdp.len() as i64),
        ),
    ]);
    let _ = py_str(None);
    CouplingScan { issues, warns, stats }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn import_extraction_covers_relative_and_parenthesised_forms() {
        let known: BTreeSet<String> = ["a", "b", "c", "d", "e"]
            .iter()
            .map(|s| s.to_string())
            .collect();
        let src = "import core.a\nfrom core import b, c\nfrom . import d\nfrom .core import e\n";
        let got = module_deps(src, "self", &known);
        assert_eq!(
            got,
            ["a", "b", "c", "d", "e"].iter().map(|s| s.to_string()).collect()
        );
    }

    #[test]
    fn parenthesised_multiline_import_is_joined() {
        let known: BTreeSet<String> = ["a", "b"].iter().map(|s| s.to_string()).collect();
        let src = "from core import (\n    a,\n    b,\n)\n";
        assert_eq!(
            module_deps(src, "self", &known),
            ["a", "b"].iter().map(|s| s.to_string()).collect()
        );
    }

    #[test]
    fn self_dependency_is_dropped() {
        let known: BTreeSet<String> = ["self", "other"].iter().map(|s| s.to_string()).collect();
        assert!(module_deps("from core import self", "self", &known).is_empty());
    }
    /// ===== 分支级差分判据（期望值由 `tools/gen_coupling_expected.py` 从真源生成）=====
    ///
    /// 真语料上 `coupling` 只有固定的那几组环/SDP，**import 抽取的各种写法一条也没被单独核过**；
    /// 而本线的抽取是**词法近似**（真源用 `ast`）——正是最该被直接核的地方。
    /// 本夹具逐形态踩：普通 / 多别名 / 点号模块 / 相对无模块 / 相对 core / 相对带模块 /
    /// 括号多行 / 别名 / 字符串与注释里的假 import / `__init__` 忽略。
    const SRC: [(&str, &str); 10] = [
        ("__init__", r#"from core.aa import x
"#),
        ("aa", r#"import core.bb
from core import cc, dd
"#),
        ("bb", r#"from core.aa import x
"#),
        ("cc", r#"from . import ee
"#),
        ("dd", r#"from .core import ff
"#),
        ("ee", r#"from ..pkg.sub import gg
"#),
        ("ff", r#"from core import (hh,
    ii)
"#),
        ("gg", r#"import core.hh as hh
"#),
        ("hh", r#"S = "from core import zzz"
# import core.yyy
"#),
        ("ii", r#"import os
import json
"#),
    ];

    fn build_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("coupling-branches");
        let core = root.join("desktop/src/core");
        std::fs::create_dir_all(&core).unwrap();
        for (name, body) in SRC {
            std::fs::write(core.join(format!("{}.py", name)), body).unwrap();
        }
        root
    }

    #[test]
    fn import_extraction_matches_ast_on_every_form() {
        let root = build_fixture();
        let g = graph(&root);
        let want: Vec<(String, Vec<String>)> = vec![
            ("aa".to_string(), vec!["bb".to_string(), "cc".to_string(), "dd".to_string()]),
            ("bb".to_string(), vec!["aa".to_string()]),
            ("cc".to_string(), vec!["ee".to_string()]),
            ("dd".to_string(), vec!["ff".to_string()]),
            ("ee".to_string(), vec![]),
            ("ff".to_string(), vec!["hh".to_string(), "ii".to_string()]),
            ("gg".to_string(), vec!["hh".to_string()]),
            ("hh".to_string(), vec![]),
            ("ii".to_string(), vec![]),
        ];
        let got: Vec<(String, Vec<String>)> = g
            .deps
            .iter()
            .map(|(k, v)| (k.clone(), v.iter().cloned().collect()))
            .collect();
        assert_eq!(got, want, "同包依赖集合须与真源 AST 版逐条一致");
    }

    #[test]
    fn ca_ce_i_match_the_truth_source() {
        let root = build_fixture();
        let g = graph(&root);
        let want: Vec<(&str, i64, i64, f64)> = vec![
            ("aa", 1, 3, 0.75),
            ("bb", 1, 1, 0.5),
            ("cc", 1, 1, 0.5),
            ("dd", 1, 1, 0.5),
            ("ee", 1, 0, 0.0),
            ("ff", 1, 2, 0.6667),
            ("gg", 0, 1, 1.0),
            ("hh", 2, 0, 0.0),
            ("ii", 1, 0, 0.0),
        ];
        for (m, ca, ce, i) in want {
            assert_eq!(g.ca.get(m).copied().unwrap_or(-1), ca, "Ca 不符：{}", m);
            assert_eq!(g.ce.get(m).copied().unwrap_or(-1), ce, "Ce 不符：{}", m);
            assert_eq!(g.i_of.get(m).copied().unwrap_or(-1.0), i, "I 不符：{}", m);
        }
    }

    #[test]
    fn cycles_and_sdp_match_the_truth_source() {
        let root = build_fixture();
        let g = graph(&root);
        let cyc = cycles(&g.deps);
        let want: Vec<Vec<String>> = vec![
            vec!["aa".to_string(), "bb".to_string()],
        ];
        assert_eq!(cyc, want, "环集合");
        let sdp = sdp_violations(&g);
        let want_sdp: Vec<(String, String)> = vec![
            ("bb".to_string(), "aa".to_string()),
            ("dd".to_string(), "ff".to_string()),
        ];
        assert_eq!(sdp, want_sdp, "SDP 违例（有方向，不排序）");
    }

    #[test]
    fn scan_reports_both_cycle_and_sdp_with_exact_wording() {
        let root = build_fixture();
        let got = scan(&root);
        assert_eq!(got.issues.len(), 3, "1 个环 + 2 处 SDP：{:?}", got.issues);
        assert!(got.issues[0].starts_with("新增模块级环：aa → bb → aa（"), "{:?}", got.issues[0]);
        assert!(got.issues[1].starts_with("新增 SDP 违例：bb(I=0.50) 依赖了更不稳的 aa(I=0.75)（"), "{:?}", got.issues[1]);
        assert!(got.issues[2].starts_with("新增 SDP 违例：dd(I=0.50) 依赖了更不稳的 ff(I=0.67)（"), "{:?}", got.issues[2]);
        assert_eq!(got.warns.len(), 1);
        assert!(got.warns[0].starts_with("无耦合基线 protocol/coupling_baseline.json"), "{:?}", got.warns[0]);
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "cycles": 1, "modules": 9, "registered_cycles": 0,
                "registered_sdp": 0, "sdp": 2
            }))
            .unwrap()
        ));
    }

}
