@echo off
title Newsletter System
cd /d "%~dp0"

echo ========================================
echo    Newsletter System Start
echo ========================================
echo.

REM Check for Scheduler execution
set "IS_SCHEDULER=0"
if "%1"=="--scheduler" set "IS_SCHEDULER=1"

if "%IS_SCHEDULER%"=="1" (
    echo [INFO] Running in Scheduler Mode...
    if not exist "logs" mkdir logs
    echo [%date% %time%] Newsletter System Start (Scheduler) >> logs\scheduler.log
)

REM Activate Virtual Environment if exists
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "venv\Scripts\activate.bat"
)

REM Run Python Script
echo [INFO] Running newsletter_system.py...

if "%IS_SCHEDULER%"=="1" (
    python -X utf8 -u newsletter_system.py >> logs\scheduler.log 2>&1
) else (
    python -X utf8 -u newsletter_system.py
)

REM Fallback to 'py' launcher if 'python' fails
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARN] 'python' command failed. Trying 'py' launcher...
    if "%IS_SCHEDULER%"=="1" (
        py -3 -X utf8 -u newsletter_system.py >> logs\scheduler.log 2>&1
    ) else (
        py -3 -X utf8 -u newsletter_system.py
    )
)

if "%IS_SCHEDULER%"=="1" (
    echo [%date% %time%] System finished. >> logs\scheduler.log
) else (
    echo.
    echo ========================================
    echo    System Finished.
    echo ========================================
    echo.
    pause
)
