"""为 `license_gate.scan` 生成分支级判据（真源在本面全绿 ⇒ 错误路径须合成夹具核）。

用法：python engine/rust/target/parity/gen_license_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import license_gate as lg  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'license-branches'
if FIX.exists():
    shutil.rmtree(FIX)
(FIX / 'library').mkdir(parents=True)

# 登记表：每行踩一种分支。列数决定 license 取哪一格：
#   `_cells` 后 len>=7 才取 c[5]，否则 license=""（真源如此）
INDEX = (
    "# 馆藏\n\n"
    "| 编号 | 标题 | 形态/领域 | 投稿人 | 入库日期 | 许可 | 分级 | 状态 | 一句话 |\n"
    "|---|---|---|---|---|---|---|---|---|\n"
    "| NF-1 | 缺许可列 | t | a | 2026-01-01 |  | g | active | s |\n"          # 空许可 → FAIL
    "| NF-2 | 表达式非法 | t | a | 2026-01-01 | Frobnicate | g | active | s |\n"  # 越词表 → FAIL
    "| NF-3 | 未声明 | t | a | 2026-01-01 | 未声明 | g | active | s |\n"          # WARN undeclared
    "| NF-4 | 无内联 | t | a | 2026-01-01 | MIT | g | active | s |\n"             # WARN no_inline
    "| NF-5 | 双源不一致 | t | a | 2026-01-01 | MIT | g | active | s |\n"         # WARN mismatched
    "| NF-6 | 全绿 | t | a | 2026-01-01 | Apache-2.0 | g | active | s |\n"        # 全绿
    "| NF-7 | 表达式合法 | t | a | 2026-01-01 | MIT OR Apache-2.0 | g | active | s |\n"  # 表达式合法（无内联 → WARN）
    "| NF-8 |\n"                                                                  # 单元格太少 → 不计入
)
(FIX / 'library' / 'INDEX.md').write_text(INDEX, encoding='utf-8', newline='')

ENTRIES = {
    'NF-1.md': "# x\n",
    'NF-2.md': "# x\n",
    'NF-3.md': "> 许可：未声明\n",
    'NF-4.md': "# x\n",
    'NF-5.md': "> 许可：BSD-3-Clause\n",
    'NF-6.md': "> 许可：Apache-2.0\n",
    'NF-7.md': "# x\n",
}
for name, body in ENTRIES.items():
    (FIX / 'library' / name).write_text(body, encoding='utf-8', newline='')

issues, stats = lg.scan(str(FIX))

print('# 真源：issues=%d' % len(issues))
for x in issues:
    print('#   ! %s' % x)
print('# stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `target/parity/gen_license_branches.py` 从真源生成）=====
    ///
    /// 真语料上许可门是**全绿**的 ⇒ 只靠契约对账核不到任何错误分支。
    /// 本夹具逐分支踩：空许可列(FAIL) / 表达式越词表(FAIL) / `未声明`(WARN) / 无内联(WARN) /
    /// 双源不一致(WARN) / 单 id 全绿 / SPDX 表达式合法 / 单元格过少不计入。
    const WANT_LIC_ISSUES: [&str; @@NI@@] = [
@@ISSUES@@
    ];

    fn build_license_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("license-branches");
        std::fs::create_dir_all(root.join("library")).unwrap();
        std::fs::write(root.join("library/INDEX.md"), @@INDEX@@).unwrap();
        for (name, body) in @@ENTRIES@@ {
            std::fs::write(root.join("library").join(name), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_license_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_LIC_ISSUES, "逐条消息与次序都须与真源一致");
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "entries": @@NE@@, "declared": @@ND@@,
                "undeclared": @@UND@@, "unknown": @@UNK@@,
                "no_inline": @@NOI@@, "mismatched": @@MIS@@,
                "warnings": @@WARN@@
            }))
            .unwrap()
        ));
    }
'''

entries_rust = "[\n" + "\n".join(
    '            (%s, %s),' % (rs(k), rj(v)) for k, v in sorted(ENTRIES.items())
) + "\n        ]"

text = (TEMPLATE
        .replace('@@NI@@', str(len(issues)))
        .replace('@@ISSUES@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False) for x in issues))
        .replace('@@INDEX@@', rj(INDEX))
        .replace('@@ENTRIES@@', entries_rust)
        .replace('@@NE@@', str(stats['entries']))
        .replace('@@ND@@', str(stats['declared']))
        .replace('@@UND@@', json.dumps(stats['undeclared'], ensure_ascii=False))
        .replace('@@UNK@@', json.dumps(stats['unknown'], ensure_ascii=False))
        .replace('@@NOI@@', json.dumps(stats['no_inline'], ensure_ascii=False))
        .replace('@@MIS@@', json.dumps(stats['mismatched'], ensure_ascii=False))
        .replace('@@WARN@@', json.dumps(stats['warnings'], ensure_ascii=False)))

path = ROOT / 'engine' / 'rust' / 'src' / 'license_gate.rs'
t = path.read_text(encoding='utf-8')
if 'license-branches' in t:
    print('# 已有分支级判据，未追加')
else:
    idx = t.rstrip().rfind('\n}')
    path.write_text(t[:idx] + text + t[idx:], encoding='utf-8', newline='')
    print('# 已追加分支级判据')
