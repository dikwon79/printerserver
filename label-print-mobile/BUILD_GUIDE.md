# APK 빌드 가이드

## 사전 준비

1. **Expo CLI 설치** (전역 설치)
   ```bash
   npm install -g eas-cli
   ```

2. **Expo 계정 로그인**
   ```bash
   eas login
   ```
   Expo 계정이 없으면 https://expo.dev 에서 회원가입하세요.

## APK 빌드 방법

### 방법 1: EAS Build 사용 (권장)

1. **프로젝트 디렉토리로 이동**
   ```bash
   cd label-print-mobile
   ```

2. **빌드 시작**
   ```bash
   eas build --platform android --profile preview
   ```
   
   또는 프로덕션 빌드:
   ```bash
   eas build --platform android --profile production
   ```

3. **빌드 완료 후 다운로드**
   - 빌드가 완료되면 Expo 대시보드에서 APK 파일을 다운로드할 수 있습니다.
   - 또는 빌드 완료 후 제공되는 링크에서 직접 다운로드 가능합니다.

### 방법 2: 로컬 빌드 (고급)

로컬에서 직접 빌드하려면:

```bash
eas build --platform android --profile preview --local
```

**주의**: 로컬 빌드는 Android SDK와 빌드 도구가 설치되어 있어야 합니다.

## 빌드 프로필 설명

- **preview**: 테스트용 APK (내부 배포용)
- **production**: 프로덕션 APK (스토어 배포용)

## APK 설치 방법

1. 빌드된 APK 파일을 Android 기기로 전송
2. 기기에서 "알 수 없는 출처" 설치 허용 설정
3. APK 파일 실행하여 설치

## 문제 해결

### 빌드 오류 발생 시

1. **의존성 확인**
   ```bash
   npm install
   ```

2. **캐시 클리어**
   ```bash
   eas build:cancel
   ```

3. **빌드 재시도**

### 네트워크 오류

- HTTP 연결을 사용하므로 `usesCleartextTraffic: true` 설정이 이미 포함되어 있습니다.

## 추가 설정

### 앱 아이콘 변경
- `assets/icon.png` 파일을 교체하세요 (1024x1024 권장)

### 앱 이름 변경
- `app.json`의 `name` 필드를 수정하세요

### 패키지 이름 변경
- `app.json`의 `android.package` 필드를 수정하세요

