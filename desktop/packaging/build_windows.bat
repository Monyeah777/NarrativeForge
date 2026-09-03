@echo off
REM Windows 构建：产物 dist\NarrativeForge.exe
REM 用法：在 Windows（已装 Python 3.10+ 且勾选 py launcher）双击或 cmd 执行本文件
cd /d "%~dp0.."

echo ==^> 安装/升级 PyInstaller
py -m pip install --upgrade pyinstaller
if errorlevel 1 exit /b 1

echo ==^> 执行打包
py -m PyInstaller --noconfirm packaging\narrative_forge.spec
if errorlevel 1 exit /b 1

echo.
echo ==^> 产物：dist\NarrativeForge.exe
echo     运行：dist\NarrativeForge.exe
