import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# 부모 디렉토리를 sys.path에 추가하여 모듈 import 가능하게 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 기존 모듈 import
from windows_utf8 import setup_windows_utf8
from logging_config import setup_utf8_logging
from news_collector_working import WorkingNewsCollector
from news_summarizer_v2 import NewsSummarizerV2
from keyword_manager import KeywordManager

# Windows UTF-8 설정
setup_windows_utf8()

class NewsletterTesterV2:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.keyword_manager = KeywordManager()
        self.news_collector = WorkingNewsCollector()
        self.news_summarizer = NewsSummarizerV2()
        
    def setup_logging(self):
        self.logger = setup_utf8_logging(
            logger_name=__name__,
            log_file='test_v2.log',
            level=logging.INFO
        )

    def run_test(self):
        self.logger.info("V2 뉴스레터 테스트 시작")
        
        # 1. 키워드 가져오기
        topics = self.keyword_manager.get_topics()
        if not topics:
            self.logger.error("키워드 설정이 없습니다.")
            return

        newsletter_sections = []

        # 2. 주제별 뉴스 수집 및 요약
        for topic in topics:
            topic_name = topic["name"]
            keywords = topic["keywords"]
            
            self.logger.info(f"주제 '{topic_name}' 처리 중...")
            
            # 뉴스 수집 (기존 로직 사용 - 어제 날짜 기준)
            # 테스트를 위해 각 주제별 첫 번째 키워드로만 3개 수집 (빠른 테스트)
            # 실제 운영 시에는 collect_news_for_topic 로직 사용
            
            all_topic_news = []
            
            # 테스트용: 모든 키워드 사용
            test_keywords = keywords
            
            for keyword in test_keywords:
                # 수집 대상 날짜 설정 (월요일은 토~일, 그 외는 전날)
                target_date = self.news_collector.get_target_search_date()
                # 날짜 필터링으로 인해 많이 제외되므로 넉넉하게 20개 수집 요청 후 상위 5개만 선택
                news_list = self.news_collector.search_naver_news_with_retry(keyword, 20, target_date)
                news_list = news_list[:5]  # 키워드당 최대 5개 제한
                
                # 중복 제거하며 추가
                for news in news_list:
                    if not any(n['link'] == news['link'] for n in all_topic_news):
                        all_topic_news.append(news)
            
            if not all_topic_news:
                self.logger.warning(f"주제 '{topic_name}' 뉴스가 없습니다. (테스트를 위해 더미 데이터 생성)")
                # 템플릿 테스트를 위한 더미 데이터
                all_topic_news.append({
                    'title': f'{topic_name} 관련 혁신적인 기술 발표',
                    'link': 'https://example.com',
                    'press': '테크뉴스',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'full_content': f'{topic_name} 분야에서 새로운 혁신이 일어났습니다. 이 기술은 업계의 판도를 바꿀 것으로 기대됩니다. 주요 기업들이 앞다투어 도입을 검토하고 있습니다.',
                    'content_preview': f'{topic_name} 혁신 기술 발표...'
                })
                
            self.logger.info(f"주제 '{topic_name}' 뉴스 {len(all_topic_news)}개 수집 완료. V2 요약 진행...")
            print(f"DEBUG: 주제 '{topic_name}' 수집된 뉴스 개수: {len(all_topic_news)}")
            
            # V2 요약 (페르소나 프롬프트 적용)
            summary_text = self.news_summarizer.summarize_topic_with_persona(all_topic_news, topic_name)
            
            newsletter_sections.append({
                "topic": topic_name,
                "content": summary_text
            })

        # 3. HTML 생성
        html_content = self.generate_html(newsletter_sections)
        
        # 4. 파일 저장
        output_file = f"v2_newsletter_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        self.logger.info(f"테스트 완료. 결과 파일: {output_file}")
        print(f"✅ 테스트 완료! 결과 파일이 생성되었습니다: {output_file}")

    def generate_html(self, sections):
        """AI가 생성한 텍스트를 파싱하여 이메일 템플릿 HTML로 변환 (new_templates.html 스타일 적용)"""
        
        # 날짜 한글 요일 처리
        days = ["월", "화", "수", "목", "금", "토", "일"]
        day_str = days[datetime.now().weekday()]
        current_date = datetime.now().strftime(f"%Y년 %m월 %d일 ({day_str})")
        
        # new_templates.html 기반 스타일 및 구조
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>[IT본부] 하나투어 비즈니스 & 테크 브리핑</title>
            <style>
                body {{ margin: 0; padding: 0; font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif; background-color: #f8f9fa; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
                .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 40px 20px; text-align: center; color: #ffffff; }}
                .summary-box {{ margin: -20px 20px 30px; background-color: #f0f7ff; border: 1px solid #d1e9ff; border-radius: 12px; padding: 20px; }}
                .section-title {{ margin: 40px 20px 15px; padding-bottom: 8px; border-bottom: 2px solid #3b82f6; color: #1e3a8a; font-size: 20px; font-weight: 800; }}
                .news-card {{ margin: 0 20px 20px; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; transition: transform 0.2s; background-color: #ffffff; }}
                .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; margin-bottom: 10px; text-transform: uppercase; }}
                .badge-it {{ background-color: #e0f2fe; color: #0369a1; }}
                .badge-ai {{ background-color: #fef3c7; color: #92400e; }}
                .badge-travel {{ background-color: #dcfce7; color: #166534; }}
                .badge-default {{ background-color: #f3f4f6; color: #4b5563; }}
                .news-title {{ font-size: 17px; font-weight: 700; line-height: 1.4; color: #111827; margin: 0 0 10px 0; }}
                .news-desc {{ font-size: 14px; line-height: 1.6; color: #4b5563; margin-bottom: 12px; }}
                .insight-box {{ background-color: #f9fafb; border-left: 3px solid #3b82f6; padding: 10px 15px; margin-bottom: 15px; font-size: 13px; color: #374151; font-style: italic; }}
                .btn-link {{ display: inline-block; color: #3b82f6; text-decoration: none; font-size: 13px; font-weight: 600; }}
                .footer {{ background-color: #1f2937; padding: 30px 20px; text-align: center; color: #9ca3af; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div style="padding: 20px 0;">
                <div class="container">
                    <!-- 헤더 -->
                    <div class="header">
                        <div style="font-size: 12px; opacity: 0.8; letter-spacing: 2px; margin-bottom: 10px;">DAILY BRIEFING</div>
                        <h1 style="margin: 0; font-size: 24px;">하나투어 비즈니스 & 테크</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">{current_date}</p>
                    </div>
        """
        
        # 3줄 요약 통합 (각 주제별 1줄씩 모아서 구성)
        combined_summary = ""
        for section in sections:
            text = section['content']
            # "분야 핵심 요약" 섹션 찾기
            if "분야 핵심 요약" in text:
                parts = text.split("개별 뉴스 카드")
                summary_part = parts[0]
                lines = summary_part.split('\n')
                for line in lines:
                    clean_line = line.strip()
                    if clean_line.startswith('•'):
                        # 끝부분 특수문자 제거 및 HTML 추가
                        clean_line = self.clean_text(clean_line)
                        combined_summary += f"{clean_line}<br>"
            # 하위 호환성 (혹시 구버전 프롬프트 결과가 있을 경우)
            elif "3줄 컷" in text:
                parts = text.split("개별 뉴스 카드")
                summary_part = parts[0]
                lines = summary_part.split('\n')
                # 첫 번째 불릿만 가져옴 (중복 방지)
                for line in lines:
                    clean_line = line.strip()
                    if clean_line.startswith('•'):
                        clean_line = self.clean_text(clean_line)
                        combined_summary += f"{clean_line}<br>"
                        break # 1줄만 가져오기
        
        if combined_summary:
            html += f"""
                    <!-- 핵심 요약 -->
                    <div class="summary-box">
                        <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #1e40af;">⚡ 오늘 소식 3줄 컷</h3>
                        <div style="font-size: 14px; line-height: 1.8; color: #374151;">
                            {combined_summary}
                        </div>
                    </div>
            """

        for section in sections:
            topic = section['topic']
            text = section['content']
            
            # 섹션 제목 매핑
            section_title_map = {
                "IT": "Technology Trends",
                "AI": "AI Insight",
                "여행": "Travel & Business"
            }
            display_title = section_title_map.get(topic, f"{topic} Trends")
            
            html += f"""
                    <div class="section-title">{display_title}</div>
            """
            
            # 뉴스 카드 파싱
            if "개별 뉴스 카드" in text:
                news_cards_part = text.split("개별 뉴스 카드")[1]
                cards = news_cards_part.split("• [")
                
                for card in cards:
                    if not card.strip() or "배지 이름" in card: continue
                    
                    # 배지 추출
                    badge_end = card.find("]")
                    badge = card[:badge_end] if badge_end != -1 else "General"
                    card_content = card[badge_end+1:]
                    
                    # 배지 스타일 결정
                    badge_class = "badge-default"
                    if "Future" in badge: badge_class = "badge-it"
                    elif "Market" in badge: badge_class = "badge-ai"
                    elif "Industry" in badge: badge_class = "badge-travel"
                    elif "Innovation" in badge: badge_class = "badge-travel"
                    
                    # 제목, 요약, 인사이트, 링크 추출 및 정제
                    title = self.clean_text(self.extract_field(card_content, "제목:"))
                    summary = self.clean_text(self.extract_field(card_content, "요약:"))
                    insight = self.clean_text(self.extract_field(card_content, "인사이트:"))
                    # 링크 추출 (다양한 패턴 시도)
                    link = self.extract_field(card_content, "링크:").strip()
                    if not link:
                        link = self.extract_field(card_content, "Link:").strip()
                    if not link:
                        link = self.extract_field(card_content, "URL:").strip()
                    
                    # 링크에서 불필요한 괄호나 텍스트 제거
                    if link.startswith('(') and link.endswith(')'):
                        link = link[1:-1]
                    
                    # 링크가 없거나 유효하지 않으면 해당 뉴스 카드 제외
                    if not link or link.lower() == "none" or link == "" or link == "#":
                        continue
                    
                    if title:
                        html += f"""
                        <div class="news-card">
                            <span class="badge {badge_class}">{badge}</span>
                            <h3 class="news-title">{title}</h3>
                            <p class="news-desc">{summary}</p>
                            <div class="insight-box">
                                {insight.replace('💡 Insight:', '💡 <b>Insight:</b>')}
                            </div>
                            <a href="{link}" target="_blank" class="btn-link">원문 읽기 →</a>
                        </div>
                        """

        html += """
                    <!-- 푸터 -->
                    <div class="footer">
                        <p style="margin-bottom: 5px;">본 이메일은 자동으로 생성되었으며, 구글 제미나이 2.5가 사용되고 있습니다.</p>
                        <p style="margin-bottom: 10px;"></p>
                        <p style="margin-bottom: 5px;">© 2026 HANATOUR IT Division. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def clean_text(self, text):
        """텍스트 끝의 불필요한 특수문자 제거"""
        if not text: return ""
        # 오른쪽 끝의 *, •, 공백 제거 (반복적으로)
        cleaned = text.strip()
        while cleaned and (cleaned.endswith('*') or cleaned.endswith('•')):
            cleaned = cleaned.rstrip('*').rstrip('•').strip()
        return cleaned

    def extract_field(self, text, field_name):
        """텍스트에서 특정 필드 값 추출"""
        start = text.find(field_name)
        if start == -1: return ""
        
        start += len(field_name)
        # 다음 필드 찾기 (순서: 제목 -> 요약 -> 인사이트 -> 링크)
        next_fields = ["요약:", "인사이트:", "링크:", "• ["]
        end = len(text)
        
        for nf in next_fields:
            nf_idx = text.find(nf, start)
            if nf_idx != -1 and nf_idx < end:
                end = nf_idx
                
        return text[start:end].strip()

if __name__ == "__main__":
    tester = NewsletterTesterV2()
    tester.run_test()
