@echo off
chcp 65001
cd /d "%~dp0"

:: 가상환경 활성화 (존재하는 경우)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: 스케줄러 실행 (백그라운드 유지를 위해 python 실행)
echo 뉴스레터 통합 스케줄러를 시작합니다...
python main.py

pause
