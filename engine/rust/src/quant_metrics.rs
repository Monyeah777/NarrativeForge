//! 量化金融域功能面：绩效报告与指标口径 —— 与真源 `desktop/src/core/quant_metrics.py` 对账。
//!
//! 用途：`量化金融域包` 的 **T4 面**（`performance-report`）。门禁用本模块按净值样例重算报告，
//! 与在盘报告逐字段比对（见 `output_forms._gen_performance_report`）。
//!
//! **移植面**：`performance_report` 闭包 16 个函数 / 约 125 行 + `load_equity_curve`（生成器要用）
//! + 同族的 `information_coefficient` / `turnover` / `drawdown_series` 与图表规格
//! （`vega_equity_curve` / `vega_drawdown` / `mermaid_declaration_flow`）。
//! 后几项虽不在**真语料**的判据路径上，但属同一族公开口径面，**一次移植完整**，不留"可达但缺席"。
//!
//! 口径纪律照搬真源：年化因子显式（252/52/12，**不得默认 365**）、样本标准差 ddof=1、
//! 最大回撤按净值历史峰值、卡尔玛分子分母同区间、换手按单边声明、IC 用截面秩相关。
//! 确定性：纯函数 / 无墙钟 / 无随机 / 固定位数四舍五入（走 `pyfloat::round_to`，银行家舍入）。

use crate::pyjson::Json;
use std::path::Path;

pub const DIGITS: usize = 6;

/// 真源 `ANNUAL_FACTORS`。
pub fn annual_factor(freq: &str) -> Option<i64> {
    match freq {
        "daily" => Some(252),
        "weekly" => Some(52),
        "monthly" => Some(12),
        _ => None,
    }
}

/// 真源 `GIPS_ALIGNMENT`（披露面原文）。
pub const GIPS_ALIGNMENT: &str = "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据";

/// 真源 `_r`（`round(x, 6)`，**银行家舍入**；返回值恒为 float）。
fn r6(x: f64) -> Json {
    Json::Float(crate::pyfloat::round_to(x, DIGITS))
}

/// 真源 `_r` 的数值版（内部计算用，不落 JSON）。
fn rn(x: f64) -> f64 {
    crate::pyfloat::round_to(x, DIGITS)
}

/// 真源 `load_equity_curve` → `(series, err)`。
pub fn load_equity_curve(path: &Path) -> Result<Json, String> {
    let text = match std::fs::read(path) {
        Ok(b) => String::from_utf8_lossy(&b).into_owned(),
        Err(e) => return Err(format!("不可读：{}", e)),
    };
    let table = crate::asset_contract::csv_rows(&text);
    if table.is_empty() {
        return Err("空表".to_string());
    }
    let header = table[0].clone();
    let mut cols: Vec<String> = header
        .iter()
        .filter(|c| !c.is_empty())
        .map(|c| c.trim().to_lowercase())
        .collect();
    cols.sort();
    for need in ["date", "equity"] {
        if !cols.iter().any(|c| c == need) {
            // 真源是 `sorted(cols)` 的 **Python 列表 repr**（单引号）：`['date', 'value']`
            let shown = crate::pyval::py_repr_list(
                &cols.iter().map(|c| Json::Str(c.clone())).collect::<Vec<_>>(),
            );
            return Err(format!("缺列 {}（实际列：{}）", need, shown));
        }
    }
    let has_bench = cols.iter().any(|c| c == "benchmark");
    let find = |row: &[String], lower: &str| -> Option<String> {
        header
            .iter()
            .position(|h| h.trim().to_lowercase() == lower)
            .and_then(|i| row.get(i).cloned())
    };
    let (mut dates, mut equity, mut bench) = (Vec::new(), Vec::new(), Vec::new());
    for (idx, row) in table.iter().skip(1).enumerate() {
        if row.len() == 1 && row[0].is_empty() {
            continue;
        }
        let line_no = idx + 2;
        // 真源 `row.get("date") or row.get("Date")`：**原样键**优先，其次大小写变体
        let d = find(row, "date").unwrap_or_default();
        dates.push(d.trim().to_string());
        let ev = find(row, "equity").unwrap_or_default();
        match ev.trim().parse::<f64>() {
            Ok(v) => equity.push(v),
            Err(_) => return Err(format!("第 {} 行数值不可解析", line_no)),
        }
        if has_bench {
            let bv = find(row, "benchmark").unwrap_or_default();
            match bv.trim().parse::<f64>() {
                Ok(v) => bench.push(v),
                Err(_) => return Err(format!("第 {} 行数值不可解析", line_no)),
            }
        }
    }
    if equity.len() < 3 {
        return Err("样本过短（< 3 个净值点）".to_string());
    }
    if equity.iter().any(|v| *v <= 0.0) {
        return Err("净值须为正数（口径：净值序列，非累计收益）".to_string());
    }
    Ok(Json::Object(vec![
        (
            "dates".to_string(),
            Json::Array(dates.into_iter().map(Json::Str).collect()),
        ),
        ("equity".to_string(), Json::Array(equity.into_iter().map(Json::Float).collect())),
        (
            "benchmark".to_string(),
            if has_bench {
                Json::Array(bench.into_iter().map(Json::Float).collect())
            } else {
                Json::Null
            },
        ),
    ]))
}

fn nums(series: &Json, key: &str) -> Vec<f64> {
    match series {
        Json::Object(o) => match o.iter().find(|(k, _)| k == key).map(|(_, v)| v) {
            Some(Json::Array(a)) => a
                .iter()
                .map(|v| match v {
                    Json::Float(f) => *f,
                    Json::Int(i) => *i as f64,
                    _ => 0.0,
                })
                .collect(),
            _ => Vec::new(),
        },
        _ => Vec::new(),
    }
}

/// 真源 `simple_returns`。
pub fn simple_returns(prices: &[f64]) -> Vec<f64> {
    (1..prices.len()).map(|i| prices[i] / prices[i - 1] - 1.0).collect()
}

/// 真源 `log_returns`。
pub fn log_returns(prices: &[f64]) -> Vec<f64> {
    (1..prices.len()).map(|i| (prices[i] / prices[i - 1]).ln()).collect()
}

/// 真源 `returns(prices, kind)`。
pub fn returns(prices: &[f64], kind: &str) -> Result<Vec<f64>, String> {
    match kind {
        "simple" => Ok(simple_returns(prices)),
        "log" => Ok(log_returns(prices)),
        other => Err(format!(
            "收益口径只支持 simple / log，实为 {}",
            crate::pyval::py_repr(&Json::Str(other.to_string()))
        )),
    }
}

/// 真源 `cumulative_return`。
pub fn cumulative_return(prices: &[f64]) -> f64 {
    prices[prices.len() - 1] / prices[0] - 1.0
}

/// 真源 `annualized_return`。
pub fn annualized_return(prices: &[f64], af: i64) -> f64 {
    let n = prices.len() as i64 - 1;
    if n <= 0 {
        return 0.0;
    }
    let growth = prices[prices.len() - 1] / prices[0];
    growth.powf(af as f64 / n as f64) - 1.0
}

/// 真源 `_mean`。
pub fn mean_of(xs: &[f64]) -> f64 {
    if xs.is_empty() {
        0.0
    } else {
        xs.iter().sum::<f64>() / xs.len() as f64
    }
}

/// 真源 `_stdev`（样本标准差 ddof=1）。
pub fn stdev(xs: &[f64]) -> f64 {
    let n = xs.len();
    if n < 2 {
        return 0.0;
    }
    let mu = mean_of(xs);
    (xs.iter().map(|x| (x - mu).powi(2)).sum::<f64>() / (n as f64 - 1.0)).sqrt()
}

/// 真源 `annualized_volatility`。
pub fn annualized_volatility(rets: &[f64], af: i64) -> f64 {
    stdev(rets) * (af as f64).sqrt()
}

/// 真源 `max_drawdown`。
pub fn max_drawdown(prices: &[f64]) -> f64 {
    let mut peak = prices[0];
    let mut mdd: f64 = 0.0;
    for p in prices {
        peak = peak.max(*p);
        mdd = mdd.max((peak - p) / peak);
    }
    mdd
}

/// 真源 `drawdown_series`。
pub fn drawdown_series(prices: &[f64]) -> Vec<f64> {
    let mut peak = prices[0];
    let mut out = Vec::new();
    for p in prices {
        peak = peak.max(*p);
        out.push((peak - p) / peak);
    }
    out
}

/// 真源 `sharpe`。
pub fn sharpe(rets: &[f64], rf_annual: f64, af: i64) -> f64 {
    let sd = stdev(rets);
    if sd == 0.0 {
        return 0.0;
    }
    let rf_period = (1.0 + rf_annual).powf(1.0 / af as f64) - 1.0;
    (mean_of(rets) - rf_period) / sd * (af as f64).sqrt()
}

/// 真源 `calmar`。
pub fn calmar(annual_ret: f64, mdd: f64) -> f64 {
    if mdd == 0.0 {
        0.0
    } else {
        annual_ret / mdd
    }
}

/// 真源 `tracking_error`。
pub fn tracking_error(rets: &[f64], bench: &[f64], af: i64) -> f64 {
    let n = rets.len().min(bench.len());
    if n < 2 {
        return 0.0;
    }
    let active: Vec<f64> = (0..n).map(|i| rets[i] - bench[i]).collect();
    stdev(&active) * (af as f64).sqrt()
}

/// 真源 `information_ratio`。
pub fn information_ratio(rets: &[f64], bench: &[f64], af: i64) -> f64 {
    let n = rets.len().min(bench.len());
    if n < 2 {
        return 0.0;
    }
    let active: Vec<f64> = (0..n).map(|i| rets[i] - bench[i]).collect();
    let sd = stdev(&active);
    if sd == 0.0 {
        return 0.0;
    }
    mean_of(&active) / sd * (af as f64).sqrt()
}

/// 真源 `_rank`（平均秩，并列取平均）。
pub fn rank(xs: &[f64]) -> Vec<f64> {
    let mut order: Vec<usize> = (0..xs.len()).collect();
    order.sort_by(|a, b| xs[*a].partial_cmp(&xs[*b]).unwrap_or(std::cmp::Ordering::Equal));
    let mut ranks = vec![0.0; xs.len()];
    let mut i = 0usize;
    while i < order.len() {
        let mut j = i;
        while j + 1 < order.len() && xs[order[j + 1]] == xs[order[i]] {
            j += 1;
        }
        let avg = (i + j) as f64 / 2.0 + 1.0;
        for k in i..=j {
            ranks[order[k]] = avg;
        }
        i = j + 1;
    }
    ranks
}

/// 真源 `_pearson`。
pub fn pearson(a: &[f64], b: &[f64]) -> f64 {
    let n = a.len().min(b.len());
    if n < 2 {
        return 0.0;
    }
    let ma = mean_of(&a[..n]);
    let mb = mean_of(&b[..n]);
    let num: f64 = (0..n).map(|i| (a[i] - ma) * (b[i] - mb)).sum();
    let da = (0..n).map(|i| (a[i] - ma).powi(2)).sum::<f64>().sqrt();
    let db = (0..n).map(|i| (b[i] - mb).powi(2)).sum::<f64>().sqrt();
    if da == 0.0 || db == 0.0 {
        0.0
    } else {
        num / (da * db)
    }
}

/// 真源 `information_coefficient`。
pub fn information_coefficient(factor: &[f64], fwd: &[f64], method: &str) -> Result<f64, String> {
    match method {
        "spearman" => Ok(pearson(&rank(factor), &rank(fwd))),
        "pearson" => Ok(pearson(factor, fwd)),
        other => Err(format!(
            "IC 口径只支持 spearman / pearson，实为 {}",
            crate::pyval::py_repr(&Json::Str(other.to_string()))
        )),
    }
}

/// 真源 `turnover`。
pub fn turnover(weights: &[Vec<f64>], single_side: bool) -> Vec<f64> {
    let mut out = Vec::new();
    for i in 1..weights.len() {
        let m = weights[i].len().min(weights[i - 1].len());
        let gross: f64 = (0..m).map(|j| (weights[i][j] - weights[i - 1][j]).abs()).sum();
        out.push(if single_side { gross / 2.0 } else { gross });
    }
    out
}

/// 真源 `_block`。
fn block(prices: &[f64], af: i64, rf: f64, kind: &str) -> Result<Json, String> {
    let rets = returns(prices, kind)?;
    let ann = annualized_return(prices, af);
    let mdd = max_drawdown(prices);
    Ok(Json::Object(vec![
        ("cumulative".to_string(), r6(cumulative_return(prices))),
        ("annualized".to_string(), r6(ann)),
        ("volatility_annualized".to_string(), r6(annualized_volatility(&rets, af))),
        ("sharpe".to_string(), r6(sharpe(&rets, rf, af))),
        ("max_drawdown".to_string(), r6(mdd)),
        ("calmar".to_string(), r6(calmar(ann, mdd))),
    ]))
}

fn pstr(params: &[(String, Json)], k: &str, d: &str) -> String {
    match params.iter().find(|(kk, _)| kk == k).map(|(_, v)| v) {
        Some(Json::Str(s)) => s.clone(),
        Some(Json::Null) | None => d.to_string(),
        Some(other) => crate::pyval::plain_str(other),
    }
}

fn pnum(params: &[(String, Json)], k: &str, d: f64) -> f64 {
    match params.iter().find(|(kk, _)| kk == k).map(|(_, v)| v) {
        Some(Json::Int(i)) => *i as f64,
        Some(Json::Float(f)) => *f,
        Some(Json::Bool(b)) => {
            if *b {
                1.0
            } else {
                0.0
            }
        }
        _ => d,
    }
}

fn pbool(params: &[(String, Json)], k: &str, d: bool) -> bool {
    match params.iter().find(|(kk, _)| kk == k).map(|(_, v)| v) {
        Some(Json::Bool(b)) => *b,
        _ => d,
    }
}

/// 真源 `performance_report`（关键字参数走 `params`）。
pub fn performance_report(series: &Json, params: &[(String, Json)]) -> Result<Json, String> {
    let frequency = pstr(params, "frequency", "daily");
    let af = match annual_factor(&frequency) {
        Some(v) => v,
        None => {
            let mut keys = vec!["daily", "weekly", "monthly"];
            keys.sort();
            // 真源是 `sorted(ANNUAL_FACTORS)` 的 **Python 列表 repr**（单引号）
            let shown = crate::pyval::py_repr_list(
                &keys.iter().map(|k| Json::Str(k.to_string())).collect::<Vec<_>>(),
            );
            return Err(format!(
                "频率须在 {} 中，实为 {}",
                shown,
                crate::pyval::py_repr(&Json::Str(frequency))
            ));
        }
    };
    let equity = nums(series, "equity");
    let bench = nums(series, "benchmark");
    let has_bench = bench.len() == equity.len() && !bench.is_empty();
    let period_start = pstr(params, "period_start", "");
    let period_end = pstr(params, "period_end", "");
    let currency = pstr(params, "currency", "CNY");
    let return_basis = pstr(params, "return_basis", "simple");
    let rf = pnum(params, "risk_free_rate_annual", 0.0);
    let benchmark_id = pstr(params, "benchmark_id", "");
    let fee = pnum(params, "cost_bps_fee", 0.0);
    let slip = pnum(params, "cost_bps_slippage", 0.0);
    let fill_rule = pstr(params, "fill_rule", "next_open");
    let single_side = pbool(params, "single_side_turnover", true);
    let as_of = pstr(params, "as_of", "");
    let gross = block(&equity, af, rf, &return_basis)?;
    let rf_txt = crate::pyfloat::repr(rn(rf));
    let fee_txt = crate::pyfloat::repr(rn(fee));
    let slip_txt = crate::pyfloat::repr(rn(slip));
    let effective_as_of = if as_of.is_empty() { period_end.clone() } else { as_of.clone() };
    // ⚠️ `benchmark` / `excess` 先在占位处写 `null`，真有值时**必须覆盖**（真源是
    // `doc["benchmark"] = {...}`）。append 会让同一份 JSON 出现**两个同名键**——
    // 实测（2026-10-04）由此整份报告对不上。
    fn set_key(doc: &mut Vec<(String, Json)>, k: &str, v: Json) {
        match doc.iter_mut().find(|(kk, _)| kk == k) {
            Some(slot) => slot.1 = v,
            None => doc.push((k.to_string(), v)),
        }
    }
    let mut doc: Vec<(String, Json)> = vec![
        ("kind".to_string(), Json::Str("nf-performance/1".to_string())),
        ("as_of".to_string(), Json::Str(effective_as_of)),
        ("currency".to_string(), Json::Str(currency)),
        ("return_basis".to_string(), Json::Str(return_basis.clone())),
        ("frequency".to_string(), Json::Str(frequency.clone())),
        ("annual_factor".to_string(), Json::Int(af)),
        ("risk_free_rate_annual".to_string(), r6(rf)),
        (
            "period".to_string(),
            Json::Object(vec![
                ("start".to_string(), Json::Str(period_start)),
                ("end".to_string(), Json::Str(period_end)),
                ("observations".to_string(), Json::Int(equity.len() as i64)),
            ]),
        ),
        ("gross".to_string(), gross.clone()),
        ("benchmark".to_string(), Json::Null),
        ("excess".to_string(), Json::Null),
        (
            "costs".to_string(),
            Json::Object(vec![
                ("fee_bps".to_string(), r6(fee)),
                ("slippage_bps".to_string(), r6(slip)),
                ("fill_rule".to_string(), Json::Str(fill_rule.clone())),
                (
                    "turnover_basis".to_string(),
                    Json::Str(if single_side { "single_side" } else { "double_side" }.to_string()),
                ),
            ]),
        ),
        (
            "disclosures".to_string(),
            Json::Array(
                vec![
                    format!(
                        "收益口径 = {}；年化因子 = {}（{}）；无风险利率年化 = {}",
                        return_basis, af, frequency, rf_txt
                    ),
                    format!(
                        "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee={} bps, slippage={} bps）",
                        fee_txt, slip_txt
                    ),
                    format!(
                        "成交价假设 = {}（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）",
                        fill_rule
                    ),
                    "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间".to_string(),
                    GIPS_ALIGNMENT.to_string(),
                ]
                .into_iter()
                .map(Json::Str)
                .collect(),
            ),
        ),
    ];
    if has_bench {
        let mut bblock: Vec<(String, Json)> = vec![(
            "id".to_string(),
            Json::Str(if benchmark_id.is_empty() { "UNSPECIFIED".to_string() } else { benchmark_id }),
        )];
        if let Json::Object(o) = block(&bench, af, rf, &return_basis)? {
            bblock.extend(o);
        }
        let gross_ann = match obj_num(&gross, "annualized") {
            v => v,
        };
        let bench_ann = obj_num(&Json::Object(bblock.clone()), "annualized");
        let rets = returns(&equity, &return_basis)?;
        let brets = returns(&bench, &return_basis)?;
        set_key(&mut doc, "benchmark", Json::Object(bblock));
        set_key(
            &mut doc,
            "excess",
            Json::Object(vec![
                ("annualized".to_string(), r6(gross_ann - bench_ann)),
                ("tracking_error".to_string(), r6(tracking_error(&rets, &brets, af))),
                ("information_ratio".to_string(), r6(information_ratio(&rets, &brets, af))),
            ]),
        );
    }
    Ok(Json::Object(doc))
}

fn obj_num(v: &Json, k: &str) -> f64 {
    match v {
        Json::Object(o) => match o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv) {
            Some(Json::Float(f)) => *f,
            Some(Json::Int(i)) => *i as f64,
            _ => 0.0,
        },
        _ => 0.0,
    }
}

/// 真源 `vega_equity_curve`。
pub fn vega_equity_curve(series: &Json, title: &str) -> Json {
    let dates = str_list(series, "dates");
    let equity = nums(series, "equity");
    let bench = nums(series, "benchmark");
    let mut data: Vec<Json> = Vec::new();
    for (d, v) in dates.iter().zip(equity.iter()) {
        data.push(Json::Object(vec![
            ("date".to_string(), Json::Str(d.clone())),
            ("series".to_string(), Json::Str("策略".to_string())),
            ("value".to_string(), Json::Float(*v)),
        ]));
    }
    if !bench.is_empty() {
        for (d, v) in dates.iter().zip(bench.iter()) {
            data.push(Json::Object(vec![
                ("date".to_string(), Json::Str(d.clone())),
                ("series".to_string(), Json::Str("基准".to_string())),
                ("value".to_string(), Json::Float(*v)),
            ]));
        }
    }
    Json::Object(vec![
        (
            "$schema".to_string(),
            Json::Str("https://vega.github.io/schema/vega-lite/v5.json".to_string()),
        ),
        ("description".to_string(), Json::Str(title.to_string())),
        (
            "data".to_string(),
            Json::Object(vec![("values".to_string(), Json::Array(data))]),
        ),
        (
            "mark".to_string(),
            Json::Object(vec![
                ("type".to_string(), Json::Str("line".to_string())),
                ("point".to_string(), Json::Bool(false)),
            ]),
        ),
        (
            "encoding".to_string(),
            Json::Object(vec![
                (
                    "x".to_string(),
                    Json::Object(vec![
                        ("field".to_string(), Json::Str("date".to_string())),
                        ("type".to_string(), Json::Str("temporal".to_string())),
                        ("title".to_string(), Json::Str("日期".to_string())),
                    ]),
                ),
                (
                    "y".to_string(),
                    Json::Object(vec![
                        ("field".to_string(), Json::Str("value".to_string())),
                        ("type".to_string(), Json::Str("quantitative".to_string())),
                        ("title".to_string(), Json::Str("净值".to_string())),
                        (
                            "scale".to_string(),
                            Json::Object(vec![("zero".to_string(), Json::Bool(false))]),
                        ),
                    ]),
                ),
                (
                    "color".to_string(),
                    Json::Object(vec![
                        ("field".to_string(), Json::Str("series".to_string())),
                        ("type".to_string(), Json::Str("nominal".to_string())),
                        ("title".to_string(), Json::Str(String::new())),
                    ]),
                ),
            ]),
        ),
    ])
}

fn str_list(series: &Json, key: &str) -> Vec<String> {
    match series {
        Json::Object(o) => match o.iter().find(|(k, _)| k == key).map(|(_, v)| v) {
            Some(Json::Array(a)) => a.iter().map(crate::pyval::plain_str).collect(),
            _ => Vec::new(),
        },
        _ => Vec::new(),
    }
}

/// 真源 `vega_drawdown`。
pub fn vega_drawdown(series: &Json, title: &str) -> Json {
    let dd = drawdown_series(&nums(series, "equity"));
    let dates = str_list(series, "dates");
    let data: Vec<Json> = dates
        .iter()
        .zip(dd.iter())
        .map(|(d, v)| {
            Json::Object(vec![
                ("date".to_string(), Json::Str(d.clone())),
                ("value".to_string(), Json::Float(-v.abs())),
            ])
        })
        .collect();
    Json::Object(vec![
        (
            "$schema".to_string(),
            Json::Str("https://vega.github.io/schema/vega-lite/v5.json".to_string()),
        ),
        ("description".to_string(), Json::Str(title.to_string())),
        (
            "data".to_string(),
            Json::Object(vec![("values".to_string(), Json::Array(data))]),
        ),
        (
            "mark".to_string(),
            Json::Object(vec![
                ("type".to_string(), Json::Str("area".to_string())),
                ("line".to_string(), Json::Bool(true)),
            ]),
        ),
        (
            "encoding".to_string(),
            Json::Object(vec![
                (
                    "x".to_string(),
                    Json::Object(vec![
                        ("field".to_string(), Json::Str("date".to_string())),
                        ("type".to_string(), Json::Str("temporal".to_string())),
                        ("title".to_string(), Json::Str("日期".to_string())),
                    ]),
                ),
                (
                    "y".to_string(),
                    Json::Object(vec![
                        ("field".to_string(), Json::Str("value".to_string())),
                        ("type".to_string(), Json::Str("quantitative".to_string())),
                        ("title".to_string(), Json::Str("回撤".to_string())),
                        (
                            "scale".to_string(),
                            Json::Object(vec![("zero".to_string(), Json::Bool(true))]),
                        ),
                    ]),
                ),
            ]),
        ),
    ])
}

/// 真源 `mermaid_declaration_flow`（**静态文本**，末尾带换行）。
pub fn mermaid_declaration_flow() -> String {
    [
        "%% 口径声明链（QUANT_METRICS 口径纪律的可视化，非新增真源）",
        "flowchart LR",
        "  A[收益口径 simple/log] --> D[绩效报告]",
        "  B[年化因子 252/52/12] --> D",
        "  C[无风险利率 rf] --> D",
        "  E[净值序列] --> D",
        "  D --> F[披露面 disclosures]",
        "  G[成本与滑点申报] --> F",
        "  H[基准与成交价假设] --> F",
    ]
    .join("\n")
        + "\n"
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_quant_metrics_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== ① 真语料 performance-report 条目：`load_equity_curve` + `performance_report` =====
    #[test]
    fn quant_metrics_matches_truth_source_over_corpus() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &str, &str, &str)] = &[
        (r#"量化金融域包"#, r#"community/量化金融域包/outputs/samples/EQUITY_CURVE.csv"#, r#"{"as_of": "2026-08-21", "benchmark_id": "NF-SAMPLE-INDEX", "cost_bps_fee": 3.0, "cost_bps_slippage": 5.0, "currency": "CNY", "fill_rule": "next_open", "frequency": "daily", "period_end": "2026-08-21", "period_start": "2026-06-01", "return_basis": "simple", "risk_free_rate_annual": 0.015, "single_side_turnover": true}"#, r#"{"annual_factor": 252, "as_of": "2026-08-21", "benchmark": {"annualized": 0.143635, "calmar": 8.516894, "cumulative": 0.031922, "id": "NF-SAMPLE-INDEX", "max_drawdown": 0.016865, "sharpe": 6.473536, "volatility_annualized": 0.018464}, "costs": {"fee_bps": 3.0, "fill_rule": "next_open", "slippage_bps": 5.0, "turnover_basis": "single_side"}, "currency": "CNY", "disclosures": ["收益口径 = simple；年化因子 = 252（daily）；无风险利率年化 = 0.015", "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=3.0 bps, slippage=5.0 bps）", "成交价假设 = next_open（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）", "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间", "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据"], "excess": {"annualized": 0.190837, "information_ratio": 8.40542, "tracking_error": 0.018409}, "frequency": "daily", "gross": {"annualized": 0.334472, "calmar": 15.541439, "cumulative": 0.069888, "max_drawdown": 0.021521, "sharpe": 9.049606, "volatility_annualized": 0.030307}, "kind": "nf-performance/1", "period": {"end": "2026-08-21", "observations": 60, "start": "2026-06-01"}, "return_basis": "simple", "risk_free_rate_annual": 0.015}"#),
        ];
        let mut ok = 0usize;
        for (pkg, src, params_s, want_s) in cases {
            let series = load_equity_curve(&root.join(src))
                .unwrap_or_else(|e| panic!("{} 读净值 {} 失败：{}", pkg, src, e));
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(params_s).unwrap(),
            )
            .unwrap();
            let params: Vec<(String, Json)> = match spec {
                Json::Object(o) => o,
                _ => Vec::new(),
            };
            let got = performance_report(&series, &params).expect("performance_report");
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_s).unwrap(),
            )
            .unwrap();
            assert!(
                crate::jsonread::json_eq(&got, &want),
                "{} 报告不一致\n  实得 {}\n  期望 {}",
                pkg,
                got.dumps_default(),
                want.dumps_default()
            );
            ok += 1;
        }
        assert!(ok > 0, "至少要真跑若干条");
    }

    /// ===== ② `load_equity_curve` 的六条分支（含四类错误支）=====
    #[test]
    fn load_equity_curve_branches_match_truth() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &str)] = &[
        (r#"good.csv"#, r#""#),
        (r#"nobench.csv"#, r#""#),
        (r#"badcol.csv"#, r#"缺列 equity（实际列：['date', 'value']）"#),
        (r#"short.csv"#, r#"样本过短（< 3 个净值点）"#),
        (r#"nonpos.csv"#, r#"净值须为正数（口径：净值序列，非累计收益）"#),
        (r#"badnum.csv"#, r#"第 3 行数值不可解析"#),
        ];
        for (name, err) in cases {
            let src = format!("engine/rust/target/test-fixtures/quant/{}", name);
            let got = load_equity_curve(&root.join(&src));
            if err.is_empty() {
                assert!(got.is_ok(), "{} 真源成功、本线报错：{:?}", name, got.err());
            } else {
                match got {
                    Ok(v) => panic!("{} 真源报错、本线成功：{}", name, v.dumps_default()),
                    Err(e) => assert_eq!(&e, err, "{} 的报错文本", name),
                }
            }
        }
    }

    /// ===== ③ `performance_report` 的参数支（基准 / log 口径 / 各频率 / 非默认参数）=====
    ///
    /// 真语料只 1 条且不含基准 ⇒ 这些支必须用合成净值踩，否则等于没核。
    #[test]
    fn performance_report_variants_match_truth() {
        let root = crate::testutil::repo_root();
        let src = root.join("engine/rust/target/test-fixtures/quant/good.csv");
        let series = load_equity_curve(&src).expect("读 good.csv");
        let cases: &[(&str, &str, &str)] = &[
        (r#"默认"#, r#"{"period_end": "2026-01-05", "period_start": "2026-01-01"}"#, r#"{"annual_factor": 252, "as_of": "2026-01-05", "benchmark": {"annualized": 1.554822, "calmar": 314.074061, "cumulative": 0.015, "id": "UNSPECIFIED", "max_drawdown": 0.00495, "sharpe": 5.842306, "volatility_annualized": 0.162537}, "costs": {"fee_bps": 0.0, "fill_rule": "next_open", "slippage_bps": 0.0, "turnover_basis": "single_side"}, "currency": "CNY", "disclosures": ["收益口径 = simple；年化因子 = 252（daily）；无风险利率年化 = 0.0", "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=0.0 bps, slippage=0.0 bps）", "成交价假设 = next_open（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）", "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间", "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据"], "excess": {"annualized": 3.883092, "information_ratio": 3.65147, "tracking_error": 0.270524}, "frequency": "daily", "gross": {"annualized": 5.437914, "calmar": 285.490474, "cumulative": 0.03, "max_drawdown": 0.019048, "sharpe": 4.516079, "volatility_annualized": 0.429001}, "kind": "nf-performance/1", "period": {"end": "2026-01-05", "observations": 5, "start": "2026-01-01"}, "return_basis": "simple", "risk_free_rate_annual": 0.0}"#),
        (r#"基准"#, r#"{"benchmark_id": "CSI300", "period_end": "2026-01-05", "period_start": "2026-01-01"}"#, r#"{"annual_factor": 252, "as_of": "2026-01-05", "benchmark": {"annualized": 1.554822, "calmar": 314.074061, "cumulative": 0.015, "id": "CSI300", "max_drawdown": 0.00495, "sharpe": 5.842306, "volatility_annualized": 0.162537}, "costs": {"fee_bps": 0.0, "fill_rule": "next_open", "slippage_bps": 0.0, "turnover_basis": "single_side"}, "currency": "CNY", "disclosures": ["收益口径 = simple；年化因子 = 252（daily）；无风险利率年化 = 0.0", "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=0.0 bps, slippage=0.0 bps）", "成交价假设 = next_open（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）", "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间", "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据"], "excess": {"annualized": 3.883092, "information_ratio": 3.65147, "tracking_error": 0.270524}, "frequency": "daily", "gross": {"annualized": 5.437914, "calmar": 285.490474, "cumulative": 0.03, "max_drawdown": 0.019048, "sharpe": 4.516079, "volatility_annualized": 0.429001}, "kind": "nf-performance/1", "period": {"end": "2026-01-05", "observations": 5, "start": "2026-01-01"}, "return_basis": "simple", "risk_free_rate_annual": 0.0}"#),
        (r#"log 口径"#, r#"{"period_end": "2026-01-05", "period_start": "2026-01-01", "return_basis": "log"}"#, r#"{"annual_factor": 252, "as_of": "2026-01-05", "benchmark": {"annualized": 1.554822, "calmar": 314.074061, "cumulative": 0.015, "id": "UNSPECIFIED", "max_drawdown": 0.00495, "sharpe": 5.795338, "volatility_annualized": 0.161851}, "costs": {"fee_bps": 0.0, "fill_rule": "next_open", "slippage_bps": 0.0, "turnover_basis": "single_side"}, "currency": "CNY", "disclosures": ["收益口径 = log；年化因子 = 252（daily）；无风险利率年化 = 0.0", "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=0.0 bps, slippage=0.0 bps）", "成交价假设 = next_open（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）", "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间", "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据"], "excess": {"annualized": 3.883092, "information_ratio": 3.460144, "tracking_error": 0.267105}, "frequency": "daily", "gross": {"annualized": 5.437914, "calmar": 285.490474, "cumulative": 0.03, "max_drawdown": 0.019048, "sharpe": 4.382818, "volatility_annualized": 0.424887}, "kind": "nf-performance/1", "period": {"end": "2026-01-05", "observations": 5, "start": "2026-01-01"}, "return_basis": "log", "risk_free_rate_annual": 0.0}"#),
        (r#"周频"#, r#"{"frequency": "weekly", "period_end": "2026-01-05", "period_start": "2026-01-01"}"#, r#"{"annual_factor": 52, "as_of": "2026-01-05", "benchmark": {"annualized": 0.213552, "calmar": 43.137594, "cumulative": 0.015, "id": "UNSPECIFIED", "max_drawdown": 0.00495, "sharpe": 2.653907, "volatility_annualized": 0.073834}, "costs": {"fee_bps": 0.0, "fill_rule": "next_open", "slippage_bps": 0.0, "turnover_basis": "single_side"}, "currency": "CNY", "disclosures": ["收益口径 = simple；年化因子 = 52（weekly）；无风险利率年化 = 0.0", "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=0.0 bps, slippage=0.0 bps）", "成交价假设 = next_open（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）", "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间", "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据"], "excess": {"annualized": 0.254982, "information_ratio": 1.658705, "tracking_error": 0.122887}, "frequency": "weekly", "gross": {"annualized": 0.468534, "calmar": 24.59802, "cumulative": 0.03, "max_drawdown": 0.019048, "sharpe": 2.051459, "volatility_annualized": 0.194877}, "kind": "nf-performance/1", "period": {"end": "2026-01-05", "observations": 5, "start": "2026-01-01"}, "return_basis": "simple", "risk_free_rate_annual": 0.0}"#),
        (r#"月频"#, r#"{"benchmark_id": "B1", "frequency": "monthly", "period_end": "2026-01-05", "period_start": "2026-01-01"}"#, r#"{"annual_factor": 12, "as_of": "2026-01-05", "benchmark": {"annualized": 0.045678, "calmar": 9.227032, "cumulative": 0.015, "id": "B1", "max_drawdown": 0.00495, "sharpe": 1.274896, "volatility_annualized": 0.035469}, "costs": {"fee_bps": 0.0, "fill_rule": "next_open", "slippage_bps": 0.0, "turnover_basis": "single_side"}, "currency": "CNY", "disclosures": ["收益口径 = simple；年化因子 = 12（monthly）；无风险利率年化 = 0.0", "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=0.0 bps, slippage=0.0 bps）", "成交价假设 = next_open（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）", "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间", "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据"], "excess": {"annualized": 0.047049, "information_ratio": 0.796816, "tracking_error": 0.059033}, "frequency": "monthly", "gross": {"annualized": 0.092727, "calmar": 4.868167, "cumulative": 0.03, "max_drawdown": 0.019048, "sharpe": 0.985489, "volatility_annualized": 0.093616}, "kind": "nf-performance/1", "period": {"end": "2026-01-05", "observations": 5, "start": "2026-01-01"}, "return_basis": "simple", "risk_free_rate_annual": 0.0}"#),
        (r#"非默认参数"#, r#"{"as_of": "2026-02-01", "benchmark_id": "SPX", "cost_bps_fee": 8.5, "cost_bps_slippage": 3.25, "currency": "USD", "fill_rule": "close", "period_end": "2026-01-05", "period_start": "2026-01-01", "risk_free_rate_annual": 0.03, "single_side_turnover": false}"#, r#"{"annual_factor": 252, "as_of": "2026-02-01", "benchmark": {"annualized": 1.554822, "calmar": 314.074061, "cumulative": 0.015, "id": "SPX", "max_drawdown": 0.00495, "sharpe": 5.660437, "volatility_annualized": 0.162537}, "costs": {"fee_bps": 8.5, "fill_rule": "close", "slippage_bps": 3.25, "turnover_basis": "double_side"}, "currency": "USD", "disclosures": ["收益口径 = simple；年化因子 = 252（daily）；无风险利率年化 = 0.03", "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=8.5 bps, slippage=3.25 bps）", "成交价假设 = close（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）", "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间", "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据"], "excess": {"annualized": 3.883092, "information_ratio": 3.65147, "tracking_error": 0.270524}, "frequency": "daily", "gross": {"annualized": 5.437914, "calmar": 285.490474, "cumulative": 0.03, "max_drawdown": 0.019048, "sharpe": 4.447174, "volatility_annualized": 0.429001}, "kind": "nf-performance/1", "period": {"end": "2026-01-05", "observations": 5, "start": "2026-01-01"}, "return_basis": "simple", "risk_free_rate_annual": 0.03}"#),
        ];
        for (name, params_s, want_s) in cases {
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(params_s).unwrap(),
            )
            .unwrap();
            let params: Vec<(String, Json)> = match spec {
                Json::Object(o) => o,
                _ => Vec::new(),
            };
            let got = performance_report(&series, &params).expect("performance_report");
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_s).unwrap(),
            )
            .unwrap();
            assert!(
                crate::jsonread::json_eq(&got, &want),
                "{} 报告不一致\n  实得 {}\n  期望 {}",
                name,
                got.dumps_default(),
                want.dumps_default()
            );
        }
        // 错频必须报错（不得静默兜底）
        let bad = vec![("frequency".to_string(), Json::Str("hourly".to_string()))];
        match performance_report(&series, &bad) {
            Ok(_) => panic!("错频竟然成功"),
            Err(e) => assert_eq!(e, r#"频率须在 ['daily', 'monthly', 'weekly'] 中，实为 'hourly'"#, "错频报错文本"),
        }
    }
    /// ===== ④ 家族助手与几何口径（真语料的判据路径**不经过**它们，必须单独核）=====
    ///
    /// 覆盖 `_rank`（含并列与空表）/ `_pearson`（含零方差）/ `information_coefficient`
    /// （spearman + pearson + **错口径必须报错**）/ `turnover`（单边与双边）/ 以及
    /// `annualized_return`/`annualized_volatility`/`max_drawdown`/`sharpe`（含 mdd=0）/
    /// `tracking_error`（样本不足）/ `information_ratio`（零标准差）/ `log_returns` 等边界。
    #[test]
    fn quant_metrics_family_helpers_match_truth() {
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"ic_pearson": [0.998633], "ic_spearman": [1.0, 0.771517], "pearson": [0.998633, 0.786373, 0.0, 0.0], "rank": [[1.0, 4.0, 2.0, 6.0, 3.0, 5.0], [1.0, 2.5, 2.5, 5.0, 5.0, 5.0], [1.0], []], "turnover_double": [[0.2, 0.6, 0.0]], "turnover_single": [[0.1, 0.3, 0.0], [], []]}"#).unwrap(),
        )
        .unwrap();
        let get = |k: &str| -> Json {
            match &want {
                Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, v)| v.clone()),
                _ => None,
            }
            .unwrap_or(Json::Null)
        };
        let factor = [0.1f64, 0.5, 0.2, 0.9, 0.4, 0.7];
        let fwd = [0.02f64, 0.11, 0.05, 0.2, 0.09, 0.15];
        let tied = [1.0f64, 2.0, 2.0, 3.0, 3.0, 3.0];
        let jf = |v: &[f64]| Json::Array(v.iter().map(|x| Json::Float(*x)).collect());
        let ranks = match get("rank") {
            Json::Array(a) => a,
            _ => Vec::new(),
        };
        assert_eq!(
            Json::Array(rank(&factor).iter().map(|x| r6(*x)).collect()),
            ranks[0], "rank(factor)");
        assert_eq!(
            Json::Array(rank(&tied).iter().map(|x| r6(*x)).collect()),
            ranks[1], "rank(并列)");
        assert_eq!(
            Json::Array(rank(&[5.0]).iter().map(|x| r6(*x)).collect()),
            ranks[2], "rank(单元素)");
        assert_eq!(
            Json::Array(rank(&[]).iter().map(|x| r6(*x)).collect()),
            ranks[3], "rank(空表)");
        let ps = match get("pearson") {
            Json::Array(a) => a,
            _ => Vec::new(),
        };
        for (i, (x, y)) in [(&factor[..], &fwd[..]), (&tied[..], &factor[..])].iter().enumerate() {
            assert_eq!(r6(pearson(x, y)), ps[i], "pearson 第 {} 例", i);
        }
        assert_eq!(r6(pearson(&[1.0], &[2.0])), ps[2], "pearson 样本不足");
        assert_eq!(r6(pearson(&[1.0, 1.0], &[2.0, 3.0])), ps[3], "pearson 零方差");
        let ics = match get("ic_spearman") {
            Json::Array(a) => a,
            _ => Vec::new(),
        };
        assert_eq!(
            r6(information_coefficient(&factor, &fwd, "spearman").unwrap()),
            ics[0],
            "IC spearman"
        );
        assert_eq!(
            r6(information_coefficient(&tied, &fwd, "spearman").unwrap()),
            ics[1],
            "IC spearman（并列）"
        );
        let icp = match get("ic_pearson") {
            Json::Array(a) => a,
            _ => Vec::new(),
        };
        assert_eq!(
            r6(information_coefficient(&factor, &fwd, "pearson").unwrap()),
            icp[0],
            "IC pearson"
        );
        match information_coefficient(&factor, &fwd, "kendall") {
            Ok(_) => panic!("IC 错口径竟然成功"),
            Err(e) => assert_eq!(e, r#"IC 口径只支持 spearman / pearson，实为 'kendall'"#, "IC 错口径报错文本"),
        }
        let w1 = vec![vec![0.5, 0.5], vec![0.6, 0.4], vec![0.3, 0.7], vec![0.3, 0.7]];
        let ts = match get("turnover_single") {
            Json::Array(a) => a,
            _ => Vec::new(),
        };
        let jv = |v: &[f64]| Json::Array(v.iter().map(|x| r6(*x)).collect());
        assert_eq!(jv(&turnover(&w1, true)), ts[0], "turnover 单边");
        assert_eq!(jv(&turnover(&[], true)), ts[1], "turnover 空");
        assert_eq!(jv(&turnover(&[vec![1.0]], true)), ts[2], "turnover 单期");
        let td = match get("turnover_double") {
            Json::Array(a) => a,
            _ => Vec::new(),
        };
        assert_eq!(jv(&turnover(&w1, false)), td[0], "turnover 双边");

        let geom: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"annualized_return_daily": 125491.736516, "calmar_zero_mdd": 0.0, "cumulative_return": 0.5, "information_ratio_zero_sd": 0.0, "log_returns": [0.09531, 0.09531], "max_drawdown": 0.25, "sharpe": 4.155689, "tracking_error_short": 0.0, "volatility": 0.3995}"#).unwrap(),
        )
        .unwrap();
        let g = |k: &str| -> Json {
            match &geom {
                Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, v)| v.clone()),
                _ => None,
            }
            .unwrap_or(Json::Null)
        };
        assert_eq!(
            r6(annualized_return(&[1.0, 1.1, 1.2, 1.15], 252)),
            g("annualized_return_daily")
        );
        assert_eq!(
            r6(annualized_volatility(&[0.01, -0.02, 0.03], 252)),
            g("volatility")
        );
        assert_eq!(r6(max_drawdown(&[1.0, 1.2, 0.9, 1.1])), g("max_drawdown"));
        assert_eq!(r6(sharpe(&[0.01, -0.02, 0.03], 0.02, 252)), g("sharpe"));
        assert_eq!(r6(calmar(0.1, 0.0)), g("calmar_zero_mdd"));
        assert_eq!(
            r6(tracking_error(&[0.1], &[0.2], 252)),
            g("tracking_error_short")
        );
        assert_eq!(
            r6(information_ratio(&[0.1, 0.1], &[0.1, 0.1], 252)),
            g("information_ratio_zero_sd")
        );
        assert_eq!(
            Json::Array(log_returns(&[1.0, 1.1, 1.21]).iter().map(|x| r6(*x)).collect()),
            g("log_returns")
        );
        assert_eq!(r6(cumulative_return(&[1.0, 1.5])), g("cumulative_return"));
        match returns(&[1.0, 2.0], "log2") {
            Ok(_) => panic!("returns 错口径竟然成功"),
            Err(e) => assert_eq!(e, r#"收益口径只支持 simple / log，实为 'log2'"#, "returns 错口径报错文本"),
        }
    }
    // <<< GENERATED
}
