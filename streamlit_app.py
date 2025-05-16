import streamlit as st
import pandas as pd
import os
import tempfile
import sys
from pathlib import Path

# 모듈 import를 위한 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 포커 파서 import
try:
    from app.parsers.poker_now_parser import parse_log_file
except ImportError:
    # Streamlit Cloud를 위한 상대 경로 설정
    if os.path.exists(os.path.join(current_dir, "app", "parsers", "poker_now_parser.py")):
        from app.parsers.poker_now_parser import parse_log_file
    else:
        st.error("포커 파서 모듈을 찾을 수 없습니다.")

# 페이지 설정
st.set_page_config(
    page_title="포커 통계 대시보드",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="collapsed"  # 사이드바 초기 상태: 축소
)

# 모바일 친화적 CSS 추가
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        font-size: 1.4rem !important;
        margin-bottom: 0.3rem !important;
    }
    h3 {
        font-size: 1.2rem !important;
    }
    .stDataFrame {
        font-size: 0.8rem !important;
    }
    .stBar, .stBarChart {
        height: auto !important;
    }
    /* 모바일에서 파일 업로드 버튼 스타일 */
    .stFileUploader label {
        width: 100% !important;
        padding: 0.5rem !important;
    }
    .stFileUploader button {
        width: 100% !important;
        padding: 0.5rem !important;
    }
    /* 메트릭 크기 조정 */
    .stMetric {
        padding: 0.5rem !important;
    }
    /* 차트 높이 제한 */
    [data-testid="stArrowVegaLiteChart"] {
        max-height: 250px !important;
    }
    @media (max-width: 768px) {
        .row-widget.stButton {
            width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🃏 포커 통계 대시보드")
    st.write("PokerNow 로그 파일을 업로드하고 통계를 확인하세요.")
    
    # 모바일 친화적 파일 업로더
    uploaded_file = st.file_uploader("포커 로그 파일 선택 (CSV)", type=['csv'], help="PokerNow에서 다운로드한 CSV 형식의 로그 파일을 업로드하세요.")
    
    # 샘플 파일 업로드 옵션 (선택 사항)
    st.caption("CSV 파일이 없으신가요? [샘플 파일 다운로드](https://github.com/donghyun-daniel/poker-stat-dashboard/raw/main/sample_poker_log.csv)")
    
    if uploaded_file is not None:
        # 파일 처리 시작
        with st.spinner("파일 분석 중..."):
            try:
                # 임시 파일로 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                    temp_file_path = temp_file.name
                    temp_file.write(uploaded_file.getvalue())
                
                # 포커 로그 파일 분석
                result = parse_log_file(temp_file_path)
                
                # 임시 파일 삭제
                os.unlink(temp_file_path)
                
                # 분석 결과 표시
                display_results(result)
                
            except Exception as e:
                st.error(f"파일 분석 중 오류가 발생했습니다: {str(e)}")
                # 에러 로그 표시
                st.exception(e)
    
    # 기본 CSV 파일 형식 안내 - 모바일에서는 작게 표시
    with st.expander("💡 PokerNow 로그 파일 형식 안내"):
        st.write("""
        PokerNow에서 다운로드한 CSV 로그 파일을 업로드하세요.
        일반적으로 파일 이름은 `poker_now_log_xxxxx.csv` 형식입니다.
        """)
        
        st.code("""
        "entry","timestamp","at"
        "The player ""player1 @ a1b2c3"" joined the game with a stack of 1000","2023-01-01 12:00:00.000","0"
        "The player ""player2 @ d4e5f6"" joined the game with a stack of 1000","2023-01-01 12:00:05.000","1"
        """, language="csv")
    
    st.divider()
    st.caption("Poker Stats Dashboard © 2025")

def display_results(data):
    """분석 결과를 시각적으로 표시합니다."""
    
    st.success("✅ 분석 완료!")
    
    # 탭으로 구성하여 모바일에서도 보기 좋게 구성
    tab1, tab2, tab3 = st.tabs(["📊 기본 정보", "📈 플레이어 통계", "🏆 승률/핸드 분석"])
    
    with tab1:
        # 게임 정보 표시를 작게 조정
        st.subheader("게임 정보")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("게임 시작", data['game_period']['start'].strftime("%Y-%m-%d %H:%M"))
        with col2:
            st.metric("게임 종료", data['game_period']['end'].strftime("%Y-%m-%d %H:%M"))
        with col3:
            st.metric("총 핸드 수", data['total_hands'])
        
        duration = data['game_period']['end'] - data['game_period']['start']
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        st.write(f"게임 진행 시간: {int(hours)}시간 {int(minutes)}분")
    
    with tab2:
        # 플레이어 정보 표시
        st.subheader("플레이어 통계")
        
        # 데이터프레임 생성
        players_df = pd.DataFrame(data['players'])
        players_df = players_df.rename(columns={
            'user_name': '플레이어',
            'rank': '순위',
            'total_rebuy_amt': '총 리바이',
            'total_win_cnt': '승리',
            'total_hand_cnt': '핸드',
            'total_chip': '최종 칩',
            'total_income': '수익/손실'
        })
        
        # 승률 계산
        players_df['승률 %'] = (players_df['승리'] / players_df['핸드'] * 100).round(1)
        
        # 음수 값 빨간색으로 표시
        def highlight_negative(val):
            color = 'red' if isinstance(val, (int, float)) and val < 0 else 'black'
            return f'color: {color}'
        
        # 데이터프레임 표시 - 컬럼 선택하여 간결하게
        display_cols = ['플레이어', '순위', '총 리바이', '최종 칩', '수익/손실', '승률 %']
        st.dataframe(
            players_df[display_cols].style.applymap(
                highlight_negative, 
                subset=['수익/손실']
            ), 
            use_container_width=True,
            height=150  # 높이 제한
        )
        
        # 모바일에서 잘 보이도록 컴팩트한 차트
        st.subheader("수익/손실 분석")
        chart_data = players_df[['플레이어', '수익/손실']].set_index('플레이어')
        st.bar_chart(chart_data, height=200)
    
    with tab3:
        # 승률 차트
        st.subheader("승률 분석")
        win_rate_data = players_df[['플레이어', '승률 %']].set_index('플레이어')
        st.bar_chart(win_rate_data, height=200)
        
        # 참여 핸드 비교
        st.subheader("참여 핸드 분석")
        hands_data = players_df[['플레이어', '핸드']].set_index('플레이어')
        st.bar_chart(hands_data, height=200)

if __name__ == "__main__":
    main() 