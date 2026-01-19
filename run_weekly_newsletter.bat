@echo off
title Weekly Newsletter Generator
cd /d "%~dp0"

echo ========================================
echo    Weekly Newsletter System Start
echo ========================================
echo.

REM Activate Virtual Environment if exists
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "venv\Scripts\activate.bat"
)

REM Run Python Script
echo [INFO] Running weekly_generator.py...
python weekly_generator.py

REM Fallback to 'py' launcher if 'python' fails
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARN] 'python' command failed. Trying 'py' launcher...
    py -3 weekly_generator.py
)

echo.
echo ========================================
echo    Finished.
echo ========================================
pause
