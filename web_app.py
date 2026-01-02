#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import threading
import time
import webbrowser
import subprocess

from newsletter_system import NewsletterSystem
from logging_config import setup_utf8_logging
from security_config import SecurityConfig, validate_and_setup_security

# 보안 설정 초기화
security_valid, security_config = validate_and_setup_security()
if not security_valid:
    print("⚠️ 보안 설정이 올바르지 않습니다. .env 파일을 확인하세요.")

app = Flask(__name__)
# 동적으로 생성된 보안 Secret Key 사용
app.secret_key = security_config.generate_flask_secret_key()
CORS(app)

# 전역 변수
newsletter_system = None
system_status = {
    'is_running': False,
    'last_run': None,
    'status_message': '대기 중'
}

# 상태 확인 요청 제한을 위한 변수
last_status_request = 0
status_request_interval = 300  # 300초마다 한 번만 허용

def setup_logging():
    """로깅 설정"""
    return setup_utf8_logging(
        logger_name=__name__,
        log_file='web_newsletter.log',
        level=logging.INFO
    )

logger = setup_logging()

def initialize_system():
    """뉴스레터 시스템 초기화"""
    global newsletter_system
    try:
        newsletter_system = NewsletterSystem()
        logger.info("뉴스레터 시스템 초기화 완료")
        return True
    except Exception as e:
        logger.error(f"시스템 초기화 실패: {e}")
        return False

def open_browser():
    """크롬 브라우저로 웹 페이지 열기"""
    try:
        # 잠시 대기 후 브라우저 열기 (서버 시작 시간 확보)
        time.sleep(2)
        
        # 크롬 브라우저 경로 찾기
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if chrome_path:
            # 크롬으로 웹 페이지 열기
            subprocess.Popen([chrome_path, "--new-window", "http://localhost:5000"])
            print("🌐 크롬 브라우저가 자동으로 열렸습니다!")
        else:
            # 기본 브라우저로 열기
            webbrowser.open("http://localhost:5000")
            print("🌐 기본 브라우저가 자동으로 열렸습니다!")
            
    except Exception as e:
        print(f"브라우저 열기 실패: {e}")
        print("수동으로 http://localhost:5000 에 접속해주세요.")

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """시스템 상태 확인"""
    global newsletter_system, system_status
    
    if newsletter_system is None:
        return jsonify({
            'status': 'error',
            'message': '시스템이 초기화되지 않았습니다.'
        })
    
    # 키워드 설정 정보 가져오기
    topics = newsletter_system.keyword_manager.get_topics()
    
    return jsonify({
        'status': 'success',
        'system_status': system_status,
        'topics_count': len(topics),
        'topics': topics,
        'receiver_count': newsletter_system.email_sender.get_receiver_count() if hasattr(newsletter_system.email_sender, 'get_receiver_count') else 1,
        'recipient_stats': newsletter_system.email_sender.get_recipient_stats() if hasattr(newsletter_system.email_sender, 'get_recipient_stats') else {'total': 1, 'active': 1, 'inactive': 0}
    })

@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    """키워드 설정 가져오기"""
    global newsletter_system
    
    if newsletter_system is None:
        return jsonify({'status': 'error', 'message': '시스템이 초기화되지 않았습니다.'})
    
    topics = newsletter_system.keyword_manager.get_topics()
    return jsonify({'status': 'success', 'topics': topics})

@app.route('/api/keywords', methods=['POST'])
def update_keywords():
    """키워드 설정 업데이트"""
    global newsletter_system
    
    if newsletter_system is None:
        return jsonify({'status': 'error', 'message': '시스템이 초기화되지 않았습니다.'})
    
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'add':
            name = data.get('name', '').strip()
            keywords = data.get('keywords', [])
            weight = data.get('weight', 20)
            
            # 입력 검증
            if not name:
                return jsonify({'status': 'error', 'message': '주제 이름을 입력해주세요.'})
            if not keywords:
                return jsonify({'status': 'error', 'message': '키워드를 입력해주세요.'})
            
            success = newsletter_system.keyword_manager.add_topic(name, keywords, weight)
            if success:
                # keyword_manager.py 파일도 업데이트
                try:
                    newsletter_system.keyword_manager.update_default_config_in_file()
                except Exception as e:
                    logger.warning(f"기본 설정 파일 업데이트 실패: {e}")
                return jsonify({'status': 'success', 'message': f'주제 "{name}"이(가) 추가되었습니다.'})
            else:
                return jsonify({'status': 'error', 'message': '주제 추가에 실패했습니다.'})
        
        elif action == 'update':
            topic_name = data.get('topic_name', '').strip()
            name = data.get('name', '').strip()
            keywords = data.get('keywords')
            weight = data.get('weight')
            
            # 입력 검증
            if not topic_name:
                return jsonify({'status': 'error', 'message': '수정할 주제 이름을 입력해주세요.'})
            if name and not name.strip():
                return jsonify({'status': 'error', 'message': '새 주제 이름을 입력해주세요.'})
            if keywords is not None and not keywords:
                return jsonify({'status': 'error', 'message': '키워드를 입력해주세요.'})
            
            success = newsletter_system.keyword_manager.update_topic(topic_name, name, keywords, weight)
            if success:
                # keyword_manager.py 파일도 업데이트
                try:
                    newsletter_system.keyword_manager.update_default_config_in_file()
                except Exception as e:
                    logger.warning(f"기본 설정 파일 업데이트 실패: {e}")
                return jsonify({'status': 'success', 'message': f'주제 "{topic_name}"이(가) 수정되었습니다.'})
            else:
                return jsonify({'status': 'error', 'message': '주제 수정에 실패했습니다.'})
        
        elif action == 'delete':
            topic_name = data.get('topic_name', '').strip()
            
            if not topic_name:
                return jsonify({'status': 'error', 'message': '삭제할 주제 이름을 입력해주세요.'})
            
            success = newsletter_system.keyword_manager.remove_topic(topic_name)
            if success:
                # keyword_manager.py 파일도 업데이트
                try:
                    newsletter_system.keyword_manager.update_default_config_in_file()
                except Exception as e:
                    logger.warning(f"기본 설정 파일 업데이트 실패: {e}")
                return jsonify({'status': 'success', 'message': f'주제 "{topic_name}"이(가) 삭제되었습니다.'})
            else:
                return jsonify({'status': 'error', 'message': '주제 삭제에 실패했습니다.'})
        
        else:
            return jsonify({'status': 'error', 'message': '잘못된 액션입니다.'})
    
    except Exception as e:
        logger.error(f"키워드 업데이트 중 오류: {e}")
        return jsonify({'status': 'error', 'message': f'오류가 발생했습니다: {str(e)}'})

@app.route('/api/test', methods=['POST'])
def run_test():
    """시스템 테스트 실행"""
    global newsletter_system, system_status
    
    logger.info("테스트 실행 API 호출됨")
    
    if newsletter_system is None:
        logger.error("시스템이 초기화되지 않았습니다.")
        return jsonify({'status': 'error', 'message': '시스템이 초기화되지 않았습니다.'})
    
    try:
        logger.info("테스트 실행 시작 - 상태 업데이트")
        system_status['is_running'] = True
        system_status['status_message'] = '테스트 실행 중...'
        
        # 백그라운드에서 테스트 실행
        def run_test_background():
            try:
                logger.info("백그라운드 테스트 실행 시작")
                newsletter_system.run_test()
                logger.info("백그라운드 테스트 실행 완료")
                system_status['is_running'] = False
                system_status['status_message'] = '테스트 완료'
                system_status['last_run'] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"백그라운드 테스트 실행 중 오류: {e}")
                import traceback
                logger.error(f"상세 오류: {traceback.format_exc()}")
                system_status['is_running'] = False
                system_status['status_message'] = f'테스트 실패: {str(e)}'
        
        logger.info("테스트 백그라운드 스레드 시작")
        thread = threading.Thread(target=run_test_background)
        thread.daemon = True  # 메인 프로세스 종료시 함께 종료
        thread.start()
        
        logger.info("테스트 백그라운드 스레드 시작됨")
        return jsonify({'status': 'success', 'message': '테스트가 시작되었습니다.'})
    
    except Exception as e:
        logger.error(f"테스트 실행 API 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        system_status['is_running'] = False
        system_status['status_message'] = f'테스트 실패: {str(e)}'
        return jsonify({'status': 'error', 'message': f'테스트 실행 중 오류: {str(e)}'})

@app.route('/api/generate', methods=['POST'])
def generate_newsletter():
    """뉴스레터 생성 및 발송"""
    global newsletter_system, system_status
    
    logger.info("뉴스레터 생성 API 호출됨")
    
    if newsletter_system is None:
        logger.error("시스템이 초기화되지 않았습니다.")
        return jsonify({'status': 'error', 'message': '시스템이 초기화되지 않았습니다.'})
    
    try:
        logger.info("뉴스레터 생성 시작 - 상태 업데이트")
        system_status['is_running'] = True
        system_status['status_message'] = '뉴스레터 생성 중...'
        
        # 백그라운드에서 뉴스레터 생성
        def generate_background():
            try:
                logger.info("백그라운드 뉴스레터 생성 시작")
                success = newsletter_system.generate_newsletter()
                logger.info(f"뉴스레터 생성 완료 - 성공: {success}")
                
                system_status['is_running'] = False
                if success:
                    system_status['status_message'] = '발송 완료'
                    logger.info("뉴스레터 발송 완료")
                else:
                    system_status['status_message'] = '발송 실패'
                    logger.error("뉴스레터 발송 실패")
                system_status['last_run'] = datetime.now().isoformat()
                
            except Exception as e:
                logger.error(f"백그라운드 뉴스레터 생성 중 오류: {e}")
                import traceback
                logger.error(f"상세 오류: {traceback.format_exc()}")
                system_status['is_running'] = False
                system_status['status_message'] = f'뉴스레터 생성 실패: {str(e)}'
        
        logger.info("백그라운드 스레드 시작")
        thread = threading.Thread(target=generate_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': '뉴스레터 생성이 시작되었습니다.',
            'template': 'new'
        })
        
    except Exception as e:
        logger.error(f"뉴스레터 생성 API 오류: {e}")
        system_status['is_running'] = False
        system_status['status_message'] = f'뉴스레터 생성 실패: {str(e)}'
        return jsonify({'status': 'error', 'message': f'뉴스레터 생성 중 오류: {str(e)}'})

@app.route('/api/preview', methods=['POST'])
def preview_newsletter():
    """뉴스레터 미리보기"""
    global newsletter_system
    
    logger.info("뉴스레터 미리보기 API 호출됨")
    
    if newsletter_system is None:
        return jsonify({'status': 'error', 'message': '시스템이 초기화되지 않았습니다.'})
    
    try:
        # 샘플 데이터로 미리보기 생성
        sample_data = {
            'IT': {
                'news_list': [
                    {
                        'title': '새로운 AI 기술 개발 소식',
                        'press': '테크뉴스',
                        'date': '2024-01-15',
                        'summary': '최신 AI 기술이 다양한 분야에서 혁신을 가져오고 있습니다.',
                        'link': '#'
                    },
                    {
                        'title': '클라우드 컴퓨팅 트렌드',
                        'press': 'IT월드',
                        'date': '2024-01-15',
                        'summary': '클라우드 기술의 발전으로 비즈니스 환경이 변화하고 있습니다.',
                        'link': '#'
                    }
                ],
                'topic_summary': 'IT 분야의 최신 기술 동향과 혁신 소식을 전해드립니다.'
            },
            '여행': {
                'news_list': [
                    {
                        'title': '해외여행 트렌드 분석',
                        'press': '여행저널',
                        'date': '2024-01-15',
                        'summary': '2024년 해외여행 시장의 새로운 트렌드를 분석했습니다.',
                        'link': '#'
                    }
                ],
                'topic_summary': '여행 업계의 최신 소식과 트렌드를 제공합니다.'
            }
        }
        
        # 새로운 템플릿으로 미리보기 생성
        preview_content = newsletter_system.generate_newsletter_content_new_template(sample_data)
        
        return jsonify({
            'status': 'success',
            'preview': preview_content,
            'template': 'new'
        })
        
    except Exception as e:
        logger.error(f"뉴스레터 미리보기 생성 중 오류: {e}")
        return jsonify({'status': 'error', 'message': f'미리보기 생성 중 오류: {str(e)}'})

@app.route('/preview')
def preview_page():
    """뉴스레터 미리보기 페이지"""
    return render_template('preview.html')

@app.route('/api/settings')
def get_settings():
    """설정 정보 가져오기"""
    try:
        # .env 파일에서 설정 읽기
        settings = {}
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        settings[key] = value
        
        return jsonify({
            'status': 'success',
            'settings': {
                'newsletter_title': settings.get('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터'),
                'max_articles_per_topic': int(settings.get('MAX_ARTICLES_PER_TOPIC', 10)),
                'max_topics': int(settings.get('MAX_TOPICS', 5)),
                'email_sender': settings.get('EMAIL_SENDER', ''),
                'email_receiver': settings.get('EMAIL_RECEIVER', ''),
                'openai_api_key': '설정됨' if settings.get('OPENAI_API_KEY') else '설정되지 않음'
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'설정 정보 가져오기 실패: {str(e)}'})

# ============================================================================
# 수신자 관리 API 엔드포인트
# ============================================================================

@app.route('/api/recipients', methods=['GET'])
def get_recipients():
    """수신자 목록 조회"""
    try:
        from recipient_manager import SimpleRecipientManager
        recipient_manager = SimpleRecipientManager()
        
        # 검색 필터
        search = request.args.get('search', '')
        if search:
            recipients = recipient_manager.search_recipients(search)
        else:
            recipients = recipient_manager.get_all_recipients()
        
        stats = recipient_manager.get_stats()
        
        return jsonify({
            'status': 'success',
            'recipients': recipients,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"수신자 목록 조회 중 오류: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/recipients', methods=['POST'])
def add_recipient():
    """단일 수신자 추가"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'status': 'error', 'message': '이메일을 입력해주세요.'})
        
        from recipient_manager import SimpleRecipientManager
        recipient_manager = SimpleRecipientManager()
        new_recipient = recipient_manager.add_recipient(email)
        
        return jsonify({
            'status': 'success',
            'message': '수신자가 추가되었습니다.',
            'recipient': new_recipient
        })
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)})
    except Exception as e:
        logger.error(f"수신자 추가 중 오류: {e}")
        return jsonify({'status': 'error', 'message': f'추가 중 오류: {str(e)}'})

@app.route('/api/recipients/bulk', methods=['POST'])
def add_multiple_recipients():
    """대량 수신자 추가 (Ctrl+C/V)"""
    try:
        data = request.get_json()
        emails_text = data.get('emails', '')
        
        if not emails_text:
            return jsonify({'status': 'error', 'message': '이메일 목록을 입력해주세요.'})
        
        from recipient_manager import SimpleRecipientManager
        recipient_manager = SimpleRecipientManager()
        result = recipient_manager.add_multiple_recipients(emails_text)
        
        return jsonify({
            'status': 'success',
            'message': f'{result["success_count"]}명 추가, {result["error_count"]}명 실패',
            'result': result
        })
    except Exception as e:
        logger.error(f"대량 수신자 추가 중 오류: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/recipients/<email>', methods=['DELETE'])
def remove_recipient(email):
    """수신자 제거"""
    try:
        from recipient_manager import SimpleRecipientManager
        recipient_manager = SimpleRecipientManager()
        success = recipient_manager.remove_recipient(email)
        
        if success:
            return jsonify({'status': 'success', 'message': '수신자가 제거되었습니다.'})
        else:
            return jsonify({'status': 'error', 'message': '수신자를 찾을 수 없습니다.'})
    except Exception as e:
        logger.error(f"수신자 제거 중 오류: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/recipients/sync', methods=['POST'])
def sync_recipients():
    """수신자 데이터를 .env 파일과 동기화"""
    try:
        from recipient_manager import SimpleRecipientManager
        recipient_manager = SimpleRecipientManager()
        active_emails = recipient_manager.get_active_emails()
        
        # .env 파일 업데이트
        env_content = []
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('EMAIL_RECEIVER='):
                    env_content.append(f'EMAIL_RECEIVER={",".join(active_emails)}\n')
                else:
                    env_content.append(line)
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.writelines(env_content)
        
        logger.info(f"수신자 동기화 완료: {len(active_emails)}명")
        return jsonify({
            'status': 'success',
            'message': f'{len(active_emails)}명의 수신자가 .env 파일에 동기화되었습니다.'
        })
    except Exception as e:
        logger.error(f"수신자 동기화 중 오류: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/recipients/import-env', methods=['POST'])
def import_from_env():
    """기존 .env 파일에서 수신자 가져오기"""
    try:
        data = request.get_json() or {}
        overwrite = data.get('overwrite', False)
        
        from recipient_manager import SimpleRecipientManager
        recipient_manager = SimpleRecipientManager()
        
        # 현재 .env 파일의 EMAIL_RECEIVER 읽기
        env_content = ""
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('EMAIL_RECEIVER='):
                        env_content = line.split('=', 1)[1].strip()
                        break
        
        if not env_content:
            return jsonify({'status': 'error', 'message': '.env 파일에서 수신자 정보를 찾을 수 없습니다.'})
        
        result = recipient_manager.import_from_env(env_content, overwrite=overwrite)
        
        return jsonify({
            'status': 'success',
            'message': f'기존 .env 파일에서 {result["success_count"]}명 가져오기 완료' + (' (기존 목록 초기화됨)' if overwrite else ''),
            'result': result
        })
    except Exception as e:
        logger.error(f"기존 .env 파일에서 가져오기 중 오류: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/recipients')
def recipients_page():
    """수신자 관리 페이지"""
    return render_template('recipients.html')

if __name__ == '__main__':
    # 시스템 초기화
    if initialize_system():
        print("뉴스레터 웹 시스템이 시작되었습니다!")
        print("웹 브라우저에서 http://localhost:5000 으로 접속하세요.")
        
        # 백그라운드에서 브라우저 열기
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    else:
        print("시스템 초기화에 실패했습니다.")
        print(".env 파일과 설정을 확인해주세요.") 