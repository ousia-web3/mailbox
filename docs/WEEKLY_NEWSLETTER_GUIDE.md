# 주간 뉴스레터 실행 가이드

## 📅 실행 시점

**매주 월요일** (지난주 월~일 데이터 기반)

## 🚀 실행 방법

### 방법 1: 배치 파일 실행 (권장)

```
run_weekly_newsletter.bat 더블클릭
```

### 방법 2: Python 직접 실행

```bash
python weekly_generator.py
```

## 📋 실행 프로세스

1. **데이터 로드**
   - 최근 5일간의 일일 뉴스 데이터 수집
   - `archives/daily/{년}/{월}/daily_news_{날짜}.json` 파일 읽기

2. **AI 큐레이션**
   - Gemini API를 사용하여 Top 10 뉴스 선정
   - Weekly Insight 생성 (핵심 트렌드 분석)

3. **HTML 생성**
   - `templates/weekly_newsletter.html` 템플릿 사용
   - Top 10 뉴스 + In Other News 섹션 생성
   - 관련 기사 뱃지 링크 추가

4. **메일 발송**
   - 제목: `[IT본부] 하나투어 주간 뉴스레터 ({날짜})`
   - 수신자: `recipients.json`에 등록된 활성 수신자

5. **아카이빙**
   - 생성된 HTML 파일 저장
   - 위치: `archives/weekly/{년}/weekly_newsletter_{날짜}.html`

## ✅ 주요 기능

### Top 10 Insights

- AI가 선정한 주간 핵심 뉴스 10개
- 각 뉴스마다 요약 및 인사이트 제공
- **관련 기사** 뱃지 클릭 시 In Other News로 이동

### Weekly Focus Analysis

- 주간 핵심 트렌드 분석
- 제목 + 300자 내외 인사이트

### In Other News

- Top 10과 동일한 뉴스 목록
- 앵커 링크로 Top 10과 연동

## 🎨 디자인 특징

- **관련 기사 뱃지**: 보라색 배경(#5e2bb8), 흰색 텍스트
- **번호 형식**: 01, 02, ... 10 (2자리)
- **템플릿**: `weekly_insight_top10_snippet.html` 가이드 준수

## 📁 관련 파일

### 핵심 파일

- `weekly_generator.py` - 주간 뉴스레터 생성 로직
- `news_summarizer_v2.py` - Gemini API 기반 AI 큐레이션
- `templates/weekly_newsletter.html` - HTML 템플릿
- `prompts/weekly_curation_prompt.md` - AI 프롬프트

### 실행 파일

- `run_weekly_newsletter.bat` - 배치 실행 파일

### 결과 파일

- `archives/weekly/{년}/weekly_newsletter_{날짜}.html`

## ⚙️ 설정

### 환경 변수 (.env)

```
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash-preview-09-2025
```

### 데이터 수집 범위

- 기본: 최근 5일 (오늘 포함)
- 수정: `weekly_generator.py` line 25-26

## 🔧 문제 해결

### 데이터가 없는 경우

- 일일 뉴스레터가 정상적으로 실행되었는지 확인
- `archives/daily/` 폴더에 JSON 파일 존재 확인

### AI 큐레이션 실패

- Gemini API 키 확인
- 네트워크 연결 확인
- 로그 파일 확인

### HTML 생성 실패

- 템플릿 파일 존재 확인
- 템플릿 구조 확인

## 📝 참고 문서

- `docs/weekly_newsletter_process.md` - 상세 프로세스
- `docs/TASK_WEEKLY_MONTHLY_NEWSLETTER.md` - 프로젝트 개요
- `rules/CHANGELOG.md` - 변경 이력
