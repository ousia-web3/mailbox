# [IT본부] 하나투어 뉴스레터 자동화 시스템

하나투어 IT본부를 위한 전문 뉴스레터 자동화 시스템입니다. 네이버 뉴스를 자동으로 수집하고 GPT-4o-mini를 통해 요약하여 이메일로 발송합니다.

## 📋 목차
- [주요 기능](#주요-기능)
- [뉴스 수집 및 요약 정책](#뉴스-수집-및-요약-정책)
- [설치 및 설정](#설치-및-설정)
- [사용법](#사용법)
- [시스템 구성](#시스템-구성)
- [API 참조](#api-참조)
- [문제 해결](#문제-해결)
- [성능 최적화](#성능-최적화)

## 🚀 주요 기능

### 핵심 기능
- **키워드 기반 뉴스 수집**: IT, AI, 여행 관련 키워드를 통한 맞춤형 뉴스 수집
- **AI 기반 요약**: GPT-4o-mini를 활용한 고품질 뉴스 요약
- **비중 기반 수집**: 주제별 중요도에 따른 차등 뉴스 수집 (IT 35%, AI 35%, 여행 30%)
- **이메일 자동 발송**: HTML 형식의 전문적인 뉴스레터 발송
- **웹 대시보드**: Flask 기반 실시간 모니터링 및 관리 인터페이스
- **스케줄러**: 자동화된 정기 발송 시스템
- **에러 복구**: 강력한 Fallback 메커니즘과 재시도 로직

### 고급 기능
- **다중 뉴스 소스**: 실제 뉴스와 샘플 데이터의 지능적 조합
- **PICK 요약 제어**: 설정을 통한 PICK 요약 기능 활성화/비활성화
- **보안 설정**: 환경변수 검증 및 보안 모범 사례 적용
- **UTF-8 지원**: Windows 환경에서의 완전한 한글 지원
- **상세 로깅**: 컴포넌트별 세분화된 로그 관리
- **테스트 스위트**: 시스템 신뢰성을 위한 포괄적 테스트

### 수신자 관리 기능 (신규)
- **웹 기반 수신자 관리**: 실시간 수신자 추가/제거/검색
- **대량 수신자 추가**: Ctrl+C/V를 통한 텍스트 기반 대량 등록
- **실시간 검색**: Ctrl+F 단축키 지원 검색 기능
- **JSON 기반 데이터 저장**: 안전하고 확장 가능한 데이터 관리
- **자동 .env 동기화**: 기존 시스템과의 완벽 호환성
- **통계 대시보드**: 전체/활성/비활성 수신자 수 실시간 표시

## 📊 뉴스 수집 및 요약 정책

### 수집 정책

#### 주제별 비중 (2025년 기준)
```yaml
IT 분야: 35%
  - 키워드: AI 인프라, 양자 컴퓨팅, 엣지컴퓨팅, 6G 네트워크, 하이브리드 컴퓨팅
  - 목표 기사 수: 최대 10개

AI 분야: 35%  
  - 키워드: 에이전틱 AI, 멀티모달 AI, 온디바이스 AI, 초개인화 AI, AI 거버넌스
  - 목표 기사 수: 최대 10개

여행 분야: 30%
  - 키워드: 하나투어, 모두투어, 마이리얼트립, 교원투어, 여기어때, 야놀자, 에어비앤비, 문체부, 패키지여행
  - 목표 기사 수: 최대 10개
```

#### 수집 프로세스
1. **키워드별 검색**: 각 키워드당 5개 기사 수집 (네이버 뉴스 API)
2. **중복 제거**: 제목 기준 중복 기사 자동 제거
3. **품질 필터링**: 관련성과 신선도 기준 필터링
4. **수량 조절**: 주제당 최대 10개로 제한
5. **최신순 정렬**: 발행일 기준 최신 기사 우선 선택

#### 수집 조건
- **검색 간격**: 키워드별 5초 대기 (API 제한 준수)
- **최대 기사 수**: 전체 30개 (주제당 10개 × 3개 주제)
- **수집 시간대**: 매일 09:00, 18:00 (기본 설정)
- **백업 메커니즘**: API 실패 시 샘플 데이터 자동 생성

### 요약 정책

#### AI 모델 설정
```yaml
모델: GPT-4o-mini
최대 토큰: 500 (개별 요약), 300 (주제 종합)
온도: 0.3 (일관성 보장)
타임아웃: 30초
재시도: 최대 3회
```

#### 요약 단계
1. **개별 기사 요약**
   - 길이: 200자 이내
   - 핵심 내용: 사실, 영향, 의미
   - 스타일: 객관적, 간결함

2. **주제별 종합 요약**
   - 길이: 200자 이내
   - 내용: 전반적 동향과 주요 이슈
   - 관점: 비즈니스 영향도 중심

3. **PICK 요약**
   - 개수: 3-5개 핵심 포인트
   - 길이: 각 40자 미만
   - 포커스: 액션 아이템과 트렌드

#### 품질 관리
- **사실 검증**: 원문 대비 정확성 확인
- **톤앤매너**: IT 전문가 대상 전문적 톤
- **가독성**: 이메일 환경 최적화된 포맷
- **일관성**: 템플릿 기반 구조화된 요약

### 콘텐츠 거버넌스

#### 필터링 기준
- **관련성 점수**: 키워드 매칭도 70% 이상
- **신뢰도 검증**: 주요 언론사 우선 선택
- **중복성 관리**: 유사 내용 기사 자동 제거
- **적시성**: 24시간 이내 발행 기사 우선

#### 품질 보증
- **자동 검증**: 요약 품질 자동 평가
- **예외 처리**: 부적절한 콘텐츠 자동 제외
- **백업 시스템**: 수집 실패 시 대체 콘텐츠 제공
- **피드백 루프**: 시스템 개선을 위한 로그 분석

## 🔧 설치 및 설정

### 시스템 요구사항
- Python 3.8 이상
- Chrome 브라우저 (Selenium용)
- 메모리 2GB 이상
- 디스크 공간 500MB 이상

### 1. 패키지 설치

```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

**필수 패키지:**
```
selenium==4.34.2          # 웹 스크래핑
webdriver-manager==4.0.2   # ChromeDriver 자동 관리
python-dotenv==1.1.1       # 환경변수 관리
requests==2.32.4           # HTTP 클라이언트
beautifulsoup4==4.13.4     # HTML 파싱
openai==1.97.1             # GPT API
schedule==1.2.2            # 작업 스케줄링
flask==2.3.3               # 웹 인터페이스
flask-cors==4.0.0          # CORS 지원
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
# ===== 필수 설정 =====
# OpenAI API 설정
OPENAI_API_KEY=sk-proj-your_api_key_here

# 이메일 설정
EMAIL_SENDER=your_email@hanatour.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_RECEIVER=team@hanatour.com,manager@hanatour.com

# ===== 선택적 설정 =====
# 네이버 API 설정 (더 안정적인 수집을 위해 권장)
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here

# 뉴스레터 커스터마이징
NEWSLETTER_TITLE=[IT본부] 하나투어 뉴스레터
MAX_ARTICLES_PER_TOPIC=10
MAX_TOPICS=5

# Flask 웹 서버 설정
FLASK_SECRET_KEY=auto_generated_secure_key
FLASK_PORT=5000
```

### 3. 이메일 설정 가이드

#### Microsoft Outlook 설정
```yaml
이메일: @hanatour.com 또는 @outlook.com
비밀번호: 일반 계정 비밀번호
SMTP: smtp-mail.outlook.com:587
보안: STARTTLS
```

#### Gmail 설정 (백업용)
1. Google 계정 → 보안 → 2단계 인증 활성화
2. 앱 비밀번호 생성 → 메일 앱 선택
3. 생성된 16자리 비밀번호를 `EMAIL_PASSWORD`에 입력

## 💻 사용법

### 웹 인터페이스 (권장)

```bash
# 웹 서버 시작
python web_app.py

# 브라우저에서 접속
http://localhost:5000
```

**웹 인터페이스 주요 기능:**
- 📊 실시간 시스템 상태 모니터링
- 🔧 키워드 및 주제 관리
- 📧 즉시 뉴스레터 생성 및 발송
- 🧪 시스템 컴포넌트별 테스트
- 📋 실시간 로그 모니터링
- ⚙️ 설정 변경 및 저장
- 👥 **수신자 관리** (신규)

### 수신자 관리 사용법

#### 1. 수신자 관리 페이지 접속
- 메인 대시보드에서 "수신자 관리" 버튼 클릭
- 또는 직접 URL 접속: `http://localhost:5000/recipients`

#### 2. 수신자 추가 방법

**단일 수신자 추가:**
1. "이메일 주소" 입력창에 이메일 입력
2. Enter 키 또는 "추가" 버튼 클릭

**대량 수신자 추가 (Ctrl+C/V):**
1. "대량 추가" 텍스트 영역 클릭
2. 이메일 목록을 복사 (Ctrl+C)
3. 텍스트 영역에 붙여넣기 (Ctrl+V)
4. "대량 추가" 버튼 클릭

**지원되는 대량 추가 형식:**
```
user1@example.com
user2@example.com, user3@example.com
user4@example.com; user5@example.com
```

#### 3. 수신자 검색 및 제거

**검색 (Ctrl+F):**
1. 검색창에 검색어 입력
2. 실시간으로 결과 필터링
3. Ctrl+F 단축키로 검색창 포커스

**수신자 제거:**
1. 수신자 목록에서 해당 이메일 옆의 "×" 버튼 클릭
2. 확인 후 즉시 제거

#### 4. .env 파일 동기화

**수신자 → .env 동기화:**
- "ENV 동기화" 버튼 클릭
- 현재 활성 수신자들이 .env 파일에 자동 저장

**기존 .env → 수신자 가져오기:**
- "ENV 가져오기" 버튼 클릭
- 기존 .env 파일의 수신자들을 관리 시스템으로 가져오기

#### 5. 통계 확인
- **전체 수신자**: 등록된 모든 수신자 수
- **활성 수신자**: 현재 뉴스레터를 받는 수신자 수
- **비활성 수신자**: 일시 중지된 수신자 수

### 명령줄 인터페이스

```bash
# 대화형 모드
python main.py

# 직접 뉴스레터 생성
python main.py --generate

# 스케줄러 모드
python main.py --scheduler

# 시스템 테스트
python main.py --test

# 백그라운드 실행 (Linux/macOS)
nohup python main.py --scheduler > scheduler.log 2>&1 &
```

### 빠른 시작 가이드

1. **초기 설정 검증**
   ```bash
   python -c "from security_config import SecurityConfig; print(SecurityConfig().validate_environment_variables())"
   ```

2. **테스트 실행**
   ```bash
   python tests/test_news_sample.py
   ```

3. **첫 뉴스레터 생성**
   ```bash
   python main.py --generate
   ```

### 🚀 간편 실행 방법 (Windows)

#### 1. 웹 인터페이스 실행 (권장)
```bash
start_newsletter.bat 더블클릭
```
- **기능**: 웹 브라우저에서 뉴스레터 시스템 관리
- **URL**: http://localhost:5000
- **특징**: 
  - 키워드 설정 관리
  - 뉴스레터 미리보기
  - 수동 뉴스레터 생성
  - 시스템 상태 확인

#### 2. 직접 뉴스레터 생성 및 발송
```bash
run_newsletter.bat 더블클릭
```
- **기능**: 뉴스 수집 → 요약 → 이메일 발송을 자동으로 수행
- **특징**:
  - 한 번 실행으로 완료
  - 자동화에 적합
  - 작업 스케줄러에 등록 가능

### 📋 실행 파일 설명

| 파일명 | 기능 | 사용 목적 |
|--------|------|-----------|
| `start_newsletter.bat` | 웹 서버 시작 | 웹 UI로 관리 |
| `run_newsletter.bat` | 뉴스레터 생성/발송 | 자동 실행 |

### 🎯 사용 시나리오

#### 웹 인터페이스 사용할 때
- ✅ 키워드 설정을 변경하고 싶을 때
- ✅ 뉴스레터를 미리보기하고 싶을 때
- ✅ 시스템 상태를 확인하고 싶을 때
- ✅ 수동으로 뉴스레터를 생성하고 싶을 때

#### 직접 실행 사용할 때
- ✅ 매일 정해진 시간에 자동으로 뉴스레터 발송
- ✅ 작업 스케줄러에 등록하여 자동화
- ✅ 간단히 한 번만 뉴스레터 생성

### PICK 요약 기능 제어

PICK 요약 기능을 활성화/비활성화할 수 있습니다:

```bash
# PICK 요약 기능 비활성화
python toggle_pick_summary.py 비활성화

# PICK 요약 기능 활성화
python toggle_pick_summary.py 활성화

# 현재 상태 확인
python toggle_pick_summary.py
```

**설정 파일 직접 편집:**
`keywords_config.json` 파일에서 `enable_pick_summary` 값을 변경:
```json
{
  "enable_pick_summary": false  // false: 비활성화, true: 활성화
}
```

### PICK 요약 기능 재활성화 가이드

나중에 PICK 요약 기능을 다시 사용하려면:

#### 1. 명령줄로 간단하게 활성화
```bash
python toggle_pick_summary.py 활성화
```

#### 2. 대화형으로 활성화
```bash
python toggle_pick_summary.py
# 그 후 "1" 선택 (활성화)
```

#### 3. 설정 파일 직접 편집
`keywords_config.json` 파일에서:
```json
{
  "enable_pick_summary": true  // false에서 true로 변경
}
```

#### 4. 활성화 후 확인 방법
```bash
# 현재 상태 확인
python toggle_pick_summary.py

# 설정 파일 확인
python -c "from keyword_manager import KeywordManager; km = KeywordManager(); print('PICK 요약 설정:', km.get_pick_summary_setting())"
```

#### 5. 요청 예시
**간단한 요청:**
```
"PICK 요약 기능을 다시 활성화해줘"
```

**상세한 요청:**
```
"뉴스레터 PICK 요약 기능을 다시 활성화하고 테스트해줘"
```

**설정 확인 요청:**
```
"현재 PICK 요약 설정 상태를 확인해줘"
```

**특정 조건으로 활성화:**
```
"PICK 요약 기능을 활성화하고, 뉴스레터 생성해서 PICK 요약이 제대로 나오는지 테스트해줘"
```

**웹 인터페이스에서 확인:**
```
"PICK 요약 기능을 활성화하고 웹 인터페이스에서 뉴스레터 미리보기로 확인해줘"
```

### 🔧 설정 파일

#### 필수 파일 (루트 폴더에 있어야 함)
- `keywords_config.json` - 키워드 설정
- `.env` - 환경 설정 (API 키 등)

### ⚠️ 주의사항

1. **Python 설치 필요**: Python이 시스템에 설치되어 있어야 함
2. **의존성 패키지**: `requirements.txt`의 패키지들이 설치되어 있어야 함
3. **설정 파일**: 루트 폴더에 설정 파일들이 있어야 함

### 🛠️ 문제 해결

#### 웹 서버가 시작되지 않는 경우
1. Python이 설치되어 있는지 확인
2. 필요한 패키지 설치: `pip install -r requirements.txt`
3. 포트 5000이 사용 중인지 확인

#### 뉴스레터 생성이 실패하는 경우
1. `.env` 파일의 API 키가 올바른지 확인
2. 인터넷 연결 상태 확인
3. 로그 파일 확인

## 🏗️ 시스템 구성

### 아키텍처 개요

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │  Command Line   │    │   Scheduler     │
│   (Flask App)   │    │   Interface     │    │  (Auto Mode)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼──────────────┐
                    │    Newsletter System       │
                    │   (Central Orchestrator)   │
                    └─────────────┬──────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐         ┌──────▼───────┐       ┌──────▼──────┐
    │   News    │         │     News     │       │   Email     │
    │ Collector │         │ Summarizer   │       │   Sender    │
    │(Selenium) │         │(GPT-4o-mini) │       │   (SMTP)    │
    └───────────┘         └──────────────┘       └─────────────┘
```

### 핵심 컴포넌트

#### 1. 뉴스레터 시스템 (`newsletter_system.py`)
```python
class NewsletterSystem:
    """중앙 orchestrator - 모든 컴포넌트를 통합 관리"""
    
    주요 메서드:
    - generate_newsletter(): 전체 뉴스레터 생성 프로세스 실행
    - collect_news_for_topic(): 주제별 뉴스 수집 (비중 적용)
    - summarize_news_list(): AI 기반 뉴스 요약
    - generate_newsletter_content(): HTML 이메일 템플릿 생성
```

#### 2. 수신자 관리 시스템 (신규)
```python
class SimpleRecipientManager:
    """JSON 기반 수신자 관리 시스템"""
    
    주요 파일:
    - recipient_manager.py: 수신자 관리 클래스
    - recipients.json: 수신자 데이터 저장소
    - templates/recipients.html: 웹 관리 인터페이스
    
    주요 기능:
    - 단일/대량 수신자 추가/제거
    - 실시간 검색 (Ctrl+F)
    - .env 파일 자동 동기화
    - 통계 대시보드
```

#### 3. 뉴스 수집기 (`news_collector_working.py`)
```python
class WorkingNewsCollector:
    """Selenium 기반 네이버 뉴스 수집기"""
    
    핵심 기능:
    - search_naver_news_with_retry(): 재시도 로직이 포함된 뉴스 검색
    - extract_news_info(): 뉴스 메타데이터 추출
    - handle_selenium_errors(): Selenium 오류 처리
    - cleanup(): 리소스 정리
```

#### 3. AI 요약기 (`news_summarizer.py`)
```python
class NewsSummarizer:
    """GPT-4o-mini 기반 뉴스 요약 시스템"""
    
    요약 타입:
    - summarize_news(): 개별 기사 요약 (200자)
    - summarize_topic_news(): 주제별 종합 요약 (200자)
    - generate_pick_summary(): PICK 요약 (3-5개 포인트)
```

#### 4. 이메일 발송기 (`email_sender.py`)
```python
class EmailSender:
    """멀티 플랫폼 이메일 발송 시스템"""
    
    지원 플랫폼:
    - Microsoft Outlook (주 사용)
    - Gmail (백업)
    - 기타 SMTP 서버
    
    기능:
    - HTML 형식 이메일
    - 첨부파일 지원
    - 배치 발송
```

#### 5. 키워드 매니저 (`keyword_manager.py`)
```python
class KeywordManager:
    """키워드 및 주제 설정 관리"""
    
    관리 기능:
    - 주제 추가/수정/삭제
    - 키워드 관리
    - 비중 설정
    - JSON 기반 설정 저장
```

### 보조 컴포넌트

#### 에러 복구 시스템 (`error_recovery.py`)
- **RetryConfig**: 재시도 설정 클래스
- **FallbackManager**: Fallback 데이터 생성
- **robust_function**: 데코레이터 기반 에러 처리

#### 보안 설정 (`security_config.py`)
- 환경변수 검증
- API 키 형식 검증
- 민감정보 마스킹
- 보안 모범사례 검사

#### 로깅 시스템 (`logging_config.py`)
- UTF-8 호환 로깅
- 컴포넌트별 로그 파일
- 로그 레벨 관리
- 파일 로테이션

### 파일 구조

```
newsletter/
├── 📁 핵심 시스템
│   ├── main.py                    # 메인 실행 파일
│   ├── newsletter_system.py       # 중앙 orchestrator
│   ├── news_collector_working.py  # 뉴스 수집기
│   ├── news_summarizer.py         # AI 요약기
│   ├── email_sender.py           # 이메일 발송기
│   ├── keyword_manager.py        # 키워드 관리자
│   └── recipient_manager.py      # 수신자 관리자 (신규)
├── 📁 웹 인터페이스
│   ├── web_app.py               # Flask 웹 서버
│   ├── templates/               # HTML 템플릿
│   │   ├── index.html          # 메인 대시보드
│   │   ├── preview.html        # 뉴스레터 미리보기
│   │   └── recipients.html     # 수신자 관리 페이지 (신규)
│   └── static/                 # 정적 파일 (CSS, JS)
├── 📁 설정 및 보안
│   ├── .env                    # 환경변수 (gitignore)
│   ├── keywords_config.json    # 키워드 설정
│   ├── recipients.json         # 수신자 데이터 (신규)
│   ├── security_config.py      # 보안 설정
│   └── windows_utf8.py         # Windows UTF-8 지원
├── 📁 유틸리티
│   ├── error_recovery.py       # 에러 복구 시스템
│   ├── logging_config.py       # 로깅 설정
│   └── requirements.txt        # Python 의존성
├── 📁 테스트
│   ├── tests/
│   │   ├── test_news.py        # 뉴스 수집 테스트
│   │   ├── test_news_sample.py # 샘플 데이터 테스트
│   │   └── test_improvements.py # 시스템 개선 테스트
├── 📁 문서
│   └── docs/                   # 프로젝트 문서 (신규)
│       ├── TASK_OVERVIEW.md    # 작업 개요
│       ├── TASK_1_COMPLETED.md # 작업 완료 보고서들
│       └── ...
└── 📁 로그 및 데이터
    └── logs/                   # 시스템 로그
        ├── newsletter.log      # 메인 시스템 로그
        ├── web_newsletter.log  # 웹 애플리케이션 로그
        ├── news_collector.log  # 뉴스 수집 로그
        └── working_news_collector.log # 개선된 수집기 로그
```

## 📚 API 참조

### NewsletterSystem API

```python
# 시스템 초기화
system = NewsletterSystem()

# 뉴스레터 생성 및 발송
success = system.generate_newsletter()

# 특정 주제 뉴스 수집
news_list = system.collect_news_for_topic(topic_config)

# 뉴스 요약
summary = system.summarize_news_list(news_list, topic_name)
```

### 수신자 관리 API (신규)

#### SimpleRecipientManager API

```python
# 수신자 관리자 초기화
manager = SimpleRecipientManager()

# 단일 수신자 추가
result = manager.add_recipient("user@example.com")

# 대량 수신자 추가
emails_text = "user1@example.com\nuser2@example.com, user3@example.com"
result = manager.add_multiple_recipients(emails_text)

# 수신자 검색
results = manager.search_recipients("user")

# 수신자 제거
success = manager.remove_recipient("user@example.com")

# 통계 조회
stats = manager.get_stats()  # {'total': 10, 'active': 8, 'inactive': 2}

# 활성 수신자 이메일 목록
emails = manager.get_active_emails()

# .env 파일 동기화
env_content = manager.export_to_env_format()
```

#### 웹 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 | 요청/응답 |
|-----------|--------|------|-----------|
| `/api/recipients` | GET | 수신자 목록 조회 | `?search=keyword` (선택) |
| `/api/recipients` | POST | 단일 수신자 추가 | `{"email": "user@example.com"}` |
| `/api/recipients/bulk` | POST | 대량 수신자 추가 | `{"emails": "email1@example.com\nemail2@example.com"}` |
| `/api/recipients/<email>` | DELETE | 수신자 제거 | - |
| `/api/recipients/sync` | POST | .env 파일 동기화 | - |
| `/api/recipients/import-env` | POST | .env 파일에서 가져오기 | - |
| `/recipients` | GET | 수신자 관리 페이지 | HTML 페이지 |

**응답 형식:**
```json
{
  "status": "success",
  "recipients": [
    {
      "id": "abc123",
      "email": "user@example.com",
      "status": "active",
      "added_date": "2025-08-21T10:00:00",
      "last_modified": "2025-08-21T10:00:00"
    }
  ],
  "stats": {
    "total": 3,
    "active": 3,
    "inactive": 0
  }
}
```

### KeywordManager API

```python
# 키워드 관리자 초기화
manager = KeywordManager()

# 주제 추가
manager.add_topic("신기술", ["블록체인", "IoT"], weight=25)

# 키워드 수정
manager.update_keywords("IT", ["클라우드", "AI", "빅데이터"])

# 설정 저장
manager.save_config()
```

### NewsSummarizer API

```python
# 요약기 초기화
summarizer = NewsSummarizer()

# 개별 기사 요약
summary = summarizer.summarize_news(news_data, max_length=200)

# 주제별 종합 요약
topic_summary = summarizer.summarize_topic_news(news_list, topic_name)

# PICK 요약 생성
pick_summary = summarizer.generate_pick_summary(topic_summary, topic_name)
```

## 🔧 문제 해결

### 일반적인 문제

#### 1. ChromeDriver 오류
```bash
# 해결방법 1: 자동 설치 확인
python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"

# 해결방법 2: Chrome 버전 확인
chrome://version/

# 해결방법 3: 수동 설치
# https://chromedriver.chromium.org/downloads
```

#### 2. 이메일 발송 실패
```yaml
Microsoft Outlook:
  - 계정 활성 상태 확인
  - SMTP 설정: smtp-mail.outlook.com:587
  - 방화벽/보안 소프트웨어 확인

Gmail:
  - 2단계 인증 활성화 필요
  - 앱 비밀번호 생성 필요
  - Less secure app access 해제
```

#### 3. OpenAI API 오류
```python
# API 키 검증
import openai
openai.api_key = "your_key_here"
# 잔액 및 사용량 확인: https://platform.openai.com/usage

# 모델 사용 가능 여부 확인
models = openai.Model.list()
print([m.id for m in models.data if 'gpt-4' in m.id])
```

#### 4. 한글 인코딩 문제 (Windows)
```python
# Windows 콘솔 설정
import os
os.system('chcp 65001')  # UTF-8로 변경

# 환경변수 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

#### 5. 수신자 관리 관련 문제

**수신자가 추가되지 않는 경우:**
```python
# 이메일 형식 검증
import re
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
is_valid = re.match(email_pattern, "user@example.com")

# 중복 확인
from recipient_manager import SimpleRecipientManager
manager = SimpleRecipientManager()
existing_emails = [r['email'] for r in manager.get_all_recipients()]
```

**대량 추가 시 오류가 발생하는 경우:**
```python
# 텍스트 형식 확인
emails_text = """
user1@example.com
user2@example.com
user3@example.com
"""
# 쉼표, 세미콜론, 줄바꿈 모두 지원
```

**웹 페이지가 로드되지 않는 경우:**
```bash
# Flask 서버 상태 확인
curl http://localhost:5000/api/status

# 포트 충돌 확인
netstat -ano | findstr :5000

# 다른 포트로 실행
python web_app.py --port 5001
```

**JSON 파일 손상 시 복구:**
```python
# 백업 파일에서 복원
from recipient_manager import SimpleRecipientManager
manager = SimpleRecipientManager()
manager.restore_from_backup("recipients_backup.json")

# 수동 복구
import json
with open("recipients.json", "w", encoding="utf-8") as f:
    json.dump([], f, ensure_ascii=False, indent=2)
```

### 로그 분석

#### 로그 파일 위치 및 용도
```bash
# 실시간 로그 모니터링
tail -f logs/newsletter.log          # 메인 시스템
tail -f logs/web_newsletter.log      # 웹 인터페이스
tail -f logs/news_collector.log      # 뉴스 수집
tail -f logs/working_news_collector.log # 개선된 수집기

# Windows에서
Get-Content logs\newsletter.log -Wait -Tail 20
```

#### 주요 에러 패턴
```yaml
"ChromeDriver 오류": 
  - 로그: "WebDriverException"
  - 해결: Chrome/ChromeDriver 버전 동기화

"OpenAI API 제한":
  - 로그: "Rate limit exceeded"
  - 해결: 요청 간격 조정, API 플랜 확인

"이메일 인증 실패":
  - 로그: "SMTPAuthenticationError"  
  - 해결: 비밀번호 확인, 보안 설정 점검

"네이버 뉴스 접근 제한":
  - 로그: "HTTP 429 Too Many Requests"
  - 해결: 요청 간격 확장, IP 변경
```

### 성능 문제 해결

#### 메모리 사용량 최적화
```python
# 뉴스 수집 후 즉시 정리
collector.cleanup()

# Selenium WebDriver 세션 관리
driver.quit()  # 브라우저 완전 종료

# 대용량 뉴스 데이터 스트리밍 처리
def process_news_stream(news_list):
    for news in news_list:
        yield process_single_news(news)
        del news  # 즉시 메모리 해제
```

#### 응답 시간 최적화
```python
# 병렬 처리
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(collect_topic_news, topic) 
               for topic in topics]
    results = [future.result() for future in futures]
```

## ⚡ 성능 최적화

### 뉴스 수집 최적화

#### 요청 최적화
```python
# 요청 간격 동적 조정
class AdaptiveRateLimit:
    def __init__(self, base_delay=5):
        self.base_delay = base_delay
        self.current_delay = base_delay
    
    def adjust_delay(self, success_rate):
        if success_rate > 0.9:
            self.current_delay = max(1, self.current_delay * 0.8)
        else:
            self.current_delay = min(30, self.current_delay * 1.5)
```

#### 캐싱 전략
```python
# Redis 기반 뉴스 캐싱
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

def cached_news_search(keyword, ttl=3600):
    cache_key = f"news:{keyword}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return json.loads(cached_result)
    
    fresh_result = search_news(keyword)
    cache.setex(cache_key, ttl, json.dumps(fresh_result))
    return fresh_result
```

### AI 요약 최적화

#### 배치 처리
```python
# 여러 기사를 한 번에 요약
def batch_summarize(articles, batch_size=5):
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        prompt = create_batch_prompt(batch)
        summaries = call_openai_api(prompt)
        yield parse_batch_summaries(summaries)
```

#### 토큰 사용량 최적화
```python
# 토큰 수 예측 및 제한
def estimate_tokens(text):
    return len(text) // 4  # 대략적인 토큰 수 추정

def optimize_prompt(article, max_tokens=400):
    estimated = estimate_tokens(article['content'])
    if estimated > max_tokens:
        article['content'] = article['content'][:max_tokens*4]
    return article
```

### 시스템 모니터링

#### 성능 메트릭
```python
import time
import psutil
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        logger.info(f"{func.__name__} - "
                   f"Time: {end_time - start_time:.2f}s, "
                   f"Memory: {(end_memory - start_memory)/1024/1024:.2f}MB")
        
        return result
    return wrapper
```

#### 시스템 상태 대시보드
```python
# 웹 인터페이스에서 실시간 모니터링
@app.route('/api/system/status')
def system_status():
    return {
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'active_processes': len([p for p in psutil.process_iter() 
                               if 'python' in p.name()]),
        'last_newsletter': get_last_newsletter_time(),
        'error_count': get_recent_error_count()
    }
```

## 🔒 보안 및 규정 준수

### 데이터 보호
- **환경변수 암호화**: 민감정보는 `.env` 파일로 분리
- **API 키 마스킹**: 로그에서 자동으로 민감정보 제거
- **접근 제어**: 웹 인터페이스 IP 화이트리스트 지원
- **데이터 보관**: 뉴스 데이터는 24시간 후 자동 삭제

### 컴플라이언스
- **저작권 준수**: 뉴스 요약만 제공, 원문 링크 필수 포함
- **개인정보 보호**: 이메일 주소 암호화 저장
- **감사 로그**: 모든 시스템 활동 상세 기록

## 📈 확장 및 커스터마이징

### 새로운 뉴스 소스 추가
```python
class CustomNewsCollector:
    def search_news(self, keyword, limit=10):
        # 커스텀 뉴스 소스 구현
        pass
    
    def integrate_with_system(self):
        # 기존 시스템과 통합
        pass
```

### AI 모델 변경
```python
# GPT-4로 업그레이드
OPENAI_MODEL = "gpt-4"  # .env 파일에 추가

# 로컬 모델 사용 (예: Ollama)
class LocalSummarizer:
    def __init__(self, model_name="llama2"):
        self.model = load_local_model(model_name)
```

### 다국어 지원
```python
# 언어별 키워드 설정
LANGUAGE_CONFIG = {
    'ko': {'keywords': ['AI', '인공지능'], 'model': 'gpt-4'},
    'en': {'keywords': ['AI', 'artificial intelligence'], 'model': 'gpt-4'},
    'ja': {'keywords': ['AI', '人工知能'], 'model': 'gpt-4'}
}
```

## 📞 지원 및 기여

### 지원 채널
- **이슈 트래킹**: GitHub Issues
- **문서**: 이 README와 코드 주석
- **로그 분석**: `logs/` 디렉토리의 상세 로그

### 기여 가이드
1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

### 개발 환경 설정
```bash
# 개발용 의존성 추가 설치
pip install -r requirements-dev.txt

# 코드 품질 검사
flake8 .
black .
pytest tests/
```

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

**버전**: 2.1.0  
**최종 업데이트**: 2025년 8월 13일  
**담당자**: 하나투어 IT본부

*이 시스템은 하나투어 내부 사용을 위해 특별히 최적화되었습니다.*