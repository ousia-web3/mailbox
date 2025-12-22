@echo off
chcp 65001 >nul
title Newsletter Web App (UTF-8)

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

cd /d "%~dp0"

echo.
echo ========================================
echo    Start Newsletter Web App
echo ========================================
echo.

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=py -3 -X utf8 web_app.py"
) else (
    set "PY_CMD=python -X utf8 web_app.py"
)

echo 🌐 웹 서버를 새 콘솔 창에서 시작합니다...
start "Newsletter Web App" cmd /k "%PY_CMD%"

echo 🔗 브라우저를 열기 전에 잠시 대기합니다...
timeout /t 2 >nul
start "" "http://localhost:5000"

echo.
echo ✅ 웹 앱 실행 및 브라우저 오픈 완료
echo.
exit /b 0



