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
    ENTRY_FEE = 5000  # 5,000 won per player
    FREE_REBUYS = 2   # First 2 rebuys are free
    REBUY_FEE = 5000  # 5,000 won for each additional rebuy (3rd and beyond)
    
    # Get total players
    player_count = len(players_df)
    
    # Calculate total prize pool
    total_prize_pool = player_count * ENTRY_FEE  # Base entry fees
    
    # Debug information about rebuy counts
    st.expander("Rebuy Details", expanded=False).dataframe(
        players_df[['Player', 'Total Rebuy-in', 'Rebuy Count']]
    )
    
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
        # - p1 > p2 > ... > pn with equal differences (p1-p2 = p2-p3 = ... = p(n-1)-pn)
        
        # For n players, we need to find d where:
        # p1 = pn + (n-1)d
        # And p1 + p2 + ... + pn = 100
        # This gives us: n*pn + (n-1)*n*d/2 = 100
        
        # Set minimum percentage (could be 0, but setting to a small value ensures everyone gets something)
        min_percentage = 5.0 if player_count <= 4 else 0.0
        
        # Calculate common difference
        common_diff = (100 - player_count * min_percentage) * 2 / (player_count * (player_count - 1))
        
        # Calculate percentages for each rank
        percentages = {}
        for rank in range(1, player_count + 1):
            # Last place gets min_percentage, first place gets the most
            percentage = min_percentage + (player_count - rank) * common_diff
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
    
    # Calculate rebuy count - use a better estimation method
    # The first buy-in doesn't count as a rebuy
    initial_buyin = players_df['Total Rebuy-in'].min()
    
    # If players have different rebuy amounts, calculate rebuys
    if players_df['Total Rebuy-in'].nunique() > 1:
        # Count rebuys assuming each rebuy is the same as initial buy-in
        # But don't count the first buy-in
        players_df['Rebuy Count'] = (players_df['Total Rebuy-in'] / initial_buyin - 1).apply(lambda x: max(int(x), 0))
    else:
        # If everyone has the same buy-in and no rebuys, set count to 0
        players_df['Rebuy Count'] = 0
    
    # Calculate win rate - round to exactly 2 decimal places and convert to string to ensure display format
    players_df['Win Rate (%)'] = players_df.apply(
        lambda row: f"{(row['Wins'] / row['Hands'] * 100):.2f}" if row['Hands'] > 0 else "0.00", 
        axis=1
    )
    
    # Convert win rate back to float for sorting
    players_df['Win Rate (%)'] = players_df['Win Rate (%)'].astype(float)
    
    # Calculate prize distribution
    prize_distribution, prize_percentages, total_prize_pool = calculate_prize_distribution(players_df)
    
    # Add prize to each player
    players_df['Prize %'] = players_df['Rank'].map(lambda x: prize_percentages.get(x, 0))
    players_df['Total Prize'] = players_df['Rank'].map(lambda x: prize_distribution.get(x, 0))
    
    # Format prize percentage as string with 2 decimal places
    players_df['Prize %'] = players_df['Prize %'].apply(lambda x: f"{x:.2f}%")
    
    # Show prize pool information
    st.caption(f"Total Prize Pool: {total_prize_pool:,} won (Entry: 5,000 won, Additional rebuys: 5,000 won from 3rd rebuy)")
    
    # Highlight positive values in green and negative values in red
    def color_values(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
        return ''
    
    # Select columns to display in the table with the new order
    display_cols = ['Rank', 'Player', 'Wins', 'Win Rate (%)', 'Final Chips', 'Total Rebuy-in', 'Income', 'Prize %', 'Total Prize']
    
    # Display DataFrame - without index
    st.dataframe(
        players_df[display_cols].set_index('Rank').style.applymap(
            color_values, 
            subset=['Income', 'Total Prize']
        ),
        use_container_width=True,
        height=180
    )
    
    # Add option to see full details including rebuy counts
    with st.expander("Show Detailed Statistics", expanded=False):
        st.dataframe(
            players_df[['Player', 'Rank', 'Total Rebuy-in', 'Rebuy Count', 'Hands', 'Wins', 'Income', 'Prize %', 'Total Prize']]
        )
        st.write("Note: Rebuy counts exclude the initial entry (first buy-in is not counted as a rebuy)")
    
    # Display prize distribution calculations
    with st.expander("Prize Distribution Details", expanded=False):
        prize_df = pd.DataFrame({
            'Rank': list(prize_percentages.keys()),
            'Player': [players_df.loc[players_df['Rank'] == r, 'Player'].values[0] for r in prize_percentages.keys()],
            'Percentage': [f"{p:.2f}%" for p in prize_percentages.values()],
            'Prize Amount': [f"{prize_distribution[r]:,} won" for r in prize_percentages.keys()]
        })
        st.dataframe(prize_df)
        
        # Show total percentage to verify it adds up to 100%
        total_pct = sum(prize_percentages.values())
        st.write(f"Total percentage: {total_pct:.2f}% (should be 100%)")
        
        # Show prize allocation method
        st.write("Prize allocation method:")
        st.write("- Percentages are calculated in equal intervals")
        st.write("- Prize amounts for 2nd place and lower are truncated to the nearest 100 won")
        st.write("- 1st place receives the remainder to ensure total matches pool exactly")
        
        # Show total prize pool breakdown
        st.write(f"Base entry fees: {len(players_df) * 5000:,} won ({len(players_df)} players × 5,000 won)")
        
        extra_rebuys = 0
        for _, player in players_df.iterrows():
            if player['Rebuy Count'] > FREE_REBUYS:
                extra_rebuys += (player['Rebuy Count'] - FREE_REBUYS)
                
        st.write(f"Additional rebuy fees: {extra_rebuys * 5000:,} won ({extra_rebuys} extra rebuys × 5,000 won)")
        st.write(f"Total prize pool: {total_prize_pool:,} won")
        
        # Verify totals match
        total_prizes = sum(prize_distribution.values())
        st.write(f"Sum of all prizes: {total_prizes:,} won (should match total prize pool)")
        if total_prizes != total_prize_pool:
            st.error(f"Error: Prize sum ({total_prizes:,}) doesn't match prize pool ({total_prize_pool:,})")
    
    st.caption("* Win Rate (%) = (Wins / Hands) × 100")
    st.caption("* Prize distribution calculated using arithmetic sequence with percentages summing to 100%")

if __name__ == "__main__":
    main() 