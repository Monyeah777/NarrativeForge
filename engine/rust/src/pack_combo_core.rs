//! `pack_combo` 的**判决层**：`combine` / `verify_certificate` / `breadth` / 证书校验 / `scan`。
//!
//! 拆分只为可读；口径与真源逐条对应。索引层见 `pack_combo`。

use crate::pack_combo as pc;
use crate::pyjson::Json;
use crate::pyval;
use std::collections::{BTreeMap, BTreeSet};
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

fn str_list(v: Option<&Json>) -> Vec<String> {
    arr_of(v).iter().map(pyval::plain_str).collect()
}

fn s_of(v: Option<&Json>) -> String {
    match v {
        None | Some(Json::Null) => String::new(),
        Some(x) => pyval::plain_str(x),
    }
}

/// 用到的那几个索引（一次构建、全程共用）。
pub struct Ctx {
    pub prof: Vec<(String, Json)>,
    pub contracts: Vec<(String, Json)>,
    pub by_id: Vec<(String, Json)>,
    pub pub_index: Vec<(String, Vec<Json>)>,
    pub core_pub: BTreeSet<String>,
}

impl Ctx {
    pub fn build(root: &Path, contracts: Vec<(String, Json)>, prof: Vec<(String, Json)>) -> Ctx {
        let (by_id, pub_index, core_pub) = pc::indexes(root, &contracts);
        Ctx { prof, contracts, by_id, pub_index, core_pub }
    }
}

fn find_rec<'a>(v: &'a [(String, Json)], key: &str) -> Option<Json> {
    if let Some((_, r)) = v.iter().find(|(k, _)| k == key) {
        return Some(r.clone());
    }
    let tail = key.rsplit(':').next().unwrap_or(key);
    v.iter().find(|(k, _)| k == tail).map(|(_, r)| r.clone())
}

/// 真源 `combine`。
pub fn combine(
    ctx: &Ctx,
    packs: &[String],
    extra_modules: &[String],
    extra_assets: &[String],
) -> Json {
    let mut unknown: Vec<String> = Vec::new();
    let mut chosen: Vec<Json> = Vec::new();
    for p in packs {
        match ctx.prof.iter().find(|(k, _)| k == p) {
            Some((_, r)) => chosen.push(r.clone()),
            None => unknown.push(p.clone()),
        }
    }
    let mut mods: Vec<(String, Json)> = Vec::new();
    for pr in &chosen {
        for rec in arr_of(obj_get(pr, "module_recs")) {
            let id = s_of(obj_get(&rec, "id"));
            match mods.iter_mut().find(|(k, _)| *k == id) {
                Some(slot) => slot.1 = rec,
                None => mods.push((id, rec)),
            }
        }
    }
    for mid in extra_modules {
        if let Some(rec) = find_rec(&ctx.contracts, mid) {
            let id = s_of(obj_get(&rec, "id"));
            match mods.iter_mut().find(|(k, _)| *k == id) {
                Some(slot) => slot.1 = rec,
                None => mods.push((id, rec)),
            }
        }
    }
    let mut borrowed: Vec<Json> = Vec::new();
    let mut unresolved_refs: Vec<Json> = Vec::new();

    for pr in &chosen {
        for r in arr_of(obj_get(pr, "references")) {
            let src = s_of(obj_get(&r, "source_package"));
            let mid = s_of(obj_get(&r, "module_id"));
            match find_rec(&ctx.contracts, &mid) {
                Some(rec) => {
                    let id = s_of(obj_get(&rec, "id"));
                    if mods.iter().any(|(k, _)| *k == id) {
                        continue;
                    }
                    let rec_pack = s_of(obj_get(&rec, "pack"));
                    mods.push((id.clone(), rec));
                    if rec_pack == src {
                        borrowed.push(Json::Object(vec![
                            ("module".to_string(), Json::Str(id)),
                            ("from".to_string(), Json::Str(src.clone())),
                            ("by".to_string(), Json::Str(s_of(obj_get(pr, "package")))),
                            ("mode".to_string(), Json::Str("module_borrow".to_string())),
                        ]));
                    } else {
                        borrowed.push(Json::Object(vec![
                            ("module".to_string(), Json::Str(id)),
                            ("from".to_string(), Json::Str(rec_pack)),
                            ("by".to_string(), Json::Str(s_of(obj_get(pr, "package")))),
                            ("mode".to_string(), Json::Str("module_borrow".to_string())),
                        ]));
                    }
                }
                None => unresolved_refs.push(Json::Object(vec![
                    ("by".to_string(), Json::Str(s_of(obj_get(pr, "package")))),
                    ("source_package".to_string(), Json::Str(src)),
                    ("module_id".to_string(), Json::Str(mid)),
                ])),
            }
        }
    }

    // 不动点闭包：依赖 inputs ∪ 事件发布方（递归），直到不再新增
    let core = pc::core_ids();
    for _round in 0..12 {
        let mut grew = false;
        let snapshot: Vec<(String, Json)> = mods.clone();
        for (m, r) in &snapshot {
            for dep in str_list(obj_get(r, "inputs")) {
                let tail = dep.rsplit(':').next().unwrap_or(&dep).to_string();
                if core.contains(&dep) || core.contains(&tail) || mods.iter().any(|(k, _)| *k == dep)
                {
                    continue;
                }
                if let Some(rec) = find_rec(&ctx.by_id, &dep) {
                    let id = s_of(obj_get(&rec, "id"));
                    if !mods.iter().any(|(k, _)| *k == id) {
                        // 真源 `_add(rec, why, by)`：`from = rec["pack"]`，`by = by or "<组件级>"`
                        // ⚠️ 必须在 `mods.push` **之前**取 pack —— push 会把 rec 移走。
                        let from_pack = s_of(obj_get(&rec, "pack"));
                        mods.push((id.clone(), rec));
                        let by = if m.is_empty() { "<组件级>".to_string() } else { m.clone() };
                        borrowed.push(Json::Object(vec![
                            ("module".to_string(), Json::Str(id)),
                            ("from".to_string(), Json::Str(from_pack)),
                            ("by".to_string(), Json::Str(by)),
                            ("mode".to_string(), Json::Str("closure_pull".to_string())),
                            ("why".to_string(), Json::Str(format!("依赖 {} 的 inputs 需要 {}", m, dep))),
                        ]));
                        grew = true;
                    }
                }
            }
        }
        let mut published_now: BTreeSet<String> = ctx.core_pub.clone();
        for (_, x) in &mods {
            for e in str_list(obj_get(x, "publish")) {
                published_now.insert(e);
            }
        }
        let snapshot2: Vec<(String, Json)> = mods.clone();
        for (m, r) in &snapshot2 {
            for ev in str_list(obj_get(r, "subscribe")) {
                if published_now.contains(&ev) {
                    continue;
                }
                let Some(recs) = ctx.pub_index.iter().find(|(k, _)| *k == ev).map(|(_, v)| v.clone())
                else {
                    continue;
                };
                for rec in recs {
                    let id = s_of(obj_get(&rec, "id"));
                    if !mods.iter().any(|(k, _)| *k == id) {
                        let from_pack = s_of(obj_get(&rec, "pack"));
                        mods.push((id.clone(), rec));
                        let by = if m.is_empty() { "<组件级>".to_string() } else { m.clone() };
                        borrowed.push(Json::Object(vec![
                            ("module".to_string(), Json::Str(id)),
                            ("from".to_string(), Json::Str(from_pack)),
                            ("by".to_string(), Json::Str(by)),
                            ("mode".to_string(), Json::Str("closure_pull".to_string())),
                            ("why".to_string(), Json::Str(format!("事件 {} 需要发布方（{} 订阅）", ev, m))),
                        ]));
                        grew = true;
                    }
                }
            }
        }
        if !grew {
            break;
        }
    }

    let mut missing_contracts: Vec<String> = mods
        .iter()
        .filter(|(_, r)| s_of(obj_get(r, "path")).is_empty())
        .map(|(k, _)| k.clone())
        .collect();
    missing_contracts.sort();
    let mut sorted_mods = mods.clone();
    sorted_mods.sort_by(|a, b| a.0.cmp(&b.0));
    let mut dangling: Vec<Json> = Vec::new();
    for (m, r) in &sorted_mods {
        for dep in str_list(obj_get(r, "inputs")) {
            let tail = dep.rsplit(':').next().unwrap_or(&dep).to_string();
            if core.contains(&dep) || core.contains(&tail) || mods.iter().any(|(k, _)| *k == dep) {
                continue;
            }
            dangling.push(Json::Object(vec![
                ("module".to_string(), Json::Str(m.clone())),
                ("needs".to_string(), Json::Str(dep)),
            ]));
        }
    }
    let mut published: BTreeSet<String> = BTreeSet::new();
    for (_, r) in &mods {
        for e in str_list(obj_get(r, "publish")) {
            published.insert(e);
        }
    }
    for e in &ctx.core_pub {
        published.insert(e.clone());
    }
    let mut unbridged: Vec<String> = BTreeSet::from_iter(
        mods.iter()
            .flat_map(|(_, r)| str_list(obj_get(r, "subscribe")))
            .filter(|e| !published.contains(e)),
    )
    .into_iter()
    .collect();
    unbridged.sort();
    let mut unpublished: Vec<String> = BTreeSet::from_iter(
        mods.iter()
            .flat_map(|(_, r)| str_list(obj_get(r, "subscribe")))
            .filter(|e| !published.contains(e) && !ctx.pub_index.iter().any(|(k, _)| k == e)),
    )
    .into_iter()
    .collect();
    unpublished.sort();

    let mut canon_packs: Vec<String> = packs.to_vec();
    canon_packs.sort();
    canon_packs.dedup();
    let order: BTreeMap<String, usize> =
        canon_packs.iter().enumerate().map(|(i, p)| (p.clone(), i)).collect();
    let mut stacks: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for pr in &chosen {
        if let Some(Json::Object(ls)) = obj_get(pr, "layers") {
            for (lay, ms) in ls {
                let entry = stacks.entry(lay.clone()).or_default();
                for m in arr_of(Some(ms)).iter().map(pyval::plain_str) {
                    if !entry.contains(&m) {
                        entry.push(m);
                    }
                }
            }
        }
    }
    for (m, r) in &sorted_mods {
        let lay = s_of(obj_get(r, "layer"));
        if !lay.is_empty() {
            let entry = stacks.entry(lay).or_default();
            if !entry.contains(m) {
                entry.push(m.clone());
            }
        }
    }
    let mut stacks2: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for (k, v) in &stacks {
        let mut uniq: Vec<String> = v.clone();
        uniq.sort();
        uniq.dedup();
        uniq.sort_by_key(|x| {
            let pack = mods
                .iter()
                .find(|(kk, _)| kk == x)
                .map(|(_, r)| s_of(obj_get(r, "pack")))
                .unwrap_or_default();
            (order.get(&pack).copied().unwrap_or(99), x.clone())
        });
        stacks2.insert(k.clone(), uniq);
    }
    let stack_list: Vec<Json> = stacks2
        .iter()
        .map(|(k, v)| {
            Json::Object(vec![
                ("layer".to_string(), Json::Str(k.clone())),
                ("modules".to_string(), Json::Array(v.iter().map(|s| Json::Str(s.clone())).collect())),
            ])
        })
        .collect();

    // 资产：借阅面
    let mut asset_index: Vec<((String, String), Json)> = Vec::new();
    for (pn, pr) in &ctx.prof {
        for a in arr_of(obj_get(pr, "assets")) {
            asset_index.push(((pn.clone(), s_of(obj_get(&a, "key"))), a.clone()));
        }
    }
    let mut borrow: Vec<Json> = Vec::new();
    let mut unresolved: Vec<String> = Vec::new();
    for pr in &chosen {
        for a in arr_of(obj_get(pr, "assets")) {
            let m = s_of(obj_get(&a, "module"));
            if !m.is_empty() && !mods.iter().any(|(k, _)| *k == m) {
                borrow.push(Json::Object(vec![
                    ("key".to_string(), Json::Str(s_of(obj_get(&a, "key")))),
                    ("from".to_string(), Json::Str(s_of(obj_get(pr, "package")))),
                    ("for_module".to_string(), Json::Str(m)),
                    ("mode".to_string(), Json::Str("asset_readonly".to_string())),
                ]));
            }
        }
    }
    for spec in extra_assets {
        let (pkg, key) = match spec.split_once(':') {
            Some((a, b)) => (a.to_string(), b.to_string()),
            None => (spec.clone(), String::new()),
        };
        if asset_index.iter().any(|((p, k), _)| *p == pkg && *k == key) {
            borrow.push(Json::Object(vec![
                ("key".to_string(), Json::Str(key)),
                ("from".to_string(), Json::Str(pkg)),
                ("for_module".to_string(), Json::Str(String::new())),
                ("mode".to_string(), Json::Str("asset_readonly".to_string())),
            ]));
        } else {
            unresolved.push(spec.clone());
        }
    }
    let mut borrow_sorted = borrow.clone();
    borrow_sorted.sort_by_key(|x| (s_of(obj_get(x, "from")), s_of(obj_get(x, "key"))));
    let mut borrowed_sorted = borrowed.clone();
    borrowed_sorted.sort_by_key(|x| (s_of(obj_get(x, "by")), s_of(obj_get(x, "module"))));
    let mut refs_sorted = unresolved_refs.clone();
    refs_sorted.sort_by_key(|x| (s_of(obj_get(x, "by")), s_of(obj_get(x, "module_id"))));
    unresolved.sort();
    let mut unknown_sorted = unknown.clone();
    unknown_sorted.sort();

    let explicit: Vec<String> = BTreeSet::from_iter(
        mods.iter()
            .flat_map(|(_, r)| str_list(obj_get(r, "inputs")))
            .filter(|d| mods.iter().any(|(k, _)| k == d)),
    )
    .into_iter()
    .collect();
    let mut core_list: Vec<String> = core.iter().cloned().collect();
    core_list.sort();
    let mut extra_sorted: Vec<String> = extra_modules.to_vec();
    extra_sorted.sort();
    extra_sorted.dedup();
    let mut mod_ids: Vec<String> = mods.iter().map(|(k, _)| k.clone()).collect();
    mod_ids.sort();

    let mut cert = Json::Object(vec![
        ("schema".to_string(), Json::Str("nf-combo/1".to_string())),
        ("packs".to_string(), str_json(&canon_packs)),
        ("unknown_packs".to_string(), str_json(&unknown_sorted)),
        ("extra_modules".to_string(), str_json(&extra_sorted)),
        ("modules".to_string(), str_json(&mod_ids)),
        ("module_count".to_string(), Json::Int(mods.len() as i64)),
        ("layer_stacks".to_string(), Json::Array(stack_list)),
        (
            "dependency_closure".to_string(),
            Json::Object(vec![
                ("core".to_string(), str_json(&core_list)),
                ("explicit".to_string(), str_json(&explicit)),
                ("dangling".to_string(), Json::Array(dangling.clone())),
            ]),
        ),
        (
            "event_closure".to_string(),
            Json::Object(vec![
                (
                    "published".to_string(),
                    str_json(&published.iter().cloned().collect::<Vec<_>>()),
                ),
                ("unbridged".to_string(), str_json(&unbridged)),
            ]),
        ),
        ("events_unpublished".to_string(), str_json(&unpublished)),
        ("assets_borrowed".to_string(), Json::Array(borrow_sorted)),
        ("modules_borrowed".to_string(), Json::Array(borrowed_sorted)),
        ("references_unresolved".to_string(), Json::Array(refs_sorted)),
        ("assets_unresolved".to_string(), str_json(&unresolved)),
        ("module_missing_contract".to_string(), str_json(&missing_contracts)),
    ]);
    let legal = unknown.is_empty()
        && dangling.is_empty()
        && unbridged.is_empty()
        && missing_contracts.is_empty()
        && unresolved.is_empty()
        && unresolved_refs.is_empty();
    if let Json::Object(o) = &mut cert {
        o.push(("legal".to_string(), Json::Bool(legal)));
    }
    let dg = pc::digest_of_cert(&cert);
    if let Json::Object(o) = &mut cert {
        o.push(("digest".to_string(), Json::Str(dg)));
    }
    cert
}

fn str_json(v: &[String]) -> Json {
    Json::Array(v.iter().map(|s| Json::Str(s.clone())).collect())
}

/// 真源 `verify_certificate`。
pub fn verify_certificate(ctx: &Ctx, cert: &Json) -> (Vec<String>, Json) {
    let fresh = combine(
        ctx,
        &str_list(obj_get(cert, "packs")),
        &str_list(obj_get(cert, "extra_modules")),
        &[],
    );
    let mut issues: Vec<String> = Vec::new();
    for key in [
        "modules",
        "module_count",
        "layer_stacks",
        "dependency_closure",
        "event_closure",
        "assets_borrowed",
        "modules_borrowed",
        "legal",
        "digest",
    ] {
        let a = obj_get(&fresh, key).cloned().unwrap_or(Json::Null);
        let b = obj_get(cert, key).cloned().unwrap_or(Json::Null);
        if !crate::jsonread::json_eq(&a, &b) {
            issues.push(format!(
                "字段不一致：{}（复算 {} ≠ 在盘 {}）",
                key,
                pyval::py_repr(&a),
                pyval::py_repr(&b)
            ));
        }
    }
    (
        issues,
        Json::Object(vec![
            ("legal".to_string(), obj_get(&fresh, "legal").cloned().unwrap_or(Json::Null)),
            ("modules".to_string(), obj_get(&fresh, "module_count").cloned().unwrap_or(Json::Null)),
        ]),
    )
}

/// 真源 `breadth`（抽样器见 `pyrandom`，已单独判据钉住）。
pub fn breadth(
    root: &Path,
    ctx: &Ctx,
    triple_sample: usize,
    quad_sample: usize,
    quint_sample: usize,
    sext_sample: usize,
    seed: u64,
) -> Json {
    let verdict = |names: &[String]| -> (bool, Vec<Json>, Vec<Json>) {
        let cert = combine(ctx, names, &[], &[]);
        let legal = matches!(obj_get(&cert, "legal"), Some(Json::Bool(true)));
        let dangling = arr_of(obj_get(&cert, "dependency_closure").and_then(|d| obj_get(d, "dangling")))
            .into_iter()
            .take(2)
            .collect();
        let unbridged = arr_of(obj_get(&cert, "event_closure").and_then(|d| obj_get(d, "unbridged")))
            .into_iter()
            .take(2)
            .collect();
        (legal, dangling, unbridged)
    };
    let mut names: Vec<String> = ctx.prof.iter().map(|(k, _)| k.clone()).collect();
    names.sort();
    let (mut pairs, mut pairs_legal) = (0i64, 0i64);
    let mut failures: Vec<Json> = Vec::new();
    for i in 0..names.len() {
        for j in (i + 1)..names.len() {
            let combo = vec![names[i].clone(), names[j].clone()];
            let (legal, dangling, unbridged) = verdict(&combo);
            pairs += 1;
            if legal {
                pairs_legal += 1;
            } else if failures.len() < 10 {
                failures.push(Json::Object(vec![
                    ("combo".to_string(), str_json(&combo)),
                    ("dangling".to_string(), Json::Array(dangling)),
                    ("unbridged".to_string(), Json::Array(unbridged)),
                ]));
            }
        }
    }
    let _ = root;
    let mut rnd = crate::pyrandom::PyRandom::new(seed);
    let draw = |r: &mut crate::pyrandom::PyRandom, size: usize, want: usize| -> Vec<Vec<String>> {
        let mut picks: BTreeSet<Vec<String>> = BTreeSet::new();
        if names.len() >= size {
            while picks.len() < std::cmp::min(want, 5000) {
                let mut s = r.sample(&names, size);
                s.sort();
                picks.insert(s);
            }
        }
        picks.into_iter().collect()
    };
    let (mut triples, mut triples_legal) = (0i64, 0i64);
    for t in draw(&mut rnd, 3, triple_sample) {
        let (legal, _, _) = verdict(&t);
        triples += 1;
        if legal {
            triples_legal += 1;
        }
    }
    let (mut quads, mut quads_legal) = (0i64, 0i64);
    for q in draw(&mut rnd, 4, quad_sample) {
        let (legal, _, _) = verdict(&q);
        quads += 1;
        if legal {
            quads_legal += 1;
        }
    }
    let (mut quints, mut quints_legal) = (0i64, 0i64);
    for p in draw(&mut rnd, 5, quint_sample) {
        let (legal, _, _) = verdict(&p);
        quints += 1;
        if legal {
            quints_legal += 1;
        }
    }
    let (mut sexts, mut sexts_legal) = (0i64, 0i64);
    for p in draw(&mut rnd, 6, sext_sample) {
        let (legal, dangling, unbridged) = verdict(&p);
        sexts += 1;
        if legal {
            sexts_legal += 1;
        } else if failures.len() < 10 {
            failures.push(Json::Object(vec![
                ("combo".to_string(), str_json(&p)),
                ("dangling".to_string(), Json::Array(dangling)),
                ("unbridged".to_string(), Json::Array(unbridged)),
            ]));
        }
    }
    let all_legal = pairs == pairs_legal
        && triples == triples_legal
        && quads == quads_legal
        && quints == quints_legal
        && sexts == sexts_legal;
    Json::Object(vec![
        ("packs".to_string(), Json::Int(names.len() as i64)),
        ("pairs".to_string(), Json::Int(pairs)),
        ("pairs_legal".to_string(), Json::Int(pairs_legal)),
        ("triples".to_string(), Json::Int(triples)),
        ("triples_legal".to_string(), Json::Int(triples_legal)),
        ("quads".to_string(), Json::Int(quads)),
        ("quads_legal".to_string(), Json::Int(quads_legal)),
        ("quints".to_string(), Json::Int(quints)),
        ("quints_legal".to_string(), Json::Int(quints_legal)),
        ("sexts".to_string(), Json::Int(sexts)),
        ("sexts_legal".to_string(), Json::Int(sexts_legal)),
        ("failures".to_string(), Json::Array(failures)),
        ("all_legal".to_string(), Json::Bool(all_legal)),
    ])
}

/// 真源 `declared`。
pub fn declared(root: &Path) -> Json {
    let text = std::fs::read_to_string(root.join(crate::output_tables::CERT_REL));
    match text.ok().and_then(|t| crate::jsonmini::parse(&t).ok().map(|r| r.value)) {
        Some(v) => v,
        None => Json::Object(vec![
            ("schema".to_string(), Json::Str("nf-combo-certificates/1".to_string())),
            ("certificates".to_string(), Json::Array(vec![])),
        ]),
    }
}

/// 真源 `_certificate_lines`（缓存层不移植）。
pub fn certificate_lines(ctx: &Ctx, cert: &Json) -> Vec<String> {
    let schema = crate::jsonmini::parse(crate::output_tables::CERT_SCHEMA_JSON)
        .map(|r| r.value)
        .unwrap_or(Json::Object(vec![]));
    let schema_errs = crate::json_schema::json_schema_check(cert, &schema);
    let (sub, _st) = verify_certificate(ctx, cert);
    let name = {
        let l = s_of(obj_get(cert, "label"));
        if !l.is_empty() {
            l
        } else {
            let joined = str_list(obj_get(cert, "packs")).join("+");
            if joined.is_empty() {
                "<空>".to_string()
            } else {
                joined
            }
        }
    };
    let mut out: Vec<String> = schema_errs
        .iter()
        .take(4)
        .map(|e| format!("组合 {}: 证书不合 schema: {}", name, e))
        .collect();
    out.extend(sub.into_iter().map(|s| format!("组合 {}: {}", name, s)));
    out
}

/// 真源 `scan` → `(issues, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let doc = declared(root);
    let certs = arr_of(obj_get(&doc, "certificates"));
    let contracts = pc::module_contracts(root);
    let prof = pc::profiles(root);
    let ctx = Ctx::build(root, contracts.clone(), prof.clone());
    let witness = pc::combo_witness(&prof, &contracts, &(ctx.by_id.clone(), ctx.pub_index.clone(), ctx.core_pub.clone()));
    let _ = witness;
    for cert in &certs {
        issues.extend(certificate_lines(&ctx, cert));
    }
    let br = breadth(root, &ctx, 400, 200, 120, 60, 20260923);
    let all_legal = matches!(obj_get(&br, "all_legal"), Some(Json::Bool(true)));
    if !all_legal {
        let g = |k: &str| pyval::py_int_or(obj_get(&br, k), 0);
        issues.push(format!(
            "广度证明不成立：两两 {}/{} · 三元 {}/{} · 四元 {}/{} · 五元 {}/{} · 六元 {}/{}（样本 {}）",
            g("pairs_legal"),
            g("pairs"),
            g("triples_legal"),
            g("triples"),
            g("quads_legal"),
            g("quads"),
            g("quints_legal"),
            g("quints"),
            g("sexts_legal"),
            g("sexts"),
            pyval::py_repr_list(&arr_of(obj_get(&br, "failures")).into_iter().take(2).collect::<Vec<_>>())
        ));
    }
    (
        issues,
        Json::Object(vec![
            ("declared_certificates".to_string(), Json::Int(certs.len() as i64)),
            ("breadth".to_string(), br),
        ]),
    )
}


/// 真源 `pack_combo.prof_get_module`：按 id（或末段）取模块记录。
pub fn prof_get_module(root: &Path, module_id: &str) -> Json {
    let contracts = pc::module_contracts(root);
    let (by_id, _pub, _core) = pc::indexes(root, &contracts);
    let mut hit = by_id.iter().find(|(k, _)| k == module_id).map(|(_, v)| v.clone());
    if hit.is_none() {
        let tail = module_id.rsplit(':').next().unwrap_or(module_id);
        hit = by_id.iter().find(|(k, _)| k == tail).map(|(_, v)| v.clone());
    }
    hit.unwrap_or(Json::Object(vec![]))
}

/// 真源 `pack_combo.combine(root, packs=..., extra_modules=..., extra_assets=...)` 的一次性入口。
///
/// 索引每次重建（真源用 `_CACHE` 兜住）。**只在少量调用点用**：`breadth` 里 6,900 次组合必须
/// 共用一份 `Ctx`，否则慢到不可用——见 `Ctx::build`。
pub fn combine_fresh(
    root: &Path,
    packs: &[String],
    extra_modules: &[String],
    extra_assets: &[String],
) -> Json {
    let contracts = pc::module_contracts(root);
    let prof = pc::profiles(root);
    let ctx = Ctx::build(root, contracts, prof);
    combine(&ctx, packs, extra_modules, extra_assets)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pack_combo_matches_truth_source() {
        let root = crate::testutil::repo_root();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, &[] as &[&str], "issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"breadth": {"all_legal": true, "failures": [], "packs": 111, "pairs": 6105, "pairs_legal": 6105, "quads": 200, "quads_legal": 200, "quints": 120, "quints_legal": 120, "sexts": 60, "sexts_legal": 60, "triples": 400, "triples_legal": 400}, "declared_certificates": 18}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want),
                "stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
    }
    // <<< GENERATED
}
