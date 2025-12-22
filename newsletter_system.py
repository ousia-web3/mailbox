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
from news_summarizer import NewsSummarizer
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
            self.news_summarizer = NewsSummarizer()
            self.email_sender = EmailSender()
            self.archiver = Archiver()
            self.logger.info("뉴스레터 시스템 컴포넌트 초기화 완료")
        except Exception as e:
            self.logger.error(f"컴포넌트 초기화 중 오류: {e}")
            raise
    
    @robust_function(max_attempts=3, delay=2.0, fallback_func=lambda self, topic: self._collect_news_fallback(topic))
    def collect_news_for_topic(self, topic):
        """특정 주제의 뉴스 수집 (비율 적용, 소수점 내림처리) - 에러 복구 강화"""
        import math
        
        topic_name = topic["name"]
        keywords = topic["keywords"]
        weight = topic["weight"]  # 비율 가져오기
        
        # 비율 기반 개수 계산 (소수점 내림처리)
        total_target_articles = 30  # 전체 목표 뉴스 수
        topic_weight_ratio = weight / 100  # 35% → 0.35
        
        # 주제별 총 뉴스 개수 계산 (내림처리)
        topic_total_articles = math.floor(total_target_articles * topic_weight_ratio)
        
        # 키워드당 뉴스 개수 계산 (내림처리)
        if len(keywords) > 0:
            articles_per_keyword = math.floor(topic_total_articles / len(keywords))
            # 최소 1개는 보장
            articles_per_keyword = max(1, articles_per_keyword)
        else:
            articles_per_keyword = 1
        
        self.logger.info(f"주제 '{topic_name}' 뉴스 수집 시작 (비율: {weight}%)")
        self.logger.info(f"주제별 총 목표: {topic_total_articles}개, 키워드당 {articles_per_keyword}개씩 수집")
        
        all_news = []
        
        for keyword in keywords:
            try:
                self.logger.info(f"키워드 '{keyword}' 검색 중... (목표: {articles_per_keyword}개)")
                # 오늘 날짜로 뉴스 수집 (전날이 아닌)
                today_date = self.news_collector.get_today_date()
                news_list = self.news_collector.search_naver_news_with_retry(keyword, 5, today_date)  # 5개 수집
                
                self.logger.info(f"키워드 '{keyword}'에서 {len(news_list)}개 뉴스 수집됨")
                
                # 키워드별로 설정된 개수만큼 선택
                if len(news_list) > articles_per_keyword:
                    news_list = news_list[:articles_per_keyword]
                    self.logger.info(f"키워드 '{keyword}'에서 최신 {articles_per_keyword}개 선택")
                
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
        """뉴스 리스트 요약"""
        try:
            self.logger.info(f"주제 '{topic_name}' 뉴스 요약 시작")
            
            # 개별 뉴스 요약 (재시도 로직 포함)
            for news in news_list:
                summary = self._summarize_single_news_with_retry(news, topic_name)
                news['summary'] = summary
            
            # 주제별 종합 요약
            topic_summary = self.news_summarizer.summarize_topic_news(news_list, topic_name)
            
            # 주제 요약을 기반으로 PICK 요약 생성 (설정에 따라 비활성화 가능)
            pick_summary = self.news_summarizer.generate_pick_summary(topic_summary, topic_name)
            
            self.logger.info(f"주제 '{topic_name}' 요약 완료")
            
            return {
                'news_list': news_list,
                'topic_summary': topic_summary,
                'pick_summary': pick_summary
            }
            
        except Exception as e:
            self.logger.error(f"뉴스 리스트 요약 중 오류: {e}")
            # PICK 요약 설정 확인
            pick_summary = []
            if hasattr(self.news_summarizer, 'config') and self.news_summarizer.config.get("enable_pick_summary", True):
                pick_summary = [f"{topic_name} PICK 요약 생성 실패"]
            
            return {
                'news_list': news_list,
                'topic_summary': f"{topic_name} 주제 요약 실패",
                'pick_summary': pick_summary
            }
    
    @robust_function(max_attempts=2, delay=5.0, fallback_func=lambda self: self._generate_emergency_newsletter())
    def generate_newsletter(self):
        """뉴스레터 생성 및 발송 (강화된 에러 복구 포함)"""
        try:
            self.logger.info("뉴스레터 생성 시작")
            
            # 키워드 설정 가져오기
            topics = self.keyword_manager.get_topics()
            
            if not topics:
                self.logger.warning("설정된 키워드가 없습니다.")
                return False
            
            topic_news_dict = {}
            total_news_count = 0
            
            # 각 주제별 뉴스 수집 및 요약
            for topic in topics:
                topic_name = topic["name"]
                self.logger.info(f"주제 '{topic_name}' 처리 시작")
                
                # 뉴스 수집
                news_list = self.collect_news_for_topic(topic)
                self.logger.info(f"주제 '{topic_name}'에서 {len(news_list)}개 뉴스 수집됨")
                
                if news_list:
                    total_news_count += len(news_list)
                    # 뉴스 요약
                    summarized_data = self.summarize_news_list(news_list, topic_name)
                    topic_news_dict[topic_name] = summarized_data
                    self.logger.info(f"주제 '{topic_name}' 요약 완료")
                else:
                    self.logger.warning(f"주제 '{topic_name}'에서 뉴스를 찾을 수 없습니다.")
                    # 뉴스가 없는 경우에도 기본 정보 추가
                    # PICK 요약 설정 확인
                    pick_summary = []
                    if hasattr(self.news_summarizer, 'config') and self.news_summarizer.config.get("enable_pick_summary", True):
                        pick_summary = [f"{topic_name} PICK 요약 생성 실패"]
                    
                    topic_news_dict[topic_name] = {
                        'news_list': [],
                        'topic_summary': f"{topic_name} 관련 최신 뉴스를 찾을 수 없습니다. 나중에 다시 시도해주세요.",
                        'pick_summary': pick_summary
                    }
            
            self.logger.info(f"총 {total_news_count}개 뉴스 수집 완료")
            
            if total_news_count == 0:
                self.logger.warning("수집된 뉴스가 없습니다. 기본 뉴스레터를 생성합니다.")
                # 기본 뉴스레터 내용 생성
                newsletter_content = self.generate_empty_newsletter(topics)
            else:
                # 뉴스레터 내용 생성 (새로운 템플릿 사용)
                newsletter_content = self.generate_newsletter_content_new_template(topic_news_dict)
                
                # 아카이빙 (데이터 및 HTML 저장)
                self.archiver.save_daily_archive(topic_news_dict, newsletter_content)
            
            # 이메일 제목 생성
            subject = f"{os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')} - {datetime.now().strftime('%Y년 %m월 %d일')}"
            
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
                                        안녕하세요! 여행 및 기술 동향 관련 소식을 전해드리는 뉴스레터입니다.
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
                                    <p style="margin: 0 0 8px 0; color: #ffffff; font-size: 12px;">본 이메일은 자동으로 생성되었으며, ChatGPT 4o-mini가 사용되고 있습니다.</p>
                                    <p style="margin: 0; color: #ffffff; font-size: 12px;">© 2025 뉴스레터 자동화 시스템. All rights reserved.</p>
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
        """이메일 클라이언트 호환성을 위한 뉴스레터 템플릿 생성"""
        try:
            current_date = datetime.now().strftime("%Y년 %m월 %d일")
            
            # 이메일 클라이언트 호환성을 위한 테이블 기반 템플릿
            html_content = f"""
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
                                    <td style="background-color: #4a90e2; padding: 30px 20px; text-align: center;">
                                        <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: bold;">[IT본부] 하나투어 뉴스레터</h1>
                                        <p style="margin: 8px 0 0 0; color: #ffffff; font-size: 14px; opacity: 0.9;">
                                            안녕하세요! 여행 및 기술 동향 관련 소식을 전해드리는 뉴스레터입니다.
                                        </p>
                                    </td>
                                </tr>
                                
                                <!-- 콘텐츠 시작 -->
                                <tr>
                                    <td style="padding: 30px 20px;">
            """
            
            # 각 주제별로 뉴스 표시
            for topic_name, topic_data in topic_news_dict.items():
                news_list = topic_data['news_list']
                topic_summary = topic_data['topic_summary']
                pick_summary = topic_data.get('pick_summary', [])
                
                html_content += f"""
                                        <!-- 주제 헤더 -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 25px;">
                                            <tr>
                                                <td style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #4a90e2;">
                                                    <h2 style="margin: 0; color: #2c3e50; font-size: 18px; font-weight: bold;">{topic_name}</h2>
                                                </td>
                                            </tr>
                                        </table>
                """
                
                # PICK 요약 배너를 먼저 표시
                if pick_summary:
                    html_content += f"""
                                        <!-- PICK 요약 배너 -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 20px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px;">
                                            <tr>
                                                <td style="padding: 15px;">
                                                    <h3 style="margin: 0 0 12px 0; color: #856404; font-size: 16px; font-weight: bold;"> {topic_name} PICK 요약</h3>
                                                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                    """
                    
                    for i, pick_item in enumerate(pick_summary, 1):
                        html_content += f"""
                                                        <tr>
                                                            <td style="padding: 4px 0; color: #856404; font-size: 13px; line-height: 1.4;">
                                                                <span style="font-weight: bold; color: #e67e22;">{i}.</span> {pick_item}
                                                            </td>
                                                        </tr>
                        """
                    
                    html_content += """
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>
                    """
                
                # 주제 요약을 PICK 요약 다음에 표시
                html_content += f"""
                                        <!-- 주제 요약 -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 20px; background-color: #f8f9fa; border-radius: 6px; border-left: 3px solid #4a90e2;">
                                            <tr>
                                                <td style="padding: 15px;">
                                                    <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 15px; font-weight: bold;">주제 요약</h3>
                                                    <p style="margin: 0; color: #666666; font-size: 13px; line-height: 1.4;">{topic_summary}</p>
                                                </td>
                                            </tr>
                                        </table>
                """
                
                for i, news in enumerate(news_list, 1):
                    title = news.get('title', '제목 없음')
                    press = news.get('press', '언론사')
                    date = news.get('date', '날짜 없음')
                    summary = news.get('summary', '요약 없음')
                    link = news.get('link', '#')
                    
                    html_content += f"""
                                        <!-- 뉴스 아이템 {i} -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 15px; background-color: #f8f9fa; border-radius: 6px; border-left: 3px solid #4a90e2;">
                                            <tr>
                                                <td style="padding: 15px;">
                                                    <h3 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 15px; font-weight: bold; line-height: 1.3;">{i}. {title}</h3>
                                                    <p style="margin: 0 0 8px 0; color: #666666; font-size: 11px;">{press} | {date}</p>
                                                    <p style="margin: 0 0 10px 0; color: #555555; font-size: 13px; line-height: 1.4;">{summary}</p>
                                                    <a href="{link}" target="_blank" style="color: #4a90e2; text-decoration: none; font-size: 12px; font-weight: 500;">원문 보기</a>
                                                </td>
                                            </tr>
                                        </table>
                    """
            
            html_content += """
                                    </td>
                                </tr>
                                
                                <!-- 푸터 -->
                                <tr>
                                    <td style="background-color: #2c3e50; padding: 20px; text-align: center;">
                                        <p style="margin: 0 0 8px 0; color: #ffffff; font-size: 12px;">본 이메일은 자동으로 생성되었으며, ChatGPT 4o-mini가 사용되고 있습니다.</p>
                                        <p style="margin: 0; color: #ffffff; font-size: 12px;">© 2025 뉴스레터 자동화 시스템. All rights reserved.</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"이메일 호환 템플릿 뉴스레터 생성 실패: {e}")
            # 기존 템플릿으로 폴백
            return self.news_summarizer.generate_newsletter_content(topic_news_dict)
    
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
            
            # 2. 뉴스 수집 테스트 (첫 번째 주제의 첫 번째 키워드만)
            self.logger.info("2. 뉴스 수집 테스트 중...")
            first_topic = topics[0]
            first_keyword = first_topic["keywords"][0] if first_topic["keywords"] else "테스트"
            test_news = self.news_collector.search_naver_news_with_retry(first_keyword, 2)
            if not test_news:
                self.logger.warning("뉴스 수집 테스트에서 뉴스를 찾지 못했습니다.")
            else:
                self.logger.info(f"뉴스 수집 테스트 완료 - {len(test_news)}개 뉴스")
            
            # 3. AI 요약 테스트
            self.logger.info("3. AI 요약 테스트 중...")
            if test_news:
                # 첫 번째 뉴스의 내용이 부족할 수 있으므로 안전하게 처리
                test_news_item = test_news[0]
                if 'full_content' not in test_news_item:
                    test_news_item['full_content'] = test_news_item.get('content_preview', test_news_item.get('title', ''))
                
                test_summary = self.news_summarizer.summarize_news(test_news_item)
                if test_summary and not test_summary.startswith("요약 실패"):
                    self.logger.info("AI 요약 테스트 완료")
                else:
                    self.logger.warning("AI 요약 테스트 실패")
            else:
                self.logger.info("AI 요약 테스트 건너뜀 (테스트 뉴스 없음)")
            
            # 4. 이메일 설정 확인
            self.logger.info("4. 이메일 설정 확인 중...")
            receiver_count = self.email_sender.get_receiver_count()
            recipient_stats = self.email_sender.get_recipient_stats()
            self.logger.info(f"이메일 설정 확인 완료 - {receiver_count}명의 수신자")
            self.logger.info(f"수신자 통계: 전체 {recipient_stats['total']}명, 활성 {recipient_stats['active']}명, 비활성 {recipient_stats['inactive']}명")
            
            # 5. 테스트 이메일 발송
            self.logger.info("5. 테스트 이메일 발송 중...")
            test_email_success = self.email_sender.send_test_email()
            if test_email_success:
                self.logger.info("테스트 이메일 발송 완료")
            else:
                self.logger.warning("테스트 이메일 발송 실패")
            
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