import logging
import sys
import os

# 부모 디렉토리를 sys.path에 추가하여 모듈 import 가능하게 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_daily_system():
    logger.info("=== 데일리 뉴스레터 시스템 테스트 ===")
    try:
        from newsletter_system import NewsletterSystem
        system = NewsletterSystem()
        # 전체 프로세스를 돌리면 이메일이 발송되므로, run_test() 메서드를 사용하거나
        # 컴포넌트 초기화만이라도 확인
        logger.info("NewsletterSystem 초기화 성공")
        
        # run_test()가 있다면 실행 (실제 발송 방지를 위해 주석 처리)
        # if hasattr(system, 'run_test'):
        #     system.run_test()
            
        return True
    except Exception as e:
        logger.error(f"데일리 시스템 테스트 실패: {e}")
        return False

def test_weekly_generator():
    logger.info("=== 주간 뉴스레터 생성기 테스트 ===")
    try:
        from weekly_generator import WeeklyNewsletterGenerator
        generator = WeeklyNewsletterGenerator()
        logger.info("WeeklyNewsletterGenerator 초기화 성공")
        
        # 실제 발송은 하지 않고 데이터 로드 부분만 체크해볼 수도 있음
        # 여기서는 초기화 및 import 에러 없는지만 확인
        return True
    except Exception as e:
        logger.error(f"주간 생성기 테스트 실패: {e}")
        return False

def test_monthly_generator():
    logger.info("=== 월간 뉴스레터 생성기 테스트 ===")
    try:
        from monthly_generator import MonthlyNewsletterGenerator
        generator = MonthlyNewsletterGenerator()
        logger.info("MonthlyNewsletterGenerator 초기화 성공")
        return True
    except Exception as e:
        logger.error(f"월간 생성기 테스트 실패: {e}")
        return False

def test_scheduler_logic():
    logger.info("=== 스케줄러 로직 테스트 ===")
    try:
        from date_utils import get_first_business_day, is_business_day
        from datetime import datetime
        
        today = datetime.now()
        first_biz = get_first_business_day(today.year, today.month)
        logger.info(f"이번 달 첫 영업일: {first_biz.strftime('%Y-%m-%d')}")
        logger.info(f"오늘 날짜: {today.strftime('%Y-%m-%d')}")
        logger.info(f"오늘이 영업일인가?: {is_business_day(today)}")
        
        return True
    except Exception as e:
        logger.error(f"스케줄러 로직 테스트 실패: {e}")
        return False

def test_email_sender_single_recipient():
    """EMAIL_RECEIVER에 1명만 지정했을 때 실제 발송 대상이 1명인지 확인"""

    # 테스트용 환경 변수 설정 (dry‑run 활성화)
    os.environ['NEWSLETTER_DRY_RUN'] = '1'
    os.environ['EMAIL_SENDER'] = 'test_sender@example.com'
    os.environ['EMAIL_PASSWORD'] = 'dummy_password'
    os.environ['EMAIL_RECEIVER'] = 'jaemin25@hanatour.com'  # 1명 지정

    from email_sender import EmailSender
    sender = EmailSender()               # 설정 로드
    final_receivers = sender.receiver_emails

    logger.info(f"테스트 설정된 최종 수신자: {final_receivers}")
    assert len(final_receivers) == 1, f"수신자 수가 1이 아니고 {len(final_receivers)}명 입니다"
    # 실제 send_newsletter 호출 (dry run이므로 실제 전송 안 함)
    result = sender.send_newsletter('테스트 제목', '테스트 내용')
    assert result is True, "dry run 모드에서 send_newsletter이 True를 반환해야 함"
    logger.info("EmailSender single recipient 테스트 성공")
    return True

if __name__ == "__main__":
    logger.info("통합 테스트 시작")
    
    results = {
        "daily": test_daily_system(),
        "weekly": test_weekly_generator(),
        "monthly": test_monthly_generator(),
        "scheduler": test_scheduler_logic(),
        "email_single": test_email_sender_single_recipient()
    }
    
    logger.info("=== 테스트 결과 요약 ===")
    all_pass = True
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{name}: {status}")
        if not result:
            all_pass = False
            
    if all_pass:
        logger.info("모든 테스트 통과 ✅")
        sys.exit(0)
    else:
        logger.error("일부 테스트 실패 ❌")
        sys.exit(1)

