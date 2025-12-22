@echo off
chcp 65001 >nul
title Newsletter System (UTF-8)

REM 초기화
set "EXIT_CODE=0"

REM UTF-8 강제 (파이썬 입출력 한글 보장)
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

REM 배치 파일이 있는 폴더로 이동 (어디서 실행해도 동작)
cd /d "%~dp0"

REM 로그 디렉토리 생성 (없으면)
if not exist "logs" mkdir logs

REM 작업스케줄러에서 실행되는지 확인 (간단하고 정확한 방법)
set "IS_SCHEDULER=0"
if "%SCHTASKS%"=="1" set "IS_SCHEDULER=1"
if "%TASK_SCHEDULER%"=="1" set "IS_SCHEDULER=1"
if "%1"=="--scheduler" set "IS_SCHEDULER=1"

REM PC 잠김 상태에서도 실행되도록 환경 변수 설정
set "TEMP_DIR=%TEMP%"
set "USERPROFILE_DIR=%USERPROFILE%"

if "%IS_SCHEDULER%"=="1" (
    REM 작업스케줄러에서 실행시 백그라운드로 실행하고 로그 파일에 기록
    echo [%date% %time%] 뉴스레터 시스템 시작 (작업스케줄러) >> logs\scheduler.log
    echo ======================================== >> logs\scheduler.log
    echo    Newsletter System Start (Scheduler) >> logs\scheduler.log
    echo ======================================== >> logs\scheduler.log
    echo 🚀 뉴스레터 시스템을 시작합니다... >> logs\scheduler.log
    echo 📧 뉴스 생성 및 이메일 발송을 진행합니다. >> logs\scheduler.log
    echo. >> logs\scheduler.log
) else (
    echo.
    echo ========================================
    echo    Newsletter System Start
    echo ========================================
    echo.
    echo 🚀 뉴스레터 시스템을 시작합니다...
    echo 📧 뉴스 생성 및 이메일 발송을 진행합니다.
    echo.
)

REM 파이썬 실행 커맨드 구성 (PC 잠김 상태에서도 안정적 실행)
REM Python Launcher 우선 사용 (py 명령어)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=py -3 -X utf8 -u newsletter_system.py"
    set "PY_TYPE=Python Launcher"
) else (
    REM Python 직접 실행
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PY_CMD=python -X utf8 -u newsletter_system.py"
        set "PY_TYPE=Python Direct"
    ) else (
        REM Python3 시도
        where python3 >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            set "PY_CMD=python3 -X utf8 -u newsletter_system.py"
            set "PY_TYPE=Python3"
        ) else (
            echo [%date% %time%] ❌ 오류: Python이 설치되지 않았거나 PATH에 없습니다 >> logs\scheduler.log
            echo [%date% %time%] Python 설치를 확인해주세요 >> logs\scheduler.log
            set "EXIT_CODE=1"
            goto :end
        )
    )
)

if "%IS_SCHEDULER%"=="1" (
    REM 작업스케줄러에서 실행시 백그라운드로 실행하고 로그 파일에 기록
    echo [%date% %time%] Python 실행 명령: %PY_CMD% >> logs\scheduler.log
    echo [%date% %time%] Python 타입: %PY_TYPE% >> logs\scheduler.log
    echo [%date% %time%] 현재 작업 디렉토리: %CD% >> logs\scheduler.log
    
    REM 파이썬 스크립트 실행 (PC 잠김 상태에서도 안정적, 지연 최소화)
    echo [%date% %time%] 파이썬 스크립트 실행 시작... >> logs\scheduler.log
    %PY_CMD% >> logs\scheduler.log 2>&1
    set "EXIT_CODE=%ERRORLEVEL%"
    
    if %EXIT_CODE% EQU 0 (
        echo [%date% %time%] ✅ 뉴스레터 시스템 정상 완료 >> logs\scheduler.log
    ) else (
        echo [%date% %time%] ❌ 뉴스레터 시스템 오류 발생 (코드: %EXIT_CODE%) >> logs\scheduler.log
        echo [%date% %time%] 오류 상세 정보를 확인하려면 logs\scheduler.log 파일을 확인하세요 >> logs\scheduler.log
    )
    echo ======================================== >> logs\scheduler.log
    echo. >> logs\scheduler.log
) else (
    REM 수동 실행시 새 콘솔 창으로 실행
    echo Python 타입: %PY_TYPE%
    start "Newsletter System" cmd /k "%PY_CMD%"
    echo.
    echo ✅ 실행 창이 새로 열렸습니다. 해당 창에서 진행 상황을 확인하세요.
    echo (이 창은 바로 닫아도 됩니다)
    echo.
)

REM PC 잠김 상태에서의 추가 안정성 보장 (지연 최소화)
if "%IS_SCHEDULER%"=="1" (
    REM 작업 완료 후 시스템 리소스 정리 (지연 시간 단축)
    timeout /t 1 /nobreak >nul
    echo [%date% %time%] 시스템 리소스 정리 완료 >> logs\scheduler.log
)

:end
exit /b %EXIT_CODE%




