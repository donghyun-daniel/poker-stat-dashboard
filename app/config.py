"""
Configuration module for the Poker Stats Dashboard.
Contains all constant values used throughout the application.
"""

# Game Constants
INITIAL_BUYIN = 20000  # Initial buy-in amount (chips)
ENTRY_FEE = 5000       # Entry fee in won
FREE_REBUYS = 2        # Number of free rebuys
REBUY_FEE = 5000       # Fee for additional rebuys in won

# UI Settings
APP_TITLE = "🃏 Poker Stats Dashboard"
APP_DESCRIPTION = "Upload poker game logs, track statistics, and analyze player performance."
APP_SIDEBAR_TEXT = """
This dashboard allows tracking and analysis of poker game statistics.
Upload log files from PokerNow to track game results and player performance over time.

Check out the repository at: 
https://github.com/donghyun-daniel/poker-stat-dashboard
"""
TABS = ["Upload Game Log", "Game History", "Player Statistics", "Admin"]

# Admin Settings
ADMIN_TITLE = "Administrator Area"
ADMIN_DESCRIPTION = "Database management and configuration."

# Database Settings
DB_PATH = "poker_stats.db"  # Database file path
DB_TABLES = ["players", "games", "game_players"]  # Tables in the database

# Date Formats
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Table Display Settings
TABLE_HEADERS = {
    "player_results": ["Rank", "Player", "Wins", "Win Rate (%)", "Final Chips", "Rebuy Count", "Income"],
    "prize_results": ["Rank", "Player", "Prize %", "Total Prize", "Total Fee", "Net Prize"]
}

# Chart Colors
BAR_CHART_COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", 
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
]

LINE_CHART_COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", 
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
]

# UI settings
UI_HEIGHT_SMALL = 150
UI_HEIGHT_MEDIUM = 180
UI_HEIGHT_LARGE = 250

# Admin settings
ADMIN_PASSWORD_KEY = "db_admin_pw"  # Key name for the admin password in Streamlit secrets

# Database settings
DEFAULT_DB_FILENAME = "poker_stats.duckdb"
DEFAULT_DB_DIR = "data"

# Date formats
DATE_FORMAT_SHORT = "%Y-%m-%d %H:%M"

# Table display settings
TABLE_HEADERS = {
    'user_name': 'Player',
    'rank': 'Rank',
    'total_rebuy_amt': 'Rebuy-in Count',
    'total_win_cnt': 'Wins',
    'total_hand_cnt': 'Hands',
    'total_chip': 'Final Chips',
    'total_income': 'Income',
    'game_id': 'Game ID',
    'log_file_name': 'Log File',
    'start_time': 'Start Time',
    'end_time': 'End Time',
    'total_hands': 'Total Hands',
    'player_count': 'Players',
    'import_date': 'Imported On',
    'player_name': 'Player',
    'games_played': 'Games',
    'avg_win_rate': 'Win Rate (%)',
    'avg_rank': 'Avg Rank',
    'first_place_count': '1st Places'
} 
