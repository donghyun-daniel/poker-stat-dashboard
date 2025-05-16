import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="CSV 파일 업로더",
    page_icon="📊"
)

st.title("📊 CSV 파일 업로더")
st.write("CSV 파일을 업로드하고 내용을 확인하세요.")

uploaded_file = st.file_uploader("CSV 파일 선택", type=['csv'])

if uploaded_file is not None:
    # 파일 저장
    with open(os.path.join("uploaded_file.csv"), "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"파일 '{uploaded_file.name}'이 성공적으로 업로드되었습니다!")
    
    # 데이터프레임으로 읽기
    try:
        df = pd.read_csv(uploaded_file)
        st.write("### 파일 내용 미리보기:")
        st.dataframe(df.head(10))
        
        st.write("### 파일 정보:")
        st.write(f"- 행: {df.shape[0]}")
        st.write(f"- 열: {df.shape[1]}")
        
        if st.button("전체 데이터 표시"):
            st.dataframe(df)
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}") 