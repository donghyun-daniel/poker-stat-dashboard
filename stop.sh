#!/bin/bash

# PID 파일이 존재하는지 확인
if [ ! -f pids.txt ]; then
    echo "PID 파일이 없습니다. 서비스가 실행 중이 아닌 것 같습니다."
    exit 1
fi

# PID 파일에서 프로세스 ID 읽기
FASTAPI_PID=$(grep "FastAPI PID" pids.txt | awk '{print $3}')
STREAMLIT_PID=$(grep "Streamlit PID" pids.txt | awk '{print $3}')

# 프로세스 종료
echo "서비스 종료 중..."

if [ ! -z "$FASTAPI_PID" ]; then
    kill $FASTAPI_PID 2>/dev/null || true
    echo "FastAPI 서버 종료됨 (PID: $FASTAPI_PID)"
fi

if [ ! -z "$STREAMLIT_PID" ]; then
    kill $STREAMLIT_PID 2>/dev/null || true
    echo "Streamlit 앱 종료됨 (PID: $STREAMLIT_PID)"
fi

# PID 파일 삭제
rm pids.txt

echo "모든 서비스가 종료되었습니다." 