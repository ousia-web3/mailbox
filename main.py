import schedule
import time
import logging
import os
from datetime import datetime
from newsletter_system import NewsletterSystem
from weekly_generator import WeeklyNewsletterGenerator
from monthly_generator import MonthlyNewsletterGenerator
from date_utils import is_business_day, get_first_business_day

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_daily_newsletter():
    """데일리 뉴스레터 실행"""
    try:
        logger.info("데일리 뉴스레터 작업 시작")
        system = NewsletterSystem()
        success = system.generate_newsletter()
        if success:
            logger.info("데일리 뉴스레터 발송 성공")
        else:
            logger.error("데일리 뉴스레터 발송 실패")
    except Exception as e:
        logger.error(f"데일리 뉴스레터 실행 중 오류: {e}")

def run_weekly_newsletter():
    """주간 뉴스레터 실행"""
    try:
        logger.info("주간 뉴스레터 작업 시작")
        generator = WeeklyNewsletterGenerator()
        success = generator.generate_weekly_newsletter()
        if success:
            logger.info("주간 뉴스레터 발송 성공")
        else:
            logger.error("주간 뉴스레터 발송 실패")
    except Exception as e:
        logger.error(f"주간 뉴스레터 실행 중 오류: {e}")

def run_monthly_newsletter_check():
    """월간 뉴스레터 실행 체크 (매일 실행되지만 첫 영업일에만 발송)"""
    try:
        today = datetime.now()
        first_business_day = get_first_business_day(today.year, today.month)
        
        # 오늘 날짜만 비교 (시간 제외)
        if today.date() == first_business_day.date():
            logger.info(f"오늘은 {today.month}월의 첫 영업일입니다. 월간 뉴스레터를 발송합니다.")
            generator = MonthlyNewsletterGenerator()
            success = generator.generate_monthly_newsletter()
            if success:
                logger.info("월간 뉴스레터 발송 성공")
            else:
                logger.error("월간 뉴스레터 발송 실패")
        else:
            # 첫 영업일이 아니면 스킵
            pass
            
    except Exception as e:
        logger.error(f"월간 뉴스레터 체크 중 오류: {e}")

def main():
    logger.info("뉴스레터 스케줄러 시작")
    
    # 1. 데일리 뉴스레터: 매일 09:00
    schedule.every().day.at("09:00").do(run_daily_newsletter)
    
    # 2. 주간 뉴스레터: 매주 월요일 09:00
    schedule.every().monday.at("09:00").do(run_weekly_newsletter)
    
    # 3. 월간 뉴스레터: 매월 첫 영업일 09:00 (매일 체크)
    schedule.every().day.at("09:00").do(run_monthly_newsletter_check)
    
    logger.info("스케줄 등록 완료:")
    logger.info("- 데일리: 매일 09:00")
    logger.info("- 주간: 매주 월요일 09:00")
    logger.info("- 월간: 매월 첫 영업일 09:00")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("스케줄러 종료 요청됨")
            break
        except Exception as e:
            logger.error(f"스케줄러 루프 중 오류: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
