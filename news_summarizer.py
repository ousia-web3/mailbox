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
            
            return topic_summary
            
        except Exception as e:
            self.logger.error(f"주제 요약 중 오류: {e}")
            return f"{topic_name} 주제 요약 실패"

    def curate_weekly_news(self, weekly_news_list, topic_name):
        """주간 뉴스 중 중요도 높은 Top 5 선별"""
        try:
            if not weekly_news_list:
                return []
            
            # 뉴스 목록 텍스트화
            news_text = ""
            for i, news in enumerate(weekly_news_list, 1):
                news_text += f"{i}. [{news['date']}] {news['title']}\n   요약: {news['summary']}\n\n"
            
            prompt = f"""
다음은 지난 한 주간 수집된 '{topic_name}' 관련 뉴스 목록입니다.
이 중에서 가장 중요하고 파급력이 큰 뉴스 5개를 선별해주세요.

뉴스 목록:
{news_text}

응답 형식 (JSON):
[
    {{
        "rank": 1,
        "original_index": (뉴스 번호),
        "reason": "선정 이유"
    }},
    ...
]
오직 JSON 형식으로만 응답해주세요.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 뉴스 큐레이션 전문가입니다. 수많은 뉴스 중에서 가장 가치 있는 뉴스를 선별해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            selected_indices = [item['original_index'] for item in result.get('news', result.get('items', [])) if 'original_index' in item]
            
            # 만약 JSON 파싱 구조가 예상과 다르면 단순 리스트로 처리 시도
            if not selected_indices and isinstance(result, list):
                selected_indices = [item['original_index'] for item in result]
            elif not selected_indices and isinstance(result, dict):
                 # 키 값을 찾아봄
                 for key in result:
                     if isinstance(result[key], list):
                         selected_indices = [item['original_index'] for item in result[key] if 'original_index' in item]
                         break
            
            # 인덱스 기반으로 뉴스 추출 (1-based index -> 0-based)
            curated_news = []
            for idx in selected_indices:
                if 1 <= idx <= len(weekly_news_list):
                    curated_news.append(weekly_news_list[idx-1])
            
            # 만약 파싱 실패 등으로 선택된 게 없으면 최신순 5개
            if not curated_news:
                self.logger.warning(f"AI 큐레이션 실패, 최신순 5개 선택: {topic_name}")
                curated_news = weekly_news_list[:5]
                
            self.logger.info(f"주간 뉴스 큐레이션 완료: {topic_name} - {len(curated_news)}개")
            return curated_news

        except Exception as e:
            self.logger.error(f"주간 뉴스 큐레이션 중 오류: {e}")
            return weekly_news_list[:5]  # 오류 시 상위 5개 반환

    def generate_weekly_insight(self, topic_news_dict):
        """주간 뉴스 데이터를 바탕으로 주간 인사이트(Weekly Insight) 생성"""
        try:
            # 각 주제별 요약 내용 취합
            summary_text = ""
            for topic, data in topic_news_dict.items():
                summary_text += f"[{topic}]\n{data.get('topic_summary', '요약 없음')}\n\n"
            
            prompt = f"""
다음은 이번 주 각 분야별(IT, AI, 여행) 뉴스 요약입니다.
이를 바탕으로 이번 주의 'Weekly Insight'를 작성해주세요.

내용:
{summary_text}

요구사항:
1. 이번 주를 관통하는 핵심 키워드 3개를 뽑아주세요.
2. 전체적인 기술 및 업계 흐름을 300자 이내로 서술해주세요.
3. 비즈니스 관점에서의 시사점을 한 문장으로 정리해주세요.

응답 형식:
**핵심 키워드**: 키워드1, 키워드2, 키워드3
**주간 트렌드**: (내용)
**비즈니스 시사점**: (내용)
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 IT 비즈니스 인사이트 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.4
            )
            
            insight = response.choices[0].message.content.strip()
            self.logger.info("주간 인사이트 생성 완료")
            return insight
            
        except Exception as e:
            self.logger.error(f"주간 인사이트 생성 중 오류: {e}")
            return "주간 인사이트 생성 실패"

    def generate_monthly_trend_report(self, weekly_insights):
        """월간 트렌드 리포트 생성"""
        try:
            insights_text = "\n\n".join([f"{i+1}주차 인사이트:\n{insight}" for i, insight in enumerate(weekly_insights)])
            
            prompt = f"""
다음은 지난 한 달간의 주간 인사이트 모음입니다.
이를 종합하여 '월간 IT & 여행 트렌드 리포트'를 작성해주세요.

주간 인사이트 모음:
{insights_text}

요구사항:
1. [이달의 핵심 이슈]: 가장 많이 언급되거나 중요했던 이슈 3가지를 선정하여 설명해주세요.
2. [기술 트렌드 변화]: 한 달간의 기술적 흐름 변화를 분석해주세요.
3. [여행 산업 동향]: 여행 산업과 관련된 주요 움직임을 정리해주세요.
4. [Next Month 전망]: 다음 달에 주목해야 할 포인트를 예측해주세요.

응답 형식:
## 🏆 이달의 핵심 이슈
(내용)

## 📈 기술 트렌드 변화
(내용)

## ✈️ 여행 산업 동향
(내용)

## 🔮 Next Month 전망
(내용)
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 IT/여행 산업 트렌드 분석가입니다. 거시적인 관점에서 월간 리포트를 작성해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.4
            )
            
            report = response.choices[0].message.content.strip()
            self.logger.info("월간 트렌드 리포트 생성 완료")
            return report
            
        except Exception as e:
            self.logger.error(f"월간 트렌드 리포트 생성 중 오류: {e}")
            return "월간 트렌드 리포트 생성 실패"

    def select_monthly_best_news(self, all_monthly_news):
        """월간 베스트 뉴스 3~5개 선정"""
        try:
            if not all_monthly_news:
                return []
                
            # 뉴스 목록 텍스트화 (최대 30개 정도로 제한하여 토큰 절약)
            # 각 주차별 Top 뉴스들이므로 이미 퀄리티가 보장됨
            news_text = ""
            for i, news in enumerate(all_monthly_news[:30], 1):
                news_text += f"{i}. [{news['date']}] {news['title']}\n"
            
            prompt = f"""
다음은 지난 한 달간 각 주차별로 선정된 주요 뉴스 목록입니다.
이 중에서 '이달의 Best of Best' 뉴스 3~5개를 선정해주세요.
가장 파급력이 크고, 업계에 미친 영향이 큰 순서대로 선정해주세요.

뉴스 목록:
{news_text}

응답 형식 (JSON):
[
    {{
        "rank": 1,
        "original_index": (뉴스 번호),
        "reason": "선정 이유"
    }},
    ...
]
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 뉴스 에디터입니다. 최고의 뉴스를 엄선해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            selected_indices = [item['original_index'] for item in result.get('news', result.get('items', [])) if 'original_index' in item]
            
            # 파싱 폴백 로직
            if not selected_indices and isinstance(result, list):
                selected_indices = [item['original_index'] for item in result]
            
            best_news = []
            for idx in selected_indices:
                if 1 <= idx <= len(all_monthly_news):
                    best_news.append(all_monthly_news[idx-1])
            
            if not best_news:
                best_news = all_monthly_news[:3]
                
            self.logger.info(f"월간 베스트 뉴스 선정 완료: {len(best_news)}개")
            return best_news
            
        except Exception as e:
            self.logger.error(f"월간 베스트 뉴스 선정 중 오류: {e}")
            return all_monthly_news[:3]
    
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