@echo off
echo 윈도우용 라벨 인쇄 프로그램 빌더
echo ========================================

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo Python이 설치되지 않았습니다.
    echo https://www.python.org/downloads/ 에서 Python을 다운로드하여 설치하세요.
    pause
    exit /b 1
)

REM 가상환경 확인 및 생성
if not exist "venv" (
    echo 가상환경을 생성합니다...
    python -m venv venv
)

REM 가상환경 활성화
echo 가상환경을 활성화합니다...
call venv\Scripts\activate.bat

REM 의존성 설치
echo 의존성을 설치합니다...
pip install -r requirements.txt

REM PyInstaller 설치 확인
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller를 설치합니다...
    pip install pyinstaller
)

REM 실행 파일 빌드
echo 실행 파일을 빌드합니다...
pyinstaller --onefile --windowed --name=LabelPrinter --distpath=dist_windows label_printer_gui.py

if exist "dist_windows\LabelPrinter.exe" (
    echo.
    echo ========================================
    echo 빌드가 완료되었습니다!
    echo dist_windows\LabelPrinter.exe 파일을 사용하세요.
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 빌드에 실패했습니다.
    echo 오류를 확인하고 다시 시도하세요.
    echo ========================================
)

pause
