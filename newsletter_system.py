import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

from windows_utf8 import setup_windows_utf8
from logging_config import setup_utf8_logging
from error_recovery import fallback_manager, robust_function

# Windows UTF-8 설정
setup_windows_utf8()
from news_collector_working import WorkingNewsCollector
from news_summarizer_v2 import NewsSummarizerV2
from email_sender import EmailSender
from keyword_manager import KeywordManager
from archiver import Archiver

class NewsletterSystem:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.setup_components()
    
    def setup_logging(self):
        """로깅 설정"""
        self.logger = setup_utf8_logging(
            logger_name=__name__,
            log_file='newsletter.log',
            level=logging.INFO
        )
    
    def setup_components(self):
        """시스템 컴포넌트 초기화"""
        try:
            self.keyword_manager = KeywordManager()
            self.news_collector = WorkingNewsCollector()
            self.news_summarizer = NewsSummarizerV2() # V2 교체
            self.email_sender = EmailSender()
            self.archiver = Archiver()
            self.logger.info("뉴스레터 시스템 컴포넌트 초기화 완료 (V2 적용)")
        except Exception as e:
            self.logger.error(f"컴포넌트 초기화 중 오류: {e}")
            raise
    
    @robust_function(max_attempts=3, delay=2.0, fallback_func=lambda self, topic: self._collect_news_fallback(topic))
    def collect_news_for_topic(self, topic):
        """특정 주제의 뉴스 수집 (키워드당 10개 고정)"""
        topic_name = topic["name"]
        keywords = topic["keywords"]
        
        # 키워드당 수집 목표 개수 고정
        articles_per_keyword = 10
        
        self.logger.info(f"주제 '{topic_name}' 뉴스 수집 시작")
        self.logger.info(f"키워드당 {articles_per_keyword}개씩 수집")
        
        all_news = []
        
        for keyword in keywords:
            try:
                self.logger.info(f"키워드 '{keyword}' 검색 중... (목표: {articles_per_keyword}개)")
                # 수집 대상 날짜 설정 (월요일은 토~일, 그 외는 전날)
                target_date = self.news_collector.get_target_search_date()
                self.logger.info(f"뉴스 수집 대상 날짜 범위: {target_date}")
                
                # 넉넉하게 20개 요청 후 10개로 자름
                news_list = self.news_collector.search_naver_news_with_retry(keyword, 20, target_date)
                
                # 키워드당 최대 10개 제한
                if len(news_list) > articles_per_keyword:
                    news_list = news_list[:articles_per_keyword]
                
                self.logger.info(f"키워드 '{keyword}'에서 {len(news_list)}개 뉴스 수집됨")
                
                # 중복 제거 및 추가
                for news in news_list:
                    # 제목 기준으로 중복 확인
                    is_duplicate = False
                    for existing_news in all_news:
                        if existing_news['title'] == news['title']:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_news.append(news)
                        self.logger.info(f"새로운 뉴스 추가: {news['title'][:50]}...")
                
            except Exception as e:
                self.logger.error(f"키워드 '{keyword}' 뉴스 수집 중 오류: {e}")
                continue
        
        self.logger.info(f"주제 '{topic_name}'에서 총 {len(all_news)}개 뉴스 수집 완료")
        return all_news

    def _collect_news_fallback(self, topic):
        """뉴스 수집 실패 시 Fallback 메서드"""
        topic_name = topic["name"]
        keywords = topic["keywords"]
        
        self.logger.warning(f"주제 '{topic_name}' 뉴스 수집 Fallback 실행")
        all_news = []
        
        # Fallback: 첫 번째 키워드로만 3개 수집 시도
        if keywords:
            keyword = keywords[0]
            try:
                news_list = self.news_collector.search_naver_news_with_retry(keyword, 3)
                all_news.extend(news_list)
            except Exception as e:
                self.logger.error(f"Fallback 수집 중 오류: {e}")
                
        return all_news

    def summarize_news_list(self, news_list, topic_name):
        """뉴스 리스트 요약 (기존 V2 방식)"""
        return self.news_summarizer.summarize_topic_with_persona(news_list, topic_name)

    def generate_empty_newsletter(self, topics):
        """빈 뉴스레터 생성"""
        return "뉴스 수집 실패로 뉴스레터를 생성할 수 없습니다."

    def generate_newsletter_content_new_template(self, topic_news_dict):
        """기존 템플릿(new_templates.html)을 위한 콘텐츠 생성"""
        return self.news_summarizer.generate_newsletter_content(topic_news_dict)

    def _format_cards(self, lines, category):
        """카드 섹션 HTML 포맷팅"""
        html = ""
        current_card = {}
        local_index = 1  # 카테고리 내 순서 (01, 02...)
        
        for line in lines:
            if line.startswith("- 번호:"):
                if current_card:
                    html += self._create_card_html(current_card, local_index)
                    current_card = {}
                    local_index += 1
                current_card['number'] = line.replace("- 번호:", "").strip()
            elif line.startswith("- 제목:"):
                current_card['title'] = line.replace("- 제목:", "").strip()
            elif line.startswith("- 요약:"):
                current_card['summary'] = line.replace("- 요약:", "").strip()
            elif line.startswith("- 링크:"):
                current_card['link'] = line.replace("- 링크:", "").strip()
        
        if current_card:
            html += self._create_card_html(current_card, local_index)
            
        return html

    def _create_card_html(self, card, local_index):
        # 타이틀용 순서 (카테고리 내 1, 2...)
        title_num = str(local_index).zfill(2)
        # 참조용 번호 (전체 1~5)
        ref_num = card.get('number', '00').zfill(2)
        
        return f"""
                    <div class="news-item">
                        <span class="news-title"><span class="news-bullet">{title_num}</span> {card.get('title', '')}</span>
                        <p class="news-body">
                            {card.get('summary', '')} <a href="#news-{int(ref_num)}" class="ref-mark">{ref_num}</a>
                        </p>
                    </div>
        """

    def _format_other_news(self, lines):
        """기타 뉴스 HTML 포맷팅"""
        html = ""
        for line in lines:
            # 포맷: - 1. 제목 | 링크
            if "|" in line:
                parts = line.split("|")
                left_part = parts[0].strip()
                link = parts[1].strip()
                
                # 번호와 제목 분리
                import re
                match = re.search(r'-\s*(\d+)\.\s*(.*)', left_part)
                if match:
                    number = match.group(1)
                    title = match.group(2).strip()
                else:
                    # 번호가 없는 경우 (기존 방식 호환)
                    number = "0"
                    title = left_part.replace("-", "").strip()
                
                html += f"""
                        <li id="news-{number}">
                            <span class="number-badge">{number}</span>
                            <a href="{link}" target="_blank" class="news-link">
                                {title}
                            </a>
                        </li>
                """
        return html
    
    def cleanup(self):
        """소멸자에서 정리"""
        try:
            if hasattr(self, 'news_collector'):
                self.news_collector.cleanup()
        except Exception as e:
            self.logger.error(f"정리 중 오류: {e}")
    
    def run_test(self):
        """시스템 테스트 실행"""
        try:
            self.logger.info("시스템 테스트 시작")
            
            # 1. 키워드 설정 확인
            self.logger.info("1. 키워드 설정 확인 중...")
            topics = self.keyword_manager.get_topics()
            if not topics:
                self.logger.error("키워드가 설정되지 않았습니다.")
                return False
            self.logger.info(f"키워드 설정 확인 완료 - {len(topics)}개 주제")
            
            # 2. 뉴스 수집 테스트 (모든 주제에 대해 수집)
            self.logger.info("2. 뉴스 수집 테스트 중 (전체 주제)...")
            test_all_news = []

            for topic in topics:
                # 실제 운영과 동일한 수집 로직 사용
                try:
                    self.logger.info(f"테스트 수집: 주제 '{topic['name']}'")
                    news = self.collect_news_for_topic(topic) or []

                    # 운영 환경과 동일한 필터링 적용 (30자 이상)
                    valid_news = []
                    for n in news:
                        content = n.get('full_content', '').strip()
                        preview = n.get('content_preview', '').strip()
                        if len(content) >= 30 or len(preview) >= 100:
                            # 카테고리 정보 추가
                            n['category'] = topic['name']
                            valid_news.append(n)

                    test_all_news.extend(valid_news)
                except Exception as e:
                    self.logger.warning(f"테스트 수집 중 오류 ({topic['name']}): {e}")
            
            if not test_all_news:
                self.logger.warning("뉴스 수집 테스트에서 뉴스를 찾지 못했습니다.")
            else:
                self.logger.info(f"뉴스 수집 테스트 완료 - 총 {len(test_all_news)}개 뉴스")
            
            # 3. AI 요약 및 템플릿 생성 테스트 (V3)
            self.logger.info("3. AI 요약 및 템플릿 생성 테스트 (V3) 중...")
            if test_all_news:
                # 전체 요약 생성
                full_summary_text = self.news_summarizer.summarize_all_news(test_all_news)
                
                if full_summary_text:
                    self.logger.info("AI 요약 테스트 완료")
                    
                    # 템플릿 생성 (테스트이므로 Fallback 데이터는 None 전달)
                    newsletter_content = self.generate_newsletter_content_v3(full_summary_text, None, test_all_news)
                    
                    if newsletter_content:
                        self.logger.info("템플릿 생성 테스트 완료")
                        
                        # 4. 이메일 설정 확인
                        self.logger.info("4. 이메일 설정 확인 중...")
                        receiver_count = self.email_sender.get_receiver_count()
                        self.logger.info(f"이메일 설정 확인 완료 - {receiver_count}명의 수신자")
                        
                        # 5. 테스트 이메일 발송 (생성된 뉴스레터 내용으로 발송)
                        self.logger.info("5. 테스트 이메일 발송 중...")
                        subject = f"[테스트 메일] {os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')}"
                        test_email_success = self.email_sender.send_newsletter(subject, newsletter_content)
                        
                        if test_email_success:
                            self.logger.info("테스트 이메일 발송 완료")
                        else:
                            self.logger.error("테스트 이메일 발송 실패")
                            return False
                    else:
                        self.logger.error("템플릿 생성 실패")
                else:
                    self.logger.error("AI 요약 실패")
            else:
                self.logger.warning("테스트 뉴스 없음으로 요약 및 발송 테스트 건너뜀")
            
            self.logger.info("시스템 테스트 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"시스템 테스트 중 오류: {e}")
            return False
    
    def _collect_news_fallback(self, topic):
        """뉴스 수집 실패 시 Fallback 메서드"""
        topic_name = topic["name"]
        keywords = topic["keywords"]
        
        self.logger.warning(f"주제 '{topic_name}' 뉴스 수집 실패, Fallback 데이터 생성")
        
        # Fallback 뉴스 데이터 생성
        fallback_news = fallback_manager.create_news_fallback_data(topic_name, keywords)
        
        return fallback_news
    
    @robust_function(max_attempts=3, delay=1.0, fallback_func=lambda self, news, topic_name: self._summarize_news_fallback(news, topic_name))
    def _summarize_single_news_with_retry(self, news, topic_name):
        """개별 뉴스 요약 (재시도 로직 포함)"""
        try:
            # news_summarizer.py는 딕셔너리 전체를 받음
            if 'full_content' not in news:
                news['full_content'] = news.get('content_preview', news.get('title', ''))
            
            summary = self.news_summarizer.summarize_news(news)
            self.logger.info(f"뉴스 요약 완료: {news['title'][:50]}...")
            return summary
            
        except Exception as e:
            self.logger.error(f"뉴스 요약 중 오류: {e}")
            raise
    
    def _summarize_news_fallback(self, news, topic_name):
        """뉴스 요약 실패 시 Fallback 메서드"""
        self.logger.warning(f"뉴스 요약 실패, Fallback 요약 생성: {news.get('title', '제목없음')[:50]}")
        return fallback_manager.create_summary_fallback(news, topic_name)
    
    def summarize_news_list(self, news_list, topic_name):
        """뉴스 리스트 요약 (V2 페르소나 적용)"""
        try:
            self.logger.info(f"주제 '{topic_name}' 뉴스 요약 시작 (V2)")
            
            # V2 페르소나 요약 (통합 요약 생성)
            topic_summary = self.news_summarizer.summarize_topic_with_persona(news_list, topic_name)
            
            if not topic_summary:
                self.logger.warning(f"주제 '{topic_name}' 요약 결과 없음 (필터링됨)")
                return {
                    'news_list': [], # 필터링되어 없음
                    'topic_summary': f"{topic_name} 관련 유효한 뉴스가 없습니다.",
                    'pick_summary': []
                }

            # PICK 요약은 topic_summary 내부에 포함되어 있으므로 별도 생성 불필요
            # 파싱은 generate_newsletter_content_new_template 에서 수행
            
            self.logger.info(f"주제 '{topic_name}' 요약 완료")
            
            return {
                'news_list': news_list,
                'topic_summary': topic_summary,
                'pick_summary': [] # V2에서는 텍스트 내 포함
            }
            
        except Exception as e:
            self.logger.error(f"뉴스 리스트 요약 중 오류: {e}")
            return {
                'news_list': news_list,
                'topic_summary': f"{topic_name} 주제 요약 실패: {e}",
                'pick_summary': []
            }
    
    @robust_function(max_attempts=2, delay=5.0, fallback_func=lambda self: self._generate_emergency_newsletter())
    def generate_newsletter(self):
        """뉴스레터 생성 및 발송 (강화된 에러 복구 포함)"""
        # 중복 실행 방지 (Lock 파일 사용)
        lock_file = os.path.join(os.path.dirname(__file__), 'newsletter.lock')
        
        # 락 파일이 존재하고, 생성된지 10분이 지나지 않았으면 실행 중단
        if os.path.exists(lock_file):
            try:
                file_time = os.path.getmtime(lock_file)
                elapsed_time = time.time() - file_time
                if elapsed_time < 600:  # 10분 (600초)
                    remaining_time = int((600 - elapsed_time) / 60)
                    self.logger.warning(f"뉴스레터 생성 프로세스가 이미 실행 중입니다. (Lock 파일 존재, {remaining_time}분 후 재시도 가능)")
                    return False
                else:
                    self.logger.warning(f"오래된 Lock 파일을 제거하고 새로 시작합니다. (경과 시간: {int(elapsed_time/60)}분)")
                    os.remove(lock_file)
            except Exception as e:
                self.logger.error(f"Lock 파일 확인 중 오류: {e}")
        
        # 락 파일 생성
        try:
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self.logger.error(f"Lock 파일 생성 실패: {e}")

        try:
            self.logger.info("뉴스레터 생성 시작")
            
            # 키워드 설정 가져오기
            topics = self.keyword_manager.get_topics()
            
            if not topics:
                self.logger.warning("설정된 키워드가 없습니다.")
                return False
            
            # 1. 모든 주제별 뉴스 수집
            raw_news_dict = {}
            
            for topic in topics:
                topic_name = topic["name"]
                self.logger.info(f"주제 '{topic_name}' 뉴스 수집 시작")
                news_list = self.collect_news_for_topic(topic) or []
                
                # 본문 내용 검증 및 필터링 (Hallucination 방지)
                valid_news_list = []
                for news in news_list:
                    content = news.get('full_content', '').strip()
                    preview = news.get('content_preview', '').strip()
                    
                    # 1. 본문이 충분히 있는 경우 (30자 이상)
                    if len(content) >= 30:
                        valid_news_list.append(news)
                    # 2. 본문은 없지만 프리뷰가 충분히 긴 경우 (100자 이상) -> 프리뷰를 본문으로 대체
                    elif len(preview) >= 100:
                        news['full_content'] = preview
                        valid_news_list.append(news)
                        self.logger.warning(f"뉴스 '{news.get('title')}' 본문 추출 실패, 프리뷰({len(preview)}자)로 대체하여 포함")
                    # 3. 둘 다 부족한 경우 -> 제외
                    else:
                        self.logger.warning(f"뉴스 '{news.get('title')}' 내용 부족으로 제외 (본문: {len(content)}자, 프리뷰: {len(preview)}자)")
                
                news_list = valid_news_list
                
                raw_news_dict[topic_name] = news_list
                self.logger.info(f"주제 '{topic_name}'에서 {len(news_list)}개 뉴스 수집됨 (유효성 검증 완료)")

            # 2. 뉴스 재분류 (IT -> AI 이동 로직)
            # 키워드 매핑 확인
            it_key = next((k for k in raw_news_dict if k in ['IT', 'Technology Trends']), None)
            ai_key = next((k for k in raw_news_dict if k in ['AI', 'AI Insight']), None)

            if it_key and ai_key:
                it_news = raw_news_dict[it_key]
                ai_news = raw_news_dict[ai_key]
                
                new_it_news = []
                moved_count = 0
                
                # AI 관련 키워드 정의
                ai_keywords = [
                    'ai', 'artificial intelligence', '인공지능', 'gpt', 'llm', 
                    'machine learning', '머신러닝', 'deep learning', '딥러닝', 
                    'neural network', '신경망', 'copilot', 'gemini', 'chatgpt', 
                    'claude', 'sora', 'genai', '생성형', 'npu', '온디바이스'
                ]
                
                for news in it_news:
                    # 제목과 내용 미리보기에서 키워드 검사
                    text_to_check = (news.get('title', '') + " " + news.get('content_preview', '')).lower()
                    
                    is_ai_related = any(k in text_to_check for k in ai_keywords)
                    
                    if is_ai_related:
                        # AI 뉴스에 중복 확인 후 추가
                        if not any(n.get('link') == news.get('link') for n in ai_news):
                            ai_news.append(news)
                            moved_count += 1
                        # IT 뉴스에서는 제외 (이동 처리)
                    else:
                        new_it_news.append(news)
                
                raw_news_dict[it_key] = new_it_news
                raw_news_dict[ai_key] = ai_news
                
                if moved_count > 0:
                    self.logger.info(f"IT 뉴스({it_key})에서 AI 관련 뉴스 {moved_count}개를 AI 카테고리({ai_key})로 이동했습니다.")

            # 3. 전체 뉴스 통합 및 요약 (V3 방식)
            all_news_list = []
            for topic_name, news_list in raw_news_dict.items():
                # 각 뉴스에 카테고리 정보 추가
                for news in news_list:
                    news['category'] = topic_name
                all_news_list.extend(news_list)

            total_news_count = len(all_news_list)
            self.logger.info(f"총 {total_news_count}개 뉴스 수집 완료")

            if total_news_count == 0:
                self.logger.warning("수집된 뉴스가 없습니다. 기본 뉴스레터를 생성합니다.")
                # 기본 뉴스레터 내용 생성
                newsletter_content = self.generate_empty_newsletter(topics)
            else:
                # 전체 뉴스 요약 (새로운 프롬프트 사용)
                self.logger.info("전체 뉴스 통합 요약 시작 (V3)")
                full_summary_text = self.news_summarizer.summarize_all_news(all_news_list)

                if not full_summary_text:
                    self.logger.error("전체 뉴스 요약 실패")
                    return False

                # 뉴스레터 내용 생성 (새로운 템플릿 사용) - 원본 뉴스 데이터도 함께 전달
                newsletter_content = self.generate_newsletter_content_v3(full_summary_text, raw_news_dict, all_news_list)

                if not newsletter_content:
                    self.logger.error("뉴스레터 콘텐츠 생성 실패")
                    return False

                # 아카이빙 (데이터 및 HTML 저장)
                archive_data = {
                    "raw_news": raw_news_dict,
                    "full_summary": full_summary_text
                }
                self.archiver.save_daily_archive(archive_data, newsletter_content)
            
            # 이메일 제목 생성
            subject = f"[Daily] {os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')}"
            
            # 뉴스가 없어도 뉴스레터는 발송하도록 수정
            self.logger.info(f"뉴스레터 생성 완료 - 뉴스 수: {total_news_count}")
            
            # 이메일 발송
            success = self.email_sender.send_newsletter(subject, newsletter_content)
            
            if success:
                self.logger.info("뉴스레터 발송 완료")
                return True
            else:
                self.logger.error("뉴스레터 발송 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"뉴스레터 생성 중 오류: {e}")
            import traceback
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
        finally:
            # 락 파일 제거
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except Exception as e:
                    self.logger.error(f"Lock 파일 제거 실패: {e}")
    
    def _generate_emergency_newsletter(self):
        """모든 수집이 실패했을 때의 응급 뉴스레터 생성 및 발송"""
        try:
            self.logger.warning("응급 뉴스레터 모드 진입")
            
            # 키워드 설정 가져오기 (최대한 시도)
            try:
                topics = self.keyword_manager.get_topics()
            except:
                topics = []
            
            # 응급 뉴스레터 내용 생성
            emergency_content = fallback_manager.create_emergency_newsletter(topics)
            
            # 이메일 제목 생성
            subject = f"[시스템 안내] {os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')} - {datetime.now().strftime('%Y년 %m월 %d일')}"
            
            # 이메일 발송 시도
            try:
                success = self.email_sender.send_newsletter(subject, emergency_content)
                if success:
                    self.logger.info("응급 뉴스레터 발송 완료")
                    return True
                else:
                    self.logger.error("응급 뉴스레터 발송 실패")
                    return False
            except Exception as e:
                self.logger.error(f"응급 뉴스레터 발송 중 오류: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"응급 뉴스레터 생성 중 오류: {e}")
            return False
    
    def generate_empty_newsletter(self, topics):
        """빈 뉴스레터 생성 (이메일 클라이언트 호환 템플릿)"""
        current_date = datetime.now().strftime("%Y년 %m월 %d일")
        
        content = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>[IT본부] 하나투어 뉴스레터</title>
            <!--[if mso]>
            <noscript>
                <xml>
                    <o:OfficeDocumentSettings>
                        <o:PixelsPerInch>96</o:PixelsPerInch>
                    </o:OfficeDocumentSettings>
                </xml>
            </noscript>
            <![endif]-->
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f4f4;">
                <tr>
                    <td align="center" style="padding: 20px 0;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                            <!-- 헤더 -->
                            <tr>
                                <td style="background-color: #5E2BB8; padding: 30px 20px; text-align: center;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: bold;">[IT본부] 하나투어 뉴스레터</h1>
                                    <p style="margin: 8px 0 0 0; color: #ffffff; font-size: 14px; opacity: 0.9;">
                                        
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- 콘텐츠 -->
                            <tr>
                                <td style="padding: 30px 20px; text-align: center;">
                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                        <tr>
                                            <td style="padding: 40px 20px;">
                                                <p style="margin: 0 0 20px 0; color: #666666; font-size: 16px; line-height: 1.5;">오늘은 수집할 수 있는 뉴스가 없습니다.</p>
                                                <p style="margin: 0; color: #666666; font-size: 14px; line-height: 1.4;">다음 발송 시 다시 시도해보겠습니다.</p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- 푸터 -->
                            <tr>
                                <td style="background-color: #2c3e50; padding: 20px; text-align: center;">
                                    <p style="margin: 0 0 8px 0; color: #ffffff; font-size: 12px;">본 이메일은 자동으로 생성되었으며, 구글 제미나이 2.5가 사용되고 있습니다.</p>
                                    <p style="margin: 0; color: #ffffff; font-size: 12px;">© 2026 뉴스레터 자동화 시스템. All rights reserved</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return content
    
    def generate_newsletter_content_new_template(self, topic_news_dict):
        """이메일 클라이언트 호환성을 위한 뉴스레터 템플릿 생성 (templates/new_templates.html 사용)"""
        try:
            # 템플릿 파일 읽기
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'new_templates.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_html = f.read()
            
            # 날짜 한글 요일 처리
            days = ["월", "화", "수", "목", "금", "토", "일"]
            day_str = days[datetime.now().weekday()]
            current_date = datetime.now().strftime(f"%Y년 %m월 %d일 ({day_str})")
            
            def clean_text(text):
                """텍스트 끝의 불필요한 특수문자 제거 (내부 헬퍼)"""
                if not text: return ""
                cleaned = text.strip()
                while cleaned and (cleaned.endswith('*') or cleaned.endswith('•')):
                    cleaned = cleaned.rstrip('*').rstrip('•').strip()
                return cleaned
            
            def extract_field(text, field_name):
                """텍스트에서 특정 필드 값 추출 (내부 헬퍼)"""
                start = text.find(field_name)
                if start == -1: return ""
                start += len(field_name)
                next_fields = ["요약:", "인사이트:", "링크:", "• [", "💡 Insight:"]
                end = len(text)
                for nf in next_fields:
                    nf_idx = text.find(nf, start)
                    if nf_idx != -1 and nf_idx < end:
                        end = nf_idx
                return text[start:end].strip()

            # 1. 전체 핵심 요약 (Executive Summary) 추출
            summary_lines_html = ""
            
            # AI 출력에서 [Executive Summary] 섹션 찾기
            exec_summary = ""
            for topic_name, topic_data in topic_news_dict.items():
                topic_summary_text = topic_data.get('topic_summary', '')
                
                # [Executive Summary] 섹션 파싱 시도
                if "[Executive Summary]" in topic_summary_text or "Executive Summary" in topic_summary_text:
                    lines = topic_summary_text.split('\n')
                    in_exec_section = False
                    exec_lines = []
                    
                    for line in lines:
                        line = line.strip()
                        if "[Executive Summary]" in line or "Executive Summary" in line:
                            in_exec_section = True
                            continue
                        if in_exec_section:
                            # 다음 섹션 시작 감지
                            if line.startswith('[') or "분야 핵심 요약" in line or "개별 뉴스 카드" in line:
                                break
                            if line and not line.startswith('#') and not line.startswith('─') and not line.startswith('='):
                                exec_lines.append(line)
                    
                    if exec_lines:
                        exec_summary = ' '.join(exec_lines).strip()
                        # 끝부분 특수문자 제거
                        while exec_summary.endswith('-') or exec_summary.endswith('=') or exec_summary.endswith('─'):
                            exec_summary = exec_summary.rstrip('-=─').strip()
                        break
            
            # Executive Summary가 있으면 사용, 없으면 기존 방식(주제별 1줄 요약) 사용
            if exec_summary:
                summary_lines_html = exec_summary
                self.logger.info(f"Executive Summary 추출 성공 ({len(exec_summary)}자)")
            else:
                self.logger.warning("Executive Summary 추출 실패, 주제별 요약으로 대체")
                # 카테고리 매핑 (주제 -> 표시 이름)
                category_map = {
                    "IT": "기술경쟁",
                    "Technology Trends": "기술경쟁",
                    "AI": "시장변화",
                    "AI Insight": "시장변화",
                    "여행": "여행정보",
                    "Travel & Business": "여행정보"
                }
                
                for topic_name, topic_data in topic_news_dict.items():
                    topic_summary_text = topic_data.get('topic_summary', '')
                    summary_line = ""
                    lines = topic_summary_text.split('\n')
                    
                    for line in lines:
                        line = line.strip().replace('**', '')
                        if not line: continue
                        if line.startswith('•') and ':' in line:
                            parts = line.split(':', 1)
                            if topic_name in parts[0] or "요약" in parts[0] or len(lines) < 5:
                                display_category = category_map.get(topic_name, topic_name)
                                summary_line = f"• <b>{display_category}:</b> {parts[1].strip()}"
                                break
                    
                    if not summary_line and lines:
                        for line in lines:
                            line = line.strip().replace('**', '').lstrip('•').strip()
                            if len(line) > 20 and "분야 핵심 요약" not in line and not line.startswith('1.'):
                                display_category = category_map.get(topic_name, topic_name)
                                summary_line = f"• <b>{display_category}:</b> {line}"
                                break
                    
                    if summary_line:
                        summary_lines_html += f"{summary_line}<br>"
            
            # 2. 뉴스 콘텐츠 구성
            content_body_html = ""
            
            for topic_name, topic_data in topic_news_dict.items():
                topic_summary = topic_data['topic_summary'] # AI가 생성한 전체 텍스트
                
                # 섹션 제목 매핑 (영어 변환)
                section_title_map = {
                    "IT": "Technology Trends",
                    "Technology Trends": "Technology Trends",
                    "AI": "AI Insight",
                    "AI Insight": "AI Insight",
                    "여행": "Travel & Business",
                    "Travel & Business": "Travel & Business"
                }
                display_title = section_title_map.get(topic_name, topic_name)
                
                content_body_html += f"""
                        <div class="section-title">{display_title}</div>
                """
                
                # 뉴스 카드 파싱 (AI 텍스트 기반)
                generated_card_count = 0
                if "개별 뉴스 카드" in topic_summary:
                    news_cards_part = topic_summary.split("개별 뉴스 카드")[1]
                    cards = news_cards_part.split("• [")
                    
                    for card in cards:
                        if not card.strip() or "배지 이름" in card: continue
                        
                        # 배지 추출 및 정제
                        badge_end = card.find("]")
                        badge_raw = card[:badge_end] if badge_end != -1 else "General"
                        # "배지: " 접두어 제거 및 공백 제거
                        badge = badge_raw.replace("배지:", "").replace("Badge:", "").strip()
                        
                        card_content = card[badge_end+1:]
                        
                        # 배지 스타일 결정 (한글 키워드 매핑 및 강제 변환)
                        badge_clean = badge.replace('[', '').replace(']', '').strip()
                        
                        # 영어 배지가 들어온 경우 강제 한글 변환
                        badge_map = {
                            "Technology Trends": "혁신 동향",
                            "AI Insight": "시장 영향",
                            "Travel & Business": "산업 분석",
                            "IT": "혁신 동향",
                            "AI": "시장 영향",
                            "Travel": "산업 분석",
                            "Business": "산업 분석"
                        }
                        if badge_clean in badge_map:
                            badge = badge_map[badge_clean]
                        
                        badge_class = "badge-default"
                        if "미래" in badge or "Future" in badge: badge_class = "badge-it"
                        elif "시장" in badge or "Market" in badge: badge_class = "badge-ai"
                        elif "산업" in badge or "Industry" in badge: badge_class = "badge-travel"
                        elif "혁신" in badge or "Innovation" in badge: badge_class = "badge-it"
                        elif "기술" in badge: badge_class = "badge-it"
                        
                        # 제목, 요약, 인사이트, 링크 추출 및 정제
                        # 하이픈, 별표, 공백 등 특수문자 제거 (lstrip 사용)
                        title = clean_text(extract_field(card_content, "제목:")).replace('**', '').lstrip('- *•').strip()
                        summary = clean_text(extract_field(card_content, "요약:")).replace('**', '').lstrip('- *•').strip()
                        
                        # 요약문 끝의 불필요한 특수문자 제거
                        summary = summary.rstrip('•').strip()
                        
                        # Insight 제거 (혹시 포함되었을 경우)
                        if "💡 Insight:" in summary:
                            summary = summary.split("💡 Insight:")[0].strip()
                        
                        # 링크 추출 (다양한 패턴 시도)
                        link = extract_field(card_content, "링크:").strip()
                        if not link: link = extract_field(card_content, "Link:").strip()
                        if not link: link = extract_field(card_content, "URL:").strip()
                        
                        # 링크 정제 (괄호, 꺽쇠, 마크다운 제거)
                        link = link.strip()
                        if link.startswith('(') and link.endswith(')'): link = link[1:-1]
                        if link.startswith('<') and link.endswith('>'): link = link[1:-1]
                        if link.startswith('[') and link.endswith(']'): link = link[1:-1]
                        # 마크다운 링크 [텍스트](URL) 형태 처리
                        if '](' in link and link.endswith(')'):
                            try:
                                link = link.split('](')[1][:-1]
                            except: pass
                        
                        # 링크 유효성 검사 (http로 시작하지 않으면 무효)
                        if not link or not link.startswith('http'):
                            # 링크가 없으면 원본 뉴스에서 찾기 시도 (매칭되는 뉴스가 있다면)
                            # 여기서는 간단히 패스하거나 # 처리
                            if link and not link.startswith('http'):
                                link = "#"
                            else:
                                continue
                        
                        # 링크 유효성 검사
                        if not link or link.lower() == "none" or link == "" or link == "#":
                            continue
                            
                        # 인사이트 영역은 사용자 요청으로 숨김 처리 (HTML에서 제외)
                        
                        content_body_html += f"""
                            <div class="news-card">
                                <span class="badge {badge_class}">{badge}</span>
                                <h3 class="news-title">{title}</h3>
                                <p class="news-desc">{summary}</p>
                                <a href="{link}" target="_blank" class="btn-link">원문 읽기 →</a>
                            </div>
                        """
                        generated_card_count += 1
                
                # AI 파싱 실패 또는 결과가 0개인 경우 기존 방식 폴백
                if generated_card_count == 0:
                    # AI 파싱 실패 시 기존 방식 폴백 (Raw Data 사용하되 포맷팅 적용)
                    news_list = topic_data.get('news_list', [])
                    for news in news_list:
                        title = clean_text(news.get('title', '제목 없음')).replace('**', '').lstrip('- *•').strip()
                        summary = clean_text(news.get('summary', '')).replace('**', '').lstrip('- *•').strip()
                        if not summary:
                            summary = clean_text(news.get('content_preview', '요약 내용이 없습니다.')).replace('**', '').lstrip('- *•').strip()
                        
                        link = news.get('link', '#')
                        if not link or link == "#": continue
                        
                        # 배지 매핑 (토픽 이름을 한글 배지로 변환)
                        badge_map = {
                            "Technology Trends": "혁신 동향",
                            "AI Insight": "시장 영향",
                            "Travel & Business": "산업 분석",
                            "IT": "혁신 동향",
                            "AI": "시장 영향",
                            "여행": "산업 분석"
                        }
                        badge = badge_map.get(topic_name, "혁신 동향")
                        
                        # 배지 스타일 결정
                        badge_class = "badge-default"
                        if badge == "혁신 동향": badge_class = "badge-it"
                        elif badge == "시장 영향": badge_class = "badge-ai"
                        elif badge == "산업 분석": badge_class = "badge-travel"
                        
                        # 인사이트 생성 (사용자 요청으로 숨김)
                        insight_html = ""
                        
                        content_body_html += f"""
                            <div class="news-card">
                                <span class="badge {badge_class}">{badge}</span>
                                <h3 class="news-title">{title}</h3>
                                <p class="news-desc">{summary}</p>
                                {insight_html}
                                <a href="{link}" target="_blank" class="btn-link">원문 읽기 →</a>
                            </div>
                        """
            
            # 템플릿 치환
            final_html = template_html.replace('{current_date}', current_date)
            final_html = final_html.replace('{summary_content}', summary_lines_html)
            final_html = final_html.replace('{content_body}', content_body_html)
            
            return final_html
            
        except Exception as e:
            self.logger.error(f"이메일 호환 템플릿 뉴스레터 생성 실패: {e}")
            return None

    def generate_newsletter_content_v3(self, full_summary_text, raw_news_dict=None, all_news_list=None):
        """새로운 템플릿(news_templates01.html)을 위한 콘텐츠 생성 (개선된 Fallback 포함)"""
        import re
        try:
            # AI 출력 디버그 저장
            debug_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, f'ai_output_v3_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
            try:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write("=== AI 출력 원본 ===\n")
                    f.write(full_summary_text)
                    f.write("\n\n=== 원본 뉴스 데이터 ===\n")
                    if raw_news_dict:
                        for topic, news_list in raw_news_dict.items():
                            f.write(f"\n[{topic}] - {len(news_list)}개 뉴스\n")
                self.logger.info(f"AI 출력 디버그 파일 저장: {debug_file}")
            except Exception as e:
                self.logger.warning(f"디버그 파일 저장 실패: {e}")

            # 템플릿 파일 읽기
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'news_templates01.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_html = f.read()

            # 날짜 처리
            days = ["월", "화", "수", "목", "금", "토", "일"]
            day_str = days[datetime.now().weekday()]
            current_date = datetime.now().strftime(f"%Y년 %m월 %d일 ({day_str})")

            # 섹션별 파싱
            sections = {
                "executive_summary": "",
                "tech_news_items": "",
                "ai_news_items": "",
                "biz_news_items": "",
                "other_news_items": ""
            }

            # 카테고리별 원본 뉴스 매핑 (Fallback용)
            fallback_news = {
                "TECH": [],
                "AI": [],
                "BIZ": []
            }
            if raw_news_dict:
                for topic_name, news_list in raw_news_dict.items():
                    if topic_name in ["IT", "Technology Trends"]:
                        fallback_news["TECH"] = news_list
                    elif topic_name in ["AI", "AI Insight"]:
                        fallback_news["AI"] = news_list
                    elif topic_name in ["여행", "Travel & Business"]:
                        fallback_news["BIZ"] = news_list

            # [중요] AI 요약에 사용된 뉴스 리스트 순서 재현 (ID 매핑용)
            # news_summarizer_v2.py의 summarize_all_news 메서드와 동일한 로직이어야 함
            reference_news_list = []
            if all_news_list:
                category_news = {}
                # 순서 보장을 위해 all_news_list 순서대로 처리
                for news in all_news_list:
                    category = news.get('category', 'Unknown')
                    if category not in category_news:
                        category_news[category] = []
                    category_news[category].append(news)
                
                # 각 카테고리에서 최대 15개씩만 선택 (Summarizer와 동일 로직)
                for category, news_list in category_news.items():
                    reference_news_list.extend(news_list[:15])
            
            self.logger.info(f"ID 참조용 뉴스 리스트 생성 완료: {len(reference_news_list)}개")

            # 섹션별 파싱 및 아이템 수집
            current_section = None
            buffer = []
            lines = full_summary_text.split('\n')
            
            # 파싱된 모든 뉴스 아이템을 저장할 리스트 (In Other News 자동 생성용)
            all_parsed_items = []
            global_index = 1

            # 섹션별 버퍼 저장소
            section_buffers = {
                "executive_summary": [],
                "tech": [],
                "ai": [],
                "biz": []
            }

            for line in lines:
                line = line.strip()
                if not line: continue

                if "[Executive Summary]" in line:
                    current_section = "executive_summary"
                    continue
                elif "[TECH]" in line:
                    current_section = "tech"
                    continue
                elif "[AI]" in line:
                    current_section = "ai"
                    continue
                elif "[BIZ]" in line:
                    current_section = "biz"
                    continue
                elif "[In Other News]" in line:
                    # In Other News 섹션은 무시 (프로그램에서 자동 생성)
                    current_section = "ignore"
                    continue

                if current_section in section_buffers:
                    section_buffers[current_section].append(line)

            # 1. Executive Summary 처리
            exec_summary = "\n".join(section_buffers["executive_summary"]).strip()
            # 끝부분의 불필요한 기호 제거 (---, === 등)
            while exec_summary.endswith('-') or exec_summary.endswith('=') or exec_summary.endswith('─') or exec_summary.endswith('#'):
                exec_summary = exec_summary.rstrip('-=─#').strip()
            sections["executive_summary"] = exec_summary

            # 2. TECH 섹션 처리
            tech_html, tech_items, next_idx = self._format_cards_v3(
                section_buffers["tech"], "TECH", fallback_news["TECH"], 
                start_index=global_index,
                reference_news_list=reference_news_list
            )
            sections["tech_news_items"] = tech_html
            all_parsed_items.extend(tech_items)
            global_index = next_idx

            # 3. AI 섹션 처리
            ai_html, ai_items, next_idx = self._format_cards_v3(
                section_buffers["ai"], "AI", fallback_news["AI"], 
                start_index=global_index,
                reference_news_list=reference_news_list
            )
            sections["ai_news_items"] = ai_html
            all_parsed_items.extend(ai_items)
            global_index = next_idx

            # 4. BIZ 섹션 처리
            biz_html, biz_items, next_idx = self._format_cards_v3(
                section_buffers["biz"], "BIZ", fallback_news["BIZ"], 
                start_index=global_index,
                reference_news_list=reference_news_list
            )
            sections["biz_news_items"] = biz_html
            all_parsed_items.extend(biz_items)
            global_index = next_idx

            # 원본 뉴스 제목 매핑 생성 (In Other News용)
            link_to_original_title = {}
            if raw_news_dict:
                for news_list in raw_news_dict.values():
                    for news in news_list:
                        if news.get('link') and news.get('title'):
                            link_to_original_title[news['link']] = news['title']

            # 5. In Other News 자동 생성 (수집된 모든 아이템 기반, 원본 제목 우선 사용)
            sections["other_news_items"] = self._generate_other_news_html(all_parsed_items, link_to_original_title)

            # 파싱 결과 로깅
            self.logger.info(f"V3 파싱 결과 - Executive Summary: {len(sections['executive_summary'])}자")
            self.logger.info(f"V3 파싱 결과 - TECH 카드: {len(tech_items)}개")
            self.logger.info(f"V3 파싱 결과 - AI 카드: {len(ai_items)}개")
            self.logger.info(f"V3 파싱 결과 - BIZ 카드: {len(biz_items)}개")
            self.logger.info(f"V3 파싱 결과 - Total Items: {len(all_parsed_items)}개")

            # 템플릿 치환
            final_html = template_html.replace('{current_date}', current_date)
            final_html = final_html.replace('{executive_summary}', sections["executive_summary"])
            final_html = final_html.replace('{tech_news_items}', sections["tech_news_items"])
            final_html = final_html.replace('{ai_news_items}', sections["ai_news_items"])
            final_html = final_html.replace('{biz_news_items}', sections["biz_news_items"])
            final_html = final_html.replace('{other_news_items}', sections["other_news_items"])

            return final_html

        except Exception as e:
            self.logger.error(f"V3 뉴스레터 생성 실패: {e}")
            import traceback
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return None

    def _format_cards_v3(self, lines, category, fallback_news_list=None, start_index=1, reference_news_list=None):
        """V3 템플릿용 카드 섹션 HTML 포맷팅 (개선된 파싱 + Fallback + 아이템 반환)"""
        html = ""
        parsed_items = []
        current_card = {}
        local_index = 1
        current_global_index = start_index

        import re

        # 정규식 패턴 (들여쓰기 허용하도록 개선)
        patterns = {
            'number': r'[-*•]?\s*(?:\*\*)?번호(?:\*\*)?\s*[:.]?\s*(\d+)',
            'id': r'[-*•]?\s*(?:\*\*)?ID(?:\*\*)?\s*[:.]?\s*(\d+)',
            'title': r'[-*•]?\s*(?:\*\*)?제목(?:\*\*)?\s*[:：]\s*(.+)',
            'summary': r'[-*•]?\s*(?:\*\*)?요약(?:내용)?(?:\*\*)?\s*[:：]\s*(.+)',
            'link': r'[-*•]?\s*(?:\*\*)?링크(?:\*\*)?\s*[:：]?\s*'
        }

        self.logger.info(f"[V3 파싱] {category} 섹션 파싱 시작 - AI 출력 라인 수: {len(lines)}")

        # 표 형식 감지 (첫 5줄 내에 '|' 문자가 3개 이상 있으면 표 형식으로 판단)
        table_format_detected = False
        for line in lines[:min(5, len(lines))]:
            if line.count('|') >= 3:
                table_format_detected = True
                self.logger.error(f"❌ {category} AI가 표(Table) 형식으로 출력했습니다! 즉시 Fallback 사용")
                break

        # 표 형식 감지 시 즉시 Fallback
        if table_format_detected:
            if fallback_news_list and len(fallback_news_list) > 0:
                self.logger.warning(f"[V3 Fallback] {category} 표 형식 감지로 인해 원본 뉴스 데이터 {len(fallback_news_list)}개로 대체")
                # 직접 Fallback 섹션으로 이동 (아래 코드 재사용)
                html = ""
                parsed_items = []
                local_index = 1
                current_global_index = start_index

                for idx, news in enumerate(fallback_news_list[:5], 1):
                    summary = news.get('content_preview', '') or news.get('full_content', '') or '요약 없음'
                    if summary and len(summary) > 200:
                        summary = summary[:200].strip()
                        last_period = summary.rfind('.')
                        if last_period > 100:
                            summary = summary[:last_period + 1]

                    fallback_card = {
                        'number': str(idx),
                        'title': news.get('title', '제목 없음'),
                        'summary': summary,
                        'link': news.get('link', '#')
                    }

                    # skip_validation=True로 품질 검증 우회 (이미 Fallback 데이터이므로)
                    card_html, card_item = self._create_card_html_v3(fallback_card, local_index, current_global_index, news, skip_validation=True)
                    if card_html:
                        html += card_html
                        parsed_items.append(card_item)
                        local_index += 1
                        current_global_index += 1

                self.logger.info(f"[V3 Fallback] {category} 표 형식으로 인한 Fallback 완료: {len(parsed_items)}개 카드 생성")
                return html, parsed_items, current_global_index
            else:
                self.logger.error(f"❌ {category} 표 형식 감지 + 원본 뉴스 없음 = 빈 결과 반환")
                return "", [], start_index

        # 원본 뉴스 링크 매핑 생성 (링크 -> 뉴스 데이터)
        link_to_news = {}
        if fallback_news_list:
            for news in fallback_news_list:
                link = news.get('link', '')
                if link:
                    link_to_news[link] = news

        for line in lines:
            line = line.strip()
            if not line: continue

            # 번호 감지
            match_num = re.search(patterns['number'], line)
            if match_num:
                if current_card:
                    card_html, card_item = self._create_card_html_v3(
                        current_card, local_index, current_global_index,
                        link_to_news.get(current_card.get('link', '')),
                        fallback_news_list=reference_news_list # 원본 뉴스 리스트 전달 (전체 기준)
                    )
                    if card_html:
                        html += card_html
                        parsed_items.append(card_item)
                        local_index += 1
                        current_global_index += 1
                    current_card = {}
                current_card['number'] = match_num.group(1)
                continue

            # ID 감지
            match_id = re.search(patterns['id'], line)
            if match_id:
                current_card['id'] = match_id.group(1)
                continue

            # 제목 감지
            match_title = re.search(patterns['title'], line)
            if match_title:
                current_card['title'] = match_title.group(1).strip()
                continue

            # 요약 감지
            match_summary = re.search(patterns['summary'], line)
            if match_summary:
                current_card['summary'] = match_summary.group(1).strip()
                continue

            # 링크 감지 (마크다운 형식 [텍스트](URL) 및 직접 URL 모두 지원)
            if re.search(patterns['link'], line):
                # 마크다운 링크 형식 [텍스트](URL) 추출
                md_link_match = re.search(r'\[.*?\]\((https?://[^\s)]+)\)', line)
                if md_link_match:
                    current_card['link'] = md_link_match.group(1).strip()
                    continue
                # 직접 URL 추출
                direct_url_match = re.search(r'(https?://[^\s)]+)', line)
                if direct_url_match:
                    current_card['link'] = direct_url_match.group(1).strip()
                    continue

        # 마지막 카드 처리
        if current_card:
            card_html, card_item = self._create_card_html_v3(
                current_card, local_index, current_global_index,
                link_to_news.get(current_card.get('link', '')),
                fallback_news_list=reference_news_list # 원본 뉴스 리스트 전달 (전체 기준)
            )
            if card_html:
                html += card_html
                parsed_items.append(card_item)
                local_index += 1
                current_global_index += 1

        # 파싱 결과 확인
        self.logger.info(f"[V3 파싱] {category} AI 파싱 결과: {len(parsed_items)}개 카드")

        # Fallback: 파싱 실패 또는 불충분한 경우 원본 뉴스 사용
        if len(parsed_items) < 5 and fallback_news_list and len(fallback_news_list) > 0:
            self.logger.warning(f"[V3 Fallback] {category} AI 파싱 부족! (파싱된 카드: {len(parsed_items)}개) 원본 뉴스 데이터 {len(fallback_news_list)}개로 대체")

            # AI 파싱 결과를 버리고 원본 데이터로 완전히 교체
            html = ""
            parsed_items = []
            local_index = 1
            current_global_index = start_index

            for idx, news in enumerate(fallback_news_list[:5], 1):  # 최대 5개
                # 요약 내용: content_preview -> full_content -> 기본값 순으로 시도
                summary = news.get('content_preview', '') or news.get('full_content', '') or '요약 없음'
                if summary and len(summary) > 200:
                    summary = summary[:200].strip()
                    # 문장 중간에서 잘리지 않도록 마지막 마침표까지만 사용
                    last_period = summary.rfind('.')
                    if last_period > 100:
                        summary = summary[:last_period + 1]

                fallback_card = {
                    'number': str(idx),
                    'title': news.get('title', '제목 없음'),
                    'summary': summary,
                    'link': news.get('link', '#')
                }

                # skip_validation=True로 품질 검증 우회 (이미 Fallback 데이터이므로)
                card_html, card_item = self._create_card_html_v3(fallback_card, local_index, current_global_index, news, skip_validation=True)
                if card_html:
                    html += card_html
                    parsed_items.append(card_item)
                    local_index += 1
                    current_global_index += 1

            self.logger.info(f"[V3 Fallback] {category} 원본 데이터로 {len(parsed_items)}개 카드 생성 완료")

        return html, parsed_items, current_global_index

    def _create_card_html_v3(self, card, local_index, global_index, original_news=None, skip_validation=False, fallback_news_list=None):
        """V3 템플릿용 카드 HTML 생성 및 아이템 반환 (제목=요약 검증 + Fallback 추가 + ID 기반 링크 복원)

        Args:
            skip_validation (bool): True일 경우 품질 검증을 건너뜀 (Fallback 카드 생성 시 사용)
            fallback_news_list (list): 원본 뉴스 리스트 (ID 기반 링크 복원용)
        """
        title_num = str(local_index).zfill(2)
        ref_num = str(global_index).zfill(2)

        # 필수 필드 검증
        title = card.get('title', '').strip()
        link = card.get('link', '').strip()
        news_id = card.get('id')

        # [ID 기반 링크 복원] AI가 링크를 잘랐을 경우를 대비하여 원본 데이터에서 복원
        if news_id and fallback_news_list:
            try:
                idx = int(news_id) - 1
                if 0 <= idx < len(fallback_news_list):
                    original_data = fallback_news_list[idx]
                    original_link = original_data.get('link')
                    if original_link:
                        if link != original_link:
                            self.logger.info(f"ID({news_id}) 기반 링크 복원: {link[:30]}... -> {original_link[:30]}...")
                            link = original_link
                            # original_news 객체도 업데이트
                            original_news = original_data
            except Exception as e:
                self.logger.warning(f"ID 기반 링크 복원 중 오류: {e}")

        if not title:
            self.logger.warning(f"카드 {local_index} 제목 누락, 건너뜀")
            return "", None
        if not link or link == '#':
            self.logger.warning(f"카드 {local_index} 링크 누락, 건너뜀")
            return "", None

        # 요약 검증 (제목과 동일하거나 너무 유사한 경우 Fallback 사용)
        summary = card.get('summary', '').strip()

        # skip_validation=True인 경우 품질 검증 생략 (이미 Fallback 처리된 데이터)
        if not skip_validation:
            # 제목과 요약 정규화 (공백, 특수문자 제거 후 비교)
            import re
            title_normalized = re.sub(r'[^\w\s]', '', title.lower()).strip()
            summary_normalized = re.sub(r'[^\w\s]', '', summary.lower()).strip()

            # 요약 품질 검사 플래그
            needs_fallback = False

            # 1. 완전히 동일한 경우
            if summary_normalized == title_normalized:
                self.logger.error(f"❌ 카드 {local_index} ('{title[:30]}...') 요약이 제목과 동일함! Fallback 사용 시도")
                needs_fallback = True

            # 2. 요약이 제목을 포함하고 있고, 추가 정보가 거의 없는 경우 (유사도 80% 이상)
            elif summary_normalized and title_normalized in summary_normalized:
                # 제목을 제외한 나머지 부분의 길이 확인
                remaining = summary_normalized.replace(title_normalized, '').strip()
                if len(remaining) < len(title_normalized) * 0.3:  # 추가 정보가 제목의 30% 미만
                    self.logger.warning(f"⚠️ 카드 {local_index} ('{title[:30]}...') 요약이 제목과 너무 유사함. Fallback 사용 시도")
                    needs_fallback = True

            # 3. 요약이 너무 짧은 경우 (20자 미만)
            elif len(summary) < 20:
                self.logger.warning(f"⚠️ 카드 {local_index} ('{title[:30]}...') 요약이 너무 짧음 ({len(summary)}자). Fallback 사용 시도")
                needs_fallback = True

            # Fallback 로직: 원본 뉴스의 content_preview 사용
            if needs_fallback and original_news:
                fallback_summary = original_news.get('content_preview', '') or original_news.get('full_content', '')
                if fallback_summary and len(fallback_summary) > 50:
                    # 200자로 제한
                    summary = fallback_summary[:200].strip()
                    # 문장 중간에서 잘리지 않도록 마지막 마침표까지만 사용
                    last_period = summary.rfind('.')
                    if last_period > 100:  # 최소 100자 이상 확보된 경우에만 마침표 기준 자르기
                        summary = summary[:last_period + 1]
                    self.logger.info(f"✅ 카드 {local_index} Fallback 요약 사용 ({len(summary)}자)")
                else:
                    self.logger.error(f"❌ 카드 {local_index} Fallback 실패 (원본 뉴스 데이터 부족), 카드 건너뜀")
                    return "", None
            elif needs_fallback and not original_news:
                self.logger.error(f"❌ 카드 {local_index} Fallback 실패 (원본 뉴스 데이터 없음), 카드 건너뜀")
                return "", None

        if not summary:
            self.logger.warning(f"카드 {local_index} ('{title[:30]}...') 요약 누락 - 빈 요약으로 생성")
            summary = ""

        html = f"""
                    <div class="news-item">
                        <span class="news-title"><span class="news-bullet">{title_num}</span> {title}</span>
                        <p class="news-body">
                            {summary} <a href="{link}" target="_blank" class="ref-mark">{ref_num}</a>
                        </p>
                    </div>
        """
        
        # 파싱된 아이템 정보 반환 (In Other News 생성용)
        item_info = {
            'global_index': global_index,
            'title': title,
            'link': link
        }
        
        return html, item_info

    def _generate_other_news_html(self, all_items, link_to_original_title=None):
        """수집된 모든 뉴스 아이템으로 In Other News 섹션 HTML 생성 (원본 제목 우선 사용)"""
        html = ""
        
        for item in all_items:
            index = item['global_index']
            link = item['link']
            
            # 원본 제목 조회 시도
            title = item['title'] # 기본값: AI가 생성한 제목
            if link_to_original_title and link in link_to_original_title:
                title = link_to_original_title[link] # 원본 제목으로 교체
            
            # 제목 글자수 제한 (50자, 초과시 ...)
            # 공백 포함 50자
            if len(title) > 50:
                display_title = title[:47] + "..."
            else:
                display_title = title
                
            html += f"""
                        <li id="news-{index}">
                            <span class="number-badge">{index}</span>
                            <a href="{link}" target="_blank" class="news-link">
                                {display_title}
                            </a>
                        </li>
            """
            
        return html

    def cleanup(self):
        """소멸자에서 정리"""
        try:
            if hasattr(self, 'news_collector'):
                self.news_collector.cleanup()
        except Exception as e:
            self.logger.error(f"정리 중 오류: {e}")
    
    def run_test(self):
        """시스템 테스트 실행"""
        try:
            self.logger.info("시스템 테스트 시작")

            # 1. 키워드 설정 확인
            self.logger.info("1. 키워드 설정 확인 중...")
            topics = self.keyword_manager.get_topics()
            if not topics:
                self.logger.error("키워드가 설정되지 않았습니다.")
                return False
            self.logger.info(f"키워드 설정 확인 완료 - {len(topics)}개 주제")

            # 2. 뉴스 수집 테스트 (주제별로 분류하여 수집)
            self.logger.info("2. 뉴스 수집 테스트 중 (전체 주제 및 키워드)...")
            test_all_news = []
            raw_news_dict = {}  # Fallback용 주제별 뉴스 데이터

            for topic in topics:
                topic_name = topic.get("name", "Unknown")
                keywords = topic.get("keywords", [])
                topic_news = []  # 이 주제의 뉴스

                if not keywords:
                    continue

                for keyword in keywords:
                    try:
                        # 테스트 시에도 충분한 데이터 확보를 위해 키워드당 10개 수집
                        news = self.news_collector.search_naver_news_with_retry(keyword, 10)

                        # 중복 제거 및 추가
                        for n in news:
                            is_duplicate = False
                            for existing in test_all_news:
                                if existing['title'] == n['title']:
                                    is_duplicate = True
                                    break
                            if not is_duplicate:
                                test_all_news.append(n)
                                topic_news.append(n)

                    except Exception as e:
                        self.logger.warning(f"테스트 수집 중 오류 ({keyword}): {e}")

                # 주제별 뉴스 저장
                raw_news_dict[topic_name] = topic_news
                self.logger.info(f"주제 '{topic_name}'에서 {len(topic_news)}개 뉴스 수집")

            if not test_all_news:
                self.logger.warning("뉴스 수집 테스트에서 뉴스를 찾지 못했습니다.")
            else:
                self.logger.info(f"뉴스 수집 테스트 완료 - 총 {len(test_all_news)}개 뉴스")

            # 3. AI 요약 및 템플릿 생성 테스트 (V3)
            self.logger.info("3. AI 요약 및 템플릿 생성 테스트 (V3) 중...")
            if test_all_news:
                # 전체 요약 생성
                full_summary_text = self.news_summarizer.summarize_all_news(test_all_news)

                if full_summary_text:
                    self.logger.info("AI 요약 테스트 완료")

                    # 템플릿 생성 (raw_news_dict를 Fallback용으로 전달)
                    newsletter_content = self.generate_newsletter_content_v3(full_summary_text, raw_news_dict, test_all_news)
                    
                    if newsletter_content:
                        self.logger.info("템플릿 생성 테스트 완료")
                        
                        # 4. 이메일 설정 확인
                        self.logger.info("4. 이메일 설정 확인 중...")
                        receiver_count = self.email_sender.get_receiver_count()
                        self.logger.info(f"이메일 설정 확인 완료 - {receiver_count}명의 수신자")
                        
                        # 5. 테스트 이메일 발송 (생성된 뉴스레터 내용으로 발송)
                        self.logger.info("5. 테스트 이메일 발송 중...")
                        subject = f"[테스트발송] {os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')}"
                        test_email_success = self.email_sender.send_newsletter(subject, newsletter_content)
                        
                        if test_email_success:
                            self.logger.info("테스트 이메일 발송 완료")
                        else:
                            self.logger.warning("테스트 이메일 발송 실패")
                    else:
                        self.logger.error("템플릿 생성 실패")
                else:
                    self.logger.error("AI 요약 실패")
            else:
                self.logger.warning("테스트 뉴스 없음으로 요약 및 발송 테스트 건너뜀")
            
            self.logger.info("시스템 테스트 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"시스템 테스트 중 오류: {e}")
            import traceback
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
    
    def __del__(self):
        """소멸자에서 정리"""
        self.cleanup()

if __name__ == "__main__":
    """메인 실행 코드"""
    try:
        print("뉴스레터 시스템 시작...")
        
        # 뉴스레터 시스템 초기화
        newsletter_system = NewsletterSystem()
        
        # 뉴스레터 생성 및 발송
        print("뉴스레터 생성 및 발송 중...")
        success = newsletter_system.generate_newsletter()
        
        if success:
            print("✅ 뉴스레터 생성 및 발송 완료!")
        else:
            print("❌ 뉴스레터 생성 및 발송 실패!")
            exit(1)
            
    except Exception as e:
        print(f"❌ 뉴스레터 시스템 실행 중 오류 발생: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        exit(1) 