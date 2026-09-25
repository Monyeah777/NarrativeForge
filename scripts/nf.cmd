@echo off
rem NF 终端启动器（Windows）：无参数 = 直接进交互终端，其余参数原样透传 nf CLI。
rem 用法：scripts\nf.cmd [shell|doctor|assemble ...]
setlocal
set "NF_ROOT=%~dp0"
if "%~1"=="" (
  python "%NF_ROOT%nf.py" shell
) else (
  python "%NF_ROOT%nf.py" %*
)
endlocal
