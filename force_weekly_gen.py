import os
import logging
from datetime import datetime, timedelta
from weekly_generator import WeeklyNewsletterGenerator

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def force_generate_weekly_with_today():
    """오늘 생성된 데일리 데이터를 강제로 포함하여 주간 뉴스레터 HTML 생성"""
    logger.info("주간 뉴스레터 강제 생성 시작 (오늘 데이터 포함)")
    
    generator = WeeklyNewsletterGenerator()
    
    # 1. 날짜 범위를 '오늘'로 강제 설정하여 데이터 로드
    # 원래는 get_last_week_range()를 쓰지만, 여기서는 오늘 날짜만 타겟팅
    today = datetime.now()
    start_date = today
    end_date = today
    
    logger.info(f"데이터 로드 범위 강제 설정: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    # load_weekly_data 메서드는 내부적으로 get_last_week_range를 호출하므로,
    # 여기서는 직접 로직을 구현해서 데이터를 가져옵니다.
    all_news = []
    current_date = start_date
    while current_date <= end_date:
        year = current_date.strftime("%Y")
        month = current_date.strftime("%m")
        date_str = current_date.strftime("%Y%m%d")
        
        file_path = os.path.join('archives/daily', year, month, f"daily_news_{date_str}.json")
        
        if os.path.exists(file_path):
            import json
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    daily_data = json.load(f)
                
                topics_data = daily_data.get('topics', {})
                for topic, content in topics_data.items():
                    news_list = content.get('news_list', [])
                    # 뉴스 리스트에 토픽 정보 추가
                    for news in news_list:
                        news['topic'] = topic
                    all_news.extend(news_list)
                logger.info(f"{date_str} 데이터 로드 성공: {len(all_news)}개 뉴스")
            except Exception as e:
                logger.error(f"{file_path} 로드 실패: {e}")
        else:
            logger.warning(f"파일 없음: {file_path}")
            
        current_date += timedelta(days=1)
    
    if not all_news:
        logger.error("로드된 뉴스가 없습니다. 생성을 중단합니다.")
        return

    # 2. AI 큐레이션 및 인사이트 생성
    # 뉴스 데이터를 주제별로 다시 분류
    topic_news_dict = {}
    for news in all_news:
        topic = news.get('topic', '기타')
        if topic not in topic_news_dict:
            topic_news_dict[topic] = {'news_list': [], 'topic_summary': ''}
        topic_news_dict[topic]['news_list'].append(news)
    
    curated_data = {}
    for topic, data in topic_news_dict.items():
        logger.info(f"주제 '{topic}' 큐레이션 중...")
        # 큐레이션 수행 (Top 5 선정)
        curated_news = generator.news_summarizer.curate_weekly_news(data['news_list'], topic)
        
        # 주제별 요약 생성 (여기서는 데일리 요약본들을 합쳐서 간단히 만듦)
        topic_summary = " ".join([n['summary'] for n in curated_news[:3]])
        
        curated_data[topic] = {
            'news_list': curated_news,
            'topic_summary': topic_summary
        }
        
    # 주간 인사이트 생성
    logger.info("주간 인사이트 생성 중...")
    weekly_insight = generator.news_summarizer.generate_weekly_insight(curated_data)
    
    # 3. HTML 생성
    html_content = generator.generate_html_template(curated_data, weekly_insight)
    
    # 4. 파일 저장
    save_path = "force_weekly_newsletter.html"
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    logger.info(f"주간 뉴스레터 HTML 생성 완료: {os.path.abspath(save_path)}")
    
    # 브라우저로 열기
    os.system(f"start {save_path}")

if __name__ == "__main__":
    force_generate_weekly_with_today()
