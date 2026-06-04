@echo off
REM ─────────────────────────────────────────────────────────────────────────
REM  LED Hex Game — Windows build script
REM  Run this on a Windows machine with Python 3.12 installed.
REM
REM  Requirements:
REM    Python 3.12  (https://www.python.org/downloads/)
REM    Git          (to clone the repo, if needed)
REM
REM  Usage:
REM    1. Open Command Prompt in this folder
REM    2. Run:  build_windows.bat
REM    3. Output will be in:  dist\ledhex\ledhex.exe
REM ─────────────────────────────────────────────────────────────────────────

echo [1/4] Creating virtual environment...
python -m venv .venv_build
call .venv_build\Scripts\activate.bat

echo [2/4] Installing dependencies...
pip install --upgrade pip
pip install pyinstaller
pip install pygame pillow fastapi "uvicorn[standard]" moviepy
pip install pycryptodome rsa loguru pyserial pynput
pip install websockets anyio starlette

echo [3/4] Building executable...
pyinstaller ledhex.spec --clean --noconfirm

echo [4/4] Done!
echo.
echo Output: dist\ledhex\ledhex.exe
echo.
echo To test: cd dist\ledhex ^&^& ledhex.exe
echo.
pause
