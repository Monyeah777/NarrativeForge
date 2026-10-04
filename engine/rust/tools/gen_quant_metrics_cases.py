"""为 `quant_metrics` 生成差分判据。

① **真语料**：`performance-report` 的 T4 条目，按 `_gen_performance_report` 的真路径跑
   `load_equity_curve` + `performance_report`；
② **合成**：真语料只 1 条且不含基准 ⇒ 含基准支、log 口径、各频率、非默认参数、
   以及 `load_equity_curve` / `performance_report` 的**错误支**都必须用合成夹具踩。

用法：python engine/rust/tools/gen_quant_metrics_cases.py
"""
import glob
import json
import pathlib
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
sys.path.insert(0, str(ROOT / 'engine' / 'rust' / 'tools'))
from _rustlit import raw as rr  # noqa: E402
from core import output_forms as of  # noqa: E402
from core import quant_metrics as qm  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'quant'
FIX.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- ① 真语料
reals = []
for f in sorted(glob.glob('community/*/outputs/INDEX.json')):
    pkg = pathlib.Path(f).parts[1]
    try:
        idx = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    for e in idx.get('outputs') or []:
        if e.get('tier') != 'T4' or of._gen_id(e) != 'performance-report':
            continue
        spec = e.get('recompute') or e.get('render') or {}
        inputs = spec.get('inputs') or []
        params = dict(spec.get('params') or {})
        src = 'community/%s/%s' % (pkg, str(inputs[0]).lstrip('/')) if inputs else ''
        series, err = qm.load_equity_curve(ROOT / src) if src else ({}, '缺 inputs')
        if err:
            print('# 真语料 %s 读取失败: %s' % (pkg, err))
            continue
        got = qm.performance_report(series, **params)
        reals.append((pkg, src, params, got))
print('# 真语料 performance-report 条目 %d 条' % len(reals))

# ---------------------------------------------------------------- ② 合成
def mk(rows, name):
    p = FIX / name
    p.write_text(rows, encoding='utf-8', newline='')
    return str(p.relative_to(ROOT)).replace('\\', '/')


GOOD = "date,equity,benchmark\n2026-01-01,1.00,1.00\n2026-01-02,1.02,1.01\n2026-01-03,1.01,1.005\n2026-01-04,1.05,1.02\n2026-01-05,1.03,1.015\n"
NOBENCH = "date,equity\n2026-01-01,1.00\n2026-01-02,0.98\n2026-01-03,1.04\n2026-01-04,1.02\n"
BADCOL = "date,value\n2026-01-01,1.00\n"
SHORT = "date,equity\n2026-01-01,1.00\n2026-01-02,1.01\n"
NONPOS = "date,equity\n2026-01-01,1.00\n2026-01-02,0.00\n2026-01-03,1.02\n"
BADNUM = "date,equity\n2026-01-01,1.00\n2026-01-02,abc\n2026-01-03,1.02\n"

load_cases = []
for name, body in (('good.csv', GOOD), ('nobench.csv', NOBENCH), ('badcol.csv', BADCOL),
                   ('short.csv', SHORT), ('nonpos.csv', NONPOS), ('badnum.csv', BADNUM)):
    src = mk(body, name)
    series, err = qm.load_equity_curve(ROOT / src)
    load_cases.append((name, src, err, series if not err else None))
    print('# load %-12s → %s' % (name, ('err: ' + err) if err else 'ok'))

series_good, _ = qm.load_equity_curve(ROOT / mk(GOOD, 'good.csv'))
BASE = {'period_start': '2026-01-01', 'period_end': '2026-01-05'}
rep_cases = []
variants = [
    ('默认', dict(BASE)),
    ('基准', {**BASE, 'benchmark_id': 'CSI300'}),
    ('log 口径', {**BASE, 'return_basis': 'log'}),
    ('周频', {**BASE, 'frequency': 'weekly'}),
    ('月频', {**BASE, 'frequency': 'monthly', 'benchmark_id': 'B1'}),
    ('非默认参数', {**BASE, 'currency': 'USD', 'risk_free_rate_annual': 0.03,
                    'cost_bps_fee': 8.5, 'cost_bps_slippage': 3.25,
                    'fill_rule': 'close', 'single_side_turnover': False,
                    'as_of': '2026-02-01', 'benchmark_id': 'SPX'}),
]
for name, kw in variants:
    got = qm.performance_report(series_good, **kw)
    rep_cases.append((name, kw, got))
    print('# report %-10s → cumulative=%s sharpe=%s benchmark=%s'
          % (name, got['gross']['cumulative'], got['gross']['sharpe'],
             'yes' if got['benchmark'] else 'no'))
try:
    qm.performance_report(series_good, **BASE, frequency='hourly')
    print('# !! hourly 未报错')
except ValueError as exc:
    err_freq = str(exc)
    print('# report 错频          → %s' % err_freq[:90])



# ---------------------------------------------------------------- ④ 家族助手（真语料判据路径不经过）
FACTOR = [0.1, 0.5, 0.2, 0.9, 0.4, 0.7]
FWD = [0.02, 0.11, 0.05, 0.2, 0.09, 0.15]
TIED = [1.0, 2.0, 2.0, 3.0, 3.0, 3.0]
W1 = [[0.5, 0.5], [0.6, 0.4], [0.3, 0.7], [0.3, 0.7]]
def _rr(x):
    """标量 → `_r()`（6 位）；列表逐项。判据侧同样过 `r6()`，两侧口径一致。"""
    if isinstance(x, list):
        return [_rr(v) for v in x]
    return qm._r(x) if isinstance(x, (int, float)) else x


HELPER = {
    'rank': [_rr(qm._rank(x)) for x in (FACTOR, TIED, [5.0], [])],
    'pearson': [_rr(x) for x in (qm._pearson(FACTOR, FWD), qm._pearson(TIED, FACTOR),
                                 qm._pearson([1.0], [2.0]), qm._pearson([1.0, 1.0], [2.0, 3.0]))],
    'ic_spearman': [_rr(qm.information_coefficient(FACTOR, FWD)),
                    _rr(qm.information_coefficient(TIED, FWD))],
    'ic_pearson': [_rr(qm.information_coefficient(FACTOR, FWD, method='pearson'))],
    'turnover_single': [_rr(qm.turnover(W1)), _rr(qm.turnover([])), _rr(qm.turnover([[1.0]]))],
    'turnover_double': [_rr(qm.turnover(W1, single_side=False))],
}
for k, v in HELPER.items():
    print('# 家族助手 %-16s %s' % (k, json.dumps(v, ensure_ascii=False)[:90]))
try:
    qm.information_coefficient(FACTOR, FWD, method='kendall')
    print('# !! IC 非法口径未报错')
except ValueError as exc:
    IC_ERR = str(exc)
    print('# 家族助手 ic 错口径      %s' % IC_ERR[:80])
try:
    qm.returns([1.0, 2.0], kind='log2')
    TYPE_ERR = ''
except ValueError as exc:
    TYPE_ERR = str(exc)
    print('# 家族助手 returns 错口径 %s' % TYPE_ERR[:80])
# ⚠️ 标量一律过 `qm._r()`（真源报告里同样是 6 位）：Python 的 `**` 与 Rust 的 `powf`
# 在位级上会有末位差，拿**未舍入**的原始值当期望值会被这点差判红——那不是真分歧。
GEOM = {
    'annualized_return_daily': qm._r(qm.annualized_return([1.0, 1.1, 1.2, 1.15], 252)),
    'volatility': qm._r(qm.annualized_volatility([0.01, -0.02, 0.03], 252)),
    'max_drawdown': qm._r(qm.max_drawdown([1.0, 1.2, 0.9, 1.1])),
    'sharpe': qm._r(qm.sharpe([0.01, -0.02, 0.03], 0.02, 252)),
    'calmar_zero_mdd': qm._r(qm.calmar(0.1, 0.0)),
    'tracking_error_short': qm._r(qm.tracking_error([0.1], [0.2], 252)),
    'information_ratio_zero_sd': qm._r(qm.information_ratio([0.1, 0.1], [0.1, 0.1], 252)),
    'log_returns': [qm._r(x) for x in qm.log_returns([1.0, 1.1, 1.21])],
    'cumulative_return': qm._r(qm.cumulative_return([1.0, 1.5])),
}
for k, v in GEOM.items():
    print('# 几何口径 %-24s %s' % (k, v))


def arr(v):
    return "&[%s]" % ", ".join(rr(str(x)) for x in v)


HELP_JSON = json.dumps(HELPER, ensure_ascii=False, sort_keys=True)
GEOM_JSON = json.dumps(GEOM, ensure_ascii=False, sort_keys=True)

TEMPLATE = r'''
    // >>> GENERATED by tools/gen_quant_metrics_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== ① 真语料 performance-report 条目：`load_equity_curve` + `performance_report` =====
    #[test]
    fn quant_metrics_matches_truth_source_over_corpus() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &str, &str, &str)] = &[
@@REAL@@
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
@@LOAD@@
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
@@REP@@
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
            Err(e) => assert_eq!(e, @@ERRFREQ@@, "错频报错文本"),
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
            &serde_json::from_str::<serde_json::Value>(@@HELP@@).unwrap(),
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
            Err(e) => assert_eq!(e, @@ICERR@@, "IC 错口径报错文本"),
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
            &serde_json::from_str::<serde_json::Value>(@@GEOM@@).unwrap(),
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
            Err(e) => assert_eq!(e, @@TYPEERR@@, "returns 错口径报错文本"),
        }
    }
    // <<< GENERATED
'''
text = (TEMPLATE
        .replace('@@REAL@@', "\n".join(
            '        (%s, %s, %s, %s),' % (rr(p), rr(src), rr(json.dumps(par, ensure_ascii=False, sort_keys=True)),
                                          rr(json.dumps(got, ensure_ascii=False, sort_keys=True)))
            for p, src, par, got in reals))
        .replace('@@LOAD@@', "\n".join(
            '        (%s, %s),' % (rr(name), rr(err)) for name, _src, err, _s in load_cases))
        .replace('@@REP@@', "\n".join(
            '        (%s, %s, %s),' % (rr(name), rr(json.dumps(kw, ensure_ascii=False, sort_keys=True)),
                                    rr(json.dumps(got, ensure_ascii=False, sort_keys=True)))
            for name, kw, got in rep_cases))
        .replace('@@ERRFREQ@@', rr(err_freq))
        .replace('@@HELP@@', rr(HELP_JSON))
        .replace('@@GEOM@@', rr(GEOM_JSON))
        .replace('@@ICERR@@', rr(IC_ERR))
        .replace('@@TYPEERR@@', rr(TYPE_ERR)))
BEGIN = '    // >>> GENERATED by tools/gen_quant_metrics_cases.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text.split(BEGIN, 1)[1]

path = ROOT / 'engine' / 'rust' / 'src' / 'quant_metrics.rs'
t = path.read_text(encoding='utf-8')
if BEGIN in t:
    a = t.index(BEGIN)
    b = t.index(END, a) + len(END)
    t = t[:a] + block + t[b:]
else:
    t = t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n}\n'
    t = t.rstrip()[:-1].rstrip() + '\n' + block + '}\n'
path.write_text(t, encoding='utf-8', newline='')
print('# 已写入 quant_metrics 判据（真语料 %d / 装载 %d / 参数 %d）'
      % (len(reals), len(load_cases), len(rep_cases)))
