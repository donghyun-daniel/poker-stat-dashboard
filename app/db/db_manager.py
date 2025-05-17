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
        
        try:
            self.initialize_db()
        except Exception as e:
            logger.error(f"Error during database initialization: {str(e)}")
            # Provide a dummy connection or in-memory DB as fallback
            try:
                logger.info("Attempting to create in-memory database as fallback")
                self.conn = duckdb.connect(":memory:")
                self.initialize_db_tables()
            except Exception as e2:
                logger.error(f"Failed to create fallback database: {str(e2)}")
    
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
            
            # Initialize tables
            self.initialize_db_tables()
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def initialize_db_tables(self):
        """Create database tables if they don't exist."""
        if not self.conn:
            logger.error("Cannot initialize tables: No database connection")
            return
            
        try:
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
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")
    
    def game_exists(self, start_time: datetime, player_names: List[str]) -> bool:
        """
        Check if a game with the same start time and players already exists in the database.
        
        Args:
            start_time: The start time of the game
            player_names: List of player names who participated in the game
            
        Returns:
            True if the game already exists, False otherwise
        """
        if not self.conn:
            logger.error("Cannot check if game exists: No database connection")
            return False
            
        try:
            # Format datetime for SQL (safely)
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"Checking for existing game at {start_time_str} with {len(player_names)} players")
            logger.info(f"Players: {', '.join(sorted(player_names))}")
            
            # Use parameterized query to prevent SQL injection
            result = self.conn.execute(
                "SELECT game_id, player_count FROM games WHERE start_time = ?",
                (start_time_str,)
            ).fetchall()
            
            if not result:
                logger.info("No games found with matching start time")
                return False
            
            logger.info(f"Found {len(result)} games with same start time")
            
            # For each potential matching game, check if the players match
            for game_id, player_count in result:
                if player_count != len(player_names):
                    logger.info(f"Game {game_id} has different player count ({player_count} vs {len(player_names)})")
                    continue
                
                # Get players for this game with parameterized query
                players_result = self.conn.execute(
                    """
                    SELECT p.player_name
                    FROM game_players gp
                    JOIN players p ON gp.player_id = p.player_id
                    WHERE gp.game_id = ?
                    """,
                    (game_id,)
                ).fetchall()
                
                db_players = [p[0] for p in players_result]
                
                # Sort both lists for comparison
                db_players.sort()
                sorted_players = sorted(player_names)
                
                if db_players == sorted_players:
                    logger.info(f"Found matching game in database: {game_id}")
                    logger.info(f"Matching players: {', '.join(db_players)}")
                    return True
                else:
                    logger.info(f"Game {game_id} has different players")
                    logger.info(f"DB players: {', '.join(db_players)}")
                    logger.info(f"Current players: {', '.join(sorted_players)}")
            
            logger.info("No matching game found after player comparison")
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
        if not self.conn:
            logger.error("Cannot store game data: No database connection")
            return None
            
        try:
            # Check for required fields in game_data
            if 'game_period' not in game_data:
                logger.error("Missing 'game_period' in game data")
                return None
                
            if 'players' not in game_data:
                logger.error("Missing 'players' in game data")
                return None
                
            # Extract game information
            try:
                start_time = game_data['game_period']['start']
                end_time = game_data['game_period']['end']
                total_hands = game_data.get('total_hands', 0)  # Default to 0 if not present
            except KeyError as e:
                logger.error(f"Missing required field in game data: {str(e)}")
                return None
            
            # Extract player names
            try:
                player_names = [player['user_name'] for player in game_data['players']]
                player_count = len(player_names)
                
                if player_count == 0:
                    logger.error("No players found in game data")
                    return None
            except (KeyError, TypeError) as e:
                logger.error(f"Error extracting player names: {str(e)}")
                return None
            
            # Check if this game already exists with more detailed logging
            if self.game_exists(start_time, player_names):
                logger.warning("This game's information is already in the database - skipping storage")
                logger.info(f"Duplicate game details: Start time={start_time}, Players={', '.join(sorted(player_names))}")
                return None
            
            # Generate a unique game ID
            try:
                # First attempt: using timestamp + hash of player names
                timestamp_str = start_time.strftime('%Y%m%d%H%M%S')
                player_hash = hash(tuple(sorted(player_names))) % 10000
                game_id = f"game_{timestamp_str}_{player_hash:04d}"
                
                # Better check if this ID already exists - use parameterized query for safety
                id_exists = self.conn.execute(
                    "SELECT 1 FROM games WHERE game_id = ? LIMIT 1", 
                    (game_id,)
                ).fetchone()
                
                # If ID exists, try different approach
                if id_exists:
                    logger.warning(f"Game ID {game_id} already exists in database, generating alternative ID")
                    
                    # Import here to avoid circular imports
                    import uuid
                    import random
                    
                    # Second attempt: Use timestamp + random UUID suffix 
                    random_suffix = str(uuid.uuid4())[:8]
                    game_id = f"game_{timestamp_str}_{random_suffix}"
                    
                    # Double check this ID doesn't exist
                    id_exists = self.conn.execute(
                        "SELECT 1 FROM games WHERE game_id = ? LIMIT 1", 
                        (game_id,)
                    ).fetchone()
                    
                    if id_exists:
                        # Third (final) attempt: full UUID
                        game_id = f"game_{str(uuid.uuid4())}"
                        logger.warning(f"Using UUID-based game ID: {game_id}")
                        
                        # Final safety check
                        id_exists = self.conn.execute(
                            "SELECT 1 FROM games WHERE game_id = ? LIMIT 1", 
                            (game_id,)
                        ).fetchone()
                        
                        if id_exists:
                            # This is extremely unlikely but handle it anyway
                            logger.error("All attempts to generate a unique game ID failed")
                            raise ValueError("Unable to generate a unique game ID after multiple attempts")
            except Exception as e:
                logger.error(f"Error generating unique game ID: {str(e)}")
                # Fallback to a simple UUID-based ID with additional random component
                import uuid
                import random
                import time
                
                # Add timestamp and random number to make it even more unique
                unique_component = f"{int(time.time())}_{random.randint(1000, 9999)}"
                game_id = f"game_{unique_component}_{uuid.uuid4()}"
                logger.warning(f"Using failsafe game ID generation method: {game_id}")
            
            logger.info(f"Using game ID: {game_id}")
            
            # Start transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            try:
                # Format datetime for SQL
                start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
                end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Insert game record with parameterized query
                self.conn.execute(
                    """
                    INSERT INTO games 
                    (game_id, log_file_name, start_time, end_time, total_hands, player_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (game_id, log_file_name, start_time_str, end_time_str, total_hands, player_count)
                )
                
                # Process each player's data
                for player_data in game_data['players']:
                    try:
                        player_name = player_data['user_name']
                        
                        # Validate required player fields
                        required_fields = ['rank', 'total_rebuy_amt', 'total_win_cnt', 
                                        'total_hand_cnt', 'total_chip', 'total_income']
                        
                        for field in required_fields:
                            if field not in player_data:
                                logger.error(f"Missing required field '{field}' for player '{player_name}'")
                                raise KeyError(f"Missing field '{field}' for player '{player_name}'")
                        
                        # Check if player exists, if not, create
                        player_id = self._get_or_create_player(player_name)
                        
                        # Insert player game stats with parameterized query
                        self.conn.execute(
                            """
                            INSERT INTO game_players 
                            (game_id, player_id, rank, total_rebuy_amt, total_win_cnt, 
                            total_hand_cnt, total_chip, total_income)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (game_id, player_id, player_data['rank'], player_data['total_rebuy_amt'],
                            player_data['total_win_cnt'], player_data['total_hand_cnt'],
                            player_data['total_chip'], player_data['total_income'])
                        )
                    except KeyError as e:
                        # Roll back transaction and return error
                        self.conn.execute("ROLLBACK")
                        logger.error(f"KeyError while processing player data: {str(e)}")
                        return None
                    except Exception as e:
                        # Roll back transaction and return error
                        self.conn.execute("ROLLBACK")
                        logger.error(f"Error processing player data for '{player_name}': {str(e)}")
                        return None
                
                # Commit transaction
                self.conn.execute("COMMIT")
                
                logger.info(f"Game data stored successfully with game_id: {game_id}")
                return game_id
                
            except Exception as e:
                # Roll back transaction in case of error
                self.conn.execute("ROLLBACK")
                logger.error(f"Database error while storing game data: {str(e)}")
                return None
            
        except KeyError as e:
            logger.error(f"Missing key in game data: {str(e)}")
            return None
        except TypeError as e:
            logger.error(f"Type error in game data: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"Value error in game data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error storing game data: {str(e)}")
            return None
    
    def _get_or_create_player(self, player_name: str) -> int:
        """
        Get a player's ID from the database or create a new player record.
        
        Args:
            player_name: The name of the player
            
        Returns:
            The player's ID
        """
        try:
            # First try to get the player using parameterized query
            result = self.conn.execute(
                "SELECT player_id FROM players WHERE player_name = ?",
                (player_name,)
            ).fetchone()
            
            if result:
                logger.debug(f"Found existing player: {player_name} with ID: {result[0]}")
                return result[0]
            
            # Player doesn't exist, create new player
            # Get the next player_id (max + 1)
            result = self.conn.execute("""
                SELECT COALESCE(MAX(player_id), 0) + 1 FROM players
            """).fetchone()
            
            next_player_id = result[0]
            
            # Insert the new player using parameterized query
            self.conn.execute(
                "INSERT INTO players (player_id, player_name) VALUES (?, ?)",
                (next_player_id, player_name)
            )
            
            logger.info(f"Created new player: {player_name} with ID: {next_player_id}")
            return next_player_id
            
        except Exception as e:
            logger.error(f"Error in _get_or_create_player for '{player_name}': {str(e)}")
            # Re-raise to allow transaction rollback in calling methods
            raise
    
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
            base_query = """
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
            
            # Use parameterized query if player_name is provided
            if player_name:
                query = base_query + " WHERE p.player_name = ? GROUP BY p.player_name ORDER BY avg_rank ASC, total_income DESC"
                result = self.conn.execute(query, (player_name,)).fetchall()
            else:
                query = base_query + " GROUP BY p.player_name ORDER BY avg_rank ASC, total_income DESC"
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
    
    def get_player_game_history(self) -> List[tuple]:
        """
        Get player game history data for visualization.
        
        Returns:
            List of tuples containing (player_name, game_id, start_time, rank, income)
        """
        if not self.conn:
            logger.error("Cannot get player game history: No database connection")
            return []
            
        try:
            query = """
                SELECT 
                    p.player_name,
                    gp.game_id,
                    g.start_time,
                    gp.rank,
                    gp.total_income
                FROM game_players gp
                JOIN players p ON gp.player_id = p.player_id
                JOIN games g ON gp.game_id = g.game_id
                ORDER BY g.start_time, gp.rank
            """
            
            result = self.conn.execute(query).fetchall()
            return result
            
        except Exception as e:
            logger.error(f"Error getting player game history: {str(e)}")
            return []
    
    def get_player_results(self, game_id: str) -> List[tuple]:
        """
        Get player results for a specific game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            List of tuples containing player results
        """
        if not self.conn:
            logger.error("Cannot get player results: No database connection")
            return []
            
        try:
            query = f"""
                SELECT 
                    p.player_name,
                    gp.rank,
                    (gp.total_rebuy_amt / 20000) - 1 as rebuy_count,
                    gp.total_win_cnt,
                    gp.total_hand_cnt,
                    gp.total_chip,
                    gp.total_income
                FROM game_players gp
                JOIN players p ON gp.player_id = p.player_id
                WHERE gp.game_id = '{game_id}'
                ORDER BY gp.rank
            """
            
            result = self.conn.execute(query).fetchall()
            return result
            
        except Exception as e:
            logger.error(f"Error getting player results: {str(e)}")
            return []
    
    def get_player_names_for_game(self, game_id: str) -> List[str]:
        """
        Get the names of players who participated in a specific game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            List of player names
        """
        if not self.conn:
            logger.error("Cannot get player names: No database connection")
            return []
            
        try:
            query = f"""
                SELECT p.player_name
                FROM game_players gp
                JOIN players p ON gp.player_id = p.player_id
                WHERE gp.game_id = '{game_id}'
                ORDER BY p.player_name
            """
            
            result = self.conn.execute(query).fetchall()
            return [r[0] for r in result]
            
        except Exception as e:
            logger.error(f"Error getting player names: {str(e)}")
            return []
            
    def get_game_info(self, game_id: str) -> tuple:
        """
        Get basic information about a game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Tuple containing (start_time, log_file_name)
        """
        if not self.conn:
            logger.error("Cannot get game info: No database connection")
            return None
            
        try:
            query = f"""
                SELECT start_time, log_file_name
                FROM games
                WHERE game_id = '{game_id}'
            """
            
            result = self.conn.execute(query).fetchone()
            return result
            
        except Exception as e:
            logger.error(f"Error getting game info: {str(e)}")
            return None
            
    def get_all_player_stats(self) -> List[tuple]:
        """
        Get statistics for all players to display in the stats tab.
        
        Returns:
            List of tuples containing player statistics
        """
        if not self.conn:
            logger.error("Cannot get all player stats: No database connection")
            return []
            
        try:
            query = """
                SELECT 
                    p.player_name,
                    COUNT(DISTINCT gp.game_id) AS game_count,
                    COUNT(DISTINCT gp.game_id) * 5000 AS total_fee,
                    SUM(CASE WHEN gp.rank = 1 THEN 1 ELSE 0 END) * 5000 * 3 AS total_prize,
                    SUM(gp.total_income) AS net_income,
                    SUM(gp.total_win_cnt) AS total_wins,
                    SUM(gp.total_hand_cnt) AS total_hands,
                    CASE 
                        WHEN SUM(gp.total_hand_cnt) > 0 THEN 
                            (SUM(gp.total_win_cnt) * 100.0 / SUM(gp.total_hand_cnt))
                        ELSE 0
                    END AS win_rate,
                    AVG(gp.rank) AS avg_rank,
                    MIN(gp.rank) AS best_rank
                FROM players p
                JOIN game_players gp ON p.player_id = gp.player_id
                GROUP BY p.player_name
                ORDER BY avg_rank ASC, net_income DESC
            """
            
            result = self.conn.execute(query).fetchall()
            return result
            
        except Exception as e:
            logger.error(f"Error getting all player stats: {str(e)}")
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