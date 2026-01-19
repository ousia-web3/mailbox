# 테스트 메일 발송 메일 제목 변경 작업 플랜

## 1. 개요

테스트 메일 발송 시 사용되는 이메일 제목을 사용자의 요청에 맞춰 변경합니다.

## 2. 변경 대상

- **파일**: `newsletter_system.py`
- **메서드**: `run_test` (시스템 테스트 실행 메서드)

## 3. 변경 내용

### 변경 전

```python
subject = f"[TEST] {os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')} - V3 템플릿 테스트"
```

### 변경 후

```python
subject = f"[테스트발송] {os.getenv('NEWSLETTER_TITLE', '[IT본부] 하나투어 뉴스레터')}"
```

## 4. 검증 계획

- 코드 수정 후 `run_test` 메서드가 포함된 파일을 확인하여 변경 사항이 올바르게 적용되었는지 검증합니다.
- (참고) `newsletter_system.py` 내에 `run_test` 메서드가 중복 정의되어 있어, 실제 실행되는 후반부 정의(약 1332라인)를 수정합니다.
