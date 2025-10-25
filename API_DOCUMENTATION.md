# 라벨 인쇄 API 문서

## 개요

이 API는 10cm x 5cm 크기의 라벨을 인쇄하기 위한 RESTful API입니다. 모바일 앱에서 서버로 데이터를 전송하여 라벨을 인쇄할 수 있습니다.

## 기본 정보

- **Base URL**: `http://YOUR_SERVER_IP:5000/api`
- **Content-Type**: `application/json`
- **인증**: 없음 (로컬 네트워크용)

## 엔드포인트

### 1. 서버 상태 확인

서버의 현재 상태와 버전 정보를 확인합니다.

```http
GET /api/status
```

**응답 예시:**

```json
{
  "success": true,
  "status": "running",
  "server_time": "2024-01-15T10:30:00.123456",
  "version": "1.0.0",
  "label_size": "10cm x 5cm"
}
```

**응답 필드:**

- `success`: 요청 성공 여부 (boolean)
- `status`: 서버 상태 ("running")
- `server_time`: 서버 시간 (ISO 8601 형식)
- `version`: API 버전
- `label_size`: 지원하는 라벨 크기

---

### 2. 프린터 목록 조회

사용 가능한 프린터 목록과 상태를 조회합니다.

```http
GET /api/printers
```

**응답 예시:**

```json
{
  "success": true,
  "printers": [
    {
      "name": "HP_LaserJet",
      "status": "available",
      "description": "프린터 HP_LaserJet"
    },
    {
      "name": "Canon_Pixma",
      "status": "busy",
      "description": "프린터 Canon_Pixma"
    }
  ]
}
```

**응답 필드:**

- `success`: 요청 성공 여부 (boolean)
- `printers`: 프린터 목록 (array)
  - `name`: 프린터 이름 (string)
  - `status`: 프린터 상태 ("available" | "busy")
  - `description`: 프린터 설명 (string)

---

### 3. 단일 라벨 인쇄

하나의 라벨을 인쇄합니다.

```http
POST /api/print
Content-Type: application/json
```

**요청 본문:**

```json
{
  "product_name": "사과",
  "weight": "1.5",
  "date": "2024-01-15",
  "barcode": "ID20240115001",
  "additional_info": "유기농"
}
```

**요청 필드:**

- `weight` (필수): 무게 (number, kg 단위)
- `product_name` (선택): 제품명 (string, 최대 20자)
- `date` (선택): 날짜 (string, YYYY-MM-DD 형식)
- `barcode` (선택): 바코드/ID (string)
- `additional_info` (선택): 추가 정보 (string, 최대 30자)

**성공 응답 (200):**

```json
{
  "success": true,
  "message": "라벨이 성공적으로 인쇄되었습니다.",
  "data": {
    "label_id": "ID20240115001",
    "weight": "1.5",
    "product_name": "사과",
    "print_time": "2024-01-15T10:30:00.123456"
  }
}
```

**오류 응답 (400):**

```json
{
  "success": false,
  "error": "WEIGHT_REQUIRED",
  "message": "무게 정보가 필요합니다."
}
```

**오류 응답 (500):**

```json
{
  "success": false,
  "error": "PRINT_FAILED",
  "message": "인쇄에 실패했습니다. 프린터 설정을 확인해주세요."
}
```

---

### 4. 일괄 라벨 인쇄

여러 라벨을 한 번에 인쇄합니다.

```http
POST /api/print/batch
Content-Type: application/json
```

**요청 본문:**

```json
{
  "labels": [
    {
      "product_name": "사과",
      "weight": "1.0",
      "barcode": "ID001"
    },
    {
      "product_name": "바나나",
      "weight": "0.8",
      "barcode": "ID002"
    },
    {
      "product_name": "오렌지",
      "weight": "1.2",
      "barcode": "ID003"
    }
  ]
}
```

**요청 필드:**

- `labels` (필수): 라벨 데이터 배열 (array)
  - 각 라벨 객체는 단일 라벨 인쇄와 동일한 필드 구조

**성공 응답 (200):**

```json
{
  "success": true,
  "message": "3/3개 라벨이 인쇄되었습니다.",
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
      "weight": "0.8"
    },
    {
      "index": 2,
      "success": true,
      "label_id": "ID003",
      "weight": "1.2"
    }
  ],
  "summary": {
    "total": 3,
    "success": 3,
    "failed": 0
  }
}
```

**부분 성공 응답 (200):**

```json
{
  "success": true,
  "message": "2/3개 라벨이 인쇄되었습니다.",
  "results": [
    {
      "index": 0,
      "success": true,
      "label_id": "ID001",
      "weight": "1.0"
    },
    {
      "index": 1,
      "success": false,
      "error": "무게 정보가 필요합니다."
    },
    {
      "index": 2,
      "success": true,
      "label_id": "ID003",
      "weight": "1.2"
    }
  ],
  "summary": {
    "total": 3,
    "success": 2,
    "failed": 1
  }
}
```

---

### 5. 인쇄 상태 조회

특정 라벨의 인쇄 상태를 조회합니다.

```http
GET /api/print/status/{label_id}
```

**URL 매개변수:**

- `label_id`: 조회할 라벨의 ID (string)

**응답 예시:**

```json
{
  "success": true,
  "label_id": "ID20240115001",
  "status": "printed",
  "print_time": "2024-01-15T10:30:00.123456"
}
```

**응답 필드:**

- `success`: 요청 성공 여부 (boolean)
- `label_id`: 라벨 ID (string)
- `status`: 인쇄 상태 ("printed")
- `print_time`: 인쇄 시간 (ISO 8601 형식)

---

## 오류 코드

| HTTP 상태 코드 | 오류 코드             | 설명                  |
| -------------- | --------------------- | --------------------- |
| 400            | `WEIGHT_REQUIRED`     | 무게 정보가 필요함    |
| 400            | `NO_LABELS`           | 인쇄할 라벨이 없음    |
| 500            | `PRINT_FAILED`        | 인쇄 실패             |
| 500            | `PRINTER_LIST_FAILED` | 프린터 목록 조회 실패 |
| 500            | `STATUS_CHECK_FAILED` | 상태 확인 실패        |
| 500            | `STATUS_QUERY_FAILED` | 상태 조회 실패        |
| 500            | `INTERNAL_ERROR`      | 서버 내부 오류        |

## 데이터 유효성 검사

### 무게 (weight)

- 필수 필드
- 0보다 큰 숫자여야 함
- 소수점 지원

### 제품명 (product_name)

- 선택 필드
- 최대 20자
- 빈 문자열 허용

### 날짜 (date)

- 선택 필드
- YYYY-MM-DD 형식
- 기본값: 현재 날짜

### 바코드/ID (barcode)

- 선택 필드
- 기본값: 자동 생성 (ID + 타임스탬프)

### 추가 정보 (additional_info)

- 선택 필드
- 최대 30자
- 빈 문자열 허용

## 사용 예시

### JavaScript (Fetch API)

```javascript
// 서버 상태 확인
const checkStatus = async () => {
  const response = await fetch("http://192.168.1.100:5000/api/status");
  const data = await response.json();
  console.log(data);
};

// 라벨 인쇄
const printLabel = async () => {
  const labelData = {
    product_name: "사과",
    weight: "1.5",
    date: "2024-01-15",
    barcode: "ID001",
    additional_info: "유기농",
  };

  const response = await fetch("http://192.168.1.100:5000/api/print", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(labelData),
  });

  const result = await response.json();
  console.log(result);
};
```

### Python (requests)

```python
import requests

# 서버 상태 확인
response = requests.get('http://192.168.1.100:5000/api/status')
print(response.json())

# 라벨 인쇄
label_data = {
    "product_name": "사과",
    "weight": "1.5",
    "date": "2024-01-15",
    "barcode": "ID001",
    "additional_info": "유기농"
}

response = requests.post(
    'http://192.168.1.100:5000/api/print',
    json=label_data
)
print(response.json())
```

## 네트워크 설정

### 방화벽 설정

서버가 실행되는 컴퓨터에서 포트 5000을 열어야 합니다:

**Linux/macOS:**

```bash
sudo ufw allow 5000
```

**Windows:**
Windows 방화벽에서 포트 5000을 허용하도록 설정

### IP 주소 확인

서버 IP 주소를 확인하려면:

**Linux/macOS:**

```bash
ifconfig | grep inet
```

**Windows:**

```cmd
ipconfig
```

## 제한사항

1. **네트워크**: 로컬 네트워크에서만 사용 가능
2. **프린터**: CUPS 지원 프린터 또는 Windows 프린터 드라이버 필요
3. **라벨 크기**: 10cm x 5cm 고정 크기
4. **동시 인쇄**: 한 번에 하나의 인쇄 작업만 처리
5. **저장**: 인쇄된 라벨 정보는 임시로만 저장됨
