# 🃏 Poker Stats Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/gallery)

A web application for analyzing PokerNow game logs and providing player statistics. The application now includes a database to store and track statistics across multiple games.

## Features

- Upload and analyze CSV logs from PokerNow
- Store game results in a database for historical tracking
- View player statistics (rankings, profits/losses, win rates) across all games
- Browse game history and detailed results
- Visualize game data with interactive charts
- Mobile-friendly interface for easy access anywhere

## Database Features

- **Game Storage**: Automatically detects and prevents duplicate game entries
- **Player Tracking**: Maintains player statistics across multiple games
- **Historical Analysis**: View trends and statistics over time
- **Game Comparison**: Compare results between different game sessions

## Online Access

Access the dashboard online through Streamlit Cloud:

[Open Poker Stats Dashboard](https://share.streamlit.io/donghyun-daniel/poker-stat-dashboard/main)

## Local Setup

To run locally:

1. Clone the repository:
```bash
git clone https://github.com/donghyun-daniel/poker-stat-dashboard.git
cd poker-stat-dashboard
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the application:
```bash
# Use the start script to run both API and UI
./start.sh

# Or run them separately:
# For API only:
python main.py
# For Streamlit UI only:
python run_streamlit.py
```

5. Test database functionality:
```bash
# Parse a log file and store in database
python test_db.py path/to/poker_log.csv
```

## How to Use

1. Access the dashboard through a web browser
2. Upload a PokerNow log file (.csv format)
3. View the automatically generated analysis
4. Store game data in the database if it's a new game
5. Explore player statistics, win rates, and profit/loss data
6. Browse game history and player performance over time

## Tabs

The application now has three main tabs:

1. **Upload Game Log**: Upload and analyze new poker game logs
2. **Game History**: Browse and view details of previously stored games
3. **Player Statistics**: View aggregated player statistics across all games

## Ranking System

Player rankings are determined as follows:

1. Players who went out during the game receive the lowest ranks (ordered by elimination time)
2. Players who remained active until the end are ranked by **income**
   - Income = Final chips - Total rebuy amount
   - Higher income results in higher ranking

## License

This project is licensed under the MIT License.
