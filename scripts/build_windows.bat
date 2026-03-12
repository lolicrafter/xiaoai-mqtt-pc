@echo off
setlocal

cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
)

call ".venv\Scripts\python.exe" -m pip install --upgrade pip
call ".venv\Scripts\python.exe" -m pip install -e ".[dev,build]"
call ".venv\Scripts\pyinstaller.exe" "packaging\xiaoai_desktop.spec" --noconfirm --clean

echo.
echo 打包完成，产物目录：dist\XiaoAiDesktop
endlocal
