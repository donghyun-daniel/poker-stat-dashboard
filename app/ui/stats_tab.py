"""
Statistics tab module for the Poker Stats Dashboard.
Analyzes player performance across multiple games.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from app.config import BAR_CHART_COLORS, LINE_CHART_COLORS

def render_stats_tab(db):
    """
    Render the statistics tab with player performance analytics.
    
    Args:
        db: Database manager instance
    """
    st.write("Analyze player performance across all games.")
    
    # Get all player stats from database
    all_stats = db.get_all_player_stats()
    
    # Check if there are stats to display
    if not all_stats:
        st.info("No player statistics available. Please upload game logs first.")
        return
    
    # Create DataFrame from player stats
    columns = ["Player", "Game Count", "Total Fee", "Total Prize", "Net Income", 
               "Total Wins", "Total Hands", "Win Rate", "Avg Rank", "Best Rank"]
    df = pd.DataFrame(all_stats, columns=columns)
    
    # Sort by net income (descending)
    df = df.sort_values("Net Income", ascending=False)
    
    # Display player performance section
    st.subheader("Player Performance Summary")
    
    # Format monetary values with commas and 'won'
    df['Total Fee Display'] = df['Total Fee'].apply(lambda x: f"{x:,} won")
    df['Total Prize Display'] = df['Total Prize'].apply(lambda x: f"{x:,} won")
    df['Net Income Display'] = df['Net Income'].apply(lambda x: f"{x:,} won")
    
    # Format win rate percentage with 2 decimal places
    df['Win Rate Display'] = df['Win Rate'].apply(lambda x: f"{x:.2f}%")
    
    # Format rank values with 2 decimal places
    df['Avg Rank Display'] = df['Avg Rank'].apply(lambda x: f"{x:.2f}")
    
    # Function to highlight positive/negative values
    def color_values(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return "color: green"
            elif val < 0:
                return "color: red"
        return ""
    
    # Select display columns and rename them for better readability
    display_cols = ["Player", "Game Count", "Total Fee Display", "Total Prize Display", 
                    "Net Income Display", "Win Rate Display", "Avg Rank Display", "Best Rank"]
    
    display_df = df[display_cols].copy()
    display_df.columns = ["Player", "Games", "Total Fee", "Total Prize", 
                         "Net Income", "Win Rate (%)", "Avg Rank", "Best Rank"]
    
    # Display player summary table
    st.dataframe(
        display_df.style.applymap(
            color_values, 
            subset=["Net Income"]
        ),
        use_container_width=True,
        height=min(300, len(df) * 35 + 38)
    )
    
    # Add explanations
    st.caption("* Net Income = Total Prize - Total Fee")
    st.caption("* Win Rate (%) = (Total Wins / Total Hands) × 100")
    st.caption("* Avg Rank = Average finishing position across all games")
    st.caption("* Best Rank = Best finishing position achieved")
    
    # Only show visualizations if there are at least 2 players
    if len(df) < 2:
        st.info("Need at least 2 players for statistical comparisons.")
        return
    
    # Only show visualizations if there are at least 2 games
    total_games = df["Game Count"].sum()
    if total_games < 2:
        st.info("Need at least 2 games for meaningful statistics.")
        return
    
    # Visualization section
    st.divider()
    st.subheader("Player Visualizations")
    
    # Create income comparison visualization
    create_income_visualization(df)
    
    # Create win rate visualization
    create_win_rate_visualization(df)
    
    # Create rank visualization
    create_rank_visualization(df)
    
    # Game history analysis section (if available)
    game_history = db.get_player_game_history()
    if game_history:
        create_game_history_visualization(game_history, df["Player"].tolist())

def create_income_visualization(df):
    """
    Create income comparison visualizations.
    
    Args:
        df: DataFrame with player statistics
    """
    st.markdown("### Income Comparison")
    
    # Filter to players with at least one game
    df_filtered = df[df["Game Count"] > 0]
    
    # Sort by net income (highest first)
    df_filtered = df_filtered.sort_values("Net Income", ascending=False)
    
    # Create a column for ROI percentage
    df_filtered["ROI (%)"] = (df_filtered["Net Income"] / df_filtered["Total Fee"] * 100).round(2)
    
    # Replace infinity with a large number (when Total Fee is 0)
    df_filtered["ROI (%)"] = df_filtered["ROI (%)"].replace([np.inf, -np.inf], 0)
    
    # Create bar chart for net income
    income_fig = px.bar(
        df_filtered,
        x="Player",
        y="Net Income",
        title="Net Income by Player",
        color="Player",
        color_discrete_sequence=BAR_CHART_COLORS,
        text_auto=True,
        labels={"Player": "Player", "Net Income": "Net Income (won)"}
    )
    
    # Improve layout
    income_fig.update_layout(
        xaxis_title="Player",
        yaxis_title="Net Income (won)",
        legend_title="Player",
        xaxis={'categoryorder': 'total descending'}
    )
    
    # Show income chart
    st.plotly_chart(income_fig, use_container_width=True)
    
    # Create ROI chart
    roi_fig = px.bar(
        df_filtered,
        x="Player",
        y="ROI (%)",
        title="Return on Investment (ROI) by Player",
        color="Player",
        color_discrete_sequence=BAR_CHART_COLORS,
        text_auto=True,
        labels={"Player": "Player", "ROI (%)": "ROI (%)"}
    )
    
    # Improve layout
    roi_fig.update_layout(
        xaxis_title="Player",
        yaxis_title="ROI (%)",
        legend_title="Player",
        xaxis={'categoryorder': 'total descending'}
    )
    
    # Show ROI chart
    st.plotly_chart(roi_fig, use_container_width=True)
    
    # Add caption explaining ROI
    st.caption("* ROI (%) = (Net Income / Total Fee) × 100, measures return on investment")

def create_win_rate_visualization(df):
    """
    Create win rate visualization.
    
    Args:
        df: DataFrame with player statistics
    """
    st.markdown("### Win Rate Comparison")
    
    # Filter to players with at least one hand played
    df_filtered = df[(df["Total Hands"] > 0) & (df["Game Count"] > 0)]
    
    # Sort by win rate (highest first)
    df_filtered = df_filtered.sort_values("Win Rate", ascending=False)
    
    # Create bar chart for win rate
    win_rate_fig = px.bar(
        df_filtered,
        x="Player",
        y="Win Rate",
        title="Win Rate by Player",
        color="Player",
        color_discrete_sequence=BAR_CHART_COLORS,
        text_auto=True,
        labels={"Player": "Player", "Win Rate": "Win Rate (%)"}
    )
    
    # Improve layout
    win_rate_fig.update_layout(
        xaxis_title="Player",
        yaxis_title="Win Rate (%)",
        legend_title="Player",
        xaxis={'categoryorder': 'total descending'}
    )
    
    # Show win rate chart
    st.plotly_chart(win_rate_fig, use_container_width=True)
    
    # Add win rate explanation
    st.caption("* Win Rate (%) = (Total Wins / Total Hands) × 100")
    st.caption("* Higher win rate generally indicates better performance in winning hands")

def create_rank_visualization(df):
    """
    Create rank visualization.
    
    Args:
        df: DataFrame with player statistics
    """
    st.markdown("### Ranking Comparison")
    
    # Filter to players with at least one game
    df_filtered = df[df["Game Count"] > 0]
    
    # Sort by average rank (lowest first, since lower rank is better)
    df_filtered = df_filtered.sort_values("Avg Rank")
    
    # Create combo chart for average rank and best rank
    rank_data = []
    
    # Add average rank as bars
    rank_data.append(
        go.Bar(
            x=df_filtered["Player"],
            y=df_filtered["Avg Rank"],
            name="Average Rank",
            text=df_filtered["Avg Rank"].round(2),
            textposition="auto",
            marker_color="royalblue"
        )
    )
    
    # Add best rank as markers
    rank_data.append(
        go.Scatter(
            x=df_filtered["Player"],
            y=df_filtered["Best Rank"],
            name="Best Rank",
            mode="markers+text",
            marker=dict(size=12, color="green"),
            text=df_filtered["Best Rank"],
            textposition="top center"
        )
    )
    
    # Create layout
    rank_layout = go.Layout(
        title="Player Rankings (Lower is Better)",
        yaxis=dict(
            title="Rank Position",
            autorange="reversed",  # Reverse y-axis for ranks (1 at top)
            tickmode="linear",
            dtick=1,  # Tick every 1 unit
            range=[0, max(df_filtered["Avg Rank"].max(), df_filtered["Best Rank"].max()) + 1]
        ),
        xaxis=dict(title="Player"),
        legend=dict(title="Metric")
    )
    
    # Create figure
    rank_fig = go.Figure(data=rank_data, layout=rank_layout)
    
    # Show rank chart
    st.plotly_chart(rank_fig, use_container_width=True)
    
    # Add rank explanation
    st.caption("* Lower ranks are better (1st place = Rank 1)")
    st.caption("* Average Rank shows consistency, Best Rank shows peak performance")

def create_game_history_visualization(game_history, player_list):
    """
    Create game history visualization showing player performance over time.
    
    Args:
        game_history: List of game history data from database
        player_list: List of player names to include in visualization
    """
    st.markdown("### Performance Over Time")
    
    # Process game history data
    history_data = []
    
    for game in game_history:
        player = game[0]
        game_id = game[1]
        start_time = game[2]
        rank = game[3]
        income = game[4]
        
        history_data.append({
            "Player": player,
            "Game ID": game_id,
            "Game Date": start_time,
            "Rank": rank,
            "Income": income
        })
    
    # Create DataFrame from history data
    history_df = pd.DataFrame(history_data)
    
    # Convert start time to datetime
    history_df["Game Date"] = pd.to_datetime(history_df["Game Date"])
    
    # Sort by game date
    history_df = history_df.sort_values("Game Date")
    
    # Create rank history chart
    rank_history_fig = px.line(
        history_df,
        x="Game Date",
        y="Rank",
        color="Player",
        title="Player Rank History (Lower is Better)",
        markers=True,
        color_discrete_sequence=LINE_CHART_COLORS,
        labels={"Game Date": "Game Date", "Rank": "Rank Position", "Player": "Player"}
    )
    
    # Improve layout
    rank_history_fig.update_layout(
        xaxis_title="Game Date",
        yaxis_title="Rank Position",
        legend_title="Player",
        yaxis=dict(autorange="reversed")  # Reverse y-axis for ranks (1 at top)
    )
    
    # Show rank history chart
    st.plotly_chart(rank_history_fig, use_container_width=True)
    
    # Create income history chart
    income_history_fig = px.line(
        history_df,
        x="Game Date",
        y="Income",
        color="Player",
        title="Player Income History",
        markers=True,
        color_discrete_sequence=LINE_CHART_COLORS,
        labels={"Game Date": "Game Date", "Income": "Income (won)", "Player": "Player"}
    )
    
    # Improve layout
    income_history_fig.update_layout(
        xaxis_title="Game Date",
        yaxis_title="Income (won)",
        legend_title="Player"
    )
    
    # Add zero reference line
    income_history_fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="grey")
    
    # Show income history chart
    st.plotly_chart(income_history_fig, use_container_width=True)
    
    # Add explanation
    st.caption("* Charts show performance trends over time")
    st.caption("* For ranks, lower is better (1st place = Rank 1)")
    st.caption("* For income, positive values (above zero line) indicate profit") 