"""Poker Statistics Dashboard Application."""

# 데이터 디렉토리 생성 확인
import os
import sys
import stat

# 프로젝트 루트 디렉토리 확인
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"프로젝트 루트 디렉토리: {root_dir}")

# 데이터 디렉토리 경로
data_dir = os.path.join(root_dir, "data")
print(f"데이터 디렉토리 경로: {data_dir}")

# 데이터 디렉토리 생성 및 권한 설정
if not os.path.exists(data_dir):
    try:
        os.makedirs(data_dir, exist_ok=True)
        print(f"데이터 디렉토리 생성됨: {data_dir}")
        
        # 모든 사용자에게 읽기/쓰기/실행 권한 부여 (777)
        os.chmod(data_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print(f"데이터 디렉토리 권한 설정 완료: {data_dir}")
    except Exception as e:
        print(f"데이터 디렉토리 설정 중 오류 발생: {e}")
else:
    print(f"데이터 디렉토리가 이미 존재함: {data_dir}")
    try:
        # 이미 존재하는 디렉토리의 권한 업데이트
        os.chmod(data_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        print(f"기존 데이터 디렉토리 권한 업데이트됨: {data_dir}")
    except Exception as e:
        print(f"권한 설정 중 오류 발생: {e}") 