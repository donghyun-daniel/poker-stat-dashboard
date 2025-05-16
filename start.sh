#!/bin/bash

# 실행 환경 준비
echo "가상 환경 활성화 중..."
source venv/bin/activate

# 필요한 패키지 확인
echo "필요한 패키지 설치 확인 중..."
pip install -r requirements.txt

# 백그라운드에서 FastAPI 서버 실행
echo "FastAPI 서버 시작 중..."
python main.py &
FASTAPI_PID=$!

# 잠시 대기하여 서버가 시작되도록 함
sleep 2

# Streamlit 앱 실행
echo "Streamlit 앱 시작 중..."
python run_streamlit.py &
STREAMLIT_PID=$!

# 프로세스 ID 저장
echo "FastAPI PID: $FASTAPI_PID" > pids.txt
echo "Streamlit PID: $STREAMLIT_PID" >> pids.txt

echo "====================================================="
echo "포커 통계 대시보드가 성공적으로 시작되었습니다!"
echo "FastAPI: http://localhost:8000"
echo "Streamlit Dashboard: http://localhost:8501"
echo "====================================================="
echo "종료하려면 Ctrl+C를 누르거나 './stop.sh'를 실행하세요."

# Ctrl+C가 눌렸을 때 프로세스 종료
trap "kill $FASTAPI_PID $STREAMLIT_PID; echo '서비스가 종료되었습니다.'; exit" INT

# 메인 프로세스 실행 유지
wait 