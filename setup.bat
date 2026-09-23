@echo off
REM CloudContextGuard - project setup (Step 1: portable foundation).
REM The project root is this script's own folder, so it keeps working
REM after the project is moved. No absolute paths are hardcoded.
setlocal

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ========================================
echo CloudContextGuard - Setup
echo ========================================
echo Project root: "%PROJECT_ROOT%"
echo.

where python >nul 2>nul
if errorlevel 1 goto :no_python

echo Creating required project directories...
python "%PROJECT_ROOT%\backend\app\core\paths.py"
if errorlevel 1 goto :failed

echo.
echo Setup complete. Backend/frontend dependencies will be added in later steps.
endlocal
exit /b 0

:no_python
echo [ERROR] Python was not found on PATH. Install Python 3.10+ and re-run setup.bat.
endlocal
exit /b 1

:failed
echo [ERROR] Directory setup failed.
endlocal
exit /b 1
