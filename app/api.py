import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.parsers.poker_now_parser import parse_log_file
from app.db.db_manager import get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Poker Stats API",
    description="API for analyzing poker game logs and retrieving statistics",
    version="1.0.0"
)

# CORS settings - adjust as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """API status check endpoint"""
    return {"status": "online", "message": "Poker Stats API is running"}

@app.post("/api/upload-log")
async def upload_log_file(file: UploadFile = File(...)):
    """
    Upload and analyze a poker log file.
    
    - **file**: CSV format poker log file
    
    Returns:
    - Game period
    - Player statistics and rankings
    - Total hand count
    """
    try:
        # Check file extension
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
        logger.info(f"File upload: {file.filename}")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        try:
            # Analyze log file
            logger.info(f"Starting log file analysis: {temp_file_path}")
            result = parse_log_file(temp_file_path)
            logger.info("Log file analysis complete")
            
            # Check if this game already exists in the database
            db = get_db_manager()
            start_time = result['game_period']['start']
            player_names = [player['user_name'] for player in result['players']]
            
            exists = db.game_exists(start_time, player_names)
            
            # Add a flag to indicate if this game is already in the database
            result['already_in_db'] = exists
            
            # Delete temporary file
            os.unlink(temp_file_path)
            
            return JSONResponse(content=result)
            
        except Exception as e:
            logger.error(f"Error analyzing log file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error analyzing log file: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during file upload: {str(e)}")

@app.post("/api/store-game")
async def store_game(game_data: dict):
    """
    Store game data in the database.
    
    - **game_data**: The game data parsed from a log file
    - **file_name**: The name of the log file
    
    Returns:
    - Success status and game_id if successful
    """
    try:
        db = get_db_manager()
        file_name = game_data.get('log_file_name', 'unknown.csv')
        
        # Check if game exists
        start_time = game_data['game_period']['start']
        player_names = [player['user_name'] for player in game_data['players']]
        
        if db.game_exists(start_time, player_names):
            return JSONResponse(
                content={"success": False, "message": "This game's information is already pushed to the database"}
            )
        
        # Store the game data
        game_id = db.store_game_data(game_data, file_name)
        
        if game_id:
            return JSONResponse(
                content={"success": True, "game_id": game_id, "message": "Game data stored successfully"}
            )
        else:
            return JSONResponse(
                content={"success": False, "message": "Failed to store game data"}
            )
            
    except Exception as e:
        logger.error(f"Error storing game data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing game data: {str(e)}")

@app.get("/api/games")
async def get_games():
    """
    Get a list of all games in the database.
    
    Returns:
    - List of games with basic information
    """
    try:
        db = get_db_manager()
        games = db.get_all_games()
        return JSONResponse(content={"games": games})
    except Exception as e:
        logger.error(f"Error retrieving games: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving games: {str(e)}")

@app.get("/api/game/{game_id}")
async def get_game_details(game_id: str):
    """
    Get detailed information about a specific game.
    
    - **game_id**: The ID of the game
    
    Returns:
    - Game details including player statistics
    """
    try:
        db = get_db_manager()
        game_details = db.get_game_details(game_id)
        
        if not game_details:
            raise HTTPException(status_code=404, detail=f"Game with ID {game_id} not found")
            
        return JSONResponse(content=game_details)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving game details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving game details: {str(e)}")

@app.get("/api/player-stats")
async def get_player_stats(player_name: str = None):
    """
    Get player statistics across all games.
    
    - **player_name**: Optional player name to filter results
    
    Returns:
    - Player statistics
    """
    try:
        db = get_db_manager()
        stats = db.get_player_statistics(player_name)
        return JSONResponse(content={"player_stats": stats})
    except Exception as e:
        logger.error(f"Error retrieving player statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving player statistics: {str(e)}")

# Additional endpoints can be implemented as needed 