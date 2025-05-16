import streamlit as st
import pandas as pd
import os
import tempfile
import sys
from pathlib import Path

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
    /* Compact game info */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
    }
    div[data-testid="metric-container"] {
        width: 100%;
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

def display_results(data):
    """Display analysis results visually."""
    
    st.success("✅ Analysis Complete!")
    
    # Display compact game information
    st.subheader("Game Information")
    col1, col2 = st.columns(2)
    
    # Calculate duration
    duration = data['game_period']['end'] - data['game_period']['start']
    hours = duration.total_seconds() // 3600
    minutes = (duration.total_seconds() % 3600) // 60
    duration_text = f"{int(hours)}h {int(minutes)}m"
    
    with col1:
        st.metric("Start", data['game_period']['start'].strftime("%Y-%m-%d %H:%M"))
    with col2:
        st.metric("End", data['game_period']['end'].strftime("%Y-%m-%d %H:%M"))
    
    st.caption(f"Game Duration: {duration_text}")
    
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
        'total_rebuy_amt': 'Total Rebuy',
        'total_win_cnt': 'Wins',
        'total_hand_cnt': 'Hands',
        'total_chip': 'Final Chips',
        'total_income': 'Income'
    })
    
    # Calculate win rate - to two decimal places
    players_df['Win Rate (%)'] = (players_df['Wins'] / players_df['Hands'] * 100).round(2)
    
    # Highlight negative values in red
    def highlight_negative(val):
        color = 'red' if isinstance(val, (int, float)) and val < 0 else 'black'
        return f'color: {color}'
    
    # Select columns to display in the table with the new order
    display_cols = ['Rank', 'Player', 'Wins', 'Win Rate (%)', 'Final Chips', 'Total Rebuy', 'Income']
    
    # Display DataFrame - without index
    st.dataframe(
        players_df[display_cols].set_index('Rank').style.applymap(
            highlight_negative, 
            subset=['Income']
        ),
        use_container_width=True,
        height=180
    )
    
    st.caption("* Win Rate (%) = (Wins / Hands) × 100")

if __name__ == "__main__":
    main() 