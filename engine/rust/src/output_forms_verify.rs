//! `output_forms` 的**复算与校验层**：`_recompute_entry` / `_deep_diff` / `_verify_pack` /
//! `index_verify` / `_dual_source_check` / `meter` / `baseline_verify` / `scan`。
//!
//! 与真源 `desktop/src/core/output_forms.py` 对账。
//!
//! **不移植**（三处，都是纯优化或写面，不改结论）：
//! - `index_verify` 的 `memo_pair` + 落盘缓存 + `_memo_reads`（同内容重复调用省时间）；
//! - `_verify_pack_cached` / `_verify_pack_io` / `pack_content_key` / `shared_face_key` /
//!   `pack_slice_index`（按包内容键的结果缓存）；
//! - `render_outputs`（**写面**）、`write_baseline`（**写面**）。

use crate::output_forms as of;
use crate::output_forms_checks as oc;
use crate::output_forms_gen::{dispatch, gen_id, GenOut};
use crate::pyjson::Json;
use crate::pyval;
use std::collections::BTreeMap;
use std::path::Path;

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

fn s_of(v: Option<&Json>) -> String {
    match v {
        None | Some(Json::Null) => String::new(),
        Some(x) => pyval::plain_str(x),
    }
}

/// 真源 `output_forms._pack_dirs`：有 `community/<包>/outputs/INDEX.json` 的包目录名（有序）。
///
/// ⚠️ 与 `pack_combo._pack_dirs`（要求 `protocol.yaml`）**不是同一个面**，别混用。
pub fn pack_dirs(root: &Path) -> Vec<String> {
    let mut rels = crate::glob::expand(root, "community/*/outputs/INDEX.json");
    rels.sort();
    let mut out: Vec<String> = Vec::new();
    for rel in rels {
        if let Some(pkg) = rel.split('/').nth(1) {
            if !out.contains(&pkg.to_string()) {
                out.push(pkg.to_string());
            }
        }
    }
    out.sort();
    out
}

/// 真源 `_count`：按某键计数（键为 `str(...)`，结果按键排序）。
pub fn count(rows: &[Json], key: &str) -> Json {
    let mut m: BTreeMap<String, i64> = BTreeMap::new();
    for r in rows {
        *m.entry(pyval::plain_str(&obj_get(r, key).cloned().unwrap_or(Json::Null))).or_insert(0) += 1;
    }
    Json::Object(m.into_iter().map(|(k, v)| (k, Json::Int(v))).collect())
}

/// 真源 `_dump`：文本补齐末尾换行；JSON 走 `indent=2, sort_keys=True` + 换行。
pub fn dump(value: &GenOut) -> String {
    match value {
        GenOut::Text(s) => {
            if s.ends_with('\n') {
                s.clone()
            } else {
                format!("{}\n", s)
            }
        }
        GenOut::Json(j) => j.dumps_file(),
    }
}

/// 真源 `_deep_diff`。
pub fn deep_diff(a: &Json, b: &Json, path: &str, out: &mut Vec<String>) {
    match (a, b) {
        (Json::Object(x), Json::Object(y)) => {
            let mut keys: Vec<String> = Vec::new();
            for (k, _) in x {
                if !keys.contains(k) {
                    keys.push(k.clone());
                }
            }
            for (k, _) in y {
                if !keys.contains(k) {
                    keys.push(k.clone());
                }
            }
            keys.sort();
            for k in keys {
                let av = x.iter().find(|(kk, _)| *kk == k).map(|(_, v)| v);
                let bv = y.iter().find(|(kk, _)| *kk == k).map(|(_, v)| v);
                match (av, bv) {
                    (None, Some(_)) => out.push(format!("{}.{} 仅存于在盘", path, k)),
                    (Some(_), None) => out.push(format!("{}.{} 仅存于复算", path, k)),
                    (Some(av), Some(bv)) => deep_diff(av, bv, &format!("{}.{}", path, k), out),
                    (None, None) => {}
                }
            }
        }
        (Json::Array(x), Json::Array(y)) => {
            if x.len() != y.len() {
                out.push(format!("{} 长度 {}≠{}", path, x.len(), y.len()));
            }
            for i in 0..x.len().min(y.len()) {
                deep_diff(&x[i], &y[i], &format!("{}[{}]", path, i), out);
            }
        }
        (Json::Int(x), Json::Int(y)) => {
            if x != y {
                out.push(format!(
                    "{} 数值 {}≠{}",
                    path,
                    pyval::py_repr(a),
                    pyval::py_repr(b)
                ));
            }
        }
        (Json::Float(x), Json::Float(y)) => {
            if (x - y).abs() > 1e-9 {
                out.push(format!(
                    "{} 数值 {}≠{}",
                    path,
                    pyval::py_repr(a),
                    pyval::py_repr(b)
                ));
            }
        }
        (Json::Int(x), Json::Float(y)) | (Json::Float(y), Json::Int(x)) => {
            if ((*x as f64) - *y).abs() > 1e-9 {
                out.push(format!(
                    "{} 数值 {}≠{}",
                    path,
                    pyval::py_repr(a),
                    pyval::py_repr(b)
                ));
            }
        }
        _ => {
            if !crate::jsonread::json_eq(a, b) {
                out.push(format!(
                    "{} {}≠{}",
                    path,
                    pyval::py_repr(a),
                    pyval::py_repr(b)
                ));
            }
        }
    }
}

/// 真源 `_recompute_entry` → `(issues, stats)`。
pub fn recompute_entry(root: &Path, entry: &Json) -> (Vec<String>, Json) {
    let out_rel = s_of(obj_get(entry, "path"));
    let gid = gen_id(entry);
    if !crate::output_forms_gen::GENERATOR_IDS.contains(&gid.as_str()) {
        return (
            vec![format!(
                "{} 声明复算 {} 无对应引擎（不得假装可复算）",
                out_rel,
                pyval::py_repr(&Json::Str(gid))
            )],
            Json::Object(vec![]),
        );
    }
    let (fresh, errs) = dispatch(root, entry);
    let Some(fresh) = fresh else {
        return (
            errs.into_iter().map(|e| format!("{}: {}", out_rel, e)).collect(),
            Json::Object(vec![]),
        );
    };
    let disk_rel = match of::declared_out_rel(root, &s_of(obj_get(entry, "_pkg")), &Json::Str(out_rel.clone())) {
        Ok(v) => v,
        Err(e) => return (vec![format!("{}: {}", out_rel, e)], Json::Object(vec![])),
    };
    let on_disk = std::fs::read(root.join(&disk_rel)).unwrap_or_default();
    let mut diffs: Vec<String> = Vec::new();
    match &fresh {
        GenOut::Text(_) => {
            if on_disk != dump(&fresh).into_bytes() {
                diffs.push("文本面与复算不一致（逐字节）".to_string());
            }
        }
        GenOut::Json(fresh_json) => {
            let text = String::from_utf8_lossy(&on_disk).into_owned();
            let declared = match crate::jsonmini::parse(&text) {
                Ok(p) => p.value,
                Err(e) => {
                    return (
                        vec![format!("{}: 在盘产物不可解析 {}", out_rel, e)],
                        Json::Object(vec![]),
                    )
                }
            };
            // 真源 `{k: declared.get(k) for k in fresh}`：以**复算值的键**取在盘值
            let projected = match fresh_json {
                Json::Object(o) => Json::Object(
                    o.iter()
                        .map(|(k, _)| {
                            (k.clone(), obj_get(&declared, k).cloned().unwrap_or(Json::Null))
                        })
                        .collect(),
                ),
                other => other.clone(),
            };
            deep_diff(fresh_json, &projected, "$", &mut diffs);
            if on_disk.windows(2).any(|w| w == b"\r\n") {
                diffs.push("在盘产物含 CRLF（仓库 EOL 契约 = LF）".to_string());
            }
        }
    }
    (
        diffs.iter().map(|d| format!("{}: 复算与在盘不一致 {}", out_rel, d)).collect(),
        Json::Object(vec![("diff".to_string(), Json::Int(diffs.len() as i64))]),
    )
}

/// 真源 `_dual_source_check`：数据面 vs 散文面（键集必须互为子集）。
pub fn dual_source_check(root: &Path, pkg: &str, path: &str, ds: &Json) -> Vec<String> {
    let md_rel = s_of(obj_get(ds, "markdown"));
    let key_text = {
        let v = s_of(obj_get(ds, "key_pattern"));
        if v.is_empty() {
            r"`([A-Z][A-Z0-9_]{2,})`".to_string()
        } else {
            v
        }
    };
    let why = crate::json_schema::pattern_issue(
        &Json::Str(key_text.clone()),
        "dual_source.key_pattern",
    );
    if !why.is_empty() {
        return vec![format!("双源 key_pattern 不合形态：{}", why)];
    }
    let re = match fancy_regex::Regex::new(&key_text) {
        Ok(r) => r,
        Err(e) => {
            return vec![format!("双源 key_pattern 不合形态：编译失败 {}", e)];
        }
    };
    let md_full = match of::declared_out_rel(root, pkg, &Json::Str(md_rel.clone())) {
        Ok(v) => v,
        Err(e) => return vec![e],
    };
    let md_path = root.join(&md_full);
    if !md_path.is_file() {
        return vec![format!("双源对照件不存在：{}", md_rel)];
    }
    let text = std::fs::read(&md_path)
        .map(|b| String::from_utf8_lossy(&b).into_owned())
        .unwrap_or_default();
    let mut md_keys: Vec<String> = findall(&re, &text);
    for drop in arr_of(obj_get(ds, "exclude")) {
        let d = pyval::plain_str(&drop);
        md_keys.retain(|x| *x != d);
    }
    let (data, err) = oc::read_json(root, path);
    if !err.is_empty() {
        return vec![err];
    }
    let field = {
        let f = s_of(obj_get(ds, "field"));
        if f.is_empty() {
            "id".to_string()
        } else {
            f
        }
    };
    let mut data_keys: Vec<String> = Vec::new();
    if let Json::Object(o) = &data {
        for (_, value) in o {
            let Json::Array(items) = value else { continue };
            for item in items {
                let v = obj_get(item, &field).cloned().unwrap_or(Json::Null);
                if pyval::py_truthy(&v) {
                    let s = pyval::plain_str(&v);
                    if !data_keys.contains(&s) {
                        data_keys.push(s);
                    }
                }
            }
        }
    }
    let mut only_md: Vec<String> = md_keys.iter().filter(|k| !data_keys.contains(k)).cloned().collect();
    only_md.sort();
    let mut only_data: Vec<String> =
        data_keys.iter().filter(|k| !md_keys.contains(k)).cloned().collect();
    only_data.sort();
    let mut out = Vec::new();
    if !only_md.is_empty() {
        out.push(format!(
            "双源不一致：散文面独有键 {}",
            pyval::py_repr_list(
                &only_md.iter().take(6).map(|s| Json::Str(s.clone())).collect::<Vec<_>>()
            )
        ));
    }
    if !only_data.is_empty() {
        out.push(format!(
            "双源不一致：数据面独有键 {}",
            pyval::py_repr_list(
                &only_data.iter().take(6).map(|s| Json::Str(s.clone())).collect::<Vec<_>>()
            )
        ));
    }
    out
}

/// 近似 Python `re.findall`：无组 → 整个匹配；**恰好一组** → 该组内容；多组 → 元组 repr。
///
/// 本仓 `dual_source.key_pattern` 实测全是**恰好一组**（101 条，如 `(D14-[0-9]{2})`），
/// 无组与多组按 Python 语义实现，不留分支缺口。
fn findall(re: &fancy_regex::Regex, text: &str) -> Vec<String> {
    let groups = re.captures_len().saturating_sub(1);
    let mut out: Vec<String> = Vec::new();
    for cap in re.captures_iter(text).flatten() {
        if groups == 0 {
            out.push(cap.get(0).map(|m| m.as_str().to_string()).unwrap_or_default());
        } else if groups == 1 {
            out.push(cap.get(1).map(|m| m.as_str().to_string()).unwrap_or_default());
        } else {
            let parts: Vec<String> = (1..=groups)
                .map(|i| {
                    let v = cap.get(i).map(|m| m.as_str().to_string());
                    format!("'{}'", v.unwrap_or_else(|| "None".to_string()))
                })
                .collect();
            out.push(if parts.len() == 1 {
                parts[0].clone()
            } else {
                format!("({})", parts.join(", "))
            });
        }
    }
    out
}

/// 真源 `_verify_pack` → `(issues, rows)`。
pub fn verify_pack(root: &Path, pkg: &str) -> (Vec<String>, Vec<Json>) {
    let mut issues: Vec<String> = Vec::new();
    let mut rows: Vec<Json> = Vec::new();
    let rel = format!("community/{}/{}", pkg, of::INDEX_REL);
    let (idx, err) = oc::read_json(root, &rel);
    if !err.is_empty() {
        issues.push(format!("{}: {}", rel, err));
        return (issues, rows);
    }
    if s_of(obj_get(&idx, "schema")) != "nf-output-index/1" {
        issues.push(format!("{}: schema 应为 nf-output-index/1", rel));
    }
    if s_of(obj_get(&idx, "package")) != pkg {
        issues.push(format!(
            "{}: package 字段 {} ≠ 包目录名 {}",
            rel,
            pyval::py_repr(&obj_get(&idx, "package").cloned().unwrap_or(Json::Null)),
            pyval::py_repr(&Json::Str(pkg.to_string()))
        ));
    }
    for entry in arr_of(obj_get(&idx, "outputs")) {
        let path = s_of(obj_get(&entry, "path"));
        let form = s_of(obj_get(&entry, "form"));
        let tier = s_of(obj_get(&entry, "tier"));
        if path.is_empty() {
            issues.push(format!("{}: outputs 条目缺 path", rel));
            continue;
        }
        if !of::TIERS.contains(&tier.as_str()) {
            issues.push(format!(
                "{}: {} 档位非法 {}",
                rel,
                path,
                pyval::py_repr(&Json::Str(tier.clone()))
            ));
            continue;
        }
        let out_rel = match of::declared_out_rel(root, pkg, &Json::Str(path.clone())) {
            Ok(v) => v,
            Err(e) => {
                issues.push(format!("{}: {}", rel, e));
                continue;
            }
        };
        if !root.join(&out_rel).is_file() {
            issues.push(format!("{}: 声明产出面不存在 {}", rel, path));
            continue;
        }
        let (got_form, got_tier) = of::detect(root, &out_rel);
        if !form.is_empty() && form != got_form {
            issues.push(format!("{}: {} 声明形态 {}，实测 {}", rel, path, form, got_form));
        }
        let ti = of::TIERS.iter().position(|t| *t == tier).unwrap_or(0);
        let gi = of::TIERS.iter().position(|t| *t == got_tier).unwrap_or(0);
        if ti > gi {
            issues.push(format!(
                "{}: {} 声明档位 {} 超出本仓可判上限 {}",
                rel, path, tier, got_tier
            ));
        }
        let form_key = if form.is_empty() { got_form.clone() } else { form.clone() };
        if let Some(sub) = oc::form_check(&form_key, root, &out_rel) {
            for s in sub {
                issues.push(format!("{}: {} {}", rel, path, s));
            }
        }
        let sch_rel = s_of(obj_get(&entry, "schema"));
        if !sch_rel.is_empty() {
            let full = match of::declared_out_rel(root, pkg, &Json::Str(sch_rel.clone())) {
                Ok(v) => v,
                Err(e) => {
                    issues.push(format!("{}: {} {}", rel, path, e));
                    String::new()
                }
            };
            let (schema, serr) = if full.is_empty() {
                (Json::Null, "schema 路径越界".to_string())
            } else {
                oc::read_json(root, &full)
            };
            if !serr.is_empty() {
                issues.push(format!("{}: {} schema {}", rel, path, serr));
            } else {
                let (inst, ierr) = oc::read_json(root, &out_rel);
                if !ierr.is_empty() {
                    issues.push(format!("{}: {} {}", rel, path, ierr));
                } else {
                    let errs = crate::json_schema::json_schema_check(&inst, &schema);
                    for e in errs.iter().take(8) {
                        issues.push(format!("{}: {} schema 不符 {}", rel, path, e));
                    }
                }
            }
        }
        if let Some(ds) = obj_get(&entry, "dual_source") {
            if matches!(ds, Json::Object(_)) {
                for m in dual_source_check(root, pkg, &out_rel, ds) {
                    issues.push(format!("{}: {} {}", rel, path, m));
                }
            }
        }
        if let Some(rc) = obj_get(&entry, "recompute") {
            if matches!(rc, Json::Object(_)) {
                let mut e2 = entry.clone();
                if let Json::Object(o) = &mut e2 {
                    o.push(("_pkg".to_string(), Json::Str(pkg.to_string())));
                }
                let (sub, _st) = recompute_entry(root, &e2);
                for s in sub {
                    issues.push(format!("{}: {}", rel, s));
                }
            }
        } else if tier == "T4" {
            issues.push(format!("{}: {} 声明 T4（可复算）却无 recompute 声明", rel, path));
        }
        rows.push(Json::Object(vec![
            ("package".to_string(), Json::Str(pkg.to_string())),
            ("path".to_string(), Json::Str(path)),
            (
                "form".to_string(),
                Json::Str(if form.is_empty() { got_form } else { form }),
            ),
            ("tier".to_string(), Json::Str(tier)),
            ("role".to_string(), Json::Str(s_of(obj_get(&entry, "role")))),
        ]));
    }
    (issues, rows)
}

/// 真源 `index_verify`（缓存层不移植）→ `(issues, stats)`。
pub fn index_verify(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let mut rows: Vec<Json> = Vec::new();
    let pkgs = pack_dirs(root);
    for pkg in &pkgs {
        let (i2, r2) = verify_pack(root, pkg);
        issues.extend(i2);
        rows.extend(r2);
    }
    let stats = Json::Object(vec![
        ("packages".to_string(), Json::Int(pkgs.len() as i64)),
        ("outputs".to_string(), Json::Int(rows.len() as i64)),
        ("by_role".to_string(), count(&rows, "role")),
        ("by_tier".to_string(), count(&rows, "tier")),
        ("by_form".to_string(), count(&rows, "form")),
    ]);
    (issues, stats)
}

/// 真源 `meter` → `(issues, stats)`（恒空 issues）。
pub fn meter(root: &Path) -> (Vec<String>, Json) {
    let mut packages: Vec<(String, Json)> = Vec::new();
    // 资产档面一次枚举（真源走共享枚举器；本线直接按模式枚举）
    let mut prose_by_pkg: BTreeMap<String, Vec<String>> = BTreeMap::new();
    let mut rels = crate::glob::expand(root, "community/*/assets/*.md");
    rels.sort();
    for rel in rels {
        let parts: Vec<&str> = rel.split('/').collect();
        if parts.len() == 4 && parts[3] != "README.md" {
            prose_by_pkg.entry(parts[1].to_string()).or_default().push(parts[3].to_string());
        }
    }
    let mut total_mv = 0i64;
    let mut total_fn = 0i64;
    let mut total_prose = 0i64;
    for pkg in pack_dirs(root) {
        let (idx, _err) = oc::read_json(root, &format!("community/{}/{}", pkg, of::INDEX_REL));
        let entries = arr_of(obj_get(&idx, "outputs"));
        let mv: Vec<Json> = entries
            .iter()
            .filter(|e| {
                matches!(obj_get(e, "tier"), Some(Json::Str(s)) if s == "T2" || s == "T3" || s == "T4")
            })
            .cloned()
            .collect();
        let fn_faces: Vec<Json> = entries
            .iter()
            .filter(|e| matches!(obj_get(e, "tier"), Some(Json::Str(s)) if s == "T4"))
            .cloned()
            .collect();
        let prose = prose_by_pkg.get(&pkg).cloned().unwrap_or_default();
        let denom = mv.len() + prose.len();
        let ratio = if denom == 0 {
            0.0
        } else {
            crate::pyfloat::round_to(mv.len() as f64 / denom as f64, 4)
        };
        let role_rows: Vec<Json> = entries
            .iter()
            .map(|e| {
                Json::Object(vec![("r".to_string(), obj_get(e, "role").cloned().unwrap_or(Json::Null))])
            })
            .collect();
        let tier_rows: Vec<Json> = entries
            .iter()
            .map(|e| {
                Json::Object(vec![("t".to_string(), obj_get(e, "tier").cloned().unwrap_or(Json::Null))])
            })
            .collect();
        total_mv += mv.len() as i64;
        total_fn += fn_faces.len() as i64;
        total_prose += prose.len() as i64;
        packages.push((
            pkg,
            Json::Object(vec![
                ("machine_verifiable".to_string(), Json::Int(mv.len() as i64)),
                ("functional".to_string(), Json::Int(fn_faces.len() as i64)),
                ("prose_assets".to_string(), Json::Int(prose.len() as i64)),
                ("machine_verifiable_ratio".to_string(), Json::Float(ratio)),
                ("roles".to_string(), count(&role_rows, "r")),
                ("tiers".to_string(), count(&tier_rows, "t")),
            ]),
        ));
    }
    let totals = if packages.is_empty() {
        Json::Object(vec![])
    } else {
        let denom = std::cmp::max(1, total_mv + total_prose) as f64;
        Json::Object(vec![
            ("machine_verifiable".to_string(), Json::Int(total_mv)),
            ("functional".to_string(), Json::Int(total_fn)),
            ("prose_assets".to_string(), Json::Int(total_prose)),
            (
                "machine_verifiable_ratio".to_string(),
                Json::Float(crate::pyfloat::round_to(total_mv as f64 / denom, 4)),
            ),
        ])
    };
    (
        Vec::new(),
        Json::Object(vec![
            ("packages".to_string(), Json::Object(packages)),
            ("totals".to_string(), totals),
        ]),
    )
}

/// 真源 `baseline_verify` → `(issues, stats)`。
pub fn baseline_verify(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let (base, err) = oc::read_json(root, of::BASELINE_REL);
    let (_, stats) = meter(root);
    if !err.is_empty() {
        return (
            vec![format!(
                "{} 缺失或不可解析（{}；重签：nf output meter --write）",
                of::BASELINE_REL, err
            )],
            stats,
        );
    }
    let prev = match obj_get(&base, "packages") {
        Some(Json::Object(o)) => o.clone(),
        _ => Vec::new(),
    };
    if let Some(Json::Object(cur)) = obj_get(&stats, "packages") {
        for (pkg, c) in cur {
            let Some(old) = prev.iter().find(|(k, _)| k == pkg).map(|(_, v)| v) else {
                continue;
            };
            let old_mv = pyval::py_int_or(obj_get(old, "machine_verifiable"), 0);
            let cur_mv = pyval::py_int_or(obj_get(c, "machine_verifiable"), 0);
            if cur_mv < old_mv {
                issues.push(format!(
                    "{} 机验产出面回退：{} → {}（基线 {}）",
                    pkg,
                    old_mv,
                    cur_mv,
                    of::BASELINE_REL
                ));
            }
            let old_fn = pyval::py_int_or(obj_get(old, "functional"), 0);
            let cur_fn = pyval::py_int_or(obj_get(c, "functional"), 0);
            if cur_fn < old_fn {
                issues.push(format!(
                    "{} 功能面（T4 可复算）回退：{} → {}",
                    pkg, old_fn, cur_fn
                ));
            }
        }
    }
    let mut merged: Vec<(String, Json)> =
        vec![("baseline".to_string(), Json::Bool(!matches!(&base, Json::Null)))];
    if let Json::Object(o) = &stats {
        merged.extend(o.clone());
    }
    (issues, Json::Object(merged))
}

/// 真源 `scan`（`memo_pair` 缓存层不移植）→ `(issues, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let (reg_issues, reg_stats) = of::registry_verify(root);
    for i in reg_issues {
        issues.push(format!("形态清单: {}", i));
    }
    let (idx_issues, idx_stats) = index_verify(root);
    for i in idx_issues {
        issues.push(format!("包级产出面: {}", i));
    }
    let (base_issues, base_stats) = baseline_verify(root);
    for i in base_issues {
        issues.push(format!("机验率基线: {}", i));
    }
    let meter_pkgs = obj_get(&base_stats, "packages").cloned().unwrap_or(Json::Object(vec![]));
    (
        issues,
        Json::Object(vec![
            ("registry".to_string(), reg_stats),
            ("index".to_string(), idx_stats),
            ("meter".to_string(), meter_pkgs),
        ]),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_output_forms_scan_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 真语料 `scan`：形态清单 + **包级产出面 1156 件逐条校验** + 机验率基线 =====
    #[test]
    fn output_forms_scan_matches_truth_source() {
        let root = crate::testutil::repo_root();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, &[] as &[&str], "issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"index": {"by_form": {"combo-cert": 4, "concept-closure": 1, "csv": 101, "domain-report": 100, "domain-spec": 100, "graphml": 105, "json": 4, "json-schema": 312, "mermaid": 106, "performance-report": 1, "quant-metrics": 1, "system-card": 105, "vega-lite": 106}, "by_role": {"chart": 106, "data": 311, "diagram": 211, "functional": 106, "schema": 312}, "by_tier": {"T2": 417, "T3": 523, "T4": 106}, "outputs": 1046, "packages": 106}, "meter": {"AI人力资源与招聘域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI保险域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI农业域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI制药与生物域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI制造业域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI医疗健康域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI政务与公共事务域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI教育域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI法律与合规域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI系统域包": {"functional": 1, "machine_verifiable": 6, "machine_verifiable_ratio": 0.8571, "prose_assets": 1, "roles": {"data": 1, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 2, "T3": 3, "T4": 1}}, "AI能源与电力域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI金融投研与风控域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI食品与餐饮域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "三维与世界模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "上下文工程与长上下文域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "世界书与设定库域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "个人助理与日常生活域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "交通与出行域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "产业与商业落地域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码与软件工程域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码大模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码审查与缺陷检测域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码生成与补全域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "企业培训与组织学习域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "传媒与新闻域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "信息抽取与结构化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "具身智能与机器人域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "内容分发与社区运营域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "内容改写与风格迁移域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "分类与情感分析域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "参数高效微调域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "可观测性成本与可靠性域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "可解释性与审计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "合成数据生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "合规与监管域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "向量库与检索管线域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与编辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与视觉创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与视觉设计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多智能体协同域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多模态大模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多语翻译与本地化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多轮对话与角色扮演域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "大语言模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "安全与对齐域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "对话与客服域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "对齐与偏好优化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "嵌入与检索表示域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "平台与基础设施域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "建筑与房地产域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "开源与开发者生态域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "强化学习与决策域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推理优化与加速域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推理服务与部署域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推荐排序与广告域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "提示工程与指令设计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "提示工程与提示模板域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "搜索与信息聚合域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "摘要与信息压缩域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数字人与虚拟形象域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数学与形式化推理域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据分析与决策支持域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据分析与表格理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据标注与标注质量域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据采集与清洗域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文旅与酒店域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文本生成与创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文档解析与版面理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "智能体与工作流编排域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "智能体框架与工具调用域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "机器翻译与本地化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "模型运营与成本域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "测试与用例生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "游戏与互动娱乐域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "版权与知识产权域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "物流与供应链域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "监督微调域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "知识管理与检索增强域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "知识问答与检索增强域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "科研与实验域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "端侧与边缘小模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "红队越狱与安全测试域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "组合包-受监管行业": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-数据管线": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-检索栈": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-轻混与保险": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "编辑校对与出版域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视觉模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与剪辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与自动剪辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "角色扮演与角色卡域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "记忆体与个性化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "评测与基准域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "评测基准与排行榜域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音合成与配音域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音识别与合成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音转写与会议记录域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "量化金融域包": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 0.6667, "prose_assets": 4, "roles": {"chart": 2, "data": 2, "diagram": 1, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "长文本与小说创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "隐私与数据治理域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "零售与电商域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "音频与音乐生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "音频音乐与语音域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "预测异常与风险域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "预训练与继续预训练域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}}, "registry": {"by_category": {"ai-domain": 15, "chart": 8, "contract": 8, "diagram": 3, "document": 9, "graph-structure": 10, "interface": 13, "packaging": 5, "quant-domain": 22, "structured-data": 8, "tabular": 9, "timeseries": 6}, "by_status": {"absorbed": 17, "deferred": 11, "planned": 61, "reference": 10, "supported": 11, "unfit": 6}, "by_tier": {"T1": 22, "T2": 55, "T3": 39}, "categories": 12, "forms": 116, "unreachable": 6}}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want),
                "stats 不一致\n  实得 {}\n  期望 {}", stats.dumps_default(), want.dumps_default());
    }

    /// 机验率计量逐包比对（`scan` 的 stats 里也含它，这里单独钉一条便于定位）。
    #[test]
    fn meter_matches_truth_source_over_corpus() {
        let root = crate::testutil::repo_root();
        let (issues, stats) = meter(&root);
        assert_eq!(issues, &[] as &[&str]);
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"packages": {"AI人力资源与招聘域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI保险域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI农业域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI制药与生物域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI制造业域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI医疗健康域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI政务与公共事务域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI教育域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI法律与合规域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI系统域包": {"functional": 1, "machine_verifiable": 6, "machine_verifiable_ratio": 0.8571, "prose_assets": 1, "roles": {"data": 1, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 2, "T3": 3, "T4": 1}}, "AI能源与电力域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI金融投研与风控域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI食品与餐饮域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "三维与世界模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "上下文工程与长上下文域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "世界书与设定库域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "个人助理与日常生活域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "交通与出行域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "产业与商业落地域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码与软件工程域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码大模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码审查与缺陷检测域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码生成与补全域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "企业培训与组织学习域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "传媒与新闻域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "信息抽取与结构化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "具身智能与机器人域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "内容分发与社区运营域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "内容改写与风格迁移域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "分类与情感分析域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "参数高效微调域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "可观测性成本与可靠性域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "可解释性与审计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "合成数据生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "合规与监管域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "向量库与检索管线域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与编辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与视觉创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与视觉设计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多智能体协同域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多模态大模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多语翻译与本地化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多轮对话与角色扮演域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "大语言模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "安全与对齐域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "对话与客服域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "对齐与偏好优化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "嵌入与检索表示域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "平台与基础设施域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "建筑与房地产域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "开源与开发者生态域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "强化学习与决策域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推理优化与加速域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推理服务与部署域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推荐排序与广告域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "提示工程与指令设计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "提示工程与提示模板域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "搜索与信息聚合域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "摘要与信息压缩域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数字人与虚拟形象域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数学与形式化推理域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据分析与决策支持域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据分析与表格理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据标注与标注质量域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据采集与清洗域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文旅与酒店域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文本生成与创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文档解析与版面理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "智能体与工作流编排域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "智能体框架与工具调用域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "机器翻译与本地化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "模型运营与成本域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "测试与用例生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "游戏与互动娱乐域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "版权与知识产权域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "物流与供应链域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "监督微调域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "知识管理与检索增强域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "知识问答与检索增强域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "科研与实验域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "端侧与边缘小模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "红队越狱与安全测试域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "组合包-受监管行业": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-数据管线": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-检索栈": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-轻混与保险": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "编辑校对与出版域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视觉模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与剪辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与自动剪辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "角色扮演与角色卡域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "记忆体与个性化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "评测与基准域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "评测基准与排行榜域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音合成与配音域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音识别与合成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音转写与会议记录域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "量化金融域包": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 0.6667, "prose_assets": 4, "roles": {"chart": 2, "data": 2, "diagram": 1, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "长文本与小说创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "隐私与数据治理域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "零售与电商域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "音频与音乐生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "音频音乐与语音域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "预测异常与风险域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "预训练与继续预训练域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}}, "totals": {"functional": 106, "machine_verifiable": 1046, "machine_verifiable_ratio": 0.7742, "prose_assets": 305}}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want), "meter stats 不一致");
    }

    /// 基线比对（可重签工件）：低于基线即 FAIL。
    #[test]
    fn baseline_verify_matches_truth_source() {
        let root = crate::testutil::repo_root();
        let (issues, stats) = baseline_verify(&root);
        assert_eq!(issues, &[] as &[&str]);
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"baseline": true, "packages": {"AI人力资源与招聘域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI保险域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI农业域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI制药与生物域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI制造业域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI医疗健康域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI政务与公共事务域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI教育域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI法律与合规域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI系统域包": {"functional": 1, "machine_verifiable": 6, "machine_verifiable_ratio": 0.8571, "prose_assets": 1, "roles": {"data": 1, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 2, "T3": 3, "T4": 1}}, "AI能源与电力域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI金融投研与风控域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "AI食品与餐饮域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "三维与世界模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "上下文工程与长上下文域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "世界书与设定库域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "个人助理与日常生活域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "交通与出行域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "产业与商业落地域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码与软件工程域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码大模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码审查与缺陷检测域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "代码生成与补全域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "企业培训与组织学习域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "传媒与新闻域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "信息抽取与结构化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "具身智能与机器人域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "内容分发与社区运营域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "内容改写与风格迁移域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "分类与情感分析域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "参数高效微调域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "可观测性成本与可靠性域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "可解释性与审计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "合成数据生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "合规与监管域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "向量库与检索管线域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与编辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与视觉创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "图像生成与视觉设计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多智能体协同域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多模态大模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多语翻译与本地化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "多轮对话与角色扮演域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "大语言模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "安全与对齐域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "对话与客服域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "对齐与偏好优化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "嵌入与检索表示域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "平台与基础设施域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "建筑与房地产域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "开源与开发者生态域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "强化学习与决策域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推理优化与加速域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推理服务与部署域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "推荐排序与广告域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "提示工程与指令设计域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "提示工程与提示模板域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "搜索与信息聚合域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "摘要与信息压缩域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数字人与虚拟形象域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数学与形式化推理域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据分析与决策支持域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据分析与表格理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据标注与标注质量域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "数据采集与清洗域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文旅与酒店域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文本生成与创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "文档解析与版面理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "智能体与工作流编排域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "智能体框架与工具调用域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "机器翻译与本地化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "模型运营与成本域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "测试与用例生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "游戏与互动娱乐域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "版权与知识产权域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "物流与供应链域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "监督微调域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "知识管理与检索增强域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "知识问答与检索增强域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "科研与实验域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "端侧与边缘小模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "红队越狱与安全测试域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "组合包-受监管行业": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-数据管线": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-检索栈": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "组合包-轻混与保险": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 1.0, "prose_assets": 0, "roles": {"chart": 1, "data": 2, "diagram": 2, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "编辑校对与出版域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视觉模型域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与剪辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与理解域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "视频生成与自动剪辑域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "角色扮演与角色卡域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "记忆体与个性化域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "评测与基准域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "评测基准与排行榜域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音合成与配音域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音识别与合成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "语音转写与会议记录域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "量化金融域包": {"functional": 1, "machine_verifiable": 8, "machine_verifiable_ratio": 0.6667, "prose_assets": 4, "roles": {"chart": 2, "data": 2, "diagram": 1, "functional": 1, "schema": 2}, "tiers": {"T2": 3, "T3": 4, "T4": 1}}, "长文本与小说创作域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "隐私与数据治理域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "零售与电商域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "音频与音乐生成域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "音频音乐与语音域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "预测异常与风险域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}, "预训练与继续预训练域包": {"functional": 1, "machine_verifiable": 10, "machine_verifiable_ratio": 0.7692, "prose_assets": 3, "roles": {"chart": 1, "data": 3, "diagram": 2, "functional": 1, "schema": 3}, "tiers": {"T2": 4, "T3": 5, "T4": 1}}}, "totals": {"functional": 106, "machine_verifiable": 1046, "machine_verifiable_ratio": 0.7742, "prose_assets": 305}}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want), "baseline stats 不一致");
    }
    // <<< GENERATED
}
