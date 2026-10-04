"""探针：逐构造定位「哪些路径的 Call 没被收集」。

把探针文件临时放进 `scripts/`（它属于 `purity_scan.IMPORT_SCAN` 三条面之一），
两侧各自算 `_ast_facts`，再比对——**用完即删**。

用法：python engine/rust/tools/probe_ast_paths.py
"""
import ast
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path('.').resolve()
PROBE = ROOT / 'scripts' / 'zz_probe_ast_paths.py'
TRUTH = ROOT / 'engine' / 'rust' / 'target' / 'parity' / 'probe_py.json'
RUST = ROOT / 'engine' / 'rust' / 'target' / 'parity' / 'probe_rs.json'
EXE = ROOT / 'engine' / 'rust' / 'target' / 'release' / 'nf-rs.exe'

# 每种构造单独一行，便于按行号对号入座
CASES = [
    'a1 = f1(1)',                                   # 1 普通表达式
    'with open2("x") as fh:',                        # 2 with 的 context_expr
    '    a2 = f3(fh)',
    'a3 = [f4(i) for i in y]',                       # 4 列表推导
    'a4 = {k: f5(k) for k in y}',                    # 5 字典推导
    'a5 = {f6(i) for i in y}',                       # 6 集合推导
    'a6 = (f7(i) for i in y)',                       # 7 生成器表达式
    'def g():',
    '    return f8()',                               # 9 函数体
    'a7 = lambda: f9()',                             # 10 lambda 体
    'try:',
    '    a8 = f10()',                                # 12 try 体
    'except ValueError as e:',
    '    a9 = f11(e)',                               # 14 except 体
    'finally:',
    '    a10 = f12()',                               # 16 finally
    'for i in y:',
    '    a11 = f13(i)',                              # 18 for 体
    'else:',
    '    a12 = f14()',                               # 20 for-else
    'while True:',
    '    a13 = f15()',                               # 23 while 体
    '    break',
    'if True:',
    '    a14 = f16()',                               # 27 if 体
    'elif False:',
    '    a15 = f17()',                               # 29 elif 体
    'else:',
    '    a16 = f18()',                               # 31 else 体
    'class C:',
    '    a17 = f19()',                               # 34 类体
    'a18 = f20(f21(1), k=f22(2))',                   # 35 嵌套调用 + 关键字
    'a19 = d["k"].f23()',                            # 36 下标后属性调用
    'a20 = (f24 or f25)()',                          # 37 括号表达式当被调者
    'a21 = [x for x in y if f26(x)]',                # 38 推导的 if
    'a22 = f27(*args, **kw)',                        # 39 星号参数
    'async def h():',
    '    a23 = await f28()',                          # 41 await
    'a24 = f29() if c else f30()',                   # 42 条件表达式
    'del a24',
    'assert f31()',                                  # 44 assert
    'a25 = f32() + f33()',                           # 45 二元
    'a26 = -f34()',                                  # 46 一元
]

src = 'y = []\nc = True\nargs = []\nkw = {}\nd = {}\n' + '\n'.join(CASES) + '\n'
PROBE.write_text(src, encoding='utf-8', newline='')
print('探针已写入：%s' % PROBE)


def truth_sinks(text):
    tree = ast.parse(text)
    return [[n.lineno, ast.unparse(n.func)] for n in ast.walk(tree) if isinstance(n, ast.Call)]


sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import purity_scan as p  # noqa: E402

t_sinks = truth_sinks(src)
TRUTH.write_text(json.dumps({'sinks': t_sinks}, ensure_ascii=False, indent=2) + '\n',
                 encoding='utf-8', newline='')

# Rust 侧：用同一套 IMPORT_SCAN（含 scripts/*.py），故它会看到探针文件
subprocess.run([str(EXE), 'purity-facts', '--root', str(ROOT), '--out', str(RUST)], check=True)
doc = json.loads(RUST.read_text(encoding='utf-8'))
key = 'scripts/zz_probe_ast_paths.py'
r = doc.get(key)
r_sinks = r['sinks'] if r else []

tset = {(a, b) for a, b in t_sinks}
rset = {(a, b) for a, b, _ in r_sinks}
print('\n真源 %d 条 / 本线 %d 条' % (len(t_sinks), len(r_sinks)))
print('\n本线**漏收**的（按行号）：')
for a, b in t_sinks:
    if (a, b) not in rset:
        print('   行 %-4d %s' % (a, b))
print('\n本线**多收**的：')
for a, b, _ in r_sinks:
    if (a, b) not in tset:
        print('   行 %-4d %s' % (a, b))

PROBE.unlink()
print('\n探针已删除')
