"""为 `postmortem.scan` 生成分支级判据（真源 16 个 issue 分支 + 空件 warn）。

用法：python engine/rust/tools/gen_postmortem_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import postmortem as pm  # noqa: E402

BASE = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'postmortem-branches'
if BASE.exists():
    shutil.rmtree(BASE)

# 真源的「根因段须指向机制」判据要求出现 ROOT_TOKENS 之一；这里用真源自身的词表拼一条合法行。
ROOT_TOK = '机制'   # 真源词表键为 `root_cause_tokens`，由声明件给出
BLAME = '疏忽'       # 同上，键为 `blame_tokens`

GREEN = (
    "---\n"
    "id: PO-1\ntitle: t\nstatus: open\ndate: 2026-01-01\n"
    "refs: check1\n"
    "---\n"
    "## 现象\np\n## 影响\ni\n"
    "## 根因\n根因是流程%s\n" % ROOT_TOK +
    "## 行动项\n- 改流程（负责人：张三）判据：跑通 verify.sh\n"
)
KITCHEN = (
    "---\n"
    "id: PO-2\n"
    "status: 越词表\n"
    "date: 2026/01/01\n"
    "refs:\n"
    "  - check99\n"
    "  - no/such/file\n"
    "---\n"
    "## 现象\np\n"                      # 其余三段缺
    "## 根因\n因为%s操作不当\n" % BLAME +
    "## 行动项\n"
    "- 没有负责人也没有判据的行动项\n"
)
CLOSED = (
    "---\n"
    "id: PO-3\ntitle: t\nstatus: closed\ndate: 2026-01-02\n"
    "refs: check1\n"
    "---\n"
    "## 现象\np\n## 影响\ni\n## 根因\n机制%s\n" % ROOT_TOK +
    "## 行动项\n- 做某事（负责人：李四）判据：跑通\n"
)

SCENARIOS = {}
for name, decl, docs in (
    ('kitchen', {"schema": "wrong/1", "sections": ["现象"], "blame_tokens": [],
                 "root_cause_tokens": []},
     {'PO-2-kitchen.md': KITCHEN, 'PO-3-closed.md': CLOSED}),
    ('gooddecl', {"schema": "nf-postmortem/1",
                  "sections": ["现象", "影响", "根因", "行动项"],
                  "blame_tokens": ["疏忽"], "root_cause_tokens": ["机制"]},
     {'PO-1-green.md': GREEN, 'PO-3-closed.md': CLOSED}),
    ('nodecl', None, {'PO-1-green.md': GREEN}),
    ('nodocs', {"schema": "nf-postmortem/1", "sections": ["现象", "影响", "根因", "行动项"],
                "blame_tokens": ["疏忽"], "root_cause_tokens": ["机制"]}, {}),
):
    fix = BASE / name
    (fix / 'protocol').mkdir(parents=True)
    if decl is not None:
        (fix / 'protocol' / 'postmortem.json').write_text(
            json.dumps(decl, ensure_ascii=False), encoding='utf-8', newline='')
    if docs:
        (fix / 'postmortems').mkdir(parents=True, exist_ok=True)
        for fn, body in docs.items():
            (fix / 'postmortems' / fn).write_text(body, encoding='utf-8', newline='')
    (fix / 'verify.sh').write_text("#!/bin/bash\ncheck1(){\n  true\n}\n",
                                   encoding='utf-8', newline='')
    # PO-3 已 closed：把它锚进回执，才能分别踩到「已锚定」与「未锚定」两侧
    (fix / 'protocol' / 'RECEIPTS.json').write_text(
        json.dumps({"schema": "nf-receipts/1",
                    "entries": [{"id": "postmortems/PO-3-closed.md"}]},
                   ensure_ascii=False), encoding='utf-8', newline='')
    issues, warns, stats = pm.scan(str(fix))
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
    /// ===== 分支级差分判据（期望值由 `tools/gen_postmortem_branches.py` 从真源生成）=====
    ///
    /// 四场景：kitchen / 声明齐 / 缺声明 / 无复盘件（门禁空转 warn）。
    /// 分支：引用指向不存在 check / 引用无法解析 / 缺必填 / status 越词表 / 日期非法 / 正文缺段落 /
    /// **命中指责性归因词** / 根因段未指向机制 / 行动项为空 / 行动项缺负责人 / 行动项缺判据 /
    /// `status=closed` 但未被回执锚定 / 声明 schema / sections 非四段 / 词表不得为空 / 全绿。
    /// 注：真源 `scan` 的 warns 在本面无消费者，故本线未纳入移植面。
    const PM_GREEN: &str = @@GREEN@@;
    const PM_KITCHEN: &str = @@KITCHEN@@;
    const PM_CLOSED: &str = @@CLOSED@@;
    const PM_DECL_OK: &str = @@DECL_OK@@;

    fn build_pm_fixture(scenario: &str, decl: Option<&str>,
                        docs: &[(&str, &str)]) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("postmortem-branches-{}", scenario));
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        if let Some(d) = decl {
            std::fs::write(root.join("protocol/postmortem.json"), d).unwrap();
        }
        if !docs.is_empty() {
            std::fs::create_dir_all(root.join("postmortems")).unwrap();
            for (name, body) in docs {
                std::fs::write(root.join("postmortems").join(name), body).unwrap();
            }
        }
        std::fs::write(root.join("verify.sh"), "#!/bin/bash\ncheck1(){\n  true\n}\n").unwrap();
        std::fs::write(
            root.join("protocol/RECEIPTS.json"),
            r#"{"schema": "nf-receipts/1", "entries": [{"id": "postmortems/PO-3-closed.md"}]}"#,
        )
        .unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_in_all_four_scenarios() {
        for (scenario, decl, docs, want) in [
            (
                "kitchen",
                Some(@@D1@@),
                &[("PO-2-kitchen.md", PM_KITCHEN), ("PO-3-closed.md", PM_CLOSED)][..],
                @@I1@@ as &[&str],
            ),
            (
                "gooddecl",
                Some(PM_DECL_OK),
                &[("PO-1-green.md", PM_GREEN), ("PO-3-closed.md", PM_CLOSED)][..],
                @@I2@@ as &[&str],
            ),
            ("nodecl", None, &[("PO-1-green.md", PM_GREEN)][..], @@I3@@ as &[&str]),
            ("nodocs", Some(PM_DECL_OK), &[][..], @@I4@@ as &[&str]),
        ] {
            let root = build_pm_fixture(scenario, decl, docs);
            let got = scan(&root);
            assert_eq!(got.issues, want, "场景 {} 的 issues", scenario);
        }
    }
'''

sc = SCENARIOS
text = (TEMPLATE
        .replace('@@GREEN@@', rj(GREEN)).replace('@@KITCHEN@@', rj(KITCHEN))
        .replace('@@CLOSED@@', rj(CLOSED))
        .replace('@@DECL_OK@@', rj(json.dumps(
            {"schema": "nf-postmortem/1", "sections": ["现象", "影响", "根因", "行动项"],
             "blame_tokens": ["疏忽"], "root_cause_tokens": ["机制"]},
            ensure_ascii=False)))
        .replace('@@D1@@', rj(json.dumps({"schema": "wrong/1", "sections": ["现象"],
                                          "blame_tokens": [], "root_cause_tokens": []},
                                         ensure_ascii=False)))
        .replace('@@I1@@', arr(sc['kitchen'][0]))
        .replace('@@I2@@', arr(sc['gooddecl'][0]))
        .replace('@@I3@@', arr(sc['nodecl'][0]))
        .replace('@@I4@@', arr(sc['nodocs'][0])))

BEGIN = '    // >>> GENERATED by tools/gen_postmortem_branches.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text + END
path = ROOT / 'engine' / 'rust' / 'src' / 'postmortem.rs'
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
