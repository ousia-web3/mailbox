# -*- coding: utf-8 -*-
"""
실제 작동하는 뉴스 수집기 - 샘플 데이터 + 실제 뉴스 수집 조합
"""
import requests
from bs4 import BeautifulSoup
import time
import logging
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from logging_config import setup_utf8_logging
import os

class WorkingNewsCollector:
    def __init__(self):
        self.setup_logging()
        self.session = requests.Session()
        self.setup_session()
        self.request_lock = Lock()  # 요청 제한을 위한 락
        self.max_workers = 3  # 동시 실행 스레드 수 제한
        

        
    def setup_logging(self):
        """UTF-8 인코딩으로 로깅 설정"""
        self.logger = setup_utf8_logging(
            logger_name=__name__,
            log_file='working_news_collector.log',
            level=logging.INFO
        )
        
    def setup_session(self):
        """requests 세션 설정"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(headers)
        
    def get_yesterday_date(self):
        """전날 날짜를 YYYYMMDD 형식으로 반환"""
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y%m%d')

    def get_today_date(self):
        """오늘 날짜를 YYYYMMDD 형식으로 반환"""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d')

    def get_yesterday_date_range(self):
        """전날 날짜 범위를 반환 (after:YYYY-MM-DD before:YYYY-MM-DD 형식)"""
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        return {
            'after': yesterday_str,      # 시작일
            'before': yesterday_str,     # 종료일
            'start_date': yesterday.strftime('%Y%m%d'),   # YYYYMMDD 형식
            'end_date': yesterday.strftime('%Y%m%d')      # YYYYMMDD 형식
        }
    
    def get_date_range_for_search(self, search_date=None):
        """검색 날짜에 따른 날짜 범위 반환"""
        from datetime import datetime, timedelta
        
        if search_date is None:
            # 기본값: 전날
            target_date = datetime.now() - timedelta(days=1)
        else:
            # 지정된 날짜 파싱
            try:
                if len(search_date) == 8:  # YYYYMMDD 형식
                    target_date = datetime.strptime(search_date, '%Y%m%d')
                elif len(search_date) == 10:  # YYYY-MM-DD 형식
                    target_date = datetime.strptime(search_date, '%Y-%m-%d')
                else:
                    # 잘못된 형식이면 전날로 설정
                    target_date = datetime.now() - timedelta(days=1)
            except:
                target_date = datetime.now() - timedelta(days=1)
        
        target_str = target_date.strftime('%Y-%m-%d')
        
        return {
            'after': target_str,
            'before': target_str,
            'start_date': target_date.strftime('%Y%m%d'),
            'end_date': target_date.strftime('%Y%m%d'),
            'target_date': target_date,
            'target_str': target_str
        }
    
    def should_exclude_hanatour_news(self, title, content, keyword):
        """하나투어 키워드 관련 제외 로직"""
        if keyword != '하나투어':
            return False
            
        exclusion_keywords = [
            '송미선 대표',
            '송미선 대표 연임',
            '송미선 연임'
        ]
        
        # 제목이나 본문에 제외 키워드가 포함되어 있는지 확인
        for ex_kw in exclusion_keywords:
            if ex_kw in title or ex_kw in content:
                self.logger.info(f"하나투어 제외 키워드 발견: {ex_kw} (제목: {title[:30]}...)")
                return True
                
        return False

    def search_naver_news_with_retry(self, keyword, max_articles=5, search_date=None):
        """키워드별 실제 뉴스 검색 (다중 소스) - 날짜 지정 가능"""
        try:
            self.logger.info(f"키워드 '{keyword}' 실제 뉴스 검색 중... (날짜: {search_date if search_date else '오늘'})")
            
            # 다중 소스에서 뉴스 검색
            news_list = self.multi_search_news(keyword, max_articles, search_date)
            
            self.logger.info(f"키워드 '{keyword}' 뉴스 검색 완료: {len(news_list)}개")
            return news_list
            
        except Exception as e:
            self.logger.warning(f"뉴스 검색 중 오류 발생 (빈 결과 반환): {e}")
            return []
    
    def multi_search_news(self, keyword, max_articles=5, search_date=None):
        """다중 소스에서 뉴스 검색 (구글뉴스 우선순위) - 날짜 지정 가능"""
        all_news = []
        
        # 날짜 설정 (기본값: 오늘)
        if search_date is None:
            search_date = self.get_today_date()
        
        self.logger.info(f"다중 소스 뉴스 검색 시작: {keyword} (날짜: {search_date})")
        
        # 1. 구글 뉴스 검색 (최우선)
        try:
            google_news = self.search_google_news(keyword, max_articles, search_date)
            # 구글 뉴스에 우선순위 표시
            for news in google_news:
                news['priority'] = 1  # 최우선
                news['source'] = '구글뉴스'
                news['search_date'] = search_date
            all_news.extend(google_news)
            self.logger.info(f"구글 뉴스에서 {len(google_news)}개 수집")
        except Exception as e:
            self.logger.warning(f"구글 뉴스 검색 실패 (다음 소스로 넘어갑니다): {e}")
        
        # 2. 네이버 뉴스 검색 (두 번째 우선순위)
        try:
            naver_news = self.search_real_naver_news(keyword, max_articles, search_date)
            # 네이버 뉴스에 우선순위 표시
            for news in naver_news:
                news['priority'] = 2  # 두 번째 우선순위
                news['source'] = '네이버뉴스'
                news['search_date'] = search_date
            all_news.extend(naver_news)
            self.logger.info(f"네이버 뉴스에서 {len(naver_news)}개 수집")
        except Exception as e:
            self.logger.warning(f"네이버 뉴스 검색 실패 (다음 소스로 넘어갑니다): {e}")
        
        # 3. 일반 뉴스 사이트 검색 (세 번째 우선순위)
        try:
            general_news = self.search_general_news(keyword, max_articles, search_date)
            # 일반 뉴스에 우선순위 표시
            for news in general_news:
                news['priority'] = 3  # 세 번째 우선순위
                news['source'] = '일반뉴스'
                news['search_date'] = search_date
            all_news.extend(general_news)
            self.logger.info(f"일반 뉴스에서 {len(general_news)}개 수집")
        except Exception as e:
            self.logger.warning(f"일반 뉴스 검색 실패 (다음 단계로 넘어갑니다): {e}")
        
        # 4. 당일 뉴스 최종 필터링
        all_news = self.filter_today_news(all_news)
        
        # 정교한 중복 제거 (제목 유사성 기반)
        unique_news = self.remove_duplicate_news(all_news, keyword)
        
        # 우선순위와 날짜순으로 정렬 (네이버뉴스 우선, 최신순)
        unique_news.sort(key=lambda x: (x.get('priority', 999), x.get('date', ''), x.get('title', '')), reverse=False)
        
        self.logger.info(f"총 {len(all_news)}개 수집 → 중복 제거 후 {len(unique_news)}개")
        
        # 모든 수집된 뉴스 반환 (제한 없음)
        return unique_news
    
    def remove_duplicate_news(self, news_list, keyword=""):
        """중복 뉴스 제거"""
        if not news_list:
            return []
        
        # 할인/캐쉬백 키워드 특별 처리
        if keyword in ['할인', '캐쉬백', '캐시백']:
            self.logger.info(f"할인/캐쉬백 키워드 '{keyword}'에 대한 강화된 중복 제거 적용")
            # 할인/캐쉬백 관련 뉴스는 더 엄격한 중복 제거 적용
            return self.remove_duplicate_discount_news(news_list, keyword)
        
        # 유사한 뉴스 그룹을 찾아서 1개씩만 유지
        unique_news = []
        processed_indices = set()
        
        self.logger.info(f"중복 제거 시작: 총 {len(news_list)}개 뉴스")
        
        for i, news in enumerate(news_list):
            if i in processed_indices:
                continue
                
            title = news.get('title', '').strip()
            if not title:
                continue
            
            # 현재 뉴스를 유지할 그룹의 대표로 선택
            current_group = [news]
            processed_indices.add(i)
            
            self.logger.info(f"중복 제거 그룹 시작: {title[:50]}...")
            
            # 나머지 뉴스들과 비교하여 유사한 것들을 같은 그룹으로 분류
            for j, other_news in enumerate(news_list[i+1:], i+1):
                if j in processed_indices:
                    continue
                    
                other_title = other_news.get('title', '').strip()
                if not other_title:
                    continue
                
                # 유사성 체크
                if self.is_similar_title(title, other_title, keyword):
                    current_group.append(other_news)
                    processed_indices.add(j)
                    self.logger.info(f"유사 뉴스 그룹화: {other_title[:50]}... (기존: {title[:50]}...)")
            
            # 그룹에서 1개만 유지 (우선순위: 네이버뉴스 > 일반뉴스 > 구글뉴스, 최신순)
            if len(current_group) > 1:
                # 우선순위와 날짜순으로 정렬
                current_group.sort(key=lambda x: (
                    x.get('priority', 999),  # 우선순위 (낮을수록 높음)
                    x.get('date', ''),       # 날짜 (최신순)
                    x.get('title', '')       # 제목 (사전순)
                ))
                self.logger.info(f"유사 뉴스 그룹에서 1개 유지: {current_group[0]['title'][:50]}... (총 {len(current_group)}개 중)")
                
                # 제거된 뉴스들 로깅
                for removed_news in current_group[1:]:
                    self.logger.info(f"중복으로 제거된 뉴스: {removed_news['title'][:50]}...")
            else:
                self.logger.info(f"중복 없는 뉴스 유지: {title[:50]}...")
            
            # 그룹의 대표 뉴스 추가
            unique_news.append(current_group[0])
        
        self.logger.info(f"중복 제거 완료: {len(news_list)}개 → {len(unique_news)}개")
        return unique_news
    
    def remove_duplicate_discount_news(self, news_list, keyword):
        """할인/캐쉬백 뉴스에 대한 강화된 중복 제거"""
        if not news_list:
            return []
        
        unique_news = []
        seen_titles = set()
        seen_products = set()  # 상품/서비스별로 중복 체크
        
        for news in news_list:
            title = news.get('title', '').strip()
            if not title:
                continue
            
            # 제목 정규화
            normalized_title = self.normalize_title(title)
            
            # 정확한 중복 체크
            if normalized_title in seen_titles:
                self.logger.info(f"할인 뉴스 정확한 중복 제거: {title[:50]}...")
                continue
            
            # 상품/서비스 키워드 추출
            product_keywords = ['카드', '신용카드', '체크카드', '포인트', '마일리지', '적립', '리워드', '혜택', '서비스', '앱', '온라인', '오프라인', '은행', '카카오', '네이버', '쿠팡', '배달', '택시', '교통', '통신', '이동통신', 'SKT', 'KT', 'LG', '삼성', '현대', '기아', '롯데', '신세계', '이마트', '홈플러스']
            
            found_products = [kw for kw in product_keywords if kw in normalized_title]
            
            # 상품별 중복 체크 (같은 상품의 할인 뉴스는 1개만 허용)
            if found_products:
                product_key = tuple(sorted(found_products))
                if product_key in seen_products:
                    self.logger.info(f"할인 뉴스 상품 중복 제거: {title[:50]}... (상품: {', '.join(found_products)})")
                    continue
                seen_products.add(product_key)
            
            # 유사한 제목 체크 (더 엄격한 기준)
            is_similar = False
            for existing_news in unique_news:
                existing_title = existing_news.get('title', '').strip()
                if self.is_similar_title(title, existing_title, keyword, similarity_threshold=0.3):  # 더 낮은 임계값
                    self.logger.info(f"할인 뉴스 유사 제목 중복 제거: {title[:50]}... (기존: {existing_title[:50]}...)")
                    is_similar = True
                    break
            
            # 강화된 패턴 매칭 체크
            if not is_similar:
                is_similar = self.check_enhanced_discount_patterns(title, unique_news, keyword)
                if is_similar:
                    self.logger.info(f"할인 뉴스 패턴 매칭 중복 제거: {title[:50]}...")
            
            if not is_similar:
                seen_titles.add(normalized_title)
                unique_news.append(news)
        
        self.logger.info(f"할인/캐쉬백 뉴스 중복 제거 완료: {len(news_list)}개 → {len(unique_news)}개")
        return unique_news
    
    def check_enhanced_discount_patterns(self, title, existing_news_list, keyword):
        """할인/캐쉬백 뉴스에 대한 강화된 패턴 매칭"""
        if not existing_news_list:
            return False
        
        title_clean = self.remove_keyword_from_title(title, keyword)
        title_norm = self.normalize_title(title_clean)
        
        for existing_news in existing_news_list:
            existing_title = existing_news.get('title', '').strip()
            existing_clean = self.remove_keyword_from_title(existing_title, keyword)
            existing_norm = self.normalize_title(existing_clean)
            
            # 할인 관련 키워드 패턴 체크
            discount_patterns = [
                ('할인', '혜택'),
                ('캐쉬백', '캐시백'),
                ('포인트', '적립'),
                ('리워드', '혜택'),
                ('프로모션', '이벤트'),
                ('쿠폰', '할인'),
                ('마일리지', '포인트'),
                ('적립', '리워드'),
                ('혜택', '서비스')
            ]
            
            for pattern1, pattern2 in discount_patterns:
                if pattern1 in title_norm and pattern2 in existing_norm:
                    # 나머지 단어들이 유사한지 확인
                    words1 = set(title_norm.split())
                    words2 = set(existing_norm.split())
                    
                    remaining_words1 = [w for w in words1 if w not in [pattern1, pattern2]]
                    remaining_words2 = [w for w in words2 if w not in [pattern1, pattern2]]
                    
                    if len(remaining_words1) > 0 and len(remaining_words2) > 0:
                        remaining_similarity = len(set(remaining_words1).intersection(set(remaining_words2))) / len(set(remaining_words1).union(set(remaining_words2)))
                        if remaining_similarity >= 0.4:  # 더 낮은 임계값
                            return True
            
            # 기존 패턴 매칭도 적용
            if self.match_number_keyword_pattern(title_norm, existing_norm):
                return True
            
            if self.match_verb_variation_pattern(title_norm, existing_norm):
                return True
        
        return False
    
    def check_enhanced_patterns(self, title, existing_news_list, keyword):
        """강화된 패턴 매칭으로 중복 체크"""
        if not existing_news_list:
            return False
        
        # 키워드 제거
        title_clean = self.remove_keyword_from_title(title, keyword)
        title_norm = self.normalize_title(title_clean)
        
        for existing_news in existing_news_list:
            existing_title = existing_news.get('title', '').strip()
            existing_clean = self.remove_keyword_from_title(existing_title, keyword)
            existing_norm = self.normalize_title(existing_clean)
            
            # 숫자 + 키워드 패턴 매칭 (예: "46기 인턴 입문 교육")
            if self.match_number_keyword_pattern(title_norm, existing_norm):
                return True
            
            # 동사 변형 패턴 매칭 (예: "실시" vs "진행")
            if self.match_verb_variation_pattern(title_norm, existing_norm):
                return True
        
        return False
    
    def match_number_keyword_pattern(self, title1, title2):
        """숫자 + 키워드 패턴 매칭"""
        import re
        
        # 숫자 추출
        numbers1 = re.findall(r'\d+', title1)
        numbers2 = re.findall(r'\d+', title2)
        
        if not numbers1 or not numbers2 or numbers1 != numbers2:
            return False
        
        # 숫자 제거 후 나머지 단어들 비교
        title1_no_numbers = re.sub(r'\d+', '', title1)
        title2_no_numbers = re.sub(r'\d+', '', title2)
        
        words1 = set(title1_no_numbers.split())
        words2 = set(title2_no_numbers.split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        # 공통 키워드 체크 (인턴, 교육, 입문 등)
        common_keywords = ['인턴', '교육', '입문', '프로그램', '과정', '기수']
        common_count1 = sum(1 for word in words1 if word in common_keywords)
        common_count2 = sum(1 for word in words2 if word in common_keywords)
        
        # 공통 키워드가 2개 이상 겹치면 유사한 것으로 판단
        if common_count1 >= 2 and common_count2 >= 2:
            intersection = len(words1.intersection(words2))
            if intersection >= 2:  # 최소 2개 단어가 겹치면
                return True
        
        return False
    
    def match_verb_variation_pattern(self, title1, title2):
        """동사 변형 패턴 매칭"""
        # 동사 변형 매핑
        verb_variations = {
            '실시': ['진행', '시작', '개시', '운영'],
            '진행': ['실시', '시작', '개시', '운영'],
            '완료': ['종료', '마감', '끝'],
            '종료': ['완료', '마감', '끝'],
            '발표': ['공개', '발표', '알림'],
            '공개': ['발표', '알림', '공개']
        }
        
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        for verb, variations in verb_variations.items():
            if verb in words1:
                for variation in variations:
                    if variation in words2:
                        # 동사 제외한 나머지 단어들 비교
                        remaining_words1 = [w for w in words1 if w not in [verb] + variations]
                        remaining_words2 = [w for w in words2 if w not in [verb] + variations]
                        
                        if len(remaining_words1) > 0 and len(remaining_words2) > 0:
                            # 나머지 단어들이 유사한지 확인
                            remaining_set1 = set(remaining_words1)
                            remaining_set2 = set(remaining_words2)
                            
                            intersection = len(remaining_set1.intersection(remaining_set2))
                            union = len(remaining_set1.union(remaining_set2))
                            
                            if union > 0 and intersection / union >= 0.5:
                                return True
        
        return False
    
    def normalize_title(self, title):
        """제목 정규화"""
        import re
        # 특수문자 제거, 소문자 변환, 공백 정리
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def is_similar_title(self, title1, title2, keyword="", similarity_threshold=0.4):
        """제목 유사성 체크 (키워드 제외)"""
        if not title1 or not title2:
            return False
        
        # 키워드 제거
        title1_clean = self.remove_keyword_from_title(title1, keyword)
        title2_clean = self.remove_keyword_from_title(title2, keyword)
        
        # 정규화
        norm1 = self.normalize_title(title1_clean)
        norm2 = self.normalize_title(title2_clean)
        
        # 정확히 같은 경우
        if norm1 == norm2:
            return True
        
        # 하나투어 키워드 특별 처리 (더 관대한 중복 제거)
        if keyword == '하나투어':
            # 하나투어 관련 뉴스는 더 관대한 기준 적용
            similarity_threshold = 0.7  # 임계값을 더 높게 설정
            
            # 하나투어 관련 핵심 키워드가 포함된 경우 중복 제거를 더 엄격하게
            hanatour_keywords = ['인턴', '교육', '입문', '46기', '기수', '프로그램', '과정']
            has_hanatour1 = any(kw in norm1 for kw in hanatour_keywords)
            has_hanatour2 = any(kw in norm2 for kw in hanatour_keywords)
            
            if has_hanatour1 and has_hanatour2:
                # 숫자 패턴이 같으면 (예: "46기") 더 엄격하게 체크
                import re
                numbers1 = re.findall(r'\d+', norm1)
                numbers2 = re.findall(r'\d+', norm2)
                
                if numbers1 and numbers2 and numbers1 == numbers2:
                    # 숫자가 같으면 나머지 단어들의 유사성 체크
                    non_number_words1 = [w for w in norm1.split() if not re.match(r'\d+', w)]
                    non_number_words2 = [w for w in norm2.split() if not re.match(r'\d+', w)]
                    
                    if len(non_number_words1) > 0 and len(non_number_words2) > 0:
                        non_number_similarity = len(set(non_number_words1).intersection(set(non_number_words2))) / len(set(non_number_words1).union(set(non_number_words2)))
                        if non_number_similarity >= 0.95:  # 95% 이상 유사해야 중복으로 판단 (더 엄격하게)
                            return True
                        else:
                            return False  # 하나투어 핵심 뉴스는 중복으로 판단하지 않음
                
                # 동사 변형이 있는 경우 중복으로 판단하지 않음 (진행 vs 시작 vs 실시)
                verb_variations = ['진행', '시작', '실시', '개시', '운영']
                verb1 = None
                verb2 = None
                
                for verb in verb_variations:
                    if verb in norm1:
                        verb1 = verb
                    if verb in norm2:
                        verb2 = verb
                
                if verb1 and verb2 and verb1 != verb2:
                    # 동사가 다르면 다른 뉴스로 판단
                    return False
        
        # 할인/캐쉬백 키워드 특별 처리
        if keyword in ['할인', '캐쉬백', '캐시백']:
            # 할인/캐쉬백 관련 키워드들이 포함된 경우 더 엄격하게 체크
            discount_keywords = ['할인', '캐쉬백', '캐시백', '혜택', '프로모션', '이벤트', '쿠폰', '포인트', '적립', '리워드']
            
            # 두 제목 모두 할인/캐쉬백 관련 키워드를 포함하는지 확인
            has_discount1 = any(kw in norm1 for kw in discount_keywords)
            has_discount2 = any(kw in norm2 for kw in discount_keywords)
            
            if has_discount1 and has_discount2:
                # 할인/캐쉬백 관련 뉴스는 더 엄격한 기준 적용
                similarity_threshold = 0.3  # 임계값을 더 낮춤
                
                # 주요 상품/서비스 키워드가 같으면 유사한 것으로 판단
                product_keywords = ['카드', '신용카드', '체크카드', '포인트', '마일리지', '적립', '리워드', '혜택', '서비스', '앱', '온라인', '오프라인']
                
                product_match1 = [kw for kw in product_keywords if kw in norm1]
                product_match2 = [kw for kw in product_keywords if kw in norm2]
                
                if product_match1 and product_match2:
                    # 주요 상품 키워드가 겹치면 유사한 것으로 판단
                    common_products = set(product_match1).intersection(set(product_match2))
                    if len(common_products) >= 1:  # 1개 이상의 상품 키워드가 겹치면
                        return True
        
        # 키워드 기반 유사성 체크
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        # Jaccard 유사도 계산
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return False
        
        similarity = intersection / union
        
        # 주요 키워드가 많이 겹치면 유사한 것으로 판단 (임계값 더 낮춤)
        if similarity >= similarity_threshold:
            return True
        

        
        # 특정 패턴 체크 (예: "진행" vs "실시", "완료" 등)
        similar_patterns = [
            ('진행', '실시'),
            ('완료', '종료'),
            ('시작', '개시'),
            ('발표', '공개'),
            ('확정', '결정'),
            ('추진', '진행'),
            ('준비', '대비'),
            ('계획', '예정'),
            ('예상', '전망'),
            ('분석', '조사'),
            ('결과', '성과'),
            ('효과', '성과'),
            ('개선', '향상'),
            ('증가', '성장'),
            ('확대', '증가'),
            ('도입', '적용'),
            ('시행', '실시'),
            ('운영', '관리'),
            ('개발', '연구'),
            ('투자', '지원'),
            ('교육', '훈련'),
            ('프로그램', '과정'),
            ('입문', '기초'),
            ('기수', '기수'),  # 같은 단어지만 다른 맥락
            ('인턴', '인턴'),
            # 할인/캐쉬백 관련 패턴 추가
            ('할인', '혜택'),
            ('캐쉬백', '캐시백'),
            ('포인트', '적립'),
            ('리워드', '혜택'),
            ('프로모션', '이벤트'),
            ('쿠폰', '할인'),
            ('마일리지', '포인트')
        ]
        
        for pattern1, pattern2 in similar_patterns:
            if pattern1 in norm1 and pattern2 in norm2:
                # 나머지 단어들이 유사한지 확인
                remaining_words1 = [w for w in words1 if w not in [pattern1, pattern2]]
                remaining_words2 = [w for w in words2 if w not in [pattern1, pattern2]]
                
                if len(remaining_words1) > 0 and len(remaining_words2) > 0:
                    remaining_similarity = len(set(remaining_words1).intersection(set(remaining_words2))) / len(set(remaining_words1).union(set(remaining_words2)))
                    if remaining_similarity >= 0.5:  # 나머지 단어들이 50% 이상 유사하면 (임계값 낮춤)
                        return True
        
        # 추가: 숫자 패턴 매칭 (예: "46기" 같은 기수)
        import re
        numbers1 = re.findall(r'\d+', norm1)
        numbers2 = re.findall(r'\d+', norm2)
        
        if numbers1 and numbers2 and numbers1 == numbers2:
            # 숫자가 같으면 나머지 단어들의 유사성 체크
            non_number_words1 = [w for w in words1 if not re.match(r'\d+', w)]
            non_number_words2 = [w for w in words2 if not re.match(r'\d+', w)]
            
            if len(non_number_words1) > 0 and len(non_number_words2) > 0:
                non_number_similarity = len(set(non_number_words1).intersection(set(non_number_words2))) / len(set(non_number_words1).union(set(non_number_words2)))
                if non_number_similarity >= 0.6:  # 숫자 제외한 단어들이 60% 이상 유사하면
                    return True
        
        return False
    
    def is_exact_keyword_match(self, title, keyword):
        """정확한 키워드 매칭 - 단어 경계를 고려한 정확한 매칭"""
        import re
        
        if not title or not keyword:
            return False
        
        # 키워드를 정규식 패턴으로 변환 (단어 경계 고려)
        # "여기어때" -> r'\b여기어때\b'
        pattern = r'\b' + re.escape(keyword) + r'\b'
        
        # 대소문자 구분 없이 검색
        return bool(re.search(pattern, title, re.IGNORECASE))
    
    def is_relevant_keyword_match(self, title, keyword):
        """관련성 있는 키워드 매칭 - 의미적 유사성도 고려"""
        import re
        
        if not title or not keyword:
            return False
        
        # "야놀자" 키워드 예외: "야 놀자"(띄어쓰기 포함)는 제외
        if keyword == '야놀자':
            # 임의의 공백까지 고려하여 제외 처리
            if '야 놀자' in title or re.search(r'야\s+놀자', title):
                return False
        
        # 1. 정확한 키워드 매칭
        if self.is_exact_keyword_match(title, keyword):
            return True
        
        # 2. 여행/숙박 관련 키워드가 함께 있는 경우만 허용
        if keyword in ['여기어때', '야놀자']:
            travel_keywords = ['여행', '숙박', '호텔', '펜션', '리조트', '관광', '휴가', '여행지', '숙소', '예약', '패키지', '할인', '혜택']
            has_travel_keyword = any(travel_kw in title for travel_kw in travel_keywords)
            if has_travel_keyword:
                return True
        
        return False

    def remove_keyword_from_title(self, title, keyword):
        """제목에서 키워드 제거"""
        if not keyword or not title:
            return title
        
        # 키워드가 제목에 포함되어 있으면 제거
        if keyword in title:
            # 키워드 앞뒤의 쉼표, 공백 등 정리
            title_clean = title.replace(keyword, '').strip()
            title_clean = title_clean.replace(',,', ',').strip(', ')
            title_clean = title_clean.replace('  ', ' ').strip()
            return title_clean
        
        return title
    
    def search_real_naver_news(self, keyword, max_articles=5, search_date=None):
        """네이버 뉴스 API 검색 - 날짜 지정 가능"""
        try:
            # 개선된 날짜 범위 설정
            date_range = self.get_date_range_for_search(search_date)
            target_date = date_range['target_str']
            
            self.logger.info(f"네이버 API 뉴스 검색: {keyword} (목표 날짜: {target_date})")
            
            # 네이버 뉴스 API URL
            api_url = "https://openapi.naver.com/v1/search/news.json"
            
            headers = {
                'X-Naver-Client-Id': os.getenv('NAVER_CLIENT_ID', ''),
                'X-Naver-Client-Secret': os.getenv('NAVER_CLIENT_SECRET', '')
            }
            
            params = {
                'query': keyword,
                'display': min(max_articles * 2, 100),  # 더 많은 결과를 가져와서 필터링
                'start': 1,
                'sort': 'date'  # 날짜순 정렬
            }
            
            self.logger.info(f"네이버 API 쿼리: {keyword}")
            
            response = self.session.get(api_url, headers=headers, params=params, timeout=8)
            
            if response.status_code != 200:
                self.logger.error(f"네이버 API 요청 실패: {response.status_code}")
                return []
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                self.logger.info("네이버 API에서 뉴스를 찾을 수 없습니다.")
                return []
            
            news_list = []
            for item in items:
                try:
                    title = item.get('title', '').replace('<b>', '').replace('</b>', '').strip()
                    link = item.get('link', '')
                    description = item.get('description', '').replace('<b>', '').replace('</b>', '').strip()
                    pub_date = item.get('pubDate', '')
                    
                    if not title or not link:
                        continue
                    
                    # 발행일 파싱
                    parsed_date = self.parse_pub_date(pub_date)
                    
                    # 날짜 정규화
                    normalized_date = self.normalize_date_format(parsed_date)
                    if not normalized_date:
                        self.logger.warning(f"네이버 API 날짜 형식 오류로 제외: {title[:50]}... (날짜: {parsed_date})")
                        continue
                    
                    # 개선된 날짜 검증
                    is_valid, validation_msg = self.validate_news_date(normalized_date, search_date, link)
                    if not is_valid:
                        self.logger.info(f"날짜 불일치로 제외: {title[:50]}... ({validation_msg})")
                        continue
                    
                                            # 당일 뉴스 포함 (실제 발행 날짜 기준)
                        # if self.is_today_news(normalized_date):
                        #     self.logger.info(f"네이버 API 당일 뉴스 제외: {title[:50]}... (날짜: {normalized_date})")
                        #     continue
                    
                    # 본문 추출 시도
                    full_content = self.extract_full_content(link)
                    if not full_content:
                        full_content = description
                    
                    # 발행사 추출
                    press = self.extract_press_from_url(link)
                    
                    # 하나투어 제외 로직 적용
                    if self.should_exclude_hanatour_news(title, full_content, keyword):
                        continue

                    news_data = {
                        'title': title,
                        'link': link,
                        'press': press,
                        'date': normalized_date,
                        'content_preview': description,
                        'full_content': full_content,
                        'keyword': keyword,
                        'search_date': search_date if search_date else target_date,
                        'source': '네이버뉴스'
                    }
                    
                    # "야놀자" 검색 시 "야 놀자"(띄어쓰기 포함) 결과 제외
                    try:
                        if keyword == '야놀자':
                            import re
                            if '야 놀자' in title or re.search(r'야\s+놀자', title):
                                self.logger.info(f"예외 키워드 규칙으로 제외: {title[:50]}... (키워드: {keyword})")
                                continue
                    except Exception:
                        pass
                    
                    
                    news_list.append(news_data)
                    self.logger.info(f"네이버 API 뉴스 수집: {title[:50]}... (날짜: {normalized_date})")
                    
                except Exception as e:
                    self.logger.warning(f"네이버 API 뉴스 처리 중 오류 (스킵): {e}")
                    continue
            
            self.logger.info(f"네이버 API에서 {len(news_list)}개 뉴스 수집 완료")
            return news_list
            
        except Exception as e:
            self.logger.warning(f"네이버 API 검색 중 오류 (빈 결과 반환): {e}")
            return []
    
    def get_original_link(self, original_url, title=""):
        """원문 링크 처리 - 네이버 뉴스 상세페이지 우선, 없으면 언론사 원문 링크"""
        try:
            if not original_url:
                return ""
            
            # 네이버 뉴스 상세페이지가 있는 경우 우선 사용
            if 'news.naver.com' in original_url:
                # 네이버 뉴스 상세페이지를 그대로 반환
                self.logger.info(f"네이버 뉴스 상세페이지 사용: {original_url[:50]}...")
                return original_url
            
            # 네이버 뉴스 상세페이지가 없는 경우 언론사 원문 링크 사용
            if original_url and 'http' in original_url:
                self.logger.info(f"언론사 원문 링크 사용: {original_url[:50]}...")
                return original_url
            
            return original_url
            
        except Exception as e:
            self.logger.warning(f"원문 링크 처리 중 오류 (기본값 반환): {e}")
            return original_url
    
    def clean_html(self, html_text):
        """HTML 태그 제거"""
        if not html_text:
            return ""
        
        # 간단한 HTML 태그 제거
        import re
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        clean_text = re.sub(r'&[^;]+;', '', clean_text)  # HTML 엔티티 제거
        return clean_text.strip()
    
    def extract_press_from_url(self, url):
        """URL에서 발행사 추출"""
        if not url:
            return "알 수 없음"
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname.lower()
            
            # 주요 언론사 매핑
            press_mapping = {
                'news.naver.com': '네이버 뉴스',
                'yna.co.kr': '연합뉴스',
                'yonhapnews.co.kr': '연합뉴스',
                'khan.co.kr': '경향신문',
                'hankyung.com': '한국경제',
                'hankookilbo.com': '한국일보',
                'chosun.com': '조선일보',
                'joongang.co.kr': '중앙일보',
                'donga.com': '동아일보',
                'seoul.co.kr': '서울신문',
                'hani.co.kr': '한겨레',
                'ohmynews.com': '오마이뉴스',
                'mk.co.kr': '매일경제',
                'mt.co.kr': '머니투데이',
                'edaily.co.kr': '이데일리',
                'biz.chosun.com': '조선비즈',
                'zdnet.co.kr': 'ZDNet Korea',
                'itworld.co.kr': 'ITWorld',
                'zdnet.com': 'ZDNet',
                'techcrunch.com': 'TechCrunch',
                'theverge.com': 'The Verge',
                'wired.com': 'Wired',
                'arstechnica.com': 'Ars Technica'
            }
            
            for domain, press in press_mapping.items():
                if domain in hostname:
                    return press
            
            # 도메인에서 직접 추출
            if '.' in hostname:
                parts = hostname.split('.')
                if len(parts) >= 2:
                    return parts[-2].title()
            
            return "알 수 없음"
            
        except Exception as e:
            return "알 수 없음"
    
    def parse_pub_date(self, pub_date_str):
        """발행일 파싱"""
        if not pub_date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # RFC 822 형식 파싱 (예: "Mon, 12 Aug 2024 10:30:00 +0900")
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date_str)
            return dt.strftime('%Y-%m-%d')
        except Exception as e:
            try:
                # 다른 형식 시도
                dt = datetime.strptime(pub_date_str, '%Y-%m-%d')
                return dt.strftime('%Y-%m-%d')
            except:
                return datetime.now().strftime('%Y-%m-%d')

    def is_today_news(self, news_date):
        """뉴스가 오늘 발행된 것인지 확인"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            return news_date == today
        except Exception as e:
            self.logger.error(f"오늘 뉴스 확인 중 오류: {e}")
            return False

    def filter_today_news(self, news_list):
        """뉴스 필터링 (당일 뉴스 포함)"""
        if not news_list:
            return []
        
        # 모든 뉴스를 포함 (당일 뉴스 제외하지 않음)
        filtered_news = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        for news in news_list:
            news_date = news.get('date', '')
            # 모든 뉴스를 포함 (날짜 검증만 수행)
            if news_date:
                filtered_news.append(news)
            else:
                self.logger.info(f"날짜 정보 없는 뉴스 제외: {news.get('title', '')[:50]}...")
        
        self.logger.info(f"뉴스 필터링: {len(news_list)}개 → {len(filtered_news)}개")
        return filtered_news
    
    def search_google_news(self, keyword, max_articles=3, search_date=None):
        """구글 뉴스 검색 - 날짜 지정 가능"""
        try:
            # 개선된 날짜 범위 설정
            date_range = self.get_date_range_for_search(search_date)
            after_date = date_range['after']
            before_date = date_range['before']
            target_date = date_range['target_str']
            
            # 구글 뉴스 검색 URL (날짜 범위 파라미터 포함)
            # after:YYYY-MM-DD before:YYYY-MM-DD 형식 사용
            search_url = f"https://news.google.com/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko&tbm=nws&tbs=cdr:1,cd_min:{after_date},cd_max:{before_date}"
            
            self.logger.info(f"구글 뉴스 검색: {keyword} (날짜 범위: {after_date} ~ {before_date})")
            self.logger.info(f"구글 뉴스 URL: {search_url}")
            
            response = self.session.get(search_url, timeout=8)
            
            if response.status_code != 200:
                self.logger.error(f"구글 뉴스 페이지 접근 실패: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 구글 뉴스 구조에 맞는 다양한 선택자들
            news_selectors = [
                'article',  # 기본 article 태그
                'div[data-n-tid]',  # 구글 뉴스 특정 데이터 속성
                '.NiLAwe',  # 구글 뉴스 클래스
                '.MQsxIb',  # 구글 뉴스 클래스
                '.IBr9hb',  # 구글 뉴스 클래스
                '.SoaBEf',  # 구글 뉴스 클래스
                '.WlydOe',  # 구글 뉴스 클래스
                'div[jslog]',  # 구글 뉴스 jslog 속성
            ]
            
            news_items = []
            for selector in news_selectors:
                items = soup.select(selector)
                if items:
                    news_items = items
                    self.logger.info(f"구글 뉴스 아이템 {len(items)}개 발견 (선택자: {selector})")
                    break
            
            if not news_items:
                # 대체 방법: 링크 기반 검색
                all_links = soup.find_all('a', href=True)
                news_links = [link for link in all_links if 'news.google.com' in link.get('href', '')]
                self.logger.info(f"구글 뉴스 링크 {len(news_links)}개 발견")
                
                news_list = []
                for link_elem in news_links[:max_articles]:
                    try:
                        title = link_elem.get_text(strip=True)
                        link = link_elem.get('href', '')
                        
                        if len(title) < 10 or not link:
                            continue
                        
                        # 구글 뉴스 링크를 실제 링크로 변환
                        if link.startswith('./'):
                            link = 'https://news.google.com' + link[1:]
                        elif link.startswith('/'):
                            link = 'https://news.google.com' + link
                        
                        # 본문 추출 시도
                        full_content = self.extract_full_content(link)
                        if not full_content:
                            full_content = f"{title} - {keyword} 관련 뉴스입니다."
                        
                        # 구글 뉴스에서 실제 발행 날짜 추출 시도
                        actual_date = self.extract_date_from_google_news(link_elem, link)
                        if not actual_date:
                            actual_date = target_date
                        
                        # 날짜 정규화
                        normalized_date = self.normalize_date_format(actual_date)
                        if not normalized_date:
                            self.logger.warning(f"구글 뉴스 날짜 형식 오류로 제외: {title[:50]}... (날짜: {actual_date})")
                            continue
                        
                        # 개선된 날짜 검증
                        is_valid, validation_msg = self.validate_news_date(normalized_date, search_date, link)
                        if not is_valid:
                            self.logger.warning(f"구글 뉴스 날짜 검증 실패로 제외: {title[:50]}... - {validation_msg}")
                            continue
                        
                        # 당일 뉴스 포함 (실제 발행 날짜 기준)
                        # if self.is_today_news(normalized_date):
                        #     self.logger.info(f"구글 뉴스 당일 뉴스 제외: {title[:50]}... (날짜: {normalized_date})")
                        #     continue
                        
                        # 하나투어 제외 로직 적용
                        if self.should_exclude_hanatour_news(title, full_content, keyword):
                            continue

                        news_data = {
                            'title': title,
                            'link': link,
                            'press': '구글 뉴스',
                            'date': normalized_date,
                            'content_preview': title,
                            'full_content': full_content,
                            'keyword': keyword,
                            'search_date': search_date if search_date else target_date,
                            'source': '구글뉴스'
                        }
                        # "야놀자" 검색 시 "야 놀자"(띄어쓰기 포함) 결과 제외
                        try:
                            if keyword == '야놀자':
                                import re
                                if '야 놀자' in title or re.search(r'야\s+놀자', title):
                                    self.logger.info(f"예외 키워드 규칙으로 제외: {title[:50]}... (키워드: {keyword})")
                                    continue
                        except Exception:
                            pass

                        news_list.append(news_data)
                        self.logger.info(f"구글 뉴스 수집: {title[:50]}... (날짜: {normalized_date})")
                        time.sleep(1)
                        
                    except Exception as e:
                        self.logger.warning(f"구글 뉴스 링크 처리 중 오류 (스킵): {e}")
                        continue
                
                self.logger.info(f"구글 뉴스에서 {len(news_list)}개 수집 완료")
                return news_list
            
            # 구조화된 뉴스 아이템 처리
            news_list = []
            for i, item in enumerate(news_items[:max_articles]):
                try:
                    # 다양한 제목 선택자 시도
                    title_selectors = [
                        'h3', 'h4', '.title', '.DY5T1d', '.ipQwMb', '.gPFEn', 'a[aria-label]'
                    ]
                    
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = item.select_one(selector)
                        if title_elem:
                            break
                    
                    # 링크 선택자 시도
                    link_selectors = [
                        'a', 'a[href]', '.WlydOe', '.SoaBEf'
                    ]
                    
                    link_elem = None
                    for selector in link_selectors:
                        link_elem = item.select_one(selector)
                        if link_elem and link_elem.get('href'):
                            break
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    
                    if len(title) < 10 or not link:
                        continue
                    
                    # 구글 뉴스 링크를 실제 링크로 변환
                    if link.startswith('./'):
                        link = 'https://news.google.com' + link[1:]
                    elif link.startswith('/'):
                        link = 'https://news.google.com' + link
                    
                    # 본문 추출 시도
                    full_content = self.extract_full_content(link)
                    if not full_content:
                        full_content = f"{title} - {keyword} 관련 뉴스입니다."
                    
                    # 구글 뉴스에서 실제 발행 날짜 추출 시도
                    actual_date = self.extract_date_from_google_news(item, link)
                    if not actual_date:
                        actual_date = target_date
                    
                    # 날짜 정규화
                    normalized_date = self.normalize_date_format(actual_date)
                    if not normalized_date:
                        self.logger.warning(f"구글 뉴스 날짜 형식 오류로 제외: {title[:50]}... (날짜: {actual_date})")
                        continue
                    
                    # 개선된 날짜 검증
                    is_valid, validation_msg = self.validate_news_date(normalized_date, search_date, link)
                    if not is_valid:
                        self.logger.warning(f"구글 뉴스 날짜 검증 실패로 제외: {title[:50]}... - {validation_msg}")
                        continue
                    
                                            # 당일 뉴스 포함 (실제 발행 날짜 기준)
                        # if self.is_today_news(normalized_date):
                        #     self.logger.info(f"구글 뉴스 당일 뉴스 제외: {title[:50]}... (날짜: {normalized_date})")
                        #     continue
                    
                    # 하나투어 제외 로직 적용
                    if self.should_exclude_hanatour_news(title, full_content, keyword):
                        continue

                    news_data = {
                        'title': title,
                        'link': link,
                        'press': '구글 뉴스',
                        'date': normalized_date,
                        'content_preview': title,
                        'full_content': full_content,
                        'keyword': keyword,
                        'search_date': search_date if search_date else target_date,
                        'source': '구글뉴스'
                    }
                    
                    # "야놀자" 검색 시 "야 놀자"(띄어쓰기 포함) 결과 제외
                    try:
                        if keyword == '야놀자':
                            import re
                            if '야 놀자' in title or re.search(r'야\s+놀자', title):
                                self.logger.info(f"예외 키워드 규칙으로 제외: {title[:50]}... (키워드: {keyword})")
                                continue
                    except Exception:
                        pass
                    
                    
                    news_list.append(news_data)
                    self.logger.info(f"구글 뉴스 수집: {title[:50]}... (날짜: {normalized_date})")
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.warning(f"구글 뉴스 아이템 처리 중 오류 (스킵): {e}")
                    continue
            
            self.logger.info(f"구글 뉴스에서 {len(news_list)}개 수집 완료")
            return news_list
            
        except Exception as e:
            self.logger.warning(f"구글 뉴스 검색 중 오류 (빈 결과 반환): {e}")
            return []
    
    def search_general_news(self, keyword, max_articles=5, search_date=None):
        """일반 뉴스 사이트 검색 - 날짜 지정 가능"""
        try:
            # 개선된 날짜 범위 설정
            date_range = self.get_date_range_for_search(search_date)
            target_date = date_range['target_str']
            
            self.logger.info(f"일반 뉴스 검색 시작: {keyword} (날짜 범위: {target_date} ~ {target_date})")
            
            all_news = []
            
            # 검색할 뉴스 사이트 목록
            news_sites = [
                {
                    'name': '연합뉴스',
                    'url': f"https://www.yna.co.kr/search/index?query={keyword}",
                    'link_selector': "a[href*='/view/']",
                    'date_selector': '.date'
                },
                {
                    'name': '경향신문',
                    'url': f"https://www.khan.co.kr/search/?word={keyword}",
                    'link_selector': "a[href*='/article/']",
                    'date_selector': '.date'
                },
                {
                    'name': '한겨레',
                    'url': f"https://search.hani.co.kr/search?searchword={keyword}",
                    'link_selector': "a[href*='/arti/']",
                    'date_selector': '.date'
                },
                {
                    'name': '조선일보',
                    'url': f"https://search.chosun.com/search?query={keyword}",
                    'link_selector': "a[href*='/article/']",
                    'date_selector': '.date'
                },
                {
                    'name': '중앙일보',
                    'url': f"https://search.joins.com/search?keyword={keyword}",
                    'link_selector': "a[href*='/article/']",
                    'date_selector': '.date'
                }
            ]
            
            for site in news_sites:
                try:
                    self.logger.info(f"{site['name']} 검색 중: {keyword}")
                    
                    # 대안 URL 시도
                    response = self.session.get(site['url'], timeout=8)
                    if response.status_code != 200:
                        # 대안 URL 시도
                        alt_url = f"https://search.naver.com/search.naver?where=news&query={keyword}+{site['name']}"
                        self.logger.info(f"{site['name']} 대안 URL 시도: {alt_url}")
                        response = self.session.get(alt_url, timeout=8)
                        
                        if response.status_code != 200:
                            self.logger.error(f"{site['name']} 접근 실패: {response.status_code}")
                            continue
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 링크 추출
                    links = soup.select(site['link_selector'])
                    self.logger.info(f"{site['name']}에서 {len(links)}개 링크 발견 (선택자: {site['link_selector']})")
                    
                    site_news = []
                    for link_elem in links[:max_articles]:
                        try:
                            title = link_elem.get_text(strip=True)
                            link = link_elem.get('href', '')
                            
                            if not title or not link or len(title) < 10:
                                continue
                            
                            # 정확한 키워드 매칭 확인
                            if not self.is_relevant_keyword_match(title, keyword):
                                self.logger.info(f"정확한 키워드 매칭 실패로 제외: {title[:50]}... (키워드: {keyword})")
                                continue
                            
                            # 상대 URL을 절대 URL로 변환
                            if link.startswith('/'):
                                link = f"https://{site['url'].split('/')[2]}{link}"
                            elif not link.startswith('http'):
                                link = f"https://{site['url'].split('/')[2]}/{link}"
                            
                            # 날짜 추출
                            date = self.extract_date_from_site(soup, link_elem, site['date_selector'], site['url'])
                            
                            # 날짜 정규화
                            normalized_date = self.normalize_date_format(date)
                            if not normalized_date:
                                self.logger.warning(f"{site['name']} 날짜 형식 오류로 제외: {title[:50]}... (날짜: {date})")
                                continue
                            
                            # 개선된 날짜 검증
                            is_valid, validation_msg = self.validate_news_date(normalized_date, search_date, link)
                            if not is_valid:
                                self.logger.warning(f"{site['name']} 날짜 검증 실패로 제외: {title[:50]}... - {validation_msg}")
                                continue
                            
                                                    # 당일 뉴스 포함 (실제 발행 날짜 기준)
                        # if self.is_today_news(normalized_date):
                        #     self.logger.info(f"{site['name']} 당일 뉴스 제외: {title[:50]}... (날짜: {normalized_date})")
                        #     continue
                            
                            # 본문 추출
                            full_content = self.extract_full_content(link)
                            if not full_content:
                                full_content = f"{title} - {keyword} 관련 뉴스입니다."
                            
                            # 하나투어 제외 로직 적용
                            if self.should_exclude_hanatour_news(title, full_content, keyword):
                                continue

                            news_data = {
                                'title': title,
                                'link': link,
                                'press': site['name'],
                                'date': normalized_date,
                                'content_preview': title,
                                'full_content': full_content,
                                'keyword': keyword,
                                'search_date': search_date if search_date else target_date,
                                'source': '일반뉴스'
                            }
                            

                            
                            site_news.append(news_data)
                            self.logger.info(f"{site['name']} 뉴스 수집: {title[:50]}... (날짜: {normalized_date})")
                            
                        except Exception as e:
                            self.logger.error(f"{site['name']} 링크 처리 중 오류: {e}")
                            continue
                    
                    all_news.extend(site_news)
                    
                except Exception as e:
                    self.logger.warning(f"{site['name']} 검색 중 오류 발생 (다음 신문사로 넘어갑니다): {e}")
                    continue
            
            self.logger.info(f"일반 뉴스에서 {len(all_news)}개 수집 완료")
            return all_news
            
        except Exception as e:
            self.logger.warning(f"일반 뉴스 검색 중 오류 (빈 결과 반환): {e}")
            return []
    
    def search_naver_news_crawling(self, keyword, max_articles=5, search_date=None):
        """네이버 뉴스 크롤링으로 뉴스 검색 (날짜 지정 가능)"""
        try:
            # 날짜 설정 (기본값: 전날)
            if search_date is None:
                date_range = self.get_yesterday_date_range()
                start_date = date_range['start_date']
                end_date = date_range['end_date']
                date_formatted = date_range['after']
            else:
                # 단일 날짜인 경우
                start_date = search_date
                end_date = search_date
                date_formatted = f"{search_date[:4]}-{search_date[4:6]}-{search_date[6:8]}"
            
            # 네이버 뉴스 검색 URL (날짜 범위 파라미터 포함)
            search_url = f"https://search.naver.com/search.naver?where=news&query={keyword}&ds={start_date}&de={end_date}"
            
            self.logger.info(f"네이버 뉴스 크롤링: {keyword} (날짜 범위: {start_date} ~ {end_date})")
            
            response = self.session.get(search_url, timeout=8)
            
            if response.status_code != 200:
                self.logger.error(f"네이버 뉴스 페이지 접근 실패: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            news_list = []
            
            # 모든 링크에서 뉴스 찾기 (가장 포괄적인 방법)
            all_links = soup.find_all('a', href=True)
            self.logger.info(f"전체 링크 {len(all_links)}개 발견")
            
            news_links = []
            for link in all_links:
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # 네이버 뉴스 링크 필터링 (더 포괄적으로)
                if ('news.naver.com' in href and 'article' in href) or \
                   ('news.naver.com' in href and len(title) > 15) or \
                   ('news.naver.com' in href and keyword in title):
                    news_links.append({
                        'title': title,
                        'link': href
                    })
            
            self.logger.info(f"네이버 뉴스 링크 {len(news_links)}개 발견")
            
            # 뉴스 데이터 생성
            for i, news_info in enumerate(news_links[:max_articles]):
                try:
                    title = news_info['title']
                    link = news_info['link']
                    
                    # 필터링 버튼 제외
                    if title in ['관련도순', '최신순', '전체', '정확도순', '정확도순', '관련도순'] or len(title) < 10:
                        self.logger.info(f"필터링 버튼 또는 짧은 제목 제외: {title}")
                        continue
                    
                    # 정확한 키워드 매칭 확인
                    if not self.is_relevant_keyword_match(title, keyword):
                        self.logger.info(f"정확한 키워드 매칭 실패로 제외: {title[:30]}... (키워드: {keyword})")
                        continue
                    
                    self.logger.info(f"뉴스 링크 처리 중: {title[:50]}...")
                    
                    # 본문 추출
                    full_content = self.extract_full_content(link)
                    if not full_content:
                        full_content = f"{title} - {keyword} 관련 뉴스입니다."
                    
                    # 발행사 추출
                    press = self.extract_press_from_url(link)
                    
                    # 날짜 정보 추출 시도
                    date_info = self.extract_date_from_news_page(link)
                    if not date_info:
                        date_info = date_formatted
                    
                    # 선택적 날짜 검증 (에러 발생 시 무시하고 계속 진행)
                    try:
                        is_valid, validation_msg = self.validate_news_date(date_info, search_date, link)
                        if not is_valid:
                            self.logger.warning(f"네이버 뉴스 날짜 검증 실패로 제외: {title[:50]}... - {validation_msg}")
                            # 검증 실패 시에도 기존 방식대로 계속 진행
                    except Exception as e:
                        self.logger.debug(f"날짜 검증 중 오류 무시: {e}")
                    
                                            # 당일 뉴스 포함
                        # if self.is_today_news(date_info):
                        #     self.logger.info(f"네이버 뉴스 크롤링 당일 뉴스 제외: {title[:50]}... (날짜: {date_info})")
                        #     continue
                    
                    # 하나투어 제외 로직 적용
                    if self.should_exclude_hanatour_news(title, full_content, keyword):
                        continue

                    news_data = {
                        'title': title,
                        'link': link,
                        'press': press,
                        'date': date_info,
                        'content_preview': title,
                        'full_content': full_content,
                        'keyword': keyword,
                        'search_date': search_date if search_date else f"{start_date}~{end_date}",
                        'source': '네이버뉴스크롤링'
                    }
                    
                    news_list.append(news_data)
                    self.logger.info(f"네이버 뉴스 크롤링 수집: {title[:50]}... (날짜: {date_info})")
                    
                    if len(news_list) >= max_articles:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"뉴스 링크 처리 중 오류 (스킵): {e}")
                    continue
            
            self.logger.info(f"네이버 뉴스 크롤링 완료: {len(news_list)}개 (날짜 범위: {start_date} ~ {end_date})")
            return news_list
            
        except Exception as e:
            self.logger.warning(f"네이버 뉴스 크롤링 중 오류 (빈 결과 반환): {e}")
            return []

    def extract_date_from_news_page(self, url):
        """뉴스 페이지에서 날짜 정보 추출 (기존 함수 - 호환성 유지)"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 날짜 선택자들 (기존 방식)
                date_selectors = [
                    'span.date',  # 네이버 뉴스 날짜
                    '.article_info .date',  # 기사 정보 날짜
                    '.news_date',  # 뉴스 날짜
                    'time',  # HTML5 time 태그
                    '.published',  # 발행일
                ]
                
                for selector in date_selectors:
                    date_elem = soup.select_one(selector)
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        # 날짜 형식 정리
                        if date_text:
                            return self.parse_date_from_text(date_text)
                
                # 새로운 강화된 날짜 추출 시도 (에러 발생 시 기존 방식으로 fallback)
                try:
                    enhanced_date = self.extract_date_enhanced(soup, url)
                    if enhanced_date:
                        return enhanced_date
                except Exception as e:
                    self.logger.warning(f"강화된 날짜 추출 실패, 기존 방식 사용: {e}")
                
                return None
                
        except Exception as e:
            self.logger.error(f"날짜 추출 중 오류: {e}")
            return None

    def extract_date_enhanced(self, soup, url):
        """강화된 날짜 추출 (새로운 기능)"""
        try:
            # 사이트별 특화 날짜 선택자
            site_specific_selectors = self.get_site_specific_date_selectors(url)
            
            # 1단계: 사이트별 특화 선택자로 날짜 추출
            for selector in site_specific_selectors:
                try:
                    date_elem = soup.select_one(selector)
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        if date_text:
                            parsed_date = self.parse_date_from_text(date_text)
                            if parsed_date:
                                self.logger.info(f"사이트별 선택자로 날짜 추출 성공: {selector} -> {parsed_date}")
                                return parsed_date
                except Exception as e:
                    self.logger.debug(f"선택자 {selector} 실패: {e}")
                    continue
            
            # 2단계: 메타 태그에서 날짜 추출
            try:
                meta_date = soup.find('meta', property='article:published_time')
                if meta_date:
                    content = meta_date.get('content', '')
                    if content:
                        parsed_date = self.parse_date_from_text(content)
                        if parsed_date:
                            self.logger.info(f"메타 태그로 날짜 추출 성공: {parsed_date}")
                            return parsed_date
            except Exception as e:
                self.logger.debug(f"메타 태그 추출 실패: {e}")
            
            # 3단계: 본문에서 날짜 패턴 추출 (선택적)
            try:
                content_date = self.extract_date_from_content(soup, url)
                if content_date:
                    self.logger.info(f"본문에서 날짜 추출 성공: {content_date}")
                    return content_date
            except Exception as e:
                self.logger.debug(f"본문 날짜 추출 실패: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"강화된 날짜 추출 중 오류: {e}")
            return None

    def get_site_specific_date_selectors(self, url):
        """사이트별 특화된 날짜 선택자 반환 (안전한 방식)"""
        try:
            if 'khan.co.kr' in url:  # 경향신문
                return [
                    '.article_date',
                    '.date',
                    '.article-info .date',
                    '.news-date',
                    '.publish-date',
                ]
            elif 'yna.co.kr' in url:  # 연합뉴스
                return [
                    '.date',
                    '.article-date',
                    '.news-date',
                    '.publish-date',
                ]
            elif 'hani.co.kr' in url:  # 한겨레
                return [
                    '.date',
                    '.article-date',
                    '.news-date',
                    '.publish-date',
                ]
            elif 'chosun.com' in url:  # 조선일보
                return [
                    '.date',
                    '.article-date',
                    '.news-date',
                    '.publish-date',
                ]
            elif 'joongang.co.kr' in url:  # 중앙일보
                return [
                    '.date',
                    '.article-date',
                    '.news-date',
                    '.publish-date',
                ]
            else:
                return []  # 기타 사이트는 빈 배열 반환
        except Exception as e:
            self.logger.error(f"사이트별 선택자 결정 중 오류: {e}")
            return []  # 에러 시 빈 배열 반환

    def extract_date_from_content(self, soup, url):
        """본문에서 날짜 패턴 추출 (안전한 방식)"""
        try:
            # 사이트별 본문 선택자
            content_selectors = self.get_site_specific_content_selectors(url)
            
            for selector in content_selectors:
                try:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        content_text = content_elem.get_text()
                        
                        # 날짜 패턴 검색
                        import re
                        date_patterns = [
                            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
                            r'(\d{4})-(\d{1,2})-(\d{1,2})',
                            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
                        ]
                        
                        for pattern in date_patterns:
                            match = re.search(pattern, content_text)
                            if match:
                                if len(match.groups()) == 3:
                                    year, month, day = match.groups()
                                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except Exception as e:
                    self.logger.debug(f"본문 선택자 {selector} 실패: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"본문에서 날짜 추출 중 오류: {e}")
            return None

    def get_site_specific_content_selectors(self, url):
        """사이트별 특화된 본문 선택자 반환 (안전한 방식)"""
        try:
            if 'khan.co.kr' in url:  # 경향신문
                return ['.article-body', '.article-content', '.content']
            elif 'yna.co.kr' in url:  # 연합뉴스
                return ['.article-body', '.article-content', '.content']
            elif 'hani.co.kr' in url:  # 한겨레
                return ['.article-body', '.article-content', '.content']
            elif 'chosun.com' in url:  # 조선일보
                return ['.article-body', '.article-content', '.content']
            elif 'joongang.co.kr' in url:  # 중앙일보
                return ['.article-body', '.article-content', '.content']
            else:
                return ['.content', '.article-content', '.news-content']
        except Exception as e:
            self.logger.error(f"사이트별 본문 선택자 결정 중 오류: {e}")
            return ['.content', '.article-content']  # 기본값 반환

    def validate_news_date(self, extracted_date, search_date=None, url=None):
        """추출된 뉴스 날짜의 합리성 검증 (선택적 사용)"""
        try:
            if not extracted_date:
                return True, "날짜 정보 없음 - 검증 생략"
            
            # 날짜 형식 검증
            if not self.is_valid_date_format(extracted_date):
                return False, f"잘못된 날짜 형식: {extracted_date}"
            
            # 현재 날짜 기준으로 합리적 범위 검증
            current_date = datetime.now()
            extracted_dt = datetime.strptime(extracted_date, '%Y-%m-%d')
            
            # 미래 날짜 검증 (1일 이상 미래는 비합리적)
            if extracted_dt > current_date + timedelta(days=1):
                return False, f"미래 날짜 비합리적: {extracted_date}"
            
            # 과거 날짜 검증 (5년 이상 과거는 의심스러움)
            if extracted_dt < current_date - timedelta(days=5*365):
                return False, f"너무 과거 날짜 의심: {extracted_date}"
            
            # 전날짜 기준 검증 (전날 발행된 뉴스만 허용)
            yesterday = current_date - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y-%m-%d')
            
            # 전날짜와 정확히 일치하는지 검증
            if extracted_date == yesterday_str:
                return True, f"전날짜 일치: {extracted_date}"
            else:
                return False, f"전날짜 불일치: 추출={extracted_date}, 기준={yesterday_str}"
            
            return True, "검증 통과"
            
        except Exception as e:
            self.logger.error(f"날짜 검증 중 오류: {e}")
            return True, f"검증 오류 - 기본 허용: {e}"  # 에러 시 기본적으로 허용

    def is_valid_date_format(self, date_str):
        """날짜 형식이 유효한지 검증"""
        if not date_str:
            return False
        
        try:
            # YYYY-MM-DD 형식 검증
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            try:
                # YYYYMMDD 형식 검증
                datetime.strptime(date_str, '%Y%m%d')
                return True
            except ValueError:
                return False



    def normalize_date_format(self, date_str):
        """날짜 형식을 YYYY-MM-DD로 정규화"""
        if not date_str:
            return None
        
        try:
            # YYYY-MM-DD 형식이면 그대로 반환
            datetime.strptime(date_str, '%Y-%m-%d')
            return date_str
        except ValueError:
            return None
    
    def clean_news_content(self, text):
        """뉴스 본문에서 노이즈 제거"""
        if not text:
            return ""
        
        import re
        
        # 1. 기자 정보 및 이메일 제거
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text) # 이메일
        text = re.sub(r'\(?([가-힣]{2,4})\s*기자\)?', '', text) # (홍길동 기자), 홍길동 기자
        text = re.sub(r'[가-힣]{2,4}\s*기자\s*=', '', text) # 홍길동 기자 =
        
        # 2. 저작권 및 재배포 금지 문구 제거
        text = re.sub(r'무단\s*전재\s*및\s*재배포\s*금지', '', text)
        text = re.sub(r'저작권자\s*\(c\).*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Copyrights\s*\(c\).*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'ⓒ\s*.*', '', text)
        
        # 3. 불필요한 공백 및 줄바꿈 정리
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # 4. 기타 노이즈 (구독, 제보 등)
        noise_patterns = [
            r'네이버에서 .* 구독하세요',
            r'SNS .* 팔로우',
            r'제보하기',
            r'구독하기',
            r'좋아요',
            r'공유하기'
        ]
        for pattern in noise_patterns:
            text = re.sub(pattern, '', text)
            
        return text.strip()
    
    def extract_full_content(self, news_url):
        """뉴스 본문 전체 추출"""
        try:
            response = self.session.get(news_url, timeout=10)
            if response.status_code != 200:
                return ""
            
            # 인코딩 처리 (한글 깨짐 방지)
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. 불필요한 요소 미리 제거 (전역)
            noise_selectors = [
                'script', 'style', 'header', 'footer', 'nav', 'aside',
                '.ad', '.advertisement', '.banner', '.social', '.share',
                '.related', '.recommend', '.popular', '.best',
                '.comment', '.reply', '.tag', '.category',
                '.footer-inner', '.header-inner', '.sidebar',
                '#footer', '#header', '#sidebar', '#comments',
                '.article-footer', '.article-header',
                '.news_guide', '.news_copyright', '.news_related',
                '.article_bottom', '.article_top',
                '.img_desc', '.caption', '.vod_area', '.video_area'
            ]
            for selector in noise_selectors:
                for elem in soup.select(selector):
                    elem.decompose()
            
            # 2. 본문 선택자 (우선순위 순)
            content_selectors = [
                '#dic_area',  # 네이버 뉴스 (신규)
                '#articleBodyContents',  # 네이버 뉴스 (기존)
                '#articleBody',  # 네이버 뉴스
                '.article_view',  # 다음 뉴스
                '#harmonyContainer',  # 다음 뉴스
                '.article_body',
                '.article_content',
                '.news_end',
                '.article_body_contents',
                '.article_text',
                '.article',
                '#article_body',
                '#article_content',
                '.content',
                '.article-content',
                '.news-content',
                '.post-content',
                '.entry-content',
                'article',
                '.text',
                '.body',
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 선택된 요소 내에서도 노이즈 다시 한번 제거
                    for elem in content_elem.select('.ad, .advertisement, .banner, .related'):
                        elem.decompose()
                    
                    raw_text = content_elem.get_text(separator='\n', strip=True)
                    cleaned_text = self.clean_news_content(raw_text)
                    
                    if len(cleaned_text) > 100:
                        content = cleaned_text
                        break
            
            # 3. 본문이 없으면 제목과 미리보기로 대체
            if not content or len(content) < 100:
                title_elem = soup.select_one('h1, .title, .headline')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                preview_elem = soup.select_one('.summary, .description, .preview')
                preview = preview_elem.get_text(strip=True) if preview_elem else ""
                
                content = f"{title}\n\n{preview}"
            
            return content
            
        except Exception as e:
            self.logger.error(f"본문 추출 중 오류: {e}")
            return ""
    
    def get_real_news_links(self, keyword):
        """실제 뉴스 사이트에서 링크 수집 (간단한 버전)"""
        try:
            # 간단한 뉴스 검색 (실패해도 괜찮음)
            search_url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
            response = self.session.get(search_url, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = []
                
                # 네이버 뉴스 링크 찾기
                for link_elem in soup.select('a[href*="news.naver.com"]')[:5]:
                    href = link_elem.get('href')
                    if href and 'article' in href:
                        links.append(href)
                
                return links
        except:
            pass
        
        # 실패 시 빈 리스트 반환
        return []
    
    def close(self):
        """세션 정리"""
        if self.session:
            self.session.close()
    
    def search_keywords_parallel(self, keywords, max_articles_per_keyword=5):
        """병렬로 여러 키워드 검색"""
        try:
            self.logger.info(f"병렬 키워드 검색 시작: {len(keywords)}개 키워드")
            start_time = time.time()
            
            all_news = []
            
            # ThreadPoolExecutor를 사용한 병렬 처리
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 각 키워드에 대한 Future 객체 생성
                future_to_keyword = {
                    executor.submit(self._search_keyword_safe, keyword, max_articles_per_keyword): keyword
                    for keyword in keywords
                }
                
                # 완료된 작업들을 처리
                for future in as_completed(future_to_keyword):
                    keyword = future_to_keyword[future]
                    try:
                        keyword_news = future.result(timeout=30)  # 30초 타임아웃
                        if keyword_news:
                            # 키워드 정보를 뉴스에 추가
                            for news in keyword_news:
                                news['source_keyword'] = keyword
                            all_news.extend(keyword_news)
                            self.logger.info(f"키워드 '{keyword}' 완료: {len(keyword_news)}개 뉴스")
                        else:
                            self.logger.warning(f"키워드 '{keyword}'에서 뉴스를 찾지 못했습니다.")
                    except Exception as e:
                        self.logger.error(f"키워드 '{keyword}' 처리 중 오류: {e}")
            
            # 중복 제거
            unique_news = self.remove_duplicate_news(all_news, "병렬검색")
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"병렬 검색 완료: {len(unique_news)}개 뉴스, 소요시간: {elapsed_time:.2f}초")
            
            return unique_news
            
        except Exception as e:
            self.logger.error(f"병렬 키워드 검색 중 오류: {e}")
            return []
    
    def _search_keyword_safe(self, keyword, max_articles):
        """스레드 안전한 키워드 검색"""
        try:
            # 요청 간격 제한 (Rate Limiting)
            with self.request_lock:
                # 최소 1초 간격 유지
                time.sleep(1)
            
            # 실제 뉴스 검색
            return self.search_naver_news_with_retry(keyword, max_articles)
            
        except Exception as e:
            self.logger.error(f"키워드 '{keyword}' 안전 검색 중 오류: {e}")
            return []
    
    def search_topics_parallel(self, topics_with_keywords):
        """주제별 키워드를 병렬로 검색"""
        try:
            self.logger.info(f"병렬 주제 검색 시작: {len(topics_with_keywords)}개 주제")
            start_time = time.time()
            
            topic_results = {}
            
            # 주제별로 병렬 처리
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_topic = {}
                
                for topic_name, keywords in topics_with_keywords.items():
                    future = executor.submit(self._search_topic_safe, topic_name, keywords)
                    future_to_topic[future] = topic_name
                
                # 완료된 작업들을 처리
                for future in as_completed(future_to_topic):
                    topic_name = future_to_topic[future]
                    try:
                        topic_news = future.result(timeout=60)  # 60초 타임아웃
                        topic_results[topic_name] = topic_news
                        self.logger.info(f"주제 '{topic_name}' 완료: {len(topic_news)}개 뉴스")
                    except Exception as e:
                        self.logger.error(f"주제 '{topic_name}' 처리 중 오류: {e}")
                        topic_results[topic_name] = []
            
            elapsed_time = time.time() - start_time
            total_news = sum(len(news) for news in topic_results.values())
            self.logger.info(f"병렬 주제 검색 완료: {total_news}개 뉴스, 소요시간: {elapsed_time:.2f}초")
            
            return topic_results
            
        except Exception as e:
            self.logger.error(f"병렬 주제 검색 중 오류: {e}")
            return {}
    
    def _search_topic_safe(self, topic_name, keywords):
        """스레드 안전한 주제별 검색"""
        try:
            # 키워드별로 검색
            all_news = []
            for keyword in keywords:
                try:
                    # 요청 간격 제한
                    with self.request_lock:
                        time.sleep(1)
                    
                    keyword_news = self.search_naver_news_with_retry(keyword, 5)
                    if keyword_news:
                        # 주제와 키워드 정보 추가
                        for news in keyword_news:
                            news['topic'] = topic_name
                            news['source_keyword'] = keyword
                        all_news.extend(keyword_news)
                        
                except Exception as e:
                    self.logger.error(f"주제 '{topic_name}' 키워드 '{keyword}' 검색 중 오류: {e}")
            
            # 주제별 중복 제거
            unique_news = self.remove_duplicate_news(all_news, topic_name)
            
            # 주제별 최대 개수 제한 (10개)
            if len(unique_news) > 10:
                unique_news = unique_news[:10]
            
            return unique_news
            
        except Exception as e:
            self.logger.error(f"주제 '{topic_name}' 안전 검색 중 오류: {e}")
            return []

    def cleanup(self):
        """정리 메서드 (NewsletterSystem 호환)"""
        self.close()
            
    def __del__(self):
        """소멸자에서 정리"""
        self.close()

    def extract_date_from_google_news(self, item, link):
        """구글 뉴스에서 실제 발행 날짜 추출 (강화된 버전)"""
        try:
            # 1. 구글 뉴스 아이템에서 날짜 정보 추출
            date_selectors = [
                'time',  # HTML5 time 태그
                '.time',  # 시간 클래스
                '.date',  # 날짜 클래스
                '.published',  # 발행일 클래스
                '[datetime]',  # datetime 속성
                '.aXjCH',  # 구글 뉴스 시간 클래스
                '.hvbAAd',  # 구글 뉴스 시간 클래스
                '.MUxGbd',  # 구글 뉴스 시간 클래스
                '.UPmit',   # 구글 뉴스 시간 클래스
            ]
            
            for selector in date_selectors:
                date_elem = item.select_one(selector)
                if date_elem:
                    # datetime 속성 확인
                    datetime_attr = date_elem.get('datetime', '')
                    if datetime_attr:
                        try:
                            # ISO 형식 날짜 파싱
                            from datetime import datetime
                            dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                            return dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    
                    # 텍스트에서 날짜 추출
                    date_text = date_elem.get_text(strip=True)
                    if date_text:
                        parsed_date = self.parse_date_from_text(date_text)
                        if parsed_date:
                            return parsed_date
            
            # 2. 링크에서 날짜 정보 추출 (구글 뉴스 URL 패턴)
            if 'news.google.com' in link:
                import re
                # 구글 뉴스 URL에서 날짜 패턴 찾기
                date_patterns = [
                    r'/(\d{4})/(\d{2})/(\d{2})/',  # /2025/08/12/
                    r'(\d{4})-(\d{2})-(\d{2})',   # 2025-08-12
                    r'(\d{4})(\d{2})(\d{2})',     # 20250812
                    r'(\d{4})년(\d{1,2})월(\d{1,2})일',  # 2025년8월12일
                    r'(\d{4})\.(\d{1,2})\.(\d{1,2})',    # 2025.8.12
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, link)
                    if match:
                        if len(match.groups()) == 3:
                            year, month, day = match.groups()
                            # 월과 일을 2자리로 맞춤
                            month = month.zfill(2)
                            day = day.zfill(2)
                            return f"{year}-{month}-{day}"
                        elif len(match.groups()) == 1:
                            date_str = match.group(1)
                            if len(date_str) == 8:
                                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            # 3. 실제 뉴스 페이지에서 날짜 추출
            try:
                response = self.session.get(link, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 메타 태그에서 날짜 정보 추출
                    meta_selectors = [
                        'meta[property="article:published_time"]',
                        'meta[name="publish_date"]',
                        'meta[name="date"]',
                        'meta[property="og:updated_time"]',
                        'meta[name="article:published_time"]',
                        'meta[property="og:published_time"]',
                    ]
                    
                    for selector in meta_selectors:
                        meta_elem = soup.select_one(selector)
                        if meta_elem:
                            content = meta_elem.get('content', '')
                            if content:
                                try:
                                    from datetime import datetime
                                    dt = datetime.fromisoformat(content.replace('Z', '+00:00'))
                                    return dt.strftime('%Y-%m-%d')
                                except:
                                    pass
                    
                    # HTML에서 날짜 정보 추출
                    date_selectors = [
                        'time[datetime]',
                        '.published',
                        '.date',
                        '.article-date',
                        '.news-date',
                        '.post-date',
                        '.entry-date',
                        '.publish-date',
                    ]
                    
                    for selector in date_selectors:
                        date_elem = soup.select_one(selector)
                        if date_elem:
                            datetime_attr = date_elem.get('datetime', '')
                            if datetime_attr:
                                try:
                                    from datetime import datetime
                                    dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                                    return dt.strftime('%Y-%m-%d')
                                except:
                                    pass
                            
                            date_text = date_elem.get_text(strip=True)
                            if date_text:
                                parsed_date = self.parse_date_from_text(date_text)
                                if parsed_date:
                                    return parsed_date
                                    
            except Exception as e:
                self.logger.error(f"뉴스 페이지 날짜 추출 중 오류: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"구글 뉴스 날짜 추출 중 오류: {e}")
            return None