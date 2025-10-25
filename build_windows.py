#!/usr/bin/env python3
"""
윈도우용 라벨 인쇄 프로그램 실행 파일 빌더
"""

import os
import sys
import subprocess
import platform

def check_pyinstaller():
    """PyInstaller 설치 확인"""
    try:
        import PyInstaller
        print(f"PyInstaller 버전: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller가 설치되지 않았습니다.")
        print("다음 명령어로 설치하세요: pip install pyinstaller")
        return False

def build_windows_executable():
    """윈도우용 실행 파일 빌드"""
    print("윈도우용 라벨 인쇄 프로그램 실행 파일 빌더")
    print("=" * 50)
    
    # PyInstaller 확인
    if not check_pyinstaller():
        return False
    
    print("윈도우용 실행 파일을 빌드합니다...")
    
    # PyInstaller 명령어 구성 (윈도우용)
    cmd = [
        "pyinstaller",
        "--onefile",  # 단일 실행 파일로 생성
        "--windowed",  # 콘솔 창 숨기기
        "--name=LabelPrinter",  # 실행 파일 이름
        "--distpath=dist_windows",  # 윈도우용 dist 폴더
        "label_printer_gui.py"
    ]
    
    # 아이콘 파일이 있으면 추가
    if os.path.exists("icon.ico"):
        cmd.append("--icon=icon.ico")
    
    try:
        subprocess.run(cmd, check=True)
        print("윈도우용 빌드가 완료되었습니다!")
        print("dist_windows/ 폴더에서 LabelPrinter.exe 파일을 찾을 수 있습니다.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"빌드 중 오류가 발생했습니다: {e}")
        return False

def create_windows_installer():
    """윈도우용 설치 패키지 생성 (선택사항)"""
    print("\n윈도우용 설치 패키지를 생성하시겠습니까? (y/n): ", end="")
    choice = input().lower()
    
    if choice == 'y':
        print("NSIS 또는 Inno Setup을 사용하여 설치 패키지를 생성할 수 있습니다.")
        print("자세한 내용은 README.md를 참조하세요.")

def main():
    """메인 함수"""
    print("현재 플랫폼:", platform.system())
    
    if platform.system() == "Windows":
        print("윈도우 환경에서 빌드합니다...")
        success = build_windows_executable()
    else:
        print("현재는 macOS/Linux 환경입니다.")
        print("윈도우용 실행 파일을 만들려면:")
        print("1. 윈도우 컴퓨터에서 이 스크립트를 실행하거나")
        print("2. GitHub Actions를 사용하여 자동 빌드하거나")
        print("3. Docker를 사용하여 윈도우 환경을 시뮬레이션하세요.")
        
        # 크로스 플랫폼 빌드 시도 (제한적)
        print("\n크로스 플랫폼 빌드를 시도합니다...")
        success = build_windows_executable()
    
    if success:
        print("\n빌드가 성공적으로 완료되었습니다!")
        print("dist_windows/ 폴더의 LabelPrinter.exe 파일을 윈도우 컴퓨터로 복사하여 사용할 수 있습니다.")
        create_windows_installer()
    else:
        print("\n빌드에 실패했습니다. 오류를 확인해주세요.")

if __name__ == "__main__":
    main()
