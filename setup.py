#!/usr/bin/env python3
"""
Setup script for Poker Stats Dashboard.
This script is used to setup a correct environment for running the Streamlit app.
"""

import os
import sys
import site
import importlib.util

# Python 3.12용 distutils 패치 설정
def setup_distutils_patch():
    """Python 3.12에서 distutils 모듈 패치 설정"""
    if sys.version_info >= (3, 12):
        try:
            # setuptools 패키지 경로 확인
            setuptools_path = None
            for path in site.getsitepackages():
                potential_path = os.path.join(path, "setuptools")
                if os.path.exists(potential_path):
                    setuptools_path = potential_path
                    break
            
            if setuptools_path:
                # distutils 패치 적용
                distutils_path = os.path.join(setuptools_path, "_distutils")
                if os.path.exists(distutils_path):
                    # 모듈 심볼릭 링크 생성 (파이썬 내부)
                    if 'distutils' not in sys.modules:
                        sys.modules['distutils'] = importlib.import_module('setuptools._distutils')
                    if 'distutils.version' not in sys.modules:
                        sys.modules['distutils.version'] = importlib.import_module('setuptools._distutils.version')
                    
                    print("✅ Successfully applied distutils patch for Python 3.12")
                    return True
            
            print("⚠️ Could not locate setuptools path for distutils patch")
        except Exception as e:
            print(f"⚠️ Error setting up distutils patch: {e}")
    
    return False

if __name__ == "__main__":
    # Python 버전 확인
    print(f"Running setup for Python {sys.version}")
    
    # distutils 패치 적용
    if sys.version_info >= (3, 12):
        setup_distutils_patch()
    
    # 데이터 디렉토리 생성
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✅ Created data directory: {data_dir}")
    else:
        print(f"ℹ️ Data directory already exists: {data_dir}")
    
    print("✅ Setup completed successfully!") 