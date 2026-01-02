import os
import json
import logging
import re
from datetime import datetime, timedelta
from date_utils import get_last_month_range, get_date_range_str
from news_summarizer import NewsSummarizer
from email_sender import EmailSender

class MonthlyNewsletterGenerator:
    """월간 뉴스레터 생성기"""
    
    def __init__(self):
        self.setup_logging()
        self.news_summarizer = NewsSummarizer()
        self.email_sender = EmailSender()
        self.base_dir = 'archives/weekly'
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def load_monthly_data(self):
        """지난달의 주간 뉴스레터 HTML 파일에서 데이터를 추출 (또는 별도 저장된 데이터 활용)
        여기서는 주간 뉴스레터 생성 시 별도 데이터 저장을 안 했으므로,
        데일리 데이터를 월 단위로 모두 긁어오거나, 
        주간 뉴스레터 생성 시 데이터를 저장하도록 수정했어야 함.
        
        대안: 데일리 아카이브(JSON)를 월 단위로 모두 스캔하여 '큐레이션' 다시 수행
        """
        start_date, end_date = get_last_month_range()
        self.logger.info(f"월간 데이터 로드 범위: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        all_news = []
        weekly_insights = [] # 주간 인사이트는 별도 저장 안 했으므로, 이번엔 뉴스 데이터만으로 새로 분석
        
        # 데일리 아카이브 순회
        current_date = start_date
        while current_date <= end_date:
            year = current_date.strftime("%Y")
            month = current_date.strftime("%m")
            date_str = current_date.strftime("%Y%m%d")
            
            file_path = os.path.join('archives/daily', year, month, f"daily_news_{date_str}.json")
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        daily_data = json.load(f)
                    
                    topics_data = daily_data.get('topics', {})
                    for topic, content in topics_data.items():
                        news_list = content.get('news_list', [])
                        all_news.extend(news_list)
                        
                except Exception as e:
                    pass
            
            current_date += timedelta(days=1)
            
        self.logger.info(f"월간 전체 뉴스 로드 완료: {len(all_news)}개")
        return all_news

    def generate_monthly_newsletter(self):
        """월간 뉴스레터 생성 및 발송"""
        try:
            self.logger.info("월간 뉴스레터 생성 시작")
            
            # 1. 데이터 로드
            all_news = self.load_monthly_data()
            if not all_news:
                self.logger.error("월간 데이터가 없습니다.")
                return False
            
            # 2. 월간 베스트 뉴스 선정 (전체 뉴스 중 Top 5)
            best_news = self.news_summarizer.select_monthly_best_news(all_news)
            
            # 3. 월간 트렌드 리포트 생성
            # 주간 인사이트 데이터가 없으므로, 베스트 뉴스와 전체 요약을 기반으로 생성 시도
            # 임시로 주차별로 데이터를 나누어 인사이트를 생성하는 과정은 생략하고,
            # 전체 뉴스 요약을 기반으로 트렌드 리포트 생성
            
            # 뉴스 요약본만 모아서 프롬프트 입력으로 사용
            news_summaries = [n['summary'] for n in all_news[:50]] # 토큰 제한으로 50개만
            
            # 가상의 주간 인사이트 리스트 생성 (프롬프트 재활용을 위해)
            # 실제로는 news_summarizer.generate_monthly_trend_report가 주간 인사이트 리스트를 받음
            # 여기서는 텍스트 덩어리로 전달
            trend_report = self.news_summarizer.generate_monthly_trend_report(news_summaries)
            
            # 4. HTML 생성
            html_content = self.generate_html_template(trend_report, best_news)
            
            # 5. 발송
            start_date, _ = get_last_month_range()
            month_name = start_date.strftime("%m월")
            subject = f"[Monthly] {month_name} 하나투어 IT 트렌드 리포트"
            
            success = self.email_sender.send_newsletter(subject, html_content)
            
            if success:
                self.logger.info("월간 뉴스레터 발송 완료")
                self.archive_monthly_html(html_content)
                return True
            else:
                self.logger.error("월간 뉴스레터 발송 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"월간 뉴스레터 생성 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
            
    def generate_html_template(self, trend_report, best_news):
        """월간 뉴스레터 HTML 템플릿"""
        start_date, _ = get_last_month_range()
        month_str = start_date.strftime("%m월")
        
        # 마크다운 -> HTML 변환 (간이)
        trend_report_html = trend_report.replace('\n', '<br>')
        trend_report_html = re.sub(r'## (.*?)(<br>|$)', r'<h3 style="color: #2c3e50; margin-top: 20px;">\1</h3>', trend_report_html)
        trend_report_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', trend_report_html)
        
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{month_str} IT 트렌드 리포트</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background-color: #f4f4f4;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f4f4;">
                <tr>
                    <td align="center" style="padding: 20px 0;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                            <!-- 헤더 -->
                            <tr>
                                <td style="background-color: #1a2980; background: linear-gradient(135deg, #1a2980 0%, #26d0ce 100%); padding: 50px 30px; text-align: center;">
                                    <span style="background-color: #3a4a9f; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; letter-spacing: 1px; display: inline-block; margin-bottom: 15px;">MONTHLY REPORT</span>
                                    <h1 style="margin: 0 0 10px 0; color: #ffffff; font-size: 32px; font-weight: 800; letter-spacing: -0.5px;">{month_str} IT 트렌드</h1>
                                    <p style="margin: 0; color: #eeeeee; font-size: 15px;">하나투어 IT본부 | 월간 기술 & 여행 동향</p>
                                </td>
                            </tr>
                            
                            <!-- 트렌드 리포트 -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <div style="margin-bottom: 40px;">
                                        <h2 style="margin: 0 0 20px 0; color: #1a2980; font-size: 22px; font-weight: 700; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                                            📊 이달의 트렌드 분석
                                        </h2>
                                        <div style="color: #444; font-size: 15px; line-height: 1.7;">
                                            {trend_report_html}
                                        </div>
                                    </div>
                                    
                                    <!-- Best News -->
                                    <div>
                                        <h2 style="margin: 0 0 20px 0; color: #1a2980; font-size: 22px; font-weight: 700; border-bottom: 2px solid #eee; padding-bottom: 10px;">
                                            🏆 Best of Best News
                                        </h2>
        """
        
        for i, news in enumerate(best_news, 1):
            html += f"""
                                        <div style="margin-bottom: 25px; background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                                            <div style="font-size: 12px; color: #1a2980; font-weight: 700; margin-bottom: 5px;">BEST {i}</div>
                                            <h3 style="margin: 0 0 10px 0; font-size: 17px; font-weight: 700; line-height: 1.4;">
                                                <a href="{news.get('link', '#')}" target="_blank" style="color: #2c3e50; text-decoration: none;">{news.get('title', '')}</a>
                                            </h3>
                                            <p style="margin: 0 0 10px 0; color: #555; font-size: 14px; line-height: 1.6;">
                                                {news.get('summary', '')}
                                            </p>
                                            <div style="font-size: 12px; color: #888;">
                                                {news.get('press', '')} | {news.get('date', '')}
                                            </div>
                                        </div>
            """
            
        html += """
                                </td>
                            </tr>
                            
                            <!-- 푸터 -->
                            <tr>
                                <td style="background-color: #1a2980; padding: 30px; text-align: center;">
                                    <p style="margin: 0 0 10px 0; color: #ffffff; font-size: 14px; font-weight: 600;">하나투어 IT본부</p>
                                    <p style="margin: 0; color: rgba(255,255,255,0.6); font-size: 12px;">Monthly IT Trend Report</p>
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

    def archive_monthly_html(self, html_content):
        """월간 뉴스레터 아카이빙"""
        try:
            now = datetime.now()
            year = now.strftime("%Y")
            save_dir = os.path.join('archives', 'monthly', year)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                
            date_str = now.strftime("%Y%m")
            filename = f"monthly_newsletter_{date_str}.html"
            path = os.path.join(save_dir, filename)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"월간 뉴스레터 아카이빙 완료: {path}")
        except Exception as e:
            self.logger.error(f"월간 뉴스레터 아카이빙 실패: {e}")

if __name__ == "__main__":
    generator = MonthlyNewsletterGenerator()
    generator.generate_monthly_newsletter()
