"""Poker Statistics Dashboard Application."""

# 데이터 디렉토리 생성 확인
import os

# 프로젝트 루트 디렉토리 확인
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 데이터 디렉토리 생성
data_dir = os.path.join(root_dir, "data")
if not os.path.exists(data_dir):
    try:
        os.makedirs(data_dir)
        print(f"데이터 디렉토리 생성됨: {data_dir}")
    except Exception as e:
        print(f"데이터 디렉토리 생성 중 오류 발생: {e}") 