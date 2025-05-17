"""
History tab module for the Poker Stats Dashboard.
Handles display of game history and detailed game information.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from app.config import DATE_FORMAT, TIME_FORMAT, DATE_TIME_FORMAT
from app.prize_calculator import calculate_prize_distribution

def render_history_tab(db):
    """
    Render the game history tab with game selection and detailed information.
    
    Args:
        db: Database manager instance
    """
    st.write("View and analyze previous games.")
    
    try:
        # Get all games from database
        all_games = db.get_all_games()
        
        # Check if there are games to display
        if not all_games:
            st.info("No games found in the database. Please upload a game log first.")
            return
        
        # Create a list of game options with formatted display names
        game_options = []
        game_id_map = {}
        
        for game in all_games:
            try:
                # Try to access dictionary values by key
                if isinstance(game, dict):
                    game_id = game['game_id']
                    start_time_str = game['start_time']
                    log_file = game['log_file_name']
                # If it's a tuple or list, access by index
                elif isinstance(game, (tuple, list)):
                    game_id = game[0]
                    start_time_str = game[1]
                    log_file = game[2]
                else:
                    st.error(f"Unexpected game data format: {type(game)}")
                    continue
                
                # Get player names for this game
                player_names = db.get_player_names_for_game(game_id)
                player_names_str = ", ".join(sorted(player_names))
                
                # Format the start time with full time format
                try:
                    start_time = datetime.strptime(str(start_time_str), "%Y-%m-%d %H:%M:%S")
                    display_time = start_time.strftime(DATE_TIME_FORMAT)
                except ValueError:
                    display_time = str(start_time_str)
                
                # Create display name with date, time and player names
                display_name = f"{display_time} ({player_names_str})"
                
                game_options.append(display_name)
                game_id_map[display_name] = game_id
            except Exception as e:
                st.error(f"Error processing game data: {str(e)}")
                continue
        
        # Add header for game selection
        st.subheader("Select Game")
        
        # Game selection dropdown at the top
        if game_options:
            selected_game_display = st.selectbox("Choose a game to view details:", game_options, index=0)
            selected_game_id = game_id_map[selected_game_display]
            
            # Display the selected game details
            display_game_details(db, selected_game_id)
        else:
            st.warning("No games available to display.")
    except Exception as e:
        st.error(f"Error displaying game history: {str(e)}")
        st.info("Please try uploading a game log first.")

def display_game_details(db, game_id):
    """
    Display detailed information for the selected game.
    
    Args:
        db: Database manager instance
        game_id: ID of the selected game
    """
    try:
        # Get game information
        game_info = db.get_game_info(game_id)
        if not game_info:
            st.error(f"Failed to retrieve information for game ID: {game_id}")
            return
        
        # Extract game details with safe handling of different return types
        try:
            if isinstance(game_info, (tuple, list)) and len(game_info) >= 2:
                start_time_str = game_info[0]
                log_file = game_info[1]
            elif isinstance(game_info, dict):
                start_time_str = game_info.get('start_time')
                log_file = game_info.get('log_file_name')
            else:
                st.error(f"Unexpected game info format: {type(game_info)}")
                start_time_str = "Unknown"
                log_file = "Unknown"
        except Exception as e:
            st.error(f"Error extracting game information: {str(e)}")
            start_time_str = "Unknown"
            log_file = "Unknown"
        
        # Format start time with full date and time
        try:
            # Convert to string to ensure compatibility with different types
            start_time_str = str(start_time_str)
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            display_time = start_time.strftime(DATE_TIME_FORMAT)
        except ValueError:
            display_time = str(start_time_str)
        
        st.divider()
        st.subheader("Game Details")
        
        # Show game date and file name
        st.markdown(f"**Date & Time:** {display_time}")
        st.markdown(f"**Log File:** {log_file if log_file else 'Unknown'}")
        
        # Get player results
        player_results = db.get_player_results(game_id)
        if not player_results:
            st.warning("No player results found for this game.")
            return
        
        # Create DataFrame from player results
        columns = ["Player", "Rank", "Rebuy Count", "Wins", "Hands", "Final Chips", "Income"]
        player_df = pd.DataFrame(player_results, columns=columns)
        
        # Sort by rank
        player_df = player_df.sort_values("Rank")
        
        # Calculate win rate
        player_df["Win Rate (%)"] = player_df.apply(
            lambda row: f"{(row['Wins'] / row['Hands'] * 100):.2f}" if row["Hands"] > 0 else "0.00",
            axis=1
        )
        
        # Convert win rate to float for sorting
        player_df["Win Rate (%)"] = player_df["Win Rate (%)"].astype(float)
        
        # Calculate fee contribution for each player
        from app.config import ENTRY_FEE, FREE_REBUYS, REBUY_FEE
        
        player_df["Entry Fee"] = ENTRY_FEE
        player_df["Additional Fee"] = player_df["Rebuy Count"].apply(
            lambda x: max(0, x - FREE_REBUYS) * REBUY_FEE
        )
        player_df["Total Fee"] = player_df["Entry Fee"] + player_df["Additional Fee"]
        
        # Calculate prize distribution
        prize_distribution, prize_percentages, total_prize_pool = calculate_prize_distribution(player_df)
        
        # Add prize information to dataframe
        player_df["Prize %"] = player_df["Rank"].map(lambda x: prize_percentages.get(x, 0))
        player_df["Total Prize"] = player_df["Rank"].map(lambda x: prize_distribution.get(x, 0))
        
        # Format prize percentage as string
        player_df["Prize %"] = player_df["Prize %"].apply(lambda x: f"{x:.2f}%")
        
        # Calculate Net Prize (Prize - Total Fee)
        player_df["Net Prize"] = player_df["Total Prize"] - player_df["Total Fee"]
        
        # Display game summary
        player_count = len(player_df)
        player_names = ", ".join(sorted(player_df["Player"].tolist()))
        
        st.markdown(f"**Players ({player_count}):** {player_names}")
        st.markdown(f"**Prize Pool:** {total_prize_pool:,} won")
        
        # Display Player Results section
        st.subheader("Player Results")
        
        # Function to highlight positive/negative values
        def color_values(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return "color: green"
                elif val < 0:
                    return "color: red"
            return ""
        
        # Display columns in the desired order for Player Results
        display_cols = ["Rank", "Player", "Wins", "Win Rate (%)", "Final Chips", "Rebuy Count", "Income"]
        
        # Display DataFrame - using Rank as index
        st.dataframe(
            player_df[display_cols].set_index("Rank").style.applymap(
                color_values, 
                subset=["Income"]
            ),
            use_container_width=True,
            height=min(180, len(player_df) * 35 + 38)
        )
        
        # Add explanation for columns
        st.caption("* Win Rate (%) = (Wins / Hands) × 100")
        st.caption("* Rebuy Count = Number of additional approvals by admin after the initial buy-in")
        
        # Display Player Prize Results section
        st.subheader("Player Prize Results")
        
        # Display prize information in a separate table
        prize_cols = ["Rank", "Player", "Prize %", "Total Prize", "Total Fee", "Net Prize"]
        
        # Create display DataFrame for prize information
        display_prize_df = player_df[prize_cols].copy()
        
        # Format monetary values with commas
        for col in ["Total Prize", "Total Fee", "Net Prize"]:
            display_prize_df[col] = display_prize_df[col].apply(lambda x: f"{x:,} won")
        
        # Display prize DataFrame
        st.dataframe(
            display_prize_df.set_index("Rank"),
            use_container_width=True,
            height=min(180, len(display_prize_df) * 35 + 38)
        )
        
        # Add explanation for columns
        st.caption("* Prize % = Percentage of the prize pool")
        st.caption("* Total Fee = Entry fee + Additional fees from rebuys")
        st.caption("* Net Prize = Prize amount minus total fees")
        
    except Exception as e:
        st.error(f"Error displaying game details: {str(e)}")
        st.info("Please try uploading a game log first or selecting a different game.") 