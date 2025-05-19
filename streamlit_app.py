"""
Streamlit application entry point for the Poker Stats Dashboard.
This file serves as the main entry point for running the application.
"""

import os
import sys
import streamlit as st

# Python 3.12에서 distutils 문제 해결을 위한 초기화
try:
    # setuptools가 있는지 확인하고 distutils에 대한 호환성 패치 적용
    import importlib
    if sys.version_info >= (3, 12):
        # setuptools의 필요 경로 설정
        major, minor = sys.version_info[:2]
        import site
        sys.path.append(os.path.join(site.getsitepackages()[0], f"setuptools/_distutils"))
        sys.path.append(os.path.join(site.getsitepackages()[0], f"setuptools"))
        
        # numpy와 pandas가 distutils 모듈을 찾지 못하는 문제 해결
        if not os.path.exists(os.path.join(site.getsitepackages()[0], "distutils")):
            sys.modules['distutils'] = importlib.import_module('setuptools._distutils')
            sys.modules['distutils.version'] = importlib.import_module('setuptools._distutils.version')
except Exception as e:
    print(f"Warning: Failed to apply distutils patch for Python 3.12: {e}")

# 기본 설정 및 초기화
st.set_page_config(
    page_title="🃏 Poker Stats Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 로딩 메시지 표시
st.markdown("## 🃏 Poker Stats Dashboard")
with st.spinner("애플리케이션을 초기화하는 중입니다..."):
    # 프로젝트 경로 설정
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 데이터 디렉토리 확인 및 생성
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    try:
        # 메인 애플리케이션 모듈 가져오기
        from app.ui.main import run_app
        
        # 애플리케이션 실행
        run_app()
        
    except ImportError as e:
        st.error(f"필요한 모듈을 가져올 수 없습니다: {e}")
        st.info("모든 의존성이 올바르게 설치되었는지 확인하세요.")
        st.code("pip install -r requirements.txt")
        
    except Exception as e:
        st.error(f"애플리케이션 시작 중 오류가 발생했습니다: {e}")
        st.info("자세한 내용은 로그를 확인하세요.")
        # 오류 세부 정보 표시
        st.exception(e) 