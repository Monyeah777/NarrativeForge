//! 代码规模与复杂度上限（棘轮冻结）—— 与真源 `desktop/src/core/code_metrics.py` 的 `scan` 对账。
//!
//! 口径（真源）：`lines` = `len(text.splitlines())`；`max_fn_lines` = 函数体行数最大值；
//! `max_fn_cc` = 函数圈复杂度最大值（McCabe 口径：`1 + 判定点数`，其中
//! `if/for/while/except/with/assert/三元/布尔运算` 各计 1，布尔每多一个操作数再加 1）。
//!
//! **不移植写面**：真源的 `write()`（冻结基线）是显式写动作，按目标纪律不碰。
//!
//! 两处顺序/口径陷阱（都影响逐字节对账）：
//!
//! 1. **`worst_fn` 取严格大于** ⇒ 并列时"谁先被 `ast.walk` 到"决定结果。`ast.walk` 是 **BFS**，
//!    故本线用 (深度, 前序) 还原 BFS 序（见 `pyast::metric_facts`）。
//! 2. **`lines` 走 Python 的 `splitlines()`**（`\v` / `\f` / `\x85` / `\u2028` 等也断行），
//!    不是 Rust 的 `lines()`——见 `pyval::splitlines_count`。
//!
//! **已知偏差**：语法坏时真源记 CPython 的 `SyntaxError` 文本，本线只能给**本线解析器**的
//! 错误文本。二者不同形（真语料上该分支不触发；已由分支夹具钉住"该分支会报 FAIL"这一行为，
//! 但**文本**不可比）。

use crate::pyjson::Json;
use crate::pyval;
use std::path::Path;

pub const BASELINE_REL: &str = "protocol/code_metrics_baseline.json";

/// 新增文件的绝对上限（存量按基线冻结，不受此限）。
const LIMITS: [(&str, i64); 3] = [("lines", 800), ("max_fn_lines", 120), ("max_fn_cc", 25)];
/// 扫描面：core 与 scripts 的 `.py`（与 purity R5/R6 同口径）。
pub const SCAN_DIRS: [&str; 2] = ["desktop/src/core", "scripts"];
/// 三项度量的（键, 中文标签），顺序即真源的遍历顺序。
const KEYS: [(&str, &str); 3] =
    [("lines", "模块行数"), ("max_fn_lines", "最长函数行数"), ("max_fn_cc", "最大圈复杂度")];

#[derive(Clone, Debug, Default)]
pub struct Metrics {
    pub lines: i64,
    pub max_fn_lines: i64,
    pub max_fn_cc: i64,
    pub worst_fn: String,
    pub syntax_error: Option<String>,
}

pub fn metrics_of(path: &Path) -> Metrics {
    // 真源用 `errors="replace"` 读 ⇒ 非法字节换成 U+FFFD
    let raw = std::fs::read(path).unwrap_or_default();
    let text = String::from_utf8_lossy(&raw).into_owned();
    let mut out = Metrics { lines: pyval::splitlines_count(&text) as i64, ..Default::default() };
    let Some(facts) = crate::pyast::metric_facts(&text) else {
        out.syntax_error = Some(
            "语法不可解析（修复指引：先修语法，度量需要可解析的 AST）".to_string(),
        );
        return out;
    };
    for f in &facts.fns {
        let ln = f.end_lineno as i64 - f.lineno as i64 + 1;
        if ln > out.max_fn_lines {
            out.max_fn_lines = ln;
        }
        // 真源 `if cc > out["max_fn_cc"]`：**严格大于** ⇒ 并列时先到者赢
        if f.cc > out.max_fn_cc {
            out.max_fn_cc = f.cc;
            out.worst_fn = format!("{}（{} 行 / cc={}）", f.name, ln, f.cc);
        }
    }
    out
}

/// 全量度量 → 按仓库相对路径排序的 `(rel, 度量)`。
pub fn measure(root: &Path) -> Vec<(String, Metrics)> {
    let mut out: Vec<(String, Metrics)> = Vec::new();
    for d in SCAN_DIRS {
        let dir = root.join(d);
        let Ok(rd) = std::fs::read_dir(&dir) else { continue };
        let mut names: Vec<String> = rd
            .flatten()
            .map(|e| e.file_name().to_string_lossy().to_string())
            .filter(|n| n.ends_with(".py"))
            .collect();
        names.sort();
        for n in names {
            let rel = format!("{}/{}", d, n);
            let m = metrics_of(&root.join(&rel));
            out.push((rel, m));
        }
    }
    out
}

/// 真源 `load_baseline`：`doc["files"] or {}`；缺件/坏件 → 空。
pub fn load_baseline(root: &Path) -> Vec<(String, Vec<(String, i64)>)> {
    let p = root.join(BASELINE_REL);
    if !p.is_file() {
        return Vec::new();
    }
    let Ok(text) = std::fs::read_to_string(&p) else { return Vec::new() };
    let Ok(v) = serde_json::from_str::<serde_json::Value>(&text) else { return Vec::new() };
    let Ok(doc) = crate::jsonread::convert(&v) else { return Vec::new() };
    let Json::Object(o) = &doc else { return Vec::new() };
    let Some((_, Json::Object(files))) = o.iter().find(|(k, _)| k == "files") else {
        return Vec::new();
    };
    let mut out = Vec::new();
    for (rel, v) in files {
        let mut kv = Vec::new();
        if let Json::Object(m) = v {
            for (k, _) in KEYS {
                let got = m
                    .iter()
                    .find(|(kk, _)| kk == k)
                    .map(|(_, vv)| pyval::py_int_or(Some(vv), 0))
                    .unwrap_or(0);
                kv.push((k.to_string(), got));
            }
        }
        out.push((rel.clone(), kv));
    }
    out
}

/// 真源 `scan` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, Vec<String>, Json) {
    let cur = measure(root);
    let base = load_baseline(root);
    let mut issues: Vec<String> = Vec::new();
    let mut warns: Vec<String> = Vec::new();
    let mut sorted: Vec<&(String, Metrics)> = cur.iter().collect();
    sorted.sort_by(|a, b| a.0.cmp(&b.0));
    for (rel, m) in &sorted {
        if let Some(se) = &m.syntax_error {
            issues.push(format!("{} {}", rel, se));
            continue;
        }
        match base.iter().find(|(r, _)| r == rel) {
            Some((_, kv)) => {
                for (key, label) in KEYS {
                    let cap = kv
                        .iter()
                        .find(|(k, _)| *k == key)
                        .map(|(_, v)| *v)
                        .unwrap_or(0);
                    let val = match key {
                        "lines" => m.lines,
                        "max_fn_lines" => m.max_fn_lines,
                        _ => m.max_fn_cc,
                    };
                    if cap != 0 && val > cap {
                        issues.push(format!(
                            "{} {} {} > 冻结值 {}（修复指引：拆分该模块/函数；确需上调须评审后重冻基线 python scripts/code_metrics.py --write）",
                            rel, label, val, cap
                        ));
                    }
                }
            }
            None => {
                for (key, label) in KEYS {
                    let lim = LIMITS.iter().find(|(k, _)| *k == key).map(|(_, v)| *v).unwrap_or(0);
                    let val = match key {
                        "lines" => m.lines,
                        "max_fn_lines" => m.max_fn_lines,
                        _ => m.max_fn_cc,
                    };
                    if val > lim {
                        issues.push(format!(
                            "{} 新文件 {} {} > 限值 {}（修复指引：拆分后再入库；确需放宽须评审后冻结基线）",
                            rel, label, val, lim
                        ));
                    }
                }
            }
        }
    }
    let max_of = |f: fn(&Metrics) -> i64| -> i64 {
        cur.iter().map(|(_, m)| f(m)).max().unwrap_or(0)
    };
    if base.is_empty() {
        warns.push(format!(
            "无基线 {}（当前按新文件限值判；修复指引：python scripts/code_metrics.py --write 冻结存量）",
            BASELINE_REL
        ));
    }
    let stats = Json::Object(vec![
        ("files".to_string(), Json::Int(cur.len() as i64)),
        ("baseline".to_string(), Json::Int(base.len() as i64)),
        ("max_lines".to_string(), Json::Int(max_of(|m| m.lines))),
        ("max_fn_lines".to_string(), Json::Int(max_of(|m| m.max_fn_lines))),
        ("max_fn_cc".to_string(), Json::Int(max_of(|m| m.max_fn_cc))),
    ]);
    (issues, warns, stats)
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_code_metrics_branches.py（勿手改；重跑生成器覆盖本段）
    /// ===== 分支级差分判据（期望值由 `tools/gen_code_metrics_branches.py` 从真源生成）=====
    ///
    /// 真语料上该判据 **0 issue** ⇒ 三支全未踩到。本夹具逐支踩：冻结值超标（三键各一支）/
    /// 新文件超限（同样三键）/ 语法坏 / 基线里 `cap=0` 的短路支 / 基线内未超标 /
    /// 缺基线的 WARN 支（单独用例）。
    ///
    /// **语法坏那一支的文本不可比**（真源给 CPython `SyntaxError` 文本，本线给本线解析器的），
    /// 故两侧都归一到 `<rel> <SYNTAX>` 后比较——**不假装文本相同**。
    const CM_BASELINE: &str = r#"{
  "files": {
    "desktop/src/core/zz_big.py": {
      "lines": 1,
      "max_fn_cc": 3,
      "max_fn_lines": 2
    },
    "scripts/zz_ok.py": {
      "lines": 9999,
      "max_fn_cc": 9999,
      "max_fn_lines": 9999
    },
    "scripts/zz_zero_cap.py": {
      "lines": 0,
      "max_fn_cc": 9999,
      "max_fn_lines": 9999
    }
  },
  "limits": {
    "lines": 800,
    "max_fn_cc": 25,
    "max_fn_lines": 120
  },
  "schema": "nf-code-metrics/1"
}
"#;
    const CM_BIGFUNC_PREFIX: &str = "def big():\n";
    const CM_BIGFUNC_BODY: &str = r#"    if x == 0:
        pass
"#;
    const CM_OK: &str = "z = 1\n";
    const CM_SYNTAX: &str = r#"def f(:
    pass
"#;
    const CM_SYN_REL: &str = "scripts/zz_syntax.py";

    fn cm_bigfunc() -> String {
        let mut s = String::from(CM_BIGFUNC_PREFIX);
        for i in 0..31 {
            s.push_str(&format!("    if x == {}:\n        pass\n", i));
        }
        s
    }

    fn build_code_metrics_fixture(with_baseline: bool) -> std::path::PathBuf {
        let name = if with_baseline { "code-metrics-branches" } else { "code-metrics-nobase" };
        let root = crate::testutil::fixture(name);
        let write = |rel: &str, body: &str| {
            let p = root.join(rel);
            std::fs::create_dir_all(p.parent().unwrap()).unwrap();
            std::fs::write(p, body).unwrap();
        };
        if with_baseline {
            write("desktop/src/core/zz_big.py", &cm_bigfunc());
            write("scripts/zz_new_long.py", &"x = 1\n".repeat(801));
            write("scripts/zz_new_bigfunc.py", &cm_bigfunc());
        }
        if with_baseline {
            write("scripts/zz_syntax.py", CM_SYNTAX);
            write("scripts/zz_zero_cap.py", "y = 1\n");
        }
        write("scripts/zz_ok.py", CM_OK);
        if with_baseline {
            write("protocol/code_metrics_baseline.json", CM_BASELINE);
        }
        root
    }

    fn cm_norm(issues: &[String]) -> Vec<String> {
        issues
            .iter()
            .map(|x| {
                if x.starts_with(&format!("{} ", CM_SYN_REL)) {
                    format!("{} <SYNTAX>", CM_SYN_REL)
                } else {
                    x.clone()
                }
            })
            .collect()
    }

    #[test]
    fn code_metrics_matches_truth_source_branch_by_branch() {
        let root = build_code_metrics_fixture(true);
        let (issues, warns, stats) = scan(&root);
        assert_eq!(cm_norm(&issues), &[r#"desktop/src/core/zz_big.py 模块行数 63 > 冻结值 1（修复指引：拆分该模块/函数；确需上调须评审后重冻基线 python scripts/code_metrics.py --write）"#, r#"desktop/src/core/zz_big.py 最长函数行数 63 > 冻结值 2（修复指引：拆分该模块/函数；确需上调须评审后重冻基线 python scripts/code_metrics.py --write）"#, r#"desktop/src/core/zz_big.py 最大圈复杂度 32 > 冻结值 3（修复指引：拆分该模块/函数；确需上调须评审后重冻基线 python scripts/code_metrics.py --write）"#, r#"scripts/zz_new_bigfunc.py 新文件 最大圈复杂度 32 > 限值 25（修复指引：拆分后再入库；确需放宽须评审后冻结基线）"#, r#"scripts/zz_new_long.py 新文件 模块行数 801 > 限值 800（修复指引：拆分后再入库；确需放宽须评审后冻结基线）"#, r#"scripts/zz_syntax.py <SYNTAX>"#] as &[&str], "issues 须逐字且同序（语法支已归一）");
        assert_eq!(warns, &[] as &[&str], "warns 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"baseline": 3, "files": 6, "max_fn_cc": 32, "max_fn_lines": 63, "max_lines": 801}"#).unwrap(),
        )
        .unwrap();
        assert!(
            crate::jsonread::json_eq(&stats, &want),
            "stats 不一致\n  实得 {}\n  期望 {}",
            stats.dumps(),
            want.dumps()
        );
    }

    #[test]
    fn code_metrics_without_baseline_warns() {
        let root = build_code_metrics_fixture(false);
        let (issues, warns, _stats) = scan(&root);
        assert!(issues.is_empty(), "缺基线不该产生 issue：{:?}", issues);
        assert_eq!(warns, &[r#"无基线 protocol/code_metrics_baseline.json（当前按新文件限值判；修复指引：python scripts/code_metrics.py --write 冻结存量）"#] as &[&str]);
    }
    // <<< GENERATED
}
