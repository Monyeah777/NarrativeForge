"""`code_metrics.scan` 的差分对账：真源 vs 本线 `nf-rs code-metrics`。

用法：python engine/rust/tools/gen_code_metrics_truth.py <仓库根> <输出.json>
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import code_metrics as cm  # noqa: E402

issues, warns, stats = cm.scan(str(ROOT))
OUT.write_bytes(
    (json.dumps({"issues": issues, "warns": warns, "stats": stats},
                ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode('utf-8'))
print('真源 code_metrics：issues=%d warns=%d stats=%s'
      % (len(issues), len(warns), json.dumps(stats, ensure_ascii=False, sort_keys=True)))
