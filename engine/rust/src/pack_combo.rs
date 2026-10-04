//! 组合包（combo）**证书复算 + 广度证明** —— 与真源 `desktop/src/core/pack_combo.py` 的 `scan` 对账。
//!
//! ## 移植面按消费者界定（有工具）
//!
//! 真源 1,268 行；从入口 `scan` 算调用闭包得 **25 个函数 / 约 602 行**，其中还有三项是**纯缓存**
//! （`_cache_key` / `_inputs_fingerprint` / `_verdict_cached` 的缓存层）——缓存只决定"要不要重算"，
//! **不改结论** ⇒ 不移植。移植的是判据与它依赖的索引层。
//!
//! ## 两处必须对齐的语义
//!
//! 1. **抽样器**：`breadth` 用 `random.Random(seed).sample(...)` 抽三/四/五/六元样，样本**进判据与
//!    stats** ⇒ 逐位复刻 CPython（见 `pyrandom`，已单独判据钉住）。
//! 2. **组合判决的耦合面**：`combine` 会经 `by_id` 拉入**任意第三方包**的模块、经 `pub_index` 拉入
//!    **任意发布方**（事件闭包）⇒ 索引必须**全局**构建一次、全程共用（真源的 `_CACHE` 同理）。
//!    本线把它做成**显式参数**，避免 6,900 次组合各重解析 235 份契约（那会慢到不可用）。
//!
//! `write` 面（`materialize` / `_write_*`）与 `cache_clear` 不移植。

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

fn read_json_opt(root: &Path, rel: &str) -> Option<Json> {
    let text = std::fs::read_to_string(root.join(rel)).ok()?;
    crate::jsonmini::parse(&text).ok().map(|r| r.value)
}

/// 真源 `_core_ids()`。
pub fn core_ids() -> BTreeSet<String> {
    let mut out: BTreeSet<String> = crate::output_tables::CORE13.iter().map(|s| s.to_string()).collect();
    for x in crate::output_tables::CORE13 {
        out.insert(x.rsplit(':').next().unwrap_or(x).to_string());
    }
    out
}

/// 真源 `_pack_dirs`：有 `community/<包>/protocol.yaml` 的包名（有序）。
pub fn pack_dirs(root: &Path) -> Vec<String> {
    let mut v = crate::glob::expand(root, "community/*/protocol.yaml");
    v.sort();
    let mut out: Vec<String> = Vec::new();
    for rel in v {
        if let Some(pkg) = rel.split('/').nth(1) {
            if !out.contains(&pkg.to_string()) {
                out.push(pkg.to_string());
            }
        }
    }
    out
}

/// 真源 `_parse_protocol` 的结果。
#[derive(Clone, Debug, Default)]
pub struct Proto {
    pub id: String,
    pub pipeline: String,
    pub module_ids: Vec<String>,
    pub mount_layers: BTreeMap<String, Vec<String>>,
    pub references: Vec<(String, String)>,
}

/// 真源 `_parse_protocol`。
pub fn parse_protocol(path: &Path) -> Proto {
    let text = std::fs::read(path).map(|b| String::from_utf8_lossy(&b).into_owned()).unwrap_or_default();
    let dir = path
        .parent()
        .and_then(|p| p.file_name())
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    let mut out = Proto::default();
    let re_id = regex::Regex::new(r"(?m)^\s*id:\s*(\S+)\s*$").expect("固定合法");
    out.id = re_id
        .captures(&text)
        .map(|c| c[1].to_string())
        .unwrap_or_else(|| dir.clone());
    let re_pipe = regex::Regex::new(r"(?m)^\s*pipeline:\s*(P\d{2,3})\s*$").expect("固定合法");
    out.pipeline = re_pipe.captures(&text).map(|c| c[1].to_string()).unwrap_or_default();
    // 行式清单：全限定与裸号两种写法并集（保持出现序、去重）
    let mut ids: Vec<String> = Vec::new();
    let re_full = regex::Regex::new(r#"(?m)^\s*-\s*"([^"]+:M\d{2,3})"\s*(?:#.*)?$"#).expect("固定合法");
    for c in re_full.captures_iter(&text) {
        let v = c[1].to_string();
        if !ids.contains(&v) {
            ids.push(v);
        }
    }
    let re_bare = regex::Regex::new(r#"(?m)^\s*-\s*"?(M\d{2,3})"?\s*(?:#.*)?$"#).expect("固定合法");
    for c in re_bare.captures_iter(&text) {
        let v = c[1].to_string();
        if !ids.contains(&v) {
            ids.push(v);
        }
    }
    if ids.is_empty() {
        let re_flow = regex::Regex::new(r"(?m)^\s*module_id_range\s*:\s*\[([^\]]*)\]").expect("固定合法");
        if let Some(c) = re_flow.captures(&text) {
            for x in c[1].split(',') {
                let v = x.trim().trim_matches(|ch| ch == '\'' || ch == '"').to_string();
                if !v.is_empty() {
                    ids.push(v);
                }
            }
        }
    }
    out.module_ids = ids;
    let re_layer =
        regex::Regex::new(r"(?m)^\s*(P\d{2})\s*[^:]*:\s*\{default:\s*\[([^\]]*)\]").expect("固定合法");
    for c in re_layer.captures_iter(&text) {
        let mods: Vec<String> = c[2]
            .split(',')
            .map(|x| x.trim().trim_matches(|ch| ch == '\'' || ch == '"').to_string())
            .filter(|x| !x.is_empty())
            .collect();
        if !mods.is_empty() {
            out.mount_layers.insert(c[1].to_string(), mods);
        }
    }
    let re_ref = regex::Regex::new(r"(?ms)^\s*-\s*source_package:\s*(\S+)\s*\n\s*module_id:\s*(\S+)")
        .expect("固定合法");
    for c in re_ref.captures_iter(&text) {
        out.references.push((
            c[1].trim_matches(|ch| ch == '\'' || ch == '"').to_string(),
            c[2].trim_matches(|ch| ch == '\'' || ch == '"').to_string(),
        ));
    }
    out
}

/// 真源 `_face_paths`：按模式枚举（**有序**）。
///
/// ⚠️ **必须排序**：真源走 `csc.iter_files`（已排序），而 `_module_contracts` 的
/// 「同一键**首次胜**」语义**依赖枚举序**——不排序时 `M01` 这类裸号会解析到**别的包**的模块。
/// 实测（2026-10-04）：`校园情感领域包 + 西幻生存领域包` 的 `modules` 因此从 23 条裸号
/// 变成 23 条跨包全限定号，整张证书对不上。
fn face_paths(root: &Path, pattern: &str) -> Vec<String> {
    let mut v = crate::glob::expand(root, pattern);
    v.sort();
    v
}

/// 真源 `_module_contracts`：`{可查键: 契约摘要}`（id / stem / id 末段三种键，首次胜）。
pub fn module_contracts(root: &Path) -> Vec<(String, Json)> {
    let mut out: Vec<(String, Json)> = Vec::new();
    for rel in face_paths(root, "community/*/modules/*.md") {
        let text = match std::fs::read(root.join(&rel)) {
            Ok(b) => String::from_utf8_lossy(&b).into_owned(),
            Err(_) => continue,
        };
        let parsed = match crate::miniyaml::fence_yaml(&text, "machine_contract") {
            Some(p) => p,
            None => continue,
        };
        let mc = obj_get(&parsed, "machine_contract").cloned().unwrap_or(Json::Object(vec![]));
        if !matches!(mc, Json::Object(_)) || matches!(&mc, Json::Object(o) if o.is_empty()) {
            continue;
        }
        let stem = rel
            .rsplit('/')
            .next()
            .unwrap_or("")
            .split('_')
            .next()
            .unwrap_or("")
            .to_string();
        let pack = rel.split('/').nth(1).unwrap_or("").to_string();
        let id = {
            let v = s_of(obj_get(&mc, "id"));
            if v.is_empty() {
                stem.clone()
            } else {
                v
            }
        };
        let events = obj_get(&mc, "events").cloned().unwrap_or(Json::Object(vec![]));
        let rec = Json::Object(vec![
            ("id".to_string(), Json::Str(id.clone())),
            ("stem".to_string(), Json::Str(stem.clone())),
            ("pack".to_string(), Json::Str(pack)),
            ("layer".to_string(), Json::Str(s_of(obj_get(&mc, "layer")))),
            ("inputs".to_string(), str_json(&str_list(obj_get(&mc, "inputs")))),
            ("outputs".to_string(), str_json(&str_list(obj_get(&mc, "outputs")))),
            ("publish".to_string(), str_json(&str_list(obj_get(&events, "publish")))),
            ("subscribe".to_string(), str_json(&str_list(obj_get(&events, "subscribe")))),
            ("path".to_string(), Json::Str(rel.clone())),
        ]);
        // ⚠️ 三个键的语义**不同**（真源是 `out[id] = rec` + 两次 `setdefault`）：
        //   · `id` 键 = **赋值（覆盖）**；`stem` / 末段 = **首次胜**。
        // 把 id 键也写成"首次胜"会**挡住后来者的赋值**：实测（2026-10-04）
        // `community/西幻生存领域包/modules/M01_职业成长.md` 的 `id` 恰是裸号 `M01`，而 AI 包
        // 那份记录（`id: AI人力资源与招聘:M01`）已先把**末段键** `M01` setdefault 掉了
        // ⇒ 真源里裸记录**覆盖**它（`M01 → M01`），本线却保留了 AI 记录
        // ⇒ `profiles` 里 111 个包的 `module_recs` 连带错位，组合证书整张对不上。
        match out.iter_mut().find(|(k, _)| *k == id) {
            Some(slot) => slot.1 = rec.clone(),
            None => out.push((id.clone(), rec.clone())),
        }
        if !out.iter().any(|(k, _)| *k == stem) {
            out.push((stem.clone(), rec.clone()));
        }
        let tail = id.rsplit(':').next().unwrap_or(&id).to_string();
        if !out.iter().any(|(k, _)| *k == tail) {
            out.push((tail, rec));
        }
    }
    out
}

fn str_json(v: &[String]) -> Json {
    Json::Array(v.iter().map(|s| Json::Str(s.clone())).collect())
}

/// 真源 `_core_contracts`。
pub fn core_contracts(root: &Path) -> Vec<(String, Json)> {
    let mut out: Vec<(String, Json)> = Vec::new();
    for rel in face_paths(root, "04_模块库/*/*.md") {
        let text = match std::fs::read(root.join(&rel)) {
            Ok(b) => String::from_utf8_lossy(&b).into_owned(),
            Err(_) => continue,
        };
        let parsed = match crate::miniyaml::fence_yaml(&text, "machine_contract") {
            Some(p) => p,
            None => continue,
        };
        let mc = obj_get(&parsed, "machine_contract").cloned().unwrap_or(Json::Object(vec![]));
        if !matches!(mc, Json::Object(_)) || matches!(&mc, Json::Object(o) if o.is_empty()) {
            continue;
        }
        let stem = rel
            .rsplit('/')
            .next()
            .unwrap_or("")
            .split('_')
            .next()
            .unwrap_or("")
            .to_string();
        let id = {
            let v = s_of(obj_get(&mc, "id"));
            if v.is_empty() {
                stem.clone()
            } else {
                v
            }
        };
        let events = obj_get(&mc, "events").cloned().unwrap_or(Json::Object(vec![]));
        let rec = Json::Object(vec![
            ("id".to_string(), Json::Str(id.clone())),
            ("stem".to_string(), Json::Str(stem.clone())),
            ("publish".to_string(), str_json(&str_list(obj_get(&events, "publish")))),
            ("subscribe".to_string(), str_json(&str_list(obj_get(&events, "subscribe")))),
            ("path".to_string(), Json::Str(rel.clone())),
        ]);
        if !out.iter().any(|(k, _)| *k == id) {
            out.push((id, rec.clone()));
        }
        if !out.iter().any(|(k, _)| *k == stem) {
            out.push((stem, rec));
        }
    }
    out
}

/// 真源 `_pack_assets`。
fn pack_assets(root: &Path, pkg_dir: &str) -> Vec<Json> {
    let doc = read_json_opt(root, &format!("community/{}/assets/provenance.json", pkg_dir))
        .unwrap_or(Json::Object(vec![]));
    arr_of(obj_get(&doc, "assets"))
        .iter()
        .map(|a| {
            Json::Object(vec![
                ("key".to_string(), Json::Str(s_of(obj_get(a, "key")))),
                ("file".to_string(), Json::Str(s_of(obj_get(a, "file")))),
                ("module".to_string(), Json::Str(s_of(obj_get(a, "module")))),
                ("source_package".to_string(), Json::Str(pkg_dir.to_string())),
            ])
        })
        .collect()
}

/// 真源 `profiles`：每个包的组合画像（**不移植两层缓存**——缓存只决定要不要重算）。
pub fn profiles(root: &Path) -> Vec<(String, Json)> {
    let contracts = module_contracts(root);
    let mut out: Vec<(String, Json)> = Vec::new();
    for d in pack_dirs(root) {
        let proto = parse_protocol(&root.join("community").join(&d).join("protocol.yaml"));
        let mut own: Vec<Json> = Vec::new();
        for mid in &proto.module_ids {
            let rec = contracts.iter().find(|(k, _)| k == mid).map(|(_, v)| v.clone()).or_else(|| {
                let tail = mid.rsplit(':').next().unwrap_or(mid);
                contracts.iter().find(|(k, _)| k == tail).map(|(_, v)| v.clone())
            });
            own.push(rec.unwrap_or_else(|| {
                Json::Object(vec![
                    ("id".to_string(), Json::Str(mid.clone())),
                    ("layer".to_string(), Json::Str(String::new())),
                    ("inputs".to_string(), Json::Array(vec![])),
                    ("publish".to_string(), Json::Array(vec![])),
                    ("subscribe".to_string(), Json::Array(vec![])),
                    ("pack".to_string(), Json::Str(proto.id.clone())),
                ])
            }));
        }
        let mut layers: Vec<(String, Vec<String>)> = Vec::new();
        for rec in &own {
            let lay = s_of(obj_get(rec, "layer"));
            if !lay.is_empty() {
                let id = s_of(obj_get(rec, "id"));
                match layers.iter_mut().find(|(k, _)| *k == lay) {
                    Some(e) => {
                        if !e.1.contains(&id) {
                            e.1.push(id);
                        }
                    }
                    None => layers.push((lay, vec![id])),
                }
            }
        }
        let mut layers_sorted: Vec<(String, Json)> = layers
            .into_iter()
            .map(|(k, v)| {
                let mut s: Vec<String> = v;
                s.sort();
                s.dedup();
                (k, str_json(&s))
            })
            .collect();
        layers_sorted.sort_by(|a, b| a.0.cmp(&b.0));
        let mut pub_set: BTreeSet<String> = BTreeSet::new();
        let mut sub_set: BTreeSet<String> = BTreeSet::new();
        for r in &own {
            for e in str_list(obj_get(r, "publish")) {
                pub_set.insert(e);
            }
            for e in str_list(obj_get(r, "subscribe")) {
                sub_set.insert(e);
            }
        }
        let rec = Json::Object(vec![
            ("package".to_string(), Json::Str(proto.id.clone())),
            ("pipeline".to_string(), Json::Str(proto.pipeline.clone())),
            (
                "modules".to_string(),
                str_json(&own.iter().map(|r| s_of(obj_get(r, "id"))).collect::<Vec<_>>()),
            ),
            ("module_recs".to_string(), Json::Array(own)),
            (
                "references".to_string(),
                Json::Array(
                    proto
                        .references
                        .iter()
                        .map(|(a, b)| {
                            Json::Object(vec![
                                ("source_package".to_string(), Json::Str(a.clone())),
                                ("module_id".to_string(), Json::Str(b.clone())),
                            ])
                        })
                        .collect(),
                ),
            ),
            ("layers".to_string(), Json::Object(layers_sorted)),
            ("assets".to_string(), Json::Array(pack_assets(root, &d))),
            (
                "publishes".to_string(),
                str_json(&pub_set.into_iter().collect::<Vec<_>>()),
            ),
            (
                "subscribes".to_string(),
                str_json(&sub_set.into_iter().collect::<Vec<_>>()),
            ),
        ]);
        out.push((proto.id, rec));
    }
    out
}

type Index = (Vec<(String, Json)>, Vec<(String, Vec<Json>)>, BTreeSet<String>);

/// 真源 `indexes`：`(by_id, pub_index, core_pub)`。
pub fn indexes(root: &Path, contracts: &[(String, Json)]) -> Index {
    let mut by_id: Vec<(String, Json)> = Vec::new();
    let mut pub_index: Vec<(String, Vec<Json>)> = Vec::new();
    for (_, r) in contracts {
        if s_of(obj_get(r, "path")).is_empty() {
            continue;
        }
        let id = s_of(obj_get(r, "id"));
        if !by_id.iter().any(|(k, _)| *k == id) {
            by_id.push((id, r.clone()));
        }
        for e in str_list(obj_get(r, "publish")) {
            match pub_index.iter_mut().find(|(k, _)| *k == e) {
                Some(slot) => slot.1.push(r.clone()),
                None => pub_index.push((e, vec![r.clone()])),
            }
        }
    }
    let mut core_pub: BTreeSet<String> = BTreeSet::new();
    for (_, r) in core_contracts(root) {
        for e in str_list(obj_get(&r, "publish")) {
            core_pub.insert(e);
        }
    }
    (by_id, pub_index, core_pub)
}

/// 真源 `_canon`：`json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)`。
///
/// ⚠️ **必须走 `dumps_default()`**（扁平、默认分隔符 `", "` / `": "`），**不能**用 `dumps()`
/// ——后者是**缩进**排版。实测（2026-10-04）：用 `dumps()` 时同一份证书的规范 JSON 长 2246 字符
/// （真源 1652），摘要随之全错 ⇒ 18 张证书全部报 `digest` 不一致。
pub fn canon(obj: &Json) -> String {
    obj.dumps_default()
}

/// 真源 `_digest`：去掉 `digest` 键后的规范 JSON 摘要（取前 32 位）。
pub fn digest_of_cert(obj: &Json) -> String {
    let stripped = match obj {
        Json::Object(o) => Json::Object(
            o.iter().filter(|(k, _)| k != "digest").map(|(k, v)| (k.clone(), v.clone())).collect(),
        ),
        other => other.clone(),
    };
    crate::merkle::hex(&crate::merkle::sha256(canon(&stripped).as_bytes()))[..32].to_string()
}

/// 真源 `_combo_witness`。
pub fn combo_witness(prof: &[(String, Json)], contracts: &[(String, Json)], by_id: &Index) -> String {
    let decl_keys =
        ["package", "pipeline", "references", "assets", "layers", "publishes", "subscribes"];
    // 真源是增量 `hashlib.sha256().update(...)`；本线的 merkle 模块只给一次性接口 ⇒
    // 累积字节后一次哈希。**结果逐位相同**（同一串字节、同一算法），且少一次 API 改动。
    let mut buf: Vec<u8> = Vec::new();
    let mut names: Vec<&String> = prof.iter().map(|(k, _)| k).collect();
    names.sort();
    for p in names {
        let rec = prof.iter().find(|(k, _)| k == p).map(|(_, v)| v.clone()).unwrap_or(Json::Object(vec![]));
        let mut decl: Vec<(String, Json)> = Vec::new();
        for k in decl_keys {
            decl.push((k.to_string(), obj_get(&rec, k).cloned().unwrap_or(Json::Null)));
        }
        let payload = Json::Array(vec![
            Json::Str("decl".to_string()),
            Json::Str(p.clone()),
            Json::Object(decl),
        ]);
        buf.extend_from_slice(canon(&payload).as_bytes());
    }
    let mut mids: Vec<&String> = contracts.iter().map(|(k, _)| k).collect();
    mids.sort();
    for mid in mids {
        let rec = contracts.iter().find(|(k, _)| k == mid).map(|(_, v)| v.clone()).unwrap_or(Json::Null);
        let payload =
            Json::Array(vec![Json::Str("contract".to_string()), Json::Str(mid.clone()), rec]);
        buf.extend_from_slice(canon(&payload).as_bytes());
    }
    let core: Vec<Json> = by_id.2.iter().map(|s| Json::Str(s.clone())).collect();
    let payload = Json::Array(vec![Json::Str("core_pub".to_string()), Json::Array(core)]);
    buf.extend_from_slice(canon(&payload).as_bytes());
    crate::merkle::hex(&crate::merkle::sha256(&buf))
}
