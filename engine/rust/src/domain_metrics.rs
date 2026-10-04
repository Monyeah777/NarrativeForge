//! 域功能引擎：12 个确定性评测口径 —— 与真源 `desktop/src/core/domain_metrics.py` 对账。
//!
//! 用途：域包的 **T4 面**（可复算产出）。门禁用本模块按声明的族与样例重算报告，再与在盘产物
//! 逐字段比对（见 `output_forms._recompute_entry` / `_gen_domain_report`）。
//!
//! **移植面**：闭包（`evaluate` 起）19 个函数 / 约 280 行 + `load_rows`（生成器要用）。
//! **不移植**：`synthesize` / `rows_to_csv` / `_Rng` —— 那是**确定性夹具生成器**（写面：
//! 造样例 CSV 入库），本线只读，没有任何已移植面会用到它。
//!
//! 口径纪律照搬真源：**确定性**（纯函数 / 无墙钟 / 无随机 / 固定位数四舍五入）+ **不夸口**
//! （算的是样例集上的口径值，不是模型能力声明）。四舍五入走 `pyfloat::round_to`（Python 的
//! 银行家舍入）——用 Rust 的 `round()` 会在正中平局处差一位。

use crate::pyjson::Json;
use crate::pyval;
use std::collections::BTreeMap;

pub const DIGITS: usize = 6;

/// 真源 `FAMILIES` 的键（12 族）。
pub const FAMILIES: [&str; 12] = [
    "classification",
    "retrieval",
    "extraction",
    "generation",
    "regression",
    "calibration",
    "agreement",
    "preference",
    "exact_judgement",
    "latency_cost",
    "drift",
    "contract_compliance",
];

/// 真源 `_r`（`round(x, 6)`，**银行家舍入**）。
fn r6(x: f64) -> f64 {
    crate::pyfloat::round_to(x, DIGITS)
}

/// 真源 `_safe_div`。
fn safe_div(a: f64, b: f64) -> f64 {
    if b == 0.0 {
        0.0
    } else {
        a / b
    }
}

type Row = BTreeMap<String, String>;

/// 真源 `load_rows`：`csv.DictReader(text.splitlines())`。
pub fn load_rows(path: &std::path::Path) -> Result<Vec<Row>, String> {
    let text = match std::fs::read(path) {
        Ok(b) => String::from_utf8_lossy(&b).into_owned(),
        Err(e) => return Err(format!("不可读：{}", e)),
    };
    let table = crate::asset_contract::csv_rows(&text);
    if table.is_empty() {
        return Err(format!(
            "空表（{}）",
            path.file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default()
        ));
    }
    let header = table[0].clone();
    let mut rows: Vec<Row> = Vec::new();
    for line in table.iter().skip(1) {
        if line.len() == 1 && line[0].is_empty() {
            continue;
        }
        let mut m: Row = BTreeMap::new();
        for (i, h) in header.iter().enumerate() {
            // `csv.DictReader`：多余列收进 `None` 键（本仓样例用不到），缺列给 `None`
            m.insert(h.clone(), line.get(i).cloned().unwrap_or_default());
        }
        rows.push(m);
    }
    if rows.is_empty() {
        return Err(format!(
            "空表（{}）",
            path.file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default()
        ));
    }
    Ok(rows)
}

/// 真源 `_num`。
fn num(row: &Row, key: &str) -> Result<f64, String> {
    let v = row.get(key).cloned().unwrap_or_default();
    v.trim().parse::<f64>().map_err(|_| {
        format!("列 {} 非数值：{}", key, pyval::py_repr(&Json::Str(v)))
    })
}

/// 真源 `_flag`。
fn flag(row: &Row, key: &str) -> Result<i64, String> {
    let v = row.get(key).cloned().unwrap_or_default().trim().to_lowercase();
    if ["1", "true", "yes", "y", "正", "是"].contains(&v.as_str()) {
        return Ok(1);
    }
    if ["0", "false", "no", "n", "负", "否"].contains(&v.as_str()) {
        return Ok(0);
    }
    Err(format!(
        "列 {} 非 0/1：{}",
        key,
        pyval::py_repr(&Json::Str(row.get(key).cloned().unwrap_or_default()))
    ))
}

fn get(row: &Row, key: &str) -> String {
    row.get(key).cloned().unwrap_or_default().trim().to_string()
}

/// 真源 `_r()` 的返回值**恒为 `float`** ⇒ JSON 里整值也写 `1.0` / `0.0`（不是 `1` / `0`）。
///
/// ⚠️ 别做「整数就转 Int」的聪明事：实测（2026-10-04）`extraction` 的 `field_recall` 因此写成
/// `1` 而真源是 `1.0`，T4 复算判据当场红。
fn jnum(x: f64) -> Json {
    Json::Float(x)
}

/// 真源 `_auc`（Mann-Whitney 口径，并列取平均秩）。
fn auc(pairs: &[(f64, i64)]) -> f64 {
    let pos: Vec<f64> = pairs.iter().filter(|(_, y)| *y == 1).map(|(s, _)| *s).collect();
    let neg: Vec<f64> = pairs.iter().filter(|(_, y)| *y == 0).map(|(s, _)| *s).collect();
    if pos.is_empty() || neg.is_empty() {
        return 0.0;
    }
    let mut wins = 0.0;
    for s in &pos {
        for t in &neg {
            wins += if s > t {
                1.0
            } else if s == t {
                0.5
            } else {
                0.0
            };
        }
    }
    wins / (pos.len() as f64 * neg.len() as f64)
}

/// 真源 `classification`。
fn classification(rows: &[Row]) -> Result<Json, String> {
    let mut labels: Vec<String> = Vec::new();
    for r in rows {
        for k in ["gold", "pred"] {
            let v = get(r, k);
            if !labels.contains(&v) {
                labels.push(v);
            }
        }
    }
    labels.sort();
    let mut cm: BTreeMap<(String, String), i64> = BTreeMap::new();
    for r in rows {
        *cm.entry((get(r, "gold"), get(r, "pred"))).or_insert(0) += 1;
    }
    let n = rows.len() as f64;
    let correct: i64 = labels.iter().map(|l| *cm.get(&(l.clone(), l.clone())).unwrap_or(&0)).sum();
    let per: Vec<(String, Json)> = labels
        .iter()
        .map(|l| {
            let tp = *cm.get(&(l.clone(), l.clone())).unwrap_or(&0);
            let fp: i64 = labels.iter().filter(|g| *g != l).map(|g| *cm.get(&(g.clone(), l.clone())).unwrap_or(&0)).sum();
            let fnn: i64 = labels.iter().filter(|p| p != &l).map(|p| *cm.get(&(l.clone(), p.clone())).unwrap_or(&0)).sum();
            let p = safe_div(tp as f64, (tp + fp) as f64);
            let rc = safe_div(tp as f64, (tp + fnn) as f64);
            let f1 = safe_div(2.0 * p * rc, p + rc);
            (
                l.clone(),
                Json::Object(vec![
                    ("precision".to_string(), jnum(r6(p))),
                    ("recall".to_string(), jnum(r6(rc))),
                    ("f1".to_string(), jnum(r6(f1))),
                    ("support".to_string(), Json::Int(tp + fnn)),
                ]),
            )
        })
        .collect();
    let macro_of = |k: &str| -> f64 {
        let s: f64 = per
            .iter()
            .map(|(_, v)| match v {
                Json::Object(o) => match o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv) {
                    Some(Json::Float(f)) => *f,
                    Some(Json::Int(i)) => *i as f64,
                    _ => 0.0,
                },
                _ => 0.0,
            })
            .sum();
        r6(s / labels.len() as f64)
    };
    let confusion: Vec<(String, Json)> = labels
        .iter()
        .map(|g| {
            let row: Vec<(String, Json)> = labels
                .iter()
                .map(|p| (p.clone(), Json::Int(*cm.get(&(g.clone(), p.clone())).unwrap_or(&0))))
                .collect();
            (g.clone(), Json::Object(row))
        })
        .collect();
    let mut out = vec![
        ("family".to_string(), Json::Str("classification".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("accuracy".to_string(), jnum(r6(correct as f64 / n))),
        (
            "macro".to_string(),
            Json::Object(vec![
                ("precision".to_string(), jnum(macro_of("precision"))),
                ("recall".to_string(), jnum(macro_of("recall"))),
                ("f1".to_string(), jnum(macro_of("f1"))),
            ]),
        ),
        ("confusion".to_string(), Json::Object(confusion)),
        ("per_label".to_string(), Json::Object(per)),
    ];
    if rows.iter().all(|r| ["0", "1"].contains(&get(r, "gold").as_str()))
        && rows.iter().all(|r| r.contains_key("score"))
    {
        let mut pairs: Vec<(f64, i64)> = Vec::new();
        for r in rows {
            let s = get(r, "score").parse::<f64>().unwrap_or(0.0);
            pairs.push((s, flag(r, "gold")?));
        }
        out.push(("roc_auc".to_string(), jnum(r6(auc(&pairs)))));
    }
    Ok(Json::Object(out))
}

/// 真源 `retrieval`。
fn retrieval(rows: &[Row], k: usize) -> Result<Json, String> {
    let mut groups: BTreeMap<String, Vec<(i64, i64)>> = BTreeMap::new();
    for r in rows {
        groups
            .entry(get(r, "query_id"))
            .or_default()
            .push((num(r, "rank")? as i64, flag(r, "relevant")?));
    }
    let (mut recalls, mut precisions, mut rrs, mut ndcgs, mut aps) =
        (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new());
    for (_, items) in groups.iter() {
        let mut it = items.clone();
        it.sort();
        let rel: Vec<i64> = it.iter().map(|(_, y)| *y).collect();
        let topk = &rel[..rel.len().min(k)];
        let total_rel: i64 = rel.iter().sum();
        recalls.push(safe_div(topk.iter().sum::<i64>() as f64, total_rel as f64));
        precisions.push(safe_div(topk.iter().sum::<i64>() as f64, k as f64));
        let mut rr = 0.0;
        for (i, y) in rel.iter().enumerate() {
            if *y != 0 {
                rr = 1.0 / (i as f64 + 1.0);
                break;
            }
        }
        rrs.push(rr);
        let dcg: f64 = rel
            .iter()
            .take(k)
            .enumerate()
            .map(|(i, y)| *y as f64 / ((i as f64 + 2.0).log2()))
            .sum();
        let ideal: f64 = (1..=(total_rel.min(k as i64)))
            .map(|i| 1.0 / ((i as f64 + 1.0).log2()))
            .sum();
        ndcgs.push(safe_div(dcg, ideal));
        let mut hits = 0i64;
        let mut ap = 0.0;
        for (i, y) in rel.iter().enumerate() {
            if *y != 0 {
                hits += 1;
                ap += hits as f64 / (i as f64 + 1.0);
            }
        }
        aps.push(safe_div(ap, total_rel as f64));
    }
    let avg = |v: &[f64]| if v.is_empty() { 0.0 } else { v.iter().sum::<f64>() / v.len() as f64 };
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("retrieval".to_string())),
        ("k".to_string(), Json::Int(k as i64)),
        ("queries".to_string(), Json::Int(groups.len() as i64)),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("recall_at_k".to_string(), jnum(r6(avg(&recalls)))),
        ("precision_at_k".to_string(), jnum(r6(avg(&precisions)))),
        ("mrr".to_string(), jnum(r6(avg(&rrs)))),
        ("ndcg_at_k".to_string(), jnum(r6(avg(&ndcgs)))),
        ("map".to_string(), jnum(r6(avg(&aps)))),
    ]))
}

/// 真源 `extraction`。
fn extraction(rows: &[Row]) -> Result<Json, String> {
    let (mut em, mut tp, mut fp, mut fnn) = (0i64, 0i64, 0i64, 0i64);
    for r in rows {
        let g = json_str_set(&get(r, "gold_fields"))?;
        let p = json_str_set(&get(r, "pred_fields"))?;
        if g == p {
            em += 1;
        }
        tp += g.intersection(&p).count() as i64;
        fp += p.difference(&g).count() as i64;
        fnn += g.difference(&p).count() as i64;
    }
    let pr = safe_div(tp as f64, (tp + fp) as f64);
    let rc = safe_div(tp as f64, (tp + fnn) as f64);
    let n = rows.len() as f64;
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("extraction".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("exact_match".to_string(), jnum(r6(em as f64 / n))),
        ("field_precision".to_string(), jnum(r6(pr))),
        ("field_recall".to_string(), jnum(r6(rc))),
        ("field_f1".to_string(), jnum(r6(safe_div(2.0 * pr * rc, pr + rc)))),
        ("tp".to_string(), Json::Int(tp)),
        ("fp".to_string(), Json::Int(fp)),
        ("fn".to_string(), Json::Int(fnn)),
    ]))
}

fn json_str_set(s: &str) -> Result<std::collections::BTreeSet<String>, String> {
    let parsed = crate::jsonmini::parse(s).map_err(|e| e.to_string())?;
    Ok(match parsed.value {
        Json::Array(a) => a.iter().map(pyval::plain_str).collect(),
        _ => std::collections::BTreeSet::new(),
    })
}

/// 真源 `generation`（字符集合用**字符**去重，词集合按空白切）。
fn generation(rows: &[Row]) -> Result<Json, String> {
    let (mut em, mut char_f1, mut set_f1) = (0i64, Vec::new(), Vec::new());
    for r in rows {
        let g = get(r, "reference");
        let p = get(r, "output");
        if g == p {
            em += 1;
        }
        let gs: std::collections::BTreeSet<char> = g.chars().collect();
        let ps: std::collections::BTreeSet<char> = p.chars().collect();
        let inter = gs.intersection(&ps).count() as f64;
        let prec = safe_div(inter, ps.len() as f64);
        let rec = safe_div(inter, gs.len() as f64);
        char_f1.push(safe_div(2.0 * prec * rec, prec + rec));
        let gt: std::collections::BTreeSet<&str> = g.split_whitespace().collect();
        let pt: std::collections::BTreeSet<&str> = p.split_whitespace().collect();
        let i2 = gt.intersection(&pt).count() as f64;
        let p2 = safe_div(i2, pt.len() as f64);
        let r2 = safe_div(i2, gt.len() as f64);
        set_f1.push(safe_div(2.0 * p2 * r2, p2 + r2));
    }
    let n = rows.len() as f64;
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("generation".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("exact_match".to_string(), jnum(r6(em as f64 / n))),
        ("char_f1".to_string(), jnum(r6(char_f1.iter().sum::<f64>() / n))),
        ("token_set_f1".to_string(), jnum(r6(set_f1.iter().sum::<f64>() / n))),
    ]))
}

/// 真源 `regression`。
fn regression(rows: &[Row]) -> Result<Json, String> {
    let g: Vec<f64> = rows.iter().map(|r| num(r, "gold")).collect::<Result<_, _>>()?;
    let p: Vec<f64> = rows.iter().map(|r| num(r, "pred")).collect::<Result<_, _>>()?;
    let n = rows.len() as f64;
    let mae = g.iter().zip(&p).map(|(a, b)| (a - b).abs()).sum::<f64>() / n;
    let rmse = (g.iter().zip(&p).map(|(a, b)| (a - b).powi(2)).sum::<f64>() / n).sqrt();
    let mg = g.iter().sum::<f64>() / n;
    let ss_tot: f64 = g.iter().map(|a| (a - mg).powi(2)).sum();
    let ss_res: f64 = g.iter().zip(&p).map(|(a, b)| (a - b).powi(2)).sum();
    let nz: Vec<(f64, f64)> = g.iter().zip(&p).filter(|(a, _)| **a != 0.0).map(|(a, b)| (*a, *b)).collect();
    let mape = if nz.is_empty() {
        0.0
    } else {
        nz.iter().map(|(a, b)| ((a - b) / a).abs()).sum::<f64>() / nz.len() as f64
    };
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("regression".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("mae".to_string(), jnum(r6(mae))),
        ("rmse".to_string(), jnum(r6(rmse))),
        ("r2".to_string(), jnum(r6(1.0 - safe_div(ss_res, ss_tot)))),
        ("mape".to_string(), jnum(r6(mape))),
        ("mape_samples".to_string(), Json::Int(nz.len() as i64)),
    ]))
}

/// 真源 `calibration`。
fn calibration(rows: &[Row], bins: usize) -> Result<Json, String> {
    let mut pairs: Vec<(f64, i64)> = Vec::new();
    for r in rows {
        pairs.push((num(r, "prob")?, flag(r, "gold")?));
    }
    if pairs.iter().any(|(p, _)| !(0.0..=1.0).contains(p)) {
        return Err("prob 必须在 [0,1]".to_string());
    }
    let n = pairs.len() as f64;
    let brier = pairs.iter().map(|(p, y)| (p - *y as f64).powi(2)).sum::<f64>() / n;
    let mut buckets: Vec<Json> = Vec::new();
    let mut ece = 0.0;
    for b in 0..bins {
        let lo = b as f64 / bins as f64;
        let hi = (b + 1) as f64 / bins as f64;
        let sel: Vec<(f64, i64)> = pairs
            .iter()
            .filter(|(p, _)| (lo <= *p && *p < hi) || (b == bins - 1 && *p == 1.0))
            .cloned()
            .collect();
        if sel.is_empty() {
            continue;
        }
        let conf = sel.iter().map(|(p, _)| *p).sum::<f64>() / sel.len() as f64;
        let acc = sel.iter().map(|(_, y)| *y as f64).sum::<f64>() / sel.len() as f64;
        ece += (sel.len() as f64 / n) * (conf - acc).abs();
        buckets.push(Json::Object(vec![
            ("range".to_string(), Json::Str(format!("[{:.1},{:.1}]", lo, hi))),
            ("n".to_string(), Json::Int(sel.len() as i64)),
            ("confidence".to_string(), jnum(r6(conf))),
            ("accuracy".to_string(), jnum(r6(acc))),
            ("gap".to_string(), jnum(r6((conf - acc).abs()))),
        ]));
    }
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("calibration".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("bins".to_string(), Json::Int(bins as i64)),
        ("nonempty_bins".to_string(), Json::Int(buckets.len() as i64)),
        ("ece".to_string(), jnum(r6(ece))),
        ("brier".to_string(), jnum(r6(brier))),
        ("buckets".to_string(), Json::Array(buckets)),
    ]))
}

/// 真源 `agreement`。
fn agreement(rows: &[Row]) -> Result<Json, String> {
    let mut labels: Vec<String> = Vec::new();
    for r in rows {
        for k in ["a", "b"] {
            let v = get(r, k);
            if !labels.contains(&v) {
                labels.push(v);
            }
        }
    }
    labels.sort();
    let n = rows.len() as f64;
    let mut cm: BTreeMap<(String, String), i64> = BTreeMap::new();
    for r in rows {
        *cm.entry((get(r, "a"), get(r, "b"))).or_insert(0) += 1;
    }
    let po = labels.iter().map(|l| *cm.get(&(l.clone(), l.clone())).unwrap_or(&0) as f64).sum::<f64>() / n;
    let pe: f64 = labels
        .iter()
        .map(|l| {
            let row_sum: i64 = labels.iter().map(|y| *cm.get(&(l.clone(), y.clone())).unwrap_or(&0)).sum();
            let col_sum: i64 = labels.iter().map(|g| *cm.get(&(g.clone(), l.clone())).unwrap_or(&0)).sum();
            (row_sum as f64 / n) * (col_sum as f64 / n)
        })
        .sum();
    let confusion: Vec<(String, Json)> = labels
        .iter()
        .map(|x| {
            let row: Vec<(String, Json)> = labels
                .iter()
                .map(|y| (y.clone(), Json::Int(*cm.get(&(x.clone(), y.clone())).unwrap_or(&0))))
                .collect();
            (x.clone(), Json::Object(row))
        })
        .collect();
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("agreement".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("labels".to_string(), Json::Int(labels.len() as i64)),
        ("observed_agreement".to_string(), jnum(r6(po))),
        ("expected_agreement".to_string(), jnum(r6(pe))),
        ("cohen_kappa".to_string(), jnum(r6(safe_div(po - pe, 1.0 - pe)))),
        ("confusion".to_string(), Json::Object(confusion)),
    ]))
}

/// 真源 `preference`。
fn preference(rows: &[Row]) -> Result<Json, String> {
    let n = rows.len() as f64;
    let agree = rows.iter().filter(|r| get(r, "judge") == get(r, "human")).count() as i64;
    let win = rows.iter().filter(|r| get(r, "judge") == "a").count() as i64;
    let loss = rows.iter().filter(|r| get(r, "judge") == "b").count() as i64;
    let tie = rows.len() as i64 - win - loss;
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("preference".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("agreement".to_string(), jnum(r6(agree as f64 / n))),
        ("win".to_string(), Json::Int(win)),
        ("loss".to_string(), Json::Int(loss)),
        ("tie".to_string(), Json::Int(tie)),
        (
            "win_rate_excl_tie".to_string(),
            jnum(r6(safe_div(win as f64, (win + loss) as f64))),
        ),
    ]))
}

/// 真源 `exact_judgement`。
fn exact_judgement(rows: &[Row], k: usize) -> Result<Json, String> {
    let mut groups: BTreeMap<String, Vec<i64>> = BTreeMap::new();
    for r in rows {
        groups.entry(get(r, "task_id")).or_default().push(flag(r, "passed")?);
    }
    let (mut pass1, mut passk, mut skipped, mut used) = (Vec::new(), Vec::new(), 0i64, 0i64);
    for (_, ys) in groups.iter() {
        let n = ys.len();
        let c: i64 = ys.iter().sum();
        pass1.push(c as f64 / n as f64);
        if n < k {
            skipped += 1;
            continue;
        }
        used += 1;
        if c == 0 {
            passk.push(0.0);
            continue;
        }
        if (n as i64 - c) < k as i64 {
            passk.push(1.0);
            continue;
        }
        let mut numv = 1.0;
        for i in 0..k {
            numv *= (n as f64 - c as f64 - i as f64) / (n as f64 - i as f64);
        }
        passk.push(1.0 - numv);
    }
    let avg = |v: &[f64]| if v.is_empty() { 0.0 } else { v.iter().sum::<f64>() / v.len() as f64 };
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("exact_judgement".to_string())),
        ("k".to_string(), Json::Int(k as i64)),
        ("tasks".to_string(), Json::Int(groups.len() as i64)),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("pass_at_1".to_string(), jnum(r6(avg(&pass1)))),
        ("pass_at_k".to_string(), jnum(r6(avg(&passk)))),
        ("tasks_used_for_passk".to_string(), Json::Int(used)),
        ("tasks_skipped_insufficient_samples".to_string(), Json::Int(skipped)),
    ]))
}

/// 真源 `latency_cost`。
fn latency_cost(rows: &[Row], pin: f64, pout: f64) -> Result<Json, String> {
    let mut lat: Vec<f64> = rows.iter().map(|r| num(r, "latency_ms")).collect::<Result<_, _>>()?;
    lat.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let pct = |q: f64| -> f64 {
        let idx = ((q * lat.len() as f64).ceil() as i64 - 1).clamp(0, lat.len() as i64 - 1) as usize;
        r6(lat[idx])
    };
    let tin: f64 = rows.iter().map(|r| num(r, "tokens_in")).collect::<Result<Vec<_>, _>>()?.iter().sum();
    let tout: f64 = rows.iter().map(|r| num(r, "tokens_out")).collect::<Result<Vec<_>, _>>()?.iter().sum();
    let n = rows.len() as f64;
    let cost = (tin / 1000.0) * pin + (tout / 1000.0) * pout;
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("latency_cost".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("p50_ms".to_string(), jnum(pct(0.50))),
        ("p95_ms".to_string(), jnum(pct(0.95))),
        ("p99_ms".to_string(), jnum(pct(0.99))),
        ("mean_ms".to_string(), jnum(r6(lat.iter().sum::<f64>() / n))),
        ("max_ms".to_string(), jnum(r6(*lat.last().unwrap_or(&0.0)))),
        ("tokens_in".to_string(), Json::Int(tin as i64)),
        ("tokens_out".to_string(), Json::Int(tout as i64)),
        ("price_per_1k_in".to_string(), jnum(r6(pin))),
        ("price_per_1k_out".to_string(), jnum(r6(pout))),
        ("cost_total".to_string(), jnum(r6(cost))),
        ("cost_per_1k_calls".to_string(), jnum(r6(cost / n * 1000.0))),
    ]))
}

/// 真源 `drift`。
fn drift(rows: &[Row]) -> Result<Json, String> {
    let eps = 1e-6;
    let mut psi = 0.0;
    let mut detail: Vec<Json> = Vec::new();
    for r in rows {
        let p = num(r, "expected")? + eps;
        let q = num(r, "actual")? + eps;
        let term = (p - q) * (p / q).ln();
        psi += term;
        detail.push(Json::Object(vec![
            ("bucket".to_string(), Json::Str(get(r, "bucket"))),
            ("expected".to_string(), jnum(r6(p))),
            ("actual".to_string(), jnum(r6(q))),
            ("term".to_string(), jnum(r6(term))),
        ]));
    }
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("drift".to_string())),
        ("buckets".to_string(), Json::Int(rows.len() as i64)),
        ("psi".to_string(), jnum(r6(psi))),
        ("smoothing_epsilon".to_string(), Json::Float(eps)),
        ("detail".to_string(), Json::Array(detail)),
    ]))
}

/// 真源 `contract_compliance`。
fn contract_compliance(rows: &[Row]) -> Result<Json, String> {
    let n = rows.len() as f64;
    let mut ok = 0i64;
    for r in rows {
        if flag(r, "valid")? == 1 {
            ok += 1;
        }
    }
    let mut missing: BTreeMap<String, i64> = BTreeMap::new();
    for r in rows {
        let raw = get(r, "missing_fields").replace('|', ",").replace(';', ",");
        for f in raw.split(',') {
            let f = f.trim();
            if !f.is_empty() {
                *missing.entry(f.to_string()).or_insert(0) += 1;
            }
        }
    }
    let mut items: Vec<(String, i64)> = missing.into_iter().collect();
    // `sorted(missing.items(), key=lambda kv: (-kv[1], kv[0]))[:5]`
    items.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
    let top: Vec<Json> = items
        .into_iter()
        .take(5)
        .map(|(k, v)| {
            Json::Object(vec![("field".to_string(), Json::Str(k)), ("count".to_string(), Json::Int(v))])
        })
        .collect();
    Ok(Json::Object(vec![
        ("family".to_string(), Json::Str("contract_compliance".to_string())),
        ("n".to_string(), Json::Int(rows.len() as i64)),
        ("compliance_rate".to_string(), jnum(r6(ok as f64 / n))),
        ("violations".to_string(), Json::Int(rows.len() as i64 - ok)),
        ("missing_top".to_string(), Json::Array(top)),
    ]))
}

/// 真源 `evaluate(family, rows, **params)`。
pub fn evaluate(family: &str, rows: &[Row], params: &[(String, Json)]) -> Result<Json, String> {
    if !FAMILIES.contains(&family) {
        return Err(format!(
            "未登记度量族：{}（可选：{:?}）",
            pyval::py_repr(&Json::Str(family.to_string())),
            {
                let mut f = FAMILIES.to_vec();
                f.sort();
                f
            }
        ));
    }
    let pget = |k: &str| params.iter().find(|(kk, _)| kk == k).map(|(_, v)| v.clone());
    let pnum = |k: &str, d: f64| -> f64 {
        match pget(k) {
            Some(Json::Int(i)) => i as f64,
            Some(Json::Float(f)) => f,
            Some(Json::Bool(b)) => {
                if b {
                    1.0
                } else {
                    0.0
                }
            }
            _ => d,
        }
    };
    let mut body = match family {
        "classification" => classification(rows)?,
        "retrieval" => retrieval(rows, pnum("k", 5.0) as usize)?,
        "extraction" => extraction(rows)?,
        "generation" => generation(rows)?,
        "regression" => regression(rows)?,
        "calibration" => calibration(rows, pnum("bins", 10.0) as usize)?,
        "agreement" => agreement(rows)?,
        "preference" => preference(rows)?,
        "exact_judgement" => exact_judgement(rows, pnum("k", 4.0) as usize)?,
        "latency_cost" => latency_cost(rows, pnum("price_per_1k_in", 0.0), pnum("price_per_1k_out", 0.0))?,
        "drift" => drift(rows)?,
        "contract_compliance" => contract_compliance(rows)?,
        _ => return Err("未登记度量族".to_string()),
    };
    if let Json::Object(o) = &mut body {
        o.push(("digits".to_string(), Json::Int(DIGITS as i64)));
        o.push((
            "note".to_string(),
            Json::Str(
                "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）"
                    .to_string(),
            ),
        ));
    }
    Ok(body)
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_domain_metrics_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 真语料 T4 域报告条目：`load_rows` + `evaluate` **全字段比对** =====
    ///
    /// 每条按真源 `_gen_domain_report` 的路径取样例 CSV（`community/<pkg>/<inputs[0]>`）→
    /// `load_rows` → `evaluate(family, rows, **params)`，与真源算出的整份报告逐字段比对。
    /// 这是 T4 复算的**真路径**（覆盖真语料实际用到的度量族）。
    #[test]
    fn domain_metrics_matches_truth_source_over_corpus() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &str, &str, &str, &str)] = &[
        (
            r#"AI人力资源与招聘域包"#,
            r#"extraction"#,
            r#"community/AI人力资源与招聘域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D14", "domain": "AI+人力资源与招聘", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.96, "field_precision": 0.923077, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 24}"#
        ),
        (
            r#"AI保险域包"#,
            r#"extraction"#,
            r#"community/AI保险域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D05", "domain": "AI+保险", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.956522, "field_precision": 0.916667, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 22}"#
        ),
        (
            r#"AI农业域包"#,
            r#"regression"#,
            r#"community/AI农业域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D10", "domain": "AI+农业", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.122494, "mape": 0.686392, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.983902, "rmse": 0.142947}"#
        ),
        (
            r#"AI制药与生物域包"#,
            r#"extraction"#,
            r#"community/AI制药与生物域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D02", "domain": "AI+制药与生物", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.958333, "field_precision": 0.92, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}"#
        ),
        (
            r#"AI制造业域包"#,
            r#"extraction"#,
            r#"community/AI制造业域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D08", "domain": "AI+制造业", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.666667, "family": "extraction", "field_f1": 0.916667, "field_precision": 0.846154, "field_recall": 1.0, "fn": 0, "fp": 4, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 22}"#
        ),
        (
            r#"AI医疗健康域包"#,
            r#"regression"#,
            r#"community/AI医疗健康域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D01", "domain": "AI+医疗健康", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.122919, "mape": 1.681713, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.982311, "rmse": 0.141885}"#
        ),
        (
            r#"AI政务与公共事务域包"#,
            r#"regression"#,
            r#"community/AI政务与公共事务域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D07", "domain": "AI+政务与公共事务", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.124244, "mape": 0.876649, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.984448, "rmse": 0.139465}"#
        ),
        (
            r#"AI教育域包"#,
            r#"classification"#,
            r#"community/AI教育域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D06", "domain": "AI+教育", "family": "classification"}"#,
            r#"{"accuracy": 0.708333, "confusion": {"neg": {"neg": 11, "pos": 4}, "pos": {"neg": 3, "pos": 6}}, "digits": 6, "family": "classification", "macro": {"f1": 0.6951, "precision": 0.692857, "recall": 0.7}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.758621, "precision": 0.785714, "recall": 0.733333, "support": 15}, "pos": {"f1": 0.631579, "precision": 0.6, "recall": 0.666667, "support": 9}}}"#
        ),
        (
            r#"AI法律与合规域包"#,
            r#"classification"#,
            r#"community/AI法律与合规域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D03", "domain": "AI+法律与合规", "family": "classification"}"#,
            r#"{"accuracy": 0.833333, "confusion": {"neg": {"neg": 11, "pos": 1}, "pos": {"neg": 3, "pos": 9}}, "digits": 6, "family": "classification", "macro": {"f1": 0.832168, "precision": 0.842857, "recall": 0.833333}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.846154, "precision": 0.785714, "recall": 0.916667, "support": 12}, "pos": {"f1": 0.818182, "precision": 0.9, "recall": 0.75, "support": 12}}}"#
        ),
        (
            r#"AI能源与电力域包"#,
            r#"classification"#,
            r#"community/AI能源与电力域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D09", "domain": "AI+能源与电力", "family": "classification"}"#,
            r#"{"accuracy": 0.833333, "confusion": {"neg": {"neg": 12, "pos": 4}, "pos": {"neg": 0, "pos": 8}}, "digits": 6, "family": "classification", "macro": {"f1": 0.828572, "precision": 0.833333, "recall": 0.875}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.857143, "precision": 1.0, "recall": 0.75, "support": 16}, "pos": {"f1": 0.8, "precision": 0.666667, "recall": 1.0, "support": 8}}}"#
        ),
        (
            r#"AI金融投研与风控域包"#,
            r#"regression"#,
            r#"community/AI金融投研与风控域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D04", "domain": "AI+金融投研与风控", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.097125, "mape": 0.103984, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.991556, "rmse": 0.119198}"#
        ),
        (
            r#"AI食品与餐饮域包"#,
            r#"regression"#,
            r#"community/AI食品与餐饮域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D16", "domain": "AI+食品与餐饮", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.142894, "mape": 0.478941, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.969999, "rmse": 0.161809}"#
        ),
        (
            r#"三维与世界模型域包"#,
            r#"regression"#,
            r#"community/三维与世界模型域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A08", "domain": "三维与世界模型", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.142494, "mape": 0.350618, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.982738, "rmse": 0.159409}"#
        ),
        (
            r#"上下文工程与长上下文域包"#,
            r#"contract_compliance"#,
            r#"community/上下文工程与长上下文域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C12", "domain": "上下文工程与长上下文", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.95, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 1, "field": "available_ts"}, {"count": 1, "field": "currency"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 1}"#
        ),
        (
            r#"世界书与设定库域包"#,
            r#"generation"#,
            r#"community/世界书与设定库域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E03", "domain": "世界书与设定库", "family": "generation"}"#,
            r#"{"char_f1": 0.707341, "digits": 6, "exact_match": 0.333333, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.333333}"#
        ),
        (
            r#"个人助理与日常生活域包"#,
            r#"preference"#,
            r#"community/个人助理与日常生活域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E16", "domain": "个人助理与日常生活", "family": "preference"}"#,
            r#"{"agreement": 0.625, "digits": 6, "family": "preference", "loss": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 4, "win": 8, "win_rate_excl_tie": 0.666667}"#
        ),
        (
            r#"交通与出行域包"#,
            r#"regression"#,
            r#"community/交通与出行域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D13", "domain": "交通与出行", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.134219, "mape": 0.395085, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.977773, "rmse": 0.150285}"#
        ),
        (
            r#"产业与商业落地域包"#,
            r#"agreement"#,
            r#"community/产业与商业落地域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F10", "domain": "产业与商业落地", "family": "agreement"}"#,
            r#"{"cohen_kappa": 0.782609, "confusion": {"F": {"F": 6, "T": 0}, "T": {"F": 2, "T": 12}}, "digits": 6, "expected_agreement": 0.54, "family": "agreement", "labels": 2, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "observed_agreement": 0.9}"#
        ),
        (
            r#"代码与软件工程域包"#,
            r#"preference"#,
            r#"community/代码与软件工程域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E13", "domain": "代码与软件工程", "family": "preference"}"#,
            r#"{"agreement": 0.875, "digits": 6, "family": "preference", "loss": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 1, "win": 11, "win_rate_excl_tie": 0.733333}"#
        ),
        (
            r#"代码大模型域包"#,
            r#"exact_judgement"#,
            r#"community/代码大模型域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A09", "domain": "代码大模型", "family": "exact_judgement"}"#,
            r#"{"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.5, "pass_at_k": 0.75, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}"#
        ),
        (
            r#"代码审查与缺陷检测域包"#,
            r#"classification"#,
            r#"community/代码审查与缺陷检测域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B09", "domain": "代码审查与缺陷检测", "family": "classification"}"#,
            r#"{"accuracy": 0.75, "confusion": {"neg": {"neg": 10, "pos": 2}, "pos": {"neg": 4, "pos": 8}}, "digits": 6, "family": "classification", "macro": {"f1": 0.748252, "precision": 0.757143, "recall": 0.75}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.769231, "precision": 0.714286, "recall": 0.833333, "support": 12}, "pos": {"f1": 0.727273, "precision": 0.8, "recall": 0.666667, "support": 12}}}"#
        ),
        (
            r#"代码生成与补全域包"#,
            r#"exact_judgement"#,
            r#"community/代码生成与补全域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B08", "domain": "代码生成与补全", "family": "exact_judgement"}"#,
            r#"{"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.625, "pass_at_k": 1.0, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}"#
        ),
        (
            r#"企业培训与组织学习域包"#,
            r#"generation"#,
            r#"community/企业培训与组织学习域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E15", "domain": "企业培训与组织学习", "family": "generation"}"#,
            r#"{"char_f1": 0.750992, "digits": 6, "exact_match": 0.333333, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.333333}"#
        ),
        (
            r#"传媒与新闻域包"#,
            r#"extraction"#,
            r#"community/传媒与新闻域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D17", "domain": "传媒与新闻", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.916667, "family": "extraction", "field_f1": 0.978723, "field_precision": 0.958333, "field_recall": 1.0, "fn": 0, "fp": 1, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}"#
        ),
        (
            r#"信息抽取与结构化域包"#,
            r#"extraction"#,
            r#"community/信息抽取与结构化域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B05", "domain": "信息抽取与结构化", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.666667, "family": "extraction", "field_f1": 0.923077, "field_precision": 0.857143, "field_recall": 1.0, "fn": 0, "fp": 4, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 24}"#
        ),
        (
            r#"具身智能与机器人域包"#,
            r#"exact_judgement"#,
            r#"community/具身智能与机器人域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A13", "domain": "具身智能与机器人", "family": "exact_judgement"}"#,
            r#"{"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.3125, "pass_at_k": 1.0, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}"#
        ),
        (
            r#"内容分发与社区运营域包"#,
            r#"preference"#,
            r#"community/内容分发与社区运营域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E19", "domain": "内容分发与社区运营", "family": "preference"}"#,
            r#"{"agreement": 0.75, "digits": 6, "family": "preference", "loss": 7, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 3, "win": 6, "win_rate_excl_tie": 0.461538}"#
        ),
        (
            r#"内容改写与风格迁移域包"#,
            r#"extraction"#,
            r#"community/内容改写与风格迁移域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E05", "domain": "内容改写与风格迁移", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.75, "family": "extraction", "field_f1": 0.941176, "field_precision": 0.888889, "field_recall": 1.0, "fn": 0, "fp": 3, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 24}"#
        ),
        (
            r#"分类与情感分析域包"#,
            r#"classification"#,
            r#"community/分类与情感分析域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B04", "domain": "分类与情感分析", "family": "classification"}"#,
            r#"{"accuracy": 0.916667, "confusion": {"neg": {"neg": 11, "pos": 2}, "pos": {"neg": 0, "pos": 11}}, "digits": 6, "family": "classification", "macro": {"f1": 0.916667, "precision": 0.923077, "recall": 0.923077}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.916667, "precision": 1.0, "recall": 0.846154, "support": 13}, "pos": {"f1": 0.916667, "precision": 0.846154, "recall": 1.0, "support": 11}}}"#
        ),
        (
            r#"参数高效微调域包"#,
            r#"contract_compliance"#,
            r#"community/参数高效微调域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C06", "domain": "参数高效微调", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.8, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 2, "field": "available_ts"}, {"count": 2, "field": "owner"}, {"count": 2, "field": "version"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 4}"#
        ),
        (
            r#"可观测性成本与可靠性域包"#,
            r#"contract_compliance"#,
            r#"community/可观测性成本与可靠性域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C18", "domain": "可观测性、成本与可靠性", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.9, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 1, "field": "currency"}, {"count": 1, "field": "owner"}, {"count": 1, "field": "unit"}, {"count": 1, "field": "version"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 2}"#
        ),
        (
            r#"可解释性与审计域包"#,
            r#"contract_compliance"#,
            r#"community/可解释性与审计域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F06", "domain": "可解释性与审计", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.75, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 4, "field": "available_ts"}, {"count": 2, "field": "owner"}, {"count": 2, "field": "version"}, {"count": 1, "field": "currency"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 5}"#
        ),
        (
            r#"合成数据生成域包"#,
            r#"contract_compliance"#,
            r#"community/合成数据生成域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C03", "domain": "合成数据生成", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.9, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 1, "field": "available_ts"}, {"count": 1, "field": "currency"}, {"count": 1, "field": "owner"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 2}"#
        ),
        (
            r#"合规与监管域包"#,
            r#"classification"#,
            r#"community/合规与监管域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F02", "domain": "合规与监管", "family": "classification"}"#,
            r#"{"accuracy": 0.875, "confusion": {"neg": {"neg": 8, "pos": 2}, "pos": {"neg": 1, "pos": 13}}, "digits": 6, "family": "classification", "macro": {"f1": 0.869328, "precision": 0.877778, "recall": 0.864286}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.842105, "precision": 0.888889, "recall": 0.8, "support": 10}, "pos": {"f1": 0.896552, "precision": 0.866667, "recall": 0.928571, "support": 14}}}"#
        ),
        (
            r#"向量库与检索管线域包"#,
            r#"contract_compliance"#,
            r#"community/向量库与检索管线域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C15", "domain": "向量库与检索管线", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.8, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 3, "field": "version"}, {"count": 2, "field": "currency"}, {"count": 1, "field": "owner"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 4}"#
        ),
        (
            r#"图像生成与编辑域包"#,
            r#"classification"#,
            r#"community/图像生成与编辑域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A07", "domain": "图像生成与编辑", "family": "classification"}"#,
            r#"{"accuracy": 0.833333, "confusion": {"neg": {"neg": 11, "pos": 2}, "pos": {"neg": 2, "pos": 9}}, "digits": 6, "family": "classification", "macro": {"f1": 0.832168, "precision": 0.832168, "recall": 0.832168}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.846154, "precision": 0.846154, "recall": 0.846154, "support": 13}, "pos": {"f1": 0.818182, "precision": 0.818182, "recall": 0.818182, "support": 11}}}"#
        ),
        (
            r#"图像生成与视觉创作域包"#,
            r#"preference"#,
            r#"community/图像生成与视觉创作域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E07", "domain": "图像生成与视觉创作", "family": "preference"}"#,
            r#"{"agreement": 0.875, "digits": 6, "family": "preference", "loss": 6, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 2, "win": 8, "win_rate_excl_tie": 0.571429}"#
        ),
        (
            r#"图像生成与视觉设计域包"#,
            r#"classification"#,
            r#"community/图像生成与视觉设计域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B15", "domain": "图像生成与视觉设计", "family": "classification"}"#,
            r#"{"accuracy": 0.875, "confusion": {"neg": {"neg": 10, "pos": 1}, "pos": {"neg": 2, "pos": 11}}, "digits": 6, "family": "classification", "macro": {"f1": 0.874783, "precision": 0.875, "recall": 0.877622}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.869565, "precision": 0.833333, "recall": 0.909091, "support": 11}, "pos": {"f1": 0.88, "precision": 0.916667, "recall": 0.846154, "support": 13}}}"#
        ),
        (
            r#"多智能体协同域包"#,
            r#"drift"#,
            r#"community/多智能体协同域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C17", "domain": "多智能体协同", "family": "drift"}"#,
            r#"{"buckets": 8, "detail": [{"actual": 0.111401, "bucket": "b0", "expected": 0.093101, "term": 0.003284}, {"actual": 0.139901, "bucket": "b1", "expected": 0.113001, "term": 0.005744}, {"actual": 0.103201, "bucket": "b2", "expected": 0.091701, "term": 0.001359}, {"actual": 0.174401, "bucket": "b3", "expected": 0.150501, "term": 0.003523}, {"actual": 0.169101, "bucket": "b4", "expected": 0.169901, "term": 4e-06}, {"actual": 0.056001, "bucket": "b5", "expected": 0.057201, "term": 2.5e-05}, {"actual": 0.063601, "bucket": "b6", "expected": 0.062401, "term": 2.3e-05}, {"actual": 0.127001, "bucket": "b7", "expected": 0.151701, "term": 0.00439}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.018351, "smoothing_epsilon": 1e-06}"#
        ),
        (
            r#"多模态大模型域包"#,
            r#"extraction"#,
            r#"community/多模态大模型域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A02", "domain": "多模态大模型", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.956522, "field_precision": 0.916667, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 22}"#
        ),
        (
            r#"多语翻译与本地化域包"#,
            r#"generation"#,
            r#"community/多语翻译与本地化域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E06", "domain": "多语翻译与本地化", "family": "generation"}"#,
            r#"{"char_f1": 0.691468, "digits": 6, "exact_match": 0.25, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.25}"#
        ),
        (
            r#"多轮对话与角色扮演域包"#,
            r#"preference"#,
            r#"community/多轮对话与角色扮演域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B07", "domain": "多轮对话与角色扮演", "family": "preference"}"#,
            r#"{"agreement": 0.8125, "digits": 6, "family": "preference", "loss": 7, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 3, "win": 6, "win_rate_excl_tie": 0.461538}"#
        ),
        (
            r#"大语言模型域包"#,
            r#"generation"#,
            r#"community/大语言模型域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A01", "domain": "大语言模型", "family": "generation"}"#,
            r#"{"char_f1": 0.856349, "digits": 6, "exact_match": 0.666667, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.666667}"#
        ),
        (
            r#"安全与对齐域包"#,
            r#"agreement"#,
            r#"community/安全与对齐域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F01", "domain": "安全与对齐", "family": "agreement"}"#,
            r#"{"cohen_kappa": 0.8, "confusion": {"F": {"F": 9, "T": 1}, "T": {"F": 1, "T": 9}}, "digits": 6, "expected_agreement": 0.5, "family": "agreement", "labels": 2, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "observed_agreement": 0.9}"#
        ),
        (
            r#"对话与客服域包"#,
            r#"generation"#,
            r#"community/对话与客服域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E18", "domain": "对话与客服", "family": "generation"}"#,
            r#"{"char_f1": 0.76746, "digits": 6, "exact_match": 0.5, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.5}"#
        ),
        (
            r#"对齐与偏好优化域包"#,
            r#"latency_cost"#,
            r#"community/对齐与偏好优化域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C07", "domain": "对齐与偏好优化", "family": "latency_cost"}"#,
            r#"{"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 874.4, "mean_ms": 434.745, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 452.0, "p95_ms": 758.9, "p99_ms": 874.4, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 20804, "tokens_out": 6744}"#
        ),
        (
            r#"嵌入与检索表示域包"#,
            r#"retrieval"#,
            r#"community/嵌入与检索表示域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A11", "domain": "嵌入与检索表示", "family": "retrieval"}"#,
            r#"{"digits": 6, "family": "retrieval", "k": 5, "map": 0.805556, "mrr": 0.833333, "n": 18, "ndcg_at_k": 0.871049, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "precision_at_k": 0.4, "queries": 3, "recall_at_k": 1.0}"#
        ),
        (
            r#"平台与基础设施域包"#,
            r#"classification"#,
            r#"community/平台与基础设施域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F08", "domain": "平台与基础设施", "family": "classification"}"#,
            r#"{"accuracy": 0.708333, "confusion": {"neg": {"neg": 10, "pos": 4}, "pos": {"neg": 3, "pos": 7}}, "digits": 6, "family": "classification", "macro": {"f1": 0.703704, "precision": 0.702797, "recall": 0.707143}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.740741, "precision": 0.769231, "recall": 0.714286, "support": 14}, "pos": {"f1": 0.666667, "precision": 0.636364, "recall": 0.7, "support": 10}}}"#
        ),
        (
            r#"建筑与房地产域包"#,
            r#"classification"#,
            r#"community/建筑与房地产域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D15", "domain": "建筑与房地产", "family": "classification"}"#,
            r#"{"accuracy": 0.75, "confusion": {"neg": {"neg": 8, "pos": 4}, "pos": {"neg": 2, "pos": 10}}, "digits": 6, "family": "classification", "macro": {"f1": 0.748252, "precision": 0.757143, "recall": 0.75}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.727273, "precision": 0.8, "recall": 0.666667, "support": 12}, "pos": {"f1": 0.769231, "precision": 0.714286, "recall": 0.833333, "support": 12}}}"#
        ),
        (
            r#"开源与开发者生态域包"#,
            r#"contract_compliance"#,
            r#"community/开源与开发者生态域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F09", "domain": "开源与开发者生态", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.75, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 3, "field": "available_ts"}, {"count": 2, "field": "currency"}, {"count": 2, "field": "version"}, {"count": 1, "field": "unit"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 5}"#
        ),
        (
            r#"强化学习与决策域包"#,
            r#"regression"#,
            r#"community/强化学习与决策域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A12", "domain": "强化学习与决策", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.154794, "mape": 0.961293, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.980296, "rmse": 0.168791}"#
        ),
        (
            r#"推理优化与加速域包"#,
            r#"latency_cost"#,
            r#"community/推理优化与加速域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C10", "domain": "推理优化与加速", "family": "latency_cost"}"#,
            r#"{"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 877.8, "mean_ms": 470.58, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 474.9, "p95_ms": 854.3, "p99_ms": 877.8, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 20871, "tokens_out": 6722}"#
        ),
        (
            r#"推理服务与部署域包"#,
            r#"drift"#,
            r#"community/推理服务与部署域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C11", "domain": "推理服务与部署", "family": "drift"}"#,
            r#"{"buckets": 8, "detail": [{"actual": 0.185001, "bucket": "b0", "expected": 0.175501, "term": 0.000501}, {"actual": 0.162001, "bucket": "b1", "expected": 0.177901, "term": 0.001489}, {"actual": 0.124701, "bucket": "b2", "expected": 0.149101, "term": 0.00436}, {"actual": 0.091601, "bucket": "b3", "expected": 0.074101, "term": 0.00371}, {"actual": 0.133201, "bucket": "b4", "expected": 0.108201, "term": 0.005197}, {"actual": 0.083601, "bucket": "b5", "expected": 0.084801, "term": 1.7e-05}, {"actual": 0.117301, "bucket": "b6", "expected": 0.090501, "term": 0.006951}, {"actual": 0.075201, "bucket": "b7", "expected": 0.055301, "term": 0.006117}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.028342, "smoothing_epsilon": 1e-06}"#
        ),
        (
            r#"推荐排序与广告域包"#,
            r#"generation"#,
            r#"community/推荐排序与广告域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B17", "domain": "推荐、排序与广告", "family": "generation"}"#,
            r#"{"char_f1": 0.863095, "digits": 6, "exact_match": 0.75, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.75}"#
        ),
        (
            r#"提示工程与指令设计域包"#,
            r#"preference"#,
            r#"community/提示工程与指令设计域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E01", "domain": "提示工程与指令设计", "family": "preference"}"#,
            r#"{"agreement": 0.9375, "digits": 6, "family": "preference", "loss": 8, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 0, "win": 8, "win_rate_excl_tie": 0.5}"#
        ),
        (
            r#"提示工程与提示模板域包"#,
            r#"latency_cost"#,
            r#"community/提示工程与提示模板域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C13", "domain": "提示工程与提示模板", "family": "latency_cost"}"#,
            r#"{"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 789.8, "mean_ms": 469.04, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 462.3, "p95_ms": 721.1, "p99_ms": 789.8, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 23392, "tokens_out": 7182}"#
        ),
        (
            r#"搜索与信息聚合域包"#,
            r#"extraction"#,
            r#"community/搜索与信息聚合域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E17", "domain": "搜索与信息聚合", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.916667, "family": "extraction", "field_f1": 0.978723, "field_precision": 0.958333, "field_recall": 1.0, "fn": 0, "fp": 1, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}"#
        ),
        (
            r#"摘要与信息压缩域包"#,
            r#"generation"#,
            r#"community/摘要与信息压缩域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B02", "domain": "摘要与信息压缩", "family": "generation"}"#,
            r#"{"char_f1": 0.676587, "digits": 6, "exact_match": 0.166667, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.166667}"#
        ),
        (
            r#"数字人与虚拟形象域包"#,
            r#"extraction"#,
            r#"community/数字人与虚拟形象域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E20", "domain": "数字人与虚拟形象", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.956522, "field_precision": 0.916667, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 22}"#
        ),
        (
            r#"数学与形式化推理域包"#,
            r#"exact_judgement"#,
            r#"community/数学与形式化推理域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A10", "domain": "数学与形式化推理", "family": "exact_judgement"}"#,
            r#"{"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.6875, "pass_at_k": 1.0, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}"#
        ),
        (
            r#"数据分析与决策支持域包"#,
            r#"extraction"#,
            r#"community/数据分析与决策支持域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E14", "domain": "数据分析与决策支持", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.75, "family": "extraction", "field_f1": 0.938776, "field_precision": 0.884615, "field_recall": 1.0, "fn": 0, "fp": 3, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}"#
        ),
        (
            r#"数据分析与表格理解域包"#,
            r#"regression"#,
            r#"community/数据分析与表格理解域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B11", "domain": "数据分析与表格理解", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.112225, "mape": 15.174802, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.98559, "rmse": 0.13578}"#
        ),
        (
            r#"数据标注与标注质量域包"#,
            r#"drift"#,
            r#"community/数据标注与标注质量域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C02", "domain": "数据标注与标注质量", "family": "drift"}"#,
            r#"{"buckets": 8, "detail": [{"actual": 0.100301, "bucket": "b0", "expected": 0.085901, "term": 0.002232}, {"actual": 0.108501, "bucket": "b1", "expected": 0.088701, "term": 0.003989}, {"actual": 0.168501, "bucket": "b2", "expected": 0.164201, "term": 0.000111}, {"actual": 0.095201, "bucket": "b3", "expected": 0.092801, "term": 6.1e-05}, {"actual": 0.167201, "bucket": "b4", "expected": 0.165901, "term": 1e-05}, {"actual": 0.154801, "bucket": "b5", "expected": 0.132701, "term": 0.003404}, {"actual": 0.090901, "bucket": "b6", "expected": 0.083101, "term": 0.0007}, {"actual": 0.117201, "bucket": "b7", "expected": 0.091901, "term": 0.006152}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.01666, "smoothing_epsilon": 1e-06}"#
        ),
        (
            r#"数据采集与清洗域包"#,
            r#"contract_compliance"#,
            r#"community/数据采集与清洗域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C01", "domain": "数据采集与清洗", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.9, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 1, "field": "available_ts"}, {"count": 1, "field": "currency"}, {"count": 1, "field": "owner"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 2}"#
        ),
        (
            r#"文旅与酒店域包"#,
            r#"regression"#,
            r#"community/文旅与酒店域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D19", "domain": "文旅与酒店", "family": "regression"}"#,
            r#"{"digits": 6, "family": "regression", "mae": 0.102119, "mape": 1.068382, "mape_samples": 16, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "r2": 0.986676, "rmse": 0.128744}"#
        ),
        (
            r#"文本生成与创作域包"#,
            r#"generation"#,
            r#"community/文本生成与创作域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B01", "domain": "文本生成与创作", "family": "generation"}"#,
            r#"{"char_f1": 0.734722, "digits": 6, "exact_match": 0.25, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.25}"#
        ),
        (
            r#"文档解析与版面理解域包"#,
            r#"extraction"#,
            r#"community/文档解析与版面理解域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B12", "domain": "文档解析与版面理解", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.916667, "family": "extraction", "field_f1": 0.97561, "field_precision": 0.952381, "field_recall": 1.0, "fn": 0, "fp": 1, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 20}"#
        ),
        (
            r#"智能体与工作流编排域包"#,
            r#"generation"#,
            r#"community/智能体与工作流编排域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E12", "domain": "智能体与工作流编排", "family": "generation"}"#,
            r#"{"char_f1": 0.765873, "digits": 6, "exact_match": 0.416667, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.416667}"#
        ),
        (
            r#"智能体框架与工具调用域包"#,
            r#"latency_cost"#,
            r#"community/智能体框架与工具调用域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C16", "domain": "智能体框架与工具调用", "family": "latency_cost"}"#,
            r#"{"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 894.3, "mean_ms": 586.97, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 609.4, "p95_ms": 874.3, "p99_ms": 894.3, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 17340, "tokens_out": 5479}"#
        ),
        (
            r#"机器翻译与本地化域包"#,
            r#"generation"#,
            r#"community/机器翻译与本地化域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B03", "domain": "机器翻译与本地化", "family": "generation"}"#,
            r#"{"char_f1": 0.725198, "digits": 6, "exact_match": 0.416667, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.416667}"#
        ),
        (
            r#"模型运营与成本域包"#,
            r#"agreement"#,
            r#"community/模型运营与成本域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F07", "domain": "模型运营与成本", "family": "agreement"}"#,
            r#"{"cohen_kappa": 0.7, "confusion": {"F": {"F": 8, "T": 2}, "T": {"F": 1, "T": 9}}, "digits": 6, "expected_agreement": 0.5, "family": "agreement", "labels": 2, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "observed_agreement": 0.85}"#
        ),
        (
            r#"测试与用例生成域包"#,
            r#"exact_judgement"#,
            r#"community/测试与用例生成域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B10", "domain": "测试与用例生成", "family": "exact_judgement"}"#,
            r#"{"digits": 6, "family": "exact_judgement", "k": 4, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "pass_at_1": 0.5, "pass_at_k": 1.0, "tasks": 4, "tasks_skipped_insufficient_samples": 0, "tasks_used_for_passk": 4}"#
        ),
        (
            r#"游戏与互动娱乐域包"#,
            r#"classification"#,
            r#"community/游戏与互动娱乐域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D18", "domain": "游戏与互动娱乐", "family": "classification"}"#,
            r#"{"accuracy": 0.791667, "confusion": {"neg": {"neg": 9, "pos": 1}, "pos": {"neg": 4, "pos": 10}}, "digits": 6, "family": "classification", "macro": {"f1": 0.791305, "precision": 0.8007, "recall": 0.807143}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.782609, "precision": 0.692308, "recall": 0.9, "support": 10}, "pos": {"f1": 0.8, "precision": 0.909091, "recall": 0.714286, "support": 14}}}"#
        ),
        (
            r#"版权与知识产权域包"#,
            r#"agreement"#,
            r#"community/版权与知识产权域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F04", "domain": "版权与知识产权", "family": "agreement"}"#,
            r#"{"cohen_kappa": 0.6, "confusion": {"F": {"F": 6, "T": 0}, "T": {"F": 4, "T": 10}}, "digits": 6, "expected_agreement": 0.5, "family": "agreement", "labels": 2, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "observed_agreement": 0.8}"#
        ),
        (
            r#"物流与供应链域包"#,
            r#"classification"#,
            r#"community/物流与供应链域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D12", "domain": "物流与供应链", "family": "classification"}"#,
            r#"{"accuracy": 0.666667, "confusion": {"neg": {"neg": 8, "pos": 4}, "pos": {"neg": 4, "pos": 8}}, "digits": 6, "family": "classification", "macro": {"f1": 0.666667, "precision": 0.666667, "recall": 0.666667}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.666667, "precision": 0.666667, "recall": 0.666667, "support": 12}, "pos": {"f1": 0.666667, "precision": 0.666667, "recall": 0.666667, "support": 12}}}"#
        ),
        (
            r#"监督微调域包"#,
            r#"drift"#,
            r#"community/监督微调域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C05", "domain": "监督微调", "family": "drift"}"#,
            r#"{"buckets": 8, "detail": [{"actual": 0.164601, "bucket": "b0", "expected": 0.143601, "term": 0.002866}, {"actual": 0.101601, "bucket": "b1", "expected": 0.116201, "term": 0.00196}, {"actual": 0.054301, "bucket": "b2", "expected": 0.051101, "term": 0.000194}, {"actual": 0.102701, "bucket": "b3", "expected": 0.091401, "term": 0.001317}, {"actual": 0.133701, "bucket": "b4", "expected": 0.106701, "term": 0.006091}, {"actual": 0.168601, "bucket": "b5", "expected": 0.193201, "term": 0.00335}, {"actual": 0.103201, "bucket": "b6", "expected": 0.112401, "term": 0.000786}, {"actual": 0.110001, "bucket": "b7", "expected": 0.082501, "term": 0.007911}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.024476, "smoothing_epsilon": 1e-06}"#
        ),
        (
            r#"知识管理与检索增强域包"#,
            r#"extraction"#,
            r#"community/知识管理与检索增强域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E11", "domain": "知识管理与检索增强", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.75, "family": "extraction", "field_f1": 0.938776, "field_precision": 0.884615, "field_recall": 1.0, "fn": 0, "fp": 3, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}"#
        ),
        (
            r#"知识问答与检索增强域包"#,
            r#"retrieval"#,
            r#"community/知识问答与检索增强域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B06", "domain": "知识问答与检索增强", "family": "retrieval"}"#,
            r#"{"digits": 6, "family": "retrieval", "k": 5, "map": 0.388889, "mrr": 0.361111, "n": 18, "ndcg_at_k": 0.550746, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "precision_at_k": 0.333333, "queries": 3, "recall_at_k": 1.0}"#
        ),
        (
            r#"科研与实验域包"#,
            r#"extraction"#,
            r#"community/科研与实验域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D20", "domain": "科研与实验", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.75, "family": "extraction", "field_f1": 0.933333, "field_precision": 0.875, "field_recall": 1.0, "fn": 0, "fp": 3, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 21}"#
        ),
        (
            r#"端侧与边缘小模型域包"#,
            r#"latency_cost"#,
            r#"community/端侧与边缘小模型域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A14", "domain": "端侧与边缘小模型", "family": "latency_cost"}"#,
            r#"{"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 878.4, "mean_ms": 576.265, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 539.1, "p95_ms": 833.5, "p99_ms": 878.4, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 16787, "tokens_out": 5116}"#
        ),
        (
            r#"红队越狱与安全测试域包"#,
            r#"contract_compliance"#,
            r#"community/红队越狱与安全测试域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C09", "domain": "红队、越狱与安全测试", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.8, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 3, "field": "unit"}, {"count": 2, "field": "currency"}, {"count": 2, "field": "version"}, {"count": 1, "field": "owner"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 4}"#
        ),
        (
            r#"编辑校对与出版域包"#,
            r#"preference"#,
            r#"community/编辑校对与出版域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E10", "domain": "编辑校对与出版", "family": "preference"}"#,
            r#"{"agreement": 0.875, "digits": 6, "family": "preference", "loss": 6, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 1, "win": 9, "win_rate_excl_tie": 0.6}"#
        ),
        (
            r#"视觉模型域包"#,
            r#"classification"#,
            r#"community/视觉模型域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A03", "domain": "视觉模型", "family": "classification"}"#,
            r#"{"accuracy": 0.958333, "confusion": {"neg": {"neg": 10, "pos": 0}, "pos": {"neg": 1, "pos": 13}}, "digits": 6, "family": "classification", "macro": {"f1": 0.957672, "precision": 0.954546, "recall": 0.964286}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.952381, "precision": 0.909091, "recall": 1.0, "support": 10}, "pos": {"f1": 0.962963, "precision": 1.0, "recall": 0.928571, "support": 14}}}"#
        ),
        (
            r#"视频生成与剪辑域包"#,
            r#"extraction"#,
            r#"community/视频生成与剪辑域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E08", "domain": "视频生成与剪辑", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.666667, "family": "extraction", "field_f1": 0.92, "field_precision": 0.851852, "field_recall": 1.0, "fn": 0, "fp": 4, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}"#
        ),
        (
            r#"视频生成与理解域包"#,
            r#"retrieval"#,
            r#"community/视频生成与理解域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A06", "domain": "视频生成与理解", "family": "retrieval"}"#,
            r#"{"digits": 6, "family": "retrieval", "k": 5, "map": 0.519444, "mrr": 0.483333, "n": 18, "ndcg_at_k": 0.500422, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "precision_at_k": 0.266667, "queries": 3, "recall_at_k": 0.666667}"#
        ),
        (
            r#"视频生成与自动剪辑域包"#,
            r#"extraction"#,
            r#"community/视频生成与自动剪辑域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B16", "domain": "视频生成与自动剪辑", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.916667, "family": "extraction", "field_f1": 0.978723, "field_precision": 0.958333, "field_recall": 1.0, "fn": 0, "fp": 1, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}"#
        ),
        (
            r#"角色扮演与角色卡域包"#,
            r#"extraction"#,
            r#"community/角色扮演与角色卡域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E02", "domain": "角色扮演与角色卡", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.954545, "field_precision": 0.913043, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 21}"#
        ),
        (
            r#"记忆体与个性化域包"#,
            r#"drift"#,
            r#"community/记忆体与个性化域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C14", "domain": "记忆体与个性化", "family": "drift"}"#,
            r#"{"buckets": 8, "detail": [{"actual": 0.052201, "bucket": "b0", "expected": 0.051201, "term": 1.9e-05}, {"actual": 0.122201, "bucket": "b1", "expected": 0.122801, "term": 3e-06}, {"actual": 0.172401, "bucket": "b2", "expected": 0.194401, "term": 0.002642}, {"actual": 0.184301, "bucket": "b3", "expected": 0.181201, "term": 5.3e-05}, {"actual": 0.060601, "bucket": "b4", "expected": 0.053701, "term": 0.000834}, {"actual": 0.073201, "bucket": "b5", "expected": 0.050901, "term": 0.008102}, {"actual": 0.087201, "bucket": "b6", "expected": 0.103301, "term": 0.002728}, {"actual": 0.083101, "bucket": "b7", "expected": 0.075301, "term": 0.000769}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.01515, "smoothing_epsilon": 1e-06}"#
        ),
        (
            r#"评测与基准域包"#,
            r#"classification"#,
            r#"community/评测与基准域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F05", "domain": "评测与基准", "family": "classification"}"#,
            r#"{"accuracy": 0.583333, "confusion": {"neg": {"neg": 8, "pos": 7}, "pos": {"neg": 3, "pos": 6}}, "digits": 6, "family": "classification", "macro": {"f1": 0.58042, "precision": 0.594405, "recall": 0.6}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.615385, "precision": 0.727273, "recall": 0.533333, "support": 15}, "pos": {"f1": 0.545455, "precision": 0.461538, "recall": 0.666667, "support": 9}}}"#
        ),
        (
            r#"评测基准与排行榜域包"#,
            r#"drift"#,
            r#"community/评测基准与排行榜域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C08", "domain": "评测、基准与排行榜", "family": "drift"}"#,
            r#"{"buckets": 8, "detail": [{"actual": 0.172001, "bucket": "b0", "expected": 0.190701, "term": 0.00193}, {"actual": 0.073301, "bucket": "b1", "expected": 0.091901, "term": 0.004206}, {"actual": 0.151501, "bucket": "b2", "expected": 0.148701, "term": 5.2e-05}, {"actual": 0.113201, "bucket": "b3", "expected": 0.086801, "term": 0.00701}, {"actual": 0.049201, "bucket": "b4", "expected": 0.075901, "term": 0.011575}, {"actual": 0.087401, "bucket": "b5", "expected": 0.058301, "term": 0.011782}, {"actual": 0.081001, "bucket": "b6", "expected": 0.067001, "term": 0.002657}, {"actual": 0.200901, "bucket": "b7", "expected": 0.189901, "term": 0.000619}], "digits": 6, "family": "drift", "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "psi": 0.039832, "smoothing_epsilon": 1e-06}"#
        ),
        (
            r#"语音合成与配音域包"#,
            r#"generation"#,
            r#"community/语音合成与配音域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B14", "domain": "语音合成与配音", "family": "generation"}"#,
            r#"{"char_f1": 0.871032, "digits": 6, "exact_match": 0.5, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.5}"#
        ),
        (
            r#"语音识别与合成域包"#,
            r#"generation"#,
            r#"community/语音识别与合成域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A04", "domain": "语音识别与合成", "family": "generation"}"#,
            r#"{"char_f1": 0.71627, "digits": 6, "exact_match": 0.25, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.25}"#
        ),
        (
            r#"语音转写与会议记录域包"#,
            r#"extraction"#,
            r#"community/语音转写与会议记录域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B13", "domain": "语音转写与会议记录", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.958333, "field_precision": 0.92, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 23}"#
        ),
        (
            r#"长文本与小说创作域包"#,
            r#"preference"#,
            r#"community/长文本与小说创作域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E04", "domain": "长文本与小说创作", "family": "preference"}"#,
            r#"{"agreement": 0.875, "digits": 6, "family": "preference", "loss": 10, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 2, "win": 4, "win_rate_excl_tie": 0.285714}"#
        ),
        (
            r#"隐私与数据治理域包"#,
            r#"contract_compliance"#,
            r#"community/隐私与数据治理域包/outputs/samples/CASES.csv"#,
            r#"{"code": "F03", "domain": "隐私与数据治理", "family": "contract_compliance"}"#,
            r#"{"compliance_rate": 0.8, "digits": 6, "family": "contract_compliance", "missing_top": [{"count": 3, "field": "currency"}, {"count": 3, "field": "version"}, {"count": 1, "field": "available_ts"}, {"count": 1, "field": "owner"}], "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "violations": 4}"#
        ),
        (
            r#"零售与电商域包"#,
            r#"extraction"#,
            r#"community/零售与电商域包/outputs/samples/CASES.csv"#,
            r#"{"code": "D11", "domain": "零售与电商", "family": "extraction"}"#,
            r#"{"digits": 6, "exact_match": 0.833333, "family": "extraction", "field_f1": 0.954545, "field_precision": 0.913043, "field_recall": 1.0, "fn": 0, "fp": 2, "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tp": 21}"#
        ),
        (
            r#"音频与音乐生成域包"#,
            r#"preference"#,
            r#"community/音频与音乐生成域包/outputs/samples/CASES.csv"#,
            r#"{"code": "A05", "domain": "音频与音乐生成", "family": "preference"}"#,
            r#"{"agreement": 1.0, "digits": 6, "family": "preference", "loss": 7, "n": 16, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "tie": 0, "win": 9, "win_rate_excl_tie": 0.5625}"#
        ),
        (
            r#"音频音乐与语音域包"#,
            r#"generation"#,
            r#"community/音频音乐与语音域包/outputs/samples/CASES.csv"#,
            r#"{"code": "E09", "domain": "音频音乐与语音", "family": "generation"}"#,
            r#"{"char_f1": 0.746032, "digits": 6, "exact_match": 0.333333, "family": "generation", "n": 12, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "token_set_f1": 0.333333}"#
        ),
        (
            r#"预测异常与风险域包"#,
            r#"classification"#,
            r#"community/预测异常与风险域包/outputs/samples/CASES.csv"#,
            r#"{"code": "B18", "domain": "预测、异常与风险", "family": "classification"}"#,
            r#"{"accuracy": 0.916667, "confusion": {"neg": {"neg": 8, "pos": 1}, "pos": {"neg": 1, "pos": 14}}, "digits": 6, "family": "classification", "macro": {"f1": 0.911111, "precision": 0.911111, "recall": 0.911111}, "n": 24, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "per_label": {"neg": {"f1": 0.888889, "precision": 0.888889, "recall": 0.888889, "support": 9}, "pos": {"f1": 0.933333, "precision": 0.933333, "recall": 0.933333, "support": 15}}}"#
        ),
        (
            r#"预训练与继续预训练域包"#,
            r#"latency_cost"#,
            r#"community/预训练与继续预训练域包/outputs/samples/CASES.csv"#,
            r#"{"code": "C04", "domain": "预训练与继续预训练", "family": "latency_cost"}"#,
            r#"{"cost_per_1k_calls": 0.0, "cost_total": 0.0, "digits": 6, "family": "latency_cost", "max_ms": 854.5, "mean_ms": 526.545, "n": 20, "note": "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；本报告由 core/domain_metrics.py 确定性复算（T4）", "p50_ms": 526.5, "p95_ms": 844.6, "p99_ms": 854.5, "price_per_1k_in": 0.0, "price_per_1k_out": 0.0, "tokens_in": 21085, "tokens_out": 6690}"#
        ),
        ];
        let mut ok = 0usize;
        let mut skipped = 0usize;
        for (pkg, family, src, params_s, want_s) in cases {
            if src.is_empty() || want_s.is_empty() {
                skipped += 1;
                continue;
            }
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(params_s).unwrap(),
            )
            .unwrap();
            let params: Vec<(String, Json)> = match spec {
                Json::Object(o) => o,
                _ => Vec::new(),
            };
            let loaded = load_rows(&root.join(src))
                .unwrap_or_else(|e| panic!("{} 读样例 {} 失败：{}", pkg, src, e));
            let got = evaluate(family, &loaded, &params)
                .unwrap_or_else(|e| panic!("{} ({}) evaluate 失败：{}", pkg, family, e));
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_s).unwrap(),
            )
            .unwrap();
            assert!(
                crate::jsonread::json_eq(&got, &want),
                "{} ({}) 报告不一致\n  实得 {}\n  期望 {}",
                pkg,
                family,
                got.dumps_default(),
                want.dumps_default()
            );
            ok += 1;
        }
        assert!(ok > 0, "至少要真跑若干条，否则判据是空转");
        eprintln!("domain_metrics 对账：{} 条通过 / {} 条跳过（缺 inputs）", ok, skipped);
    }
    // <<< GENERATED
}
