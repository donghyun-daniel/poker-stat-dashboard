"""
Streamlit application entry point for the Poker Stats Dashboard.
This file serves as the main entry point for running the application.
"""

import os
import sys
import stat
import streamlit as st
import subprocess
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Streamlit 페이지 설정
st.set_page_config(
    page_title="🃏 Poker Stats Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 시작 메시지 출력
logger.info("앱 초기화 시작")
print("앱 초기화 시작")

# Add path to the project root to allow imports from app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 데이터 디렉토리 확인
data_dir = os.path.join(current_dir, "data")
if not os.path.exists(data_dir):
    try:
        os.makedirs(data_dir, exist_ok=True)
        # 전체 권한 설정 (777)
        os.chmod(data_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        st.success(f"데이터 디렉토리 생성 및 권한 설정 완료: {data_dir}")
    except Exception as e:
        st.warning(f"데이터 디렉토리 설정 중 오류 발생: {e}")
        st.info("관리자 권한이 필요할 수 있습니다.")

# 초기화 스크립트 실행
try:
    init_script = os.path.join(current_dir, "init_db.py")
    if os.path.exists(init_script):
        print(f"데이터베이스 초기화 스크립트 실행: {init_script}")
        try:
            result = subprocess.run(
                [sys.executable, init_script],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"초기화 스크립트 출력:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"초기화 스크립트 오류:\n{e.stderr}")
    else:
        print(f"초기화 스크립트를 찾을 수 없음: {init_script}")
        
except Exception as e:
    error_msg = f"초기화 중 오류 발생: {str(e)}"
    print(error_msg)
    logger.error(error_msg)
    st.error(f"**관리자 권한이 필요할 수 있습니다:** {error_msg}")

try:
    # Import the main application module
    from app.ui.main import run_app
    
    # Run the application
    run_app()
    
except Exception as e:
    error_msg = f"앱 실행 중 오류 발생: {str(e)}"
    print(error_msg)
    logger.error(error_msg)
    st.error(f"**오류 발생:** {error_msg}\n\n상세 오류를 확인하려면 로그를 확인하세요.")
    
    # 트레이스백 출력
    import traceback
    tb = traceback.format_exc()
    st.code(tb) 