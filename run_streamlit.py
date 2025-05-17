import streamlit.web.cli as stcli
import sys
import os

if __name__ == "__main__":
    # Get the current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we should use the standalone or app module version
    standalone_app_path = os.path.join(current_dir, "streamlit_app.py")
    app_module_path = os.path.join(current_dir, "app", "streamlit_app.py")
    
    # Use standalone version if it exists, otherwise use the app module version
    if os.path.exists(standalone_app_path):
        streamlit_app_path = standalone_app_path
        print(f"Using standalone Streamlit app: {streamlit_app_path}")
    else:
        streamlit_app_path = app_module_path
        print(f"Using app module Streamlit app: {streamlit_app_path}")
    
    # Set command line arguments
    sys.argv = [
        "streamlit", 
        "run", 
        streamlit_app_path,
        "--server.port=8501", 
        "--server.address=0.0.0.0"
    ]
    
    # Run Streamlit
    sys.exit(stcli.main()) 