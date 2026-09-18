@echo off
REM ============================================================
REM  LED Hexagon - STOP everything
REM  Double-click this file to shut down the game cleanly.
REM  (START_GAME.bat also calls this with /quiet before relaunch.)
REM ============================================================
setlocal EnableExtensions
cd /d "%~dp0"

set "QUIET=%~1"
if /i not "%QUIET%"=="/quiet" (
  title LED Hexagon - Stopping
  echo.
  echo  ========================================
  echo   LED Hexagon - Stopping game
  echo  ========================================
  echo.
)

REM Kill by window titles started by START_GAME.bat
taskkill /FI "WINDOWTITLE eq LED Hexagon API*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq LED Hexagon Bridge*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq LED Hexagon UI*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq LED Hexagon Frontend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Activerse Kiosk Exit*" /T /F >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\kiosk\kill-kiosk-browser.ps1" -ProfileSlug hexagon

REM Also free ports (works even if window titles differ)
powershell -NoProfile -Command ^
  "foreach ($p in 8004,8767,5177) { Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }" >nul 2>&1

if /i "%QUIET%"=="/quiet" (
  endlocal
  exit /b 0
)

echo.
echo  LED Hexagon stopped. Ports 8004 / 8767 / 5177 are free.
echo  You can close this window.
echo.
pause
endlocal
