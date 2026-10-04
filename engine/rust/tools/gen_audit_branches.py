"""为 `audit.scan` 生成分支级判据：构造逐分支踩的合成审计面，用真源跑出 issues/warns/stats，
既打印期望值、也把 Rust 判据直接写进 `src/audit.rs`。

用法：python engine/rust/target/parity/gen_audit_branches.py
"""
import hashlib
from _rustlit import rs  # noqa: E402
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import audit as au  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'audit-branches'
if FIX.exists():
    shutil.rmtree(FIX)
(FIX / 'protocol').mkdir(parents=True)
(FIX / 'results' / 'audit').mkdir(parents=True)

DECL = {"schema": "nf-audit/1", "verdict_vocabulary": ["pass", "fail", "warn"], "rules": ["r"]}
(FIX / 'protocol' / 'audit.json').write_text(json.dumps(DECL, ensure_ascii=False), encoding='utf-8')

# ⚠️ `newline=''`：否则 Windows 把 \n 翻成 CRLF，与 Rust 侧写的 LF 不是同一份件（踩过）
(FIX / 'subject.md').write_text("hello\n", encoding='utf-8', newline='')
GOOD = hashlib.sha256(b"hello\n").hexdigest()
Z64, O64 = '0' * 64, '1' * 64

A1 = "---\ntitle: 无编号\n---\n正文\n"          # 无审计头 → legacy（WARN 挂账，不判死）

A2_P = (
    "---\nid: AUD-0002\nscope: s\nverdict: 越词表\ndate: 2026/01/01\nauditor: a\nsubjects:\n"
    "  - 没有冒号\n"
    "  - no/such.md:%s\n"
    "  - subject.md:%s\n"
    "  - subject.md:%s\n"
    "accepted_by: 张三\naccepted_at: 不是日期\n---\n正文\n" % (Z64, GOOD, O64)
)
A2_R = (
    "---\nid: AUD-0002\nscope: s\nverdict: 越词表\ndate: 2026/01/01\nauditor: a\nsubjects:\n"
    "  - 没有冒号\n"
    "  - no/such.md:@Z64@\n"
    "  - subject.md:@GOOD@\n"
    "  - subject.md:@O64@\n"
    "accepted_by: 张三\naccepted_at: 不是日期\n---\n正文\n"
)
A3_P = (
    "---\nid: AUD-0003\nscope: s\nverdict: pass\ndate: 2026-01-02\nauditor: a\nsubjects:\n"
    "  - subject.md:%s\n"
    "accepted_by: 李四\naccepted_at: 2026-01-03\n---\n正文\n" % GOOD
)
A3_R = A3_P.replace(GOOD, "@GOOD@")

for name, body in (('A1.md', A1), ('A2.md', A2_P), ('A3.md', A3_P)):
    (FIX / 'results' / 'audit' / name).write_text(body, encoding='utf-8', newline='')

issues, warns, stats = au.scan(str(FIX))

print('# 真源：issues=%d warns=%d' % (len(issues), len(warns)))
for x in issues:
    print('#   ! %s' % x)
for x in warns:
    print('#   ~ %s' % x)
print('# stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))


def rj(s):
    assert '"#' not in s, '内容含 "# 会提前终止 Rust 原始字符串'
    return 'r#"%s"#' % s


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `target/parity/gen_audit_branches.py` 从真源生成）=====
    ///
    /// 真语料上 `audit` 的 issues 会随外部状态漂（`verify.sh` 一改，多件审计的 subjects 摘要
    /// 就失效）——**正是"结论依赖外部状态"的面，最不该只靠真语料对账**。
    /// 本夹具逐分支踩：无审计头(legacy) / verdict 越词表 / date 非法 / subjects 无冒号 /
    /// 被审对象不存在 / 摘要不符 / 摘要相符 / accepted_by 缺合法 accepted_at / 签收双要素齐(全绿)。
    const WANT_AUDIT_ISSUES: [&str; @@NI@@] = [
@@ISSUES@@
    ];
    const WANT_AUDIT_WARNS: [&str; @@NW@@] = [
@@WARNS@@
    ];

    fn build_audit_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("audit-branches");
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        std::fs::create_dir_all(root.join("results/audit")).unwrap();
        std::fs::write(root.join("protocol/audit.json"), @@DECL@@).unwrap();
        std::fs::write(root.join("subject.md"), "hello\n").unwrap();
        let good = crate::merkle::hex(&crate::merkle::sha256(b"hello\n"));
        std::fs::write(root.join("results/audit/A1.md"), @@A1@@).unwrap();
        let a2 = @@A2@@
            .replace("@GOOD@", &good)
            .replace("@Z64@", &"0".repeat(64))
            .replace("@O64@", &"1".repeat(64));
        std::fs::write(root.join("results/audit/A2.md"), a2).unwrap();
        let a3 = @@A3@@.replace("@GOOD@", &good);
        std::fs::write(root.join("results/audit/A3.md"), a3).unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_audit_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_AUDIT_ISSUES, "逐条消息与次序都须与真源一致");
        assert_eq!(got.warns, WANT_AUDIT_WARNS);
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "audits": @@NA@@, "with_header": @@NW2@@,
                "legacy": @@NL@@, "subjects_ok": @@NS@@
            }))
            .unwrap()
        ));
    }
'''

text = (TEMPLATE
        .replace('@@NI@@', str(len(issues)))
        .replace('@@ISSUES@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False) for x in issues))
        .replace('@@NW@@', str(len(warns)))
        .replace('@@WARNS@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False) for x in warns))
        .replace('@@DECL@@', rj(json.dumps(DECL, ensure_ascii=False)))
        .replace('@@A1@@', rj(A1))
        .replace('@@A2@@', rj(A2_R))
        .replace('@@A3@@', rj(A3_R))
        .replace('@@NA@@', str(stats['audits']))
        .replace('@@NW2@@', str(stats['with_header']))
        .replace('@@NL@@', str(stats['legacy']))
        .replace('@@NS@@', str(stats['subjects_ok'])))

path = ROOT / 'engine' / 'rust' / 'src' / 'audit.rs'
t = path.read_text(encoding='utf-8')
if '#[cfg(test)]' in t:
    print('# audit.rs 已有 tests 模块，未追加')
else:
    path.write_text(t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n'
                    + text + '}\n', encoding='utf-8', newline='')
    print('# 已追加分支级判据')
