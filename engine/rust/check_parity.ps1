# NF Rust 只读快线 —— 逐字节对账门（engine/rust/）
#
# 纪律（2026-10-03 实测教训）：本仓常有并发会话改动语料，同一轮内回执根/自述数字都会变。
# 因此对账必须**两侧实时重算、背靠背比对**——拿在盘旧产物（如 protocol/RECEIPTS.json、
# protocol/repo_stats.json）当基准会假红。本脚本每次都用 Python 真源现场重算，再与 Rust 侧现场比对。
#
# 覆盖面：
#   ① receipts —— nf-rs receipts build  vs  真源 receipts.write_scope 的落盘字节
#   ② stats    —— nf-rs stats --json    vs  `nf stats --json` 的输出字节
#
# 用法：pwsh -NoProfile -File engine/rust/check_parity.ps1 [-Root <仓库根>] [-Scope protocol]
# 退出码：0 = 全部逐字节一致；1 = 有不一致或前置失败。

param(
    [string]$Root = '',
    [string]$Scope = 'protocol'
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
}
$Root = (Resolve-Path $Root).Path
$RustDir = $PSScriptRoot
$Parity = Join-Path $RustDir 'target\parity'
New-Item -ItemType Directory -Force -Path $Parity | Out-Null

$env:PYTHONIOENCODING = 'utf-8'
$script:Failed = 0

# ---- 工具链定位（不假设 PATH 已注入）
$cargo = Join-Path $env:USERPROFILE '.cargo\bin\cargo.exe'
if (-not (Test-Path $cargo)) { $cargo = 'cargo' }


Write-Host '== 1/3 构建 Rust 侧'
& $cargo build --release --manifest-path (Join-Path $RustDir 'Cargo.toml')
if ($LASTEXITCODE -ne 0) { Write-Host '[FAIL] cargo build 失败'; exit 1 }

$PythonExe = 'python'
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $PythonExe = 'py' }
$exe = Join-Path $RustDir 'target\release\nf-rs.exe'
if (-not (Test-Path $exe)) { $exe = Join-Path $RustDir 'target\release\nf-rs' }
if (-not (Test-Path $exe)) { Write-Host '[FAIL] 未产出 nf-rs 可执行文件'; exit 1 }

# ---- 2. Python 真源现场重算（两个面各一份）
Write-Host '== 2/3 生成 Python 真源基准'
$genReceipts = Join-Path $Parity 'gen_truth_receipts.py'
Set-Content -Path $genReceipts -Encoding UTF8 -Value @'
import json, sys, hashlib
from pathlib import Path
root = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2])
scope = sys.argv[3] if len(sys.argv) > 3 else "protocol"
sys.path.insert(0, str(root / "desktop" / "src"))
from core import receipts as rc
doc = rc.build_scope(str(root), scope=scope)
raw = (json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
out.write_bytes(raw)
print("TRUTH receipts: count=%d bytes=%d sha256=%s" % (doc["count"], len(raw), hashlib.sha256(raw).hexdigest()))
'@

$genStats = Join-Path $Parity 'gen_truth_stats.py'
Set-Content -Path $genStats -Encoding UTF8 -Value @'
import json, sys, hashlib
from pathlib import Path
root = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2])
sys.path.insert(0, str(root / "desktop" / "src"))
from core import repo_stats as rs
issues, stats = rs.check(str(root))
raw = (json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
out.write_bytes(raw)
print("TRUTH stats: bytes=%d sha256=%s issues=%d" % (len(raw), hashlib.sha256(raw).hexdigest(), len(issues)))
'@

# ---- 3. 逐面背靠背比对
function Compare-Face {
    param([string]$Name, [string]$TruthPy, [string]$Truth, [string]$Rust, [scriptblock]$RustRun)

    Write-Host ("== " + $Name + " ==")
    & python $TruthPy $Root $Truth | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] Python 真源重算失败'; $script:Failed++; return }

    & $RustRun | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host ("  [FAIL] nf-rs 退出码 " + $LASTEXITCODE); $script:Failed++; return }

    $hT = (Get-FileHash $Truth -Algorithm SHA256).Hash.ToLower()
    $hR = (Get-FileHash $Rust  -Algorithm SHA256).Hash.ToLower()
    Write-Host ("  Python : {0} bytes  {1}" -f (Get-Item $Truth).Length, $hT)
    Write-Host ("  Rust   : {0} bytes  {1}" -f (Get-Item $Rust).Length,  $hR)
    if ($hT -eq $hR) {
        Write-Host '  [PASS] 逐字节一致'
    } else {
        Write-Host '  [FAIL] 不一致'
        $a = [IO.File]::ReadAllBytes($Rust); $b = [IO.File]::ReadAllBytes($Truth)
        $n = [Math]::Min($a.Length, $b.Length); $shown = 0
        for ($i = 0; $i -lt $n -and $shown -lt 5; $i++) {
            if ($a[$i] -ne $b[$i]) {
                Write-Host ("    差异 offset {0} : rust=0x{1:X2} py=0x{2:X2}" -f $i, $a[$i], $b[$i]); $shown++
            }
        }
        $script:Failed++
    }
}

$truthReceipts = Join-Path $Parity 'truth_receipts.json'
$rustReceipts  = Join-Path $Parity 'rust_receipts.json'
Compare-Face -Name '面 1 · receipts（协议层回执单根）' -TruthPy $genReceipts -Truth $truthReceipts -Rust $rustReceipts -RustRun {
    & $exe receipts build --root $Root --scope $Scope --out $rustReceipts
}

$truthStats = Join-Path $Parity 'truth_stats.json'
$rustStats  = Join-Path $Parity 'rust_stats.json'
Compare-Face -Name '面 2 · stats（自述数字实算）' -TruthPy $genStats -Truth $truthStats -Rust $rustStats -RustRun {
    & $exe stats --root $Root --json --out $rustStats
}

# ---- 面 3：conformance 封缄内核（裁决行 → 防篡改报告）
# 输入 = 真源 run() 的契约行**剥掉 digest**；期望输出 = 真源 write() 的落盘字节。
Write-Host '== 面 3 · conformance 封缄内核 =='
$genConf = Join-Path $Parity 'gen_truth_conformance.py'
Set-Content -Path $genConf -Encoding UTF8 -Value @'
import json, sys, hashlib
from pathlib import Path
root = Path(sys.argv[1]).resolve(); out_dir = Path(sys.argv[2])
sys.path.insert(0, str(root / "desktop" / "src"))
from core import conformance_report as cr
doc = cr.run(str(root))
rows = [{"id": r["id"], "ok": r["ok"], "detail": r["detail"], "description": r["description"]}
        for r in doc["contracts"]]
(out_dir / "truth_rows.json").write_bytes(
    (json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
raw = (json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
out = Path(sys.argv[3]); out.write_bytes(raw)
print("TRUTH conformance: total=%d passed=%d root=%s bytes=%d sha256=%s"
      % (doc["total"], doc["passed"], doc["root"][:16], len(raw), hashlib.sha256(raw).hexdigest()))
'@
$truthConf = Join-Path $Parity 'truth_doc.json'
$rustConf  = Join-Path $Parity 'rust_doc.json'
$rowsConf  = Join-Path $Parity 'truth_rows.json'
& python $genConf $Root $Parity $truthConf | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] Python 真源重算失败'; $script:Failed++ }
else {
    & $exe conformance seal --in $rowsConf --out $rustConf | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host ("  [FAIL] nf-rs 退出码 " + $LASTEXITCODE); $script:Failed++ }
    else {
        $hT = (Get-FileHash $truthConf -Algorithm SHA256).Hash.ToLower()
        $hR = (Get-FileHash $rustConf  -Algorithm SHA256).Hash.ToLower()
        Write-Host ("  Python : {0} bytes  {1}" -f (Get-Item $truthConf).Length, $hT)
        Write-Host ("  Rust   : {0} bytes  {1}" -f (Get-Item $rustConf).Length,  $hR)
        if ($hT -eq $hR) { Write-Host '  [PASS] 逐字节一致' }
        else { Write-Host '  [FAIL] 不一致'; $script:Failed++ }
    }
}

# ---- 面 4：conformance 差分核对（喂真源自带摘要的对象，本线须逐条复算一致）
Write-Host '== 面 4 · conformance 差分核对（真源摘要 vs 本线重算） =='
& $exe conformance seal --in $truthConf --out (Join-Path $Parity 'rust_doc_check.json')
if ($LASTEXITCODE -ne 0) {
    Write-Host ("  [FAIL] 真源摘要与本线重算不一致，退出码 " + $LASTEXITCODE); $script:Failed++
} else { Write-Host '  [PASS] 27 条契约摘要逐条重算一致' }

# ---- 面 5：逐条已移植契约（id 清单由 nf-rs 自描述，脚本不硬编码）
Write-Host '== 面 5 · conformance 已移植契约逐条对账 =='
$ported = & $exe conformance list
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] 取不到已移植契约清单'; $script:Failed++ }
elseif (-not $ported) { Write-Host '  [i] 尚无已移植契约（跳过）' }
else {
    $rowGen = Join-Path $Parity 'gen_row.py'
    Set-Content -Path $rowGen -Encoding UTF8 -Value @'
import json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]); cid = sys.argv[3]
sys.path.insert(0, str(root / "desktop" / "src"))
from core import conformance_report as cr
doc = cr.run(str(root))
row = next(r for r in doc["contracts"] if r["id"] == cid)
out.write_bytes((json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
print("TRUTH row %s: ok=%s digest=%s" % (cid, row["ok"], row["digest"][:16]))
'@
    foreach ($cid in $ported) {
        $cid = "$cid".Trim()
        if (-not $cid) { continue }
        $pyRow = Join-Path $Parity ("row_py_" + $cid + ".json")
        $rsRow = Join-Path $Parity ("row_rust_" + $cid + ".json")
        & python $rowGen $Root $pyRow $cid | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host ("  [FAIL] 真源取行失败：" + $cid); $script:Failed++; continue }
        & $exe conformance contract $cid --root $Root --out $rsRow | Out-Null
        # ⚠️ **不能假设「已移植契约都该绿」**：真源自己就会判定某些契约 ok=false
        # （实测 2026-10-03：`audit` 因并发会话改了 verify.sh 而正确报 FAIL）。
        # 正确判据是「本线退出码 == 真源 ok 的映射」：ok=true → 0，ok=false → 1。
        # 早先写成「非 0 即失败」，既误报、又等于**从没核过 false 这一侧的退出码语义**。
        $rsExit = $LASTEXITCODE
        $pyOk = (Get-Content $pyRow -Raw | ConvertFrom-Json).ok
        $wantExit = if ($pyOk -eq $false) { 1 } else { 0 }
        if ($rsExit -ne $wantExit) {
            Write-Host ("  [FAIL] " + $cid + " 退出码 " + $rsExit + " != 真源 ok=" + $pyOk + " 应有的 " + $wantExit)
            $script:Failed++
            continue
        }
        $hT = (Get-FileHash $pyRow -Algorithm SHA256).Hash.ToLower()
        $hR = (Get-FileHash $rsRow -Algorithm SHA256).Hash.ToLower()
        if ($hT -eq $hR) { Write-Host ("  [PASS] " + $cid + " 契约行逐字节一致") }
        else { Write-Host ("  [FAIL] " + $cid + " 契约行不一致"); $script:Failed++ }
    }
}

# ---- 面 6：layers 阶梯体检（整面）
Write-Host '== 面 6 · layers 阶梯体检（--verify --json） =='
$genLayers = Join-Path $Parity 'gen_truth_layers.py'
Set-Content -Path $genLayers -Encoding UTF8 -Value @'
import json, sys, hashlib
from pathlib import Path
root = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2])
sys.path.insert(0, str(root / "desktop" / "src"))
from core import layer_model as lm
issues, stats = lm.scan(str(root))
payload = {"kind": "layers-verify", "ok": not issues, "issues": issues, "stats": stats}
raw = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
out.write_bytes(raw)
print("TRUTH layers: ok=%s issues=%d bytes=%d sha256=%s"
      % (not issues, len(issues), len(raw), hashlib.sha256(raw).hexdigest()))
'@
$truthLayers = Join-Path $Parity 'truth_layers.json'
$rustLayers  = Join-Path $Parity 'rust_layers.json'
& python $genLayers $Root $truthLayers | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] Python 真源重算失败'; $script:Failed++ }
else {
    & $exe layers --root $Root --verify --json --out $rustLayers | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host ("  [FAIL] nf-rs 退出码 " + $LASTEXITCODE); $script:Failed++ }
    else {
        $hT = (Get-FileHash $truthLayers -Algorithm SHA256).Hash.ToLower()
        $hR = (Get-FileHash $rustLayers  -Algorithm SHA256).Hash.ToLower()
        Write-Host ("  Python : {0} bytes  {1}" -f (Get-Item $truthLayers).Length, $hT)
        Write-Host ("  Rust   : {0} bytes  {1}" -f (Get-Item $rustLayers).Length,  $hR)
        if ($hT -eq $hR) { Write-Host '  [PASS] 逐字节一致' }
        else { Write-Host '  [FAIL] 不一致'; $script:Failed++ }
    }
}

# ---- 面 7：浮点 repr 口径（穷举式：位模式 → repr，逐值比对真源）
Write-Host '== 面 7 · 浮点 repr 口径（CPython float.__repr__） =='
$genFl = Join-Path $Parity 'gen_truth_floats.py'
Set-Content -Path $genFl -Encoding UTF8 -Value @'
import struct, random, sys
from pathlib import Path
d = Path(sys.argv[1])
vals = [0.0, -0.0, 1.0, -1.0, 0.5, 1.5, 100.0, 0.1, 0.2, 1/3, 2/3, 1e15, 1e16, 1e17,
        1e-4, 1e-5, 1e-6, 1e100, 1e-100, 1e308, 5e-324, 2.5e-10, 1.23e20, 0.0001234,
        9999999999999998.0, 123456789012345.0, 1.7976931348623157e308,
        float('inf'), float('-inf')]
bits = [struct.unpack('<Q', struct.pack('<d', v))[0] for v in vals]
rng = random.Random(20261003)
while len(bits) < 20000:
    b = rng.getrandbits(64)
    if struct.unpack('<d', struct.pack('<Q', b))[0] != struct.unpack('<d', struct.pack('<Q', b))[0]:
        continue                      # 跳过 NaN（repr 不保号，语义另论）
    bits.append(b)
(d / 'bits.txt').write_text('\n'.join('%016x' % b for b in bits) + '\n', encoding='utf-8')
(d / 'reprs_py.txt').write_text(
    '\n'.join(repr(struct.unpack('<d', struct.pack('<Q', b))[0]) for b in bits) + '\n', encoding='utf-8')
print("TRUTH floats: %d 例位模式 + repr" % len(bits))
'@
& python $genFl $Parity | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] 真源基准生成失败'; $script:Failed++ }
else {
    $rustReprs = Join-Path $Parity 'reprs_rust.txt'
    & $exe pyval reprf --in (Join-Path $Parity 'bits.txt') --out $rustReprs | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host ("  [FAIL] nf-rs 退出码 " + $LASTEXITCODE); $script:Failed++ }
    else {
        $py = Get-Content (Join-Path $Parity 'reprs_py.txt')
        $rs = Get-Content $rustReprs
        $bad = 0
        if ($py.Count -ne $rs.Count) { Write-Host "  [FAIL] 行数不等：py=$($py.Count) rust=$($rs.Count)"; $script:Failed++ }
        else {
            for ($i = 0; $i -lt $py.Count; $i++) {
                if ($py[$i] -ne $rs[$i]) {
                    if ($bad -lt 5) { Write-Host ("    行 {0}：py='{1}' rust='{2}'" -f $i, $py[$i], $rs[$i]) }
                    $bad++
                }
            }
            if ($bad -eq 0) { Write-Host ("  [PASS] {0} 例浮点 repr 逐值一致" -f $py.Count) }
            else { Write-Host ("  [FAIL] {0} 例不一致" -f $bad); $script:Failed++ }
        }
    }
}

# ---- 面 8 · asset_density 扫描（score 的信号源之一）
Write-Host '== 面 8 · asset_density 扫描（键密度：文件名令牌 ∪ 正文头三路） =='
$densityPy = Join-Path $Parity 'density_py.json'
$densityRs = Join-Path $Parity 'density_rust.json'
$root = $Root
& $PythonExe -c @"
import sys, json
sys.path.insert(0, 'desktop/src')
from core import asset_density as ad
issues, stats = ad.scan(r'$root')
open(r'$densityPy','w',encoding='utf-8',newline='').write(
    json.dumps({'issues': issues, 'stats': stats}, ensure_ascii=False, indent=2, sort_keys=True) + chr(10))
"@
& $exe density --root $Root --json --out $densityRs
if ((Get-FileHash $densityPy).Hash -ne (Get-FileHash $densityRs).Hash) {
    Write-Host '  [FAIL] 逐字节不一致'; $script:Failed++
} else { Write-Host '  [PASS] 逐字节一致' }

# ---- 面 9 · score 内核（基线相对回归评分 + compare）
Write-Host '== 面 9 · score 内核（加权信号 + 容差/例外判定） =='
$scoreSignals = Join-Path $Parity 'score_signals.json'
$scorePy = Join-Path $Parity 'score_py.json'
$scoreRs = Join-Path $Parity 'score_rust.json'
& $PythonExe -c @"
import sys, os, json, importlib
sys.path.insert(0, 'desktop/src')
root = r'$root'
# 尚未移植的扫描器：把**计数**喂给 Rust（缺键 = 扫描器不可用，真源 _count 的哨兵语义）。其余已自主算出，故不喂。
# 2026-10-04：`purity_clean` 已改自算（本线跑 `purity_scan.scan`），故只剩 `depth_clean` 要喂。
sig = {}
for name, mod in (('depth_clean','quality_depth_scan'),):
    m = importlib.import_module('core.' + mod)
    r = m.scan(root)
    sig[name] = len(r[0] if isinstance(r, tuple) else r)
open(r'$scoreSignals','w',encoding='utf-8',newline='').write(json.dumps(sig))

from core import regression_score as rs
cur = rs.evaluate(root)
bpath = os.path.join(root, 'protocol', 'score_baseline.json')
base = json.load(open(bpath, encoding='utf-8')) if os.path.isfile(bpath) else {'schema': rs.SCHEMA}
out = rs.compare(cur, base, tolerance=0.0, exceptions=[])
open(r'$scorePy','w',encoding='utf-8',newline='').write(
    json.dumps({'kind':'score','current':cur,'compare':out}, ensure_ascii=False, indent=2, sort_keys=True) + chr(10))
"@
& $exe score --root $Root --signals $scoreSignals --json --out $scoreRs
if ((Get-FileHash $scorePy).Hash -ne (Get-FileHash $scoreRs).Hash) {
    Write-Host '  [FAIL] 逐字节不一致'; $script:Failed++
} else { Write-Host '  [PASS] 逐字节一致' }

# ---- 面 14 · purity_scan 扫描（R1–R7；`purity` 判据 / `purity-clean` 契约 / score 信号源）
Write-Host '== 面 14 · purity_scan 扫描（R1–R7 纯度体检 + 分层阶梯） =='
$purPy = Join-Path $Parity 'purity_py.json'
$purRs = Join-Path $Parity 'purity_rs.json'
& $PythonExe (Join-Path $Root 'engine/rust/tools/gen_purity_truth.py') $Root $purPy | Out-Null
& $exe purity-scan --root $Root --out $purRs
if ((Get-FileHash $purPy).Hash -ne (Get-FileHash $purRs).Hash) {
    Write-Host '  [FAIL] 逐字节不一致（issues + stats）'; $script:Failed++
} else { Write-Host '  [PASS] 逐字节一致（issues + stats，含 R7 分层阶梯）' }

# ---- 面 15 · code_metrics 扫描（规模/复杂度棘轮；`code_metrics` 判据面）
Write-Host '== 面 15 · code_metrics 扫描（规模/复杂度上限，含圈复杂度） =='
$cmPy = Join-Path $Parity 'cm_py.json'
$cmRs = Join-Path $Parity 'cm_rs.json'
& $PythonExe (Join-Path $Root 'engine/rust/tools/gen_code_metrics_truth.py') $Root $cmPy | Out-Null
& $exe code-metrics --root $Root --out $cmRs
if ((Get-FileHash $cmPy).Hash -ne (Get-FileHash $cmRs).Hash) {
    Write-Host '  [FAIL] 逐字节不一致（issues + warns + stats）'; $script:Failed++
} else { Write-Host '  [PASS] 逐字节一致（issues + warns + stats）' }

# ---- 面 10 · schema_lint（check28 协议件子集校验）
Write-Host '== 面 10 · schema_lint（JSON-Schema 子集校验 + 五张面） =='
$slPy = Join-Path $Parity 'schemalint_py.json'
$slRs = Join-Path $Parity 'schemalint_rust.json'
& $PythonExe -c @"
import sys, json
sys.path.insert(0, 'desktop/src')
from core import schema_lint as sl
issues, stats = sl.scan(r'$Root')
open(r'$slPy','w',encoding='utf-8',newline='').write(
    json.dumps({'issues': issues, 'stats': stats}, ensure_ascii=False, indent=2, sort_keys=True) + chr(10))
"@
& $exe schema-lint --root $Root --json --out $slRs
if ((Get-FileHash $slPy).Hash -ne (Get-FileHash $slRs).Hash) {
    Write-Host '  [FAIL] 逐字节不一致'; $script:Failed++
} else { Write-Host '  [PASS] 逐字节一致' }

# ---- 面 11 · 子集校验器差分（真仓库 check28 全绿 ⇒ 光靠对账抓不到校验器 bug）
Write-Host '== 面 11 · 子集校验器差分（合成 instance×schema 逐条比对消息） =='
$diffOut = & $PythonExe -c @"
import sys, json, subprocess, os
sys.path.insert(0, 'desktop/src')
from core import schema_lint as sl
root = r'$Root'; par = r'$Parity'
exe = os.path.join(root, 'engine', 'rust', 'target', 'release', 'nf-rs.exe')
if not os.path.isfile(exe): exe = exe[:-4]
schemas = [
  {'type':'object','required':['a'],'properties':{'a':{'type':'string'}},'additionalProperties':False},
  {'type':'object','properties':{'n':{'type':'integer','minimum':3}},'propertyNames':{'type':'string','pattern':'^[a-z]+$'}},
  {'type':'object','properties':{'f':{'type':'number','minimum':0.5}}},
  {'type':'array','minItems':2,'maxItems':3,'items':{'type':'string','pattern':'^[A-Z]+$'}},
  {'type':'string','enum':['a','b'],'minLength':1},
  {'type':'string','enum':[1,2]},
  {'type':'number','minimum':0},
  {'type':'boolean'},
  {'type':'null'},
  {'type':'object','properties':{'x':{'type':'array','items':{'type':'object','required':['k'],'properties':{'k':{'type':'string'}}}}}},
]
insts = [{}, {'a':'x'}, {'a':'x','b':1}, {'a':1}, {'n':2}, {'n':5}, {'N':1}, {'n':'x'},
  {'f':0.4}, {'f':0.6}, [], ['A'], ['A','B'], ['A','B','C','D'], ['a'], [1], 'a', 'z', '', 0, 1, -1, 1.5,
  True, False, None, {'x':[{'k':'v'},{'k':1},{}]}, {'x':'nope'}]
sp = os.path.join(par, '_sv_s.json'); ip = os.path.join(par, '_sv_i.json')
n = bad = 0
for si, sch in enumerate(schemas):
    for inst in insts:
        open(sp,'w',encoding='utf-8').write(json.dumps(sch))
        open(ip,'w',encoding='utf-8').write(json.dumps(inst))
        py = sl.subset_validate(inst, sch, 'instance')
        r = subprocess.run([exe,'schema-validate','--schema',sp,'--instance',ip], capture_output=True)
        rs = json.loads(r.stdout.decode('utf-8'))['messages'] if r.returncode == 0 else ['<crash>']
        n += 1
        if py != rs:
            bad += 1
            if bad <= 3: print('    差异 schema#%d inst=%r' % (si, inst)); print('      py  : %r' % (py,)); print('      rust: %r' % (rs,))
print('%d %d' % (n, bad))
"@
$diffOut | Where-Object { $_ -notmatch '^\d+ \d+$' } | ForEach-Object { Write-Host $_ }
$last = ($diffOut | Select-Object -Last 1) -split ' '
if ($last.Count -eq 2 -and $last[1] -eq '0') {
    Write-Host ("  [PASS] {0} 例差分逐条一致" -f $last[0])
} else {
    Write-Host ("  [FAIL] 差分不一致"); $script:Failed++
}

# ---- 面 12 · verify_report（28 条判据聚合 + 声明面 + root_digest + 渲染）
Write-Host '== 面 12 · verify_report 内核（聚合/归一/摘要/渲染） =='
$vrResults = Join-Path $Parity 'vr_results.json'
$vrPy = Join-Path $Parity 'vr_py.json'
$vrRs = Join-Path $Parity 'vr_rust.json'
& $PythonExe -c @"
import sys, json
sys.path.insert(0, 'desktop/src')
from core import verify_report as vr
root = r'$Root'
# 本线已自主算出这 4 条；其余喂入子结果（未移植的扫描器）
NATIVE = {'schema', 'doc_markers', 'baseline', 'self_stats', 'payload', 'assets_ledger', 'instruction', 'key_naming', 'intake', 'library', 'library_projection', 'rating', 'audit', 'workflow_policy', 'judgement_coverage', 'license', 'coupling', 'contract', 'knowledge', 'conformance', 'receipts', 'drill_fidelity', 'purity', 'conformance_report', 'code_metrics', 'asset_contract'}
res = {}
for spec in vr.SPECS:
    if spec[0] in NATIVE: continue
    status, issues, warns, stats = vr._call(spec, root)
    e = {'issues': issues, 'warns': warns, 'stats': stats}
    if status == 'error': e['status'] = 'error'
    res[spec[0]] = e
open(r'$vrResults','w',encoding='utf-8',newline='').write(json.dumps(res, ensure_ascii=False))
open(r'$vrPy','w',encoding='utf-8',newline='').write(vr.render(vr.build(root)))
"@
& $exe verify-report --root $Root --results $vrResults --json --out $vrRs
if ((Get-FileHash $vrPy).Hash -ne (Get-FileHash $vrRs).Hash) {
    Write-Host '  [FAIL] 逐字节不一致'; $script:Failed++
} else { Write-Host '  [PASS] 逐字节一致（含 root_digest）' }
# ---- 附：Rust 自校验（每条包含证明折叠回根）
& $exe receipts selfcheck --root $Root --scope $Scope
if ($LASTEXITCODE -ne 0) { Write-Host '[FAIL] selfcheck 未通过'; $script:Failed++ }
else { Write-Host '  [PASS] selfcheck：每条包含证明折叠回根' }

# ---- 面 13：附加守护（不是"逐字节对账"，而是**判据自身可信度**的不变量）
# 这三项原先要分别手工跑；并进来是为了让「一条命令跑完全部门禁」成立——靠人记得跑的东西迟早会漏。
Write-Host '== 面 13 · 附加守护（判据自身的不变量） =='
$tools = Join-Path $Root 'engine/rust/tools'

# 13a：自算面一致性（native 优先于 --results ⇒ 少列一条不会红，故须机器可检）
$syncOut = & $PythonExe (Join-Path $tools 'check_native_sync.py') $Root 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] 自算集与快线实际自算面不一致'; $syncOut | ForEach-Object { "      $_" }; $script:Failed++ }
else { Write-Host '  [PASS] 两处手写自算集 == 快线实际自算面' }

# 13b：pub 项读者普查（揪出"没人核的代码面"）
$pubOut = & $PythonExe (Join-Path $tools 'audit_pub_readers.py') $Root 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] 存在全仓零引用的 pub 项（死代码）'; $pubOut | Select-String '\[dead\]' | ForEach-Object { "      $_" }; $script:Failed++ }
else { Write-Host '  [PASS] 无死代码（pub 项均有读者或已写明 test-only 理由）' }

# 13e：AST 事实对账（内置 Python 解析器的地基：遍历序 + unparse）
#   `purity_scan._ast_facts` 的 raises/modules 须**逐字节**一致；sinks 允许 1 处 unparser
#   括号差异，但必须**证明命中标志序列一致**（23k 条候选）——不靠"我认为无害"。
$factsPy = Join-Path $Parity 'facts_py.json'
$factsRs = Join-Path $Parity 'facts_rust.json'
& $PythonExe (Join-Path (Join-Path $Root 'engine/rust/tools') 'gen_purity_facts_truth.py') $Root $factsPy | Out-Null
& $exe purity-facts --root $Root --out $factsRs
$astSame = (Get-FileHash $factsPy).Hash -eq (Get-FileHash $factsRs).Hash
$inert = & $PythonExe (Join-Path (Join-Path $Root 'engine/rust/tools') 'check_ast_facts_inert.py') $Root 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] AST 事实的命中标志序列不一致'; $inert | ForEach-Object { "      $_" }; $script:Failed++ }
elseif ($astSame) { Write-Host '  [PASS] AST 事实逐字节一致（含 sinks 的 unparse）' }
else { Write-Host '  [PASS] AST 事实：raises/modules 逐字节一致；sinks 仅 unparser 括号差异且已证明命中标志一致' }

# 13d：Rust 字面量 lint（`json.dumps` 默认转义成 \\uXXXX，Rust 只认 \\u{XXXX} ⇒ 编译不过）
$litOut = & $PythonExe (Join-Path $tools 'audit_rust_literals.py') $Root 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] tools/ 内有会把 Rust 源码写坏的 json.dumps 用法'; $litOut | ForEach-Object { "      $_" }; $script:Failed++ }
else { Write-Host '  [PASS] tools/ 内无「缺 ensure_ascii 的 json.dumps」写法' }

# 13c：未移植面的反向依赖（证「可选体量」而非「缺口」）
$unpOut = & $PythonExe (Join-Path $tools 'audit_unported_consumers.py') $Root 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host '  [FAIL] 有未移植模块被已移植面依赖（缺口）'; $unpOut | Select-String '已移植面' | ForEach-Object { "      $_" }; $script:Failed++ }
else { Write-Host '  [PASS] 未移植模块无一落在已移植面的判据链上' }

if ($script:Failed -gt 0) { Write-Host ("[FAIL] " + $script:Failed + " 项未通过"); exit 1 }
Write-Host '== 3/3 全部面逐字节一致'
exit 0
