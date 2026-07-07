@echo off
REM Start Hexagon dev stack (API 8004, ws_bridge 8767, UI 5177).
setlocal
cd /d "%~dp0.."

echo ==^> LED Hexagon dev stack from %CD%

start "LED Hexagon API" cmd /k "cd /d %CD% && set USE_SERIAL_HD=1 && python -m uvicorn api.main:app --host 0.0.0.0 --port 8004"
timeout /t 2 /nobreak >nul
start "LED Hexagon ws_bridge" cmd /k "cd /d %CD% && set API_PORT=8004 && set WS_BRIDGE_PORT=8767 && python ws_bridge.py"
timeout /t 2 /nobreak >nul
start "LED Hexagon Frontend" cmd /k "cd /d %CD%\frontend && npm run dev"

echo.
echo Hexagon ready:
echo   UI:        http://localhost:5177
echo   API:       http://localhost:8004
echo   ws_bridge: http://localhost:8767
echo.
echo Close the three command windows to stop the stack.
endlocal
