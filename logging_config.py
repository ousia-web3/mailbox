# -*- coding: utf-8 -*-
"""
로깅 설정 유틸리티 - UTF-8 인코딩 지원
"""
import os
import sys
import logging
from datetime import datetime

def setup_utf8_logging(logger_name=None, log_file=None, level=logging.INFO):
    """UTF-8 인코딩을 지원하는 로거 설정"""
    
    # Windows에서 콘솔 출력 UTF-8 설정
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        # Windows 콘솔 UTF-8 강제 설정
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass
        
    # 기존 핸들러 제거
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 핸들러 목록
    handlers = []
    
    # 콘솔 핸들러 (UTF-8 출력)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    handlers.append(console_handler)
    
    # 파일 핸들러 (UTF-8 저장)
    if log_file:
        # logs 디렉토리 생성
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # logs 디렉토리 내에 로그 파일 저장
        log_file_path = os.path.join(logs_dir, log_file)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='a')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        handlers.append(file_handler)
    
    # 로깅 설정 적용
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )
    
    # 특정 로거 반환
    if logger_name:
        return logging.getLogger(logger_name)
    else:
        return logging.getLogger()

def get_logger(name, log_file=None):
    """UTF-8 로거 인스턴스 반환"""
    return setup_utf8_logging(name, log_file)

# 전역 로거 설정 함수
def configure_global_logging():
    """전역 로깅 설정"""
    setup_utf8_logging(log_file='newsletter_system.log')
    
    # 특정 라이브러리 로그 레벨 조정
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)