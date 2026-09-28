@echo off
rem NF terminal launcher (Windows cmd). No arguments = interactive shell; others pass
rem straight through to the nf CLI.
rem
rem Usage: scripts\nf.cmd [shell|doctor|assemble ...]
rem
rem KEEP THIS FILE ASCII-ONLY (2026-09 real defect): cmd.exe reads .cmd sources in the
rem OEM code page, so non-ASCII comments get mis-decoded and can split into executable
rem garbage -- the launcher then fails before python is ever reached (observed: rc=255,
rem "'...' is not recognized as an internal or external command"). Same lesson as
rem .github/requirements-ci.txt ("deliberately ASCII-only"). Guarded by a test.
rem
rem Note: the millisecond-class client (daemon socket fast path) is the POSIX launcher
rem scripts/nf plus "eval $(nf daemon shell-init bash)"; cmd.exe has no built-in socket,
rem so this wrapper always takes the python direct path.
setlocal
set "NF_ROOT=%~dp0"
set "NF_PY=python"
where python >nul 2>nul || set "NF_PY=py"
if "%~1"=="" (
  "%NF_PY%" "%NF_ROOT%nf.py" shell
) else (
  "%NF_PY%" "%NF_ROOT%nf.py" %*
)
endlocal
