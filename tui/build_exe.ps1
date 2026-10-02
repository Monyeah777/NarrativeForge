# NF terminal TUI - single-file build (PyInstaller onefile).
#
# Usage : powershell -ExecutionPolicy Bypass -File tui/build_exe.ps1
# Output: tui/dist/nf.exe (single file; intermediates in tui/build/, not committed)
# Rule  : run --selftest on the source first, then on the frozen artifact.
# NOTE  : this file stays ASCII-only on purpose - Windows PowerShell 5.1 reads
#         .ps1 as the local ANSI codepage, so non-ASCII here would break parsing.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $here
try {
    Write-Host "[1/3] selftest (source)"
    python nf.py --selftest
    if ($LASTEXITCODE -ne 0) { throw "source selftest failed (exit $LASTEXITCODE)" }

    # Build intermediates go to the system temp dir, never into the repo: the
    # public-surface gate scans the working tree, and PyInstaller writes absolute
    # build paths into build/*/warn-*.txt.
    $work = Join-Path $env:TEMP ("nf-tui-build-" + [guid]::NewGuid().ToString("N").Substring(0, 8))

    Write-Host "[2/3] PyInstaller onefile (work dir: $work)"
    python -m PyInstaller --noconfirm --clean --onefile --name nf `
        --distpath dist --workpath $work --specpath $work nf.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

    Write-Host "[3/3] selftest (artifact)"
    & "$here\dist\nf.exe" --version
    & "$here\dist\nf.exe" --selftest
    if ($LASTEXITCODE -ne 0) { throw "artifact selftest failed (exit $LASTEXITCODE)" }
    Write-Host "done: $here\dist\nf.exe"
}
finally {
    Pop-Location
}
