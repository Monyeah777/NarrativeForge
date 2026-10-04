//! 概念图资产体检 —— 与真源 `desktop/src/core/concept_graph.py` 的 `scan` 对账。
//!
//! **移植面按消费者界定**：只移植门禁判据面（`graph_assets` / `load_graph` / `prereqs_of` /
//! `problems` 及其依赖）。真源里 `resolve` / `closure` / `missing` / `frontier` / `violations`
//! / `node_meta` 是给**求值器工具**（`scripts/ai_domain_closure.py`）用的，不是判据面 ⇒ 不移植
//! （不写没人核的代码）。
//!
//! 判据：结构（id 唯一 / 层位 ∈ P00–P80 / 必备 `name` / 边带 provenance 且键在图例中）+
//! 图论（无环 / 前置无悬空 / 无自环）+ 别名唯一 + 分支完备 + 证据强度声明与**覆盖实况**自洽。
//!
//! **一处口径说明**：真源别名键用 `str.casefold()`，本线用 `to_lowercase()`。二者在 ASCII 与
//! CJK 上一致，差异只在 `ß`/终结 sigma 这类特殊折叠（本仓资产无此）——若将来出现，对账会红。

use crate::pyjson::Json;
use crate::pyval;
use std::path::Path;

pub const BLOCK_MARKER: &str = "concept_graph";
pub const LAYERS: [&str; 9] =
    ["P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80"];
/// 真源 `SHELF_GLOBS`（资产货架，单层）。
pub const SHELF_GLOBS: [&str; 2] = ["community/*/assets/*.md", "05_资产库/用户自定义/*.md"];
const PROVENANCE_STRENGTHS: [&str; 4] = ["external", "mixed", "domain-logic", "inferred"];
const NON_SOURCE_KEYS: [&str; 2] = ["inferred", "domain-logic"];

fn obj_get<'a>(v: &'a Json, k: &str) -> Option<&'a Json> {
    match v {
        Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv),
        _ => None,
    }
}

fn arr_of(v: Option<&Json>) -> Vec<Json> {
    match v {
        Some(Json::Array(a)) => a.clone(),
        _ => Vec::new(),
    }
}

fn s(v: &Json) -> String {
    pyval::plain_str(v)
}

/// 真源 `fenced_block`：取含 marker 的 ```yaml 围栏**正文**（无则空串）。
pub fn fenced_block(text: &str, marker: &str) -> String {
    // `(?ms)^```yaml\s*\n(.*?)^```` 的等价物
    let mut idx = 0usize;
    let lines: Vec<&str> = text.split('\n').collect();
    while idx < lines.len() {
        if lines[idx].trim_end() == "```yaml" {
            let start = idx + 1;
            let mut end = start;
            while end < lines.len() && lines[end].trim_end() != "```" {
                end += 1;
            }
            if end <= lines.len() {
                let body = lines[start..end].join("\n");
                if has_marker(&body, marker) {
                    return body;
                }
                idx = end + 1;
                continue;
            }
        }
        idx += 1;
    }
    String::new()
}

/// 真源 `re.search(r"(?m)^%s\s*:" % escape(marker), body)`。
fn has_marker(body: &str, marker: &str) -> bool {
    body.split('\n').any(|l| {
        l.strip_prefix(marker)
            .map(|rest| rest.trim_start().starts_with(':'))
            .unwrap_or(false)
    })
}

/// 真源 `load_graph`：读资产 → `concept_graph` 字典；失败即 `Err(原因)`（对应 `ClosureError`）。
pub fn load_graph(root: &Path, rel: &str) -> Result<Json, String> {
    let path = root.join(rel);
    if !path.is_file() {
        return Err(format!(
            "概念图资产不存在：{}（修复指引：给出域包内 assets/CONCEPT_GRAPH.md 路径）",
            path.display()
        ));
    }
    let text = std::fs::read(&path)
        .map(|b| String::from_utf8_lossy(&b).into_owned())
        .unwrap_or_default();
    let body = fenced_block(&text, BLOCK_MARKER);
    if body.is_empty() {
        return Err(format!(
            "资产缺 `{}:` 机器可读块：{}（修复指引：补 ```yaml 围栏块，块内首键为 {}）",
            BLOCK_MARKER,
            path.display(),
            BLOCK_MARKER
        ));
    }
    let data = crate::miniyaml::parse(&body)?;
    match obj_get(&data, BLOCK_MARKER) {
        Some(g @ Json::Object(_)) => Ok(g.clone()),
        _ => Err(format!(
            "机读块结构非法：{}（修复指引：顶层键须为 {}）",
            path.display(),
            BLOCK_MARKER
        )),
    }
}

/// 真源 `graph_assets`：仓库内带概念图机读块的资产（相对路径，排序）。
pub fn graph_assets(root: &Path) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for pat in SHELF_GLOBS {
        let mut hits = crate::glob::expand(root, pat);
        hits.sort();
        for f in hits {
            let text = std::fs::read(root.join(&f))
                .map(|b| String::from_utf8_lossy(&b).into_owned())
                .unwrap_or_default();
            if !fenced_block(&text, BLOCK_MARKER).is_empty() {
                out.push(f);
            }
        }
    }
    out
}

/// 真源 `prereqs_of`：`{概念 id: 直接前置 id 列表}`（保持声明序，去重）。
pub fn prereqs_of(graph: &Json) -> Vec<(String, Vec<String>)> {
    let mut out: Vec<(String, Vec<String>)> = Vec::new();
    for node in arr_of(obj_get(graph, "nodes")) {
        let Json::Object(_) = &node else { continue };
        let id = match obj_get(&node, "id") {
            Some(v) if pyval::py_truthy(v) => s(v),
            _ => continue,
        };
        let mut seen: Vec<String> = Vec::new();
        for p in arr_of(obj_get(&node, "prereqs")) {
            let ps = s(&p);
            if !seen.contains(&ps) {
                seen.push(ps);
            }
        }
        out.push((id, seen));
    }
    out
}

/// 真源 `branch_map`：`{分支 id: [概念 id]}`（保持声明序）。
pub fn branch_map(graph: &Json) -> Vec<(String, Vec<String>)> {
    let mut out: Vec<(String, Vec<String>)> = Vec::new();
    for br in arr_of(obj_get(graph, "branches")) {
        let Json::Object(_) = &br else { continue };
        if let Some(id) = obj_get(&br, "id") {
            if pyval::py_truthy(id) {
                out.push((
                    s(id),
                    arr_of(obj_get(&br, "nodes")).iter().map(s).collect(),
                ));
            }
        }
    }
    out
}

/// 真源 `node_branch`：`{概念 id: 分支 id}`（首次出现者胜）。
pub fn node_branch(graph: &Json) -> Vec<(String, String)> {
    let mut out: Vec<(String, String)> = Vec::new();
    for (bid, nodes) in branch_map(graph) {
        for nid in nodes {
            if !out.iter().any(|(k, _)| *k == nid) {
                out.push((nid, bid.clone()));
            }
        }
    }
    out
}

/// 真源 `alias_map`：`{别名(casefold): 概念 id}`；重复即 `Err`。
pub fn alias_map(graph: &Json) -> Result<Vec<(String, String)>, String> {
    let mut out: Vec<(String, String)> = Vec::new();
    for node in arr_of(obj_get(graph, "nodes")) {
        let Json::Object(_) = &node else { continue };
        let id = match obj_get(&node, "id") {
            Some(v) if pyval::py_truthy(v) => s(v),
            _ => continue,
        };
        for raw in arr_of(obj_get(&node, "aliases")) {
            let key = s(&raw).trim().to_lowercase();
            if key.is_empty() {
                continue;
            }
            if let Some((_, prev)) = out.iter().find(|(k, _)| *k == key) {
                if *prev != id {
                    return Err(format!(
                        "别名重复：{} 同时指向 {} 与 {}（修复指引：别名在图内须唯一——与 01 §1.1 词法纪律同源）",
                        pyval::py_repr(&Json::Str(s(&raw))),
                        prev,
                        id
                    ));
                }
            }
            match out.iter_mut().find(|(k, _)| *k == key) {
                Some(e) => e.1 = id.clone(),
                None => out.push((key, id.clone())),
            }
        }
    }
    Ok(out)
}

/// 真源 `external_coverage` → (有外部来源锚的节点数, 包内节点总数)。
pub fn external_coverage(graph: &Json) -> (i64, i64) {
    let (mut total, mut covered) = (0i64, 0i64);
    for node in arr_of(obj_get(graph, "nodes")) {
        let Json::Object(_) = &node else { continue };
        match obj_get(&node, "id") {
            Some(v) if pyval::py_truthy(v) => {}
            _ => continue,
        }
        total += 1;
        let prov: Vec<String> = arr_of(obj_get(&node, "provenance")).iter().map(s).collect();
        if prov.iter().any(|p| !NON_SOURCE_KEYS.contains(&p.as_str())) {
            covered += 1;
        }
    }
    (covered, total)
}

/// 真源 `provenance_strength`。
pub fn provenance_strength(graph: &Json) -> String {
    match obj_get(graph, "provenance_strength") {
        Some(Json::Null) | None => String::new(),
        Some(v) => s(v).trim().to_string(),
    }
}

/// 真源 `toposort`（Kahn；并列按 id 升序）。有环 → `Err`。
pub fn toposort(graph: &Json) -> Result<Vec<String>, String> {
    let prereqs = prereqs_of(graph);
    let mut ids: Vec<String> = prereqs.iter().map(|(k, _)| k.clone()).collect();
    ids.sort();
    let mut indeg: Vec<(String, i64)> = ids.iter().map(|i| (i.clone(), 0)).collect();
    let mut children: Vec<(String, Vec<String>)> =
        ids.iter().map(|i| (i.clone(), Vec::new())).collect();
    for (i, ps) in &prereqs {
        for p in ps {
            if indeg.iter().any(|(k, _)| k == p) {
                if let Some(e) = indeg.iter_mut().find(|(k, _)| k == i) {
                    e.1 += 1;
                }
                if let Some(e) = children.iter_mut().find(|(k, _)| k == p) {
                    let _ = &e.0;
                    e.1.push(i.clone());
                }
            }
        }
    }
    let mut ready: Vec<String> = indeg
        .iter()
        .filter(|(_, d)| *d == 0)
        .map(|(k, _)| k.clone())
        .collect();
    ready.sort();
    let mut out: Vec<String> = Vec::new();
    while !ready.is_empty() {
        let cur = ready.remove(0);
        out.push(cur.clone());
        let mut nxts: Vec<String> = children
            .iter()
            .find(|(k, _)| *k == cur)
            .map(|(_, v)| v.clone())
            .unwrap_or_default();
        nxts.sort();
        for nxt in nxts {
            if let Some(e) = indeg.iter_mut().find(|(k, _)| *k == nxt) {
                e.1 -= 1;
                if e.1 == 0 {
                    ready.push(nxt);
                }
            }
        }
        ready.sort();
    }
    if out.len() != ids.len() {
        return Err("概念图存在环，无法给出装载序（修复指引：按资产 §4 conflict_rules 归并并列节点）"
            .to_string());
    }
    Ok(out)
}

/// 真源 `problems`：图健康度判据。
pub fn problems(graph: &Json) -> Vec<String> {
    let mut issues: Vec<String> = Vec::new();
    let prereqs = prereqs_of(graph);
    let ext: Vec<String> = arr_of(obj_get(graph, "external_prereqs"))
        .iter()
        .filter(|x| matches!(x, Json::Object(_)))
        .map(|x| s(&obj_get(x, "id").cloned().unwrap_or(Json::Null)))
        .collect();
    let mut declared: Vec<String> = prereqs.iter().map(|(k, _)| k.clone()).collect();
    declared.extend(ext);
    let legend: Vec<String> = match obj_get(graph, "provenance_legend") {
        Some(Json::Object(o)) => o.iter().map(|(k, _)| k.clone()).collect(),
        _ => Vec::new(),
    };
    let strength = provenance_strength(graph);
    if strength.is_empty() {
        issues.push(format!(
            "图缺 provenance_strength 声明（修复指引：在机读块声明取值 {}——证据强度须显式，不得默认按强证据理解）",
            PROVENANCE_STRENGTHS.join(" / ")
        ));
    } else if !PROVENANCE_STRENGTHS.contains(&strength.as_str()) {
        issues.push(format!(
            "provenance_strength 越词表：{}（取值 {}）",
            strength,
            PROVENANCE_STRENGTHS.join(" / ")
        ));
    } else {
        let (covered, total) = external_coverage(graph);
        let ratio = if total != 0 { covered as f64 / total as f64 } else { 0.0 };
        if strength == "external" && ratio < 1.0 {
            issues.push(format!(
                "provenance_strength=external 但外部覆盖仅 {}/{}（修复指引：补齐每节点的外部来源锚，或按实况降为 mixed / domain-logic）",
                covered, total
            ));
        } else if strength == "mixed" && !(ratio > 0.0 && ratio < 1.0) {
            issues.push(format!(
                "provenance_strength=mixed 但外部覆盖 = {}/{}（修复指引：全覆盖用 external；无外部锚用 domain-logic / inferred）",
                covered, total
            ));
        } else if (strength == "domain-logic" || strength == "inferred") && ratio > 0.0 {
            issues.push(format!(
                "provenance_strength={} 但已有 {}/{} 节点挂外部来源键（修复指引：按实况升为 mixed / external）",
                strength, covered, total
            ));
        }
    }
    let mut seen_nodes: Vec<String> = Vec::new();
    for node in arr_of(obj_get(graph, "nodes")) {
        let Json::Object(_) = &node else { continue };
        let idv = obj_get(&node, "id").cloned().unwrap_or(Json::Null);
        if !pyval::py_truthy(&idv) {
            issues.push("节点缺 id（修复指引：每个节点须有 Cxx 编号）".to_string());
            continue;
        }
        let nid = s(&idv);
        if seen_nodes.contains(&nid) {
            issues.push(format!("节点 id 重复：{}（编号须唯一）", nid));
        }
        seen_nodes.push(nid.clone());
        let name = obj_get(&node, "name").cloned().unwrap_or(Json::Null);
        if s(&name).trim().is_empty() {
            issues.push(format!("节点 {} 缺 name（修复指引：每个概念须有可读名）", nid));
        }
        let prov = arr_of(obj_get(&node, "provenance"));
        if prov.is_empty() {
            issues.push(format!("节点 {} 缺 provenance（边无溯源即不可复核）", nid));
        } else {
            for key in &prov {
                if !legend.contains(&s(key)) {
                    issues.push(format!(
                        "节点 {} 的 provenance 键 {} 不在 provenance_legend 中（修复指引：补图例键，防图例漂移静默）",
                        nid,
                        pyval::py_repr(key)
                    ));
                }
            }
        }
        let layer = match obj_get(&node, "layer") {
            Some(Json::Null) | None => String::new(),
            Some(v) => s(v),
        };
        if !layer.is_empty() && !LAYERS.contains(&layer.as_str()) {
            issues.push(format!(
                "节点 {} 层位越界：{}（取值 {}）",
                nid,
                layer,
                LAYERS.join("/")
            ));
        }
    }
    let mut sorted_prereqs = prereqs.clone();
    sorted_prereqs.sort_by(|a, b| a.0.cmp(&b.0));
    for (nid, ps) in &sorted_prereqs {
        for p in ps {
            if !declared.contains(p) {
                issues.push(format!("悬空前置：{} ← {}（前置不在节点表 / 外部前置族中）", nid, p));
            }
            if p == nid {
                issues.push(format!("自环：{} ← {}", nid, p));
            }
        }
    }
    let bids = node_branch(graph);
    let mut unbranched: Vec<String> = prereqs
        .iter()
        .map(|(k, _)| k.clone())
        .filter(|n| !bids.iter().any(|(k, _)| k == n))
        .collect();
    unbranched.sort();
    for nid in unbranched {
        issues.push(format!("概念 {} 未归入任何分支（修复指引：在图 branches 段登记）", nid));
    }
    let mut ghost: Vec<String> = bids
        .iter()
        .map(|(k, _)| k.clone())
        .filter(|n| !prereqs.iter().any(|(k, _)| k == n))
        .collect();
    ghost.sort();
    for nid in ghost {
        issues.push(format!("分支声明了不存在的概念：{}（修复指引：核对 branches.nodes）", nid));
    }
    let flat: Vec<String> = branch_map(graph).into_iter().flat_map(|(_, v)| v).collect();
    let mut uniq = flat.clone();
    uniq.sort();
    uniq.dedup();
    if uniq.len() != flat.len() {
        issues.push("概念被多个分支重复声明（修复指引：一概念只入一个分支）".to_string());
    }
    if let Err(e) = alias_map(graph) {
        issues.push(e);
    }
    if let Err(e) = toposort(graph) {
        issues.push(e);
    }
    issues
}

/// 真源 `scan` → `(issues, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let (mut nodes, mut edges) = (0i64, 0i64);
    let assets = graph_assets(root);
    for rel in &assets {
        let graph = match load_graph(root, rel) {
            Ok(g) => g,
            Err(e) => {
                issues.push(format!("{}: {}", rel, e));
                continue;
            }
        };
        let prereqs = prereqs_of(&graph);
        nodes += prereqs.len() as i64;
        edges += prereqs.iter().map(|(_, v)| v.len() as i64).sum::<i64>();
        for msg in problems(&graph) {
            issues.push(format!("{}: {}", rel, msg));
        }
    }
    (
        issues,
        Json::Object(vec![
            ("graphs".to_string(), Json::Int(assets.len() as i64)),
            ("nodes".to_string(), Json::Int(nodes)),
            ("edges".to_string(), Json::Int(edges)),
        ]),
    )
}


/// 真源 `DEFAULT_ASSET`。
pub const DEFAULT_ASSET: &str = "community/AI系统域包/assets/CONCEPT_GRAPH.md";

/// 真源 `node_meta`：`{概念 id: 节点元信息}`（含包外前置，标 `external=True`）。
pub fn node_meta(graph: &Json) -> Vec<(String, Json)> {
    let mut out: Vec<(String, Json)> = Vec::new();
    if let Json::Object(o) = graph {
        if let Some(Json::Array(nodes)) = o.iter().find(|(k, _)| k == "nodes").map(|(_, v)| v) {
            for n in nodes {
                if let Json::Object(no) = n {
                    if let Some(Json::Str(id)) = no.iter().find(|(k, _)| k == "id").map(|(_, v)| v) {
                        let mut rec = no.clone();
                        rec.push(("external".to_string(), Json::Bool(false)));
                        out.push((id.clone(), Json::Object(rec)));
                    }
                }
            }
        }
        if let Some(Json::Array(ext)) =
            o.iter().find(|(k, _)| k == "external_prereqs").map(|(_, v)| v)
        {
            for n in ext {
                if let Json::Object(no) = n {
                    if let Some(Json::Str(id)) = no.iter().find(|(k, _)| k == "id").map(|(_, v)| v) {
                        if !out.iter().any(|(k, _)| k == id) {
                            let mut rec = no.clone();
                            rec.push(("external".to_string(), Json::Bool(true)));
                            out.push((id.clone(), Json::Object(rec)));
                        }
                    }
                }
            }
        }
    }
    out
}

/// 真源 `in_package_ids`：包内概念 id（外部前置族不计入装载序），**有序**。
pub fn in_package_ids(graph: &Json) -> Vec<String> {
    let mut ids: Vec<String> = prereqs_of(graph).into_iter().map(|(k, _)| k).collect();
    ids.sort();
    ids
}

/// 真源 `resolve`：检索词 → 概念 id（顺序：条目键 → 别名 → 概念名）。
///
/// ⚠️ 别名比对真源用 `str.casefold()`，本线用 `to_lowercase()`（与 `miniyaml` 的别名口径同一
/// 已登记偏差）；本仓语料无 casefold 与 lowercase 分歧的字符。
pub fn resolve(graph: &Json, token: &str) -> Result<String, String> {
    let t = token.trim().to_string();
    let meta = node_meta(graph);
    if meta.iter().any(|(k, _)| *k == t) {
        return Ok(t);
    }
    let am = alias_map(graph)?;
    if let Some((_, v)) = am.iter().find(|(k, _)| *k == t.to_lowercase()) {
        return Ok(v.clone());
    }
    for (nid, rec) in &meta {
        let name = match rec {
            Json::Object(o) => match o.iter().find(|(k, _)| k == "name").map(|(_, v)| v) {
                Some(Json::Str(s)) => s.trim().to_string(),
                _ => String::new(),
            },
            _ => String::new(),
        };
        if name.to_lowercase() == t.to_lowercase() {
            return Ok(nid.clone());
        }
    }
    Err(format!(
        "检索词不在图中：{}（修复指引：用条目键 Cxx、别名或概念名——`--list` 可枚举全表）",
        token
    ))
}

/// 真源 `closure`：传递闭包 `closure(target) = {target} ∪ ⋃ closure(p)`；返回**排序**列表。
pub fn closure(graph: &Json, target: &str) -> Result<Vec<String>, String> {
    let tid = resolve(graph, target)?;
    let prereqs = prereqs_of(graph);
    let mut seen: Vec<String> = Vec::new();
    let mut stack: Vec<String> = vec![tid];
    while let Some(cur) = stack.pop() {
        if seen.contains(&cur) {
            continue;
        }
        seen.push(cur.clone());
        if let Some((_, ps)) = prereqs.iter().find(|(k, _)| *k == cur) {
            for p in ps {
                stack.push(p.clone());
            }
        }
    }
    seen.sort();
    Ok(seen)
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_concept_graph_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 真实语料差分（期望值由生成器从真源取）=====
    ///
    /// 真语料上 **0 份图资产全部健康**（issues=0），故判据面里那些错误分支要另做合成夹具
    /// （下一轮）；这一条钉的是**枚举面 + 通过路径 + stats 三项计数**。
    #[test]
    fn concept_graph_matches_truth_source() {
        let root = crate::testutil::repo_root();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, &[] as &[&str], "issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"edges": 4840, "graphs": 102, "nodes": 2635}"#).unwrap(),
        )
        .unwrap();
        assert!(
            crate::jsonread::json_eq(&stats, &want),
            "stats 不一致\n  实得 {}\n  期望 {}",
            stats.dumps(),
            want.dumps()
        );
    }

    /// 枚举面单独钉一条：`graph_assets` 的相对路径清单须与真源逐条同序。
    #[test]
    fn concept_graph_asset_enumeration_matches_truth_source() {
        let root = crate::testutil::repo_root();
        assert_eq!(graph_assets(&root), &[r#"community/AI人力资源与招聘域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI保险域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI农业域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI制药与生物域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI制造业域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI医疗健康域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI政务与公共事务域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI教育域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI法律与合规域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI系统域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI能源与电力域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI金融投研与风控域包/assets/CONCEPT_GRAPH.md"#, r#"community/AI食品与餐饮域包/assets/CONCEPT_GRAPH.md"#, r#"community/三维与世界模型域包/assets/CONCEPT_GRAPH.md"#, r#"community/上下文工程与长上下文域包/assets/CONCEPT_GRAPH.md"#, r#"community/世界书与设定库域包/assets/CONCEPT_GRAPH.md"#, r#"community/个人助理与日常生活域包/assets/CONCEPT_GRAPH.md"#, r#"community/交通与出行域包/assets/CONCEPT_GRAPH.md"#, r#"community/产业与商业落地域包/assets/CONCEPT_GRAPH.md"#, r#"community/代码与软件工程域包/assets/CONCEPT_GRAPH.md"#, r#"community/代码大模型域包/assets/CONCEPT_GRAPH.md"#, r#"community/代码审查与缺陷检测域包/assets/CONCEPT_GRAPH.md"#, r#"community/代码生成与补全域包/assets/CONCEPT_GRAPH.md"#, r#"community/企业培训与组织学习域包/assets/CONCEPT_GRAPH.md"#, r#"community/传媒与新闻域包/assets/CONCEPT_GRAPH.md"#, r#"community/信息抽取与结构化域包/assets/CONCEPT_GRAPH.md"#, r#"community/具身智能与机器人域包/assets/CONCEPT_GRAPH.md"#, r#"community/内容分发与社区运营域包/assets/CONCEPT_GRAPH.md"#, r#"community/内容改写与风格迁移域包/assets/CONCEPT_GRAPH.md"#, r#"community/分类与情感分析域包/assets/CONCEPT_GRAPH.md"#, r#"community/参数高效微调域包/assets/CONCEPT_GRAPH.md"#, r#"community/可观测性成本与可靠性域包/assets/CONCEPT_GRAPH.md"#, r#"community/可解释性与审计域包/assets/CONCEPT_GRAPH.md"#, r#"community/合成数据生成域包/assets/CONCEPT_GRAPH.md"#, r#"community/合规与监管域包/assets/CONCEPT_GRAPH.md"#, r#"community/向量库与检索管线域包/assets/CONCEPT_GRAPH.md"#, r#"community/图像生成与编辑域包/assets/CONCEPT_GRAPH.md"#, r#"community/图像生成与视觉创作域包/assets/CONCEPT_GRAPH.md"#, r#"community/图像生成与视觉设计域包/assets/CONCEPT_GRAPH.md"#, r#"community/多智能体协同域包/assets/CONCEPT_GRAPH.md"#, r#"community/多模态大模型域包/assets/CONCEPT_GRAPH.md"#, r#"community/多语翻译与本地化域包/assets/CONCEPT_GRAPH.md"#, r#"community/多轮对话与角色扮演域包/assets/CONCEPT_GRAPH.md"#, r#"community/大语言模型域包/assets/CONCEPT_GRAPH.md"#, r#"community/安全与对齐域包/assets/CONCEPT_GRAPH.md"#, r#"community/对话与客服域包/assets/CONCEPT_GRAPH.md"#, r#"community/对齐与偏好优化域包/assets/CONCEPT_GRAPH.md"#, r#"community/嵌入与检索表示域包/assets/CONCEPT_GRAPH.md"#, r#"community/平台与基础设施域包/assets/CONCEPT_GRAPH.md"#, r#"community/建筑与房地产域包/assets/CONCEPT_GRAPH.md"#, r#"community/开源与开发者生态域包/assets/CONCEPT_GRAPH.md"#, r#"community/强化学习与决策域包/assets/CONCEPT_GRAPH.md"#, r#"community/推理优化与加速域包/assets/CONCEPT_GRAPH.md"#, r#"community/推理服务与部署域包/assets/CONCEPT_GRAPH.md"#, r#"community/推荐排序与广告域包/assets/CONCEPT_GRAPH.md"#, r#"community/提示工程与指令设计域包/assets/CONCEPT_GRAPH.md"#, r#"community/提示工程与提示模板域包/assets/CONCEPT_GRAPH.md"#, r#"community/搜索与信息聚合域包/assets/CONCEPT_GRAPH.md"#, r#"community/摘要与信息压缩域包/assets/CONCEPT_GRAPH.md"#, r#"community/数字人与虚拟形象域包/assets/CONCEPT_GRAPH.md"#, r#"community/数学与形式化推理域包/assets/CONCEPT_GRAPH.md"#, r#"community/数据分析与决策支持域包/assets/CONCEPT_GRAPH.md"#, r#"community/数据分析与表格理解域包/assets/CONCEPT_GRAPH.md"#, r#"community/数据标注与标注质量域包/assets/CONCEPT_GRAPH.md"#, r#"community/数据采集与清洗域包/assets/CONCEPT_GRAPH.md"#, r#"community/文旅与酒店域包/assets/CONCEPT_GRAPH.md"#, r#"community/文本生成与创作域包/assets/CONCEPT_GRAPH.md"#, r#"community/文档解析与版面理解域包/assets/CONCEPT_GRAPH.md"#, r#"community/智能体与工作流编排域包/assets/CONCEPT_GRAPH.md"#, r#"community/智能体框架与工具调用域包/assets/CONCEPT_GRAPH.md"#, r#"community/机器翻译与本地化域包/assets/CONCEPT_GRAPH.md"#, r#"community/模型运营与成本域包/assets/CONCEPT_GRAPH.md"#, r#"community/测试与用例生成域包/assets/CONCEPT_GRAPH.md"#, r#"community/游戏与互动娱乐域包/assets/CONCEPT_GRAPH.md"#, r#"community/版权与知识产权域包/assets/CONCEPT_GRAPH.md"#, r#"community/物流与供应链域包/assets/CONCEPT_GRAPH.md"#, r#"community/监督微调域包/assets/CONCEPT_GRAPH.md"#, r#"community/知识管理与检索增强域包/assets/CONCEPT_GRAPH.md"#, r#"community/知识问答与检索增强域包/assets/CONCEPT_GRAPH.md"#, r#"community/科研与实验域包/assets/CONCEPT_GRAPH.md"#, r#"community/端侧与边缘小模型域包/assets/CONCEPT_GRAPH.md"#, r#"community/红队越狱与安全测试域包/assets/CONCEPT_GRAPH.md"#, r#"community/编辑校对与出版域包/assets/CONCEPT_GRAPH.md"#, r#"community/视觉模型域包/assets/CONCEPT_GRAPH.md"#, r#"community/视频生成与剪辑域包/assets/CONCEPT_GRAPH.md"#, r#"community/视频生成与理解域包/assets/CONCEPT_GRAPH.md"#, r#"community/视频生成与自动剪辑域包/assets/CONCEPT_GRAPH.md"#, r#"community/角色扮演与角色卡域包/assets/CONCEPT_GRAPH.md"#, r#"community/记忆体与个性化域包/assets/CONCEPT_GRAPH.md"#, r#"community/评测与基准域包/assets/CONCEPT_GRAPH.md"#, r#"community/评测基准与排行榜域包/assets/CONCEPT_GRAPH.md"#, r#"community/语音合成与配音域包/assets/CONCEPT_GRAPH.md"#, r#"community/语音识别与合成域包/assets/CONCEPT_GRAPH.md"#, r#"community/语音转写与会议记录域包/assets/CONCEPT_GRAPH.md"#, r#"community/量化金融域包/assets/QUANT_GRAPH.md"#, r#"community/长文本与小说创作域包/assets/CONCEPT_GRAPH.md"#, r#"community/隐私与数据治理域包/assets/CONCEPT_GRAPH.md"#, r#"community/零售与电商域包/assets/CONCEPT_GRAPH.md"#, r#"community/音频与音乐生成域包/assets/CONCEPT_GRAPH.md"#, r#"community/音频音乐与语音域包/assets/CONCEPT_GRAPH.md"#, r#"community/预测异常与风险域包/assets/CONCEPT_GRAPH.md"#, r#"community/预训练与继续预训练域包/assets/CONCEPT_GRAPH.md"#] as &[&str]);
    }
    // <<< GENERATED
}
