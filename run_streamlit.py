"""
Run script for Poker Stats Dashboard Streamlit application.
This script launches the Streamlit app on the specified port.
"""

import os
import sys
import streamlit.web.bootstrap as bootstrap

def run_streamlit():
    """
    Run the Streamlit application with specified parameters.
    """
    # Get the path to the streamlit_app.py file
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamlit_app.py")
    
    # Define Streamlit arguments
    flags = [
        "--server.port=8501",  # Port to run the app on
        "--server.address=0.0.0.0",  # Listen on all network interfaces
        "--browser.serverAddress=localhost",  # Server address for browser
        "--server.headless=true",  # Run in headless mode
        "--theme.base=light"  # Use light theme
    ]
    
    # Run the Streamlit app
    sys.argv = ["streamlit", "run", app_path] + flags
    bootstrap.run(app_path, "", sys.argv, flag_options={})

if __name__ == "__main__":
    run_streamlit() 