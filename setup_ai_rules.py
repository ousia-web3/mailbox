from pathlib import Path

# 1. 파일 내용 정의
files = {
    ".ai/instructions.md": """# AI 작업 헌법 (AI Work Constitution)

이 문서는 이 프로젝트에서 AI(Cursor, Windsurf 등)가 작업을 수행할 때 반드시 준수해야 할 절대적인 규칙을 정의합니다.

## 0. 프로젝트 초기화 규칙 (Project Bootstrap)

- 이 프로젝트는 초기 실행 시 자동으로 필수 폴더 및 규칙 파일을 생성할 수 있습니다.
- 초기화 단계에서 생성되는 파일은 표준 템플릿을 따릅니다.
- 초기화 스크립트는 기존 파일이 있을 경우 덮어쓰지 않고, 누락된 항목만 보완합니다.

## 1. 실행 정책 (Execution Policy)

- **기본 원칙**: 모든 명령어 실행은 `rules/EXEC_POLICY.md`를 따릅니다.
- **안전한 실행**: 시스템에 파괴적인 영향을 줄 수 있는 명령어는 실행 전 반드시 사용자의 확인을 받아야 합니다.
- **테스트 및 검증**: 코드의 정확성을 검증하기 위한 테스트 실행은 권장되나, 실행 전 사용자에게 알리는 것을 원칙으로 합니다.
- **테스트 파일 관리**: 모든 테스트 관련 파일(단위 테스트, 통합 테스트, 재현 스크립트 등)은 반드시 `tests/` 폴더 내에 생성하거나 이동시켜야 합니다. 프로젝트 루트 디렉토리를 어지럽히지 마십시오.

## 2. 코드 수정 원칙 (Code Modification Principles)

- **최소 diff 원칙**: 수정이 필요한 부분만 정확히 타겟팅하여 변경해야 합니다. 파일 전체를 불필요하게 덮어쓰거나 포맷팅을 변경하여 diff를 어지럽히지 마십시오.
- **관련 없는 파일 수정 금지**: 요청된 작업과 직접적인 관련이 없는 파일은 절대 건드리지 마십시오.
- **정적 추론 및 검증**: 코드 실행 전 정적 분석을 통해 논리적 오류를 최대한 사전에 검증하십시오.
- **자동 생성 파일 보호**: 자동 생성된 규칙/로그 파일은 프로젝트 기준 문서이므로, 사용자의 명시적인 요청 없이 내용 변경을 허용하지 않습니다.
- **AI vs 코드 역할 분담**: 창의적 생성, 요약, 추론은 AI가 담당하되, **데이터 정합성(개수 일치, 포맷팅 등)**이 중요한 로직은 반드시 **코드(Python 등)**로 구현하여 처리해야 합니다. AI의 생성 능력에 의존하여 정형 데이터를 처리하지 마십시오.

## 3. 오류 관리 및 이력 (Error Management & History)

- **이력 문서 갱신 필수**: 오류가 발생하거나 오류를 수정했을 경우, 반드시 `logs/ERROR_HISTORY.md`와 `rules/CHANGELOG.md`를 갱신해야 합니다.
- **선행 참조**: 코드 수정을 시작하기 전에 `logs/ERROR_HISTORY.md`와 `rules/CHANGELOG.md`를 먼저 읽고, 과거의 실수나 패턴을 파악하여 동일한 오류를 반복하지 않도록 주의하십시오.
- **컨텍스트 최적화**: `rules/CHANGELOG.md` 참조 시 토큰 절약을 위해 전체를 읽지 말고 **최근 5개 항목**을 우선적으로 참조하십시오.
- **예방 조치 기록**: 명시적 오류가 발생하지 않았더라도, 재현 가능성이 높거나 과거 오류와 유사한 위험 요소를 제거한 경우 `rules/CHANGELOG.md`에 예방 조치로 기록합니다.

## 4. 문서화 및 완료 조건 (Documentation & Definition of Done)

### 4.1. 문서화 의무 (Mandatory Documentation)
- **모든 코드 변경은 문서 변경을 동반해야 합니다.** 코드만 수정하고 문서를 수정하지 않는 것은 "미완성" 작업입니다.
- **필수 갱신 문서**:
  - `rules/CHANGELOG.md`: 변경 내용, 이유, 재발 방지 대책 기록
  - `logs/ERROR_HISTORY.md`: 오류 수정 시 발생 원인과 해결책 기록
- **타이밍**: 코드를 수정하기 **직전** 또는 수정과 **동시에** 문서 업데이트 계획을 세우십시오.

### 4.2. 완료 조건 (Definition of Done)
AI는 다음 질문에 모두 "예"라고 답할 수 있을 때만 작업을 완료했다고 간주해야 합니다.
1. 사용자의 요구사항을 충족하는 코드를 작성했는가?
2. 코드가 의도한 대로 동작함을 검증했는가?
3. **`rules/CHANGELOG.md`에 변경 내역을 기록했는가?**
4. **오류 수정의 경우 `logs/ERROR_HISTORY.md`를 업데이트했는가?**
5. 불필요하게 생성된 임시 파일은 정리했는가?
""",

    "rules/EXEC_POLICY.md": """# 실행 권한 정책 (Execution Policy)

이 문서는 프로젝트 내에서 명령어 실행에 대한 정책을 정의합니다.

## 기본 원칙
1. **AI는 기본적으로 어떠한 명령어도 자동으로 실행하지 않습니다.**
2. 모든 명령어는 사용자가 직접 터미널에 입력하여 실행하는 것을 원칙으로 합니다.

## 예외 허용 (Explicit User Request)
사용자가 대화창을 통해 명시적으로 **"실행해"**, **"명령어 실행해줘"** 등의 표현을 사용하여 지시한 경우에만 예외적으로 명령 실행 도구를 사용할 수 있습니다.

### 허용되는 경우
- 사용자가 특정 스크립트 실행을 요청했을 때 (예: `python main.py 실행해줘`)
- 사용자가 테스트 실행을 요청했을 때 (예: `테스트 코드 돌려줘`)
- 사용자가 파일 생성을 위한 쉘 명령 실행을 명시적으로 허락했을 때

### 절대 금지 (Never Execute)
사용자의 요청이 있더라도 다음의 명령어는 절대 실행해서는 안 됩니다:
- 시스템 설정 변경 (레지스트리 수정, 방화벽 해제 등)
- 외부 네트워크로의 무단 데이터 전송
- `rm -rf /` 와 같은 파괴적인 삭제 명령
- 검증되지 않은 외부 스크립트 다운로드 및 실행 (`curl | bash` 등)

## 실행 전 확인 절차
명령어를 실행하기 전, AI는 다음 사항을 스스로 검토해야 합니다:
1. 이 명령어가 프로젝트 범위를 벗어나지 않는가?
2. 이 명령어가 시스템에 영구적인 손상을 줄 가능성이 있는가?
3. 이 명령어가 되돌릴 수 없는 변경을 가하는가?

안전하지 않다고 판단되면 실행을 거부하고 사용자에게 이유를 설명해야 합니다.
""",

    "rules/CHANGELOG.md": """# 변경 이력 (CHANGELOG)

이 문서는 프로젝트의 주요 수정, 개선, 오류 조치 이력을 기록합니다.
AI는 작업 완료 후 이 문서를 갱신해야 합니다.

## 양식 가이드
- **날짜**: YYYY-MM-DD
- **변경 대상**: 수정된 파일명 또는 모듈
- **유형**: [오류수정], [리팩토링], [기능개선], [문서화]
- **내용**:
  - **문제 요약**: 무엇이 문제였는지 간단히
  - **수정 내용**: 어떻게 고쳤는지
  - **재발 방지**: 향후 주의할 점

---
""",

    "logs/ERROR_HISTORY.md": """# 오류 기록 (ERROR HISTORY)

이 문서는 프로젝트 진행 중 발생한 실제 오류와 그 해결 과정을 기록합니다.
동일한 실수를 반복하지 않기 위해 AI는 작업 전 이 문서를 반드시 참조해야 합니다.

## 양식 가이드
- **발생 일자**: YYYY-MM-DD
- **상태**: [해결됨] / [미해결]
- **오류 메시지/증상**: 로그 메시지 또는 사용자 보고 증상
- **원인 분석**: 왜 발생했는지 근본 원인
- **해결 방법**: 구체적인 수정 코드 또는 조치 사항
- **재발 방지 규칙**: 향후 유사 상황 방지를 위한 지침

---
"""
}

def setup_ai_rules():
    print("🚀 AI 협업 규칙 설치를 시작합니다...")

    # 2. 파일 생성
    for file_path, content in files.items():
        path = Path(file_path)
        
        # 부모 디렉토리 생성
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            print(f"📁 폴더 생성: {path.parent}")
        
        # 파일 생성
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            print(f"✅ 파일 생성: {path}")
        else:
            print(f"ℹ️ 이미 존재함 (건너뜀): {path}")

    # 3. .gitignore 설정
    gitignore_path = Path(".gitignore")
    gitignore_rule = "\n# AI Rules Logs\nlogs/\n!logs/ERROR_HISTORY.md\n"
    
    if gitignore_path.exists():
        current_content = gitignore_path.read_text(encoding="utf-8")
        if "!logs/ERROR_HISTORY.md" not in current_content:
            with gitignore_path.open("a", encoding="utf-8") as f:
                f.write(gitignore_rule)
            print("✅ .gitignore 업데이트 완료")
    else:
        gitignore_path.write_text(gitignore_rule, encoding="utf-8")
        print("✅ .gitignore 생성 완료")

    # 4. README.md 업데이트
    readme_path = Path("README.md")
    readme_section = """
## 🤖 AI 협업 규칙 및 오류 관리

이 프로젝트는 AI와의 효율적이고 안전한 협업을 위해 다음 문서를 기준으로 작업합니다.
모든 작업 전 아래 문서를 반드시 확인해 주세요.

- **[작업 헌법]** `.ai/instructions.md`: AI 작업의 절대 규칙 (실행 제한, 최소 diff 등)
- **[실행 정책]** `rules/EXEC_POLICY.md`: 명령어 실행 권한 및 절차
- **[변경 이력]** `rules/CHANGELOG.md`: 주요 변경 사항 및 리팩토링 기록
- **[오류 기록]** `logs/ERROR_HISTORY.md`: 발생한 오류와 해결 방법, 재발 방지책
"""
    
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        if "AI 협업 규칙" not in content:
            with readme_path.open("a", encoding="utf-8") as f:
                f.write(readme_section)
            print("✅ README.md 섹션 추가 완료")
    else:
        readme_path.write_text(f"# Project\n{readme_section}", encoding="utf-8")
        print("✅ README.md 생성 완료")

    print("\n✨ 설치가 완료되었습니다!")
    print("\n🤖 [AI 에이전트 필독]")
    print("1. 프로젝트 루트에 있는 .ai/instructions.md와 rules/ 폴더의 규칙들을 읽고 숙지해줘.")
    print("2. 앞으로 모든 작업은 이 규칙을 준수해야 해.")

if __name__ == "__main__":
    setup_ai_rules()
