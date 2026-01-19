@echo off
title Stop Newsletter Servers
cd /d "%~dp0"

echo ========================================
echo    Stopping Newsletter Servers
echo ========================================
echo.

echo [INFO] Terminating Python processes (web_app.py, newsletter_system.py)...

REM Terminate specific python processes
wmic process where "name='python.exe' and CommandLine like '%%web_app.py%%'" call terminate >nul 2>&1
wmic process where "name='py.exe' and CommandLine like '%%web_app.py%%'" call terminate >nul 2>&1
wmic process where "name='python.exe' and CommandLine like '%%newsletter_system.py%%'" call terminate >nul 2>&1
wmic process where "name='py.exe' and CommandLine like '%%newsletter_system.py%%'" call terminate >nul 2>&1

echo [INFO] Cleaning up remaining processes...
taskkill /IM python.exe /F >nul 2>&1
taskkill /IM py.exe /F >nul 2>&1

echo [INFO] Closing console windows...
taskkill /FI "WINDOWTITLE eq Newsletter System" /F >nul 2>&1

echo.
echo [SUCCESS] Servers stopped.
echo.
pause
