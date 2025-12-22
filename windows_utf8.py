# -*- coding: utf-8 -*-
"""
Windows UTF-8 콘솔 출력 설정
"""
import sys
import os
import locale

def setup_windows_utf8():
    """Windows에서 UTF-8 콘솔 출력 설정"""
    try:
        # 환경변수 설정
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Windows 콘솔 코드페이지를 UTF-8로 설정
        if sys.platform.startswith('win'):
            try:
                # cmd에서 chcp 65001 실행
                os.system('chcp 65001 >nul 2>&1')
            except:
                pass
            
            # Python 출력 인코딩 설정
            try:
                import codecs
                if hasattr(sys.stdout, 'buffer'):
                    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
                    sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
            except:
                try:
                    # 대안 방법
                    import io
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
                except:
                    pass
        
        return True
    except Exception as e:
        print(f"UTF-8 설정 실패: {e}")
        return False

# 모듈 import 시 자동 설정
if __name__ != '__main__':
    setup_windows_utf8()