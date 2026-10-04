"""为 `workflow_policy` 生成分支级判据：构造逐分支踩的合成 `.github/` 语料，
用真源跑出 issues/warns/stats，再打印成 Rust 判据片段。

用法：python engine/rust/target/parity/gen_workflow_expected.py
"""
import json
from _rustlit import rs  # noqa: E402
import shutil
import sys
from pathlib import Path

ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import workflow_policy as wp  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'workflow-branches'
if FIX.exists():
    shutil.rmtree(FIX)
WF = FIX / '.github' / 'workflows'
WF.mkdir(parents=True)

SHA = 'a' * 40
SHA2 = 'b' * 40

WF_FILES = {
    # 一行踩齐：未钉 SHA / 缺版本 / 本地豁免 / 钉了带注释 / 钉了无注释
    'mixed.yml': (
        "name: mixed\n"
        "on: push\n"
        "permissions:\n  contents: read\n"
        "jobs:\n"
        "  j:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 5\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: actions/setup-python\n"
        "      - uses: ./local-action\n"
        "      - uses: actions/cache@%s # v3\n"
        "      - uses: actions/upload-artifact@%s\n" % (SHA, SHA2)
    ),
    # 缺显式 permissions + 缺 timeout
    'noperms.yml': (
        "name: noperms\n"
        "on: push\n"
        "jobs:\n"
        "  j:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: echo hi\n"
    ),
    # write-all
    'writeall.yml': (
        "name: wa\n"
        "on: push\n"
        "permissions: write-all\n"
        "jobs:\n"
        "  j:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 3\n"
        "    steps:\n"
        "      - run: echo hi\n"
    ),
    # 全绿
    'clean.yml': (
        "name: clean\n"
        "on: push\n"
        "permissions:\n  contents: read\n"
        "jobs:\n"
        "  j:\n"
        "    runs-on: ubuntu-latest\n"
        "    timeout-minutes: 10\n"
        "    steps:\n"
        "      - uses: actions/checkout@%s # v4\n" % SHA
    ),
    # 非 .yml/.yaml：必须被忽略
    'notes.txt': "uses: actions/checkout@v4\n",
}
for name, body in WF_FILES.items():
    (WF / name).write_text(body, encoding='utf-8')

REQS = {
    'requirements-a.txt': "pyyaml==6.0\n# 注释\n-r other.txt\nrequests\n",
    'requirements-b.txt': "numpy==1.26.0\n",
}
for name, body in REQS.items():
    (FIX / '.github' / name).write_text(body, encoding='utf-8')

issues, warns, stats = wp.scan(str(FIX))

print('// ===== 由 gen_workflow_expected.py 从真源生成，勿手改 =====')
print('const WANT_WF_ISSUES: [&str; %d] = [' % len(issues))
for x in issues:
    print('    %s,' % json.dumps(x, ensure_ascii=False))
print('];')
print('const WANT_WF_WARNS: [&str; %d] = [' % len(warns))
for x in warns:
    print('    %s,' % json.dumps(x, ensure_ascii=False))
print('];')
print('// stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))
print('const WF_FILES: [(&str, &str); %d] = [' % len(WF_FILES))
for name in sorted(WF_FILES):
    print('    (%s, %s),' % (rs(name), rs(WF_FILES[name])))
print('];')
print('const WF_REQS: [(&str, &str); %d] = [' % len(REQS))
for name in sorted(REQS):
    print('    (%s, %s),' % (rs(name), rs(REQS[name])))
print('];')
