import os
import json
import logging
from datetime import datetime, timedelta
from date_utils import get_last_week_range, get_newsletter_title_date, get_date_range_str
from news_summarizer import NewsSummarizer
from email_sender import EmailSender

class WeeklyNewsletterGenerator:
    """주간 뉴스레터 생성기"""
    
    def __init__(self):
        self.setup_logging()
        self.news_summarizer = NewsSummarizer()
        self.email_sender = EmailSender()
        self.base_dir = 'archives/daily'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def load_weekly_data(self):
        """지난주(월~일)의 JSON 데이터를 모두 로드하여 병합"""
        start_date, end_date = get_last_week_range()
        self.logger.info(f"주간 데이터 로드 범위: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        merged_data = {} # {topic: [news_list]}
        
        current_date = start_date
        while current_date <= end_date:
            year = current_date.strftime("%Y")
            month = current_date.strftime("%m")
            date_str = current_date.strftime("%Y%m%d")
            
            # 파일 경로: archives/daily/{YYYY}/{MM}/daily_news_{YYYYMMDD}.json
            file_path = os.path.join(self.base_dir, year, month, f"daily_news_{date_str}.json")
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)
                        
                    topics_data = daily_data.get('topics', {})
                    for topic, content in topics_data.items():
                        if topic not in merged_data:
                            merged_data[topic] = []
                        
                        # 뉴스 리스트 병합
                        news_list = content.get('news_list', [])
                        merged_data[topic].extend(news_list)
                        
                    self.logger.info(f"데이터 로드 성공: {date_str}")
                except Exception as e:
                    self.logger.error(f"데이터 로드 실패 ({date_str}): {e}")
            else:
                self.logger.warning(f"데이터 파일 없음: {file_path}")
                
            current_date += timedelta(days=1)
            
        return merged_data
        
    def generate_weekly_newsletter(self):
        """주간 뉴스레터 생성 및 발송 메인 로직"""
        try:
            self.logger.info("주간 뉴스레터 생성 시작")
            
            # 1. 데이터 로드
            weekly_raw_data = self.load_weekly_data()
            if not weekly_raw_data:
                self.logger.error("주간 데이터가 없습니다.")
                return False
                
            # 2. AI 큐레이션 및 요약
            curated_data = {}
            for topic, news_list in weekly_raw_data.items():
                self.logger.info(f"주제 '{topic}' 큐레이션 시작 (총 {len(news_list)}개 뉴스)")
                
                # Top 5 선별
                top_news = self.news_summarizer.curate_weekly_news(news_list, topic)
                
                # 주간 주제 요약 (선별된 뉴스 기반)
                topic_summary = self.news_summarizer.summarize_topic_news(top_news, topic)
                
                curated_data[topic] = {
                    'news_list': top_news,
                    'topic_summary': topic_summary
                }
            
            # 3. Weekly Insight 생성
            weekly_insight = self.news_summarizer.generate_weekly_insight(curated_data)
            
            # 4. HTML 생성
            html_content = self.generate_html_template(curated_data, weekly_insight)
            
            # 5. 발송
            title_date = get_newsletter_title_date()
            subject = "[IT본부] 하나투어 주간 뉴스레터"
            
            success = self.email_sender.send_newsletter(subject, html_content)
            
            if success:
                self.logger.info("주간 뉴스레터 발송 완료")
                # 주간 뉴스레터도 아카이빙 (HTML 저장)
                self.archive_weekly_html(html_content)
                return True
            else:
                self.logger.error("주간 뉴스레터 발송 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"주간 뉴스레터 생성 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def generate_html_template(self, curated_data, weekly_insight):
        """주간 뉴스레터 HTML 템플릿 생성"""
        title_date = get_newsletter_title_date()
        start_date, end_date = get_last_week_range()
        date_range_str = get_date_range_str(start_date, end_date)
        
        # Insight 파싱 (키워드, 트렌드, 시사점 분리)
        # 마크다운 볼드(**)를 HTML strong 태그로 변환
        import re
        # 1. 마크다운 볼드(**)를 HTML strong 태그로 변환
        weekly_insight_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', weekly_insight)
        
        # 2. 각 섹션(핵심 키워드, 주간 트렌드, 비즈니스 시사점) 앞에 줄바꿈 추가
        # "<strong>...</strong>:" 패턴 앞에 <br><br> 추가 (단, 맨 처음은 제외)
        weekly_insight_html = re.sub(r'(?<!^)(<strong>.*?</strong>:)', r'<br><br>\1', weekly_insight_html)
        
        # 3. 나머지 줄바꿈 처리
        weekly_insight_html = weekly_insight_html.replace('\n', ' ')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title_date} 하나투어 IT 뉴스레터</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background-color: #f4f4f4;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f4f4;">
                <tr>
                    <td align="center" style="padding: 20px 0;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                            <!-- 헤더 -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #5E2BB8 0%, #4a90e2 100%); padding: 40px 30px; text-align: center;">
                                    <span style="background-color: rgba(255,255,255,0.2); color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; letter-spacing: 1px;">WEEKLY NEWSLETTER</span>
                                    <h1 style="margin: 15px 0 10px 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">{title_date}</h1>
                                    <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 14px;">{date_range_str} | IT본부</p>
                                </td>
                            </tr>
                            
                            <!-- Weekly Insight -->
                            <tr>
                                <td style="padding: 30px;">
                                    <div style="background-color: #f8f9fa; border-left: 4px solid #5E2BB8; padding: 20px; border-radius: 4px;">
                                        <h2 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 18px; font-weight: 700;">💡 Weekly Insight</h2>
                                        <div style="color: #444; font-size: 14px; line-height: 1.6;">
                                            {weekly_insight_html}
                                        </div>
                                    </div>
                                </td>
                            </tr>
        """
        
        for topic, data in curated_data.items():
            news_list = data['news_list']
            
            html += f"""
                            <!-- {topic} 섹션 -->
                            <tr>
                                <td style="padding: 0 30px 30px 30px;">
                                    <h2 style="margin: 0 0 20px 0; color: #2c3e50; font-size: 20px; font-weight: 700; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                                        <span style="color: #5E2BB8;">#</span> {topic}
                                    </h2>
            """
            
            for i, news in enumerate(news_list, 1):
                html += f"""
                                    <div style="margin-bottom: 20px;">
                                        <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 600; line-height: 1.4;">
                                            <span style="color: #5E2BB8; margin-right: 5px;">{i}.</span>
                                            <a href="{news.get('link', '#')}" target="_blank" style="color: #2c3e50; text-decoration: none;">{news.get('title', '')}</a>
                                        </h3>
                                        <p style="margin: 0 0 8px 0; color: #666; font-size: 13px; line-height: 1.5;">
                                            {news.get('summary', '')}
                                        </p>
                                        <div style="font-size: 11px; color: #999;">
                                            <a href="{news.get('link', '#')}" target="_blank" style="color: #999; text-decoration: none;">{news.get('press', '')} | {news.get('date', '')}</a>
                                        </div>
                                    </div>
                """
                
            html += """
                                </td>
                            </tr>
            """
            
        html += """
                            <!-- 푸터 -->
                            <tr>
                                <td style="background-color: #2c3e50; padding: 30px; text-align: center;">
                                    <p style="margin: 0 0 10px 0; color: #ffffff; font-size: 14px; font-weight: 600;">하나투어 IT본부</p>
                                    <p style="margin: 0; color: #8898aa; font-size: 12px;">본 이메일은 자동으로 생성되었으며, ChatGPT 4o-mini가 사용되고 있습니다.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        return html

    def archive_weekly_html(self, html_content):
        """주간 뉴스레터 HTML 아카이빙"""
        try:
            now = datetime.now()
            year = now.strftime("%Y")
            # 주간 뉴스레터는 별도 weekly 폴더에 저장
            save_dir = os.path.join('archives', 'weekly', year)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                
            date_str = now.strftime("%Y%m%d")
            filename = f"weekly_newsletter_{date_str}.html"
            path = os.path.join(save_dir, filename)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"주간 뉴스레터 아카이빙 완료: {path}")
        except Exception as e:
            self.logger.error(f"주간 뉴스레터 아카이빙 실패: {e}")

if __name__ == "__main__":
    # 테스트 실행
    generator = WeeklyNewsletterGenerator()
    generator.generate_weekly_newsletter()
