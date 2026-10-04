"""算「从入口出发、模块内可达」的调用闭包 —— 用来**按消费者界定移植面**。

用法：python engine/rust/tools/trace_call_closure.py <模块名> <入口1,入口2,...>

例：python engine/rust/tools/trace_call_closure.py output_forms scan

输出：闭包内的函数清单 + 行数合计，以及**不在闭包内**的函数（即真源的写面/工具面，不移植）。
"""
import ast
import inspect
import pathlib
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
import importlib  # noqa: E402

mod_name = sys.argv[1]
entries = sys.argv[2].split(',')

mod = importlib.import_module('core.' + mod_name)
src_path = pathlib.Path(inspect.getsourcefile(mod))
tree = ast.parse(src_path.read_text(encoding='utf-8'))

# 收集模块级函数/类方法：名字 → 该函数体里出现的所有名字（简化的调用图）
funcs: dict = {}
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        names = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                names.add(sub.id)
            elif isinstance(sub, ast.Attribute):
                names.add(sub.attr)
        funcs[node.name] = (node, names)

# 模块级**分派表**：把 dict/list 字面量里出现的本模块函数名并进入口
# （只跟函数体内引用会低估移植面——间接调用同样要移植）。
for node in tree.body:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        value = node.value if isinstance(node, ast.AnnAssign) else node.value
        if value is None:
            continue
        for sub in ast.walk(value):
            if isinstance(sub, ast.Name) and sub.id in funcs:
                entries.append(sub.id)
    # 复合字面量类型注解里的 lambda 也覆盖：lambda 体里引用的名字
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        for sub in ast.walk(node.value):
            if isinstance(sub, ast.Lambda):
                for s2 in ast.walk(sub):
                    if isinstance(s2, ast.Name) and s2.id in funcs:
                        entries.append(s2.id)

# 从入口做可达闭包（只走本模块内**已定义**的函数名）
seen: set = set()
stack = list(entries)
while stack:
    cur = stack.pop()
    if cur in seen or cur not in funcs:
        continue
    seen.add(cur)
    for n in funcs[cur][1]:
        if n in funcs and n not in seen:
            stack.append(n)

total_lines = src_path.read_text(encoding='utf-8').count('\n') + 1
in_lines = 0
for name in sorted(seen):
    node = funcs[name][0]
    in_lines += (node.end_lineno or node.lineno) - node.lineno + 1

out_funcs = sorted(set(funcs) - seen)
print('模块 %s：共 %d 行 / %d 个函数' % (mod_name, total_lines, len(funcs)))
print('闭包内 %d 个函数，约 %d 行（占函数体行数）' % (len(seen), in_lines))
print('\n闭包内：')
for n in sorted(seen):
    node = funcs[n][0]
    print('  %-34s 行 %d-%d' % (n, node.lineno, node.end_lineno))
print('\n闭包外（不移植）：%d 个' % len(out_funcs))
for n in out_funcs:
    node = funcs[n][0]
    print('  %-34s 行 %d-%d' % (n, node.lineno, node.end_lineno))
