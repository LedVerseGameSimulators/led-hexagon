@echo off
REM ═══════════════════════════════════════════════════════════════
REM  LED Hex — Hardware Mode Setup
REM
REM  Run this ONCE to connect the physical LED floor tiles.
REM  It scans COM ports, lets you pick the right one, and
REM  enables hardware mode in the app.
REM
REM  After running this, use setup_and_run_windows.bat to start.
REM  To go back to simulator-only: setup_hardware.bat --disable
REM ═══════════════════════════════════════════════════════════════

setlocal

REM ── Activate venv if present ────────────────────────────────────
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM ── Pass any command-line arguments through (--status, --disable)
python setup_hardware.py %*

pause
