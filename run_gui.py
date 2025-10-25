"""
라벨 인쇄 프로그램 GUI 실행 스크립트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from label_printer_gui import main
    
    if __name__ == "__main__":
        print("라벨 인쇄 프로그램을 시작합니다...")
        main()
        
except ImportError as e:
    print(f"필요한 모듈을 찾을 수 없습니다: {e}")
    print("다음 명령어로 의존성을 설치해주세요:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"프로그램 실행 중 오류가 발생했습니다: {e}")
    sys.exit(1)
