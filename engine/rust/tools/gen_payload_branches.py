"""为 `payload_registry.scan` 生成分支级判据。

用法：python engine/rust/target/parity/gen_payload_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import payload_registry as pr  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'payload-branches'
if FIX.exists():
    shutil.rmtree(FIX)
(FIX / 'protocol').mkdir(parents=True)
(FIX / 'desktop' / 'src' / 'core').mkdir(parents=True)
(FIX / '04_模块库' / '通用类').mkdir(parents=True)

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema", "events"],
    "properties": {
        "schema": {"type": "string", "enum": ["community-event-registry/1"]},
        "events": {"type": "object"},
    },
}
(FIX / 'protocol' / 'event_payload.schema.json').write_text(
    json.dumps(SCHEMA, ensure_ascii=False), encoding='utf-8', newline='')

# 注册表：`b` 无 fields（pending）、`dead_ev` 无人引用（死注册）；`schema` 故意写错以踩 subset_validate
REGISTRY = {
    "schema": "wrong/1",
    "events": {
        "a": {"fields": ["f1"]},
        "b": {},
        "dead_ev": {"fields": ["f2"]},
    },
}
(FIX / 'protocol' / 'event_registry.json').write_text(
    json.dumps(REGISTRY, ensure_ascii=False), encoding='utf-8', newline='')

# 模块文档：publish a；subscribe b 与一个未登记事件
(FIX / '04_模块库' / '通用类' / 'M01_x.md').write_text(
    "```yaml\nmachine_contract:\n  id: M01\n  events:\n    publish: [a]\n"
    "    subscribe: [b, unregistered_ev]\n```\n", encoding='utf-8', newline='')

# registry.json 的 subscriptions 也要计入 used
(FIX / 'desktop' / 'src' / 'core' / 'registry.json').write_text(
    json.dumps({"subscriptions": {"sub_ev": {}}}, ensure_ascii=False),
    encoding='utf-8', newline='')

issues, stats = pr.scan(str(FIX))

print('# 真源：issues=%d' % len(issues))
for x in issues:
    print('#   ! %s' % x)
print('# stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `target/parity/gen_payload_branches.py` 从真源生成）=====
    ///
    /// 真语料上该面只有固定的几条 ⇒ 错误分支须合成夹具核。本夹具踩：
    /// schema 自校验不过 / 死注册（登记了没人引用）/ 漏登（引用未登记）/ `fields` 缺失计入 pending /
    /// `registry.subscriptions` 也计入 used。
    const WANT_PL_ISSUES: [&str; @@NI@@] = [
@@ISSUES@@
    ];

    fn build_payload_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("payload-branches");
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        std::fs::create_dir_all(root.join("desktop/src/core")).unwrap();
        std::fs::create_dir_all(root.join("04_模块库/通用类")).unwrap();
        std::fs::write(root.join("protocol/event_payload.schema.json"), @@SCHEMA@@).unwrap();
        std::fs::write(root.join("protocol/event_registry.json"), @@REGISTRY@@).unwrap();
        std::fs::write(root.join("04_模块库/通用类/M01_x.md"), @@DOC@@).unwrap();
        std::fs::write(root.join("desktop/src/core/registry.json"), @@REGJSON@@).unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_payload_fixture();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, WANT_PL_ISSUES, "逐条消息与次序都须与真源一致");
        assert!(crate::jsonread::json_eq(
            &stats.map(|s| s.to_json()).unwrap_or_else(|| serde_json::from_str("{}").unwrap()),
            &crate::jsonread::convert(&serde_json::json!({
                "registered": @@NR@@, "used": @@NU@@,
                "declared": @@ND@@, "pending": @@NP@@
            }))
            .unwrap()
        ));
    }
'''

DOC = ("```yaml\nmachine_contract:\n  id: M01\n  events:\n    publish: [a]\n"
       "    subscribe: [b, unregistered_ev]\n```\n")

text = (TEMPLATE
        .replace('@@NI@@', str(len(issues)))
        .replace('@@ISSUES@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False) for x in issues))
        .replace('@@SCHEMA@@', rj(json.dumps(SCHEMA, ensure_ascii=False)))
        .replace('@@REGISTRY@@', rj(json.dumps(REGISTRY, ensure_ascii=False)))
        .replace('@@DOC@@', rj(DOC))
        .replace('@@REGJSON@@', rj(json.dumps({"subscriptions": {"sub_ev": {}}}, ensure_ascii=False)))
        .replace('@@NR@@', str(stats['registered']))
        .replace('@@NU@@', str(stats['used']))
        .replace('@@ND@@', str(stats['declared']))
        .replace('@@NP@@', str(stats['pending'])))

path = ROOT / 'engine' / 'rust' / 'src' / 'payload_registry.rs'
t = path.read_text(encoding='utf-8')
if 'payload-branches' in t:
    print('# 已有分支级判据，未追加')
else:
    path.write_text(t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n'
                    + text + '}\n', encoding='utf-8', newline='')
    print('# 已追加分支级判据')
