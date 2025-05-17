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
    st.write("Upload your poker game log file and view the statistics.")
    
    # File uploader
    uploaded_file = st.file_uploader("Select a poker log file (CSV)", type=['csv'])
    
    if uploaded_file is not None:
        with st.spinner("Analyzing log file..."):
            # Send file to API
            api_url = os.environ.get("API_URL", "http://localhost:8000/api/upload-log")
            
            try:
                # API call
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                response = requests.post(api_url, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    display_results(data)
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"API Connection Error: {str(e)}")
    
    st.divider()
    st.caption("Poker Stats Dashboard © 2025")

def display_results(data):
    """Display analysis results in a user-friendly format."""
    
    st.success("Analysis Complete!")
    
    # Game information
    col1, col2, col3 = st.columns(3)
    
    start_time = datetime.fromisoformat(data['game_period']['start'].replace('Z', ''))
    end_time = datetime.fromisoformat(data['game_period']['end'].replace('Z', ''))
    duration = end_time - start_time
    
    with col1:
        st.metric("Game Start", start_time.strftime("%Y-%m-%d %H:%M"))
    with col2:
        st.metric("Game End", end_time.strftime("%Y-%m-%d %H:%M"))
    with col3:
        st.metric("Total Hands", data['total_hands'])
    
    st.write(f"Game Duration: {duration}")
    
    # Convert player information to DataFrame
    players_df = pd.DataFrame(data['players'])
    
    # Rename columns
    players_df = players_df.rename(columns={
        'user_name': 'Player',
        'rank': 'Rank',
        'total_rebuy_amt': 'Total Rebuy',
        'total_win_cnt': 'Wins',
        'total_hand_cnt': 'Hands Played',
        'total_chip': 'Final Chips',
        'total_income': 'Profit/Loss'
    })
    
    # Display player statistics
    st.subheader("Player Statistics")
    
    # Color negative values in red
    def highlight_negative(val):
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'
    
    # Style the DataFrame
    styled_df = players_df.style.map(
        highlight_negative, 
        subset=['Profit/Loss']
    )
    
    st.dataframe(styled_df)
    
    # Profit/Loss chart
    st.subheader("Profit/Loss Analysis")
    chart_data = players_df[['Player', 'Profit/Loss']].set_index('Player')
    st.bar_chart(chart_data)
    
    # Win rate calculation and chart
    st.subheader("Win Rate Analysis")
    players_df['Win Rate'] = (players_df['Wins'] / players_df['Hands Played'] * 100).round(2)
    win_rate_data = players_df[['Player', 'Win Rate']].set_index('Player')
    st.bar_chart(win_rate_data)

if __name__ == "__main__":
    main() 