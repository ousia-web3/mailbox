from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import time
import json

class NewsSummarizer:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.setup_openai()
        self.load_config()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def setup_openai(self):
        """OpenAI API 설정"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
        
        self.client = OpenAI(api_key=api_key)
        self.logger.info("OpenAI API 설정 완료")
        
    def load_config(self):
        """설정 파일 로드"""
        try:
            with open('keywords_config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.logger.info("설정 파일 로드 완료")
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
            # 기본 설정값
            self.config = {"enable_pick_summary": True}
        
    def summarize_news(self, news_data, max_length=200):
        """뉴스 기사를 요약"""
        try:
            # 요약 프롬프트 생성
            prompt = f"""
다음 뉴스 기사를 {max_length}자 이내로 요약해주세요. 
중요한 사실과 핵심 내용을 포함하여 간결하고 명확하게 작성해주세요.

제목: {news_data['title']}
언론사: {news_data['press']}
발행일: {news_data['date']}
본문: {news_data['full_content'][:1500]}

요약:
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 뉴스 요약 전문가입니다. 뉴스 기사의 핵심 내용을 간결하고 정확하게 요약해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            self.logger.info(f"뉴스 요약 완료: {news_data['title'][:30]}...")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"뉴스 요약 중 오류: {e}")
            return f"요약 실패: {news_data['title']}"
    
    def generate_pick_summary(self, topic_summary, topic_name):
        """주제 요약 내용을 기반으로 PICK 요약 생성 (3-5개 단락, 각 40자 미만)"""
        # PICK 요약 기능이 비활성화된 경우 빈 리스트 반환
        if not self.config.get("enable_pick_summary", True):
            self.logger.info(f"PICK 요약 기능이 비활성화되어 있습니다: {topic_name}")
            return []
            
        try:
            if not topic_summary or topic_summary == f"{topic_name} 관련 뉴스가 없습니다.":
                return [f"{topic_name} 관련 정보가 부족합니다."]
            
            # 주제 요약 내용을 기반으로 PICK 요약 프롬프트
            prompt = f"""
다음은 '{topic_name}' 주제의 요약 내용입니다. 
이 요약 내용에서 가장 중요한 핵심 정보를 3-5개 단락으로 추출해주세요.

주제 요약: {topic_summary}

각 단락은 40자 미만으로 작성하고, 중요한 정보가 3개면 3개, 5개면 5개로 유연하게 생성해주세요.
다음과 같은 형식으로 응답해주세요:
1. [첫 번째 핵심 정보]
2. [두 번째 핵심 정보]
3. [세 번째 핵심 정보]
(필요시 4, 5번 추가)

PICK 요약:
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 뉴스 분석 전문가입니다. 주제 요약에서 가장 중요한 핵심 정보를 3-5개로 유연하게 추출해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            pick_summary_text = response.choices[0].message.content.strip()
            
            # 응답을 단락으로 분리
            pick_summary_list = []
            lines = pick_summary_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                           line.startswith(('1)', '2)', '3)', '4)', '5)')) or
                           line.startswith(('•', '-', '▶', '→'))):
                    # 번호나 기호 제거하고 내용만 추출
                    content = line
                    for prefix in ['1.', '2.', '3.', '4.', '5.', '1)', '2)', '3)', '4)', '5)', '•', '-', '▶', '→']:
                        if content.startswith(prefix):
                            content = content[len(prefix):].strip()
                            break
                    
                    if content and len(content) < 40:
                        pick_summary_list.append(content)
                    elif content:
                        # 40자 초과시 자르기
                        pick_summary_list.append(content[:39])
            
            # 최소 3개, 최대 5개로 조정
            if len(pick_summary_list) < 3:
                # 3개 미만이면 기본 정보로 보충
                while len(pick_summary_list) < 3:
                    pick_summary_list.append(f"{topic_name} 관련 추가 정보")
            elif len(pick_summary_list) > 5:
                # 5개 초과면 앞에서 5개만 선택
                pick_summary_list = pick_summary_list[:5]
            
            self.logger.info(f"PICK 요약 완료: {topic_name} - {len(pick_summary_list)}개 단락")
            return pick_summary_list
            
        except Exception as e:
            self.logger.error(f"PICK 요약 생성 중 오류: {e}")
            return [f"{topic_name} PICK 요약 생성 실패"]
    
    def summarize_topic_news(self, news_list, topic_name):
        """특정 주제의 뉴스들을 종합 요약"""
        try:
            if not news_list:
                return f"{topic_name} 관련 뉴스가 없습니다."
            
            # 모든 뉴스 제목과 요약을 하나로 합치기
            combined_content = f"주제: {topic_name}\n\n"
            
            for i, news in enumerate(news_list, 1):  # 전체 뉴스 사용
                combined_content += f"{i}. {news['title']}\n"
                combined_content += f"   {news['summary']}\n\n"
            
            # 종합 요약 프롬프트
            prompt = f"""
다음은 '{topic_name}' 관련 뉴스들의 요약입니다. 
이 뉴스들을 종합하여 해당 주제의 전반적인 동향과 주요 이슈를 200자 이내로 요약해주세요.

{combined_content}

종합 요약:
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 뉴스 분석 전문가입니다. 여러 뉴스를 종합하여 주제별 동향을 분석해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            topic_summary = response.choices[0].message.content.strip()
            self.logger.info(f"주제 종합 요약 완료: {topic_name}")
            
            return topic_summary
            
        except Exception as e:
            self.logger.error(f"주제 요약 중 오류: {e}")
            return f"{topic_name} 주제 요약 실패"
    
    def generate_newsletter_content(self, topic_news_dict):
        """뉴스레터 전체 내용 생성"""
        try:
            newsletter_content = "# [IT본부] 하나투어 뉴스레터\n\n"
            newsletter_content += f"발행일: {time.strftime('%Y년 %m월 %d일')}\n\n"
            
            for topic, news_data in topic_news_dict.items():
                newsletter_content += f"## {topic}\n\n"
                newsletter_content += f"{news_data['topic_summary']}\n\n"
                
                # PICK 요약이 활성화된 경우에만 표시
                if self.config.get("enable_pick_summary", True) and news_data.get('pick_summary'):
                    newsletter_content += "### PICK 요약\n\n"
                    for i, pick_item in enumerate(news_data['pick_summary'], 1):
                        newsletter_content += f"{i}. {pick_item}\n"
                    newsletter_content += "\n"
                
                newsletter_content += "### 주요 뉴스\n\n"
                for i, news in enumerate(news_data['news_list'], 1):  # 모든 뉴스 표시
                    newsletter_content += f"**{i}. {news['title']}**\n"
                    newsletter_content += f"   {news['date']} | [원문 보기]({news['link']})\n"
                    newsletter_content += f"   [AI] {news['summary']}\n\n\n\n"
                    
                
                newsletter_content += "---\n\n\n\n"
            
            self.logger.info("뉴스레터 내용 생성 완료")
            return newsletter_content
            
        except Exception as e:
            self.logger.error(f"뉴스레터 내용 생성 중 오류: {e}")
            return "뉴스레터 생성 실패" 