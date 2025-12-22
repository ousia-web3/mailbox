#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import logging

class SimpleRecipientManager:
    """
    간단한 수신자 관리 클래스
    - JSON 기반 데이터 저장
    - Ctrl+C/V 대량 추가 지원
    - Ctrl+F 검색 기능
    - 실시간 삭제 기능
    """
    
    def __init__(self, data_file: str = "recipients.json"):
        self.data_file = data_file
        self.setup_logging()
        self.recipients = self.load_recipients()
    
    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def load_recipients(self) -> List[Dict]:
        """수신자 데이터 로드"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"수신자 데이터 로드 완료: {len(data)}명")
                    return data
            except Exception as e:
                self.logger.error(f"수신자 데이터 로드 실패: {e}")
                return []
        else:
            self.logger.info("수신자 데이터 파일이 없습니다. 새로 생성합니다.")
            return []
    
    def save_recipients(self):
        """수신자 데이터 저장"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.recipients, f, ensure_ascii=False, indent=2)
            self.logger.info(f"수신자 데이터 저장 완료: {len(self.recipients)}명")
        except Exception as e:
            self.logger.error(f"수신자 데이터 저장 실패: {e}")
            raise
    
    def add_recipient(self, email: str) -> Dict:
        """단일 수신자 추가"""
        email = email.strip()
        
        # 이메일 형식 검증
        if not self.validate_email(email):
            raise ValueError("올바르지 않은 이메일 형식입니다.")
        
        # 중복 확인
        if any(r['email'] == email for r in self.recipients):
            raise ValueError("이미 등록된 이메일입니다.")
        
        recipient = {
            'id': self.generate_id(),
            'email': email,
            'status': 'active',
            'added_date': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
        
        self.recipients.append(recipient)
        self.save_recipients()
        self.logger.info(f"수신자 추가 완료: {email}")
        return recipient
    
    def add_multiple_recipients(self, emails_text: str) -> Dict:
        """대량 수신자 추가 (Ctrl+C/V 텍스트)"""
        # 줄바꿈, 쉼표, 세미콜론으로 구분된 이메일 처리
        emails = []
        for line in emails_text.split('\n'):
            line = line.strip()
            if line:
                # 쉼표나 세미콜론으로 구분된 경우 분리
                for email in re.split(r'[,;]', line):
                    email = email.strip()
                    if email:
                        emails.append(email)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for email in emails:
            try:
                self.add_recipient(email)
                success_count += 1
            except ValueError as e:
                error_count += 1
                errors.append(f"{email}: {str(e)}")
            except Exception as e:
                error_count += 1
                errors.append(f"{email}: 예상치 못한 오류 - {str(e)}")
        
        self.logger.info(f"대량 추가 완료: 성공 {success_count}명, 실패 {error_count}명")
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
    
    def remove_recipient(self, email: str) -> bool:
        """수신자 제거"""
        for i, recipient in enumerate(self.recipients):
            if recipient['email'] == email:
                del self.recipients[i]
                self.save_recipients()
                self.logger.info(f"수신자 제거 완료: {email}")
                return True
        self.logger.warning(f"제거할 수신자를 찾을 수 없음: {email}")
        return False
    
    def search_recipients(self, query: str) -> List[Dict]:
        """수신자 검색 (Ctrl+F 기능)"""
        query = query.lower()
        results = []
        for recipient in self.recipients:
            if query in recipient['email'].lower():
                results.append(recipient)
        self.logger.info(f"검색 결과: '{query}' -> {len(results)}명")
        return results
    
    def get_active_emails(self) -> List[str]:
        """활성 수신자 이메일 목록 반환"""
        active_emails = [r['email'] for r in self.recipients if r['status'] == 'active']
        self.logger.info(f"활성 수신자 수: {len(active_emails)}명")
        return active_emails
    
    def get_all_recipients(self) -> List[Dict]:
        """전체 수신자 목록 반환"""
        return self.recipients
    
    def validate_email(self, email: str) -> bool:
        """이메일 형식 검증"""
        if not email or len(email) > 254:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def generate_id(self) -> str:
        """고유 ID 생성"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_stats(self) -> Dict:
        """수신자 통계"""
        total = len(self.recipients)
        active = len([r for r in self.recipients if r['status'] == 'active'])
        inactive = total - active
        
        stats = {
            'total': total,
            'active': active,
            'inactive': inactive
        }
        
        self.logger.info(f"수신자 통계: 전체 {total}명, 활성 {active}명, 비활성 {inactive}명")
        return stats
    
    def update_recipient_status(self, email: str, status: str) -> bool:
        """수신자 상태 업데이트"""
        for recipient in self.recipients:
            if recipient['email'] == email:
                recipient['status'] = status
                recipient['last_modified'] = datetime.now().isoformat()
                self.save_recipients()
                self.logger.info(f"수신자 상태 업데이트: {email} -> {status}")
                return True
        return False
    
    def export_to_env_format(self) -> str:
        """수신자 목록을 .env 형식으로 내보내기"""
        active_emails = self.get_active_emails()
        return ','.join(active_emails)
    
    def import_from_env(self, env_content: str) -> Dict:
        """기존 .env 파일에서 수신자 가져오기"""
        if not env_content:
            return {'success_count': 0, 'error_count': 0, 'errors': []}
        
        emails = [email.strip() for email in env_content.split(',') if email.strip()]
        return self.add_multiple_recipients('\n'.join(emails))
    
    def backup_data(self, backup_file: str = None) -> str:
        """데이터 백업"""
        if backup_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"recipients_backup_{timestamp}.json"
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.recipients, f, ensure_ascii=False, indent=2)
            self.logger.info(f"데이터 백업 완료: {backup_file}")
            return backup_file
        except Exception as e:
            self.logger.error(f"데이터 백업 실패: {e}")
            raise
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """백업에서 데이터 복원"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            self.recipients = backup_data
            self.save_recipients()
            self.logger.info(f"백업에서 복원 완료: {backup_file}")
            return True
        except Exception as e:
            self.logger.error(f"백업 복원 실패: {e}")
            return False


# 테스트용 함수
def test_recipient_manager():
    """수신자 관리자 테스트"""
    print("=== 수신자 관리자 테스트 시작 ===")
    
    # 관리자 인스턴스 생성
    manager = SimpleRecipientManager("test_recipients.json")
    
    # 테스트 이메일들
    test_emails = [
        "test1@hanatour.com",
        "test2@hanatour.com",
        "test3@hanatour.com"
    ]
    
    # 단일 추가 테스트
    print("\n1. 단일 수신자 추가 테스트")
    for email in test_emails:
        try:
            result = manager.add_recipient(email)
            print(f"✅ 추가 성공: {result['email']}")
        except Exception as e:
            print(f"❌ 추가 실패: {email} - {e}")
    
    # 대량 추가 테스트
    print("\n2. 대량 수신자 추가 테스트")
    bulk_emails = """
    bulk1@hanatour.com
    bulk2@hanatour.com, bulk3@hanatour.com
    bulk4@hanatour.com; bulk5@hanatour.com
    """
    
    result = manager.add_multiple_recipients(bulk_emails)
    print(f"✅ 대량 추가 결과: 성공 {result['success_count']}명, 실패 {result['error_count']}명")
    
    # 검색 테스트
    print("\n3. 검색 테스트")
    search_results = manager.search_recipients("test")
    print(f"✅ 검색 결과: {len(search_results)}명")
    
    # 통계 테스트
    print("\n4. 통계 테스트")
    stats = manager.get_stats()
    print(f"✅ 통계: 전체 {stats['total']}명, 활성 {stats['active']}명")
    
    # 제거 테스트
    print("\n5. 제거 테스트")
    if manager.remove_recipient("test1@hanatour.com"):
        print("✅ 제거 성공")
    else:
        print("❌ 제거 실패")
    
    print("\n=== 테스트 완료 ===")


if __name__ == "__main__":
    test_recipient_manager()
