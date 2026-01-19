# 뉴스레터 생성 및 발송(운영계) 메일 제목 변경 작업 플랜

## 1. 개요

운영계 뉴스레터 발송 시 사용되는 이메일 제목을 사용자의 요청에 맞춰 변경합니다.

## 2. 변경 대상

- **파일**: `newsletter_system.py`
- **메서드**: `generate_newsletter` (운영계 뉴스레터 생성 및 발송 메서드)

## 3. 변경 내용

### 변경 전

```python
subject = f"{os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')} - {datetime.now().strftime('%Y년 %m월 %d일')}"
```

### 변경 후

```python
subject = f"[Daily] {os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')}"
```

## 4. 검증 계획

- 코드 수정 후 `generate_newsletter` 메서드가 포함된 파일을 확인하여 변경 사항이 올바르게 적용되었는지 검증합니다.
- 실제 발송 시 제목에 날짜가 제외되고 `[Daily]` 접두어가 붙는지 확인이 필요합니다.
