#!/bin/bash

# 실행 환경 준비
echo "가상 환경 활성화 중..."
source venv/bin/activate

# pip 업데이트
echo "pip 업데이트 중..."
pip install --upgrade pip

# 필요한 패키지 설치
echo "필요한 패키지 설치 중..."
# setuptools와 wheel 먼저 설치
pip install --upgrade setuptools wheel

# Rich 패키지 먼저 설치 (Streamlit과 호환되는 버전으로)
echo "Rich 패키지 버전 설치 중..."
pip uninstall -y rich markdown-it-py
pip install rich==13.3.5 --no-deps
pip install markdown-it-py==2.2.0

# requirements.txt의 패키지들 설치 (rich 제외)
echo "필수 패키지 설치 중..."
grep -v "rich==" requirements.txt > temp_requirements.txt
pip install -r temp_requirements.txt
rm temp_requirements.txt

# Rich 호환성 최종 확인
echo "Rich 패키지 호환성 확인 중..."
RICH_VERSION=$(pip list | grep rich | awk '{print $2}')
if [ "$RICH_VERSION" != "13.3.5" ]; then
    echo "Rich 버전 불일치 감지. 올바른 버전으로 강제 설치 중..."
    pip uninstall -y rich
    pip install rich==13.3.5 --no-deps
    pip install markdown-it-py==2.2.0
fi

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