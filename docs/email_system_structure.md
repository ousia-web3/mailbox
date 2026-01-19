# 이메일 발송 템플릿 및 수신자 관리 구조 정리

이 문서는 이메일 발송 시스템의 핵심 로직, 템플릿 생성, 수신자 관리와 관련된 주요 파일 및 코드 위치를 정리한 것입니다.

## 1. 이메일 발송 로직 (`email_sender.py`)

이메일 서버 설정, HTML 변환, 실제 발송을 담당하는 핵심 파일입니다.

| 기능            | 라인  | 설명                                                                    |
| :-------------- | :---- | :---------------------------------------------------------------------- |
| **클래스 정의** | `11`  | `EmailSender` 클래스 시작                                               |
| **설정 로드**   | `22`  | `setup_email_config`: SMTP 서버 및 계정 정보 설정                       |
| **발송 로직**   | `116` | `send_newsletter`: 수신자 목록을 순회하며 이메일 발송                   |
| **HTML 변환**   | `283` | `convert_to_html`: 마크다운 본문을 이메일용 HTML로 변환 (스타일링 포함) |
| **수신자 갱신** | `257` | `refresh_recipients`: 수신자 관리자로부터 최신 목록 동기화              |

### SMTP 포트 및 서버 설정

`setup_email_config` 메서드(라인 22) 내에서 발신자 이메일 도메인을 확인하여 자동으로 설정합니다.

- **Outlook / Hotmail / Hanatour**:
  - 서버: `smtp-mail.outlook.com`
  - 포트: `587`
  - 보안: STARTTLS
- **Gmail 및 기타**:
  - 서버: `smtp.gmail.com`
  - 포트: `587`

**관련 코드 (`email_sender.py` 66-74라인):**

```python
# Microsoft 계정인지 확인
if '@outlook.com' in self.sender_email or '@hotmail.com' in self.sender_email or '@hanatour.com' in self.sender_email:
    self.smtp_server = 'smtp-mail.outlook.com'
    self.smtp_port = 587
    self.logger.info("Microsoft 계정 SMTP 설정 사용")
else:
    # 기본값 (Gmail)
    self.smtp_server = 'smtp.gmail.com'
    self.smtp_port = 587
    self.logger.info("Gmail SMTP 설정 사용")
```

## 2. 수신자 관리 (`recipient_manager.py`)

수신자 목록을 `recipients.json` 파일에 저장하고 관리하는 로직입니다.

| 기능            | 라인  | 설명                                                                    |
| :-------------- | :---- | :---------------------------------------------------------------------- |
| **클래스 정의** | `11`  | `SimpleRecipientManager` 클래스 시작                                    |
| **데이터 로드** | `35`  | `load_recipients`: JSON 파일에서 수신자 목록 읽기                       |
| **데이터 저장** | `50`  | `save_recipients`: 변경된 목록을 JSON 파일에 저장                       |
| **추가 (단일)** | `60`  | `add_recipient`: 이메일 유효성 검사 후 추가                             |
| **추가 (대량)** | `85`  | `add_multiple_recipients`: 텍스트(Ctrl+V)에서 이메일 추출하여 일괄 추가 |
| **삭제**        | `120` | `remove_recipient`: 특정 이메일 삭제                                    |
| **가져오기**    | `201` | `import_from_env`: 기존 `.env` 파일 형식에서 데이터 가져오기            |

## 3. 뉴스레터 템플릿 생성

뉴스레터의 HTML 구조와 디자인을 생성하는 부분입니다. 별도의 HTML 파일이 아닌 파이썬 코드 내에서 동적으로 생성됩니다.

### 주간 뉴스레터 (`weekly_generator.py`)

- **`116` 라인 (`generate_html_template`)**: 주간 뉴스레터의 HTML 구조, CSS 스타일, 본문 구성을 정의합니다.

### 월간 뉴스레터 (`monthly_generator.py`)

- **`115` 라인 (`generate_html_template`)**: 월간 트렌드 리포트 및 베스트 뉴스를 포함한 HTML 템플릿을 생성합니다.

## 4. 웹 관리자 기능 (`web_app.py`)

웹 인터페이스를 통해 수신자를 관리하는 API 및 라우트입니다.

| 기능              | 라인  | 설명                                                          |
| :---------------- | :---- | :------------------------------------------------------------ |
| **목록 조회 API** | `415` | `get_recipients`: 수신자 목록 JSON 반환                       |
| **추가 API**      | `440` | `add_recipient`: 웹에서 입력받은 수신자 추가                  |
| **삭제 API**      | `488` | `remove_recipient`: 웹에서 요청한 수신자 삭제                 |
| **페이지 라우트** | `566` | `recipients_page`: 수신자 관리 화면(`recipients.html`) 렌더링 |

## 5. 데이터 저장소

- **`recipients.json`**: 수신자 이메일, 등록일, 상태(활성/비활성) 등의 데이터가 저장되는 파일입니다.
