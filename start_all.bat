@echo off
REM CloudContextGuard - start backend and frontend.
REM The project root is this script's own folder; no absolute paths are hardcoded.
setlocal

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ========================================
echo CloudContextGuard - Start All
echo ========================================
echo Project root: "%PROJECT_ROOT%"
echo.
echo Opening the backend and frontend each in their own window...

start "CloudContextGuard Backend" cmd /k "%PROJECT_ROOT%\start_backend.bat"
start "CloudContextGuard Frontend" cmd /k "%PROJECT_ROOT%\start_frontend.bat"

endlocal
exit /b 0
