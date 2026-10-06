<#
NF .NET 引擎 · 一键本地只读门（无 bash、无 Python）

跑什么：
  1) nf-dotnet verify      —— 聚合门 11 件（协议回执 / 馆藏回执 / 透明链 / 组合证书 / 断言表 /
                              决策门禁 / 馆藏条目与投影 / 建模三件 / 认知族 / 01-36 知识签名 /
                              conformance（已移植 10/27 契约））
  2) nf-dotnet selftest    —— 负例与健壮性 22 例（撞号 / 深链 / 未知包 / 悬空 / 未桥接 /
                              四类篡改 / 破坏输入 5 例 / 并行不变性 / 一致性契约 4 例）
  3) nf-dotnet bench       —— 性能基线：首次跑写基线，之后每次比对（容差 ×2 且 50 ms 地板）

退出码：0 全通过 / 1 有失败项 / 2 用法或环境错误
用法：
  pwsh -File run-gate.ps1                                  # 默认对 NinFenz-main 工作区
  pwsh -File run-gate.ps1 -Root <仓库或快照路径>
  pwsh -File run-gate.ps1 -Cli <nf-dotnet 可执行体路径>
#>
param(
    # 默认根 = **钉死的导出快照**（不是活仓库）：本门的「真材料」钉锚定金标（HEAD 983741b 的快照），
    # 拿活仓库跑会把「语料漂了」误报成「引擎错了」（第八十六片实测：HEAD 前移到 7e74557 后，
    # 文档命令面计数 277→282、扩展策略面因 .git 在场而 bump 面按边界标 UNKNOWN，各红一条）。
    # 自第八十六片起：导出态断金标摘要，工作区态（带 .git）断语义不变量——两种根都能跑，但**默认**取快照。
    # 要对着当前工作区体检：`run-gate.ps1 -Root <你的仓库路径>`
    # 默认值**不写死机器路径**（第一百一十九片）：可用 NF_SNAPSHOT 环境变量覆盖，缺省取「本脚本上一级的 nf-snap-h5」。
    [string]$Root = $(if ($env:NF_SNAPSHOT) { $env:NF_SNAPSHOT } else { Join-Path (Split-Path $PSScriptRoot -Parent) 'nf-snap-h16' }),
    # 默认 CLI = **源码构建产物**（`dotnet build` 后永远最新）。旧默认指向最早的那个 dist 目录
    # （`dist/nf-dotnet-win-x64`，聚合 10 件 / 自检 18 例的老二进制），会把门跑成「老引擎 PASS」的假象。
    # 要验**交付形态**，显式指到当片产物：`-Cli <…/dist/nf-dotnet-<rid>-fNN-<日期>/nf-dotnet[.exe]>`
    [string]$Cli = $(if ($env:NF_CLI) { $env:NF_CLI } else {
        Join-Path $PSScriptRoot ('tools/nf-dotnet/bin/Release/net8.0/nf-dotnet' + $(if ($env:OS -eq 'Windows_NT') { '.exe' } else { '' })) }),
    [string]$Baseline = $(if ($env:NF_BENCH_BASELINE) { $env:NF_BENCH_BASELINE } else { Join-Path $PSScriptRoot 'dist/bench-baseline.json' })
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Cli)) {
    Write-Error "找不到 CLI：$Cli（先跑 dotnet publish，见引擎 README「交付形态」）"
    exit 2
}
if (-not (Test-Path -LiteralPath (Join-Path $Root "protocol"))) {
    Write-Error "根目录不含 protocol/：$Root"
    exit 2
}

$failures = New-Object System.Collections.Generic.List[string]

Write-Host "== NF .NET 只读门 =="
Write-Host ("   root = " + $Root)
Write-Host ("   cli  = " + $Cli)

# 新鲜度守卫：交付形态（dist 自包含产物）由 dotnet publish 生成，改源码后**不会**自动跟着变；
# 这里只提示、不擅自重建（重建要覆盖 dist 下的既有产物）。
$engineSrc = Join-Path $PSScriptRoot "src\Nf.Engine"
if (Test-Path -LiteralPath $engineSrc) {
    $newestSrc = Get-ChildItem -LiteralPath $engineSrc -Recurse -File -Include *.cs |
        Where-Object { $_.FullName -notmatch '\\obj\\' } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    # CLI 的新鲜度看它所在目录里最新的一件（exe 本身在只改引擎库的增量构建里不会重写）
    $cliStamp = (Get-ChildItem -LiteralPath (Split-Path -Parent $Cli) -File |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    if ($newestSrc -and $cliStamp -lt $newestSrc.LastWriteTime) {
        $cliTime = $cliStamp.ToString("MM-dd HH:mm:ss")
        $srcTime = $newestSrc.LastWriteTime.ToString("MM-dd HH:mm:ss")
        Write-Host ("   [注意] CLI 产物早于源码（{0} < {1}）：先跑 dotnet publish，或用 -Cli 指向 bin 产物" -f $cliTime, $srcTime)
    }
}

# 1) 聚合门
# 语料身份预检（第一百零六片）：先量「被测语料」本身，好让**摘要类钉的红**能被正确归因——
# 作者前移 HEAD 后重新导出快照再跑门，摘要钉会红，那是「语料变了」而不是「引擎坏了」（实测：
# nf-snap-h6 指纹 23a7922f… ≠ 金标 66db1450…，当时只有一条摘要钉红、完全看不出原因）。
$corpusOut = & $Cli --root $Root corpus 2>&1
$corpusLine = ($corpusOut | Select-Object -First 1)
$corpusMismatch = ($corpusLine -match "匹配=否") -and ($corpusLine -match "模式=导出快照")
Write-Host ("   语料 = " + $corpusLine)
if ($corpusMismatch) {
    Write-Host "   [注意] 语料与金标基线不同 → 摘要类钉的红应从「复基线」处置（按对账表各片探针流程重生成 fixtures 并重嵌常量），或改跑活仓库走语义模式。"
}

$verifyOut = & $Cli --root $Root verify 2>&1
$verifyCode = $LASTEXITCODE
$components = ($verifyOut | Select-String -Pattern "✓|✗" | Measure-Object).Count
$verifyLine = ($verifyOut | Select-Object -Last 1)
Write-Host ("[1/3] 聚合门     exit={0} · 分量 {1} · {2}" -f $verifyCode, $components, $verifyLine)
if ($verifyCode -ne 0) { $failures.Add("聚合门（分量 $components 中至少一项失败）") }

# 2) 自检
$selftestOut = & $Cli --root $Root selftest 2>&1
$selftestCode = $LASTEXITCODE
$selftestLine = ($selftestOut | Select-Object -Last 1)
Write-Host ("[2/3] 负例自检   exit={0} · {1}" -f $selftestCode, $selftestLine)
if ($selftestCode -ne 0) { $failures.Add("自检（" + $selftestLine + "）") }
if ($selftestCode -ne 0 -and $corpusMismatch) {
    $failures.Add("↑ 归因提示：语料与金标基线不同（见上方「语料」行）——先复基线再判引擎")
}
# 第一百零七片补：自检失败时**把失败钉名与 detail 打出来**。此前只打「通过 N · 失败 N」——
# 本轮遇到过一次性瞬态失败（222/223，随后同拷贝 8/8 全绿），当场**不知道红的是哪条钉**，无从归因。
if ($selftestCode -ne 0) {
    $jsonOut = & $Cli --root $Root selftest --json 2>&1
    try {
        $rows = ($jsonOut | Out-String | ConvertFrom-Json).rows
        $badRows = @($rows | Where-Object { -not $_.passed })
        Write-Host ("   ✗ 失败钉 {0} 条（同名钉连跑可判是否瞬态）：" -f $badRows.Count)
        $badRows | Select-Object -First 5 | ForEach-Object {
            $detail = $_.detail
            if ($detail.Length -gt 160) { $detail = $detail.Substring(0, 160) }
            Write-Host ("     · " + $_.name)
            Write-Host ("       " + $detail)
        }
    } catch {
        Write-Host "   ✗ 失败钉解析失败（selftest --json 输出不可解析）"
    }
}

# 3) 性能基线
if (-not (Test-Path -LiteralPath $Baseline)) {
    & $Cli --root $Root bench --write-baseline $Baseline | Out-Null
    Write-Host ("[3/3] 性能基线   已写入基线：{0}（下次运行起做回归比对）" -f $Baseline)
} else {
    $benchOut = & $Cli --root $Root bench --baseline $Baseline 2>&1
    $benchCode = $LASTEXITCODE
    $benchLine = ($benchOut | Select-Object -Last 1)
    Write-Host ("[3/3] 性能基线   exit={0} · {1}" -f $benchCode, $benchLine)
    if ($benchCode -ne 0) { $failures.Add("性能回归（" + $benchLine + "）") }
}

if ($failures.Count -eq 0) {
    Write-Host "== NF .NET 门：PASS =="
    exit 0
}
Write-Host "== NF .NET 门：FAIL =="
foreach ($f in $failures) { Write-Host ("   ✗ " + $f) }
exit 1
