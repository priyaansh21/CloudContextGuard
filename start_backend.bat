@echo off
REM CloudContextGuard - start backend.
REM The project root is this script's own folder; no absolute paths are hardcoded.
setlocal

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ========================================
echo CloudContextGuard - Backend
echo ========================================
echo Project root: "%PROJECT_ROOT%"
echo Backend dir:  "%PROJECT_ROOT%\backend"
echo.

if not exist "%PROJECT_ROOT%\backend\.venv\Scripts\python.exe" goto :no_venv

"%PROJECT_ROOT%\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir "%PROJECT_ROOT%\backend"

endlocal
exit /b 0

:no_venv
echo [ERROR] backend\.venv not found. Create it and install backend\requirements.txt first.
endlocal
exit /b 1
