"""为 `handover.scan` / `check_doc` 生成分支级判据（三个场景：声明坏 / 缺声明 / 无交接件）。

用法：python engine/rust/tools/gen_handover_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import handover as ho  # noqa: E402

BASE = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'handover-branches'
if BASE.exists():
    shutil.rmtree(BASE)

DECL_BAD = {
    "schema": "wrong/1",                                   # schema 不匹配
    "sections": ["情境", "背景"],                            # 非五段
    "rules": [],                                           # rules 为空
    "required_fields": ["id", "date", "from", "to", "status", "refs", "extra"],
    "status_vocabulary": ["open", "closed"],
}
DECL_OK = {
    "schema": "nf-handover/1",
    "sections": ["情境", "背景", "评估", "建议", "未决项"],
    "rules": ["r"],
    "required_fields": ["id", "date", "from", "to", "status", "refs"],
    "status_vocabulary": ["open", "closed"],
}

KITCHEN = (
    "---\n"
    "id: HO-2\n"
    "from: a\n"
    "to: b\n"
    "status: 越词表\n"
    "date: 2026/01/01\n"
    "refs: check99\n"                     # 字符串形态（非列表）+ 不存在的 check
    "---\n"
    "## 情境\ns\n"                         # 只给一段，其余缺
    "## 未决项\n"
    "- 没有判据的一条\n"                    # 未决项缺判据
    "- 有判据的一条（判据：能跑通）\n"
)
GREEN = (
    "---\n"
    "id: HO-3\n"
    "from: a\n"
    "to: b\n"
    "status: open\n"
    "date: 2026-01-02\n"
    "refs:\n"
    "  - check1\n"                         # 在册 check
    "  - ADR-0001\n"                       # ADR 豁免
    "  - no/such/file\n"                   # 无法解析
    "---\n"
    + "".join("## %s\nx\n" % s for s in ("情境", "背景", "评估", "建议"))
    + "## 未决项\n- 做完某事的判据：跑通 verify.sh\n"
)

SCENARIOS = {}
for name, decl, docs in (
    ('baddecl', DECL_BAD, {'HO-2-kitchen.md': KITCHEN, 'HO-3-green.md': GREEN}),
    ('nodecl', None, {'HO-4.md': GREEN}),
    ('nodocs', DECL_OK, {}),
):
    fix = BASE / name
    (fix / 'protocol').mkdir(parents=True)
    if decl is not None:
        (fix / 'protocol' / 'handover.json').write_text(
            json.dumps(decl, ensure_ascii=False), encoding='utf-8', newline='')
    for fn, body in docs.items():
        (fix / 'handovers').mkdir(parents=True, exist_ok=True)
        (fix / 'handovers' / fn).write_text(body, encoding='utf-8', newline='')
    (fix / 'verify.sh').write_text("#!/bin/bash\ncheck1(){\n  true\n}\n",
                                   encoding='utf-8', newline='')
    issues, warns, stats = ho.scan(str(fix))
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
    /// ===== 分支级差分判据（期望值由 `tools/gen_handover_branches.py` 从真源生成）=====
    ///
    /// 三个场景：声明坏（schema / 非五段 / rules 空）/ 缺声明 / 无交接件（门禁空转 warn）。
    /// 交接件逐分支踩：缺必填 / status 越词表 / 日期非法 / 正文缺段落 /
    /// **未决项为空**（空未决 = 不合格交接）/ 未决项缺判据 / `refs` 为字符串形态 /
    /// **移植面**：真源 `scan` 还返回 warns（「门禁空转」提示），但该面无消费者（契约只看 issues），
    /// 故本线结构体未纳入；期望值里的 `want_warns` 仅作记录，不参与断言。
    const HO_KITCHEN: &str = @@KITCHEN@@;
    const HO_GREEN: &str = @@GREEN@@;

    fn build_handover_fixture(scenario: &str, decl: Option<&str>,
                              docs: &[(&str, &str)]) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("handover-branches-{}", scenario));
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        if let Some(d) = decl {
            std::fs::write(root.join("protocol/handover.json"), d).unwrap();
        }
        if !docs.is_empty() {
            std::fs::create_dir_all(root.join("handovers")).unwrap();
            for (name, body) in docs {
                std::fs::write(root.join("handovers").join(name), body).unwrap();
            }
        }
        std::fs::write(root.join("verify.sh"), "#!/bin/bash\ncheck1(){\n  true\n}\n").unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_in_all_three_scenarios() {
        for (scenario, decl, docs, want_issues, want_warns, want_handovers, want_pending) in [
            (
                "baddecl",
                Some(@@DECL_BAD@@),
                &[("HO-2-kitchen.md", HO_KITCHEN), ("HO-3-green.md", HO_GREEN)][..],
                @@I1@@ as &[&str],
                @@W1@@ as &[&str],
                @@H1@@, @@P1@@,
            ),
            (
                "nodecl",
                None,
                &[("HO-4.md", HO_GREEN)][..],
                @@I2@@ as &[&str],
                @@W2@@ as &[&str],
                @@H2@@, @@P2@@,
            ),
            ("nodocs", Some(@@DECL_OK@@), &[][..],
             @@I3@@ as &[&str], @@W3@@ as &[&str], @@H3@@, @@P3@@),
        ] {
            let root = build_handover_fixture(scenario, decl, docs);
            let got = scan(&root);
            assert_eq!(got.issues, want_issues, "场景 {} 的 issues", scenario);
            // 真源 `handover.scan` 还返回 warns（门禁空转提示），但本面无消费者，故未纳入移植面；
            // `want_warns` 仅作记录（前缀下划线以免 unused）。
            let _want_warns = want_warns;
            let _ = _want_warns;
            assert_eq!(got.handovers, want_handovers, "场景 {} 的件数", scenario);
            assert_eq!(got.pending, want_pending, "场景 {} 的未决项数", scenario);
        }
    }
'''

sc = SCENARIOS
text = (TEMPLATE
        .replace('@@KITCHEN@@', rj(KITCHEN))
        .replace('@@GREEN@@', rj(GREEN))
        .replace('@@DECL_BAD@@', rj(json.dumps(DECL_BAD, ensure_ascii=False)))
        .replace('@@DECL_OK@@', rj(json.dumps(DECL_OK, ensure_ascii=False)))
        .replace('@@I1@@', arr(sc['baddecl'][0])).replace('@@W1@@', arr(sc['baddecl'][1]))
        .replace('@@I2@@', arr(sc['nodecl'][0])).replace('@@W2@@', arr(sc['nodecl'][1]))
        .replace('@@I3@@', arr(sc['nodocs'][0])).replace('@@W3@@', arr(sc['nodocs'][1]))
        .replace('@@H1@@', str(sc['baddecl'][2].get('handovers', 0)))
        .replace('@@P1@@', str(sc['baddecl'][2].get('pending', 0)))
        .replace('@@H2@@', str(sc['nodecl'][2].get('handovers', 0)))
        .replace('@@P2@@', str(sc['nodecl'][2].get('pending', 0)))
        .replace('@@H3@@', str(sc['nodocs'][2].get('handovers', 0)))
        .replace('@@P3@@', str(sc['nodocs'][2].get('pending', 0))))

BEGIN = '    // >>> GENERATED by tools/gen_handover_branches.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text + END
path = ROOT / 'engine' / 'rust' / 'src' / 'handover.rs'
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
