#!/usr/bin/env python3
"""
데이터 디렉토리를 초기화하는 스크립트
"""

import os
import sys

def main():
    print("데이터 디렉토리 초기화 중...")
    
    # 현재 디렉토리 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"현재 디렉토리: {current_dir}")
    
    # 데이터 디렉토리 생성
    data_dir = os.path.join(current_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"데이터 디렉토리 생성됨: {data_dir}")
    else:
        print(f"데이터 디렉토리가 이미 존재함: {data_dir}")
    
    # 권한 설정
    try:
        os.chmod(data_dir, 0o777)
        print("데이터 디렉토리 권한 설정 완료")
    except Exception as e:
        print(f"권한 설정 중 오류 발생: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 