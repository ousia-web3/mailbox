import sys
import os

# 부모 디렉토리를 sys.path에 추가하여 모듈 import 가능하게 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from newsletter_system import NewsletterSystem
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)

def run_test():
    print("뉴스레터 생성 및 발송 테스트 시작...")
    system = NewsletterSystem()
    success = system.generate_newsletter()
    
    if success:
        print("✅ 테스트 성공: 뉴스레터가 생성되고 발송되었습니다.")
    else:
        print("❌ 테스트 실패: 뉴스레터 생성 또는 발송 중 오류가 발생했습니다.")

if __name__ == "__main__":
    run_test()
