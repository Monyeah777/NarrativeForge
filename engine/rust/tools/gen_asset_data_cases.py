"""为 `asset_contract` 生成**数据面**用例级判据（逐条真实声明）。

真语料上 `scan` 是 0 issue ⇒ 数据面的错误分支一个都踩不到。这里做两件事：

1. **逐条真实声明**跑 `_check_data`，期望值从真源取——覆盖 JSON(schema+required+link)、
   CSV(required_columns+min_rows)、markdown、sha256 四条真声明的**通过路径**；
2. **合成夹具**覆盖错误分支（缺件 / format 非法 / sha256 多件 / 必填缺 / CSV 空/空列名/列数不齐/
   缺列/行数不足 / markdown 缺 frontmatter/表列数不齐 / link 取不到/件不在场/行数不符）。

用法：python engine/rust/tools/gen_asset_data_cases.py
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
sys.path.insert(0, str(ROOT / 'engine' / 'rust' / 'tools'))
from _rustlit import raw as rr  # noqa: E402
from core import asset_contract as ac  # noqa: E402

# ---- ① 真实声明的四条（在真仓库根上跑）
doc = json.loads((ROOT / 'protocol' / 'asset_contracts.json').read_text(encoding='utf-8'))
real = []
for spec in doc.get('data') or []:
    issues, stats = ac._check_data(str(ROOT), spec)
    real.append((spec, issues, stats))
    print('# 真实 %-20s issues=%d stats=%s'
          % (spec.get('id'), len(issues), json.dumps(stats, ensure_ascii=False, sort_keys=True)))

# ---- ② 合成夹具（在夹具根上跑），覆盖错误分支
FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'asset-data-cases'
if FIX.exists():
    shutil.rmtree(FIX)
FIX.mkdir(parents=True)

(FIX / 'ok.json').write_text('{"a": 1, "n": 3}\n', encoding='utf-8', newline='')
(FIX / 'bad.json').write_text('{"a": "x"}\n', encoding='utf-8', newline='')
(FIX / 'nonan.json').write_text('{"a": NaN}\n', encoding='utf-8', newline='')
(FIX / 'sch.json').write_text('{"type": "object", "required": ["a"]}\n', encoding='utf-8',
                              newline='')
(FIX / 'badschema.json').write_text('{"type": }\n', encoding='utf-8', newline='')
(FIX / 'ok.csv').write_text('a,b\n1,2\n3,4\n', encoding='utf-8', newline='')
(FIX / 'empty.csv').write_text('', encoding='utf-8', newline='')
(FIX / 'blankhdr.csv').write_text('a,,c\n1,2,3\n', encoding='utf-8', newline='')
(FIX / 'ragged.csv').write_text('a,b\n1,2,3\n4,5\n', encoding='utf-8', newline='')
(FIX / 'quoted.csv').write_text('a,b\n"x,1",2\n', encoding='utf-8', newline='')
(FIX / 'ok.md').write_text('---\nx: 1\n---\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n',
                           encoding='utf-8', newline='')
(FIX / 'ragged.md').write_text('---\n\n| a | b |\n| --- | --- |\n| 1 |\n', encoding='utf-8',
                               newline='')
(FIX / 'nofm.md').write_text('| a |\n| --- |\n| 1 |\n', encoding='utf-8', newline='')
(FIX / 'link.csv').write_text('h\n1\n2\n3\n', encoding='utf-8', newline='')
(FIX / 'link.json').write_text('{"p": "link.csv", "n": 3}\n', encoding='utf-8', newline='')
(FIX / 'linkbad.json').write_text('{"p": "link.csv", "n": 9}\n', encoding='utf-8', newline='')
(FIX / 'linkmiss.json').write_text('{"p": "nope.csv", "n": 1}\n', encoding='utf-8', newline='')
(FIX / 'plain.txt').write_text('l1\nl2\n', encoding='utf-8', newline='')


def sc(**kw):
    return kw


SYNTH = [
    ("ok-json-schema", sc(id="s1", path="ok.json", format="json", schema="sch.json")),
    ("bad-json-schema", sc(id="s2", path="bad.json", format="json", schema="sch.json")),
    ("non-rfc8259", sc(id="s3", path="nonan.json", format="json")),
    ("bad-schema-json", sc(id="s4", path="ok.json", format="json", schema="badschema.json")),
    ("schema-missing", sc(id="s5", path="ok.json", format="json", schema="nope.json")),
    ("required-missing", sc(id="s6", path="bad.json", format="json", required_fields=["zz"])),
    ("format-invalid", sc(id="s7", path="ok.json", format="xml")),
    ("path-missing", sc(id="s8", path="nope.json", format="json")),
    ("glob-empty", sc(id="s9", glob="*.nope", format="json")),
    ("sha-multi", sc(id="s10", glob="*.csv", format="csv", sha256="00")),
    ("sha-mismatch", sc(id="s11", path="ok.csv", format="csv", sha256="00")),
    ("csv-ok", sc(id="s12", path="ok.csv", format="csv", required_columns=["a"])),
    ("csv-empty", sc(id="s13", path="empty.csv", format="csv")),
    ("csv-blank-header", sc(id="s14", path="blankhdr.csv", format="csv")),
    ("csv-ragged", sc(id="s15", path="ragged.csv", format="csv")),
    ("csv-missing-col", sc(id="s16", path="ok.csv", format="csv", required_columns=["zz"])),
    ("csv-min-rows", sc(id="s17", path="ok.csv", format="csv", min_rows=99)),
    ("csv-quoted", sc(id="s18", path="quoted.csv", format="csv", required_columns=["a", "b"])),
    ("md-ok", sc(id="s19", path="ok.md", format="markdown", frontmatter=True)),
    ("md-ragged", sc(id="s20", path="ragged.md", format="markdown", frontmatter=True)),
    ("md-no-frontmatter", sc(id="s21", path="nofm.md", format="markdown", frontmatter=True)),
    ("text-lines", sc(id="s22", path="plain.txt", format="text")),
    ("link-ok", sc(id="s23", path="link.json", format="json",
                   link={"path_field": "p", "rows_field": "n"})),
    ("link-mismatch", sc(id="s24", path="linkbad.json", format="json",
                         link={"path_field": "p", "rows_field": "n"})),
    ("link-missing", sc(id="s25", path="linkmiss.json", format="json",
                        link={"path_field": "p"})),
    ("link-no-path-field", sc(id="s26", path="link.json", format="json",
                              link={"path_field": "nope"})),
]

synth = []
for name, spec in SYNTH:
    issues, stats = ac._check_data(str(FIX), spec)
    synth.append((name, spec, issues, stats))
    print('# 合成 %-20s issues=%d %s' % (name, len(issues),
                                     ('| ' + issues[0][:70]) if issues else ''))


def arr(v):
    return "&[%s]" % ", ".join(rr(x) for x in v)


real_entries = []
for spec, issues, stats in real:
    real_entries.append('        (\n            %s,\n            %s,\n            %s\n        ),'
                        % (rr(json.dumps(spec, ensure_ascii=False, sort_keys=True)),
                           arr(issues),
                           rr(json.dumps(stats, ensure_ascii=False, sort_keys=True))))

synth_entries = []
for name, spec, issues, stats in synth:
    synth_entries.append('        (\n            %s,\n            %s,\n            %s,\n            %s\n        ),'
                         % (rr(name),
                            rr(json.dumps(spec, ensure_ascii=False, sort_keys=True)),
                            arr(issues),
                            rr(json.dumps(stats, ensure_ascii=False, sort_keys=True))))

TEMPLATE = r'''
    // >>> GENERATED by tools/gen_asset_data_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 数据面用例级判据（期望值由 `tools/gen_asset_data_cases.py` 从真源生成）=====
    ///
    /// ① **真实声明的四条**在**真仓库根**上跑：JSON(schema+required+link) / CSV(required_columns+
    /// min_rows) / markdown / sha256 的通过路径。
    /// ② **合成夹具**覆盖错误分支：缺件 / format 非法 / sha256 多件 / 必填缺 / CSV 空·空列名·
    /// 列数不齐·缺列·行数不足·带引号字段 / markdown 缺 frontmatter·表列数不齐 / link 三类。
    ///
    /// `strict_json` 与 `_read` 的**报错文本**两处已知偏差（serde_json / std::io vs CPython），
    /// 故断言前对这两类消息做**归一**——不假装文本相同。
    fn ac_repo_root() -> std::path::PathBuf {
        std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
    }

    /// 归一：解析/读件失败的文本两侧不可比，只留稳定前缀。
    fn ac_norm(issues: &[String]) -> Vec<String> {
        issues
            .iter()
            .map(|x| {
                for pat in ["不是合法 JSON：", "schema 本身不是合法 JSON：", "读不到 ",
                            " 不是 UTF-8："] {
                    if let Some(i) = x.find(pat) {
                        return format!("{}<TEXT>", &x[..i + pat.len()]);
                    }
                }
                x.clone()
            })
            .collect()
    }

    #[test]
    fn asset_data_real_declarations_match_truth_source() {
        let root = ac_repo_root();
        let cases: &[(&str, &[&str], &str)] = &[
@@REAL@@
        ];
        for (spec_s, want_issues, want_stats) in cases {
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(spec_s).unwrap(),
            )
            .unwrap();
            let (issues, stats) = check_data(&root, &spec);
            assert_eq!(ac_norm(&issues), ac_norm(&want_issues.iter().map(|s| s.to_string()).collect::<Vec<_>>()),
                       "真实声明 issues 不一致");
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_stats).unwrap(),
            )
            .unwrap();
            assert!(crate::jsonread::json_eq(&stats, &want),
                    "真实声明 stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
        }
    }

    #[test]
    fn asset_data_synthetic_branches_match_truth_source() {
        let root = crate::testutil::fixture("asset-data-cases-src");
        write_asset_data_fixture(&root);
        let cases: &[(&str, &str, &[&str], &str)] = &[
@@SYNTH@@
        ];
        for (name, spec_s, want_issues, want_stats) in cases {
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(spec_s).unwrap(),
            )
            .unwrap();
            let (issues, stats) = check_data(&root, &spec);
            assert_eq!(ac_norm(&issues),
                       ac_norm(&want_issues.iter().map(|s| s.to_string()).collect::<Vec<_>>()),
                       "合成用例 {} 的 issues 不一致", name);
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_stats).unwrap(),
            )
            .unwrap();
            assert!(crate::jsonread::json_eq(&stats, &want),
                    "合成用例 {} 的 stats 不一致\n  实得 {}\n  期望 {}", name,
                    stats.dumps(), want.dumps());
        }
    }
    // <<< GENERATED
'''

text = (TEMPLATE.replace('@@REAL@@', "\n".join(real_entries))
        .replace('@@SYNTH@@', "\n".join(synth_entries)))
BEGIN = '    // >>> GENERATED by tools/gen_asset_data_cases.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text.split(BEGIN, 1)[1]

# 合成夹具的内容表（Rust 侧重建同一份树）
FIXFILES = {}
for p in sorted(FIX.rglob('*')):
    if p.is_file():
        FIXFILES[p.relative_to(FIX).as_posix()] = p.read_text(encoding='utf-8')
fix_entries = "\n".join('        (%s, %s),' % (rr(k), rr(v)) for k, v in FIXFILES.items())
helper = '''
    /// 合成夹具的内容（与 `tools/gen_asset_data_cases.py` 里 Python 侧那份**逐字同源**）。
    const AC_FIX_FILES: [(&str, &str); %d] = [
%s
    ];

    fn write_asset_data_fixture(root: &std::path::Path) {
        for (rel, body) in AC_FIX_FILES {
            let p = root.join(rel);
            std::fs::create_dir_all(p.parent().unwrap()).unwrap();
            std::fs::write(p, body).unwrap();
        }
    }
''' % (len(FIXFILES), fix_entries)

path = ROOT / 'engine' / 'rust' / 'src' / 'asset_contract.rs'
t = path.read_text(encoding='utf-8')
if BEGIN in t:
    a = t.index(BEGIN)
    b = t.index(END, a) + len(END)
    t = t[:a] + block + t[b:]
else:
    t = t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n}\n'
    t = t.rstrip()[:-1].rstrip() + '\n' + block + '}\n'
# 助手放进 tests 模块内（紧跟 use super::*;）
t = t.replace('#[cfg(test)]\nmod tests {\n    use super::*;\n',
              '#[cfg(test)]\nmod tests {\n    use super::*;\n' + helper, 1)
path.write_text(t, encoding='utf-8', newline='')
print('# 已写入 asset_contract 的数据面判据（真实 %d 条 / 合成 %d 条）' % (len(real), len(synth)))
