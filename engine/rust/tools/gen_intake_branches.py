"""为 `intake.scan` 生成分支级判据。

用法：python engine/rust/target/parity/gen_intake_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import intake as itk  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'intake-branches'
if FIX.exists():
    shutil.rmtree(FIX)
(FIX / 'library').mkdir(parents=True)
(FIX / '.github' / 'scripts').mkdir(parents=True)

DECL = {
    "schema": "wrong/1",                      # schema 不匹配
    "updated": "2026/01/01",                  # 日期非法
    "after_action": "  ",                     # 空 → 缺 after_action
    "channels": {
        # mode 非法 + 缺 index_label
        "bad-mode": {"mode": "sometimes"},
        # author_only 但白名单空 + label 不在 INDEX
        "auth-only": {"mode": "author_only", "allowlist": ["  ", ""], "index_label": "不存在的措辞"},
        # 全绿
        "good": {"mode": "open", "index_label": "开放投稿"},
        # 合法 author_only
        "paused-ok": {"mode": "paused", "index_label": "暂停接收"},
    },
}
(FIX / 'library' / 'intake.json').write_text(
    json.dumps(DECL, ensure_ascii=False), encoding='utf-8', newline='')
(FIX / 'library' / 'INDEX.md').write_text(
    "# 馆藏\n\n> 开放投稿\n> 暂停接收\n", encoding='utf-8', newline='')

# 机器人脚本：一个缺、一个不引用声明件
(FIX / '.github' / 'scripts' / 'library_ingest.py').write_text(
    "# 读 library/intake.json\n", encoding='utf-8', newline='')

issues, stats = itk.scan(str(FIX))

print('# 真源：issues=%d' % len(issues))
for x in issues:
    print('#   ! %s' % x)
print('# stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `target/parity/gen_intake_branches.py` 从真源生成）=====
    ///
    /// 真语料上该面全绿 ⇒ 错误分支须合成夹具核。本夹具踩：schema / updated 非日期 / 缺 after_action /
    /// mode 非法 / author_only 白名单为空 / 缺 index_label / index_label 不在 INDEX /
    /// 合法 mode（open 与 paused）/ 缺机器人脚本 / 机器人未引用声明件。
    const WANT_IT_ISSUES: [&str; @@NI@@] = [
@@ISSUES@@
    ];

    fn build_intake_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("intake-branches");
        std::fs::create_dir_all(root.join("library")).unwrap();
        std::fs::create_dir_all(root.join(".github/scripts")).unwrap();
        std::fs::write(root.join("library/intake.json"), @@DECL@@).unwrap();
        std::fs::write(root.join("library/INDEX.md"), @@INDEX@@).unwrap();
        std::fs::write(root.join(".github/scripts/library_ingest.py"), @@BOT@@).unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_intake_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_IT_ISSUES, "逐条消息与次序都须与真源一致");
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "channels": @@NCH@@, "modes": @@MODES@@
            }))
            .unwrap()
        ));
    }
'''

text = (TEMPLATE
        .replace('@@NI@@', str(len(issues)))
        .replace('@@ISSUES@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False) for x in issues))
        .replace('@@DECL@@', rj(json.dumps(DECL, ensure_ascii=False)))
        .replace('@@INDEX@@', rj("# 馆藏\n\n> 开放投稿\n> 暂停接收\n"))
        .replace('@@BOT@@', rj("# 读 library/intake.json\n"))
        .replace('@@NCH@@', str(stats['channels']))
        .replace('@@MODES@@', json.dumps(stats['modes'], ensure_ascii=False)))

path = ROOT / 'engine' / 'rust' / 'src' / 'intake.rs'
t = path.read_text(encoding='utf-8')
if 'intake-branches' in t:
    print('# 已有分支级判据，未追加')
else:
    path.write_text(t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n'
                    + text + '}\n', encoding='utf-8', newline='')
    print('# 已追加分支级判据')
