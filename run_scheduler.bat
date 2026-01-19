@echo off
title Run Scheduler
cd /d "%~dp0"

echo ========================================
echo    Run Scheduler Manually
echo ========================================
echo.

REM Activate Virtual Environment if exists
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "venv\Scripts\activate.bat"
)

REM Run Python Script
echo [INFO] Running main.py...
python main.py

REM Fallback to 'py' launcher if 'python' fails
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARN] 'python' command failed. Trying 'py' launcher...
    py -3 main.py
)

echo.
echo ========================================
echo    Finished.
echo ========================================
pause
