@echo off
REM ============================================================
REM  LED Hexagon - ONE-CLICK START (studio operator)
REM ============================================================
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

if not defined ACTIVERSE_KIOSK set "ACTIVERSE_KIOSK=1"

title LED Hexagon - Starting
color 0A
echo.
echo  ========================================
echo   LED Hexagon - starting...
echo   Mode: HARDWARE + simulator
echo  ========================================
echo.

set "PATH=C:\Program Files\nodejs;%PATH%"
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

where python >nul 2>&1
if errorlevel 1 (
  if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
  ) else (
    echo  ERROR: Python was not found. Ask tech to run SETUP_FIRST_TIME.bat
    goto :fail
  )
)

where npm >nul 2>&1
if errorlevel 1 (
  echo  ERROR: npm was not found. Ask tech to run SETUP_FIRST_TIME.bat
  goto :fail
)

if not exist "%ROOT%\games\setting\led_parameter.dat" goto :copy_settings
goto :after_settings

:copy_settings
if not exist "D:\ledhexagonv010109\ledhexagon\setting\led_parameter.dat" (
  echo  ERROR: Floor settings missing: games\setting\led_parameter
  goto :fail
)
echo  Copying floor settings from D drive...
if not exist "%ROOT%\games\setting" mkdir "%ROOT%\games\setting"
copy /Y "D:\ledhexagonv010109\ledhexagon\setting\*" "%ROOT%\games\setting" >nul
if errorlevel 1 goto :fail

:after_settings
REM Prefer Python 3.11 when both 3.11 and 3.12 are installed
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
  set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;%PATH%"
)

echo  Checking Python packages...
python -c "import fastapi, uvicorn, httpx, serial" >nul 2>&1
if errorlevel 1 (
  echo  Installing Python packages - first time...
  python -m pip install -r "%ROOT%\api\requirements.txt"
  if errorlevel 1 goto :fail
)

if exist "%ROOT%\frontend\node_modules" goto :after_npm
echo  First run: installing UI packages...
pushd "%ROOT%\frontend"
call npm install
if errorlevel 1 (
  popd
  goto :fail
)
popd

:after_npm
if not exist "%ROOT%\frontend\.env" (
  if exist "%ROOT%\frontend\.env.example" (
    copy /Y "%ROOT%\frontend\.env.example" "%ROOT%\frontend\.env" >nul
    echo  Created frontend\.env — confirm RFID IP if needed.
  )
)

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

echo  Stopping any previous game session...
call "%ROOT%\STOP_GAME.bat" /quiet
ping -n 3 127.0.0.1 >nul

echo  Starting floor engine with HARDWARE mode (API port 8004)...
start "LED Hexagon API" /MIN /D "%ROOT%" cmd /k "call scripts\run-api-hardware.bat"
ping -n 4 127.0.0.1 >nul

echo  Starting bridge (port 8767)...
start "LED Hexagon Bridge" /MIN /D "%ROOT%" cmd /k "python ws_bridge.py"
ping -n 3 127.0.0.1 >nul

echo  Starting game UI (port 5177)...
set "WINDOW_TITLE_UI=LED Hexagon UI"
call "%ROOT%\scripts\kiosk\run-ui-prod.bat" 5177
if errorlevel 1 goto :fail
ping -n 5 127.0.0.1 >nul

echo  Waiting for the UI...
set /a _tries=0

:waitui
set /a _tries+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:5177/; if ($r.StatusCode -ge 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto :uiready
if !_tries! GEQ 30 (
  echo  WARNING: UI did not respond in time. Opening browser anyway.
  goto :check_hw
)
ping -n 2 127.0.0.1 >nul
goto :waitui

:uiready
echo  UI is ready.

:check_hw
echo  Checking hardware mode...
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://localhost:8004/hw-debug' -TimeoutSec 5; if ($r.use_serial_hd) { Write-Host 'HARDWARE MODE: ON' } else { Write-Host 'ERROR: HARDWARE MODE OFF - floor will stay dark'; exit 2 } } catch { Write-Host 'WARNING: could not confirm hardware mode yet'; exit 0 }"
if errorlevel 2 goto :fail

call "%ROOT%\scripts\kiosk\open-ui.bat" 5177 hexagon

echo.
echo  ========================================
echo   LED Hexagon is running (HARDWARE)
echo   Open:  http://127.0.0.1:5177/
echo   Ctrl+Shift+K exits fullscreen kiosk
echo   To stop: double-click STOP_GAME.bat
echo  ========================================
echo.
exit /b 0

:fail
echo.
echo  Start failed. See OPERATOR_GUIDE.md or run SETUP_FIRST_TIME.bat
pause
exit /b 1
