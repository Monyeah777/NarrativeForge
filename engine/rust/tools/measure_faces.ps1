# 冷测三对面：端到端 CLI（含进程启动），min of 7。
# 真源侧一律 NF_NO_DISK_CACHE=1 —— 否则第二次起会命中持久缓存，量到的是"热"数。
$env:NF_NO_DISK_CACHE = '1'
$env:PYTHONIOENCODING = 'utf-8'
$root = (Get-Location).Path
$exe = Join-Path $root 'engine\rust\target\release\nf-rs.exe'
$N = 7

function Min-Ms([scriptblock]$body) {
    $best = [double]::MaxValue
    for ($i = 0; $i -lt $N; $i++) {
        $ms = (Measure-Command $body).TotalMilliseconds
        if ($ms -lt $best) { $best = $ms }
    }
    return [math]::Round($best, 1)
}

$faces = @(
    @{ name = 'stats --json';        py = { python scripts/nf.py stats --json | Out-Null };
       rs = { & $exe stats --root $root --json | Out-Null } },
    @{ name = 'layers --verify';     py = { python scripts/nf.py layers --verify --json | Out-Null };
       rs = { & $exe layers --root $root --verify --json | Out-Null } },
    @{ name = 'receipts (protocol)'; py = { python scripts/nf.py receipts --scope protocol | Out-Null };
       rs = { & $exe receipts build --root $root --scope protocol | Out-Null } }
)

"| 面 | Python 真源 | Rust 快线 | 倍数 |"
"|---|---|---|---|"
foreach ($f in $faces) {
    $p = Min-Ms $f.py
    $r = Min-Ms $f.rs
    $x = if ($r -gt 0) { [math]::Round($p / $r, 1) } else { 0 }
    "| ``$($f.name)`` | $p ms | **$r ms** | **$x×** |"
}
