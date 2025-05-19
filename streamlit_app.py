"""
Streamlit application entry point for the Poker Stats Dashboard.
This file serves as the main entry point for running the application.
"""

import os
import sys
import streamlit as st

# 기본 설정
st.set_page_config(
    page_title="🃏 Poker Stats Dashboard",
    page_icon="🎮",
    layout="wide"
)

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 데이터 디렉토리 생성
data_dir = os.path.join(current_dir, "data")
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

try:
    # 앱 실행
    from app.ui.main import run_app
    run_app()
except Exception as e:
    st.error("앱 시작 중 오류가 발생했습니다.")
    st.exception(e) 