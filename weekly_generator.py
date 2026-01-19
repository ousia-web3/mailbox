import os
import json
import logging
from datetime import datetime, timedelta
from date_utils import get_last_week_range, get_newsletter_title_date, get_date_range_str
from news_summarizer_v2 import NewsSummarizerV2
from email_sender import EmailSender

class WeeklyNewsletterGenerator:
    """주간 뉴스레터 생성기"""
    
    def __init__(self):
        self.setup_logging()
        self.news_summarizer = NewsSummarizerV2()
        self.email_sender = EmailSender()
        self.base_dir = 'archives/daily'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def load_weekly_data(self):
        """최근 5일간의 JSON 데이터를 모두 로드하여 병합"""
        # 최근 5일 데이터 수집 (오늘 포함)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=4)  # 오늘 포함 5일
        
        self.logger.info(f"주간 데이터 로드 범위 (최근 5일): {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
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
                        
                    # 실제 구조: topics -> raw_news -> {카테고리: [뉴스리스트]}
                    topics_data = daily_data.get('topics', {})
                    raw_news = topics_data.get('raw_news', {})
                    
                    if isinstance(raw_news, dict):
                        for topic, news_list in raw_news.items():
                            if topic not in merged_data:
                                merged_data[topic] = []
                            
                            # 뉴스 리스트 병합
                            if isinstance(news_list, list):
                                merged_data[topic].extend(news_list)
                        
                        self.logger.info(f"데이터 로드 성공: {date_str} ({len(raw_news)} 카테고리)")
                    else:
                        self.logger.warning(f"raw_news가 dict가 아님: {date_str}")
                        
                except Exception as e:
                    self.logger.error(f"데이터 로드 실패 ({date_str}): {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())
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
            
            # 모든 뉴스 통합
            all_news_list = []
            for topic, news_list in weekly_raw_data.items():
                all_news_list.extend(news_list)
                
            self.logger.info(f"총 {len(all_news_list)}개의 뉴스 수집됨")
                
            # 2. AI 큐레이션 (Top 10 및 인사이트)
            curated_result = self.news_summarizer.curate_weekly_top_10(all_news_list)
            if not curated_result:
                self.logger.error("AI 큐레이션 실패")
                return False
            
            # 3. HTML 생성
            html_content = self.generate_html_template(curated_result)
            
            
            # 4. 발송 (테스트 모드: 발송 생략)
            title_date = get_newsletter_title_date()
            subject = f"[IT본부] 하나투어 주간 뉴스레터 ({title_date})"
            
            success = self.email_sender.send_newsletter(subject, html_content)
            # self.logger.info("테스트 모드: 메일 발송을 건너뜁니다.")
            # success = True # 테스트를 위해 성공으로 간주
            
            if success:
                self.logger.info("주간 뉴스레터 생성 완료 (발송 생략)")
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

    def generate_html_template(self, curated_result):
        """주간 뉴스레터 HTML 템플릿 생성"""
        try:
            # 템플릿 파일 읽기
            template_path = os.path.join('templates', 'weekly_newsletter.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
                
            title_date = get_newsletter_title_date()
            
            # 1. 기본 정보 치환
            html = html_template.replace('{{TITLE_DATE}}', title_date)
            
            # 2. Insight 치환
            insight = curated_result.get('weekly_insight', {})
            html = html.replace('{{WEEKLY_INSIGHT_TITLE}}', insight.get('title', 'Weekly Insight'))
            html = html.replace('{{WEEKLY_INSIGHT_CONTENT}}', insight.get('content', '내용이 없습니다.'))
            
            # 3. Top 10 리스트 생성 (Table Layout for Email Compatibility)
            top_10_html = ""
            for item in curated_result.get('top_10', []):
                rank = item.get('rank', 0)
                
                top_10_html += f"""
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom: 20px; border-bottom: 1px solid #f1f5f9; padding-bottom: 20px;">
              <tr>
                <td valign="top" width="40" style="padding-right: 12px;">
                  <div style="font-size: 24px; font-weight: 800; color: #5e2bb8; line-height: 1;">{rank:02d}</div>
                </td>
                <td valign="top">
                  <a href="{item.get('link', '#')}" target="_blank" style="font-size: 16px; font-weight: 600; color: #1e293b; text-decoration: none; display: block; margin-bottom: 8px; line-height: 1.4;">{item.get('title', '')}</a>
                  <p style="font-size: 15px; line-height: 1.7; color: #64748b; margin: 0;">
                    {item.get('summary', '')}
                    <a href="#news-{rank}" style="display: inline-block; padding: 1px 6px; background-color: #f8fafc; color: #475569; border: 1px solid #e2e8f0; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: 600; margin-left: 4px; vertical-align: 1px;">{rank}</a>
                  </p>
                </td>
              </tr>
            </table>
                """
            html = html.replace('{{TOP_10_ITEMS}}', top_10_html)
            
            # 4. In Other News 리스트 생성 (Table Layout for Email Compatibility)
            other_news_html = ""
            for item in curated_result.get('top_10', []):
                rank = item.get('rank', 0)
                other_news_html += f"""
              <table id="news-{rank}" width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom: 12px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 12px;">
                <tr>
                  <td valign="top" width="30">
                    <span style="display: inline-block; width: 20px; height: 20px; background-color: #334155; color: #ffffff; border-radius: 4px; text-align: center; line-height: 20px; font-size: 11px; font-weight: 700;">{rank}</span>
                  </td>
                  <td valign="top">
                    <a href="{item.get('link', '#')}" target="_blank" style="font-size: 14px; color: #475569; text-decoration: none; line-height: 1.6; display: block;">
                      {item.get('title', '')}
                    </a>
                  </td>
                </tr>
              </table>
                """
            html = html.replace('{{OTHER_NEWS_ITEMS}}', other_news_html)
            
            return html
            
        except Exception as e:
            self.logger.error(f"HTML 템플릿 생성 중 오류: {e}")
            return "HTML 생성 실패"

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
