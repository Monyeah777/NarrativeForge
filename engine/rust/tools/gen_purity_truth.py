"""`purity_scan.scan` 的差分对账：真源 vs 本线 `nf-rs purity-scan`。

用法：python engine/rust/tools/gen_purity_truth.py <仓库根> <输出.json>
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import purity_scan as p  # noqa: E402

issues, stats = p.scan(str(ROOT))
OUT.write_bytes(
    (json.dumps({"issues": issues, "stats": stats}, ensure_ascii=False,
                sort_keys=True, indent=2) + "\n").encode('utf-8'))
print('真源 purity_scan：issues=%d' % len(issues))
