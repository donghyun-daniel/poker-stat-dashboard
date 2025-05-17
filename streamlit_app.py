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
    [data-testid="stDataFrame"] th:nth-child(8),
    [data-testid="stDataFrame"] th:nth-child(9) {
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
    
    st.divider()
    st.caption("Poker Stats Dashboard © 2025")

def calculate_prize_distribution(players_df):
    """Calculate the prize distribution based on specified rules."""
    
    # Constants
    ENTRY_FEE = 4000  # 4,000 won per player
    FREE_REBUYS = 2   # First 2 rebuys are free
    REBUY_FEE = 4000  # 4,000 won for each additional rebuy (3rd and beyond)
    
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
    
    # Calculate prize distribution percentages in arithmetic sequence
    if player_count > 1:
        # Calculate the common difference for the arithmetic sequence
        # If we have n players, and want percentages p1, p2, ..., pn where:
        # - The sum p1 + p2 + ... + pn = 100%
        # - pn = 0 (last place gets 0%)
        # - p1 > p2 > ... > p(n-1) > pn = 0 with equal differences
        
        # For arithmetic sequence with last term = 0:
        # p1, p2, ..., p(n-1), pn = 0
        # Common difference = d
        # p1 = (n-1)d
        # The sum: n/2 * [(n-1)d + 0] = 100%
        # (n-1)nd/2 = 100
        # d = 200 / (n(n-1))
        
        # Calculate common difference for equal interval percentages
        common_diff = 200 / (player_count * (player_count - 1))
        
        # Calculate percentages for each rank
        percentages = {}
        for rank in range(1, player_count + 1):
            # Last place gets 0%, first place gets the most
            if rank == player_count:
                # Last place always gets 0%
                percentage = 0
            else:
                # Others get percentages in equal intervals
                percentage = (player_count - rank) * common_diff
            
            percentages[rank] = round(percentage, 2)
            
        # Adjust to ensure sum is exactly 100%
        total_pct = sum(percentages.values())
        if abs(total_pct - 100) > 0.01:  # If not very close to 100%
            # Adjust first place to make sum exactly 100%
            percentages[1] = round(percentages[1] + (100 - total_pct), 2)
            
        # Calculate prize amounts - truncate to nearest 100 won
        prizes = {}
        prize_percentages = {}
        total_truncated = 0
        
        for rank in range(1, player_count + 1):
            percentage = percentages[rank]
            # Calculate exact amount
            exact_prize = total_prize_pool * percentage / 100
            # Truncate to nearest 100 won (floor to hundreds)
            truncated_prize = int(exact_prize // 100 * 100)
            
            if rank > 1:  # For all except first place
                prizes[rank] = truncated_prize
                total_truncated += truncated_prize
            
            prize_percentages[rank] = percentage
        
        # First place gets the remainder to ensure total matches pool exactly
        prizes[1] = total_prize_pool - total_truncated
        
        return prizes, prize_percentages, total_prize_pool
        
    else:
        # If there's only one player, they get the entire pool (100%)
        return {1: total_prize_pool}, {1: 100.0}, total_prize_pool

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
    
    # Display game info in a compact format
    st.markdown(f"**{start_time} ~ {end_time} ({duration_text})**", unsafe_allow_html=True)
    
    # Create DataFrame for player stats
    players_df = pd.DataFrame(data['players'])
    
    # Sort by rank
    players_df = players_df.sort_values(by='rank')
    
    # Rename columns and select needed columns
    players_df = players_df.rename(columns={
        'user_name': 'Player',
        'rank': 'Rank',
        'total_rebuy_amt': 'Rebuy-in Count',
        'total_win_cnt': 'Wins',
        'total_hand_cnt': 'Hands',
        'total_chip': 'Final Chips',
        'total_income': 'Income'
    })
    
    # Calculate rebuy count based on the total rebuy amount from parser
    # The parser now simply counts the number of times a player joined the game
    # The first join is the initial buy-in, all subsequent joins are rebuys
    # The total_rebuy_amt from parser is initial_buyin * (1 + rebuy_count)
    # So rebuy count = (total_rebuy_amt / initial_buyin) - 1
    players_df['Rebuy Count'] = (players_df['Rebuy-in Count'] / 20000 - 1).apply(lambda x: max(int(round(x)), 0))
    
    # Add a note about the rebuy count meaning
    st.caption("* Rebuy Count: Number of times a player rejoined the game after the initial buy-in")
    
    # 각 플레이어별 참가 금액 계산 (기본 ENTRY_FEE + 추가 리바이인)
    ENTRY_FEE = 4000  # 4,000 won per player
    FREE_REBUYS = 2   # First 2 rebuys are free
    REBUY_FEE = 4000  # 4,000 won for each additional rebuy (3rd and beyond)
    
    players_df['Entry Fee'] = ENTRY_FEE
    players_df['Additional Fee'] = players_df['Rebuy Count'].apply(
        lambda x: max(0, x - FREE_REBUYS) * REBUY_FEE
    )
    players_df['Total Fee'] = players_df['Entry Fee'] + players_df['Additional Fee']
    
    # 참가 금액별로 정렬 (큰 금액순, 같은 금액은 이름순)
    fee_df = players_df[['Player', 'Total Fee', 'Entry Fee', 'Additional Fee', 'Rebuy Count']].copy()
    fee_df = fee_df.sort_values(by=['Total Fee', 'Player'], ascending=[False, True])
    
    # Calculate prize distribution
    prize_distribution, prize_percentages, total_prize_pool = calculate_prize_distribution(players_df)
    
    # Add prize pool info to game information section
    st.markdown(f"**Prize Pool: {total_prize_pool:,} won**", unsafe_allow_html=True)
    
    # Show player fee contributions
    st.markdown("**Player Contributions:**")
    
    # 금액에 콤마 추가하여 표시
    fee_df['Total Fee'] = fee_df['Total Fee'].apply(lambda x: f"{x:,} won")
    fee_df['Entry Fee'] = fee_df['Entry Fee'].apply(lambda x: f"{x:,} won")
    fee_df['Additional Fee'] = fee_df['Additional Fee'].apply(lambda x: f"{x:,} won")
    
    # 소형 테이블로 참가 금액 표시
    st.dataframe(
        fee_df[['Player', 'Total Fee', 'Entry Fee', 'Additional Fee', 'Rebuy Count']],
        use_container_width=True,
        height=min(150, len(fee_df) * 35 + 38)  # 플레이어 수에 따라 높이 조정
    )
    
    st.divider()
    
    # Display player information
    st.subheader("Player Statistics")
    
    # Calculate win rate - round to exactly 2 decimal places and convert to string to ensure display format
    players_df['Win Rate (%)'] = players_df.apply(
        lambda row: f"{(row['Wins'] / row['Hands'] * 100):.2f}" if row['Hands'] > 0 else "0.00", 
        axis=1
    )
    
    # Convert win rate back to float for sorting
    players_df['Win Rate (%)'] = players_df['Win Rate (%)'].astype(float)
    
    # Add prize to each player
    players_df['Prize %'] = players_df['Rank'].map(lambda x: prize_percentages.get(x, 0))
    players_df['Total Prize'] = players_df['Rank'].map(lambda x: prize_distribution.get(x, 0))
    
    # Format prize percentage as string with 2 decimal places
    players_df['Prize %'] = players_df['Prize %'].apply(lambda x: f"{x:.2f}%")
    
    # Highlight positive values in green and negative values in red
    def color_values(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
        return ''
    
    # Select columns to display in the table with the new order - removing Prize columns
    display_cols = ['Rank', 'Player', 'Wins', 'Win Rate (%)', 'Final Chips', 'Rebuy Count', 'Income']
    
    # Display DataFrame - without index
    st.dataframe(
        players_df[display_cols].set_index('Rank').style.applymap(
            color_values, 
            subset=['Income']
        ),
        use_container_width=True,
        height=180
    )
    
    st.caption("* Win Rate (%) = (Wins / Hands) × 100")
    st.caption("* Rebuy Count = Number of times a player rejoined the game after the initial buy-in")
    
    # Add new Player Prize Statistics section
    st.divider()
    st.subheader("Player Prize Statistics")
    
    # Create a copy of the dataframe for prize calculations
    prize_df = players_df.copy()
    
    # Calculate Net Prize (Prize - Total Fee)
    prize_df['Net Prize'] = prize_df['Total Prize'] - prize_df['Total Fee']
    
    # Create prize table columns
    prize_cols = ['Rank', 'Player', 'Prize %', 'Total Prize', 'Net Prize']
    
    # Apply colorization function for prize table
    def prize_color_values(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
        return ''
    
    # Make a copy to avoid modifying the original dataframe
    display_prize_df = prize_df[prize_cols].copy()
    
    # Format prize amounts with commas after calculations
    display_prize_df['Total Prize'] = display_prize_df['Total Prize'].apply(lambda x: f"{x:,} won")
    display_prize_df['Net Prize'] = display_prize_df['Net Prize'].apply(lambda x: f"{x:,} won")
    
    # Display prize statistics
    st.dataframe(
        display_prize_df.set_index('Rank').style.applymap(
            prize_color_values,
            subset=['Net Prize']
        ),
        use_container_width=True,
        height=180
    )
    
    st.caption("* Prize % = Percentage of the prize pool")
    st.caption("* Net Prize = Prize amount minus entry fees")

if __name__ == "__main__":
    main() 