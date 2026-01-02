@echo off
chcp 65001 >nul
title Weekly Newsletter Generator

echo ========================================
echo    Weekly Newsletter System Start
echo ========================================
echo.
echo 🚀 주간 뉴스레터 생성을 시작합니다...
echo 📊 지난주 데이터를 취합하여 AI 큐레이션을 진행합니다.
echo.

:: 파이썬 실행
python weekly_generator.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 주간 뉴스레터 발송이 완료되었습니다!
) else (
    echo.
    echo ❌ 오류가 발생했습니다. 로그를 확인해주세요.
)

echo.
pause
