import json, pathlib
from _rustlit import rs  # noqa: E402

WANT_ISSUES = [
    ".github/workflows/mixed.yml:10 未钉提交 SHA：actions/checkout@v4（修复指引：钉 40 位 SHA——`@v4` 这类可变引用可被上游改写；改法见 ossf/scorecard docs/checks.md §Pinned-Dependencies）",
    ".github/workflows/mixed.yml:11 uses 缺版本引用：actions/setup-python（修复指引：钉 owner/repo@<40 位提交 SHA>）",
    ".github/workflows/noperms.yml 缺显式 permissions 段（修复指引：按 ossf/scorecard §Token-Permissions 给 GITHUB_TOKEN 最小权限，如 `permissions:\n  contents: read`）",
    ".github/workflows/noperms.yml 未声明 job 级 `timeout-minutes`（修复指引：在该 job 的 `runs-on` 下一行加 `timeout-minutes: <分钟>`；挂死不许占满默认 6h）",
    ".github/workflows/writeall.yml 使用 write-all（修复指引：改为按需最小集，见 §Token-Permissions）",
    "requirements-a.txt:4 依赖未钉版本：requests（修复指引：改 `包==版本`——FAIR4RS R 面要求依赖可重建，见 DOI 10.5281/zenodo.6374314 / Scorecard §Pinned-Dependencies）",
]
WANT_WARNS = [
    ".github/workflows/mixed.yml 钉了 SHA 但没写版本注释（修复指引：行尾补 `# v4` 一类注释，便于依赖更新）",
]
SHA = 'a' * 40
SHA2 = 'b' * 40
WF_FILES = {
    'clean.yml': "name: clean\non: push\npermissions:\n  contents: read\njobs:\n  j:\n    runs-on: ubuntu-latest\n    timeout-minutes: 10\n    steps:\n      - uses: actions/checkout@%s # v4\n" % SHA,
    'mixed.yml': "name: mixed\non: push\npermissions:\n  contents: read\njobs:\n  j:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python\n      - uses: ./local-action\n      - uses: actions/cache@%s # v3\n      - uses: actions/upload-artifact@%s\n" % (SHA, SHA2),
    'noperms.yml': "name: noperms\non: push\njobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hi\n",
    'notes.txt': "uses: actions/checkout@v4\n",
    'writeall.yml': "name: wa\non: push\npermissions: write-all\njobs:\n  j:\n    runs-on: ubuntu-latest\n    timeout-minutes: 3\n    steps:\n      - run: echo hi\n",
}
REQS = {
    'requirements-a.txt': "pyyaml==6.0\n# 注释\n-r other.txt\nrequests\n",
    'requirements-b.txt': "numpy==1.26.0\n",
}


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `target/parity/gen_workflow_expected.py` 从真源生成）=====
    ///
    /// 真语料上 `workflow_policy` **全绿**（0 issues / 0 warns）⇒ 只靠契约对账，**各路判据一条
    /// 也没被核过**。本夹具逐分支踩：未钉 SHA / 缺版本引用 / 本地动作豁免 / 钉了带注释 /
    /// 钉了无注释 / 缺 permissions / write-all / 缺 timeout / 全绿 / 非 .yml 忽略 /
    /// requirements 已钉与未钉（`-` 开头跳过）。
    const WF_FILES: [(&str, &str); @@NF@@] = [
@@FILES@@
    ];
    const WF_REQS: [(&str, &str); @@NR@@] = [
@@REQS@@
    ];
    const WANT_WF_ISSUES: [&str; @@NI@@] = [
@@ISSUES@@
    ];
    const WANT_WF_WARNS: [&str; @@NW@@] = [
@@WARNS@@
    ];

    fn build_wf_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("workflow-branches");
        let wf = root.join(".github/workflows");
        std::fs::create_dir_all(&wf).unwrap();
        for (name, body) in WF_FILES {
            std::fs::write(wf.join(name), body).unwrap();
        }
        for (name, body) in WF_REQS {
            std::fs::write(root.join(".github").join(name), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_wf_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_WF_ISSUES, "逐条消息与次序都须与真源一致");
        assert_eq!(got.warns, WANT_WF_WARNS);
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "workflows": 4, "pinned_uses": 3,
                "with_explicit_permissions": 3, "requirements_files": 2
            }))
            .unwrap()
        ));
    }
'''

text = (TEMPLATE
        .replace('@@NF@@', str(len(WF_FILES)))
        .replace('@@FILES@@', "\n".join('        (%s, %s),' % (rs(k), rj(v))
                                       for k, v in sorted(WF_FILES.items())))
        .replace('@@NR@@', str(len(REQS)))
        .replace('@@REQS@@', "\n".join('        (%s, %s),' % (rs(k), rj(v))
                                      for k, v in sorted(REQS.items())))
        .replace('@@NI@@', str(len(WANT_ISSUES)))
        .replace('@@ISSUES@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False)
                                         for x in WANT_ISSUES))
        .replace('@@NW@@', str(len(WANT_WARNS)))
        .replace('@@WARNS@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False)
                                        for x in WANT_WARNS)))

path = pathlib.Path('engine/rust/src/workflow_policy.rs')
t = path.read_text(encoding='utf-8')
if 'workflow-branches' in t:
    print('已存在分支级判据，未追加')
else:
    path.write_text(t.rstrip() + '\n' + text, encoding='utf-8', newline='')
    print('已追加分支级判据：issues=%d warns=%d' % (len(WANT_ISSUES), len(WANT_WARNS)))
