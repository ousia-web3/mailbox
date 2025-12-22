# Windows 작업 스케줄러 설정 스크립트
# 관리자 권한으로 실행해야 합니다.

param(
    [string]$TaskName = "NewsletterAutoSend",
    [string]$Schedule = "Daily",  # Daily, Weekly, Monthly
    [string]$Time = "09:00",
    [string]$ProjectPath = "C:\Users\hana\Desktop\USER_PJ\mailbox"
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "뉴스레터 자동화 작업 스케줄러 설정" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# BAT 파일 경로 확인
$batFilePath = Join-Path $ProjectPath "run_newsletter.bat"
if (-not (Test-Path $batFilePath)) {
    Write-Host "❌ BAT 파일을 찾을 수 없습니다: $batFilePath" -ForegroundColor Red
    Write-Host "먼저 run_newsletter.bat 파일을 생성해주세요." -ForegroundColor Red
    exit 1
}

Write-Host "✅ BAT 파일 확인됨: $batFilePath" -ForegroundColor Green

# 기존 작업이 있는지 확인하고 삭제
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "기존 작업을 삭제합니다: $TaskName" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# 작업 실행자 설정 (작업스케줄러 모드로 실행)
$action = New-ScheduledTaskAction -Execute $batFilePath -WorkingDirectory $ProjectPath -Argument "--scheduler"

# 트리거 설정
switch ($Schedule.ToLower()) {
    "daily" {
        $trigger = New-ScheduledTaskTrigger -Daily -At $Time
        Write-Host "매일 $Time 에 실행되도록 설정합니다." -ForegroundColor Green
    }
    "weekly" {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $Time
        Write-Host "매주 월요일 $Time 에 실행되도록 설정합니다." -ForegroundColor Green
    }
    "monthly" {
        $trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At $Time
        Write-Host "매월 1일 $Time 에 실행되도록 설정합니다." -ForegroundColor Green
    }
    default {
        $trigger = New-ScheduledTaskTrigger -Daily -At $Time
        Write-Host "매일 $Time 에 실행되도록 설정합니다." -ForegroundColor Green
    }
}

# 설정 옵션 (잠김 상태에서도 실행되도록 개선)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# 보안 옵션 (시스템 계정으로 실행하여 잠김 상태에서도 동작)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# 작업 등록
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "뉴스레터 자동 생성 및 발송 (잠김 상태에서도 실행)"
    
    Write-Host "✅ 작업 스케줄러 등록 완료!" -ForegroundColor Green
    Write-Host "작업 이름: $TaskName" -ForegroundColor Cyan
    Write-Host "실행 파일: $batFilePath" -ForegroundColor Cyan
    Write-Host "스케줄: $Schedule at $Time" -ForegroundColor Cyan
    Write-Host "실행 계정: SYSTEM (잠김 상태에서도 실행)" -ForegroundColor Cyan
    Write-Host "로그 파일: $ProjectPath\logs\scheduler.log" -ForegroundColor Cyan
    
    # 작업 상태 확인
    $task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "작업 상태: $($task.State)" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ 작업 스케줄러 등록 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "관리자 권한으로 실행했는지 확인해주세요." -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "설정 완료!" -ForegroundColor Green
Write-Host "작업 스케줄러에서 '$TaskName' 작업을 확인할 수 있습니다." -ForegroundColor Green
Write-Host "잠김 상태에서도 정상 실행됩니다." -ForegroundColor Green
Write-Host "실행 로그는 logs\scheduler.log 파일에서 확인하세요." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green 