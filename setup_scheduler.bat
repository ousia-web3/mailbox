@echo off
title Task Scheduler Setup Tool
cd /d "%~dp0"

echo ========================================
echo    Task Scheduler Setup Tool
echo ========================================
echo.

REM Check Current User
echo Current User: %USERNAME%
echo.

echo Setting up Newsletter Task in Scheduler...
echo.

REM Delete existing task
schtasks /delete /tn "NewsletterSystem" /f >nul 2>&1

REM Create new task
REM Runs daily at 09:00, with highest privileges
schtasks /create /tn "NewsletterSystem" /tr "\"%~dp0run_newsletter.bat\" --scheduler" /sc daily /st 09:00 /ru "%USERNAME%" /rl highest /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Task Scheduler setup complete!
    echo.
    echo Settings:
    echo - Task Name: NewsletterSystem
    echo - Time: Daily 09:00
    echo - File: %~dp0run_newsletter.bat
    echo.
    echo Logs will be saved to: logs\scheduler.log
) else (
    echo.
    echo [ERROR] Failed to setup Task Scheduler.
    echo Please run as Administrator.
)

echo.
echo Checking Task Status:
schtasks /query /tn "NewsletterSystem" /fo list 2>nul

echo.
pause
