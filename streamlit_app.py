"""
Streamlit application entry point for the Poker Stats Dashboard.
This file serves as the main entry point for running the application.
"""

import os
import sys
import streamlit as st

# Add path to the project root to allow imports from app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Show a simple loading message while the app initializes
st.set_page_config(
    page_title="🃏 Poker Stats Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    # Import the main application module
    from app.ui.main import run_app
    
    # Run the application
    run_app()
    
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Please make sure all dependencies are installed correctly.")
    st.code("pip install -r requirements.txt")
    
except Exception as e:
    st.error(f"Error starting the application: {e}")
    st.info("Please check the logs for more details.") 