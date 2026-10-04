"""定位 AST 事实的差异（真源 vs 本线）。"""
import json
import pathlib
import sys

ROOT = pathlib.Path('.')
P = ROOT / 'engine' / 'rust' / 'target' / 'parity'
py = json.loads((P / 'facts_py.json').read_text(encoding='utf-8'))
rs = json.loads((P / 'facts_rust.json').read_text(encoding='utf-8'))

only_py = sorted(set(py) - set(rs))
only_rs = sorted(set(rs) - set(py))
if only_py:
    print('仅真源有:', only_py[:5])
if only_rs:
    print('仅本线有:', only_rs[:5])

bad = []
for rel in sorted(set(py) & set(rs)):
    a, b = py[rel], rs[rel]
    if a == b:
        continue
    if a is None or b is None:
        bad.append((rel, 'parse', a is None, b is None))
        continue
    for k in ('raises', 'guarded', 'modules', 'sinks'):
        if a[k] != b[k]:
            bad.append((rel, k, a[k], b[k]))

print('差异文件数: %d / %d' % (len(bad), len(py)))
fields = {}
for _, k, *_ in bad:
    fields[k] = fields.get(k, 0) + 1
print('按字段:', fields)
print()
shown = 0
for rel, k, a, b in bad:
    if shown >= 6:
        break
    shown += 1
    print('---- %s  [%s]' % (rel, k))
    print('   真源:', json.dumps(a, ensure_ascii=False)[:300])
    print('   本线:', json.dumps(b, ensure_ascii=False)[:300])
