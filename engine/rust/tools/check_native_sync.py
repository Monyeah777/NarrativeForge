"""把「自算集必须与快线实际自算面一致」变成**机器可检的不变量**。

## 为什么需要它（实测事故，2026-10-04）

`verify_report.call` 是 **native 优先于 `--results`**。后果不对称：

- 自算集里**多列**一条 → 无害（喂进去的值被自算覆盖）；
- 自算集里**少列**一条 → **有害**：只要该条的分派将来断掉，就会静默回落到喂入值，
  **对账门照样全绿**。

实测踩到：对账门面 12 的自算集停在 11 条、同行常驻判据停在 19 条，都比实际自算面少一截；
而此前几次「同步」用 `String.Replace` 打在不存在的目标串上、**静默空转**。

## 怎么检（不新增 CLI 面）

给 `nf-rs verify-report` 喂一份**空** `--results`：凡是本线**没有**自算的判据，都会以
「…未移植且未喂入结果…」的 issue 报出来。于是：

    实际自算集 = 全部 28 条 − 报「未移植且未喂入」的那些

再把它与两处**手写清单**比对（对账门 `check_parity.ps1` 面 12、同行判据
`desktop/tests/test_rust_fastlane.py`）：不一致即退出码 1。

用法：python engine/rust/tools/check_native_sync.py [仓库根]
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
EXE = ROOT / 'engine' / 'rust' / 'target' / 'release' / 'nf-rs.exe'
GATE = ROOT / 'engine' / 'rust' / 'check_parity.ps1'
PEER = ROOT / 'desktop' / 'tests' / 'test_rust_fastlane.py'

UNPORTED_MARK = '未移植且未喂入结果'


def actual_native() -> set:
    """喂空 results → 报「未移植且未喂入」的就是非自算项。"""
    # ⚠️ 暂存**必须落在工作区内**：本机沙箱拒绝子进程写 `%TEMP%`（实测 os error 5）。
    # 落 `target/parity/`（已 gitignore）既在许可范围内，也不污染仓库——与单元判据同一处置。
    td = ROOT / 'engine' / 'rust' / 'target' / 'parity'
    td.mkdir(parents=True, exist_ok=True)
    empty = td / 'native_sync_empty.json'
    empty.write_text('{}', encoding='utf-8', newline='')
    out = td / 'native_sync_out.json'
    out.unlink(missing_ok=True)
    proc = subprocess.run(
        [str(EXE), 'verify-report', '--root', str(ROOT),
         '--results', str(empty), '--json', '--out', str(out)],
        capture_output=True, check=False,
    )
    if not out.is_file():
        print(proc.stderr.decode('utf-8', 'replace')[:400])
        raise SystemExit('nf-rs 未产出报告')
    doc = json.loads(out.read_text(encoding='utf-8'))
    native = set()
    for it in doc['items']:
        # 渲染后的条目里 issues 是**计数**，消息样本在 sample（实测形状）
        if not any(UNPORTED_MARK in i for i in it.get('sample') or []):
            native.add(it['id'])
    return native


def declared_in_gate() -> set:
    t = GATE.read_text(encoding='utf-8')
    m = re.search(r'NATIVE = \{([^}]*)\}', t)
    if not m:
        raise SystemExit('对账门里找不到 NATIVE = {...}')
    return set(re.findall(r"'([^']+)'", m.group(1)))


def declared_in_peer() -> set:
    t = PEER.read_text(encoding='utf-8')
    m = re.search(r'^\s*native = \{([^}]*)\}', t, re.M)
    if not m:
        raise SystemExit('同行判据里找不到 native = {...}')
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def main() -> int:
    if not EXE.is_file():
        print('先构建：cargo build --release --manifest-path engine/rust/Cargo.toml')
        return 2
    actual = actual_native()
    gate = declared_in_gate()
    peer = declared_in_peer()
    print('  快线实际自算：%d 条' % len(actual))
    print('  对账门声明  ：%d 条' % len(gate))
    print('  同行判据声明：%d 条' % len(peer))
    bad = 0
    for name, got in (('对账门 check_parity.ps1 面 12', gate), ('同行 test_rust_fastlane.py', peer)):
        miss = sorted(actual - got)      # 少列 → 危险（分派断掉不会红）
        extra = sorted(got - actual)     # 多列 → 无害但误导
        if miss:
            print('  [FAIL] %s 少列（危险：该条分派断掉也不会红）：%s' % (name, miss))
            bad += 1
        if extra:
            print('  [FAIL] %s 多列（喂入值会被自算覆盖，属误导）：%s' % (name, extra))
            bad += 1
        if not miss and not extra:
            print('  [PASS] %s 与实际自算面一致' % name)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
