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

# Add path to the project root to allow imports from app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Show a simple loading message while the app initializes
st.set_page_config(
    page_title="🃏 Poker Stats Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    # Import the main application module
    from app.ui.main import run_app
    
    # Run the application
    run_app()
    
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Please make sure all dependencies are installed correctly.")
    st.code("pip install -r requirements.txt")
    
except Exception as e:
    st.error(f"Error starting the application: {e}")
    st.info("Please check the logs for more details.") 