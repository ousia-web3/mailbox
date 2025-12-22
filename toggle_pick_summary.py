#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PICK 요약 기능 활성화/비활성화 스크립트
"""

import json
import sys
from keyword_manager import KeywordManager

def main():
    """PICK 요약 기능 설정 변경"""
    try:
        manager = KeywordManager()
        
        # 현재 설정 확인
        current_setting = manager.get_pick_summary_setting()
        print(f"현재 PICK 요약 기능 상태: {'활성화' if current_setting else '비활성화'}")
        
        if len(sys.argv) > 1:
            # 명령행 인수로 설정 변경
            if sys.argv[1].lower() in ['true', '1', 'on', 'enable', '활성화']:
                new_setting = True
            elif sys.argv[1].lower() in ['false', '0', 'off', 'disable', '비활성화']:
                new_setting = False
            else:
                print("사용법: python toggle_pick_summary.py [활성화|비활성화|true|false]")
                return
        else:
            # 대화형 설정 변경
            print("\nPICK 요약 기능을 어떻게 설정하시겠습니까?")
            print("1. 활성화")
            print("2. 비활성화")
            
            while True:
                choice = input("선택하세요 (1 또는 2): ").strip()
                if choice == '1':
                    new_setting = True
                    break
                elif choice == '2':
                    new_setting = False
                    break
                else:
                    print("1 또는 2를 입력해주세요.")
        
        # 설정 변경
        if current_setting != new_setting:
            success = manager.update_pick_summary_setting(new_setting)
            if success:
                print(f"PICK 요약 기능이 {'활성화' if new_setting else '비활성화'}되었습니다.")
            else:
                print("설정 변경에 실패했습니다.")
        else:
            print("설정이 이미 원하는 상태입니다.")
            
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
