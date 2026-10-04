"""揪出 `tools/` 里**把 `json.dumps` 输出当 Rust 字面量**的写法。

## 为什么需要它（同一个陷阱咬了三次）

`json.dumps` 默认 `ensure_ascii=True` ⇒ 中文写成 `\\uXXXX` ⇒ **Rust 只认 `\\u{XXXX}`**，
生成的源码直接编译不过（`incorrect unicode escape sequence`）。
实测踩过：`pipeline-dryrun` 移植时（fork 报）、批量替换那轮（我报）、`doc-kinds` 生成器（我又报）。

## 判据（能区分两类用法）

同一文件里 `json.dumps` 有两种正当用途，靠**有没有 `ensure_ascii` 参数**区分：

- **不带** `ensure_ascii` ⇒ 输出会当 Rust 字面量用 ⇒ **应改走 `_rustlit.rs()`** ⇒ 报错；
- **带** `ensure_ascii=False` ⇒ 是写 JSON 夹具内容（文件要可读中文）⇒ 正常。

用法：python engine/rust/tools/audit_rust_literals.py [仓库根]
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
TOOLS = ROOT / 'engine' / 'rust' / 'tools'

def matching_paren(s, i):
    depth = 0
    while i < len(s):
        if s[i] == '(':
            depth += 1
        elif s[i] == ')':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


bad = []
for p in sorted(TOOLS.glob('*.py')):
    if p.name.startswith('_') or p.name == 'audit_rust_literals.py':
        continue
    text = p.read_text(encoding='utf-8')
    pos = 0
    while True:
        j = text.find('json.dumps(', pos)
        if j < 0:
            break
        end = matching_paren(text, j + len('json.dumps'))
        if end < 0:
            break
        call = text[j:end + 1]
        # 整个调用里没有 ensure_ascii ⇒ 输出会当 Rust 字面量用（或本就该显式声明）
        if 'ensure_ascii' not in call:
            line_no = text[:j].count(chr(10)) + 1
            bad.append('%s:%d  %s' % (p.name, line_no, call.splitlines()[0].strip()[:80]))
        pos = end + 1

if bad:
    print('  [FAIL] 以下 `json.dumps` 调用缺 `ensure_ascii`，若其输出当 Rust 字面量用会编译不过：')
    for b in bad:
        print('    ' + b)
    print('  （正当用法：写 JSON 夹具内容时带 ensure_ascii=False；作 Rust 字面量时改走 `_rustlit.rs()`）')
    sys.exit(1)
print('  [PASS] tools/ 内无「缺 ensure_ascii 的 json.dumps」写法')
