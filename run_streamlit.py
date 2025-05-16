import streamlit.web.cli as stcli
import sys
import os

if __name__ == "__main__":
    # 현재 파일의 디렉토리 경로 구하기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Streamlit 앱 파일 경로
    streamlit_app_path = os.path.join(current_dir, "app", "streamlit_app.py")
    
    # 명령행 인자 설정
    sys.argv = [
        "streamlit", 
        "run", 
        streamlit_app_path,
        "--server.port=8501", 
        "--server.address=0.0.0.0"
    ]
    
    # Streamlit 실행
    sys.exit(stcli.main()) 