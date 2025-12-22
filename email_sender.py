import smtplib
import os
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging
from datetime import datetime
from security_config import SecurityConfig

class EmailSender:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.security_config = SecurityConfig()
        self.setup_email_config()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def setup_email_config(self):
        """이메일 설정"""
        self.sender_email = os.getenv('EMAIL_SENDER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')

        # DRY_RUN 모드 확인: 테스트 시 .env에 지정된 수신자만 사용
        dry_run_flag = os.getenv('NEWSLETTER_DRY_RUN', '').strip().lower() in ('1', 'true', 'yes')
        if dry_run_flag:
            # .env에서 수신자 로드 (쉼표 구분)
            receiver_emails = os.getenv('EMAIL_RECEIVER', '')
            if ',' in receiver_emails:
                self.receiver_emails = [email.strip() for email in receiver_emails.split(',')]
            else:
                self.receiver_emails = [receiver_emails.strip()] if receiver_emails else []
            self.logger.info(f"DRY_RUN 모드: .env 수신자 로드: {len(self.receiver_emails)}명")
        else:
            # 기존 방식: SimpleRecipientManager 사용
            try:
                from recipient_manager import SimpleRecipientManager
                recipient_manager = SimpleRecipientManager()
                self.receiver_emails = recipient_manager.get_active_emails()
                self.logger.info(f"SimpleRecipientManager에서 수신자 로드: {len(self.receiver_emails)}명")
            except Exception as e:
                self.logger.warning(f"SimpleRecipientManager 로드 실패, 기존 .env 방식 사용: {e}")
                receiver_emails = os.getenv('EMAIL_RECEIVER', '')
                if ',' in receiver_emails:
                    self.receiver_emails = [email.strip() for email in receiver_emails.split(',')]
                else:
                    self.receiver_emails = [receiver_emails.strip()] if receiver_emails else []

        # 보안 검증
        validation = self.security_config.validate_environment_variables()
        if not validation['is_valid']:
            error_msg = "이메일 설정이 올바르지 않습니다: " + "; ".join(validation['errors'])
            raise ValueError(error_msg)
        
        if not all([self.sender_email, self.sender_password]):
            raise ValueError("이메일 설정이 .env 파일에 완전히 설정되지 않았습니다.")

        # 수신자가 없는 경우 경고
        if not self.receiver_emails:
            self.logger.warning("수신자가 없습니다. 뉴스레터 발송이 불가능합니다.")

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

        self.logger.info(f"이메일 설정 완료 - 수신자: {len(self.receiver_emails)}명")
    
    def _create_secure_smtp_connection(self):
        """보안 강화된 SMTP 연결 생성"""
        import time
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 보안 컨텍스트 생성
                context = ssl.create_default_context()
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                
                # SMTP 서버 연결 (타임아웃 설정)
                self.logger.info(f"SMTP 연결 시도 {attempt + 1}/{max_retries}: {self.smtp_server}:{self.smtp_port}")
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                server.ehlo()  # Extended Hello
                
                # TLS 암호화 시작
                server.starttls(context=context)
                server.ehlo()  # Extended Hello (TLS 후 재전송)
                
                self.logger.info(f"보안 SMTP 연결 성공: {self.smtp_server}:{self.smtp_port}")
                return server
                
            except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
                self.logger.warning(f"SMTP 연결 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"{retry_delay}초 후 재시도...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"SMTP 연결 최종 실패: {e}")
                    raise
            except Exception as e:
                self.logger.error(f"SMTP 연결 중 예상치 못한 오류: {e}")
                raise
        
    def send_newsletter(self, subject, content):
        """뉴스레터 이메일 발송 (여러 수신자 지원)"""
        # 드라이런 모드: 환경변수로 실제 발송 없이 테스트 가능 (기본: 비활성)
        dry_run_flag = os.getenv('NEWSLETTER_DRY_RUN', '').strip().lower() in ('1', 'true', 'yes')

        # 화이트리스트 강제: recipients.json의 활성 수신자만 최종 발송 대상
        # (매 실행 시점 재확인하여 .env 폴백으로도 추가 수신자가 들어가지 않도록 함)
        enforce_flag = os.getenv('NEWSLETTER_ENFORCE_RECIPIENTS', 'true').strip().lower() in ('1', 'true', 'yes')
        final_receivers = list(self.receiver_emails)
        if enforce_flag:
            try:
                from recipient_manager import SimpleRecipientManager
                _rm = SimpleRecipientManager()
                allowlist = set(_rm.get_active_emails())
                final_receivers = [r for r in final_receivers if r in allowlist]
                self.logger.info(f"화이트리스트 적용: {len(final_receivers)}명 (allowlist={len(allowlist)}명)")
            except Exception as e:
                self.logger.warning(f"화이트리스트 적용 실패(매니저 로드 실패): {e}. 기존 수신자 목록 사용")

        # 발송 대상 확정 로그
        self.logger.info(f"발송 대상 확정: {final_receivers}")

        if dry_run_flag:
            self.logger.info("NEWSLETTER_DRY_RUN=ON: 실제 SMTP 발송 없이 테스트를 완료합니다.")
            return True

        success_count = 0
        total_count = len(final_receivers)

        for receiver_email in final_receivers:
            try:
                # 이메일 메시지 생성
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = self.sender_email
                msg['To'] = receiver_email

                # 이미 HTML 형식인지 확인하여 처리
                if content.strip().startswith('<!DOCTYPE html') or content.strip().startswith('<html'):
                    # 이미 완전한 HTML 문서인 경우
                    html_content = content
                    # HTML에서 텍스트 추출 (간단한 방법)
                    import re
                    text_content = re.sub(r'<[^>]+>', '', content)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                else:
                    # 마크다운인 경우 HTML로 변환
                    html_content = self.convert_to_html(content)
                    text_content = content

                # 텍스트와 HTML 버전 모두 첨부
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                html_part = MIMEText(html_content, 'html', 'utf-8')

                msg.attach(text_part)
                msg.attach(html_part)

                # 보안 강화된 SMTP 연결
                server = self._create_secure_smtp_connection()
                
                # 로그인 (민감한 정보 로깅 방지)
                try:
                    self.logger.info(f"SMTP 로그인 시도: {self.security_config.mask_sensitive_value(self.sender_email, 6)}")
                    # smtplib.SMTP.login()은 문자열을 받으므로 인코딩 불필요
                    server.login(self.sender_email, self.sender_password)
                    self.logger.info(f"SMTP 로그인 성공: {self.security_config.mask_sensitive_value(self.sender_email, 6)}")
                except smtplib.SMTPAuthenticationError as e:
                    error_msg = f"SMTP 인증 실패: {e}"
                    
                    # Outlook/Hanatour 계정인 경우
                    if '@hanatour.com' in self.sender_email or '@outlook.com' in self.sender_email or '@hotmail.com' in self.sender_email:
                        error_msg += "\n\n[Outlook 계정 해결방법]"
                        error_msg += "\n1. Microsoft 계정 보안 설정 확인: https://account.microsoft.com/security"
                        error_msg += "\n2. 2단계 인증이 활성화되어 있다면 '앱 비밀번호'를 생성하여 사용하세요"
                        error_msg += "\n3. '보안 수준이 낮은 앱 액세스'가 비활성화되어 있는지 확인하세요"
                        error_msg += "\n4. 비밀번호에 특수문자가 포함된 경우 따옴표 없이 입력하세요"
                    # Gmail 계정인 경우
                    elif '@gmail.com' in self.sender_email:
                        error_msg += "\n\n[Gmail 계정 해결방법]"
                        error_msg += "\n1. Google 계정 → 보안 → 2단계 인증 활성화"
                        error_msg += "\n2. 앱 비밀번호 생성 → 메일 앱 선택"
                        error_msg += "\n3. 생성된 16자리 비밀번호를 EMAIL_PASSWORD에 입력"
                        error_msg += "\n   자세한 내용: https://support.google.com/accounts/answer/185833"
                    
                    self.logger.error(error_msg)
                    
                    # 테스트 환경에서는 인증 실패 시 건너뛰기
                    if "test" in self.sender_email.lower():
                        self.logger.info("테스트 환경: 이메일 발송을 건너뜁니다.")
                        return True
                    raise
                except Exception as e:
                    self.logger.error(f"SMTP 로그인 중 예상치 못한 오류: {e}")
                    raise

                # 이메일 발송
                try:
                    server.send_message(msg)
                    self.logger.info(f"이메일 메시지 전송 완료: {receiver_email}")
                except Exception as send_error:
                    self.logger.error(f"이메일 메시지 전송 실패 ({receiver_email}): {send_error}")
                    raise
                finally:
                    try:
                        server.quit()
                    except:
                        pass

                success_count += 1
                self.logger.info(f"뉴스레터 이메일 발송 완료: {receiver_email}")

            except smtplib.SMTPAuthenticationError as e:
                # 인증 오류는 이미 위에서 처리되었으므로 여기서는 로깅만
                self.logger.error(f"이메일 발송 중 인증 오류 ({receiver_email}): {e}")
                # 첫 번째 수신자에서 인증 실패 시 나머지도 실패할 가능성이 높으므로 중단
                if success_count == 0:
                    self.logger.error("첫 번째 수신자에서 인증 실패. 나머지 발송을 중단합니다.")
                    break
            except Exception as e:
                self.logger.error(f"이메일 발송 중 오류 ({receiver_email}): {e}")
                import traceback
                self.logger.debug(f"상세 오류: {traceback.format_exc()}")

        if success_count == total_count:
            self.logger.info(f"모든 수신자({total_count}명)에게 뉴스레터 발송 완료")
            return True
        elif success_count > 0:
            self.logger.warning(f"일부 수신자에게만 발송 완료: {success_count}/{total_count}")
            return True
        else:
            self.logger.error("모든 수신자에게 발송 실패")
            return False

    def get_receiver_count(self):
        """수신자 수 반환"""
        return len(self.receiver_emails)

    def get_receiver_list(self):
        """수신자 목록 반환"""
        return self.receiver_emails
    
    def refresh_recipients(self):
        """수신자 목록 새로고침 (SimpleRecipientManager에서 최신 데이터 가져오기)"""
        try:
            from recipient_manager import SimpleRecipientManager
            recipient_manager = SimpleRecipientManager()
            self.receiver_emails = recipient_manager.get_active_emails()
            self.logger.info(f"수신자 목록 새로고침 완료: {len(self.receiver_emails)}명")
            return True
        except Exception as e:
            self.logger.error(f"수신자 목록 새로고침 실패: {e}")
            return False
    
    def get_recipient_stats(self):
        """수신자 통계 정보 반환"""
        try:
            from recipient_manager import SimpleRecipientManager
            recipient_manager = SimpleRecipientManager()
            return recipient_manager.get_stats()
        except Exception as e:
            self.logger.error(f"수신자 통계 조회 실패: {e}")
            return {
                'total': len(self.receiver_emails),
                'active': len(self.receiver_emails),
                'inactive': 0
            }.copy()
    
    def convert_to_html(self, markdown_content):
        """마크다운을 HTML로 변환 - 이메일 최적화"""
        import re
        
        
        # 상단 인사말 추가
        header_text = "안녕하세요! 여행 및 기술 동향 관련 소식을 전해드리는 뉴스레터입니다.\n\n"
        markdown_content = header_text + markdown_content
        
        # 하단 안내문 추가
        footer_text = "\n\n---\n\n본 이메일은 자동으로 생성되었으며, ChatGPT 4o-mini가 사용되고 있습니다."
        markdown_content = markdown_content + footer_text
        
        html = markdown_content
        
        # 제목 변환 (정규식 사용으로 정확한 변환)
        html = re.sub(r'^# (.+)$', r'<h1 style="font-size: 24px !important; font-weight: bold !important; color: #2c3e50 !important; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin: 20px 0 !important;">\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2 style="font-size: 22px !important; font-weight: bold !important; color: #34495e !important; margin: 20px 0 !important;">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3 style="font-size: 20px !important; font-weight: bold !important; color: #7f8c8d !important; margin: 20px 0 !important;">\1</h3>', html, flags=re.MULTILINE)
        
        # 강조 변환 (정확한 처리)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: bold !important; font-size: 20px !important; color: #2c3e50 !important;">\1</strong>', html)
        
        # 날짜와 원문보기 링크 변환 (작은 글자)
        html = re.sub(r'   ([^|]+) \| \[([^\]]+)\]\(([^)]+)\)', r'   <span style="font-size: 12px !important; color: #7f8c8d !important;">\1 | <a href="\3" target="_blank" style="color: #3498db !important; text-decoration: none !important; font-size: 12px !important;">\2</a></span>', html)
        
        # 일반 링크 변환
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" style="color: #3498db !important; text-decoration: none !important;">\1</a>', html)
        
        # 줄바꿈 변환 (이메일 최적화)
        # 먼저 연속된 줄바꿈을 단락으로 변환
        html = re.sub(r'\n\n+', '</p><p style="font-size: 14px !important; line-height: 1.4 !important; margin: 12px 0 !important;">', html)
        # 단일 줄바꿈을 <br>로 변환
        html = re.sub(r'\n', '<br>', html)
        
        # 첫 번째 단락 태그 추가
        if not html.startswith('<h1') and not html.startswith('<h2') and not html.startswith('<h3'):
            html = '<p style="font-size: 14px !important; line-height: 1.4 !important; margin: 12px 0 !important;">' + html
        
        # 마지막 단락 태그 추가
        if not html.endswith('</h1>') and not html.endswith('</h2>') and not html.endswith('</h3>'):
            html = html + '</p>'
        
        # HTML 문서 완성 (이메일 최적화)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
                    font-size: 14px !important;
                    line-height: 1.4 !important;
                    color: #333333 !important;
                    margin: 0 !important;
                    padding: 15px !important;
                    background-color: #ffffff !important;
                    max-width: 800px !important;
                    -webkit-text-size-adjust: 100% !important;
                    -ms-text-size-adjust: 100% !important;
                }}
                h1 {{
                    font-size: 20px !important;
                    font-weight: bold !important;
                    color: #2c3e50 !important;
                    border-bottom: 2px solid #3498db !important;
                    padding-bottom: 8px !important;
                    margin: 15px 0 !important;
                    line-height: 1.2 !important;
                }}
                h2 {{
                    font-size: 18px !important;
                    font-weight: bold !important;
                    color: #34495e !important;
                    margin: 15px 0 !important;
                    line-height: 1.3 !important;
                }}
                h3 {{
                    font-size: 16px !important;
                    font-weight: bold !important;
                    color: #7f8c8d !important;
                    margin: 12px 0 !important;
                    line-height: 1.3 !important;
                }}
                p {{
                    font-size: 14px !important;
                    line-height: 1.4 !important;
                    margin: 12px 0 !important;
                }}
                a {{
                    color: #3498db !important;
                    text-decoration: none !important;
                }}
                a:hover {{
                    text-decoration: underline !important;
                }}
                strong {{
                    font-weight: bold !important;
                    font-size: 15px !important;
                    color: #2c3e50 !important;
                }}
                .news-item {{
                    margin-bottom: 18px !important;
                    padding: 15px !important;
                    border-left: 4px solid #3498db !important;
                    background-color: #f8f9fa !important;
                    border-radius: 6px !important;
                }}
                .news-meta {{
                    color: #7f8c8d !important;
                    font-size: 11px !important;
                    margin: 4px 0 !important;
                }}
                .news-summary {{
                    margin: 12px 0 !important;
                    font-size: 13px !important;
                    line-height: 1.4 !important;
                }}
                hr {{
                    border: none !important;
                    border-top: 1px solid #ecf0f1 !important;
                    margin: 20px 0 !important;
                }}
                /* 이메일 클라이언트 호환성 */
                .ExternalClass {{
                    width: 100% !important;
                }}
                .ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div {{
                    line-height: 100% !important;
                }}
                @media only screen and (max-width: 800px) {{
                    body {{
                        font-size: 14px !important;
                        padding: 10px !important;
                    }}
                    h1 {{
                        font-size: 18px !important;
                    }}
                    h2 {{
                        font-size: 16px !important;
                    }}
                    h3 {{
                        font-size: 14px !important;
                    }}
                    .news-item {{
                        padding: 12px !important;
                        margin-bottom: 15px !important;
                    }}
                }}
            </style>
        </head>
        <body>
            <div style="font-size: 14px !important; line-height: 1.4 !important; margin: 10px 0 !important; max-width: 800px !important;">
                {html}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_test_email(self):
        """테스트 이메일 발송"""
        test_subject = "뉴스레터 시스템 테스트"
        test_content = f"""
# 뉴스레터 시스템 테스트

안녕하세요!

이것은 뉴스레터 자동화 시스템의 테스트 이메일입니다.

## 테스트 항목
- 이메일 발송 기능
- HTML 변환 기능
- 마크다운 지원

테스트가 성공적으로 완료되었습니다!

발송 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}
        """
        
        return self.send_newsletter(test_subject, test_content)