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
rem Fast path (2026-10-01): cmd.exe has no built-in socket, so the millisecond client lives in
rem scripts\nf_client.py (stdlib only, run with -S). It hands the command to the resident daemon
rem over 127.0.0.1 and exits 111 when it cannot serve -- then this wrapper falls back to the
rem python direct path. Same contract as the POSIX launcher scripts/nf: fast path only speeds
rem things up, never changes availability. Long-running commands (daemon/shell/terminal/serve/lsp)
rem and "no daemon yet" both take the fallback.
setlocal
set "NF_ROOT=%~dp0"
set "NF_PY=python"
rem Flow is goto-based on purpose: inside a "( ... )" block cmd expands %ERRORLEVEL% when the
rem whole block is parsed, so the rc would be the pre-block value (classic cmd pitfall).
rem No "where python" probe: measured 2026-10-01, that one subprocess costs ~98 ms here (cmd bare
rem 15 ms, "+where" 113 ms) -- more than the entire fast path. Instead: just run, and switch to the
rem "py" launcher only when cmd reports 9009 (program not found).
if "%~1"=="" goto :nf_shell
"%NF_PY%" -S "%NF_ROOT%nf_client.py" %*
set "NF_RC=%ERRORLEVEL%"
if "%NF_RC%"=="9009" goto :nf_use_py
if "%NF_RC%"=="111" goto :nf_direct
goto :nf_done
:nf_use_py
set "NF_PY=py"
"%NF_PY%" -S "%NF_ROOT%nf_client.py" %*
set "NF_RC=%ERRORLEVEL%"
if "%NF_RC%"=="9009" goto :nf_direct
if "%NF_RC%"=="111" goto :nf_direct
goto :nf_done
:nf_direct
rem Fallback: fast path could not serve (no daemon / long-running command / frame mismatch).
"%NF_PY%" "%NF_ROOT%nf.py" %*
set "NF_RC=%ERRORLEVEL%"
goto :nf_done
:nf_shell
"%NF_PY%" "%NF_ROOT%nf.py" shell
set "NF_RC=%ERRORLEVEL%"
if "%NF_RC%"=="9009" goto :nf_shell_py
goto :nf_done
:nf_shell_py
"py" "%NF_ROOT%nf.py" shell
set "NF_RC=%ERRORLEVEL%"
:nf_done
endlocal & exit /b %NF_RC%
