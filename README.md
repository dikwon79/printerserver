# 라벨 인쇄 시스템

10cm x 5cm 크기의 라벨을 인쇄할 수 있는 파이썬 서버와 리액트 네이티브 모바일 앱입니다.

## 기능

- **라벨 인쇄**: 10cm x 5cm 크기의 라벨을 PDF로 생성하여 인쇄
- **모바일 지원**: 리액트 네이티브 앱을 통한 모바일에서 라벨 인쇄
- **일괄 인쇄**: 여러 라벨을 한 번에 인쇄
- **프린터 관리**: 사용 가능한 프린터 목록 조회 및 상태 확인
- **실시간 상태**: 서버 연결 상태 및 인쇄 상태 실시간 확인

## 시스템 요구사항

### 서버 (Python)

- Python 3.7 이상
- CUPS (Linux/macOS) 또는 Windows 프린터 드라이버
- 네트워크 프린터 또는 로컬 프린터

### 모바일 앱 (React Native)

- React Native 0.72 이상
- Expo CLI
- iOS/Android 디바이스

## 설치 및 실행

### 1. 데스크톱 프로그램 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# GUI 프로그램 실행
python label_printer_gui.py
# 또는
python run_gui.py
```

### 2. 실행 파일 생성 (선택사항)

#### macOS/Linux

```bash
# 실행 파일 빌드
python build_executable.py
```

#### Windows

```bash
# 방법 1: 배치 파일 사용
build_windows.bat

# 방법 2: Python 스크립트 사용
python build_windows.py
```

빌드가 완료되면 다음 폴더에서 실행 파일을 찾을 수 있습니다:

- macOS: `dist/LabelPrinter`
- Linux: `dist/LabelPrinter.exe`
- Windows: `dist_windows/LabelPrinter.exe`

#### 윈도우용 상세 가이드

윈도우에서 실행 파일을 만드는 자세한 방법은 [WINDOWS_BUILD_GUIDE.md](WINDOWS_BUILD_GUIDE.md)를 참조하세요.

### 3. 모바일 앱 설정

```bash
# 모바일 앱 디렉토리로 이동
cd react-native-example

# 의존성 설치
npm install

# Expo 앱 실행
npm start
```

### 4. 네트워크 설정

모바일 앱에서 데스크톱 프로그램에 접속하려면:

1. 데스크톱 프로그램이 실행 중인 컴퓨터의 IP 주소를 확인
2. `LabelPrintService.js` 파일의 `API_BASE_URL`을 실제 IP 주소로 변경
3. 모바일 디바이스와 데스크톱 프로그램이 같은 네트워크에 연결되어 있는지 확인

**중요**: 데스크톱 프로그램을 실행하면 자동으로 백그라운드에서 API 서버가 시작됩니다.

## API 문서

### 기본 URL

```
http://YOUR_SERVER_IP:5000/api
```

### 엔드포인트

#### 1. 서버 상태 확인

```http
GET /api/status
```

**응답:**

```json
{
  "success": true,
  "status": "running",
  "server_time": "2024-01-01T12:00:00",
  "version": "1.0.0",
  "label_size": "10cm x 5cm"
}
```

#### 2. 프린터 목록 조회

```http
GET /api/printers
```

**응답:**

```json
{
  "success": true,
  "printers": [
    {
      "name": "printer_name",
      "status": "available",
      "description": "프린터 설명"
    }
  ]
}
```

#### 3. 단일 라벨 인쇄

```http
POST /api/print
Content-Type: application/json

{
  "product_name": "제품명",
  "weight": "1.5",
  "date": "2024-01-01",
  "barcode": "ID123456789",
  "additional_info": "추가 정보"
}
```

**응답:**

```json
{
  "success": true,
  "message": "라벨이 성공적으로 인쇄되었습니다.",
  "data": {
    "label_id": "ID123456789",
    "weight": "1.5",
    "product_name": "제품명",
    "print_time": "2024-01-01T12:00:00"
  }
}
```

#### 4. 일괄 라벨 인쇄

```http
POST /api/print/batch
Content-Type: application/json

{
  "labels": [
    {
      "product_name": "제품1",
      "weight": "1.0",
      "barcode": "ID001"
    },
    {
      "product_name": "제품2",
      "weight": "2.0",
      "barcode": "ID002"
    }
  ]
}
```

**응답:**

```json
{
  "success": true,
  "message": "2/2개 라벨이 인쇄되었습니다.",
  "results": [
    {
      "index": 0,
      "success": true,
      "label_id": "ID001",
      "weight": "1.0"
    },
    {
      "index": 1,
      "success": true,
      "label_id": "ID002",
      "weight": "2.0"
    }
  ],
  "summary": {
    "total": 2,
    "success": 2,
    "failed": 0
  }
}
```

#### 5. 인쇄 상태 조회

```http
GET /api/print/status/{label_id}
```

**응답:**

```json
{
  "success": true,
  "label_id": "ID123456789",
  "status": "printed",
  "print_time": "2024-01-01T12:00:00"
}
```

## 라벨 형식

라벨은 10cm x 5cm 크기로 다음 정보를 포함합니다:

- **제품명**: 상단에 표시 (최대 20자)
- **무게**: 중앙에 큰 글씨로 표시 (kg 단위)
- **날짜**: 하단 좌측에 표시
- **바코드/ID**: 하단 우측에 표시
- **추가 정보**: 하단 중앙에 표시 (최대 30자)

## 오류 코드

| 오류 코드             | 설명                  |
| --------------------- | --------------------- |
| `WEIGHT_REQUIRED`     | 무게 정보가 필요함    |
| `PRINT_FAILED`        | 인쇄 실패             |
| `NO_LABELS`           | 인쇄할 라벨이 없음    |
| `PRINTER_LIST_FAILED` | 프린터 목록 조회 실패 |
| `STATUS_CHECK_FAILED` | 상태 확인 실패        |
| `INTERNAL_ERROR`      | 서버 내부 오류        |

## 문제 해결

### 1. 프린터가 인쇄되지 않는 경우

- 프린터가 켜져 있고 연결되어 있는지 확인
- 프린터 드라이버가 올바르게 설치되어 있는지 확인
- CUPS 설정 확인 (Linux/macOS)

### 2. 모바일 앱에서 서버에 연결되지 않는 경우

- 서버 IP 주소가 올바른지 확인
- 방화벽 설정 확인
- 모바일 디바이스와 서버가 같은 네트워크에 있는지 확인

### 3. 라벨이 올바르게 인쇄되지 않는 경우

- 프린터 용지 크기 설정 확인
- 라벨 용지가 올바른 크기(10cm x 5cm)인지 확인

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.
# printerserver

