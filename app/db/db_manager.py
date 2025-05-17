import duckdb
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PokerDBManager:
    """
    Database manager for poker game statistics using DuckDB.
    Handles storing and retrieving game information and player stats.
    """
    
    def __init__(self, db_path: str = "poker_stats.duckdb"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = db_path
        self.conn = None
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize the database connection and create tables if they don't exist."""
        try:
            # Create db directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                
            # Connect to DuckDB
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to database: {self.db_path}")
            
            # Create games table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    game_id VARCHAR PRIMARY KEY,
                    log_file_name VARCHAR,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    total_hands INTEGER,
                    player_count INTEGER,
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create players table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id INTEGER PRIMARY KEY,
                    player_name VARCHAR UNIQUE
                )
            """)
            
            # Create game_players table (many-to-many relationship)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS game_players (
                    game_id VARCHAR,
                    player_id INTEGER,
                    rank INTEGER,
                    total_rebuy_amt INTEGER,
                    total_win_cnt INTEGER,
                    total_hand_cnt INTEGER,
                    total_chip INTEGER,
                    total_income INTEGER,
                    PRIMARY KEY (game_id, player_id),
                    FOREIGN KEY (game_id) REFERENCES games(game_id),
                    FOREIGN KEY (player_id) REFERENCES players(player_id)
                )
            """)
            
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def game_exists(self, start_time: datetime, player_names: List[str]) -> bool:
        """
        Check if a game with the same start time and players already exists in the database.
        
        Args:
            start_time: The start time of the game
            player_names: List of player names who participated in the game
            
        Returns:
            True if the game already exists, False otherwise
        """
        try:
            # Format datetime for SQL
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # First check if we have a game with the same start time
            result = self.conn.execute(f"""
                SELECT game_id, player_count 
                FROM games 
                WHERE start_time = '{start_time_str}'
            """).fetchall()
            
            if not result:
                return False
            
            # For each potential matching game, check if the players match
            for game_id, player_count in result:
                if player_count != len(player_names):
                    continue
                
                # Get players for this game
                players_result = self.conn.execute(f"""
                    SELECT p.player_name
                    FROM game_players gp
                    JOIN players p ON gp.player_id = p.player_id
                    WHERE gp.game_id = '{game_id}'
                """).fetchall()
                
                db_players = [p[0] for p in players_result]
                
                # Sort both lists for comparison
                db_players.sort()
                sorted_players = sorted(player_names)
                
                if db_players == sorted_players:
                    logger.info(f"Found matching game in database: {game_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if game exists: {str(e)}")
            return False
    
    def store_game_data(self, game_data: Dict[str, Any], log_file_name: str) -> Optional[str]:
        """
        Store game data and player statistics in the database.
        
        Args:
            game_data: The parsed game data dictionary
            log_file_name: The name of the log file
            
        Returns:
            The game_id if successful, None otherwise
        """
        try:
            # Extract game information
            start_time = game_data['game_period']['start']
            end_time = game_data['game_period']['end']
            total_hands = game_data['total_hands']
            
            # Extract player names
            player_names = [player['user_name'] for player in game_data['players']]
            player_count = len(player_names)
            
            # Check if this game already exists
            if self.game_exists(start_time, player_names):
                logger.info("This game's information is already pushed to the database")
                return None
            
            # Generate a unique game ID (using timestamp + hash of player names)
            game_id = f"game_{start_time.strftime('%Y%m%d%H%M%S')}_{hash(tuple(sorted(player_names))) % 10000:04d}"
            
            # Insert game record
            self.conn.execute(f"""
                INSERT INTO games (game_id, log_file_name, start_time, end_time, total_hands, player_count)
                VALUES ('{game_id}', '{log_file_name}', '{start_time}', '{end_time}', {total_hands}, {player_count})
            """)
            
            # Process each player's data
            for player_data in game_data['players']:
                player_name = player_data['user_name']
                
                # Check if player exists, if not, create
                player_id = self._get_or_create_player(player_name)
                
                # Insert player game stats
                self.conn.execute(f"""
                    INSERT INTO game_players (
                        game_id, 
                        player_id, 
                        rank, 
                        total_rebuy_amt, 
                        total_win_cnt, 
                        total_hand_cnt, 
                        total_chip, 
                        total_income
                    ) VALUES (
                        '{game_id}', 
                        {player_id}, 
                        {player_data['rank']}, 
                        {player_data['total_rebuy_amt']}, 
                        {player_data['total_win_cnt']}, 
                        {player_data['total_hand_cnt']}, 
                        {player_data['total_chip']}, 
                        {player_data['total_income']}
                    )
                """)
            
            logger.info(f"Game data stored successfully with game_id: {game_id}")
            return game_id
            
        except Exception as e:
            logger.error(f"Error storing game data: {str(e)}")
            return None
    
    def _get_or_create_player(self, player_name: str) -> int:
        """
        Get a player's ID from the database or create a new player record.
        
        Args:
            player_name: The name of the player
            
        Returns:
            The player's ID
        """
        # First try to get the player
        result = self.conn.execute(f"""
            SELECT player_id FROM players WHERE player_name = '{player_name}'
        """).fetchone()
        
        if result:
            return result[0]
        
        # Player doesn't exist, create new player
        # Get the next player_id (max + 1)
        result = self.conn.execute("""
            SELECT COALESCE(MAX(player_id), 0) + 1 FROM players
        """).fetchone()
        
        next_player_id = result[0]
        
        # Insert the new player
        self.conn.execute(f"""
            INSERT INTO players (player_id, player_name)
            VALUES ({next_player_id}, '{player_name}')
        """)
        
        logger.info(f"Created new player: {player_name} with ID: {next_player_id}")
        return next_player_id
    
    def get_all_games(self) -> List[Dict[str, Any]]:
        """
        Get information about all games in the database.
        
        Returns:
            List of dictionaries with game information
        """
        try:
            result = self.conn.execute("""
                SELECT 
                    g.game_id, 
                    g.log_file_name, 
                    g.start_time, 
                    g.end_time, 
                    g.total_hands, 
                    g.player_count,
                    g.import_date
                FROM games g
                ORDER BY g.start_time DESC
            """).fetchall()
            
            games = []
            for row in result:
                games.append({
                    'game_id': row[0],
                    'log_file_name': row[1],
                    'start_time': row[2],
                    'end_time': row[3],
                    'total_hands': row[4],
                    'player_count': row[5],
                    'import_date': row[6]
                })
            
            return games
            
        except Exception as e:
            logger.error(f"Error getting all games: {str(e)}")
            return []
    
    def get_game_details(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific game, including player stats.
        
        Args:
            game_id: The ID of the game
            
        Returns:
            Dictionary with game information and player stats
        """
        try:
            # Get game information
            game_result = self.conn.execute(f"""
                SELECT 
                    game_id, 
                    log_file_name, 
                    start_time, 
                    end_time, 
                    total_hands, 
                    player_count
                FROM games 
                WHERE game_id = '{game_id}'
            """).fetchone()
            
            if not game_result:
                return None
                
            game_info = {
                'game_id': game_result[0],
                'log_file_name': game_result[1],
                'start_time': game_result[2],
                'end_time': game_result[3],
                'total_hands': game_result[4],
                'player_count': game_result[5],
                'players': []
            }
            
            # Get player stats for this game
            player_result = self.conn.execute(f"""
                SELECT 
                    p.player_name,
                    gp.rank,
                    gp.total_rebuy_amt,
                    gp.total_win_cnt,
                    gp.total_hand_cnt,
                    gp.total_chip,
                    gp.total_income
                FROM game_players gp
                JOIN players p ON gp.player_id = p.player_id
                WHERE gp.game_id = '{game_id}'
                ORDER BY gp.rank
            """).fetchall()
            
            for player_row in player_result:
                player_info = {
                    'user_name': player_row[0],
                    'rank': player_row[1],
                    'total_rebuy_amt': player_row[2],
                    'total_win_cnt': player_row[3],
                    'total_hand_cnt': player_row[4],
                    'total_chip': player_row[5],
                    'total_income': player_row[6]
                }
                game_info['players'].append(player_info)
            
            return game_info
            
        except Exception as e:
            logger.error(f"Error getting game details: {str(e)}")
            return None
    
    def get_player_statistics(self, player_name: str = None) -> List[Dict[str, Any]]:
        """
        Get aggregated statistics for one or all players.
        
        Args:
            player_name: Optional player name to filter results
            
        Returns:
            List of dictionaries with player statistics
        """
        try:
            query = """
                SELECT 
                    p.player_name,
                    COUNT(DISTINCT gp.game_id) AS games_played,
                    SUM(gp.total_win_cnt) AS total_wins,
                    SUM(gp.total_hand_cnt) AS total_hands,
                    AVG(gp.total_win_cnt * 100.0 / NULLIF(gp.total_hand_cnt, 0)) AS avg_win_rate,
                    SUM(gp.total_income) AS total_income,
                    AVG(gp.rank) AS avg_rank,
                    COUNT(CASE WHEN gp.rank = 1 THEN 1 END) AS first_place_count
                FROM players p
                JOIN game_players gp ON p.player_id = gp.player_id
            """
            
            if player_name:
                query += f" WHERE p.player_name = '{player_name}'"
                
            query += " GROUP BY p.player_name ORDER BY total_income DESC"
            
            result = self.conn.execute(query).fetchall()
            
            players_stats = []
            for row in result:
                stats = {
                    'player_name': row[0],
                    'games_played': row[1],
                    'total_wins': row[2],
                    'total_hands': row[3],
                    'avg_win_rate': row[4],
                    'total_income': row[5],
                    'avg_rank': row[6],
                    'first_place_count': row[7]
                }
                players_stats.append(stats)
            
            return players_stats
            
        except Exception as e:
            logger.error(f"Error getting player statistics: {str(e)}")
            return []


# Create a singleton instance
db_manager = None

def get_db_manager(db_path: str = None) -> PokerDBManager:
    """
    Get a singleton instance of the PokerDBManager.
    
    Args:
        db_path: Optional custom path to the database file
        
    Returns:
        PokerDBManager instance
    """
    global db_manager
    
    if db_manager is None:
        if db_path is None:
            # Use default path relative to the project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            db_path = os.path.join(project_root, "data", "poker_stats.duckdb")
        
        db_manager = PokerDBManager(db_path)
    
    return db_manager 