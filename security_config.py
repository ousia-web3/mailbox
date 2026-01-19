#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
보안 설정 및 환경변수 검증 모듈
"""

import os
import re
import secrets
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class SecurityConfig:
    """보안 설정 및 환경변수 검증 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        load_dotenv()
        
    def validate_environment_variables(self) -> Dict[str, Any]:
        """환경변수 검증 및 보안 검사"""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'missing_vars': []
        }
        
        # 필수 환경변수 목록
        required_vars = [
            'GEMINI_API_KEY',
            'EMAIL_SENDER', 
            'EMAIL_PASSWORD',
            'EMAIL_RECEIVER'
        ]
        
        # 선택적 환경변수 목록
        optional_vars = [
            'OPENAI_API_KEY',
            'NAVER_CLIENT_ID',
            'NAVER_CLIENT_SECRET',
            'NEWSLETTER_TITLE',
            'MAX_ARTICLES_PER_TOPIC',
            'MAX_TOPICS'
        ]
        
        # 필수 환경변수 검증
        for var in required_vars:
            value = os.getenv(var)
            if not value or value in ['your_gemini_api_key_here', 'your_email@outlook.com', 
                                     'your_app_password_here', 'receiver1@example.com,receiver2@example.com']:
                validation_results['missing_vars'].append(var)
                validation_results['errors'].append(f"필수 환경변수 {var}가 설정되지 않았거나 기본값입니다.")
                validation_results['is_valid'] = False
        
        # API 키 형식 검증 (Gemini)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and not self._validate_api_key_format(gemini_key):
            validation_results['warnings'].append("Gemini API 키 형식이 올바르지 않을 수 있습니다.")
        
        # 이메일 형식 검증
        email_sender = os.getenv('EMAIL_SENDER')
        if email_sender and not self._validate_email_format(email_sender):
            validation_results['errors'].append("EMAIL_SENDER 형식이 올바르지 않습니다.")
            validation_results['is_valid'] = False
        
        email_receivers = os.getenv('EMAIL_RECEIVER', '')
        for email in email_receivers.split(','):
            email = email.strip()
            if email and not self._validate_email_format(email):
                validation_results['errors'].append(f"수신자 이메일 {email} 형식이 올바르지 않습니다.")
                validation_results['is_valid'] = False
        
        # 비밀번호 보안 검증
        password = os.getenv('EMAIL_PASSWORD')
        if password and len(password) < 8:
            validation_results['warnings'].append("이메일 비밀번호가 너무 짧습니다. Gmail 앱 비밀번호를 사용하세요.")
        
        return validation_results
    
    def _validate_api_key_format(self, key: str) -> bool:
        """API 키 형식 검증 (기본 길이 체크)"""
        # Gemini 키 등 일반적인 API 키 길이 체크
        return len(key) > 20
    
    def _validate_email_format(self, email: str) -> bool:
        """이메일 형식 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def generate_flask_secret_key(self) -> str:
        """Flask용 보안 Secret Key 생성"""
        # 환경변수에서 기존 키 확인
        existing_key = os.getenv('FLASK_SECRET_KEY')
        if existing_key and len(existing_key) >= 32:
            return existing_key
        
        # 새로운 보안 키 생성 (32바이트 = 256비트)
        new_key = secrets.token_urlsafe(32)
        self.logger.info("새로운 Flask Secret Key가 생성되었습니다.")
        return new_key
    
    def mask_sensitive_value(self, value: str, visible_chars: int = 4) -> str:
        """민감한 정보 마스킹"""
        if not value or len(value) <= visible_chars:
            return "*" * len(value) if value else ""
        
        return value[:visible_chars] + "*" * (len(value) - visible_chars)
    
    def get_safe_config_display(self) -> Dict[str, str]:
        """안전한 설정 정보 표시용 딕셔너리"""
        return {
            'GEMINI_API_KEY': self.mask_sensitive_value(os.getenv('GEMINI_API_KEY', '')),
            'NAVER_CLIENT_ID': self.mask_sensitive_value(os.getenv('NAVER_CLIENT_ID', '')),
            'NAVER_CLIENT_SECRET': self.mask_sensitive_value(os.getenv('NAVER_CLIENT_SECRET', '')),
            'EMAIL_SENDER': os.getenv('EMAIL_SENDER', ''),
            'EMAIL_PASSWORD': self.mask_sensitive_value(os.getenv('EMAIL_PASSWORD', '')),
            'EMAIL_RECEIVER': os.getenv('EMAIL_RECEIVER', ''),
            'NEWSLETTER_TITLE': os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터'),
            'MAX_ARTICLES_PER_TOPIC': os.getenv('MAX_ARTICLES_PER_TOPIC', '10'),
            'MAX_TOPICS': os.getenv('MAX_TOPICS', '5')
        }
    
    def check_security_best_practices(self) -> Dict[str, Any]:
        """보안 모범 사례 검사"""
        recommendations = {
            'critical': [],
            'warnings': [],
            'suggestions': []
        }
        
        # .env 파일 권한 검사 (Windows에서는 제한적)
        env_path = '.env'
        if os.path.exists(env_path):
            recommendations['suggestions'].append(
                ".env 파일이 버전 관리 시스템(.gitignore)에서 제외되었는지 확인하세요."
            )
        
        # API 키 순환 권장
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and gemini_key != 'your_gemini_api_key_here':
            recommendations['suggestions'].append(
                "정기적으로 API 키를 순환(rotation)하는 것을 권장합니다."
            )
        
        # Gmail 앱 비밀번호 사용 권장
        email_sender = os.getenv('EMAIL_SENDER', '')
        if 'gmail.com' in email_sender:
            recommendations['warnings'].append(
                "Gmail 사용 시 앱 비밀번호를 사용하고 2단계 인증을 활성화하세요."
            )
        
        return recommendations
    
    def setup_secure_logging(self):
        """보안을 고려한 로깅 설정"""
        # 민감한 정보가 로그에 출력되지 않도록 필터 설정
        class SensitiveDataFilter(logging.Filter):
            def filter(self, record):
                # API 키나 비밀번호가 포함된 로그 메시지 필터링
                sensitive_patterns = [
                    r'sk-[a-zA-Z0-9]+',  # OpenAI API 키
                    r'password[\'\"]*\s*[:=]\s*[\'\"]*[^\s\'\"]+',  # 비밀번호
                    r'key[\'\"]*\s*[:=]\s*[\'\"]*[^\s\'\"]+',  # 일반적인 키
                ]
                
                message = str(record.getMessage())
                for pattern in sensitive_patterns:
                    if re.search(pattern, message, re.IGNORECASE):
                        record.msg = re.sub(pattern, '[REDACTED]', record.msg, flags=re.IGNORECASE)
                
                return True
        
        # 모든 로거에 필터 추가
        for handler in logging.root.handlers:
            handler.addFilter(SensitiveDataFilter())

def validate_and_setup_security():
    """보안 설정 검증 및 초기화"""
    security = SecurityConfig()
    
    # 환경변수 검증
    validation = security.validate_environment_variables()
    
    if not validation['is_valid']:
        print("[보안] 검증 실패:")
        for error in validation['errors']:
            print(f"   - {error}")
        
        print("\n[해결방법]:")
        print("   1. .env.example 파일을 참조하여 .env 파일을 올바르게 설정하세요.")
        print("   2. 실제 API 키와 이메일 정보를 입력하세요.")
        print("   3. Gmail 사용 시 앱 비밀번호를 생성하여 사용하세요.")
        
        return False, security
    
    # 경고 사항 표시
    if validation['warnings']:
        print("[경고] 보안 경고:")
        for warning in validation['warnings']:
            print(f"   - {warning}")
    
    # 보안 모범 사례 검사
    recommendations = security.check_security_best_practices()
    if recommendations['warnings'] or recommendations['suggestions']:
        print("\n[권장사항] 보안 권장사항:")
        for warning in recommendations['warnings']:
            print(f"   - {warning}")
        for suggestion in recommendations['suggestions']:
            print(f"   - {suggestion}")
    
    # 보안 로깅 설정
    security.setup_secure_logging()
    
    print("[완료] 보안 검증 완료")
    return True, security

if __name__ == "__main__":
    validate_and_setup_security()