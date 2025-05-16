import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import os
import io

st.set_page_config(
    page_title="Poker Stats Dashboard",
    page_icon="🃏",
    layout="wide"
)

def main():
    st.title("🃏 Poker Stats Dashboard")
    st.write("포커 게임 로그 파일을 업로드하고 통계를 확인하세요.")
    
    # 파일 업로더
    uploaded_file = st.file_uploader("포커 로그 파일 선택 (CSV)", type=['csv'])
    
    if uploaded_file is not None:
        with st.spinner("로그 파일 분석 중..."):
            # API에 파일 전송
            api_url = os.environ.get("API_URL", "http://localhost:8000/api/upload-log")
            
            try:
                # API 호출
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                response = requests.post(api_url, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    display_results(data)
                else:
                    st.error(f"API 오류: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"API 연결 오류: {str(e)}")
    
    st.divider()
    st.caption("Poker Stats Dashboard © 2025")

def display_results(data):
    """분석 결과를 보기 좋게 표시합니다."""
    
    st.success("분석 완료!")
    
    # 게임 정보
    col1, col2, col3 = st.columns(3)
    
    start_time = datetime.fromisoformat(data['game_period']['start'].replace('Z', ''))
    end_time = datetime.fromisoformat(data['game_period']['end'].replace('Z', ''))
    duration = end_time - start_time
    
    with col1:
        st.metric("게임 시작", start_time.strftime("%Y-%m-%d %H:%M"))
    with col2:
        st.metric("게임 종료", end_time.strftime("%Y-%m-%d %H:%M"))
    with col3:
        st.metric("총 핸드 수", data['total_hands'])
    
    st.write(f"게임 진행 시간: {duration}")
    
    # 플레이어 정보를 데이터프레임으로 변환
    players_df = pd.DataFrame(data['players'])
    
    # 데이터프레임 컬럼 이름 변경
    players_df = players_df.rename(columns={
        'user_name': '플레이어',
        'rank': '순위',
        'total_rebuy_amt': '총 리바이 금액',
        'total_win_cnt': '승리 횟수',
        'total_hand_cnt': '참여 핸드 수',
        'total_chip': '최종 칩',
        'total_income': '수익/손실'
    })
    
    # 플레이어 정보 표시
    st.subheader("플레이어 통계")
    
    # 음수 값 빨간색으로 표시
    def highlight_negative(val):
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'
    
    # 데이터프레임 스타일링
    styled_df = players_df.style.applymap(
        highlight_negative, 
        subset=['수익/손실']
    )
    
    st.dataframe(styled_df)
    
    # 수익/손실 차트
    st.subheader("수익/손실 분석")
    chart_data = players_df[['플레이어', '수익/손실']].set_index('플레이어')
    st.bar_chart(chart_data)
    
    # 승률 계산 및 차트
    st.subheader("승률 분석")
    players_df['승률'] = (players_df['승리 횟수'] / players_df['참여 핸드 수'] * 100).round(2)
    win_rate_data = players_df[['플레이어', '승률']].set_index('플레이어')
    st.bar_chart(win_rate_data)

if __name__ == "__main__":
    main() 