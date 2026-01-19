@echo off
title Newsletter Web App
cd /d "%~dp0"

echo Starting Newsletter Web App...
echo ------------------------------

if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "venv\Scripts\activate.bat"
)

echo Running web_app.py...
python -X utf8 web_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 'python' command failed. Trying 'py' launcher...
    py -3 -X utf8 web_app.py
)

echo.
echo ==========================================
echo Server stopped. Please check errors above.
echo ==========================================
pause
