<#
  NF 零依赖复算样例 · 外部侧复算器（Windows / PowerShell 7）

  做什么：只读 NF 契约语料 → 用 .NET 引擎复算组合证书 → 与 scenario.json 的钉定期望逐项比对 →
          落 out/ 产物与确定性 receipt.json。

  纪律：
    · 只读语料（不写语料树）；产物只落本样例 out/
    · 不依赖 NF 代码、不依赖 Python（引擎是自包含产物）
    · 判定三态：PASS(0) / 语料漂移(3) / FAIL(1)——**语料漂移不写 PASS**
    · receipt.json 确定性：不含时间戳、不含本机绝对路径（可字节比对）
#>
[CmdletBinding()]
param(
  [string]$Cli  = $(if ($env:NF_SAMPLE_CLI) { $env:NF_SAMPLE_CLI } else { Join-Path $PSScriptRoot 'dist\nf-dotnet-win-x64-f111-2026-09-28\nf-dotnet.exe' }),
  [string]$Root = $(if ($env:NF_SAMPLE_ROOT) { $env:NF_SAMPLE_ROOT } else { Join-Path (Split-Path $PSScriptRoot -Parent) 'nf-snap-h8' }),
  # 外部侧可以带自己的钉定件（默认用本样例的 scenario.json；负对照 = 期望值故意写错）
  [string]$ScenarioFile = $(Join-Path $PSScriptRoot 'scenario.json'),
  [ValidateSet('small', 'limit', 'all')][string]$Scenario = 'small'
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$Utf8NoBom = New-Object Text.UTF8Encoding($false)

function Write-Text([string]$Path, [string]$Text) {
  $dir = Split-Path $Path -Parent
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [IO.File]::WriteAllText($Path, $Text, $Utf8NoBom)
}
function Sha256Hex([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower() }
# 注意：参数名**不能叫 $Args**（PowerShell 自动变量，会让 @Args 展开失效 ⇒ 命令拿到零参数、回落到用法文本）
function Run-Cli([string[]]$CliArgs) {
  # 走 ProcessStartInfo + ArgumentList 直读：① 参数不经 PowerShell 再解析（CJK 包名安全）
  # ② stdout 直读**不换行风格转换**（Out-String 会把引擎的 LF 变成 CRLF ⇒ 摘要与字节比对失真）
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $Cli
  foreach ($a in $CliArgs) { [void]$psi.ArgumentList.Add($a) }
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $psi.StandardOutputEncoding = New-Object Text.UTF8Encoding($false)
  $psi.StandardErrorEncoding = New-Object Text.UTF8Encoding($false)
  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd()
  $err = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  return @{ exit = $p.ExitCode; text = $out; err = $err }
}

if (-not (Test-Path -LiteralPath $Cli))   { Write-Error "找不到引擎产物：$Cli"; exit 1 }
if (-not (Test-Path -LiteralPath $Root))  { Write-Error "找不到语料根：$Root"; exit 1 }
$Root = (Resolve-Path -LiteralPath $Root).Path
$scnPath = $ScenarioFile
if (-not (Test-Path -LiteralPath $scnPath)) { Write-Error "找不到场景件：$scnPath"; exit 1 }
$scn = Get-Content -LiteralPath $scnPath -Raw -Encoding UTF8 | ConvertFrom-Json
$certFile = Join-Path $Root 'protocol\combo_certificates.json'
if (-not (Test-Path -LiteralPath $certFile)) { Write-Error "语料缺 protocol/combo_certificates.json：$Root"; exit 1 }
$corpus = Get-Content -LiteralPath $certFile -Raw -Encoding UTF8 | ConvertFrom-Json
$outDir = Join-Path $PSScriptRoot 'out'

Write-Host '== NF 零依赖复算样例 =='
Write-Host ("   cli    = {0}" -f (Split-Path $Cli -Leaf))
Write-Host ("   root   = {0}" -f (Split-Path $Root -Leaf))
Write-Host ("   语料钉定 = {0}" -f $scn.corpus.corpus_fingerprint)

# ① 语料身份（引擎自报；外部侧独立于 NF 代码）
$fp = Run-Cli @('--root', $Root, 'corpus', '--json')
if ($fp.exit -ne 0) { Write-Error "corpus 命令失败：$($fp.text)"; exit 1 }
$fpJson = $fp.text | ConvertFrom-Json
$fingerprint = [string]$fpJson.fingerprint
Write-Host ("   语料实测 = {0}（匹配钉定 = {1}）" -f $fingerprint, ($fingerprint -eq $scn.corpus.corpus_fingerprint))

# ② 17 条证书全量复算（T4）
$vall = Run-Cli @('--root', $Root, 'combine', 'verify', '--json')
$verifyPath = Join-Path $outDir 'verify_all.json'
Write-Text $verifyPath $vall.text
$vallJson = $null
try { $vallJson = $vall.text | ConvertFrom-Json } catch { }

# ③ 选定场景：从语料里读输入（只读契约），复算后逐项比对
$targets = @()
if ($Scenario -eq 'all') {
  for ($i = 0; $i -lt $corpus.certificates.Count; $i++) {
    $targets += [pscustomobject]@{ id = "cert-$i"; index = $i; expected = $corpus.certificates[$i].digest; modules = $corpus.certificates[$i].module_count; legal = $corpus.certificates[$i].legal }
  }
} else {
  $s = $scn.scenarios | Where-Object { $_.id -eq $Scenario }
  $targets += [pscustomobject]@{ id = $s.id; index = [int]$s.certificate_index; expected = $s.expected_digest; modules = [int]$s.expected_module_count; legal = [bool]$s.expected_legal }
}

$rows = @(); $mismatch = 0; $caseCount = 0
foreach ($t in $targets) {
  $cert = $corpus.certificates[$t.index]
  $packsArg = ($cert.packs -join ',')
  $argv = @('--root', $Root, 'combine', 'plan')
  if ($packsArg) { $argv += @('--packs', $packsArg) }
  if ($cert.extra_modules -and $cert.extra_modules.Count -gt 0) { $argv += @('--extra-modules', ($cert.extra_modules -join ',')) }
  $argv += '--json'
  $r = Run-Cli $argv
  $caseCount++
  $certPath = Join-Path $outDir ("certificate_{0}.json" -f $t.index)
  Write-Text $certPath $r.text
  $got = $null
  try { $got = $r.text | ConvertFrom-Json } catch { }
  $ok = ($r.exit -eq 0) -and $got -and ([string]$got.digest -eq [string]$t.expected) `
        -and ([int]$got.module_count -eq [int]$t.modules) -and ([bool]$got.legal -eq [bool]$t.legal)
  if (-not $ok) { $mismatch++ }
  $rows += [ordered]@{
    case             = $t.id
    certificate_index = $t.index
    packs            = $cert.packs.Count
    module_count     = if ($got) { $got.module_count } else { $null }
    legal            = if ($got) { $got.legal } else { $null }
    digest_expected  = [string]$t.expected
    digest_actual    = if ($got) { [string]$got.digest } else { $null }
    output_sha256    = (Sha256Hex $certPath)
    ok               = $ok
  }
  Write-Host ("   [{0}] cert#{1} · packs {2} · digest {3}" -f $(if ($ok) { 'OK  ' } else { 'FAIL' }), $t.index, $cert.packs.Count, ([string]$t.expected).Substring(0, 12))
}

# ④ 判定（三态）
$corpusMatches = ($fingerprint -eq $scn.corpus.corpus_fingerprint)
$verdict = if ($mismatch -gt 0) { 'FAIL' } elseif (-not $corpusMatches) { 'CORPUS_DRIFT' } else { 'PASS' }
$exit = switch ($verdict) { 'PASS' { 0 } 'CORPUS_DRIFT' { 3 } default { 1 } }

# ⑤ 确定性 receipt（无时间戳 / 无本机绝对路径）
$receipt = [ordered]@{
  schema              = 'nf-zero-dep-sample-receipt/1'
  sample              = 'NF_NET引擎_零依赖复算样例_v1'
  scenario_file       = (Split-Path $scnPath -Leaf)
  engine_form         = $scn.engine.delivery_form
  # 换行风格 = 平台原生（Windows CRLF / Linux LF）——与真源 Python 文本模式一致，
  # 故**同平台**逐字节对账成立；跨平台的 stdout 字节不可直接比（摘要按规范串算，故不受影响）。
  platform            = $(if ($IsWindows) { 'windows' } elseif ($IsLinux) { 'linux' } else { 'macos' })
  stdout_newline      = $(if ($IsWindows) { 'crlf' } else { 'lf' })
  cli_leaf            = (Split-Path $Cli -Leaf)
  cli_sha256          = (Sha256Hex $Cli)
  corpus_leaf         = (Split-Path $Root -Leaf)
  corpus_fingerprint  = $fingerprint
  corpus_pinned       = $scn.corpus.corpus_fingerprint
  corpus_matches      = $corpusMatches
  scenario            = $Scenario
  cases               = $caseCount
  mismatches          = $mismatch
  verify_all_exit     = $vall.exit
  verify_all_failed   = if ($vallJson) { $vallJson.failed } else { $null }
  verify_all_sha256   = (Sha256Hex $verifyPath)
  rows                = $rows
  verdict             = $verdict
}
$receiptPath = Join-Path $outDir 'receipt.json'
Write-Text $receiptPath (($receipt | ConvertTo-Json -Depth 6) + "`n")

Write-Host ("== 判定：{0}（用例 {1} · 不符 {2} · 语料匹配 {3}）==" -f $verdict, $caseCount, $mismatch, $corpusMatches)
Write-Host ("   receipt = {0}" -f $receiptPath)
if ($verdict -eq 'CORPUS_DRIFT') { Write-Host '   说明：语料非钉定版本 ⇒ 期望摘要不可比，须按复基线处置（不是引擎坏）' }
exit $exit
