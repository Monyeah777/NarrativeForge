"""AST 事实的差分对账：真源 `purity_scan._ast_facts` vs 本线 `nf-rs purity-facts`。

用法：python engine/rust/tools/gen_purity_facts_truth.py <仓库根> <输出.json>
"""
import ast
import json
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import purity_scan as p  # noqa: E402

rels = []
for pat in p.IMPORT_SCAN:
    rels.extend(sorted(x.relative_to(ROOT).as_posix() for x in ROOT.glob(pat)))
rels = sorted(set(rels))

doc = {}
for rel in rels:
    text = (ROOT / rel).read_text(encoding='utf-8')
    try:
        tree = ast.parse(text)
    except SyntaxError:
        doc[rel] = None
        continue
    raises, guarded, modules, sinks = p._ast_facts(tree)
    doc[rel] = {
        "raises": [[int(a), str(b)] for a, b in raises],
        "guarded": sorted(int(x) for x in guarded),
        "modules": [[str(a), int(b)] for a, b in modules],
        "sinks": [[int(a), str(b), bool(c)] for a, b, c in sinks],
    }

OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
               encoding='utf-8', newline='')
print('真源事实：%d 个文件' % len(doc))
