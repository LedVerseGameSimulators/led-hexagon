@echo off
REM ============================================================
REM  LED Hexagon - STOP everything
REM  Double-click this file to shut down the game cleanly.
REM  (START_GAME.bat also calls this with /quiet before relaunch.)
REM ============================================================
setlocal EnableExtensions
cd /d "%~dp0"

set "QUIET=0"
if /I "%~1"=="/quiet" set "QUIET=1"

if "%QUIET%"=="0" (
  echo.
  echo  Stopping LED Hexagon...
  echo.
)

REM Close the three service windows by title
taskkill /FI "WINDOWTITLE eq LED Hexagon API*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq LED Hexagon Bridge*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq LED Hexagon UI*" /T /F >nul 2>&1

REM Also free the ports in case a window was already closed
call :killport 8004
call :killport 8767
call :killport 5177

if "%QUIET%"=="0" (
  echo.
  echo  LED Hexagon stopped.
  echo  If tiles stayed lit, start once more, use Stop in the UI,
  echo  then run STOP_GAME.bat again.
  echo.
  ping -n 3 127.0.0.1 >nul
)
exit /b 0

:killport
set "PORT=%~1"
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":%PORT% " ^| findstr LISTENING') do (
  if not "%%P"=="0" (
    taskkill /F /PID %%P >nul 2>&1
  )
)
exit /b 0
