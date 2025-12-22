import os
import json
import logging
from datetime import datetime

class Archiver:
    """뉴스레터 데이터 및 HTML 아카이빙 관리 클래스"""
    
    def __init__(self, base_dir='archives'):
        self.base_dir = base_dir
        self.setup_logging()
        
    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        
    def _ensure_directory(self, path):
        """디렉토리가 없으면 생성"""
        if not os.path.exists(path):
            os.makedirs(path)
            self.logger.info(f"디렉토리 생성: {path}")
            
    def save_daily_archive(self, topic_news_dict, html_content):
        """데일리 뉴스레터 데이터(JSON) 및 HTML 저장"""
        try:
            now = datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%m")
            date_str = now.strftime("%Y%m%d")
            
            # 저장 경로: archives/daily/{YYYY}/{MM}/
            save_dir = os.path.join(self.base_dir, 'daily', year, month)
            self._ensure_directory(save_dir)
            
            # 1. JSON 데이터 저장
            json_filename = f"daily_news_{date_str}.json"
            json_path = os.path.join(save_dir, json_filename)
            
            # topic_news_dict에 메타데이터 추가
            archive_data = {
                "date": date_str,
                "timestamp": now.isoformat(),
                "topics": topic_news_dict
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"데일리 뉴스 데이터 아카이빙 완료: {json_path}")
            
            # 2. HTML 파일 저장
            # 파일명에 시간까지 포함하여 중복 방지 (하루에 여러 번 테스트할 수 있으므로)
            # 요구사항에는 daily_newsletter_{YYYYMMDD}_{HH}.html 로 되어 있음
            hour = now.strftime("%H")
            html_filename = f"daily_newsletter_{date_str}_{hour}.html"
            html_path = os.path.join(save_dir, html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"데일리 뉴스레터 HTML 아카이빙 완료: {html_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"아카이빙 중 오류 발생: {e}")
            return False
