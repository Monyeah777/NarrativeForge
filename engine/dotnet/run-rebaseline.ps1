<#
  一键复基线：真源前移后，把「金标基线」从旧快照搬到新快照。

  为什么要有这一件：第一百二十一片我**手工**走了一遍复基线（导出新快照 → 逐条比对漂移 →
  同步引擎 → 重生成三份夹具 → 改四个金标常量与三处计数 → 重建三类产物 → 全批复跑），
  前后两三个小时。真源还在动（本次会话里它就前移了两次），这种仪式必须变成命令。

  本脚本做的是**机械部分**（不改判据逻辑）：
    ① 预检：新快照在场、含 protocol/ 与 library/，且**指纹与当前基线不同**（否则无事可做）
    ② 重生成三份语料锚定夹具（`--write-fixture`：text_hygiene / prose_lint / regression_score）
    ③ 从夹具里**读出新值**（三个摘要 + 编码卫生计数 + 文档命令面计数）与 `corpus` 新指纹
    ④ 改写常量：CorpusStamp.Baseline · SelfTest 的三个摘要 + 三处计数 + 两处钉名文案
       （可选：`-SnapName` 同时改 `_paths.py` / `run-gate.ps1` / `run-probes.ps1` 的默认快照名）
    ⑤ 重建**三类产物**（Nf.Engine / nf-dotnet / **nfparity**——后者自带判据库副本，漏了会假红）
    ⑥ 对**新快照**跑一键门，打印结论与会话留痕用的变更表

  用法：
    pwsh -NoProfile -File run-rebaseline.ps1 -Snap <新快照> [-SnapName nf-snap-h8] [-Apply]
      · 缺省 **dry-run**：只报告"会改什么"（夹具改了会还原，源码不动）
      · `-Apply`：真正落改并重建 + 跑门
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Snap,
  [string]$SnapName = '',
  # 新靶的 HEAD（真源 `git rev-parse HEAD`）——用于重写 CorpusStamp 的**出处段落**（快照名 + HEAD）。
  # 缺省不传 ⇒ 跳过该段重写（并打印提示），避免写出空快照名。
  [string]$Head = '',
  [string]$Engine = $PSScriptRoot,
  [string]$Cli = '',
  [string]$Python = '',
  [int]$TimeoutSec = 3600,
  [switch]$Force,
  [switch]$Apply
)
$ErrorActionPreference = 'Stop'

function Write-Step([string]$t) { Write-Host ("`n== " + $t + " ==") -ForegroundColor Cyan }

function Resolve-Tool([string]$given, [string]$envName, [string[]]$candidates) {
  if ($given) { return $given }
  $ev = [Environment]::GetEnvironmentVariable($envName)
  if ($ev) { return $ev }
  $cfgPath = Join-Path $Engine 'probes\_paths.local.json'
  if (Test-Path -LiteralPath $cfgPath) {
    try {
      $cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
      $key = switch ($envName) { 'NF_PYTHON' { 'python' } 'NF_DOTNET' { 'dotnet' } 'NF_BASH' { 'bash' } default { '' } }
      if ($key -and $cfg.PSObject.Properties.Name -contains $key -and $cfg.$key) { return [string]$cfg.$key }
    } catch { }
  }
  foreach ($c in $candidates) {
    $g = Get-Command $c -ErrorAction SilentlyContinue
    if ($g) { return $g.Source }
    if ($c -match '[\\/]' -and (Test-Path -LiteralPath $c)) { return $c }
  }
  return $candidates[0]
}

$python = Resolve-Tool $Python 'NF_PYTHON' @('python', 'python3')
if (-not $Cli) {
  $dist = Get-ChildItem (Join-Path $Engine 'dist') -Directory -Filter 'nf-dotnet-win-x64-f*-*' -ErrorAction SilentlyContinue |
    Sort-Object { [int]($_.Name -replace '.*-f(\d+)-.*', '$1') } | Select-Object -Last 1
  $Cli = if ($dist) { Join-Path $dist.FullName 'nf-dotnet.exe' }
  else { Join-Path $Engine ('tools/nf-dotnet/bin/Release/net8.0/nf-dotnet' + $(if ($env:OS -eq 'Windows_NT') { '.exe' } else { '' })) }
}
if (-not (Test-Path -LiteralPath $Cli)) { Write-Error "找不到 CLI：$Cli（用 -Cli 指定）"; exit 1 }

$snapPath = (Resolve-Path -LiteralPath $Snap).Path
$stampCs = Join-Path $Engine 'src\Nf.Engine\CorpusStamp.cs'
$selfTestCs = Join-Path $Engine 'src\Nf.Engine\SelfTest.cs'
$probes = Join-Path $Engine 'probes'
$fixtures = Join-Path $probes '_fixtures'

# ── ① 预检
Write-Step "① 预检（$snapPath）"
foreach ($need in @('protocol', 'library')) {
  if (-not (Test-Path -LiteralPath (Join-Path $snapPath $need))) { Write-Error "新快照缺 $need/：$snapPath"; exit 1 }
}
$corpus = (& $Cli --root $snapPath corpus --json | ConvertFrom-Json)
Write-Host ("   语料指纹 = {0} · 当前金标 = {1} · 匹配 = {2}" -f $corpus.fingerprint, $corpus.baseline, $corpus.matches_baseline)
if ($corpus.matches_baseline -and -not $Force) {
  Write-Host '   指纹与当前金标相同 ⇒ 无需复基线（如确实要重刷，加 -Force）' -ForegroundColor Yellow
  exit 2
}

# ── ② 重生成三份语料锚定夹具
Write-Step '② 重生成语料锚定夹具（text_hygiene / prose_lint / regression_score）'
$backup = Join-Path $env:TEMP ('nf-rebaseline-backup-' + (Get-Date -Format 'HHmmss'))
New-Item -ItemType Directory -Force -Path $backup | Out-Null
$names = @('_text_hygiene_golden.json', '_prose_lint_golden.json', '_regression_score_golden.json')
foreach ($n in $names) { Copy-Item -LiteralPath (Join-Path $fixtures $n) -Destination (Join-Path $backup $n) -Force }
$probeMap = @{
  '_text_hygiene_golden.json' = 'text_hygiene_probe.py'
  '_prose_lint_golden.json' = 'prose_lint_probe.py'
  '_regression_score_golden.json' = 'regression_score_probe.py'
}
foreach ($n in $names) {
  $out = & $python -X utf8 (Join-Path $probes $probeMap[$n]) --snap $snapPath --cli $Cli --write-fixture 2>&1
  if ($LASTEXITCODE -ne 0) { Write-Error ("夹具重生成失败：" + $probeMap[$n] + "`n" + ($out | Select-Object -Last 4 | Out-String)); exit 1 }
  Write-Host ("   OK " + $probeMap[$n] + " → " + $n)
}

# ── ③ 读出新值
Write-Step '③ 读出新值'
function Read-Json([string]$p) { Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json }
$hyg = Read-Json (Join-Path $fixtures '_text_hygiene_golden.json')
$pro = Read-Json (Join-Path $fixtures '_prose_lint_golden.json')
$reg = Read-Json (Join-Path $fixtures '_regression_score_golden.json')
$new = [ordered]@{
  stamp = $corpus.fingerprint
  hygDigest = $hyg.cases.real.digest32
  proDigest = $pro.cases.real_command_face.digest32
  cscNegative = $reg.cases.conformance_negative.digest32
  hygSummary = $hyg.cases.real.summary
  proStat = $pro.cases.real_command_face.log[0]
}
$m = [regex]::Match($new.hygSummary, '文本 (\d+) 件 / JSON (\d+) 件 / 键 (\d+) 个 / 版本 (\d+) 个')
if (-not $m.Success) { Write-Error ("卫生 summary 解析失败：" + $new.hygSummary); exit 1 }
$new.text = $m.Groups[1].Value; $new.json = $m.Groups[2].Value; $new.keys = $m.Groups[3].Value; $new.versions = $m.Groups[4].Value
$m2 = [regex]::Match($new.proStat, 'docs=(\d+) commands_checked=(\d+) cli_commands=(\d+) mcp_tools=(\d+)')
if (-not $m2.Success) { Write-Error ("文档面 STAT 解析失败：" + $new.proStat); exit 1 }
$new.docs = $m2.Groups[1].Value; $new.checked = $m2.Groups[2].Value; $new.cli = $m2.Groups[3].Value; $new.mcp = $m2.Groups[4].Value
Write-Host ("   指纹 {0}`n   编码卫生 {1}（{2}）`n   文档命令面 {3}（{4}）`n   conformance 合成虚标 {5}" -f $new.stamp, $new.hygDigest, $new.hygSummary, $new.proDigest, $new.proStat, $new.cscNegative)

# ── ④ 生成改写清单（断言每条恰好命中一次）
Write-Step '④ 改写清单（dry-run 时只报告）'
function Edit-Once([string]$file, [string]$pattern, [string]$replacement, [string]$label, [System.Collections.Generic.List[object]]$log) {
  $text = [IO.File]::ReadAllText($file, [Text.UTF8Encoding]::new($false))
  $rx = [regex]::new($pattern)
  $hits = $rx.Matches($text)
  if ($hits.Count -ne 1) { Write-Error ("$label 命中 $($hits.Count) 次（应为 1）：$pattern"); exit 1 }
  $oldLine = ($hits[0].Value -split "`n")[0]
  $newLine = $rx.Replace($text, $replacement, 1)
  $newLine = ($rx.Replace($hits[0].Value, $replacement, 1) -split "`n")[0]
  $log.Add([pscustomobject]@{ file = (Split-Path $file -Leaf); label = $label; old = $oldLine.Trim(); new = $newLine.Trim() })
  if ($Apply) { [IO.File]::WriteAllText($file, $rx.Replace($text, $replacement, 1), [Text.UTF8Encoding]::new($false)) }
}
$log = [System.Collections.Generic.List[object]]::new()
Edit-Once $stampCs 'public const string Baseline = "[0-9a-f]+";' ('public const string Baseline = "' + $new.stamp + '";') '语料指纹' $log
if ($Head -and $SnapName) {
  Edit-Once $stampCs '金标语料（\*\*`nf-snap-h[0-9]+` · HEAD `[0-9a-f]+` 导出快照\*\*）的指纹。' ('金标语料（**`' + $SnapName + '` · HEAD `' + $Head + '` 导出快照**）的指纹。') '金标出处（快照名 + HEAD）' $log
} else {
  Write-Host '   [提示] 未同时给 -SnapName 与 -Head ⇒ 跳过 CorpusStamp 出处段落重写（该段会与常量脱节）' -ForegroundColor Yellow
}
Edit-Once $selfTestCs 'const string CscNegative = "[0-9a-f]+";' ('const string CscNegative = "' + $new.cscNegative + '";') 'conformance 合成虚标摘要' $log
Edit-Once $selfTestCs '（零问题 · 导出态断 72 文档/\d+ 处与金标摘要 / 工作区态断语义）' ('（零问题 · 导出态断 72 文档/' + $new.checked + ' 处与金标摘要 / 工作区态断语义）') '文档面钉名' $log
Edit-Once $selfTestCs 'Convert\.ToInt64\(real\.Stats\["cli_commands"\]\) == \d+' ('Convert.ToInt64(real.Stats["cli_commands"]) == ' + $new.cli) 'cli 命令数' $log
Edit-Once $selfTestCs 'Convert\.ToInt64\(real\.Stats\["commands_checked"\]\) == \d+' ('Convert.ToInt64(real.Stats["commands_checked"]) == ' + $new.checked) '文档提及处数' $log
Edit-Once $selfTestCs '（零问题 · 导出态另断 \d+/\d+/\d+/\d+ 与金标摘要）' ('（零问题 · 导出态另断 ' + $new.text + '/' + $new.json + '/' + $new.keys + '/' + $new.versions + ' 与金标摘要）') '编码卫生钉名' $log
Edit-Once $selfTestCs 'Convert\.ToInt64\(real\.Stats\["text"\]\) == \d+' ('Convert.ToInt64(real.Stats["text"]) == ' + $new.text) '文本件数' $log
# 两处同名常量 RealGoldenDigest：按所在方法块定位
foreach ($pair in @(@('ProseLintCases', $new.proDigest, '文档面真材料摘要'), @('TextHygieneCases', $new.hygDigest, '编码卫生真材料摘要'))) {
  $text = [IO.File]::ReadAllText($selfTestCs, [Text.UTF8Encoding]::new($false))
  $anchor = $text.IndexOf('private static void ' + $pair[0] + '(')
  if ($anchor -lt 0) { Write-Error ('找不到方法：' + $pair[0]); exit 1 }
  $rx = [regex]::new('const string RealGoldenDigest = "[0-9a-f]+";')
  $hit = $rx.Match($text, $anchor)
  if (-not $hit.Success) { Write-Error ('方法内找不到 RealGoldenDigest：' + $pair[0]); exit 1 }
  $log.Add([pscustomobject]@{ file = 'SelfTest.cs'; label = $pair[2]; old = $hit.Value.Trim(); new = ('const string RealGoldenDigest = "' + $pair[1] + '";') })
  if ($Apply) {
    $replaced = $text.Substring(0, $hit.Index) + 'const string RealGoldenDigest = "' + $pair[1] + '";' + $text.Substring($hit.Index + $hit.Length)
    [IO.File]::WriteAllText($selfTestCs, $replaced, [Text.UTF8Encoding]::new($false))
  }
}
if ($SnapName) {
  # ⚠️ 只改**基线快照**那一处：`SNAP_OTHER` / `-Other`（对照快照）必须留着，
  #    否则「拿另一份快照跑门、看归因」这条判据就废了（本工具首版整体替换过，dry-run 当场照出）。
  $targets = @(
    @{ file = (Join-Path $probes '_paths.py'); rx = 'SNAP: str = os\.environ\.get\("NF_SNAPSHOT"\) or str\(_SIBLING / "[^"]+"\)'; rep = 'SNAP: str = os.environ.get("NF_SNAPSHOT") or str(_SIBLING / "' + $SnapName + '")' },
    @{ file = (Join-Path $Engine 'run-gate.ps1'); rx = "\[string\]\`$Root = \`$\(if \(\`$env:NF_SNAPSHOT\) \{ \`$env:NF_SNAPSHOT \} else \{ Join-Path \(Split-Path \`$PSScriptRoot -Parent\) '[^']+' \}\)"; rep = "[string]`$Root = `$(if (`$env:NF_SNAPSHOT) { `$env:NF_SNAPSHOT } else { Join-Path (Split-Path `$PSScriptRoot -Parent) '" + $SnapName + "' })" },
    @{ file = (Join-Path $Engine 'run-probes.ps1'); rx = "\[string\]\`$Snap\s+= \`$\(if \(\`$env:NF_SNAPSHOT\) \{ \`$env:NF_SNAPSHOT \} else \{ Join-Path \(Split-Path \`$PSScriptRoot -Parent\) '[^']+' \}\)"; rep = "[string]`$Snap     = `$(if (`$env:NF_SNAPSHOT) { `$env:NF_SNAPSHOT } else { Join-Path (Split-Path `$PSScriptRoot -Parent) '" + $SnapName + "' })" }
  )
  foreach ($t in $targets) {
    $text = [IO.File]::ReadAllText($t.file, [Text.UTF8Encoding]::new($false))
    $rx = [regex]::new($t.rx)
    $hits = $rx.Matches($text)
    if ($hits.Count -ne 1) { Write-Error ("默认快照名在 " + (Split-Path $t.file -Leaf) + " 命中 $($hits.Count) 次（应为 1）"); exit 1 }
    $log.Add([pscustomobject]@{ file = (Split-Path $t.file -Leaf); label = '默认基线快照名'; old = $hits[0].Value.Trim(); new = $t.rep.Trim() })
    if ($Apply) { [IO.File]::WriteAllText($t.file, $rx.Replace($text, $t.rep, 1), [Text.UTF8Encoding]::new($false)) }
  }
}
$log | Format-Table -AutoSize -Wrap

if (-not $Apply) {
  foreach ($n in $names) { Copy-Item -LiteralPath (Join-Path $backup $n) -Destination (Join-Path $fixtures $n) -Force }
  Write-Host "`n[dry-run] 夹具已还原、源码未动。要落改请加 -Apply。" -ForegroundColor Yellow
  exit 0
}

# ── ⑤ 重建三类产物（含 nfparity——它自带判据库副本）
Write-Step '⑤ 重建 Nf.Engine / nf-dotnet / nfparity'
$dotnet = Resolve-Tool '' 'NF_DOTNET' @('dotnet')
foreach ($csproj in @('src/Nf.Engine/Nf.Engine.csproj', 'tools/nf-dotnet/nf-dotnet.csproj', 'tools/nfparity/nfparity.csproj')) {
  & $dotnet build (Join-Path $Engine $csproj) -c Release -v q --nologo 2>&1 | Select-Object -Last 1 | Out-Null
  if ($LASTEXITCODE -ne 0) { Write-Error ("构建失败：" + $csproj); exit 1 }
  Write-Host ("   OK " + $csproj)
}

# ── ⑥ 对新快照跑门
Write-Step '⑥ 对新快照跑一键门'
$gateCli = Join-Path $Engine ('tools/nf-dotnet/bin/Release/net8.0/nf-dotnet' + $(if ($env:OS -eq 'Windows_NT') { '.exe' } else { '' }))
$gate = & pwsh -NoProfile -File (Join-Path $Engine 'run-gate.ps1') -Root $snapPath -Cli $gateCli -Baseline (Join-Path $env:TEMP 'rebaseline-bench.json') 2>&1
$gate | Select-Object -Last 6 | ForEach-Object { Write-Host $_ }
$ok = ($gate | Where-Object { $_ -match '== NF \.NET 门：PASS ==' }).Count -gt 0
Write-Host ''
if ($ok) { Write-Host ("复基线完成：新基线指纹 " + $new.stamp + " · 门 PASS（新快照）") -ForegroundColor Green; exit 0 }
Write-Host '复基线后门未通过——按失败钉逐条处理（多半还有别的语料锚定夹具未重生成）' -ForegroundColor Red
exit 1
