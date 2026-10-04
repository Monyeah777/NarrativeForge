"""为 `rating_gate.scan` 生成分支级判据（两个场景：声明齐 / 声明缺）。

用法：python engine/rust/target/parity/gen_rating_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import rating_gate as rg  # noqa: E402

BASE = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures'
if BASE.joinpath('rating-branches').exists():
    shutil.rmtree(BASE / 'rating-branches')

ENTRIES = {
    # 缺 rating → FAIL
    'NF-1.md': "---\nid: NF-1\ntype: t\ntitle: A\n---\n正文\n",
    # rating 越词表 → FAIL
    'NF-2.md': "---\nid: NF-2\ntype: t\ntitle: B\nrating: bogus\n---\n正文\n",
    # rating 合法 → 计数
    'NF-3.md': "---\nid: NF-3\ntype: t\ntitle: C\nrating: teen\n---\n正文\n",
}

DECL_OK = {"rating": {"vocabulary": ["general", "teen", "unrated"]}}
DECL_NO_VOCAB = {"rating": {}}

SCENARIOS = {}
for name, decl in (('withvocab', DECL_OK), ('novocab', DECL_NO_VOCAB), ('nodecl', None)):
    fix = BASE / 'rating-branches' / name
    (fix / 'library').mkdir(parents=True)
    if decl is not None:
        (fix / 'library' / 'intake.json').write_text(
            json.dumps(decl, ensure_ascii=False), encoding='utf-8', newline='')
    for fn, body in ENTRIES.items():
        (fix / 'library' / fn).write_text(body, encoding='utf-8', newline='')
    issues, stats = rg.scan(str(fix))
    SCENARIOS[name] = (issues, stats)
    print('# 场景 %s：issues=%d' % (name, len(issues)))
    for x in issues:
        print('#   ! %s' % x)
    print('# stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


def arr(v):
    return "&[%s]" % ", ".join(json.dumps(x, ensure_ascii=False) for x in v)


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `target/parity/gen_rating_branches.py` 从真源生成）=====
    ///
    /// 三个场景：声明齐（rating.vocabulary 成文）/ 声明在但缺 rating.vocabulary / 声明件缺失。
    /// 每场景都踩：缺 `rating` 字段 / rating 越词表 / rating 合法（计数）。
    const RATING_ENTRIES: [(&str, &str); 3] = [
        ("NF-1.md", "---\nid: NF-1\ntype: t\ntitle: A\n---\n正文\n"),
        ("NF-2.md", "---\nid: NF-2\ntype: t\ntitle: B\nrating: bogus\n---\n正文\n"),
        ("NF-3.md", "---\nid: NF-3\ntype: t\ntitle: C\nrating: teen\n---\n正文\n"),
    ];

    fn build_rating_fixture(scenario: &str, decl: Option<&str>) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("rating-branches-{}", scenario));
        std::fs::create_dir_all(root.join("library")).unwrap();
        if let Some(d) = decl {
            std::fs::write(root.join("library/intake.json"), d).unwrap();
        }
        for (name, body) in RATING_ENTRIES {
            std::fs::write(root.join("library").join(name), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_in_all_three_declaration_states() {
        for (scenario, decl, want_issues, want_vocab, want_counts) in [
            (
                "withvocab",
                Some(r#"{"rating": {"vocabulary": ["general", "teen", "unrated"]}}"#),
                @@W1@@ as &[&str],
                @@V1@@ as &[&str],
                @@C1@@ as &[(&str, i64)],
            ),
            (
                "novocab",
                Some(r#"{"rating": {}}"#),
                @@W2@@ as &[&str],
                @@V2@@ as &[&str],
                @@C2@@ as &[(&str, i64)],
            ),
            ("nodecl", None, @@W3@@ as &[&str], @@V3@@ as &[&str], @@C3@@ as &[(&str, i64)]),
        ] {
            let root = build_rating_fixture(scenario, decl);
            let got = scan(&root);
            assert_eq!(got.issues, want_issues, "场景 {} 的 issues", scenario);
            let want = crate::pyjson::Json::Object(vec![
                (
                    "entries".to_string(),
                    crate::pyjson::Json::Int(3),
                ),
                (
                    "vocabulary".to_string(),
                    crate::pyjson::Json::Array(
                        want_vocab.iter().map(|s| crate::pyjson::Json::Str((*s).to_string())).collect(),
                    ),
                ),
                (
                    "counts".to_string(),
                    crate::pyjson::Json::Object(
                        want_counts
                            .iter()
                            .map(|(k, v)| ((*k).to_string(), crate::pyjson::Json::Int(*v)))
                            .collect(),
                    ),
                ),
                (
                    "issues".to_string(),
                    crate::pyjson::Json::Int(want_issues.len() as i64),
                ),
            ]);
            assert!(
                crate::jsonread::json_eq(&got.stats, &want),
                "场景 {} 的 stats：实得 {:?}",
                scenario,
                got.stats
            );
        }
    }
'''


def counts_of(stats):
    return "&[%s]" % ", ".join('(%s, %di64)' % (rs(k), v) for k, v in sorted(stats['counts'].items()))


text = (TEMPLATE
        .replace('@@W1@@', arr(SCENARIOS['withvocab'][0]))
        .replace('@@W2@@', arr(SCENARIOS['novocab'][0]))
        .replace('@@W3@@', arr(SCENARIOS['nodecl'][0]))
        .replace('@@V1@@', arr(SCENARIOS['withvocab'][1]['vocabulary']))
        .replace('@@V2@@', arr(SCENARIOS['novocab'][1]['vocabulary']))
        .replace('@@V3@@', arr(SCENARIOS['nodecl'][1]['vocabulary']))
        .replace('@@C1@@', counts_of(SCENARIOS['withvocab'][1]))
        .replace('@@C2@@', counts_of(SCENARIOS['novocab'][1]))
        .replace('@@C3@@', counts_of(SCENARIOS['nodecl'][1])))

path = ROOT / 'engine' / 'rust' / 'src' / 'rating_gate.rs'
t = path.read_text(encoding='utf-8')
if 'rating-branches' in t:
    print('# 已有分支级判据，未追加')
else:
    idx = t.rstrip().rfind('\n}')
    path.write_text(t[:idx] + text + t[idx:], encoding='utf-8', newline='')
    print('# 已追加分支级判据')
