"""刷新 `mcp_tables.rs` 里的 `TOOL_NAMES` / `PROMPT_NAMES`（真源 `core.mcp_runtime` 的两张常量表）。

## ⚠️ 覆盖缺口

真源增删工具/提示面时，**只有 `mcp-package` 契约会因此变红**（它判「声明的 tools/prompts 必须与
运行时逐名一致」）。若该契约尚未移植，则没有判据会红——此时**必须重跑本脚本**。

用法：python engine/rust/tools/gen_mcp_tables.py
"""
import pathlib
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core.mcp_runtime import PROMPT_DEFS, TOOL_DEFS  # noqa: E402


def block(tag, const, names):
    out = ['// >>> GENERATED %s by tools/gen_mcp_tables.py（勿手改；重跑生成器覆盖本段）' % tag]
    if not names:
        out.append('pub const %s: [&str; 0] = [];' % const)
    else:
        out.append('pub const %s: [&str; %d] = [' % (const, len(names)))
        out += ['    "%s",' % n for n in names]
        out.append('];')
    out.append('// <<< GENERATED %s' % tag)
    return '\n'.join(out) + '\n'


tools = sorted(t['name'] for t in TOOL_DEFS)
prompts = sorted(p['name'] for p in PROMPT_DEFS)

p = ROOT / 'engine' / 'rust' / 'src' / 'mcp_tables.rs'
t = p.read_text(encoding='utf-8')
for tag, const, names in (('TOOL_NAMES', 'TOOL_NAMES', tools), ('PROMPT_NAMES', 'PROMPT_NAMES', prompts)):
    begin = '// >>> GENERATED %s' % tag
    end = '// <<< GENERATED %s\n' % tag
    a = t.index(begin)
    b = t.index(end, a) + len(end)
    t = t[:a] + block(tag, const, names) + t[b:]
p.write_text(t, encoding='utf-8', newline='')
print('已刷新：tools=%d %s / prompts=%d %s' % (len(tools), tools, len(prompts), prompts))
