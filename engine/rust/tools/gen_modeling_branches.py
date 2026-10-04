"""为 `modeling.scan` 生成分支级判据（三件子判据 + 词表/规范/契约各分支）。

用法：python engine/rust/target/parity/gen_modeling_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import modeling as md  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'modeling-branches'
if FIX.exists():
    shutil.rmtree(FIX)
for d in ('protocol', 'protocol/schema', 'docs', 'docs/ex', 'library'):
    (FIX / d).mkdir(parents=True)

W = lambda rel, obj: (FIX / rel).write_text(  # noqa: E731
    obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False),
    encoding='utf-8', newline='')

# ---- 词表：schema 错 / status 词表错 / 每个 scheme 踩一支 -------------------------
W('protocol/vocabularies.json', {
    "schema": "wrong/1",
    "status_vocabulary": ["active"],
    "probe_kinds": ["literal", "json_path", "python_attr"],
    "schemes": [
        # 正常（literal 不计入漂移）
        {"id": "v-literal", "status": "active", "values": ["a", "b"], "probe": {"kind": "literal"}},
        # id 重复 + 值不足两个
        {"id": "v-literal", "status": "active", "values": ["a"], "probe": {"kind": "literal"}},
        # status 越词表
        {"id": "v-status", "status": "bogus", "values": ["a", "b"], "probe": {"kind": "literal"}},
        # 值重复 + alias 撞车
        {"id": "v-dup", "status": "active", "values": ["a", "a"], "aliases": ["a"],
         "probe": {"kind": "literal"}},
        # probe.kind 不在册
        {"id": "v-kind", "status": "active", "values": ["a", "b"], "probe": {"kind": "nope"}},
        # json_path 断链
        {"id": "v-broken", "status": "active", "values": ["a", "b"],
         "probe": {"kind": "json_path", "file": "protocol/other.json", "path": "nope.deep"}},
        # json_path 与真源漂移
        {"id": "v-drift", "status": "active", "values": ["x", "y"],
         "probe": {"kind": "json_path", "file": "protocol/other.json", "path": "words"}},
        # python_attr 已登记（doc-kinds）
        {"id": "v-attr", "status": "deprecated", "values": ["tutorial", "how-to", "reference", "explanation"],
         "probe": {"kind": "python_attr", "module": "core.doc_hygiene", "attr": "KINDS"}},
        # ⚠️ **刻意不放「未登记的 python_attr」这一支**：真源 `importlib.import_module("core.nope")`
        # 会直接抛 ModuleNotFoundError（整条判据记 ERROR），本线则返回一条显式 issue（记 FAIL）。
        # 两边**都是红的**，但语义不同（ERROR vs FAIL）——这条差异无法逐字比对，故单列说明，
        # 不塞进逐条对账的夹具里（详见 README 的「已知偏差」）。
    ],
})
W('protocol/other.json', {"words": ["x", "z"]})

# ---- 规范/说明件 ---------------------------------------------------------------
W('docs/norm-a.md', "# a\n")
W('docs/ex/one.md', "# one\n")
W('docs/ex/two.md', "# two\n")
W('protocol/normative.json', {
    "schema": "wrong/1",
    "normative": [
        {"path": ""},                                                   # 缺 path
        "docs/missing.md",                                              # 不存在
        {"path": "docs/norm-a.md"},                                     # 无回执且无 covered_by
        {"path": "docs/norm-a.md", "covered_by": ["check99"]},          # 指向不存在的 check
        {"path": "docs/norm-b.md", "covered_by": ["check1"]},           # 合法
        {"path": "docs/ex/one.md"},                                     # 与 informative 重叠
    ],
    "informative": ["docs/ex/**", "docs/none/**"],
})
W('docs/norm-b.md', "# b\n")
W('verify.sh', "#!/bin/bash\ncheck1(){\n  true\n}\ncheck2(){\n  true\n}\n")
W('protocol/RECEIPTS.json', {"schema": "nf-receipts/1", "entries": [{"id": "docs/norm-b.md"}]})

# ---- 数据契约 -----------------------------------------------------------------
W('protocol/data_contracts.json', {
    "schema": "wrong/1",
    "status_vocabulary": ["active"],
    "rule_prefixes": ["check"],
    "contracts": [
        {"id": "c1", "artifact": "docs/norm-a.md", "status": "active", "owner": "o",
         "freshness": "f", "quality_rule": "check1"},                    # 指向不存在的 check
        {"id": "c1", "artifact": "no/such", "status": "bogus", "owner": "",
         "freshness": "", "quality_rule": "assertion:nope"},             # id 重复 + 各分支
        {"id": "c3", "artifact": "docs/norm-a.md", "status": "active", "owner": "o",
         "freshness": "f", "quality_rule": "不能解析"},                   # 无法解析
        {"id": "c4", "artifact": "docs/norm-b.md", "status": "active", "owner": "o",
         "freshness": "f", "quality_rule": "assertion:a1"},              # 合法（断言在册）
    ],
})
W('protocol/assertions.json', {"assertions": [{"id": "a1"}]})

issues, warns, stats = md.scan(str(FIX))

# 真源 stats 是 {vocabularies:{…}, normative:{…}, data_contracts:{…}}；
# 契约行只取其中四项计数，故这里同时打印两者。
v, n, d = stats.get('vocabularies', {}), stats.get('normative', {}), stats.get('data_contracts', {})

print('# 真源：issues=%d' % len(issues))
for x in issues:
    print('#   ! %s' % x)
print('# schemes=%s normative=%s informative=%s contracts=%s'
      % (v.get('schemes'), n.get('normative'), n.get('informative_files'), d.get('contracts')))


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


FILES = {}
for rel in ('protocol/vocabularies.json', 'protocol/other.json', 'protocol/normative.json',
            'protocol/data_contracts.json', 'protocol/assertions.json', 'protocol/RECEIPTS.json',
            'docs/norm-a.md', 'docs/norm-b.md', 'docs/ex/one.md', 'docs/ex/two.md', 'verify.sh'):
    FILES[rel] = (FIX / rel).read_text(encoding='utf-8')

TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `target/parity/gen_modeling_branches.py` 从真源生成）=====
    ///
    /// 真语料上 `modeling` 三件全绿 ⇒ 只靠契约对账核不到错误分支。本夹具逐分支踩：
    /// 词表（schema / status 词表 / id 重复 / 值不足 / 值重复 / alias 撞车 / probe.kind 不在册 /
    /// json_path 断链 / 真源漂移 / python_attr 已登记与未登记）、规范件（缺 path / 不存在 /
    /// 无锚定 / covered_by 指向不存在 check / 合法 / 与说明件重叠 / 说明面未命中）、
    /// 数据契约（schema / rule_prefixes / id 重复 / artifact 缺 / status 越词表 / 缺 owner /
    /// 缺 freshness / 规则指向不存在 check / 指向不存在断言 / 无法解析 / 合法）。
    const WANT_MD_ISSUES: [&str; @@NI@@] = [
@@ISSUES@@
    ];

    fn build_modeling_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("modeling-branches");
        for rel in ["protocol", "protocol/schema", "docs", "docs/ex", "library"] {
            std::fs::create_dir_all(root.join(rel)).unwrap();
        }
        for (rel, body) in @@FILES@@ {
            std::fs::write(root.join(rel), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_modeling_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_MD_ISSUES, "逐条消息与次序都须与真源一致");
        assert_eq!(got.schemes, @@NS@@);
        assert_eq!(got.normative, @@NN@@);
        assert_eq!(got.informative_files, @@NF@@);
        assert_eq!(got.contracts, @@NC@@);
    }
'''

files_rust = "[\n" + "\n".join(
    '            (%s, %s),' % (rs(k), rj(v)) for k, v in sorted(FILES.items())
) + "\n        ]"

text = (TEMPLATE
        .replace('@@NI@@', str(len(issues)))
        .replace('@@ISSUES@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False) for x in issues))
        .replace('@@FILES@@', files_rust)
        .replace('@@NS@@', str(v.get('schemes', 0)))
        .replace('@@NN@@', str(n.get('normative', 0)))
        .replace('@@NF@@', str(n.get('informative_files', 0)))
        .replace('@@NC@@', str(d.get('contracts', 0))))

path = ROOT / 'engine' / 'rust' / 'src' / 'modeling.rs'
t = path.read_text(encoding='utf-8')
if 'modeling-branches' in t:
    print('# 已有分支级判据，未追加')
else:
    idx = t.rstrip().rfind('\n}')
    path.write_text(t[:idx] + text + t[idx:], encoding='utf-8', newline='')
    print('# 已追加分支级判据')
