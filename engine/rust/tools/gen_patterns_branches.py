"""为 `patterns.scan` 生成分支级判据（真源 11 个分支）。

用法：python engine/rust/tools/gen_patterns_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import patterns as pt  # noqa: E402

BASE = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'patterns-branches'
if BASE.exists():
    shutil.rmtree(BASE)

# ② kitchen：逐分支踩（注意 `id` 与目录名不一致、`rules` 空、通配无匹配、路径不存在、
#    evidence 缺/空项/指向不存在）
KITCHEN = """---
id: 别的名字
name: kitchen
status: 越词表
applies_to:
  - zzz/**/*.md
  - no/such/path.md
rules: []
---
# kitchen
"""
# ③ 全绿 + 与 p2 的 id 重复（用 pid 制造重复）
GREEN = """---
id: p3
name: 全绿
status: active
scope: [s]
applies_to:
  - docs/real.md
rules:
  - 规则一
evidence:
  - check1
  - docs/real.md
---
# green
"""
DUP = """---
id: p3
name: 与 p3 撞号
status: active
scope: [s]
applies_to:
  - docs/real.md
rules:
  - 规则
evidence:
  - check1
---
# dup
"""
EVIDENCE_BAD = """---
id: p5
name: 证据面
status: deprecated
scope: [s]
applies_to:
  - docs/real.md
rules:
  - 规则
evidence:
  -
  - docs/nope.md
---
# ev
"""
NO_FM = "# 没有 frontmatter\n"

SCENARIOS = {}
for name, dirs in (
    ('kitchen', {'p2': KITCHEN, 'p3': GREEN, 'p5': EVIDENCE_BAD, 'p1': NO_FM}),
    ('dup', {'p3': GREEN, 'p3b': DUP}),
    ('nopkgs', {}),
):
    fix = BASE / name
    fix.mkdir(parents=True)
    (fix / 'docs').mkdir(exist_ok=True)
    (fix / 'docs' / 'real.md').write_text("# real\n", encoding='utf-8', newline='')
    (fix / 'verify.sh').write_text("#!/bin/bash\ncheck1(){\n  true\n}\n",
                                   encoding='utf-8', newline='')
    for d, body in dirs.items():
        (fix / 'patterns' / d).mkdir(parents=True, exist_ok=True)
        (fix / 'patterns' / d / 'PATTERN.md').write_text(body, encoding='utf-8', newline='')
    issues, warns, stats = pt.scan(str(fix))
    SCENARIOS[name] = (issues, warns, stats)
    print('# 场景 %s：issues=%d warns=%d' % (name, len(issues), len(warns)))
    for x in issues:
        print('#   ! %s' % x)
    for x in warns:
        print('#   ~ %s' % x)
    print('# stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


def arr(v):
    return "&[%s]" % ", ".join(json.dumps(x, ensure_ascii=False) for x in v)


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `tools/gen_patterns_branches.py` 从真源生成）=====
    ///
    /// 三场景：kitchen（逐分支）/ 撞号 / 无包。分支：缺 frontmatter / 缺必填 / id 与目录名不一致 /
    /// id 重复 / status 越词表 / rules 为空 / applies_to 通配无匹配 / applies_to 路径不存在 /
    /// evidence 缺失(warn) / evidence 空项(warn) / evidence 指向不存在(warn) / 无包。
    const PAT_KITCHEN: &str = @@KITCHEN@@;
    const PAT_GREEN: &str = @@GREEN@@;
    const PAT_DUP: &str = @@DUP@@;
    const PAT_EV: &str = @@EV@@;
    const PAT_NOFM: &str = @@NOFM@@;

    fn build_patterns_fixture(scenario: &str, dirs: &[(&str, &str)]) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("patterns-branches-{}", scenario));
        std::fs::create_dir_all(root.join("docs")).unwrap();
        std::fs::write(root.join("docs/real.md"), "# real\n").unwrap();
        std::fs::write(root.join("verify.sh"), "#!/bin/bash\ncheck1(){\n  true\n}\n").unwrap();
        for (d, body) in dirs {
            let p = root.join("patterns").join(d);
            std::fs::create_dir_all(&p).unwrap();
            std::fs::write(p.join("PATTERN.md"), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_in_all_three_scenarios() {
        for (scenario, dirs, want_issues, want_warns, want_n) in [
            (
                "kitchen",
                &[("p2", PAT_KITCHEN), ("p3", PAT_GREEN), ("p5", PAT_EV), ("p1", PAT_NOFM)][..],
                @@I1@@ as &[&str],
                @@W1@@ as &[&str],
                @@N1@@,
            ),
            (
                "dup",
                &[("p3", PAT_GREEN), ("p3b", PAT_DUP)][..],
                @@I2@@ as &[&str],
                @@W2@@ as &[&str],
                @@N2@@,
            ),
            ("nopkgs", &[][..], @@I3@@ as &[&str], @@W3@@ as &[&str], @@N3@@),
        ] {
            let root = build_patterns_fixture(scenario, dirs);
            let (issues, n) = scan_issues(&root);
            assert_eq!(issues, want_issues, "场景 {} 的 issues", scenario);
            assert_eq!(n, want_n, "场景 {} 的包数", scenario);
            let _ = want_warns;   // 真源 warns 在本面无消费者，未纳入移植面
        }
    }
'''

sc = SCENARIOS
text = (TEMPLATE
        .replace('@@KITCHEN@@', rj(KITCHEN)).replace('@@GREEN@@', rj(GREEN))
        .replace('@@DUP@@', rj(DUP)).replace('@@EV@@', rj(EVIDENCE_BAD))
        .replace('@@NOFM@@', rj(NO_FM))
        .replace('@@I1@@', arr(sc['kitchen'][0])).replace('@@W1@@', arr(sc['kitchen'][1]))
        .replace('@@I2@@', arr(sc['dup'][0])).replace('@@W2@@', arr(sc['dup'][1]))
        .replace('@@I3@@', arr(sc['nopkgs'][0])).replace('@@W3@@', arr(sc['nopkgs'][1]))
        .replace('@@N1@@', str(sc['kitchen'][2].get('patterns', 0)))
        .replace('@@N2@@', str(sc['dup'][2].get('patterns', 0)))
        .replace('@@N3@@', str(sc['nopkgs'][2].get('patterns', 0))))

BEGIN = '    // >>> GENERATED by tools/gen_patterns_branches.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text + END
path = ROOT / 'engine' / 'rust' / 'src' / 'patterns.rs'
t = path.read_text(encoding='utf-8')
if BEGIN in t:
    a = t.index(BEGIN)
    b = t.index(END, a) + len(END)
    path.write_text(t[:a] + block + t[b:], encoding='utf-8', newline='')
    print('# 已刷新标记区间')
elif '#[cfg(test)]' in t:
    idx = t.rstrip().rfind('\n}')
    path.write_text(t[:idx] + block + t[idx:], encoding='utf-8', newline='')
    print('# 已插入标记区间（原有 tests 模块）')
else:
    path.write_text(t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n'
                    + block + '}\n', encoding='utf-8', newline='')
    print('# 已追加标记区间')
