//! 模块 I/O 类型面（`io-types`）—— 与真源 `desktop/src/core/io_types.py` 的 `scan` / `coverage` 对账。
//!
//! NF 的 `inputs`/`outputs` 一直是**裸字符串**：能查"谁连谁"，查不了"连的是什么类型"。本模块给机读
//! 契约加一层**可选类型面**，并给出**可证**的类型检查——只判可证的不匹配，不给未收窄的字段编类型。
//!
//! 四种结论的落点：可证不匹配 / 越词表 = **FAIL**；未收窄（`untyped`）/ 无机读契约（L0）= **WARN**。
//!
//! **移植面按消费者界定**：真源的 `apply` / `inject` / `render_io_types` 是**写面**（就地编辑源件），
//! 契约 `_c_io_types` 只读 `scan` + `coverage`，故不移植。
//!
//! 真源 `coverage` 内部**再跑一遍 `scan`**；本线一次扫描供两处用（纯函数，结论同）。

use crate::miniyaml;
use crate::pyjson::Json;
use crate::pyval::{get, py_str};
use std::collections::BTreeMap;
use std::path::Path;

pub const KINDS: [&str; 9] = [
    "string", "integer", "number", "boolean", "array", "object", "event", "state", "untyped",
];

fn io_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^(\s*)io_types:\s*$").expect("io 正则固定合法"))
}

fn sub_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"^(\s*)(outputs|inputs):\s*(\{\})?\s*$").expect("段正则固定合法")
    })
}

/// 键**允许冒号**（跨包依赖键写作 `AI保险:M01`）——旧模式 `[^:\s]+` 会把这类键整条读不出来，
/// 于是「写出去的键读不回来」。非贪婪键 + 锚定行尾：`AI保险:M01: untyped` 切成 键/值 两段。
fn pair_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^(\s*)(\S+?):\s*(\S+)\s*$").expect("键值正则固定合法"))
}

/// 真源 `parse_io_types`：从 `machine_contract` 围栏里读 `io_types`（行式解析；无则 `None`）。
pub fn parse_io_types(text: &str) -> Option<Json> {
    let lines: Vec<&str> = text.lines().collect();
    let mut start = None;
    let mut base = 0usize;
    for (i, ln) in lines.iter().enumerate() {
        if let Some(c) = io_re().captures(ln) {
            start = Some(i);
            base = c[1].chars().count();
            break;
        }
    }
    let start = start?;
    let mut outputs: Vec<(String, Json)> = Vec::new();
    let mut inputs: Vec<(String, Json)> = Vec::new();
    let mut sub: Option<String> = None;
    for ln in &lines[start + 1..] {
        if ln.trim().is_empty() {
            continue;
        }
        let indent = ln.chars().take_while(|c| *c == ' ').count();
        if indent <= base {
            break;
        }
        if let Some(sm) = sub_re().captures(ln) {
            let name = sm[2].to_string();
            if sm.get(3).is_some() {
                // `outputs: {}` / `inputs: {}` —— 显式空段
                match name.as_str() {
                    "outputs" => outputs.clear(),
                    _ => inputs.clear(),
                }
            }
            sub = Some(name);
            continue;
        }
        if let Some(pm) = pair_re().captures(ln) {
            let key = pm[2].trim().trim_matches(|c| c == '\'' || c == '"').to_string();
            let val = Json::Str(pm[3].to_string());
            match sub.as_deref() {
                Some("outputs") => {
                    if let Some(slot) = outputs.iter_mut().find(|(k, _)| *k == key) {
                        slot.1 = val;
                    } else {
                        outputs.push((key, val));
                    }
                }
                Some("inputs") => {
                    if let Some(slot) = inputs.iter_mut().find(|(k, _)| *k == key) {
                        slot.1 = val;
                    } else {
                        inputs.push((key, val));
                    }
                }
                _ => {}
            }
        }
    }
    Some(Json::Object(vec![
        ("outputs".to_string(), Json::Object(outputs)),
        ("inputs".to_string(), Json::Object(inputs)),
    ]))
}

fn str_list(j: Option<&Json>) -> Vec<String> {
    match j {
        Some(Json::Array(a)) => a.iter().map(|v| crate::pyval::plain_str(v)).collect(),
        _ => Vec::new(),
    }
}

fn keys_of(j: &Json) -> Vec<String> {
    match j {
        Json::Object(p) => p.iter().map(|(k, _)| k.clone()).collect(),
        _ => Vec::new(),
    }
}

pub struct IoTypesScan {
    pub issues: Vec<String>,
    pub stats: Json,
    /// 真源 `scan` 的 warns：**契约 `_c_io_types` 不消费**（只看 issues），但其中含**实质判据**
    /// ——`io_types.outputs`/`inputs` 与 `machine_contract` 的**键集对齐**、未标 `io_types`、L0 件
    /// 明细。删掉会让这些判据变成"没人核的代码"，故**保留**并由
    /// `tools/gen_io_types_branches.py` 的分支级判据覆盖；这里的 `allow` 只针对"成品二进制里无读者"。
    #[allow(dead_code)]
    pub warns: Vec<String>,
}

/// 真源 `scan`。
pub fn scan(root: &Path) -> IoTypesScan {
    let mut issues: Vec<String> = Vec::new();
    let mut warns: Vec<String> = Vec::new();
    let mut typed = 0i64;
    let mut untyped = 0i64;
    let mut provided: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut l0: Vec<String> = Vec::new();
    let mut rows = 0usize;

    // 先收一遍模块（含文本与 mc），供两轮循环复用
    let mut mods: Vec<(String, String, Json)> = Vec::new();
    for rel in crate::module_signature::module_docs(root) {
        rows += 1;
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
            mods.push((rel, String::new(), Json::Object(Vec::new())));
            continue;
        };
        let mc = miniyaml::fence_yaml(&text, "machine_contract")
            .and_then(|p| get(&p, "machine_contract").cloned())
            .unwrap_or(Json::Null);
        let mc = if matches!(mc, Json::Null) { Json::Object(Vec::new()) } else { mc };
        mods.push((rel, text, mc));
    }

    for (rel, text, mc) in &mods {
        let mid = py_str(get(mc, "id"));
        if mid.is_empty() {
            l0.push(rel.clone());
            continue;
        }
        let Some(io) = parse_io_types(text) else {
            warns.push(format!("{} 未标 io_types（修复指引：nf module types --write）", mid));
            continue;
        };
        for sec in ["outputs", "inputs"] {
            let Some(Json::Object(pairs)) = get(&io, sec) else { continue };
            for (key, kind) in pairs.clone() {
                let kind = py_str(Some(&kind));
                if !KINDS.contains(&kind.as_str()) {
                    issues.push(format!(
                        "{} io_types.{}.{} 类型越词表：{}（{}）",
                        mid,
                        sec,
                        key,
                        kind,
                        KINDS.join("/")
                    ));
                }
                if kind == "untyped" {
                    untyped += 1;
                } else {
                    typed += 1;
                }
            }
        }
        let declared: Vec<String> = str_list(get(mc, "outputs"));
        let marked = keys_of(get(&io, "outputs").unwrap_or(&Json::Null));
        if !same_set(&declared, &marked) {
            warns.push(format!(
                "{} io_types.outputs 与 outputs 键集不一致（缺 {} / 多 {}）",
                mid,
                py_sorted_list(&minus(&declared, &marked)),
                py_sorted_list(&minus(&marked, &declared))
            ));
        }
        let declared_in: Vec<String> = str_list(get(mc, "inputs"));
        let marked_in = keys_of(get(&io, "inputs").unwrap_or(&Json::Null));
        if !same_set(&declared_in, &marked_in) {
            warns.push(format!(
                "{} io_types.inputs 与 inputs 键集不一致（缺 {} / 多 {}）",
                mid,
                py_sorted_list(&minus(&declared_in, &marked_in)),
                py_sorted_list(&minus(&marked_in, &declared_in))
            ));
        }
        provided.insert(mid, keys_values(get(&io, "outputs").unwrap_or(&Json::Null)));
    }

    // 可证不匹配：消费方声明期望类型，提供方有类型声明但无一匹配
    for (_rel, text, mc) in &mods {
        let mid = py_str(get(mc, "id"));
        if mid.is_empty() {
            continue;
        }
        let Some(io) = parse_io_types(text) else { continue };
        let Some(Json::Object(ins)) = get(&io, "inputs") else { continue };
        for (dep, want) in ins {
            let want = py_str(Some(want));
            if want == "untyped" || want == "state" {
                continue;
            }
            if let Some(got) = provided.get(dep) {
                if !got.is_empty() && !got.iter().any(|g| *g == want) {
                    let mut uniq: Vec<String> = got.clone();
                    uniq.sort();
                    uniq.dedup();
                    issues.push(format!(
                        "类型不匹配：{} 期望 {} 提供 {}，但 {} 声明输出类型为 {}（修复指引：对齐 io_types 或改依赖）",
                        mid,
                        dep,
                        want,
                        dep,
                        py_sorted_list(&uniq)
                    ));
                }
            }
        }
    }

    let modules_with_contract = rows - l0.len();
    if !l0.is_empty() {
        warns.push(format!(
            "无机读契约（L0，无法承载 io_types）共 {} 件：{}",
            l0.len(),
            l0.iter().take(3).cloned().collect::<Vec<_>>().join("、")
        ));
    }
    let stats = Json::Object(vec![
        ("modules_with_contract".to_string(), Json::Int(modules_with_contract as i64)),
        ("l0_modules".to_string(), Json::Int(l0.len() as i64)),
        ("typed_fields".to_string(), Json::Int(typed)),
        ("untyped_fields".to_string(), Json::Int(untyped)),
    ]);
    IoTypesScan { issues, warns, stats }
}

/// 真源 `coverage`：`stats` 再加 `coverage`（百分比，一位小数）。
pub fn coverage(root: &Path) -> (IoTypesScan, f64) {
    let s = scan(root);
    let typed = match get(&s.stats, "typed_fields") {
        Some(Json::Int(n)) => *n,
        _ => 0,
    };
    let untyped = match get(&s.stats, "untyped_fields") {
        Some(Json::Int(n)) => *n,
        _ => 0,
    };
    let total = typed + untyped;
    let cov = if total != 0 {
        crate::pyfloat::round_to(100.0 * typed as f64 / total as f64, 1)
    } else {
        0.0
    };
    (s, cov)
}

// ---------------------------------------------------------------- 小工具

fn same_set(a: &[String], b: &[String]) -> bool {
    let sa: std::collections::BTreeSet<&String> = a.iter().collect();
    let sb: std::collections::BTreeSet<&String> = b.iter().collect();
    sa == sb
}

fn minus(a: &[String], b: &[String]) -> Vec<String> {
    let sb: std::collections::BTreeSet<&String> = b.iter().collect();
    a.iter().filter(|x| !sb.contains(x)).cloned().collect()
}

/// Python `sorted(list)` 的 `%s` 形态：`['a', 'b']`。
fn py_sorted_list(v: &[String]) -> String {
    let mut s: Vec<String> = v.to_vec();
    s.sort();
    format!(
        "[{}]",
        s.iter().map(|x| format!("'{}'", x)).collect::<Vec<_>>().join(", ")
    )
}

/// `io_types.outputs` 的值集（供「提供方有类型声明」比对）。
fn keys_values(j: &Json) -> Vec<String> {
    match j {
        Json::Object(p) => p.iter().map(|(_, v)| py_str(Some(v))).collect(),
        _ => Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_io_types_branches.py（勿手改；重跑生成器覆盖本段）
    /// ===== 分支级差分判据（期望值由 `tools/gen_io_types_branches.py` 从真源生成）=====
    ///
    /// 契约只看 issues + coverage，**warns 无消费者**——而 warns 里含实质判据（键集对齐、未标、L0），
    /// 故本判据**两侧都比**（warns 正是靠这里才不是"没人核的代码"）。
    /// 分支：L0 件 / 未标 io_types / 类型越词表 / 输出键集不一致 / 输入键集不一致 /
    /// 类型不匹配（提供方有声明但无一匹配）/ `state` 与 `untyped` 跳过 / 含冒号的跨包键 /
    /// 显式空段 `outputs: {}` / 全绿。
    const IOT_MODS: [(&str, &str); 7] = [
        ("M90-l0.md", r#"# 无契约
正文
"#),
        ("M91-unmarked.md", r#"```yaml
machine_contract:
  id: M91
  outputs: [a]
```
"#),
        ("M92-badkind.md", r#"```yaml
machine_contract:
  id: M92
  outputs: [a]
  inputs: [x]
  io_types:
    outputs:
      b: 不存在的类型
      c: untyped
    inputs:
      y: untyped
```
"#),
        ("M93-provider.md", r#"```yaml
machine_contract:
  id: M93
  outputs: [foo]
  io_types:
    outputs:
      foo: number
```
"#),
        ("M94-consumer.md", r#"```yaml
machine_contract:
  id: M94
  inputs: [M93, M95, M96]
  io_types:
    outputs: {}
    inputs:
      M93: string
      M95: state
      M96: untyped
```
"#),
        ("M95-colonkey.md", r#"```yaml
machine_contract:
  id: M95
  outputs: []
  io_types:
    outputs: {}
    inputs:
      'AI保险:M01': untyped
```
"#),
        ("M96-green.md", r#"```yaml
machine_contract:
  id: M96
  outputs: [g]
  outputs: [g]
  io_types:
    outputs:
      g: event
    inputs: {}
```
"#),
    ];

    fn build_io_types_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("io-types-branches");
        let dir = root.join("04_模块库/通用类");
        std::fs::create_dir_all(&dir).unwrap();
        for (name, body) in IOT_MODS {
            std::fs::write(dir.join(name), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_on_both_sides() {
        let root = build_io_types_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, &["M92 io_types.outputs.b 类型越词表：不存在的类型（string/integer/number/boolean/array/object/event/state/untyped）", "类型不匹配：M94 期望 M93 提供 string，但 M93 声明输出类型为 ['number']（修复指引：对齐 io_types 或改依赖）"] as &[&str], "issues 须逐字且同序");
        assert_eq!(got.warns, &["M91 未标 io_types（修复指引：nf module types --write）", "M92 io_types.outputs 与 outputs 键集不一致（缺 ['a'] / 多 ['b', 'c']）", "M92 io_types.inputs 与 inputs 键集不一致（缺 ['x'] / 多 ['y']）", "M95 io_types.inputs 与 inputs 键集不一致（缺 [] / 多 ['AI保险:M01']）", "无机读契约（L0，无法承载 io_types）共 1 件：04_模块库/通用类/M90-l0.md"] as &[&str], "warns 须逐字且同序");
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "modules_with_contract": 6, "l0_modules": 1,
                "typed_fields": 5, "untyped_fields": 4
            }))
            .unwrap()
        ));
    }

    #[test]
    fn coverage_matches_the_truth_source() {
        let root = build_io_types_fixture();
        let (_s, cov) = coverage(&root);
        assert_eq!(cov, 55.6, "覆盖率（一位小数、正确舍入）");
    }
    // <<< GENERATED
}
