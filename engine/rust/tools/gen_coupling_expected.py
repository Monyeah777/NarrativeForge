"""为 `coupling_metrics` 生成分支级期望：构造一个逐形态踩 import 写法的合成 core 目录，
用真源（AST 版）跑出 deps / metrics / cycles / sdp / scan，再打印成 Rust 判据片段。

用法：python engine/rust/target/parity/gen_coupling_expected.py
"""
import json
from _rustlit import rs  # noqa: E402
import shutil
import sys
from pathlib import Path

ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import coupling_metrics as cm  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'coupling-branches'
CORE = FIX / 'desktop' / 'src' / 'core'
if FIX.exists():
    shutil.rmtree(FIX)
CORE.mkdir(parents=True)

# 每个模块踩一种 import 形态；`__init__` 必须被忽略
SRC = {
    'aa': "import core.bb\nfrom core import cc, dd\n",                 # 普通 / 多别名
    'bb': "from core.aa import x\n",                                   # 点号模块 → 首段
    'cc': "from . import ee\n",                                        # 相对无模块 → 名单
    'dd': "from .core import ff\n",                                    # 相对 core → 走第一支
    'ee': "from ..pkg.sub import gg\n",                                # 相对带模块 → 首段
    'ff': "from core import (hh,\n    ii)\n",                          # 括号多行
    'gg': 'import core.hh as hh\n',                                    # 别名
    'hh': 'S = "from core import zzz"\n# import core.yyy\n',           # 字符串/注释里的假 import
    'ii': "import os\nimport json\n",                                  # 无同包依赖
    '__init__': "from core.aa import x\n",                             # 必须被忽略
}
for name, body in SRC.items():
    (CORE / ('%s.py' % name)).write_text(body, encoding='utf-8')

deps, metrics = cm.graph(str(FIX))
cyc = cm.cycles(deps)
sdp = cm.sdp_violations(deps, metrics)
issues, warns, stats = cm.scan(str(FIX))

print('// ===== 由 gen_coupling_expected.py 从真源生成，勿手改 =====')
print('const WANT_DEPS: [(&str, &[&str]); %d] = [' % len(deps))
for m in sorted(deps):
    print('    (%s, &[%s]),' % (rs(m), ', '.join(rs(d) for d in sorted(deps[m]))))
print('];')
print('const WANT_METRICS: [(&str, i64, i64, f64); %d] = [' % len(metrics))
for m in sorted(metrics):
    print('    (%s, %d, %d, %s),' % (rs(m), metrics[m]['ca'], metrics[m]['ce'], repr(metrics[m]['i'])))
print('];')
print('const WANT_CYCLES: [&[&str]; %d] = [' % len(cyc))
for c in cyc:
    print('    &[%s],' % ', '.join(rs(x) for x in c))
print('];')
print('const WANT_SDP: [(&str, &str); %d] = [' % len(sdp))
for a, b in sdp:
    print('    (%s, %s),' % (rs(a), rs(b)))
print('];')
print('// issues = %d' % len(issues))
for x in issues:
    print('//   ! %s' % x)
print('// warns = %d' % len(warns))
for x in warns:
    print('//   ~ %s' % x)
print('// stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))
print('// 源文件内容（Rust 侧照此重建）:')
print('const SRC: [(&str, &str); %d] = [' % len(SRC))
for name in sorted(SRC):
    print('    (%s, %s),' % (rs(name), rs(SRC[name])))
print('];')
