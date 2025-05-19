"""
Streamlit application entry point for the Poker Stats Dashboard.
This file serves as the main entry point for running the application.
"""

import os
import sys

# Add path to the project root to allow imports from app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main application module
from app.ui.main import run_app

# Run the application
if __name__ == "__main__":
    run_app() 