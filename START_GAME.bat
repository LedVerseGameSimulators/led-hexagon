@echo off
REM ============================================================
REM  LED Hexagon - ONE-CLICK START (studio operator)
REM  Double-click this file. Do not edit unless asked by tech.
REM ============================================================
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title LED Hexagon Launcher
color 0A
echo.
echo  ========================================
echo   LED Hexagon - starting...
echo  ========================================
echo.

set "PATH=C:\Program Files\nodejs;%PATH%"
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

where python >nul 2>&1
if errorlevel 1 (
  echo  ERROR: Python was not found.
  echo  Ask tech to install Python 3.11+ and add it to PATH.
  goto :fail
)

where node >nul 2>&1
if errorlevel 1 (
  echo  ERROR: Node.js was not found.
  echo  Ask tech to install Node.js LTS from https://nodejs.org
  goto :fail
)
where npm >nul 2>&1
if errorlevel 1 (
  echo  ERROR: npm was not found. Reinstall Node.js LTS.
  goto :fail
)

if not exist "%ROOT%\games\setting\led_parameter.dat" goto :copy_settings
goto :after_settings

:copy_settings
if not exist "D:\ledhexagonv010109\ledhexagon\setting\led_parameter.dat" (
  echo  ERROR: Floor settings missing: games\setting\led_parameter
  echo  Ask tech to copy the setting folder from the original game install.
  goto :fail
)
echo  Copying floor settings from D drive...
if not exist "%ROOT%\games\setting" mkdir "%ROOT%\games\setting"
copy /Y "D:\ledhexagonv010109\ledhexagon\setting\*" "%ROOT%\games\setting" >nul
if errorlevel 1 (
  echo  ERROR: Could not copy floor settings.
  goto :fail
)

:after_settings
if exist "%ROOT%\frontend\node_modules" goto :after_npm
echo  First run: installing UI packages (may take a minute)...
pushd "%ROOT%\frontend"
call npm install
if errorlevel 1 (
  echo  ERROR: npm install failed.
  popd
  goto :fail
)
popd

:after_npm
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

echo  Stopping any previous game session...
call "%ROOT%\STOP_GAME.bat" /quiet
ping -n 3 127.0.0.1 >nul

echo  Starting floor engine (API)...
start "LED Hexagon API" cmd /k "cd /d %ROOT% && set USE_SERIAL_HD=1&& set API_PORT=8004&& python -m uvicorn api.main:app --host 0.0.0.0 --port 8004"
ping -n 4 127.0.0.1 >nul

echo  Starting bridge...
start "LED Hexagon Bridge" cmd /k "cd /d %ROOT% && set API_PORT=8004&& set WS_BRIDGE_PORT=8767&& python ws_bridge.py"
ping -n 3 127.0.0.1 >nul

echo  Starting game UI...
start "LED Hexagon UI" cmd /k "cd /d %ROOT%\frontend && set PATH=C:\Program Files\nodejs;%PATH%&& npm run dev"
echo.
echo  Waiting for the UI to become ready...

set /a _tries=0
:waitui
set /a _tries+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:5177/; if ($r.StatusCode -ge 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto :uiready
if !_tries! GEQ 45 (
  echo  WARNING: UI did not respond in time. Opening browser anyway.
  goto :openbrowser
)
ping -n 2 127.0.0.1 >nul
goto :waitui

:uiready
echo  UI is ready.

:openbrowser
echo.
echo  ========================================
echo   LED Hexagon is running
echo   Open:  http://localhost:5177
echo  ========================================
echo.
echo  When finished, double-click STOP_GAME.bat
echo.
start "" "http://localhost:5177/"
ping -n 3 127.0.0.1 >nul
exit /b 0

:fail
echo.
echo  Start failed. See messages above, then ask tech for help.
echo.
pause
exit /b 1
