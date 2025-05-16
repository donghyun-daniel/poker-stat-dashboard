# 🃏 Poker Stats Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/gallery)

A web application for analyzing PokerNow game logs and providing player statistics.

## Features

- Upload and analyze CSV logs from PokerNow
- View player statistics (rankings, profits/losses, win rates)
- Visualize game data with interactive charts
- Mobile-friendly interface for easy access anywhere

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

4. Run the app:
```bash
streamlit run streamlit_app.py
```

## How to Use

1. Access the dashboard through a web browser
2. Upload a PokerNow log file (.csv format)
3. View the automatically generated analysis
4. Explore player statistics, win rates, and profit/loss data

## Ranking System

Player rankings are determined as follows:

1. Players who went out during the game receive the lowest ranks (ordered by elimination time)
2. Players who remained active until the end are ranked by **income**
   - Income = Final chips - Total rebuy amount
   - Higher income results in higher ranking

## License

This project is licensed under the MIT License.
