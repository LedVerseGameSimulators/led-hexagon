@echo off
REM ═══════════════════════════════════════════════════════════════
REM  LED Hex — Windows Setup + Run (SOURCE mode, full debug output)
REM
REM  Use this INSTEAD of the .exe when debugging.
REM  You'll see the exact Python error in this window.
REM
REM  Requirements: Python 3.12 installed from https://python.org
REM  Run once to set up, then just double-click again to run.
REM ═══════════════════════════════════════════════════════════════

setlocal

REM ── Check Python ────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.12 from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo Python found:
python --version

REM ── Create venv if not exists ───────────────────────────────────
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 ( echo ERROR creating venv & pause & exit /b 1 )
)

REM ── Activate venv ───────────────────────────────────────────────
call .venv\Scripts\activate.bat

REM ── Install dependencies if not installed ───────────────────────
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [2/3] Installing dependencies (first time only, ~2 min)...
    pip install --upgrade pip --quiet
    pip install pygame pillow --quiet
    pip install fastapi "uvicorn[standard]" websockets starlette anyio --quiet
    pip install moviepy --quiet
    pip install pycryptodome rsa --quiet
    pip install loguru --quiet
    pip install pyserial --quiet
    pip install pynput --quiet
    echo Dependencies installed.
)

REM ── Run the game ────────────────────────────────────────────────
echo.
echo [3/3] Starting LED Hex game...
echo ────────────────────────────────────────────────────────────
echo  If it crashes, THE ERROR WILL APPEAR ABOVE THIS LINE.
echo  Screenshot or copy the red error text and send it for fixing.
echo ────────────────────────────────────────────────────────────
echo.

python run_simulator.py

echo.
echo ════════════════════════════════════════════════════════════
echo  Game exited. If you see an error above, that is the bug.
echo ════════════════════════════════════════════════════════════
pause
