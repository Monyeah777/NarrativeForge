"""精确列出 AST 事实的首个不同元素。"""
import json
import pathlib

P = pathlib.Path('.') / 'engine' / 'rust' / 'target' / 'parity'
py = json.loads((P / 'facts_py.json').read_text(encoding='utf-8'))
rs = json.loads((P / 'facts_rust.json').read_text(encoding='utf-8'))

for field in ('sinks', 'raises', 'modules'):
    n = 0
    print('===== %s' % field)
    for rel in sorted(set(py) & set(rs)):
        a, b = py[rel], rs[rel]
        if a is None or b is None or a[field] == b[field]:
            continue
        n += 1
        if n > 4:
            continue
        la, lb = a[field], b[field]
        k = next((i for i in range(min(len(la), len(lb))) if la[i] != lb[i]), min(len(la), len(lb)))
        print('  %s' % rel)
        print('    长度 真源=%d 本线=%d  首个不同 idx=%d' % (len(la), len(lb), k))
        if k < len(la):
            print('      真源: %s' % json.dumps(la[k], ensure_ascii=False))
        if k < len(lb):
            print('      本线: %s' % json.dumps(lb[k], ensure_ascii=False))
    print('  ---- 差异文件数: %d' % n)
