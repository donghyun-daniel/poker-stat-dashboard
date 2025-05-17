"""
Upload tab module for the Poker Stats Dashboard.
Handles file uploads and displays analysis results.
"""

import streamlit as st
import tempfile
import os
import pandas as pd
from datetime import datetime

from app.parsers.poker_now_parser import parse_log_file
from app.config import ENTRY_FEE, FREE_REBUYS, REBUY_FEE, INITIAL_BUYIN
from app.prize_calculator import calculate_prize_distribution

def render_upload_tab(db):
    """
    Render the upload tab with file upload functionality and result display.
    
    Args:
        db: Database manager instance
    """
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

def display_results(data, show_store_button=False, temp_file_path=None, log_file_name=None, db=None):
    """
    Display analysis results visually.
    
    Args:
        data: Parsed game data
        show_store_button: Whether to show the button to store data in DB
        temp_file_path: Path to the temporary file
        log_file_name: Original file name
        db: Database manager instance
    """
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
    players_df['Rebuy Count'] = (players_df['Rebuy-in Count'] / INITIAL_BUYIN - 1).apply(lambda x: max(int(round(x)), 0))
    
    # Add a note about the rebuy count meaning
    st.caption("* Rebuy Count: Number of times a player was approved by the admin after the initial buy-in")
    
    # Calculate player fee contributions
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
        players_df[display_cols].set_index('Rank').style.map(
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
    
    # Make a copy to avoid modifying the original dataframe
    display_prize_df = prize_df[prize_cols].copy()
    
    # Format prize amounts with commas after calculations
    display_prize_df['Total Prize'] = display_prize_df['Total Prize'].apply(lambda x: f"{x:,} won")
    display_prize_df['Net Prize'] = display_prize_df['Net Prize'].apply(lambda x: f"{x:,} won")
    
    # Display prize statistics
    st.dataframe(
        display_prize_df.set_index('Rank').style.map(
            color_values,
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
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("📊 Store this game in the database to track statistics over time.")
        
        with col2:
            if st.button("💾 Store Game Data", help="Save this game data to the database for future reference and statistics"):
                with st.spinner("Storing game data..."):
                    success, message = store_game_in_db(data, log_file_name, db)
                    
                    if success:
                        st.success(message)
                        st.balloons()  # Add a fun element for successful storage
                        
                        # Show next steps
                        st.info("You can now view this game in the Game History and Player Statistics tabs.")
                    else:
                        # Parse the error message to provide more helpful information
                        error_type = "database error"
                        if "already exists" in message.lower():
                            error_type = "duplicate game"
                            st.error(message)
                            st.info("This game is already stored in the database. You can view it in the Game History tab.")
                        elif "missing" in message.lower():
                            error_type = "missing data"
                            st.error(message)
                            st.info("The game data is missing some required information. Please check the log file.")
                        elif "type error" in message.lower():
                            error_type = "data format"
                            st.error(message)
                            st.info("There's an issue with the data format. Please check the log file.")
                        else:
                            # Generic error
                            st.error(message)
                            
                        # Log for debugging
                        st.error(f"Error type: {error_type}")
                        
                        # Add a expandable section with troubleshooting tips
                        with st.expander("Troubleshooting Tips"):
                            st.markdown("""
                            ### Common Issues and Solutions:
                            
                            1. **Duplicate Game**: The game is already in the database. You can view it in the Game History tab.
                            
                            2. **Missing Data**: The log file may be incomplete or corrupted. Try re-downloading the log file from PokerNow.
                            
                            3. **Database Connection**: The database connection might be temporarily unavailable. Try refreshing the page.
                            
                            4. **Data Format**: There might be an issue with the log file format. Ensure it's a valid PokerNow log file.
                            
                            If you continue to experience issues, please check the application logs or contact support.
                            """)

def store_game_in_db(game_data, log_file_name, db):
    """
    Store game data in the database.
    
    Args:
        game_data: Parsed game data
        log_file_name: Original file name
        db: Database manager instance
        
    Returns:
        tuple: (success, message)
    """
    try:
        # First check if this game already exists
        start_time = game_data['game_period']['start']
        player_names = [player['user_name'] for player in game_data['players']]
        
        if db.game_exists(start_time, player_names):
            return False, "Failed to store game data: This game already exists in the database"
            
        # Try to store the game data
        game_id = db.store_game_data(game_data, log_file_name)
        
        if game_id:
            return True, f"Game data successfully stored in the database with ID: {game_id}"
        else:
            return False, "Failed to store game data: Unknown database error occurred"
            
    except KeyError as e:
        # Handle missing required fields in game data
        return False, f"Failed to store game data: Missing required field in game data ({str(e)})"
    except TypeError as e:
        # Handle type errors (e.g., wrong data type for a field)
        return False, f"Failed to store game data: Type error ({str(e)})"
    except ValueError as e:
        # Handle value errors (e.g., invalid values)
        return False, f"Failed to store game data: Invalid value ({str(e)})"
    except Exception as e:
        # Handle any other exceptions
        return False, f"Failed to store game data: {str(e)}" 