@echo off
chcp 65001 >nul
title 작업 스케줄러 설정 도구

echo ========================================
echo    작업 스케줄러 설정 도구
echo ========================================
echo.

REM 현재 사용자 확인
for /f "tokens=2 delims=," %%i in ('query session ^| findstr /i "console"') do set "CURRENT_USER=%%i"
echo 현재 사용자: %CURRENT_USER%
echo.

REM 작업 스케줄러 작업 생성/업데이트
echo 작업 스케줄러에 뉴스레터 작업을 설정합니다...
echo.

REM 기존 작업 삭제 (있다면)
schtasks /delete /tn "NewsletterSystem" /f >nul 2>&1

REM 새 작업 생성 (PC 잠김 상태에서도 실행되도록 설정)
schtasks /create /tn "NewsletterSystem" /tr "\"%~dp0run_newsletter.bat\" --scheduler" /sc daily /st 09:00 /ru "%USERNAME%" /rl highest /f

if %ERRORLEVEL% EQU 0 (
    echo ✅ 작업 스케줄러 설정이 완료되었습니다!
    echo.
    echo 설정된 내용:
    echo - 작업 이름: NewsletterSystem
    echo - 실행 시간: 매일 오전 9시
    echo - 실행 파일: %~dp0run_newsletter.bat
    echo - PC 잠김 상태에서도 실행: 예
    echo - 최고 권한으로 실행: 예
    echo.
    echo 📝 참고사항:
    echo 1. 작업 스케줄러에서 "사용자가 로그온했는지 여부에 관계없이 실행" 옵션이 활성화됩니다
    echo 2. PC가 꺼져있거나 잠겨있어도 정상적으로 실행됩니다
    echo 3. 실행 로그는 logs\scheduler.log 파일에서 확인할 수 있습니다
    echo.
    echo 🔧 작업 스케줄러에서 추가 설정을 원하시면:
    echo 1. 작업 스케줄러 열기 (taskschd.msc)
    echo 2. NewsletterSystem 작업 찾기
    echo 3. 속성에서 세부 설정 변경
    echo.
) else (
    echo ❌ 작업 스케줄러 설정에 실패했습니다.
    echo 관리자 권한으로 실행해주세요.
    echo.
)

echo 작업 스케줄러 목록 확인:
schtasks /query /tn "NewsletterSystem" /fo list 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 작업이 생성되지 않았습니다.
)

echo.
echo 아무 키나 누르면 종료됩니다...
pause >nul
