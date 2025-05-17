"""
Main application module for the Poker Stats Dashboard.
Integrates all UI components and handles tab navigation.
"""

import streamlit as st
import os
import sys

# Add path to the project root to allow imports from app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ui.upload_tab import render_upload_tab
from app.ui.history_tab import render_history_tab
from app.ui.stats_tab import render_stats_tab
from app.ui.admin_panel import render_admin_panel
from app.config import APP_TITLE, APP_DESCRIPTION, APP_SIDEBAR_TEXT, TABS
from app.db.db_manager import PokerDBManager

def setup_page_config():
    """
    Configure Streamlit page settings.
    """
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def render_header():
    """
    Render application header.
    """
    st.title(APP_TITLE)
    st.markdown(APP_DESCRIPTION)

def render_sidebar():
    """
    Render application sidebar.
    """
    st.sidebar.title("About")
    st.sidebar.info(APP_SIDEBAR_TEXT)
    
    # Add version info
    st.sidebar.caption("v1.0.0")

def load_database():
    """
    Initialize the database connection.
    
    Returns:
        PokerDBManager: Database manager instance
    """
    db = PokerDBManager()
    db.connect()
    db.initialize_db_if_needed()
    return db

def render_main_ui():
    """
    Render the main application UI with tabs.
    """
    # Initialize the database manager
    db = load_database()
    
    # Create tabs for navigation
    upload_tab, history_tab, stats_tab, admin_tab = st.tabs(TABS)
    
    # Render each tab content
    with upload_tab:
        render_upload_tab(db)
    
    with history_tab:
        render_history_tab(db)
    
    with stats_tab:
        render_stats_tab(db)
    
    with admin_tab:
        render_admin_panel(db)
    
    # Close database connection at the end
    db.close()

def run_app():
    """
    Main function to run the Streamlit application.
    """
    # Setup page configuration
    setup_page_config()
    
    # Render header and sidebar
    render_header()
    render_sidebar()
    
    # Render main UI with all tabs
    render_main_ui()

if __name__ == "__main__":
    run_app() 