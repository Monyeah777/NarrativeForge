"""为 knowledge.verify_transform / verify_usage 生成 Rust 判据：
构造一个**触发各错误分支**的夹具语料，用真源跑出逐条消息，再打印成 assert 语句。

用法：python engine/rust/target/parity/gen_knowledge_expected.py > 片段.rs
"""
import json
from _rustlit import rs  # noqa: E402
import shutil
import sys
from pathlib import Path

ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import knowledge as kn  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'knowledge-branches'
if FIX.exists():
    shutil.rmtree(FIX)
(FIX / 'protocol').mkdir(parents=True)

decl = {
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
(FIX / 'protocol' / 'knowledge_sources.json').write_text(
    json.dumps(decl, ensure_ascii=False), encoding='utf-8')

# 消化记录：逐条踩一个分支
# 给 `to` 一个真实产物，才能触发 digest 比对分支（不符 / 相符各一例）
(FIX / 'protocol' / 'LAYERS.json').write_text('{}', encoding='utf-8')
import hashlib as _h
_real = _h.sha256((FIX / 'protocol' / 'LAYERS.json').read_bytes()).hexdigest()

(FIX / 'protocol' / 'transform_log.json').write_text(json.dumps({
    "schema": "nf-transform-log/1",
    "entries": [
        "不是对象",
        {},                                                     # 缺全部必填
        {"from": "ghost", "to": "no/such.md", "digest": "x",
         "reviewed_by": "a", "reviewed_at": "2026-13-99", "evidence": [],
         "reuse_count": -1, "promoted": True},                  # from 非法 / to 不存在 / 日期非法 / 转正缺证据档 / reuse_count 负
        {"from": "ext-x", "to": "protocol/LAYERS.json", "digest": "deadbeef",
         "reviewed_by": "  ", "reviewed_at": "2026-01-01", "evidence": [],
         "promoted": True},                                     # digest 不符 / 转正无复核人
        {"from": "ext-x", "to": "protocol/LAYERS.json", "digest": _real,
         "reviewed_by": "张三", "reviewed_at": "2026-01-01",
         "evidence": ["machine-checkable", "reproducible", "externally-attestable"],
         "promoted": True, "reuse_count": 4},                    # 全绿：证明判据不是空转
    ],
}, ensure_ascii=False), encoding='utf-8')

# 频率台账：schema 不符 / 幽灵源 / 负计数 / total 不一致 / 与 reuse_count 不可复算
(FIX / 'protocol' / 'knowledge_usage.json').write_text(json.dumps({
    "schema": "wrong/1",
    "counts": {"ghost-source": 3, "ext-x": -1, "nf-protocol": 4},
    "total": 999,
}, ensure_ascii=False), encoding='utf-8')

t = kn.verify_transform(str(FIX))
u = kn.verify_usage(str(FIX))
print('// ===== 以下由 gen_knowledge_expected.py 从真源生成，勿手改 =====')
print('// transform issues = %d, stats = %s' % (len(t[0]), json.dumps(t[2], ensure_ascii=False, sort_keys=True)))
print('// usage     issues = %d, stats = %s' % (len(u[0]), json.dumps(u[2], ensure_ascii=False, sort_keys=True)))
print('const WANT_TRANSFORM: [&str; %d] = [' % len(t[0]))
for x in t[0]:
    print('    %s,' % json.dumps(x, ensure_ascii=False))
print('];')
print('const WANT_USAGE: [&str; %d] = [' % len(u[0]))
for x in u[0]:
    print('    %s,' % json.dumps(x, ensure_ascii=False))
print('];')
print('// transform stats: %s' % json.dumps(t[2], ensure_ascii=False, sort_keys=True))
print('// usage stats:     %s' % json.dumps(u[2], ensure_ascii=False, sort_keys=True))
