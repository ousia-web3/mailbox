#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
에러 복구 및 Fallback 메커니즘 모듈
"""

import time
import logging
import functools
from typing import Any, Callable, Optional, List, Dict
from datetime import datetime
import traceback

class RetryConfig:
    """재시도 설정 클래스"""
    def __init__(self, max_attempts: int = 3, delay: float = 1.0, 
                 backoff_multiplier: float = 2.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff_multiplier = backoff_multiplier
        self.max_delay = max_delay

class FallbackManager:
    """Fallback 메커니즘 관리 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fallback_data = {}
        self.error_counts = {}
    
    def with_retry_and_fallback(self, retry_config: RetryConfig = None, 
                               fallback_func: Callable = None,
                               exception_types: tuple = (Exception,)):
        """재시도 및 Fallback 데코레이터"""
        if retry_config is None:
            retry_config = RetryConfig()
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                delay = retry_config.delay
                
                # 함수 이름으로 에러 카운트 추적
                func_name = f"{func.__module__}.{func.__name__}"
                
                for attempt in range(retry_config.max_attempts):
                    try:
                        # 함수 실행
                        result = func(*args, **kwargs)
                        
                        # 성공 시 에러 카운트 리셋
                        if func_name in self.error_counts:
                            del self.error_counts[func_name]
                        
                        return result
                        
                    except exception_types as e:
                        last_exception = e
                        
                        # 에러 카운트 증가
                        self.error_counts[func_name] = self.error_counts.get(func_name, 0) + 1
                        
                        self.logger.warning(
                            f"함수 {func_name} 실행 실패 (시도 {attempt + 1}/{retry_config.max_attempts}): {e}"
                        )
                        
                        # 마지막 시도가 아니면 대기
                        if attempt < retry_config.max_attempts - 1:
                            time.sleep(delay)
                            delay = min(delay * retry_config.backoff_multiplier, retry_config.max_delay)
                        
                        # 3번째 연속 실패부터 Fallback 시작 고려
                        if self.error_counts[func_name] >= 3 and fallback_func:
                            self.logger.info(f"함수 {func_name} Fallback 모드 진입")
                            try:
                                return fallback_func(*args, **kwargs)
                            except Exception as fallback_error:
                                self.logger.error(f"Fallback 함수도 실패: {fallback_error}")
                
                # 모든 시도 실패
                self.logger.error(f"함수 {func_name} 모든 재시도 실패: {last_exception}")
                
                # Fallback이 있으면 시도
                if fallback_func:
                    try:
                        self.logger.info(f"최종 Fallback 시도: {func_name}")
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        self.logger.error(f"최종 Fallback도 실패: {fallback_error}")
                
                # 최종적으로 원본 예외 발생
                raise last_exception
            
            return wrapper
        return decorator
    
    def create_news_fallback_data(self, topic_name: str, keywords: List[str]) -> List[Dict]:
        """뉴스 수집 실패 시 Fallback 데이터 생성"""
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            fallback_news = []
            for i, keyword in enumerate(keywords[:3]):  # 최대 3개만
                news_item = {
                    'title': f'{topic_name} 관련 최신 동향 - {keyword}',
                    'link': f'https://example.com/news/{keyword.replace(" ", "-")}',
                    'press': '뉴스레터 시스템',
                    'date': current_date,
                    'content_preview': f'{keyword}에 대한 최신 정보를 수집 중입니다. 다음 발송에서 더 자세한 내용을 제공해드리겠습니다.',
                    'full_content': f'''
                    {keyword} 관련 소식
                    
                    현재 {keyword}에 대한 최신 뉴스를 수집하는 중입니다. 
                    일시적인 네트워크 문제나 소스 사이트 접근 제한으로 인해 
                    실시간 뉴스를 가져올 수 없었습니다.
                    
                    다음 뉴스레터에서는 더 풍부한 {keyword} 관련 소식을 
                    제공해드릴 예정입니다.
                    
                    지속적인 관심에 감사드립니다.
                    ''',
                    'priority': 999,  # 낮은 우선순위
                    'source': 'fallback',
                    'topic': topic_name,
                    'source_keyword': keyword
                }
                fallback_news.append(news_item)
            
            self.logger.info(f"주제 '{topic_name}'에 대한 Fallback 뉴스 {len(fallback_news)}개 생성됨")
            return fallback_news
            
        except Exception as e:
            self.logger.error(f"Fallback 뉴스 생성 중 오류: {e}")
            return []
    
    def create_summary_fallback(self, news_item: Dict, topic_name: str = "") -> str:
        """AI 요약 실패 시 Fallback 요약 생성"""
        try:
            title = news_item.get('title', '제목 없음')
            content = news_item.get('content_preview', news_item.get('full_content', ''))
            
            # 간단한 요약 생성 (제목 + 내용 일부)
            summary_parts = []
            
            # 제목 정리
            if title and title != '제목 없음':
                summary_parts.append(title)
            
            # 내용 일부 추가
            if content:
                # 내용을 200자로 제한
                content_summary = content.strip()[:200]
                if len(content) > 200:
                    content_summary += "..."
                summary_parts.append(content_summary)
            
            # 기본 메시지 추가
            if not summary_parts:
                return f"{topic_name} 관련 뉴스입니다. 자세한 내용은 원문을 참조해주세요."
            
            fallback_summary = " ".join(summary_parts)
            
            # Fallback 표시 추가
            fallback_summary += "\n\n[자동 요약: AI 요약 서비스 일시 중단으로 인한 기본 요약]"
            
            self.logger.info("Fallback 요약 생성 완료")
            return fallback_summary
            
        except Exception as e:
            self.logger.error(f"Fallback 요약 생성 중 오류: {e}")
            return f"{topic_name} 관련 뉴스입니다. 자세한 내용은 원문을 참조해주세요."
    
    def create_emergency_newsletter(self, topics: List[Dict]) -> str:
        """모든 수집이 실패했을 때의 응급 뉴스레터"""
        try:
            current_date = datetime.now().strftime('%Y년 %m월 %d일')
            
            content = f"""
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>뉴스레터 서비스 안내</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h1 style="color: #2c3e50; margin: 0;">뉴스레터 서비스 안내</h1>
                    <p style="color: #7f8c8d; margin: 5px 0 0 0;">발행일: {current_date}</p>
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 20px 0;">
                    <h2 style="color: #856404; margin: 0 0 10px 0;">📋 서비스 안내</h2>
                    <p style="margin: 0; color: #856404;">
                        오늘은 일시적인 기술적 문제로 인해 정상적인 뉴스 수집이 어려운 상황입니다.
                        <br><br>
                        다음 발송 시에는 정상적인 뉴스 서비스를 제공해드릴 예정입니다.
                        <br><br>
                        불편을 드려 죄송합니다.
                    </p>
                </div>
                
                <div style="background-color: #e3f2fd; border-radius: 6px; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #1976d2; margin: 0 0 10px 0;">📈 모니터링 중인 주제</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #1976d2;">
            """
            
            # 설정된 주제들 표시
            for topic in topics:
                topic_name = topic.get('name', '알 수 없는 주제')
                keywords = topic.get('keywords', [])
                content += f"<li><strong>{topic_name}</strong>: {', '.join(keywords[:3])}</li>"
            
            content += """
                    </ul>
                </div>
                
                <div style="background-color: #2c3e50; color: white; padding: 15px; border-radius: 6px; text-align: center; margin-top: 30px;">
                    <p style="margin: 0; font-size: 12px;">
                        본 이메일은 자동으로 생성되었습니다.<br>
                        © 2026 뉴스레터 자동화 시스템. All rights reserved
                    </p>
                </div>
            </body>
            </html>
            """
            
            self.logger.info("응급 뉴스레터 생성 완료")
            return content
            
        except Exception as e:
            self.logger.error(f"응급 뉴스레터 생성 중 오류: {e}")
            return """
            <html><body>
            <h1>뉴스레터 서비스 일시 중단</h1>
            <p>기술적 문제로 인해 오늘의 뉴스레터 발송이 어렵습니다.</p>
            <p>다음 발송 시 정상 서비스를 제공해드리겠습니다.</p>
            </body></html>
            """
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """에러 통계 반환"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_functions': len(self.error_counts),
            'error_details': self.error_counts.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_error_counts(self):
        """에러 카운트 리셋"""
        self.error_counts.clear()
        self.logger.info("에러 카운트가 리셋되었습니다.")

# 전역 FallbackManager 인스턴스
fallback_manager = FallbackManager()

# 편의 함수들
def with_retry(max_attempts=3, delay=1.0, backoff_multiplier=2.0):
    """간단한 재시도 데코레이터"""
    retry_config = RetryConfig(max_attempts, delay, backoff_multiplier)
    return fallback_manager.with_retry_and_fallback(retry_config)

def with_fallback(fallback_func):
    """Fallback 함수를 포함한 데코레이터"""
    return fallback_manager.with_retry_and_fallback(fallback_func=fallback_func)

def robust_function(max_attempts=3, delay=1.0, fallback_func=None):
    """완전한 에러 복구 데코레이터"""
    retry_config = RetryConfig(max_attempts, delay)
    return fallback_manager.with_retry_and_fallback(retry_config, fallback_func)