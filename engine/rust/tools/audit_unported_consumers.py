"""复核「未移植的那个子扫描器只是可选体量、不是缺口」——查它们的**反向依赖**。

## 为什么需要它

我在 README 里断言：`depth_clean` 的 8 个未移植子扫描器属于「**可做但没做**」（体量），
而不是「不可做」。这个断言若错了（某个子扫描器其实**支撑着某条已移植的判据**），
那结论就不是"没做完"，而是"**声称做完的面其实有缺口**"——性质完全不同。

## 判据

对每个未移植模块，扫全仓有哪些 `.py` 引用它：

- 引用者**只在** `quality_depth_scan` / CLI / 测试 / 未移植面里 ⇒ 确实是可选体量；
- 引用者里出现**已移植面**的模块 ⇒ **缺口**，退出码 1。

用法：python engine/rust/tools/audit_unported_consumers.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()

#: `quality_depth_scan` 聚合但本线未移植的 8 个。
UNPORTED = [
    'concept_graph', 'domain_pack', 'output_forms', 'pack_combo',
    'payload_consumer', 'tool_face', 'world_model', 'world_slots',
]

#: 本线**已移植**的真源模块（判据链上的）。
PORTED = {
    'receipts', 'repo_stats', 'layers', 'score', 'conformance_report', 'conformance_scan',
    'conformance_decl', 'doc_hygiene', 'module_signature', 'registry_cross', 'modeling',
    'knowledge', 'mdblocks', 'handover', 'postmortem', 'decisions', 'patterns', 'schema_lint',
    'baseline', 'asset_density', 'verify_report', 'payload_registry', 'instruction_step_audit',
    'asset_ledger_projection', 'key_naming', 'intake', 'library_entries', 'library', 'rating_gate',
    'audit', 'workflow_policy', 'judgement_coverage', 'license_gate', 'coupling_metrics',
    'machine_contract', 'endpoint', 'mcp_package', 'pipeline_loader', 'pipelinerun',
    'payload_harvest', 'io_types', 'drill_fidelity', 'execution_drill', 'round_drill',
    'state_front', 'declaration', 'public_surface',
}

SOURCES = [p for p in (ROOT / 'desktop' / 'src').rglob('*.py')]
SOURCES += [p for p in (ROOT / 'scripts').rglob('*.py')]
TEXTS = {p: p.read_text(encoding='utf-8', errors='replace') for p in SOURCES}

gaps = []
for name in UNPORTED:
    pat = re.compile(r'(?:^|\n)\s*(?:from\s+core\.?\w*\s+import\s+[^\n]*\b%s\b'
                     r'|from\s+core\.%s\s+import|import\s+core\.%s\b)' % (name, name, name))
    users = []
    for p, text in TEXTS.items():
        if name in text and pat.search(text):
            users.append(p.stem)
    users = sorted(set(users))
    ported_users = sorted(set(users) & PORTED)
    verdict = '缺口' if ported_users else '可选体量'
    if ported_users:
        gaps.append(name)
    print('  %-18s 引用者 %-46s → %s'
          % (name, '、'.join(users)[:46] or '(无)', verdict))
    if ported_users:
        print('        ⚠ 其中**已移植面**在用：%s' % '、'.join(ported_users))

print()
print('  结论：%s' % ('发现 %d 处缺口：%s' % (len(gaps), gaps) if gaps
                    else '8 个都只被未移植面/CLI 引用 ⇒ 「可选体量」的断言成立'))
sys.exit(1 if gaps else 0)
