import json, pathlib
from _rustlit import rs  # noqa: E402

WANT_TRANSFORM = [
    "记录 #1 非对象",
    "记录 #2 缺必填字段：from",
    "记录 #2 缺必填字段：to",
    "记录 #2 缺必填字段：digest",
    "记录 #2 缺必填字段：reviewed_by",
    "记录 #2 缺必填字段：reviewed_at",
    "记录 #2 缺必填字段：evidence",
    "记录 #3 的 from 不是已声明的参考级源：ghost",
    "记录 #3 的产物不存在：no/such.md",
    "记录 #3 声明转正但缺证据档：machine-checkable/reproducible/externally-attestable",
    "记录 #3 的 reuse_count 非非负整数（频次判据不可复算）",
    "记录 #4 的产物摘要与记录不一致：protocol/LAYERS.json（产物已改，记录失效；修复指引：重新消化并更新 digest）",
    "记录 #4 声明转正但缺证据档：machine-checkable/reproducible/externally-attestable",
    "记录 #4 声明转正但无复核人（消化审核未双签）",
]
WANT_USAGE = [
    "频率台账 schema 不匹配（期望 nf-knowledge-usage/1）",
    "频率台账含未声明的源：ghost-source（防幽灵频次）",
    "频率计数非非负整数：ext-x",
    "频率台账 total 与 counts 求和不一致（手改痕迹）",
    "频次不可复算：ghost 的记录 reuse_count=-1，频率台账=None（修复指引：按 trace 重算，不要手写频次）",
    "频次不可复算：ext-x 的记录 reuse_count=4，频率台账=-1（修复指引：按 trace 重算，不要手写频次）",
]

DECL = {
    "schema": "nf-knowledge-sources/1",
    "authority_vocabulary": ["contract", "reference"],
    "kind_vocabulary": ["local-compiled", "external-retrieval"],
    "visibility_vocabulary": ["public", "internal", "restricted"],
    "sources": [
        {"id": "nf-protocol", "authority": "contract", "kind": "local-compiled",
         "locator": "protocol/LAYERS.json", "requires_source_label": False,
         "visibility": "public", "freshness": {"policy": "stale_after"}},
        {"id": "ext-x", "authority": "reference", "kind": "external-retrieval",
         "locator": "protocol/LAYERS.json", "requires_source_label": True,
         "visibility": "public", "freshness": {"policy": "ttl", "ttl_days": 7}},
    ],
    "query_order": ["nf-protocol", "ext-x"],
    "promotion": {"evidence_tiers": ["machine-checkable", "reproducible", "externally-attestable"],
                  "triggers": ["reuse-frequency", "author-mark", "machine-check-pass"],
                  "rule": "r", "on_missing_evidence": "stay-reference"},
    "review": {"machine_gates": ["g"], "rule": "r"},
    "cognition": {"filter_module": "M23"},
}

LOG_HEAD = {
    "schema": "nf-transform-log/1",
    "entries": [
        "不是对象",
        {},
        {"from": "ghost", "to": "no/such.md", "digest": "x",
         "reviewed_by": "a", "reviewed_at": "2026-13-99", "evidence": [],
         "reuse_count": -1, "promoted": True},
        {"from": "ext-x", "to": "protocol/LAYERS.json", "digest": "deadbeef",
         "reviewed_by": "  ", "reviewed_at": "2026-01-01", "evidence": [],
         "promoted": True},
    ],
}
USAGE = {
    "schema": "wrong/1",
    "counts": {"ghost-source": 3, "ext-x": -1, "nf-protocol": 4},
    "total": 999,
}


def rust_str_list(v):
    return "\n".join('            %s,' % json.dumps(x, ensure_ascii=False) for x in v)


def raw(s):
    # Rust 原始字符串：内容里没有 "# 组合即可
    assert '"#' not in s
    return 'r#"%s"#' % s


out = []
out.append("""
#[cfg(test)]
mod tests {
    use super::*;

    /// 真源在真语料上是**全绿**的（0 issues）⇒ 只靠契约对账**核不到错误路径**。
    /// 本判据构造一个逐条踩分支的夹具，期望值由 `target/parity/gen_knowledge_expected.py`
    /// 从真源生成（勿手改）——这样每条消息的措辞都真的被核过。
    /// 第 5 条是**全绿样本**：证明这套判据不是空转。
    const WANT_TRANSFORM: [&str; %d] = [
%s
    ];
    const WANT_USAGE: [&str; %d] = [
%s
    ];

    fn build_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("knowledge-branches");
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        std::fs::write(root.join("protocol/LAYERS.json"), "{}").unwrap();
        let real = crate::merkle::hex(&crate::merkle::sha256(b"{}"));
        std::fs::write(root.join("protocol/knowledge_sources.json"), %s).unwrap();
        let mut log = LOG_HEAD.clone();
        if let Some(serde_json::Value::Array(a)) = log.get_mut("entries") {
            a.push(serde_json::json!({
                "from": "ext-x", "to": "protocol/LAYERS.json", "digest": real,
                "reviewed_by": "张三", "reviewed_at": "2026-01-01",
                "evidence": ["machine-checkable", "reproducible", "externally-attestable"],
                "promoted": true, "reuse_count": 4
            }));
        }
        std::fs::write(root.join("protocol/transform_log.json"), log.to_string()).unwrap();
        std::fs::write(root.join("protocol/knowledge_usage.json"), USAGE_JSON).unwrap();
        root
    }

    #[test]
    fn verify_transform_matches_truth_source_branch_by_branch() {
        let root = build_fixture();
        let got = verify_transform(&root);
        assert_eq!(got.issues, WANT_TRANSFORM, "逐条消息须与真源一致");
        assert_eq!(
            got.stats,
            crate::jsonread::convert(&serde_json::json!({"entries": 5, "promoted": 3})).unwrap()
        );
    }

    #[test]
    fn verify_usage_matches_truth_source_branch_by_branch() {
        let root = build_fixture();
        let got = verify_usage(&root);
        assert_eq!(got.issues, WANT_USAGE, "逐条消息须与真源一致");
        assert_eq!(
            got.stats,
            crate::jsonread::convert(
                &serde_json::json!({"events": 6, "sources_with_usage": 3})
            )
            .unwrap()
        );
    }
}
""" % (
    len(WANT_TRANSFORM), rust_str_list(WANT_TRANSFORM),
    len(WANT_USAGE), rust_str_list(WANT_USAGE),
    raw(json.dumps(DECL, ensure_ascii=False)),
))

text = "\n".join(out).replace('USAGE_JSON', raw(json.dumps(USAGE, ensure_ascii=False)))

# LOG_HEAD 常量
log_const = ('\n    static LOG_HEAD: std::sync::OnceLock<serde_json::Value> = '
             'std::sync::OnceLock::new();\n'
             '    fn log_head() -> &\'static serde_json::Value {\n'
             '        LOG_HEAD.get_or_init(|| serde_json::from_str(%s).unwrap())\n'
             '    }\n' % raw(json.dumps(LOG_HEAD, ensure_ascii=False)))
text = text.replace('    fn build_fixture()', log_const + '\n    fn build_fixture()')
text = text.replace('LOG_HEAD.clone()', 'log_head().clone()')

path = pathlib.Path('engine/rust/src/knowledge.rs')
t = path.read_text(encoding='utf-8')
if '#[cfg(test)]' in t:
    print('knowledge.rs 已有 tests 模块，未追加')
else:
    path.write_text(t.rstrip() + '\n' + text, encoding='utf-8', newline='')
    print('已追加 tests 模块')
    print('WANT_TRANSFORM:', len(WANT_TRANSFORM), ' WANT_USAGE:', len(WANT_USAGE))
