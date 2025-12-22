@echo off
chcp 65001 >nul
title Stop Newsletter Servers (UTF-8)

cd /d "%~dp0"

echo.
echo ========================================
echo    Stopping Newsletter Servers
echo ========================================
echo.

echo 🔎 백엔드 프로세스 종료 중...(web_app.py, newsletter_system.py)
wmic process where "name='python.exe' and CommandLine like '%%web_app.py%%'" call terminate >nul 2>&1
wmic process where "name='py.exe' and CommandLine like '%%web_app.py%%'" call terminate >nul 2>&1
wmic process where "name='python.exe' and CommandLine like '%%newsletter_system.py%%'" call terminate >nul 2>&1
wmic process where "name='py.exe' and CommandLine like '%%newsletter_system.py%%'" call terminate >nul 2>&1

echo 🧹 잔여 파이썬 프로세스 정리(필요 시)
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM py.exe /F >nul 2>&1

echo 🪟 배치로 띄운 콘솔 창 정리("Newsletter System" 제목)
taskkill /FI "WINDOWTITLE eq Newsletter System" /F >nul 2>&1

echo.
echo ✅ 백엔드 및 콘솔 창 종료 완료
echo.
exit /b 0



