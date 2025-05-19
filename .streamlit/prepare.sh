#!/bin/bash
# Streamlit Cloud에서 앱 실행 전 준비 스크립트

# Python 버전 정보 출력
echo "Python 버전 확인:"
python --version

# 데이터 디렉토리 초기화
echo "데이터 디렉토리 초기화 실행:"
python init_data_dir.py

echo "환경 준비 완료" 