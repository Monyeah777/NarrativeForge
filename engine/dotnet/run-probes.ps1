<#
  NF .NET 工业引擎 · 判据探针一键跑批（probes/*.py）

  为什么要有这一件：38 个探针的口径（哪个用 nf-dotnet、哪个用 nfparity、要传哪些路径）
  此前只存在于编制者脑内与逐片补记里，每次全量复跑都要人工逐条拼参数——第一百零八片已经
  因此出过一次假红（跑批靠字符串匹配猜 CLI，把 nf-dotnet 误换成 nfparity）。
  本件把口径收进 probes/probe_manifest.json（唯一出处），这里只做三件事：
  读清单 → 代换 token → 逐条跑并汇总。**不在脚本里硬编码任何探针参数。**

  用法（全部路径可覆盖；默认值 = 本机实测口径）：
    pwsh -NoProfile -File run-probes.ps1                     # 默认跑 core 集合
    pwsh -NoProfile -File run-probes.ps1 -Tier all           # 含重型集合（两道门同判 / 规模 / 模糊 / 敌意输入）
    pwsh -NoProfile -File run-probes.ps1 -Tier long          # 只跑重型集合（同样 5 条）
    pwsh -NoProfile -File run-probes.ps1 -Only face-parity,corpus-stamp
    pwsh -NoProfile -File run-probes.ps1 -Snap <另一份快照> -Cli <另一份产物>

  纪律：
    · 只读被测语料；写物只落 probes/_stout（含记录件重定向，绝不覆盖具名记录件）
    · 任一条 FAIL / 超时 / 参数代换不净 → 整体 exit 1
    · 结果落 probes/_stout/_probe_run.json（机器面）与每条的 .out.txt/.err.txt
#>
[CmdletBinding()]
param(
  [string]$Engine   = $PSScriptRoot,
  # 默认值**不写死机器路径**（第一百一十九片）：环境变量优先，缺省取「引擎工作区上一级的同级快照」
  [string]$Snap     = $(if ($env:NF_SNAPSHOT) { $env:NF_SNAPSHOT } else { Join-Path (Split-Path $PSScriptRoot -Parent) 'nf-snap-h16' }),
  [string]$Other    = $(if ($env:NF_SNAPSHOT_OTHER) { $env:NF_SNAPSHOT_OTHER } else { Join-Path (Split-Path $PSScriptRoot -Parent) 'nf-snap-h5' }),
  [string]$Cli      = '',
  [string]$Parity   = '',
  [string]$Python   = '',
  [string]$DotNet   = '',
  [string]$Bash     = '',
  [string]$Manifest = '',
  [ValidateSet('core', 'long', 'all')][string]$Tier = 'core',
  [string[]]$Only   = @(),
  [int]$TimeoutSec  = 3600
)
$ErrorActionPreference = 'Stop'

# 解释器/工具的解析顺序：显式参数 > 环境变量（NF_PYTHON/NF_DOTNET/NF_BASH）>
# **机器本地配置** `probes/_paths.local.json`（本机专用、不进交付包）> PATH 常见名。
# 这样「交付包里的默认值」是通用的，而我这台机器的 quirks（例如 Git 装在 comfyui 下）
# 只写在本地配置里，不会被带进仓库。
$localCfg = $null
$localCfgPath = Join-Path $Engine 'probes\_paths.local.json'
if (Test-Path -LiteralPath $localCfgPath) {
  try { $localCfg = Get-Content -LiteralPath $localCfgPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $localCfg = $null }
}
function Resolve-Tool([string]$given, [string]$envName, [string]$cfgName, [string[]]$candidates) {
  if ($given) { return $given }
  if ($envName -and (Get-Item -Path "env:$envName" -ErrorAction SilentlyContinue)) { return (Get-Item -Path "env:$envName").Value }
  if ($localCfg -and $cfgName -and $localCfg.PSObject.Properties.Name -contains $cfgName) {
    $v = [string]$localCfg.$cfgName
    if ($v) { return $v }
  }
  foreach ($c in $candidates) {
    $g = Get-Command $c -ErrorAction SilentlyContinue
    if ($g) { return $g.Source }
    if ($c -match '[\\/]' -and (Test-Path -LiteralPath $c)) { return $c }
  }
  return $candidates[0]
}
$Python = Resolve-Tool $Python 'NF_PYTHON' 'python' @('python', 'python3')
$DotNet = Resolve-Tool $DotNet 'NF_DOTNET' 'dotnet' @('dotnet')
$Bash   = Resolve-Tool $Bash   'NF_BASH'   'bash'   @('bash', '/bin/bash')

if (-not $Manifest) { $Manifest = Join-Path $Engine 'probes\probe_manifest.json' }
$stout = Join-Path $Engine 'probes\_stout'
New-Item -ItemType Directory -Force -Path $stout | Out-Null

function Get-NewestDist([string]$engine, [string]$rid) {
  $best = ''; $bestN = -1
  $root = Join-Path $engine 'dist'
  if (-not (Test-Path $root)) { return '' }
  foreach ($d in (Get-ChildItem $root -Directory -Filter "nf-dotnet-$rid-f*-*" -ErrorAction SilentlyContinue)) {
    if ($d.Name -match '-f(\d+)-') {
      $n = [int]$Matches[1]
      if ($n -gt $bestN) { $bestN = $n; $best = $d.FullName }
    }
  }
  return $best
}

$binDir = Join-Path $Engine 'tools\nf-dotnet\bin\Release\net8.0'
$winDir = Get-NewestDist $Engine 'win-x64'
$linDir = Get-NewestDist $Engine 'linux-x64'
if (-not $Cli) {
  if ($winDir) { $Cli = Join-Path $winDir 'nf-dotnet.exe' } else { $Cli = Join-Path $binDir 'nf-dotnet.exe' }
}
if (-not $Parity) { $Parity = Join-Path $Engine 'tools\nfparity\bin\Release\net8.0\nfparity.exe' }

$tok = [ordered]@{
  '{engine}' = (Resolve-Path $Engine).Path
  '{snap}'   = $Snap
  '{other}'  = $Other
  '{cli}'    = $Cli
  '{parity}' = $Parity
  '{py}'     = $Python
  '{dotnet}' = $DotNet
  '{bash}'   = $Bash
  '{self}'   = (Join-Path $Engine 'src\Nf.Engine\SelfTest.cs')
  '{stout}'  = $stout
  '{bin}'    = $binDir
  '{win}'    = $winDir
  '{linux}'  = $linDir
}

Write-Output '== NF .NET 判据探针跑批 =='
foreach ($k in $tok.Keys) { Write-Output ('   {0,-9} = {1}' -f $k, $tok[$k]) }
$missing = @()
foreach ($k in @('{engine}', '{snap}', '{cli}', '{parity}', '{py}', '{dotnet}', '{bash}', '{self}', '{bin}', '{win}', '{linux}')) {
  $v = $tok[$k]
  if (-not $v -or -not (Test-Path $v)) { $missing += ('{0} -> {1}' -f $k, $v) }
}
if ($missing.Count -gt 0) {
  Write-Output 'FAIL: 下列 token 解析不到实体（缺产物或缺路径）：'
  $missing | ForEach-Object { Write-Output ('   - ' + $_) }
  exit 1
}

$manifestPath = $Manifest
$mRaw = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8
if (-not $mRaw) {
  Write-Output ('FAIL: 清单读不到内容：' + $manifestPath)
  exit 1
}
try { $manifestObj = $mRaw | ConvertFrom-Json }
catch { Write-Output ('FAIL: 清单不是合法 JSON（' + $manifestPath + '）：' + $_.Exception.Message); exit 1 }
if (-not $manifestObj.probes) {
  Write-Output ('FAIL: 清单里 probes 为空或缺失：' + $manifestPath)
  exit 1
}

# 清单 ↔ 磁盘一一对应（fail-closed）：新增 .py 而不登记、或登记了不存在的脚本，都必须当场红。
# 探针 = `probes/*.py` 里**不以 `_` 开头**的（`_paths.py` 是辅助模块、`_fixtures/` 是夹具）
$pyProbes = @(Get-ChildItem (Join-Path $Engine 'probes') -Filter '*.py' | Where-Object { $_.Name -notlike '_*' } | Select-Object -ExpandProperty Name)
$declared = @($manifestObj.probes | Select-Object -ExpandProperty script)
$undeclared = @($pyProbes | Where-Object { $declared -notcontains $_ })
$missingScript = @($declared | Where-Object { $pyProbes -notcontains $_ })
if ($undeclared.Count -gt 0 -or $missingScript.Count -gt 0) {
  Write-Output 'FAIL: 清单与 probes/*.py 不一致（跑批口径必须一一对应）：'
  if ($undeclared.Count -gt 0) { Write-Output ('   - 磁盘上有、清单里没有：' + ($undeclared -join ', ')) }
  if ($missingScript.Count -gt 0) { Write-Output ('   - 清单里有、磁盘上没有：' + ($missingScript -join ', ')) }
  exit 1
}
Write-Output ('   清单一致性：probes/*.py ' + $pyProbes.Count + ' 个 ↔ 清单 ' + $declared.Count + ' 条（一一对应）')
$plan = @()
foreach ($p in $manifestObj.probes) {
  if ($Tier -ne 'all' -and $p.tier -ne $Tier) { continue }
  if ($Only.Count -gt 0 -and ($Only -notcontains $p.name)) { continue }
  $plan += $p
}
Write-Output ('   集合 = ' + $Tier + ' · 本批 ' + $plan.Count + ' 个探针（清单共 ' + $manifestObj.probes.Count + ' 个 · ' + $manifestPath + '）')
if ($plan.Count -eq 0) {
  Write-Output 'FAIL: 本次筛选命中 0 条探针（-Tier/-Only 写错时不许报 PASS —— 跑了 0 条不是绿）'
  exit 1
}
Write-Output ''

$results = @()
$fail = 0
$total = [Diagnostics.Stopwatch]::StartNew()

foreach ($p in $plan) {
  $script = Join-Path $Engine ('probes\' + $p.script)
  if (-not (Test-Path $script)) {
    Write-Output ('FAIL ' + $p.name + ' —— 探针文件不在场：' + $script)
    $results += [ordered]@{ name = $p.name; script = $p.script; tier = $p.tier; exit = -1; seconds = 0; note = 'script missing' }
    $fail++
    continue
  }
  $argv = @()
  $bad = @()
  foreach ($a in $p.args) {
    $v = [string]$a
    foreach ($k in $tok.Keys) { $v = $v.Replace($k, [string]$tok[$k]) }
    if ($v -match '\{[a-z]+\}') { $bad += $v }
    $argv += $v
  }
  if ($bad.Count -gt 0) {
    Write-Output ('FAIL ' + $p.name + ' —— 参数代换不净：' + ($bad -join ' '))
    $results += [ordered]@{ name = $p.name; script = $p.script; tier = $p.tier; exit = -1; seconds = 0; note = 'unsubstituted token' }
    $fail++
    continue
  }

  $outFile = Join-Path $stout ('_' + $p.name + '.out.txt')
  $errFile = Join-Path $stout ('_' + $p.name + '.err.txt')

  # 用 ProcessStartInfo.ArgumentList：**原生按参数逐个传递**。
  # （Start-Process -ArgumentList 是拼成一个命令行字符串，带空格的路径会被切开——
  #  本轮实测：‘C:\Program Files\Python311\python.exe’ 被拆成两段，argparse 报 unrecognized arguments。）
  # `-B`：连 `import _paths` 这类模块导入也不许写 `__pycache__`（本项目「170 个 .pyc」教训）
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName = $Python
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
  $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
  $psi.WorkingDirectory = $Engine
  foreach ($a in (@('-X', 'utf8', '-B', $script) + $argv)) { $psi.ArgumentList.Add($a) }

  $sw = [Diagnostics.Stopwatch]::StartNew()
  $proc = [System.Diagnostics.Process]::new()
  $proc.StartInfo = $psi
  $null = $proc.Start()
  $outTask = $proc.StandardOutput.ReadToEndAsync()
  $errTask = $proc.StandardError.ReadToEndAsync()
  $timedOut = $false
  if (-not $proc.WaitForExit($TimeoutSec * 1000)) {
    $timedOut = $true
    try { $proc.Kill($true) } catch { }
    Start-Sleep -Seconds 2
  }
  $code = if ($timedOut) { 124 } else { $proc.ExitCode }
  $outText = $outTask.GetAwaiter().GetResult()
  $errText = $errTask.GetAwaiter().GetResult()
  $sw.Stop()
  Set-Content -LiteralPath $outFile -Value $outText -Encoding UTF8 -NoNewline
  Set-Content -LiteralPath $errFile -Value $errText -Encoding UTF8 -NoNewline

  $tail = ''
  $lines = @($outText -split "`r?`n" | Where-Object { $_.Trim() -ne '' })
  if ($lines.Count -gt 0) { $tail = ($lines[-1]).Trim() }
  if (-not $tail) {
    $elines = @($errText -split "`r?`n" | Where-Object { $_.Trim() -ne '' })
    if ($elines.Count -gt 0) { $tail = 'stderr: ' + ($elines[-1]).Trim() }
  }
  if ($tail.Length -gt 120) { $tail = $tail.Substring(0, 120) + '…' }

  $verdict = if ($code -eq 0) { 'OK  ' } else { 'FAIL' }
  if ($code -ne 0) { $fail++ }
  Write-Output ('{0} {1,-22} exit={2,-4} {3,6:N1}s  {4}' -f $verdict, $p.name, $code, $sw.Elapsed.TotalSeconds, $tail)
  $results += [ordered]@{
    name = $p.name; script = $p.script; tier = $p.tier; exit = $code
    seconds = [Math]::Round($sw.Elapsed.TotalSeconds, 1); timedOut = $timedOut; tail = $tail
  }
}

$total.Stop()
Write-Output ''
Write-Output ('== 跑批结论：' + ($plan.Count - $fail) + '/' + $plan.Count + ' 通过 · 用时 ' + [Math]::Round($total.Elapsed.TotalSeconds, 1) + ' s ==')

$record = [ordered]@{
  schema      = 'nf-net-probe-run/1'
  date        = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
  tier        = $Tier
  snap        = $Snap
  other       = $Other
  cli         = $Cli
  parity      = $Parity
  python      = $Python
  bash        = $Bash
  manifest    = $Manifest
  passed      = ($plan.Count - $fail)
  total       = $plan.Count
  failed      = $fail
  seconds     = [Math]::Round($total.Elapsed.TotalSeconds, 1)
  results     = $results
}
$runJson = Join-Path $stout '_probe_run.json'
($record | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $runJson -Encoding UTF8
Write-Output ('   机器面已写：' + $runJson)

if ($fail -gt 0) { Write-Output '== 探针跑批：FAIL =='; exit 1 }
Write-Output '== 探针跑批：PASS =='
exit 0
