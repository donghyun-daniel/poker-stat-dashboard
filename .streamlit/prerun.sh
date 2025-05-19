#!/bin/bash

# Streamlit Cloud에서 앱 실행 전에 실행되는 스크립트

echo "Running pre-start setup for Poker Stats Dashboard"

# Python 버전 정보 출력
python --version

# setup.py 스크립트 실행
python setup.py

# 데이터 디렉토리 확인
mkdir -p data

# 필요한 권한 설정
chmod -R 777 data

echo "Pre-start setup completed successfully!" 