@echo off
REM CloudContextGuard - start frontend.
REM The project root is this script's own folder; no absolute paths are hardcoded.
setlocal

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ========================================
echo CloudContextGuard - Frontend
echo ========================================
echo Project root: "%PROJECT_ROOT%"
echo Frontend dir: "%PROJECT_ROOT%\frontend"
echo.

if not exist "%PROJECT_ROOT%\frontend\node_modules" goto :no_modules

pushd "%PROJECT_ROOT%\frontend"
call npm run dev
popd

endlocal
exit /b 0

:no_modules
echo [ERROR] frontend\node_modules not found. Run "npm install" in frontend\ first.
endlocal
exit /b 1
