#!/bin/bash

echo "🚀 APK 빌드를 시작합니다..."

# EAS CLI 설치 확인
if ! command -v eas &> /dev/null; then
    echo "📦 EAS CLI를 설치합니다..."
    npm install -g eas-cli
fi

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# 의존성 설치 확인
if [ ! -d "node_modules" ]; then
    echo "📦 의존성을 설치합니다..."
    npm install
fi

# Expo 로그인 확인
echo "🔐 Expo 계정 로그인이 필요합니다..."
eas whoami || eas login

# 빌드 시작
echo "🔨 APK 빌드를 시작합니다..."
eas build --platform android --profile preview

echo "✅ 빌드가 완료되면 Expo 대시보드에서 APK를 다운로드할 수 있습니다."

