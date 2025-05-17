import streamlit as st
import pandas as pd
import os
import tempfile
import sys
import pathlib
import numpy as np
from datetime import datetime
from pathlib import Path

# Set up path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import poker parser and database manager
try:
    from app.parsers.poker_now_parser import parse_log_file
    from app.db.db_manager import get_db_manager
except ImportError:
    # Setup relative path for Streamlit Cloud
    if os.path.exists(os.path.join(current_dir, "app", "parsers", "poker_now_parser.py")):
        from app.parsers.poker_now_parser import parse_log_file
        from app.db.db_manager import get_db_manager
    else:
        st.error("Required modules not found.")

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
    /* Tab content height */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    /* Success/Error message style */
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        color: #721c24;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🃏 Poker Stats Dashboard")
    
    # Initialize database connection
    db = get_db_manager()
    
    # Create tabs for different sections
    tabs = st.tabs(["Upload Game Log", "Game History", "Player Statistics"])
    
    # Tab 1: Upload Game Log
    with tabs[0]:
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
                    
                    # Extract game information for DB comparison
                    start_time = result['game_period']['start']
                    player_names = [player['user_name'] for player in result['players']]
                    
                    # Check if game already exists in DB
                    if db.game_exists(start_time, player_names):
                        st.error("This game's information is already pushed to the database")
                        display_results(result, show_store_button=False)
                    else:
                        # Show results with store button
                        display_results(result, show_store_button=True, temp_file_path=temp_file_path, 
                                       log_file_name=uploaded_file.name, db=db)
                    
                    # Delete temporary file
                    os.unlink(temp_file_path)
                    
                except Exception as e:
                    st.error(f"Error occurred during file analysis: {str(e)}")
                    # Show error log
                    st.exception(e)
    
    # Tab 2: Game History
    with tabs[1]:
        st.subheader("Game History")
        
        # Get all games from the database
        games = db.get_all_games()
        
        if not games:
            st.info("No games found in the database. Upload a game log to get started.")
        else:
            # Create a custom display name for each game with time and players
            game_options = {}
            for game in games:
                # Parse start time with full details including hours, minutes, seconds
                start_time = pd.to_datetime(game['start_time'])
                start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Get player info for this game
                game_details = db.get_game_details(game['game_id'])
                if game_details and 'players' in game_details:
                    player_names = [p['user_name'] for p in game_details['players']]
                    player_names.sort()  # Sort alphabetically
                    players_str = ", ".join(player_names)
                    
                    # Create display name: "2023-05-17 13:45:22 (player1, player2, player3)"
                    display_name = f"{start_time_str} ({players_str})"
                    game_options[display_name] = game['game_id']
            
            # Let user select a game to view details at the top of the page
            if game_options:
                display_names = list(game_options.keys())
                # Sort by date, newest first
                display_names.sort(reverse=True)
                
                selected_display = st.selectbox("Select a game:", display_names)
                selected_game_id = game_options[selected_display]
                
                # Get game details
                game_details = db.get_game_details(selected_game_id)
                
                if game_details:
                    # Display game details
                    display_game_details(game_details)
                else:
                    st.warning("Could not retrieve game details.")
            
            # Show full game list table below
            st.subheader("All Games")
            
            # Create a DataFrame for games
            games_df = pd.DataFrame(games)
            
            # Format datetime columns with full time details
            games_df['start_time'] = pd.to_datetime(games_df['start_time']).dt.strftime("%Y-%m-%d %H:%M:%S")
            games_df['end_time'] = pd.to_datetime(games_df['end_time']).dt.strftime("%Y-%m-%d %H:%M:%S")
            games_df['import_date'] = pd.to_datetime(games_df['import_date']).dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Rename columns for display
            games_df = games_df.rename(columns={
                'game_id': 'Game ID',
                'log_file_name': 'Log File',
                'start_time': 'Start Time',
                'end_time': 'End Time',
                'total_hands': 'Total Hands',
                'player_count': 'Players',
                'import_date': 'Imported On'
            })
            
            # Display the games table
            st.dataframe(games_df, use_container_width=True)
    
    # Tab 3: Player Statistics
    with tabs[2]:
        st.subheader("Player Statistics")
        
        # Get all player statistics
        player_stats = db.get_player_statistics()
        
        if not player_stats:
            st.info("No player statistics found in the database. Upload a game log to get started.")
        else:
            # Create a DataFrame for player stats
            stats_df = pd.DataFrame(player_stats)
            
            # Format columns
            stats_df['avg_win_rate'] = stats_df['avg_win_rate'].round(2)
            stats_df['avg_rank'] = stats_df['avg_rank'].round(2)
            
            # Rename columns for display
            stats_df = stats_df.rename(columns={
                'player_name': 'Player',
                'games_played': 'Games',
                'total_wins': 'Wins',
                'total_hands': 'Hands',
                'avg_win_rate': 'Win Rate (%)',
                'total_income': 'Total Income',
                'avg_rank': 'Avg Rank',
                'first_place_count': '1st Places'
            })
            
            # Display the player stats table
            st.dataframe(stats_df, use_container_width=True)
            
            # Player detail charts
            if len(stats_df) > 0:
                st.subheader("Player Comparison")
                
                # Income comparison
                st.write("Total Income Comparison")
                income_chart = stats_df[['Player', 'Total Income']].set_index('Player')
                st.bar_chart(income_chart)
                
                # Win rate comparison
                st.write("Win Rate Comparison")
                win_rate_chart = stats_df[['Player', 'Win Rate (%)']].set_index('Player')
                st.bar_chart(win_rate_chart)
    
    st.divider()
    
    # Admin area (at the bottom of the page)
    with st.expander("Administrator Area"):
        st.write("This is the admin area for database management.")
        
        admin_password = st.text_input("Admin Password", type="password")
        
        # Get the admin password from secrets or use a default for development
        correct_password = ""
        try:
            correct_password = st.secrets["db_admin_pw"]
        except (KeyError, FileNotFoundError):
            # If running locally without secrets file
            st.warning("⚠️ Admin password not configured in secrets. Authentication will fail.")
        
        if admin_password and correct_password and admin_password == correct_password:
            st.success("Administrator authentication successful!")
            
            if st.button("🗑️ Reset Database", help="Warning: All game data will be deleted!"):
                try:
                    # Delete table data
                    db.conn.execute("DELETE FROM game_players")
                    db.conn.execute("DELETE FROM games")
                    db.conn.execute("DELETE FROM players")
                    
                    # Reset IDs (optional)
                    db.conn.execute("DELETE FROM sqlite_sequence WHERE name='players'")
                    
                    st.success("✅ Database has been successfully reset!")
                    st.info("Please refresh the page to see the changes.")
                except Exception as e:
                    st.error(f"Error occurred while resetting database: {str(e)}")
        elif admin_password and (not correct_password or admin_password != correct_password):
            st.error("Incorrect password. Authentication failed.")
    
    st.caption("Poker Stats Dashboard © 2025")

def store_game_in_db(game_data, log_file_name, db):
    """Store game data in the database and return success status and message."""
    game_id = db.store_game_data(game_data, log_file_name)
    
    if game_id:
        return True, f"Game data successfully stored in the database with ID: {game_id}"
    else:
        return False, "Failed to store game data in the database"

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

def display_results(data, show_store_button=False, temp_file_path=None, log_file_name=None, db=None):
    """Display analysis results visually."""
    
    st.success("✅ Analysis Complete!")
    
    # Display compact game information
    st.subheader("Game Information")
    
    # Format date and time
    start_time = data['game_period']['start']
    end_time = data['game_period']['end']
    
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('Z', ''))
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time.replace('Z', ''))
    
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M")
    
    # Calculate duration
    duration = end_time - start_time
    hours = duration.total_seconds() // 3600
    minutes = (duration.total_seconds() % 3600) // 60
    duration_text = f"{int(hours)}h {int(minutes)}m"
    
    # Get player names
    player_names = [player['user_name'] for player in data['players']]
    player_count = len(player_names)
    
    # Sort player names alphabetically
    sorted_player_names = sorted(player_names)
    players_text = ", ".join(sorted_player_names)
    
    # Display game info in a compact format
    st.markdown(f"**{start_time_str} ~ {end_time_str} ({duration_text})**", unsafe_allow_html=True)
    st.markdown(f"**Players ({player_count}):** {players_text}", unsafe_allow_html=True)
    
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
    # The parser now counts admin approvals
    # The first approval is the initial buy-in, all subsequent approvals are rebuys
    # The total_rebuy_amt from parser is initial_buyin * (1 + rebuy_count)
    # So rebuy count = (total_rebuy_amt / initial_buyin) - 1
    players_df['Rebuy Count'] = (players_df['Rebuy-in Count'] / 20000 - 1).apply(lambda x: max(int(round(x)), 0))
    
    # Add a note about the rebuy count meaning
    st.caption("* Rebuy Count: Number of times a player was approved by the admin after the initial buy-in")
    
    # Calculate player fee contributions
    ENTRY_FEE = 5000  # 5,000 won per player
    FREE_REBUYS = 2   # First 2 rebuys are free
    REBUY_FEE = 5000  # 5,000 won for each additional rebuy (3rd and beyond)
    
    players_df['Entry Fee'] = ENTRY_FEE
    players_df['Additional Fee'] = players_df['Rebuy Count'].apply(
        lambda x: max(0, x - FREE_REBUYS) * REBUY_FEE
    )
    players_df['Total Fee'] = players_df['Entry Fee'] + players_df['Additional Fee']
    
    # Sort by fee contributions (highest first, then by name)
    fee_df = players_df[['Player', 'Total Fee', 'Entry Fee', 'Additional Fee', 'Rebuy Count']].copy()
    fee_df = fee_df.sort_values(by=['Total Fee', 'Player'], ascending=[False, True])
    
    # Calculate prize distribution
    prize_distribution, prize_percentages, total_prize_pool = calculate_prize_distribution(players_df)
    
    # Add prize pool info to game information section
    st.markdown(f"**Prize Pool: {total_prize_pool:,} won**", unsafe_allow_html=True)
    
    # Show player fee contributions
    st.markdown("**Player Contributions:**")
    
    # Format numbers with commas
    fee_df['Total Fee'] = fee_df['Total Fee'].apply(lambda x: f"{x:,} won")
    fee_df['Entry Fee'] = fee_df['Entry Fee'].apply(lambda x: f"{x:,} won")
    fee_df['Additional Fee'] = fee_df['Additional Fee'].apply(lambda x: f"{x:,} won")
    
    # Show compact table of player fees
    st.dataframe(
        fee_df[['Player', 'Total Fee', 'Entry Fee', 'Additional Fee', 'Rebuy Count']],
        use_container_width=True,
        height=min(150, len(fee_df) * 35 + 38)  # Adjust height based on number of players
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
    
    # Select columns to display in the table with the new order
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
    st.caption("* Rebuy Count = Number of additional approvals by admin after the initial buy-in")
    
    # Add Player Prize Statistics section
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
    
    # Add button to store game data in database if requested
    if show_store_button and db and log_file_name:
        st.divider()
        if st.button("Store Game Data in Database"):
            success, message = store_game_in_db(data, log_file_name, db)
            if success:
                st.success(message)
            else:
                st.error(message)

def display_game_details(game_data):
    """Display details for a specific game from the database."""
    
    # Format dates
    if isinstance(game_data['start_time'], str):
        start_time = datetime.fromisoformat(game_data['start_time'].replace('Z', ''))
    else:
        start_time = game_data['start_time']
        
    if isinstance(game_data['end_time'], str):
        end_time = datetime.fromisoformat(game_data['end_time'].replace('Z', ''))
    else:
        end_time = game_data['end_time']
    
    # Calculate duration
    duration = end_time - start_time
    hours = duration.total_seconds() // 3600
    minutes = (duration.total_seconds() % 3600) // 60
    duration_text = f"{int(hours)}h {int(minutes)}m"
    
    # Display game info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Game Date", start_time.strftime("%Y-%m-%d %H:%M:%S"))
    with col2:
        st.metric("Duration", duration_text)
    with col3:
        st.metric("Total Hands", game_data['total_hands'])
    
    # Create DataFrame for player stats
    players_df = pd.DataFrame(game_data['players'])
    
    # Sort by rank
    players_df = players_df.sort_values(by='rank')
    
    # Rename columns for better display
    players_df = players_df.rename(columns={
        'user_name': 'Player',
        'rank': 'Rank',
        'total_rebuy_amt': 'Total Rebuy',
        'total_win_cnt': 'Wins',
        'total_hand_cnt': 'Hands',
        'total_chip': 'Final Chips',
        'total_income': 'Income'
    })
    
    # Calculate win rate
    players_df['Win Rate (%)'] = players_df.apply(
        lambda row: round((row['Wins'] / row['Hands'] * 100), 2) if row['Hands'] > 0 else 0, 
        axis=1
    )
    
    # Calculate rebuy count from total rebuy amount
    players_df['Rebuy Count'] = (players_df['Total Rebuy'] / 20000 - 1).apply(lambda x: max(int(round(x)), 0))
    
    # Calculate player fee contributions
    ENTRY_FEE = 5000  # 5,000 won per player
    FREE_REBUYS = 2   # First 2 rebuys are free
    REBUY_FEE = 5000  # 5,000 won for each additional rebuy (3rd and beyond)
    
    players_df['Entry Fee'] = ENTRY_FEE
    players_df['Additional Fee'] = players_df['Rebuy Count'].apply(
        lambda x: max(0, x - FREE_REBUYS) * REBUY_FEE
    )
    players_df['Total Fee'] = players_df['Entry Fee'] + players_df['Additional Fee']
    
    # Calculate prize distribution
    prize_distribution, prize_percentages, total_prize_pool = calculate_prize_distribution(players_df)
    
    # Add prize info to each player
    players_df['Prize %'] = players_df['Rank'].map(lambda x: prize_percentages.get(x, 0))
    players_df['Total Prize'] = players_df['Rank'].map(lambda x: prize_distribution.get(x, 0))
    players_df['Net Prize'] = players_df['Total Prize'] - players_df['Total Fee']
    
    # Format prize percentage as string with 2 decimal places
    players_df['Prize %'] = players_df['Prize %'].apply(lambda x: f"{x:.2f}%")
    
    # Format Income with colors
    def color_values(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: green'
            elif val < 0:
                return 'color: red'
        return ''
    
    # Display player results
    st.subheader("Player Results")
    
    display_cols = ['Rank', 'Player', 'Wins', 'Win Rate (%)', 'Final Chips', 'Rebuy Count', 'Income']
    
    # Create a copy with selected columns
    display_df = players_df[display_cols].copy()
    
    # Display the dataframe
    st.dataframe(
        display_df.set_index('Rank').style.applymap(
            color_values, 
            subset=['Income']
        ),
        use_container_width=True,
        height=180
    )
    
    # Display prize results
    st.subheader("Player Prize Results")
    
    # Add prize pool info
    st.markdown(f"**Prize Pool: {total_prize_pool:,} won**", unsafe_allow_html=True)
    
    prize_cols = ['Rank', 'Player', 'Prize %', 'Total Fee', 'Total Prize', 'Net Prize']
    
    # Make a copy to avoid modifying the original dataframe
    prize_df = players_df[prize_cols].copy()
    
    # Format monetary values with commas
    prize_df['Total Fee'] = prize_df['Total Fee'].apply(lambda x: f"{x:,} won")
    prize_df['Total Prize'] = prize_df['Total Prize'].apply(lambda x: f"{x:,} won")
    prize_df['Net Prize'] = prize_df['Net Prize'].apply(lambda x: f"{x:,} won")
    
    # Display prize table
    st.dataframe(
        prize_df.set_index('Rank').style.applymap(
            color_values,
            subset=['Net Prize']
        ),
        use_container_width=True,
        height=180
    )
    
    st.caption("* Prize % = Percentage of the prize pool")
    st.caption("* Net Prize = Prize amount minus entry fees")

if __name__ == "__main__":
    main() 