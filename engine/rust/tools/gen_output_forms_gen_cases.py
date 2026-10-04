"""为 `output_forms` 的 13 个生成器生成差分判据。

① **真语料**：全部 T4 条目（`domain-report` 100 / `combo-cert` 4 / `concept-closure` 1 /
   `performance-report` 1），按真源 `GENERATORS[gid](root, {**entry, "_pkg": pkg})` 逐条复算；
② **合成**：另外 9 个生成器真语料从不触发 ⇒ 用**真实产物**当输入造入口（概念图 / 组合证书 /
   域报告 / 净值样例），保证 13 个生成器**全部被踩过**，不留"可达但未核"。

用法：python engine/rust/tools/gen_output_forms_gen_cases.py
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

reals = []
kinds = {}
for f in sorted(glob.glob('community/*/outputs/INDEX.json')):
    pkg = pathlib.Path(f).parts[1]
    try:
        idx = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    for e in idx.get('outputs') or []:
        if e.get('tier') != 'T4':
            continue
        gid = of._gen_id(e)
        if gid not in of.GENERATORS:
            continue
        got, errs = of.GENERATORS[gid](str(ROOT), {**e, '_pkg': pkg})
        kinds[gid] = kinds.get(gid, 0) + 1
        reals.append((pkg, gid, json.dumps({**e, '_pkg': pkg}, ensure_ascii=False, sort_keys=True),
                      'text' if isinstance(got, str) else 'json',
                      (got if isinstance(got, str) else json.dumps(got, ensure_ascii=False, sort_keys=True))
                      if got is not None else '',
                      json.dumps(errs, ensure_ascii=False)))
print('# 真语料 T4 条目 %d 条：%s' % (len(reals), kinds))

# ---------------------------------------------------------------- ② 合成入口
# 产物名按真语料实况取（域报告是 REPORT.json，不是 DOMAIN_REPORT.json）。
def first_artifact(gid):
    for f in sorted(glob.glob('community/*/outputs/INDEX.json')):
        pkg = pathlib.Path(f).parts[1]
        try:
            idx = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        for e in idx.get('outputs') or []:
            if e.get('tier') == 'T4' and of._gen_id(e) == gid:
                return pkg, 'community/%s/%s' % (pkg, e.get('path'))
    return '', ''


cc_pkg, CC = first_artifact('combo-cert')
dr_pkg, DR = first_artifact('domain-report')
pr_pkg, PR = first_artifact('performance-report')
CG = 'community/AI系统域包/assets/CONCEPT_GRAPH.md'
EQ = ''
EQ_REL = ''
if PR:
    try:
        idx = json.load(open('community/%s/outputs/INDEX.json' % pr_pkg, encoding='utf-8'))
        for e in idx.get('outputs') or []:
            if str(e.get('path') or '').endswith(PR.split('/outputs/', 1)[1]):
                ins = ((e.get('recompute') or {}).get('inputs') or [''])[0]
                # 真源 `inputs[0]` 是**包内相对**路径（如 outputs/samples/EQUITY_CURVE.csv）
                EQ_REL = str(ins).lstrip('/')
                EQ = 'community/%s/%s' % (pr_pkg, EQ_REL)
    except Exception:
        pass
print('# 真实产物：combo-cert=%s 域报告=%s 净值=%s' % (CC or '(缺)', DR or '(缺)', EQ or '(缺)'))

synth = []
specs = [
    ('vega-equity-curve', 'recompute', {'id': 'vega-equity-curve',
                                        'inputs': [EQ_REL],
                                        'params': {'title': '自检净值'}}, pr_pkg, EQ),
    ('vega-drawdown', 'recompute', {'id': 'vega-drawdown',
                                    'inputs': [EQ_REL]}, pr_pkg, EQ),
    ('mermaid-declaration-flow', 'recompute', {'id': 'mermaid-declaration-flow'}, '量化金融域包', 'x'),
    ('vega-metrics', 'render', {'id': 'vega-metrics',
                                'inputs': ['outputs/' + DR.split('/outputs/', 1)[-1]],
                                'params': {'title': '域指标图'}}, dr_pkg, DR),
    ('vega-layer-stack', 'render', {'id': 'vega-layer-stack',
                                    'inputs': ['outputs/' + CC.split('/outputs/', 1)[-1]],
                                    'params': {'title': '层位堆叠自检'}}, cc_pkg, CC),
    ('mermaid-layer-load', 'render', {'id': 'mermaid-layer-load',
                                      'inputs': ['outputs/' + CC.split('/outputs/', 1)[-1]]}, cc_pkg, CC),
    ('graphml-module-deps', 'render', {'id': 'graphml-module-deps',
                                       'inputs': ['outputs/' + CC.split('/outputs/', 1)[-1]]}, cc_pkg, CC),
    ('mermaid-concept-dag', 'recompute', {'id': 'mermaid-concept-dag', 'graph': CG},
     'AI系统域包', 'x'),
    ('graphml-concept-dag', 'recompute', {'id': 'graphml-concept-dag', 'graph': CG},
     'AI系统域包', 'x'),
]
for gid, key, spec, pkg, need in specs:
    if not pkg or not need:
        print('# 跳过 %s（缺真实产物）' % gid)
        continue
    entry = {'_pkg': pkg, key: spec}
    got, errs = of.GENERATORS[gid](str(ROOT), entry)
    synth.append(('合成', gid, json.dumps(entry, ensure_ascii=False, sort_keys=True),
                  'text' if isinstance(got, str) else 'json',
                  (got if isinstance(got, str) else json.dumps(got, ensure_ascii=False, sort_keys=True))
                  if got is not None else '',
                  json.dumps(errs, ensure_ascii=False)))
    print('# 合成 %-24s → %s' % (gid, 'ok' if got is not None else ('err ' + str(errs)[:70])))

entries = []
for pkg, gid, entry_s, kind, want_s, errs_s in reals + synth:
    entries.append(
        '        (%s, %s, %s, %s, %s, %s),'
        % (rr(pkg), rr(gid), rr(entry_s), rr(kind), rr(want_s), rr(errs_s)))

TEMPLATE = r'''
    // >>> GENERATED by tools/gen_output_forms_gen_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 13 个生成器：真语料 106 条 + 9 个未触发生成器的合成入口 =====
    ///
    /// 比对取**最严**口径：JSON 走 `dumps_default()` 字符串相等（含键序），纯文本走字符串相等。
    /// 真源返回 `None` 的（缺 inputs / 不可解析）断言本线也返回 `None` 且 issue 列表一致。
    #[test]
    fn generators_match_truth_source() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &str, &str, &str, &str, &str)] = &[
@@CASES@@
        ];
        let mut json_ok = 0usize;
        let mut text_ok = 0usize;
        let mut none_ok = 0usize;
        for (pkg, gid, entry_s, kind, want_s, errs_s) in cases {
            let entry: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(entry_s).unwrap(),
            )
            .unwrap();
            let (got, errs) = dispatch(&root, &entry);
            let want_errs: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(errs_s).unwrap(),
            )
            .unwrap();
            if want_s.is_empty() {
                match got {
                    None => none_ok += 1,
                    Some(g) => panic!(
                        "{} {}：真源返回 None，本线给了 {:?}",
                        pkg, gid, g
                    ),
                }
                let want_list: Vec<String> =
                    match want_errs { Json::Array(a) => a.iter().map(crate::pyval::plain_str).collect(), _ => Vec::new() };
                assert_eq!(errs, want_list, "{} {} 的 issue 列表", pkg, gid);
                continue;
            }
            match got {
                None => panic!("{} {}：真源有值、本线返回 None（issue {}）", pkg, gid, errs.join("；")),
                Some(g) => match (kind, g) {
                    (&"text", GenOut::Text(t)) => {
                        assert_eq!(&t, want_s, "{} {} 的文本", pkg, gid);
                        text_ok += 1;
                    }
                    (&"json", GenOut::Json(v)) => {
                        assert_eq!(&v.dumps_default(), want_s, "{} {} 的 JSON", pkg, gid);
                        json_ok += 1;
                    }
                    (k, other) => panic!("{} {}：期望 {} 实得 {:?}", pkg, gid, k, other),
                },
            }
        }
        eprintln!(
            "生成器对账：JSON {} / 文本 {} / 中性 None {}",
            json_ok, text_ok, none_ok
        );
        assert!(json_ok > 0 && text_ok > 0, "两类都要真跑到，否则判据是空转");
    }

    /// 登记表齐全：13 个 id 全部在册且 `dispatch` 都认得（不得靠 `other` 兜底）。
    #[test]
    fn generator_registry_is_complete() {
        assert_eq!(GENERATOR_IDS.len(), 13);
        for gid in GENERATOR_IDS {
            let entry = Json::Object(vec![(
                "recompute".to_string(),
                Json::Object(vec![("id".to_string(), Json::Str(gid.to_string()))]),
            )]);
            let (_out, errs) = dispatch(&crate::testutil::repo_root(), &entry);
            for e in &errs {
                assert!(!e.starts_with("未登记生成器"), "{} 未被 dispatch 认领", gid);
            }
        }
    }
    // <<< GENERATED
'''
text = TEMPLATE.replace('@@CASES@@', "\n".join(entries))
BEGIN = '    // >>> GENERATED by tools/gen_output_forms_gen_cases.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text.split(BEGIN, 1)[1]

path = ROOT / 'engine' / 'rust' / 'src' / 'output_forms_gen.rs'
t = path.read_text(encoding='utf-8')
if BEGIN in t:
    a = t.index(BEGIN)
    b = t.index(END, a) + len(END)
    t = t[:a] + block + t[b:]
else:
    t = t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n}\n'
    t = t.rstrip()[:-1].rstrip() + '\n' + block + '}\n'
path.write_text(t, encoding='utf-8', newline='')
print('# 已写入生成器判据（真语料 %d + 合成 %d）' % (len(reals), len(synth)))
