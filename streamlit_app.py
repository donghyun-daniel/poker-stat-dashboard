import streamlit as st
import pandas as pd
import os
import tempfile
import sys
from pathlib import Path
import numpy as np

# Set up path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import poker parser
try:
    from app.parsers.poker_now_parser import parse_log_file
except ImportError:
    # Setup relative path for Streamlit Cloud
    if os.path.exists(os.path.join(current_dir, "app", "parsers", "poker_now_parser.py")):
        from app.parsers.poker_now_parser import parse_log_file
    else:
        st.error("Poker parser module not found.")

# Page configuration
st.set_page_config(
    page_title="Poker Stats Dashboard",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar initial state: collapsed
)

# Mobile-friendly CSS
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
    /* Hide table index */
    .row_heading.level0 {
        display: none !important;
    }
    .index_name {
        display: none !important;
    }
    /* Mobile file upload button style */
    .stFileUploader label {
        width: 100% !important;
        padding: 0.5rem !important;
    }
    .stFileUploader button {
        width: 100% !important;
        padding: 0.5rem !important;
    }
    /* Metric size adjustment */
    .stMetric {
        padding: 0.5rem !important;
    }
    /* Game info text */
    .game-info {
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
    }
    @media (max-width: 768px) {
        .row-widget.stButton {
            width: 100% !important;
        }
    }
    /* Divider style */
    hr {
        margin: 1rem 0 !important;
    }
    /* Custom table column width */
    [data-testid="stDataFrame"] table {
        width: 100%;
    }
    [data-testid="stDataFrame"] th:nth-child(1) {
        min-width: 60px;
        max-width: 80px;
    }
    [data-testid="stDataFrame"] th:nth-child(2) {
        min-width: 140px;
        max-width: 200px;
    }
    [data-testid="stDataFrame"] th:nth-child(3) {
        min-width: 70px;
        max-width: 90px;
    }
    [data-testid="stDataFrame"] th:nth-child(4) {
        min-width: 90px;
        max-width: 110px;
    }
    [data-testid="stDataFrame"] th:nth-child(5), 
    [data-testid="stDataFrame"] th:nth-child(6) {
        min-width: 100px;
        max-width: 130px;
    }
    [data-testid="stDataFrame"] th:nth-child(7),
    [data-testid="stDataFrame"] th:nth-child(8) {
        min-width: 100px;
        max-width: 130px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🃏 Poker Stats Dashboard")
    st.write("Upload your PokerNow log file and view the statistics.")
    
    # Mobile-friendly file uploader
    uploaded_file = st.file_uploader("Select Poker Log File (CSV)", type=['csv'], help="Upload a CSV log file downloaded from PokerNow.")
    
    # Sample file download option
    st.caption("Don't have a CSV file? [Download Sample File](https://github.com/donghyun-daniel/poker-stat-dashboard/raw/main/sample_poker_log.csv)")
    
    if uploaded_file is not None:
        # Start file processing
        with st.spinner("Analyzing file..."):
            try:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                    temp_file_path = temp_file.name
                    temp_file.write(uploaded_file.getvalue())
                
                # Analyze poker log file
                result = parse_log_file(temp_file_path)
                
                # Delete temporary file
                os.unlink(temp_file_path)
                
                # Display analysis results
                display_results(result)
                
            except Exception as e:
                st.error(f"Error occurred during file analysis: {str(e)}")
                # Show error log
                st.exception(e)
    
    # CSV file format guidance - compact display on mobile
    with st.expander("💡 PokerNow Log File Format Guide"):
        st.write("""
        Upload a CSV log file downloaded from PokerNow.
        Typically, the file name follows the format `poker_now_log_xxxxx.csv`.
        """)
        
        st.code("""
        "entry","timestamp","at"
        "The player ""player1 @ a1b2c3"" joined the game with a stack of 1000","2023-01-01 12:00:00.000","0"
        "The player ""player2 @ d4e5f6"" joined the game with a stack of 1000","2023-01-01 12:00:05.000","1"
        """, language="csv")
    
    st.divider()
    st.caption("Poker Stats Dashboard © 2025")

def calculate_prize_distribution(players_df):
    """Calculate the prize distribution based on specified rules."""
    
    # Constants
    ENTRY_FEE = 4000  # 4,000 won per player
    FREE_REBUYS = 2   # First 2 rebuys are free
    REBUY_FEE = 5000  # 5,000 won for each additional rebuy (3rd and beyond)
    
    # Get total players
    player_count = len(players_df)
    
    # Calculate total prize pool
    total_prize_pool = player_count * ENTRY_FEE  # Base entry fees
    
    # Add additional rebuy fees to the prize pool
    for _, player in players_df.iterrows():
        rebuy_count = player['Rebuy Count']
        # Only charge for rebuys beyond the free limit
        if rebuy_count > FREE_REBUYS:
            additional_rebuys = rebuy_count - FREE_REBUYS
            total_prize_pool += additional_rebuys * REBUY_FEE
    
    # Calculate prize for each rank
    # For even distribution with equal intervals:
    # First place gets the largest prize, last place gets 0
    # The difference between consecutive ranks is constant
    if player_count > 1:
        interval = total_prize_pool / (player_count * (player_count - 1) / 2)
        prizes = {}
        
        for rank in range(1, player_count + 1):
            # Prize formula: decreases linearly with rank
            prize = int(interval * (player_count - rank))
            prizes[rank] = prize
            
        # Ensure total distributed prize matches the pool (handle rounding)
        total_distributed = sum(prizes.values())
        if total_distributed < total_prize_pool:
            # Add remainder to first place
            prizes[1] += (total_prize_pool - total_distributed)
        
        return prizes, total_prize_pool
    else:
        # If there's only one player, they get the entire pool
        return {1: total_prize_pool}, total_prize_pool

def display_results(data):
    """Display analysis results visually."""
    
    st.success("✅ Analysis Complete!")
    
    # Display compact game information
    st.subheader("Game Information")
    
    # Format date and time
    start_time = data['game_period']['start'].strftime("%Y-%m-%d %H:%M")
    end_time = data['game_period']['end'].strftime("%Y-%m-%d %H:%M")
    
    # Calculate duration
    duration = data['game_period']['end'] - data['game_period']['start']
    hours = duration.total_seconds() // 3600
    minutes = (duration.total_seconds() % 3600) // 60
    duration_text = f"{int(hours)}h {int(minutes)}m"
    
    # Get player names
    player_names = [player['user_name'] for player in data['players']]
    player_count = len(player_names)
    
    # Format player list with proper commas and spacing
    player_list = ", ".join(player_names)
    
    # Display game info in a compact format
    st.markdown(f"**{start_time} ~ {end_time} ({duration_text})**", unsafe_allow_html=True)
    st.markdown(f"**{player_count} players** - {player_list}", unsafe_allow_html=True)
    
    st.divider()
    
    # Display player information
    st.subheader("Player Statistics")
    
    # Create DataFrame
    players_df = pd.DataFrame(data['players'])
    
    # Sort by rank
    players_df = players_df.sort_values(by='rank')
    
    # Rename columns and select needed columns
    players_df = players_df.rename(columns={
        'user_name': 'Player',
        'rank': 'Rank',
        'total_rebuy_amt': 'Total Rebuy-in',
        'total_win_cnt': 'Wins',
        'total_hand_cnt': 'Hands',
        'total_chip': 'Final Chips',
        'total_income': 'Income'
    })
    
    # Count number of rebuy-ins (dividing by 1000, assuming each rebuy is 1000 chips)
    # We'll assume the first buy-in is also included in the total_rebuy_amt
    players_df['Rebuy Count'] = players_df['Total Rebuy-in'] // 1000
    
    # Calculate win rate - round to exactly 2 decimal places and convert to string to ensure display format
    players_df['Win Rate (%)'] = players_df.apply(
        lambda row: f"{(row['Wins'] / row['Hands'] * 100):.2f}" if row['Hands'] > 0 else "0.00", 
        axis=1
    )
    
    # Convert win rate back to float for sorting
    players_df['Win Rate (%)'] = players_df['Win Rate (%)'].astype(float)
    
    # Calculate prize distribution
    prize_distribution, total_prize_pool = calculate_prize_distribution(players_df)
    
    # Add prize to each player
    players_df['Total Prize'] = players_df['Rank'].map(lambda x: prize_distribution.get(x, 0))
    
    # Show prize pool information
    st.caption(f"Total Prize Pool: {total_prize_pool:,} won (Entry: 4,000 won, Additional rebuys: 5,000 won from 3rd rebuy)")
    
    # Highlight positive values in green and negative values in red
    def color_values(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
        return ''
    
    # Select columns to display in the table with the new order
    display_cols = ['Rank', 'Player', 'Wins', 'Win Rate (%)', 'Final Chips', 'Total Rebuy-in', 'Income', 'Total Prize']
    
    # Display DataFrame - without index
    st.dataframe(
        players_df[display_cols].set_index('Rank').style.applymap(
            color_values, 
            subset=['Income', 'Total Prize']
        ),
        use_container_width=True,
        height=180
    )
    
    st.caption("* Win Rate (%) = (Wins / Hands) × 100")
    st.caption("* Total Prize based on rank: 1st place receives the highest amount, decreasing by equal intervals to last place")

if __name__ == "__main__":
    main() 