import sys
import os
import json
from pathlib import Path
from pprint import pprint

# Add the parent directory to the sys.path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parsers.poker_now_parser import parse_log_file

def main():
    """Test the PokerNow log parser with a sample file."""
    # Get the sample log file path
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent
    sample_file = root_dir / "poker_now_log_pglOLvS8-uuLBZjRaDQ_NsfyP.csv"
    
    if not sample_file.exists():
        print(f"Error: Sample file not found at {sample_file}")
        return
    
    print(f"Parsing log file: {sample_file}")
    
    # Parse the log file
    result = parse_log_file(str(sample_file))
    
    # Print the results
    print("\nGame Period:")
    print(f"Start: {result['game_period']['start']}")
    print(f"End: {result['game_period']['end']}")
    print(f"Duration: {result['game_period']['end'] - result['game_period']['start']}")
    print(f"Total Hands Played: {result['total_hands']}")
    
    print("\nPlayer Statistics (sorted by rank):")
    print(f"{'Player':<15} {'Rank':<5} {'Rebuy':<10} {'Wins':<5} {'Hands':<5} {'Final Chips':<12} {'Income':<10}")
    print("-" * 70)
    
    for player in result['players']:
        print(f"{player['user_name']:<15} {player['rank']:<5} {player['total_rebuy_amt']:<10} "
              f"{player['total_win_cnt']:<5} {player['total_hand_cnt']:<5} "
              f"{player['total_chip']:<12} {player['total_income']:<10}")

if __name__ == "__main__":
    main() 