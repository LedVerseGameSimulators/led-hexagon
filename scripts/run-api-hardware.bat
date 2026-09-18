@echo off
REM Launches the Hexagon API with physical floor hardware enabled.
cd /d "%~dp0.."
set USE_SERIAL_HD=1
set API_PORT=8004
echo.
echo [LED Hexagon API] HARDWARE MODE ON  USE_SERIAL_HD=%USE_SERIAL_HD%
echo Floor LEDs + sensors enabled. Keep this window open.
echo.
python -m uvicorn api.main:app --host 0.0.0.0 --port 8004
echo.
echo API stopped.
pause
