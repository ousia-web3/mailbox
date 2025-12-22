# 뉴스레터 발송 프로세스 상세 가이드

이 문서는 하나투어 뉴스레터 시스템의 데일리, 주간, 월간 발송 프로세스의 상세 흐름을 설명합니다.

## 📂 실행 파일 및 프로젝트 구조

```text
mailbox/
├── main.py                     # [메인] 스케줄러 실행 파일 (데일리/주간/월간 통합 제어)
├── newsletter_system.py        # [데일리] 뉴스레터 생성 및 발송 시스템
├── weekly_generator.py         # [주간] 주간 뉴스레터 생성기
├── monthly_generator.py        # [월간] 월간 뉴스레터 생성기
├── news_collector_working.py   # [공통] 뉴스 수집 모듈
├── news_summarizer.py          # [공통] AI 요약 및 큐레이션 모듈
├── email_sender.py             # [공통] 이메일 발송 모듈
├── archiver.py                 # [공통] 아카이빙 모듈
├── date_utils.py               # [유틸] 날짜 계산 유틸리티
├── run_newsletter.bat          # [실행] 윈도우 배치 실행 스크립트
└── archives/                   # [데이터] 아카이브 저장소
    ├── daily/                  # 데일리 뉴스 (JSON/HTML)
    ├── weekly/                 # 주간 뉴스레터 (HTML)
    └── monthly/                # 월간 뉴스레터 (HTML)
```

---

## 1. 데일리 뉴스레터 (Daily Newsletter)

**목적**: 매일 발생하는 최신 IT, AI, 여행 관련 뉴스를 신속하게 수집하고 요약하여 전달합니다.  
**실행 주기**: 담당자가 지정한 시간 (Windows 작업 스케줄러 기준)
**실행 파일**: `newsletter_system.py` (직접 실행 시) 또는 `run_newsletter.bat`

### 🔄 프로세스 흐름

1.  **뉴스 수집 (Collection)**
    - **담당**: `WorkingNewsCollector`
    - **동작**: 네이버 뉴스 API/크롤링을 통해 설정된 키워드(IT, AI, 여행 등)에 대한 최신 뉴스를 검색합니다.
    - **필터링**: 제목 기준 중복 제거, 관련성 낮은 기사 제외, 최신순 정렬.
2.  **AI 요약 (Summarization)**

    - **담당**: `NewsSummarizer` (GPT-4o-mini)
    - **동작**:
      - 개별 기사 3줄 요약.
      - 주제별(IT/AI/여행) 종합 요약 생성.
      - 핵심 내용을 짚어주는 'PICK' 요약 생성.

3.  **콘텐츠 생성 및 발송 (Generation & Sending)**

    - **담당**: `NewsletterSystem`, `EmailSender`
    - **동작**: 수집/요약된 데이터를 HTML 템플릿에 매핑하여 이메일을 발송합니다.
    - **제목**: `[IT본부] 하나투어 뉴스레터`

4.  **아카이빙 (Archiving)**
    - **담당**: `Archiver`
    - **저장 위치**:
      - 데이터: `archives/daily/{YYYY}/{MM}/daily_news_{YYYYMMDD}.json` (주간/월간 생성의 원천 데이터)
      - 화면: `archives/daily/{YYYY}/{MM}/daily_newsletter_{YYYYMMDD}.html`

---

## 2. 주간 뉴스레터 (Weekly Newsletter)

**목적**: 지난 한 주간 축적된 데일리 뉴스를 기반으로, AI가 중요 뉴스를 선별(Curation)하고 주간 인사이트를 제공합니다.  
**실행 주기**: 매주 월요일 09:00
**실행 파일**: `main.py` (통합 스케줄러) 또는 `run_scheduler.bat`

### 🔄 프로세스 흐름

1.  **데이터 로드 (Data Loading)**

    - **담당**: `WeeklyNewsletterGenerator`
    - **동작**: 지난주 월요일 ~ 일요일(7일간)에 생성된 **데일리 JSON 아카이브** 파일들을 모두 읽어옵니다.

2.  **AI 큐레이션 & 인사이트 (Curation & Insight)**

    - **담당**: `NewsSummarizer`
    - **동작**:
      - **Top 5 선정**: 단순 나열이 아닌, AI가 중요도/파급력을 판단하여 주제별 상위 5개 뉴스를 선정합니다.
      - **Weekly Insight**: 선정된 뉴스를 바탕으로 한 주간의 기술/업계 흐름을 요약한 인사이트 리포트를 작성합니다.

3.  **발송 (Sending)**

    - **담당**: `EmailSender`
    - **제목**: `[IT본부] 하나투어 주간 뉴스레터` (고정 제목)

4.  **아카이빙 (Archiving)**
    - **저장 위치**: `archives/weekly/{YYYY}/weekly_newsletter_{YYYYMMDD}.html`
    - **예시**: `archives/weekly/2025/weekly_newsletter_20251222.html`

---

## 3. 월간 뉴스레터 (Monthly Newsletter)

**목적**: 한 달간의 데이터를 종합 분석하여 거시적인 트렌드 리포트와 Best 뉴스를 전달합니다.  
**실행 주기**: 매월 첫 영업일 09:00 (예: 1일이 주말이면 월요일 발송)
**실행 파일**: `main.py` (통합 스케줄러) 또는 `run_scheduler.bat`

### 🔄 프로세스 흐름

1.  **데이터 로드 (Data Loading)**

    - **담당**: `MonthlyNewsletterGenerator`
    - **동작**: 지난달 1일 ~ 말일까지의 모든 **데일리 JSON 아카이브**를 로드합니다.

2.  **트렌드 분석 & Best 선정 (Analysis)**

    - **담당**: `NewsSummarizer`
    - **동작**:
      - **Monthly Trend Report**: '이달의 핵심 이슈', '기술 트렌드 변화', '여행 산업 동향', 'Next Month 전망' 4가지 관점의 심층 보고서를 생성합니다.
      - **Best of Best**: 한 달 전체 뉴스 중 가장 영향력 있었던 3~5개의 뉴스를 엄선합니다.

3.  **발송 (Sending)**

    - **담당**: `EmailSender`
    - **제목**: `[IT본부] 하나투어 월간 뉴스레터 ({N}월)`

4.  **아카이빙 (Archiving)**
    - **저장 위치**: `archives/monthly/{YYYY}/monthly_newsletter_{YYYYMM}.html`
    - **예시**: `archives/monthly/2025/monthly_newsletter_202512.html`
