#!/usr/bin/env python3
"""
Test script for the DuckDB database functionality.
Run this script to verify that the database operations are working correctly.
"""

import sys
import os
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup path for importing app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import app modules
try:
    from app.parsers.poker_now_parser import parse_log_file
    from app.db.db_manager import get_db_manager
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    sys.exit(1)

def test_parse_and_store(log_file_path: str):
    """
    Test parsing a log file and storing the results in the database.
    
    Args:
        log_file_path: Path to the poker log file to parse
    """
    logger.info(f"Testing database operations with log file: {log_file_path}")
    
    # Check if file exists
    if not os.path.exists(log_file_path):
        logger.error(f"Log file does not exist: {log_file_path}")
        return
    
    try:
        # Parse the log file
        logger.info("Parsing log file...")
        result = parse_log_file(log_file_path)
        
        # Get database manager
        logger.info("Connecting to database...")
        db = get_db_manager()
        
        # Extract game information for DB comparison
        start_time = result['game_period']['start']
        player_names = [player['user_name'] for player in result['players']]
        
        # Check if game already exists in DB
        logger.info("Checking if game already exists...")
        if db.game_exists(start_time, player_names):
            logger.info("This game's information is already in the database.")
        else:
            # Store game data
            logger.info("Storing game data in database...")
            log_file_name = os.path.basename(log_file_path)
            game_id = db.store_game_data(result, log_file_name)
            
            if game_id:
                logger.info(f"Game data successfully stored with ID: {game_id}")
            else:
                logger.error("Failed to store game data in database")
        
        # Display some statistics
        logger.info("\nTesting retrieval operations...")
        
        # Get all games
        games = db.get_all_games()
        logger.info(f"Found {len(games)} games in the database")
        
        if games:
            # Get player statistics
            player_stats = db.get_player_statistics()
            logger.info(f"Found statistics for {len(player_stats)} players")
            
            # Print top 3 players by income
            if player_stats:
                logger.info("\nTop players by income:")
                # Sort by total_income descending
                sorted_stats = sorted(player_stats, key=lambda x: x.get('total_income', 0), reverse=True)
                
                for i, player in enumerate(sorted_stats[:3], 1):
                    logger.info(f"{i}. {player['player_name']} - Income: {player.get('total_income', 0)}, "
                               f"Games: {player.get('games_played', 0)}, "
                               f"Win Rate: {player.get('avg_win_rate', 0):.2f}%")
        
        logger.info("\nDatabase test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during database test: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the database test."""
    parser = argparse.ArgumentParser(description="Test the poker statistics database functionality")
    parser.add_argument("log_file", help="Path to the poker game log file (CSV)")
    
    args = parser.parse_args()
    
    test_parse_and_store(args.log_file)

if __name__ == "__main__":
    main() 