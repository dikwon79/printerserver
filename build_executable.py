"""
실행 파일 빌드 스크립트
PyInstaller를 사용하여 Windows/macOS 실행 파일을 생성합니다.
"""

import os
import sys
import subprocess

def install_pyinstaller():
    """PyInstaller 설치"""
    try:
        import PyInstaller
        print("PyInstaller가 이미 설치되어 있습니다.")
    except ImportError:
        print("PyInstaller를 설치합니다...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    """실행 파일 빌드"""
    print("실행 파일을 빌드합니다...")
    
    # PyInstaller 명령어 구성
    cmd = [
        "pyinstaller",
        "--onefile",  # 단일 실행 파일로 생성
        "--windowed",  # 콘솔 창 숨기기 (Windows/macOS)
        "--name=LabelPrinter",  # 실행 파일 이름
        "label_printer_gui.py"
    ]
    
    # 아이콘 파일이 있으면 추가
    if os.path.exists("icon.ico"):
        cmd.append("--icon=icon.ico")
    
    try:
        subprocess.run(cmd, check=True)
        print("빌드가 완료되었습니다!")
        print("dist/ 폴더에서 LabelPrinter.exe (Windows) 또는 LabelPrinter (macOS) 파일을 찾을 수 있습니다.")
    except subprocess.CalledProcessError as e:
        print(f"빌드 중 오류가 발생했습니다: {e}")
        return False
    
    return True

def main():
    print("라벨 인쇄 프로그램 실행 파일 빌더")
    print("=" * 40)
    
    # PyInstaller 설치 확인
    install_pyinstaller()
    
    # 빌드 실행
    if build_executable():
        print("\n빌드가 성공적으로 완료되었습니다!")
        print("dist/ 폴더의 실행 파일을 다른 컴퓨터로 복사하여 사용할 수 있습니다.")
    else:
        print("\n빌드에 실패했습니다. 오류를 확인해주세요.")

if __name__ == "__main__":
    main()
