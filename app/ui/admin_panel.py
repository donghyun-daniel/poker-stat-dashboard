"""
Admin panel module for the Poker Stats Dashboard.
Provides administrative functions like database management.
"""

import streamlit as st
from app.config import ADMIN_PASSWORD_KEY

def render_admin_panel(db):
    """
    Render the administrator panel with authentication and database reset functionality.
    
    Args:
        db: Database manager instance
    """
    with st.expander("Administrator Area"):
        st.write("This is the admin area for database management.")
        
        admin_password = st.text_input("Admin Password", type="password")
        
        # Get the admin password from secrets or use a default for development
        correct_password = ""
        try:
            correct_password = st.secrets[ADMIN_PASSWORD_KEY]
        except (KeyError, FileNotFoundError):
            # If running locally without secrets file
            st.warning("⚠️ Admin password not configured in secrets. Authentication will fail.")
        
        if admin_password and correct_password and admin_password == correct_password:
            st.success("Administrator authentication successful!")
            
            if st.button("🗑️ Reset Database", help="Warning: All game data will be deleted!"):
                _reset_database(db)
        elif admin_password and (not correct_password or admin_password != correct_password):
            st.error("Incorrect password. Authentication failed.")

def _reset_database(db):
    """
    Reset the database by deleting all data and optionally rebuilding tables.
    
    Args:
        db: Database manager instance
    """
    try:
        # Make sure we have a database connection
        if not db.conn:
            st.error("No database connection available.")
            return
            
        # Delete table data - in the correct order to avoid foreign key issues
        st.info("Attempting to delete data from tables...")
        
        try:
            # Order matters due to foreign key constraints
            db.conn.execute("DELETE FROM game_players")
            db.conn.execute("DELETE FROM games")
            db.conn.execute("DELETE FROM players")
            
            st.success("✅ Database has been successfully reset!")
            st.info("Please refresh the page to see the changes.")
        except Exception as e:
            st.warning(f"Could not delete data: {str(e)}")
            st.info("Trying alternative approach - dropping and recreating tables...")
            
            try:
                # Drop tables in the correct order to avoid foreign key constraints
                db.conn.execute("DROP TABLE IF EXISTS game_players")
                db.conn.execute("DROP TABLE IF EXISTS games")
                db.conn.execute("DROP TABLE IF EXISTS players")
                
                # Reinitialize the database tables
                try:
                    # Try with the more specific method if available
                    db.initialize_db_tables()
                except AttributeError:
                    # Fall back to the general method
                    db.initialize_db()
                
                st.success("✅ Database has been successfully reset and rebuilt!")
                st.info("Please refresh the page to see the changes.")
            except Exception as e2:
                st.error(f"Failed to rebuild database: {str(e2)}")
                st.info("You may need to manually delete the database file and restart the application.")
                st.code("""
                # To manually reset the database:
                1. Stop the application
                2. Delete the 'poker_stats.duckdb' and any '.wal' files in the data directory
                3. Restart the application
                """)
    except Exception as e:
        st.error(f"Unexpected error during database reset: {str(e)}")
        st.info("Please try restarting the application.") 