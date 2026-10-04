"""普查 `src/*.rs` 里的 `pub` 项**是否真有读者**——揪出"没人核的代码面"。

## 为什么要它

本线的纪律是「**不写没人核的代码**」：移植面按消费者界定（`machine_contract` 只移植 id 那条路径、
`handover`/`state_front`/`postmortem`/`endpoint` 不落 `warns`……）。
但纪律靠人记就会漏，故做成普查：某个 `pub fn` / `pub const` / `pub struct` 若**除定义处外无人引用**
（含测试），它要么是死代码，要么是"写了但没人验"——两种都该被看见。

## 判读

- `[dead]`：全仓（含测试）零引用 → 应删，或补判据。
- `[test-only]`：只在 `#[cfg(test)]` 之外无引用、但测试里有 → 需在注释里写明理由
  （例如 `IoTypesScan.warns`：契约不消费，但含实质判据，靠分支级判据覆盖）。
- 其余为「有读者」，正常。

用法：python engine/rust/tools/audit_pub_readers.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
SRC = ROOT / 'engine' / 'rust' / 'src'

DEF = re.compile(r'^\s*pub (?:fn|const|struct|enum) ([A-Za-z_][A-Za-z0-9_]*)', re.M)

files = {p: p.read_text(encoding='utf-8') for p in sorted(SRC.glob('*.rs'))}

#: 测试区起点 = `#[cfg(test)]` 后紧邻 `mod X {`（**块**）。注意 `#[cfg(test)] mod testutil;`
#: 是**文件模块**、不是块——旧判据没区分，把 main.rs 里它之后的整片都当测试，
#: 于是所有真读者都被误报成 `[test-only]`（实测踩到）。
_TEST_BLOCK = re.compile(r'#\[cfg\(test\)\]\s*\n\s*mod \w+ \{')


def test_region_start(text: str) -> int:
    m = _TEST_BLOCK.search(text)
    return m.start() if m else len(text)


def line_offset(text: str, lineno: int) -> int:
    return sum(len(x) + 1 for x in text.splitlines()[:lineno])
dead, test_only, ok = [], [], 0

for p, text in files.items():
    for m in DEF.finditer(text):
        name = m.group(1)
        refs = 0
        refs_in_test = 0
        for q, qtext in files.items():
            for i, ln in enumerate(qtext.splitlines()):
                if not re.search(r'\b' + re.escape(name) + r'\b', ln):
                    continue
                if q is p and i == text[:m.start()].count('\n'):
                    continue                     # 定义那一行
                refs += 1
                if line_offset(qtext, i) >= test_region_start(qtext):
                    refs_in_test += 1
        if refs == 0:
            dead.append('%s::%s' % (p.name, name))
        elif refs == refs_in_test:
            test_only.append('%s::%s' % (p.name, name))
        else:
            ok += 1

print('  有读者      : %d' % ok)
print('  仅测试引用  : %d' % len(test_only))
for x in test_only:
    print('    [test-only] %s' % x)
print('  全仓零引用  : %d' % len(dead))
for x in dead:
    print('    [dead] %s' % x)

sys.exit(1 if dead else 0)
