"""证明「unparser 的括号差异」对本线判据**无影响**——用可检的方式，而不是"我认为"。

## 背景

逐文件对账后，`sinks` 只剩 1 处差异（`scripts/sast_check.py` 第 78 行）：

    真源: collections.Counter((r.get('issue_severity') for r in rows)).most_common
    本线: collections.Counter(r.get('issue_severity') for r in rows).most_common

CPython 的 `ast.unparse` 在「生成器表达式作为唯一实参」时补一层括号，rustpython 的不补。

## 判据

R6 只用 `call` 做两件事（真源 `purity_scan` 第 365–382 行）：

1. `call in DANGEROUS_CALLS` —— 整串精确匹配；
2. `call.rsplit(".", 1)[-1] in METHOD_SINKS` —— **末段**匹配；
3. `shell_true` —— 与本串无关。

故只要**两侧导出的 `(行号, 命中标志名)` 序列完全相同**，这个差异就是无害的。
本脚本直接算这个序列并比对：不一致即退出码 1。

用法：python engine/rust/tools/check_ast_facts_inert.py <仓库根>
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
P = ROOT / 'engine' / 'rust' / 'target' / 'parity'
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import purity_scan as p  # noqa: E402


def flags_for(sinks):
    """复刻真源 R6 的「命中标志」推导（第 365–377 行），只用 `call` 与末段。"""
    out = []
    for lineno, call, shell_true in sinks:
        names = []
        if call in p.DANGEROUS_CALLS:
            names.append(call)
        method = call.rsplit('.', 1)[-1]
        if method in p.METHOD_SINKS:
            names.append(method)
        if shell_true:
            names.append('subprocess(shell=True)')
        for n in names:
            out.append((lineno, n))
    return out


py = json.loads((P / 'facts_py.json').read_text(encoding='utf-8'))
rs = json.loads((P / 'facts_rust.json').read_text(encoding='utf-8'))

bad = []
n_sinks = 0
for rel in sorted(set(py) & set(rs)):
    a, b = py[rel], rs[rel]
    if a is None or b is None:
        if (a is None) != (b is None):
            bad.append('%s：解析可用性不一致' % rel)
        continue
    n_sinks += len(a['sinks'])
    fa = flags_for([tuple(x) for x in a['sinks']])
    fb = flags_for([tuple(x) for x in b['sinks']])
    if fa != fb:
        bad.append('%s：命中标志序列不同\n    真源 %s\n    本线 %s'
                   % (rel, fa[:6], fb[:6]))

print('  比对 %d 个文件 / %d 条 sink 候选' % (len(py), n_sinks))
if bad:
    print('  [FAIL] 有 %d 个文件的**命中标志**不同（那就不是无害差异）：' % len(bad))
    for x in bad[:5]:
        print('    ' + x)
    sys.exit(1)
print('  [PASS] 全部文件的命中标志序列一致 ⇒ unparser 的括号差异对本线判据**无影响**（有据，非推断）')
