"""
Prize calculator module for the Poker Stats Dashboard.
Handles calculations related to prize distribution, fees, and player payouts.
"""

from app.config import ENTRY_FEE, FREE_REBUYS, REBUY_FEE

def calculate_prize_distribution(players_df):
    """
    Calculate the prize distribution based on specified rules.
    
    Args:
        players_df: DataFrame containing player information with at least 'Rank' and 'Rebuy Count' columns
        
    Returns:
        tuple: (prizes, prize_percentages, total_prize_pool)
            - prizes: Dict mapping ranks to prize amounts
            - prize_percentages: Dict mapping ranks to percentage of prize pool
            - total_prize_pool: Total prize pool amount
    """
    # Get total players
    player_count = len(players_df)
    
    # Calculate total prize pool
    total_prize_pool = player_count * ENTRY_FEE  # Base entry fees
    
    # Add additional rebuy fees to the prize pool
    for _, player in players_df.iterrows():
        rebuy_count = player['Rebuy Count']
        # Only charge for rebuys beyond the free limit
        if rebuy_count > FREE_REBUYS:
            additional_rebuys = rebuy_count - FREE_REBUYS
            total_prize_pool += additional_rebuys * REBUY_FEE
    
    # Calculate prize distribution percentages in arithmetic sequence
    if player_count > 1:
        # Calculate the common difference for the arithmetic sequence
        # If we have n players, and want percentages p1, p2, ..., pn where:
        # - The sum p1 + p2 + ... + pn = 100%
        # - pn = 0 (last place gets 0%)
        # - p1 > p2 > ... > p(n-1) > pn = 0 with equal differences
        
        # For arithmetic sequence with last term = 0:
        # p1, p2, ..., p(n-1), pn = 0
        # Common difference = d
        # p1 = (n-1)d
        # The sum: n/2 * [(n-1)d + 0] = 100%
        # (n-1)nd/2 = 100
        # d = 200 / (n(n-1))
        
        # Calculate common difference for equal interval percentages
        common_diff = 200 / (player_count * (player_count - 1))
        
        # Calculate percentages for each rank
        percentages = {}
        for rank in range(1, player_count + 1):
            # Last place gets 0%, first place gets the most
            if rank == player_count:
                # Last place always gets 0%
                percentage = 0
            else:
                # Others get percentages in equal intervals
                percentage = (player_count - rank) * common_diff
            
            percentages[rank] = round(percentage, 2)
            
        # Adjust to ensure sum is exactly 100%
        total_pct = sum(percentages.values())
        if abs(total_pct - 100) > 0.01:  # If not very close to 100%
            # Adjust first place to make sum exactly 100%
            percentages[1] = round(percentages[1] + (100 - total_pct), 2)
            
        # Calculate prize amounts - truncate to nearest 100 won
        prizes = {}
        prize_percentages = {}
        total_truncated = 0
        
        for rank in range(1, player_count + 1):
            percentage = percentages[rank]
            # Calculate exact amount
            exact_prize = total_prize_pool * percentage / 100
            # Truncate to nearest 100 won (floor to hundreds)
            truncated_prize = int(exact_prize // 100 * 100)
            
            if rank > 1:  # For all except first place
                prizes[rank] = truncated_prize
                total_truncated += truncated_prize
            
            prize_percentages[rank] = percentage
        
        # First place gets the remainder to ensure total matches pool exactly
        prizes[1] = total_prize_pool - total_truncated
        
        return prizes, prize_percentages, total_prize_pool
        
    else:
        # If there's only one player, they get the entire pool (100%)
        return {1: total_prize_pool}, {1: 100.0}, total_prize_pool

def calculate_player_fees(rebuy_count):
    """
    Calculate the fees a player needs to pay based on their rebuy count.
    
    Args:
        rebuy_count: Number of rebuys the player has made
        
    Returns:
        tuple: (entry_fee, additional_fee, total_fee)
    """
    entry_fee = ENTRY_FEE
    
    # Calculate additional fees for rebuys beyond the free limit
    if rebuy_count > FREE_REBUYS:
        additional_rebuys = rebuy_count - FREE_REBUYS
        additional_fee = additional_rebuys * REBUY_FEE
    else:
        additional_fee = 0
        
    total_fee = entry_fee + additional_fee
    
    return entry_fee, additional_fee, total_fee 