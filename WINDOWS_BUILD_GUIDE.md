# 윈도우용 라벨 인쇄 프로그램 빌드 가이드

## 🖥️ 윈도우에서 실행 파일 만들기

### 1. 필요한 소프트웨어 설치

#### Python 설치

1. [Python 공식 사이트](https://www.python.org/downloads/)에서 Python 3.8 이상 다운로드
2. 설치 시 "Add Python to PATH" 옵션 체크
3. 설치 완료 후 명령 프롬프트에서 확인:
   ```cmd
   python --version
   pip --version
   ```

#### Git 설치 (선택사항)

1. [Git 공식 사이트](https://git-scm.com/download/win)에서 다운로드
2. 기본 설정으로 설치

### 2. 프로젝트 다운로드

#### 방법 1: ZIP 파일 다운로드

1. 이 프로젝트를 ZIP 파일로 다운로드
2. 원하는 폴더에 압축 해제

#### 방법 2: Git 사용

```cmd
git clone <프로젝트_URL>
cd inno
```

### 3. 가상환경 설정 및 의존성 설치

```cmd
# 프로젝트 폴더로 이동
cd inno

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 4. 실행 파일 빌드

```cmd
# 가상환경이 활성화된 상태에서
python build_windows.py
```

또는 직접 PyInstaller 사용:

```cmd
pyinstaller --onefile --windowed --name=LabelPrinter label_printer_gui.py
```

### 5. 빌드 결과

빌드가 완료되면 다음 위치에 실행 파일이 생성됩니다:

- `dist_windows/LabelPrinter.exe` (또는 `dist/LabelPrinter.exe`)

## 🚀 윈도우에서 사용하기

### 1. 실행 파일 배포

- `LabelPrinter.exe` 파일을 윈도우 컴퓨터로 복사
- 별도 설치 없이 바로 실행 가능

### 2. 실행 방법

1. `LabelPrinter.exe` 더블클릭
2. 프로그램이 시작되면 자동으로 서버가 실행됨
3. GUI에서 라벨 정보 입력 후 인쇄

### 3. 네트워크 설정

- 프로그램이 자동으로 IP 주소를 감지
- 모바일 앱에서 표시된 IP 주소로 접속

## 🔧 문제 해결

### 빌드 오류

- **"pyinstaller가 인식되지 않습니다"**: `pip install pyinstaller` 실행
- **"tkinter 모듈을 찾을 수 없습니다"**: Python 재설치 시 "tcl/tk and IDLE" 옵션 체크
- **"reportlab 오류"**: `pip install --upgrade reportlab` 실행

### 실행 오류

- **"DLL을 찾을 수 없습니다"**: Visual C++ Redistributable 설치
- **"프린터를 찾을 수 없습니다"**: 윈도우 프린터 설정 확인
- **"포트가 사용 중입니다"**: 방화벽 설정 확인

### 네트워크 문제

- **모바일에서 연결 안됨**: 윈도우 방화벽에서 포트 허용
- **IP 주소가 다름**: 같은 Wi-Fi 네트워크에 연결 확인

## 📱 모바일 앱 설정

### React Native 앱

1. `react-native-example` 폴더의 앱을 빌드
2. 앱에서 자동으로 서버 IP 감지
3. 연결 후 라벨 인쇄 가능

### API 테스트

```cmd
# 서버 상태 확인
curl http://YOUR_IP:8080/api/status

# 인쇄 테스트
curl -X POST http://YOUR_IP:8080/api/print -H "Content-Type: application/json" -d "{\"total_weight\": \"20.0\", \"pallet_weight\": \"4.5\"}"
```

## 🎯 주요 기능

- **자동 IP 감지**: 네트워크 환경에 맞게 자동 설정
- **프린터 자동 감지**: 시스템의 프린터를 자동으로 찾아서 목록에 표시
- **인쇄 기록 저장**: 모든 인쇄 기록을 자동으로 저장하고 표시
- **모바일 연동**: React Native 앱과 실시간 연동
- **크로스 플랫폼**: 윈도우, macOS, Linux에서 모두 작동

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. Python 버전 (3.8 이상)
2. 모든 의존성 설치 완료
3. 네트워크 연결 상태
4. 프린터 드라이버 설치
5. 방화벽 설정
