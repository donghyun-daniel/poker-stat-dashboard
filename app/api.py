import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.parsers.poker_now_parser import parse_log_file

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Poker Stats API",
    description="API for analyzing poker game logs and retrieving statistics",
    version="1.0.0"
)

# CORS 설정 - 필요에 따라 조정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 출처만 허용하도록 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """API 상태 확인을 위한 엔드포인트"""
    return {"status": "online", "message": "Poker Stats API is running"}

@app.post("/api/upload-log")
async def upload_log_file(file: UploadFile = File(...)):
    """
    포커 로그 파일을 업로드하고 분석 결과를 반환합니다.
    
    - **file**: CSV 형식의 포커 로그 파일
    
    반환값:
    - 게임 기간
    - 플레이어 통계 및 순위
    - 총 핸드 수
    """
    try:
        # 파일 확장자 확인
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="CSV 파일만 허용됩니다.")
        
        logger.info(f"파일 업로드: {file.filename}")
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        try:
            # 로그 파일 분석
            logger.info(f"로그 파일 분석 시작: {temp_file_path}")
            result = parse_log_file(temp_file_path)
            logger.info("로그 파일 분석 완료")
            
            # 임시 파일 삭제
            os.unlink(temp_file_path)
            
            return JSONResponse(content=result)
            
        except Exception as e:
            logger.error(f"로그 파일 분석 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"로그 파일 분석 중 오류 발생: {str(e)}")
        
    except Exception as e:
        logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}")

# 추가 엔드포인트는 필요에 따라 구현 