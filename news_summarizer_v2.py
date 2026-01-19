import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
import json

class NewsSummarizerV2:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.setup_gemini()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def setup_gemini(self):
        api_key = os.getenv('GEMINI_API_KEY')
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-preview-09-2025')

        if not api_key:
            raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")

        # Gemini API 설정
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.logger.info(f"Gemini API 초기화 완료 (모델: {model_name})")
        
    def summarize_topic_with_persona(self, news_list, topic_name):
        """사용자 정의 페르소나 프롬프트를 사용하여 주제별 뉴스 요약"""
        if not news_list:
            return None

        # 1. 필터링: 영문 기사 제외 (본문 길이 필터링 완화)
        filtered_news_list = []
        for news in news_list:
            title = news.get('title', '')
            content = news.get('full_content', '') or news.get('content_preview', '')
            
            # 1-1. 한글 포함 여부 확인 (영문 기사 제외)
            if not any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7a3' for char in title + content):
                continue
            
            # 1-2. 본문 길이 확인 (필터링 완화)
            # 사용자가 "본문 없는 기사 제외"를 요청했으나, 너무 엄격하여 모든 뉴스가 사라지는 문제 발생.
            # 따라서 최소한의 길이(10자)만 확인하거나, 제목이 충분히 길면 허용하는 방식으로 변경.
            if len(content.strip()) < 10 and len(title) < 10:
                self.logger.info(f"내용과 제목이 모두 부실하여 제외: {title}")
                continue
                
            filtered_news_list.append(news)
            
        if not filtered_news_list:
            self.logger.warning(f"주제 '{topic_name}'에 유효한 뉴스(한글)가 없습니다.")
            return None

        # 뉴스 데이터 텍스트화
        news_input_text = ""
        for i, news in enumerate(filtered_news_list, 1):
            news_input_text += f"[{i}]\n"
            news_input_text += f"제목: {news['title']}\n"
            news_input_text += f"링크: {news['link']}\n"
            # 본문은 너무 길면 자름 (토큰 제한 고려)
            content = news.get('full_content', '')
            if not content:
                content = news.get('content_preview', '')
            news_input_text += f"본문: {content[:1000]}\n\n"

        # 사용자 요청 프롬프트 구성
        news_count = len(filtered_news_list)
        # 프롬프트 파일 읽기
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'newsletter_prompt.md')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt_template = f.read()
        except Exception as e:
            self.logger.error(f"프롬프트 파일 로드 실패: {e}")
        except Exception as e:
            self.logger.error(f"프롬프트 파일 로드 실패: {e}")
            return None

        # 프롬프트 구성
        try:
            prompt = system_prompt_template.format(
                news_data=news_input_text,
                topic_name=topic_name,
                news_count=news_count
            )
        except KeyError as e:
            self.logger.error(f"프롬프트 포맷팅 오류 (키 누락): {e}")
            return None

        try:
            # Gemini 프롬프트 구성 (system instruction + user prompt)
            full_prompt = f"""당신은 하나투어 IT본부의 유능한 전략 기획자입니다.

{prompt}"""

            # Gemini API 호출
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4000,
                    temperature=0.5,
                )
            )

            # 응답 상태 확인
            if not response.candidates:
                self.logger.error(f"Gemini API 응답 없음 (주제: {topic_name})")
                return None

            # Safety rating 확인
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                self.logger.info(f"Gemini 응답 finish_reason: {candidate.finish_reason}")
                # 1 = STOP (정상 완료), 2 = MAX_TOKENS (토큰 한계, 부분 응답 사용 가능)
                if candidate.finish_reason not in [1, 2]:
                    self.logger.error(f"Gemini 응답이 비정상 종료됨 (주제: {topic_name}): {candidate.finish_reason}")
                    if hasattr(candidate, 'safety_ratings'):
                        self.logger.error(f"Safety ratings: {candidate.safety_ratings}")
                    return None
                elif candidate.finish_reason == 2:
                    self.logger.warning(f"Gemini 응답이 토큰 한계로 잘렸습니다 (주제: {topic_name}, MAX_TOKENS). 부분 응답 사용.")

            try:
                result = response.text.strip()
            except ValueError as ve:
                self.logger.warning(f"response.text 접근 실패: {ve}, parts에서 추출 시도")
                parts = []
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            parts.append(part.text)
                result = "".join(parts).strip()

            if not result:
                self.logger.error(f"Gemini API 응답이 비어있음 (주제: {topic_name})")
                return None

            # 결과 텍스트 정제 (끝부분의 불필요한 기호 제거)
            result = result.strip()
            while result.endswith('-') or result.endswith('=') or result.endswith('─') or result.endswith('#'):
                result = result.rstrip('-=─#').strip()

            self.logger.info(f"주제 '{topic_name}' 페르소나 요약 완료 (길이: {len(result)}자)")
            return result

        except Exception as e:
            self.logger.error(f"요약 생성 중 오류 (주제: {topic_name}): {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return f"요약 생성 실패: {e}"

    def summarize_all_news(self, all_news_list):
        """전체 뉴스를 대상으로 새로운 템플릿 프롬프트를 사용하여 요약"""
        if not all_news_list:
            return None

        # 토큰 한계 고려: 카테고리별로 그룹핑하고 각 카테고리에서 상위 15개만 선택
        category_news = {}
        for news in all_news_list:
            category = news.get('category', 'Unknown')
            if category not in category_news:
                category_news[category] = []
            category_news[category].append(news)

        # 각 카테고리에서 최대 15개씩만 선택
        limited_news_list = []
        for category, news_list in category_news.items():
            limited_news_list.extend(news_list[:15])
            if len(news_list) > 15:
                self.logger.warning(f"카테고리 '{category}': {len(news_list)}개 중 15개만 선택 (토큰 한계)")

        self.logger.info(f"전체 뉴스 {len(all_news_list)}개 중 {len(limited_news_list)}개를 Gemini에 전달")

        # 뉴스 데이터 텍스트화
        news_input_text = ""
        for i, news in enumerate(limited_news_list, 1):
            news_input_text += f"[{i}]\n"
            news_input_text += f"제목: {news.get('title', '')}\n"
            news_input_text += f"링크: {news.get('link', '')}\n"
            content = news.get('full_content', '') or news.get('content_preview', '')
            news_input_text += f"본문: {content[:1000]}\n\n"

        # 프롬프트 파일 읽기
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'newsletter_template_prompt.md')
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt_template = f.read()
        except Exception as e:
            self.logger.error(f"프롬프트 파일 로드 실패: {e}")
            return None

        # 프롬프트 구성
        try:
            prompt = system_prompt_template.format(news_data=news_input_text)
        except KeyError as e:
            self.logger.error(f"프롬프트 포맷팅 오류: {e}")
            return None

        try:
            # Gemini 프롬프트 구성 (system instruction + user prompt)
            full_prompt = f"""당신은 하나투어 IT본부의 전문 테크 에디터입니다.

{prompt}"""

            # Gemini API 호출
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=8000,
                    temperature=0.5,
                )
            )

            # 응답 상태 확인
            if not response.candidates:
                self.logger.error("Gemini API 응답 없음 (candidates 비어있음)")
                return None

            # Safety rating 확인
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                self.logger.info(f"Gemini 응답 finish_reason: {candidate.finish_reason}")
                # 1 = STOP (정상 완료), 2 = MAX_TOKENS (토큰 한계, 부분 응답 사용 가능)
                if candidate.finish_reason not in [1, 2]:
                    self.logger.error(f"Gemini 응답이 비정상 종료됨: {candidate.finish_reason}")
                    if hasattr(candidate, 'safety_ratings'):
                        self.logger.error(f"Safety ratings: {candidate.safety_ratings}")
                    return None
                elif candidate.finish_reason == 2:
                    self.logger.warning("Gemini 응답이 토큰 한계로 잘렸습니다 (MAX_TOKENS). 부분 응답 사용.")

            try:
                result = response.text.strip()
            except ValueError as ve:
                self.logger.warning(f"response.text 접근 실패: {ve}, parts에서 추출 시도")
                parts = []
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            parts.append(part.text)
                result = "".join(parts).strip()

            if not result:
                self.logger.error("Gemini API 응답이 비어있음")
                return None

            # 결과 텍스트 정제 (끝부분의 불필요한 기호 제거)
            result = result.strip()
            while result.endswith('-') or result.endswith('=') or result.endswith('─') or result.endswith('#'):
                result = result.rstrip('-=─#').strip()

            self.logger.info(f"전체 뉴스 통합 요약 완료 (길이: {len(result)}자)")
            return result

        except Exception as e:
            self.logger.error(f"전체 요약 생성 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def curate_weekly_top_10(self, weekly_news_list):
        """주간 뉴스 중 Top 10 선정 및 인사이트 생성"""
        try:
            if not weekly_news_list:
                return None
            
            # 뉴스 목록 텍스트화
            news_text = ""
            for i, news in enumerate(weekly_news_list, 1):
                news_text += f"ID: {i}\n제목: {news['title']}\n요약: {news.get('summary', news.get('content_preview', ''))}\n언론사: {news.get('press', 'Unknown')}\n\n"
            
            # 프롬프트 파일 읽기
            try:
                prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'weekly_curation_prompt.md')
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
            except Exception as e:
                self.logger.error(f"프롬프트 파일 로드 실패: {e}")
                return None
            
            # 프롬프트 구성
            prompt = prompt_template.format(news_text=news_text)
            
            # Gemini API 호출
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=5000,
                    temperature=0.3
                )
            )
            
            # 응답 상태 확인
            if not response.candidates:
                self.logger.error("Gemini API 응답 없음 (주간 큐레이션)")
                return None
            
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                self.logger.info(f"Gemini 응답 finish_reason: {candidate.finish_reason}")
                if candidate.finish_reason not in [1, 2]:
                    self.logger.error(f"Gemini 응답이 비정상 종료됨: {candidate.finish_reason}")
                    return None
                elif candidate.finish_reason == 2:
                    self.logger.warning("Gemini 응답이 토큰 한계로 잘렸습니다 (MAX_TOKENS). 부분 응답 사용 시도.")
            
            try:
                result_text = response.text.strip()
            except ValueError as ve:
                self.logger.warning(f"response.text 접근 실패: {ve}, parts에서 추출 시도")
                parts = []
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            parts.append(part.text)
                result_text = "".join(parts).strip()
            
            self.logger.info(f"Gemini 응답 길이: {len(result_text)}자")
            self.logger.info(f"Gemini 응답 앞부분 (500자): {result_text[:500]}")
            
            if not result_text:
                self.logger.error("Gemini API 응답이 비어있음 (주간 큐레이션)")
                return None
            
            # 마크다운 코드 블록 제거
            if result_text.startswith("```json"):
                result_text = result_text[7:]  # ```json 제거
            if result_text.startswith("```"):
                result_text = result_text[3:]  # ``` 제거
            if result_text.endswith("```"):
                result_text = result_text[:-3]  # 끝의 ``` 제거
            result_text = result_text.strip()
            
            self.logger.info(f"전처리 후 응답 길이: {len(result_text)}자")
            
            # JSON 파싱
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as je:
                self.logger.error(f"JSON 파싱 실패: {je}")
                self.logger.error(f"응답 전체 내용: {result_text}")
                return None
            
            # 원본 뉴스 데이터와 매핑하여 링크 정보 복원
            def map_news(item_list):
                mapped_list = []
                for item in item_list:
                    try:
                        idx = int(item['original_id']) - 1
                        if 0 <= idx < len(weekly_news_list):
                            original = weekly_news_list[idx]
                            item['link'] = original.get('link', '#')
                            item['press'] = original.get('press', '')
                            item['date'] = original.get('date', '')
                            mapped_list.append(item)
                    except:
                        continue
                return mapped_list

            result['top_10'] = map_news(result.get('top_10', []))
            # result['other_news'] = map_news(result.get('other_news', [])) # 프롬프트에서 제거됨
            
            self.logger.info(f"주간 Top 10 큐레이션 완료")
            return result

        except Exception as e:
            self.logger.error(f"주간 Top 10 큐레이션 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
