#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트 뉴스레터 실행 스크립트
"""

import json
import os
from datetime import datetime
from newsletter_system import NewsletterSystem

def test_newsletter():
    """테스트 뉴스레터 발송"""
    
    print("=" * 60)
    print("📧 테스트 뉴스레터 발송 시작")
    print("=" * 60)
    
    try:
        # 1. 테스트용 수신자 설정 로드
        test_recipients_file = 'test_recipient.json'
        if not os.path.exists(test_recipients_file):
            print(f"❌ 테스트 수신자 파일이 없습니다: {test_recipients_file}")
            return False
        
        with open(test_recipients_file, 'r', encoding='utf-8') as f:
            test_config = json.load(f)
        
        test_recipients = test_config['recipients']
        print(f"✅ 테스트 수신자 로드 완료: {len(test_recipients)}명")
        
        for recipient in test_recipients:
            print(f"   📧 {recipient['email']} ({recipient['name']})")
        
        # 2. 뉴스레터 시스템 초기화
        print("\n🔄 뉴스레터 시스템 초기화 중...")
        newsletter_system = NewsletterSystem()
        
        # 3. 테스트용 수신자로 설정 변경
        print("📝 테스트용 수신자로 설정 변경...")
        test_emails = [recipient['email'] for recipient in test_recipients]
        newsletter_system.email_sender.receiver_emails = test_emails
        print(f"✅ 테스트 수신자 설정 완료: {test_emails}")
        
        # 4. 뉴스 수집 및 뉴스레터 생성
        print("\n📰 뉴스 수집 및 뉴스레터 생성 시작...")
        success = newsletter_system.generate_newsletter()
        
        if success:
            print("\n✅ 테스트 뉴스레터 발송 완료!")
            print(f"📧 발송 대상: {len(test_recipients)}명")
            for recipient in test_recipients:
                print(f"   ✅ {recipient['email']} - 발송 완료")
        else:
            print("\n❌ 테스트 뉴스레터 발송 실패!")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 실행 함수"""
    print(f"🚀 테스트 뉴스레터 실행 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 테스트 실행
    success = test_newsletter()
    
    if success:
        print("\n🎉 테스트 완료! 메일함을 확인해주세요.")
    else:
        print("\n💥 테스트 실패! 로그를 확인해주세요.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
