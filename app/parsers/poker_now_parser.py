import csv
import re
import pandas as pd
from datetime import datetime
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PokerNowLogParser:
    """Parser for PokerNow poker game log files."""
    
    def __init__(self, log_file_path: str):
        """Initialize the parser with the log file path."""
        self.log_file_path = log_file_path
        self.game_data = []
        self.sorted_game_data = []  # Will hold time-sorted data
        self.player_names = set()
        self.player_ids = {}  # Will map player names to IDs
        self.player_stats = {}
        self.game_start_time = None
        self.game_end_time = None
        self.total_hands = 0  # Track total hands played
        self.hand_data = {}  # Will store data about each hand
        
    def parse(self) -> Dict[str, Any]:
        """Parse the log file and extract all relevant information."""
        self._read_log_file()
        self._sort_data_by_time()  # Sort data chronologically
        self._extract_player_names_and_ids()
        self._process_game_period()
        self._process_hands()
        self._calculate_player_stats()
        
        return self._format_results()
    
    def _read_log_file(self) -> None:
        """Read the log file and store the data."""
        logger.info(f"Reading log file: {self.log_file_path}")
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip the header row
            next(reader, None)
            for row in reader:
                if len(row) >= 3:  # Ensure the row has the expected structure
                    # Store the raw entry without stripping quotes
                    entry = row[0]
                    timestamp = row[1]
                    order = row[2]
                    self.game_data.append({
                        'entry': entry,
                        'timestamp': timestamp,
                        'order': order
                    })
        logger.info(f"Read {len(self.game_data)} log entries")
                    
    def _sort_data_by_time(self) -> None:
        """Sort the game data chronologically by timestamp."""
        logger.info("Sorting log entries by timestamp")
        # Convert timestamp strings to datetime objects for proper sorting
        for entry in self.game_data:
            if entry['timestamp'] != 'at':  # Skip header if present
                try:
                    entry['datetime'] = datetime.fromisoformat(entry['timestamp'].rstrip('Z'))
                except ValueError:
                    # If there's an issue with the timestamp, use a default
                    entry['datetime'] = datetime.min
        
        # Sort the data by timestamp (ascending order - oldest first)
        self.sorted_game_data = sorted(self.game_data, key=lambda x: x.get('datetime', datetime.min))
        logger.info("Data sorted chronologically")
    
    def _extract_player_names_and_ids(self) -> None:
        """Extract unique player names and their IDs from the log."""
        logger.info("Extracting player names and IDs")
        # This pattern will match both the player name and ID in a single match
        player_pattern = re.compile(r'"([^@]+) @ ([^"]+)"')
        
        for entry in self.sorted_game_data:
            matches = player_pattern.findall(entry['entry'])
            for match in matches:
                if len(match) == 2:
                    player_name = match[0].strip()
                    player_id = match[1].strip()
                    self.player_names.add(player_name)
                    # Store the ID for each player
                    if player_name not in self.player_ids:
                        self.player_ids[player_name] = player_id
        
        logger.info(f"Found {len(self.player_names)} players: {', '.join(self.player_names)}")
        for player, player_id in self.player_ids.items():
            logger.info(f"Player: {player}, ID: {player_id}")
    
    def _process_game_period(self) -> None:
        """Process the game period (start and end time)."""
        if not self.sorted_game_data:
            return
            
        # Get the first and last timestamps
        self.game_start_time = self.sorted_game_data[0].get('datetime', None)
        self.game_end_time = self.sorted_game_data[-1].get('datetime', None)
        logger.info(f"Game period: {self.game_start_time} to {self.game_end_time}")
    
    def _process_hands(self) -> None:
        """Process all hands in the game and collect data about each hand."""
        logger.info("Processing hand data")
        # Initialize tracking variables
        current_hand_id = None
        current_hand_number = None
        
        # Process all entries in chronological order
        for i, entry in enumerate(self.sorted_game_data):
            entry_text = entry['entry']
            
            # Check for new hand start
            hand_match = re.search(r'-- starting hand #(\d+) \(id: ([a-z0-9]+)\)', entry_text)
            if hand_match:
                current_hand_number = int(hand_match.group(1))
                current_hand_id = hand_match.group(2)
                # Initialize new hand data
                self.hand_data[current_hand_id] = {
                    'number': current_hand_number,
                    'players_involved': set(),
                    'winners': set(),
                    'pot_amounts': []
                }
                # Update total hand count
                if current_hand_number > self.total_hands:
                    self.total_hands = current_hand_number
                logger.debug(f"Started hand #{current_hand_number} (ID: {current_hand_id})")
            
            # If we have a current hand, process player actions
            if current_hand_id and current_hand_id in self.hand_data:
                # Check for player actions in current hand
                for player_name, player_id in self.player_ids.items():
                    # Pattern to match player taking action in this hand
                    action_pattern = rf'"{re.escape(player_name)} @ {re.escape(player_id)}"'
                    if re.search(action_pattern, entry_text):
                        self.hand_data[current_hand_id]['players_involved'].add(player_name)
                        
                        # Check for pot collection (winning)
                        if "collected" in entry_text and "from pot" in entry_text:
                            # Extract the pot amount
                            pot_match = re.search(rf'"{re.escape(player_name)} @ {re.escape(player_id)}" collected (\d+) from pot', entry_text)
                            if pot_match:
                                pot_amount = int(pot_match.group(1))
                                # Log the winner
                                self.hand_data[current_hand_id]['winners'].add(player_name)
                                self.hand_data[current_hand_id]['pot_amounts'].append(pot_amount)
                                logger.debug(f"Hand #{current_hand_number}: {player_name} collected {pot_amount}")
        
        # Log some statistics about hands and winners
        winner_counts = {player: 0 for player in self.player_names}
        hand_counts = {player: 0 for player in self.player_names}
        
        for hand_id, data in self.hand_data.items():
            for player in data['winners']:
                winner_counts[player] += 1
            for player in data['players_involved']:
                hand_counts[player] += 1
                
        total_winners = sum(len(data['winners']) for data in self.hand_data.values())
        logger.info(f"Processed {len(self.hand_data)} hands with {total_winners} wins recorded")
        
        # Log player participation in hands
        for player in self.player_names:
            logger.info(f"Player {player}: played {hand_counts[player]} hands, won {winner_counts[player]} hands")
    
    def _calculate_player_stats(self) -> None:
        """Calculate statistics for each player."""
        logger.info("Calculating player statistics")
            
        # Track players' chip counts at each stack update
        player_chip_history = {player: [] for player in self.player_names}
        
        # Process the sorted game data to capture chip history
        for entry in self.sorted_game_data:
            entry_text = entry['entry']
            # Look for stack updates for all players
            stack_match = re.search(r'Player stacks: (.*)', entry_text)
            if stack_match:
                stack_line = stack_match.group(1)
                # Find all stack updates in this line
                stack_updates = re.findall(r'"([^@]+) @ ([^"]+)" \((\d+)\)', stack_line)
                for update in stack_updates:
                    if len(update) >= 3:
                        player_name = update[0].strip()
                        chips = int(update[2])
                        timestamp = entry.get('datetime')
                        if player_name in self.player_names:
                            player_chip_history[player_name].append((timestamp, chips))
        
        # Count wins for each player
        player_wins = {player: 0 for player in self.player_names}
        player_hands = {player: 0 for player in self.player_names}
        
        for hand_id, data in self.hand_data.items():
            for player in data['winners']:
                player_wins[player] += 1
            for player in data['players_involved']:
                player_hands[player] += 1
        
        # Calculate player statistics based on hand data
        for player_name in self.player_names:
            # Get final chip count
            final_chips = 0
            if player_chip_history[player_name]:
                final_chips = player_chip_history[player_name][-1][1]
            
            # Get rebuy amount
            rebuy_amount = self._calculate_rebuy_amount(player_name)
            
            # Store player stats
            self.player_stats[player_name] = {
                'total_rebuy_amt': rebuy_amount,
                'total_win_cnt': player_wins[player_name],
                'total_hand_cnt': player_hands[player_name],
                'total_chip': final_chips,
                'rank': None,  # Will be calculated later
                'total_income': final_chips - rebuy_amount,
                'out_time': self._get_out_time(player_name, player_chip_history)
            }
            
            logger.info(f"Stats for {player_name}: chips={final_chips}, rebuy={rebuy_amount}, "
                       f"hands={player_hands[player_name]}, wins={player_wins[player_name]}")
        
        # Calculate rankings
        self._calculate_rankings()
    
    def _calculate_rebuy_amount(self, player_name: str) -> int:
        """Calculate the total rebuy amount for a player."""
        # For the initial buy-in and rebuys, we need to look at the initial stack and any increases
        initial_stack_pattern = rf'The player "{re.escape(player_name)} @ [^"]+" joined the game with a stack of (\d+)'
        
        # Add patterns for away status and return
        away_pattern = rf'The player "{re.escape(player_name)} @ [^"]+" stands up'
        return_pattern = rf'The player "{re.escape(player_name)} @ [^"]+" sits back with the stack of (\d+)'
        
        # Define a new direct rebuy detection pattern (adding chips)
        rebuy_pattern = rf'The player "{re.escape(player_name)} @ [^"]+" (?:stand|sit)s with the stack of (\d+)'
        stack_update_pattern = rf'"{re.escape(player_name)} @ [^"]+" \((\d+)\)'
        
        total_rebuy = 0
        rebuy_details = []  # Store detailed history for debugging
        
        # Track player status and stack
        first_join = True
        away_status = False
        initial_buyin = 20000  # Default initial buy-in
        current_stack = 0
        last_stack = 0
        rebuy_count = 0  # Explicitly track rebuy count
        
        # Track all player stack changes
        stack_history = []
        
        for entry in self.sorted_game_data:
            entry_text = entry['entry']
            timestamp = entry.get('datetime', '?')
            
            # Check for stack updates in "Player stacks:" entries
            if "Player stacks:" in entry_text:
                stack_match = re.search(stack_update_pattern, entry_text)
                if stack_match:
                    new_stack = int(stack_match.group(1))
                    if current_stack > 0 and new_stack > current_stack and not away_status:
                        # If stack increases while player is active, it's likely a rebuy
                        stack_increase = new_stack - current_stack
                        if stack_increase >= 15000:  # Consider substantial increases as rebuys
                            rebuy_count += 1
                            rebuy_details.append((timestamp, stack_increase, f"Stack increase (likely rebuy #{rebuy_count})"))
                            logger.debug(f"Detected rebuy for {player_name}: +{stack_increase} at {timestamp}")
                            total_rebuy += stack_increase
                    
                    # Update current stack
                    last_stack = current_stack
                    current_stack = new_stack
                    stack_history.append((timestamp, current_stack, "Stack update"))
            
            # Initial join or actual rebuy (new participation in game)
            join_match = re.search(initial_stack_pattern, entry_text)
            if join_match:
                amount = int(join_match.group(1))
                
                # Save initial buy-in amount for the first join
                if first_join:
                    initial_buyin = amount
                    current_stack = amount
                    last_stack = amount
                    total_rebuy = amount  # Initial buy-in is counted in total
                    rebuy_details.append((timestamp, amount, "Initial buy-in"))
                    logger.debug(f"Initial buy-in for {player_name}: {amount} at {timestamp}")
                    first_join = False
                    stack_history.append((timestamp, current_stack, "Initial join"))
                elif not away_status:
                    # This is a genuine rebuy - player rejoined without being away
                    rebuy_count += 1
                    total_rebuy += amount
                    rebuy_details.append((timestamp, amount, f"New join/rebuy #{rebuy_count}"))
                    logger.debug(f"Rebuy #{rebuy_count} for {player_name}: +{amount} at {timestamp}")
                    current_stack = amount
                    last_stack = amount
                    stack_history.append((timestamp, current_stack, "New join"))
                else:
                    # Don't count return from away as rebuy
                    rebuy_details.append((timestamp, amount, "Return from away"))
                    logger.debug(f"Player {player_name} returned with {amount} at {timestamp} (Not a rebuy)")
                    away_status = False
                    current_stack = amount
                    last_stack = amount
                    stack_history.append((timestamp, current_stack, "Return from away"))
            
            # Track away status
            if re.search(away_pattern, entry_text):
                away_status = True
                rebuy_details.append((timestamp, current_stack, "Went away"))
                logger.debug(f"Player {player_name} went away with stack {current_stack} at {timestamp}")
                stack_history.append((timestamp, current_stack, "Went away"))
            
            # Track return from away status
            return_match = re.search(return_pattern, entry_text)
            if return_match:
                amount = int(return_match.group(1))
                away_status = False
                
                # If the stack increased significantly during away, it might be a rebuy
                if amount > (last_stack + 15000):  # Significant increase threshold
                    rebuy_count += 1
                    stack_increase = amount - last_stack
                    rebuy_details.append((timestamp, stack_increase, f"Stack increase while away (likely rebuy #{rebuy_count})"))
                    logger.debug(f"Detected rebuy during away for {player_name}: +{stack_increase} at {timestamp}")
                    total_rebuy += stack_increase
                
                current_stack = amount
                rebuy_details.append((timestamp, amount, "Sat back"))
                logger.debug(f"Player {player_name} sat back with {amount} at {timestamp}")
                stack_history.append((timestamp, current_stack, "Sat back"))
            
            # Check for direct rebuys (rare but possible)
            rebuy_match = re.search(rebuy_pattern, entry_text)
            if rebuy_match and not join_match and not return_match:  # Avoid duplicate matches
                amount = int(rebuy_match.group(1))
                if amount > (current_stack + 15000):  # Significant increase threshold
                    rebuy_count += 1
                    stack_increase = amount - current_stack
                    rebuy_details.append((timestamp, stack_increase, f"Direct rebuy #{rebuy_count}"))
                    logger.debug(f"Direct rebuy for {player_name}: +{stack_increase} at {timestamp}")
                    total_rebuy += stack_increase
                current_stack = amount
        
        # Validate rebuy count with a more robust general method
        # Most games have players doing 0 or 1 rebuys, so if our count is much higher,
        # it's likely due to detection errors rather than actual multiple rebuys
        if rebuy_count > 2:
            max_expected_rebuys = 2  # Most players don't do more than 2 rebuys in typical games
            logger.info(f"Detected unusually high rebuy count ({rebuy_count}) for {player_name}")
            
            # If we detect more than 2 rebuys, let's verify by checking if there's a clear pattern
            # of stack increases that match exactly to initial_buyin
            exact_rebuy_count = 0
            for i, (_, stack, event) in enumerate(stack_history):
                if i > 0 and event in ["New join", "Sat back", "Stack update"]:
                    prev_stack = stack_history[i-1][1]
                    if abs(stack - prev_stack - initial_buyin) < 1000:  # Allow small variance
                        exact_rebuy_count += 1
                        logger.info(f"Found exact rebuy pattern: {prev_stack} -> {stack} ({event})")
            
            # If we found exact matches for rebuys, use that count instead
            if exact_rebuy_count > 0 and exact_rebuy_count < rebuy_count:
                logger.info(f"Correcting rebuy count from {rebuy_count} to {exact_rebuy_count} based on stack pattern analysis")
                rebuy_count = exact_rebuy_count
                # Recalculate total_rebuy accordingly
                total_rebuy = initial_buyin + (rebuy_count * initial_buyin)
            # If we still have an unusual count, use a conservative approach
            elif rebuy_count > max_expected_rebuys:
                logger.info(f"Using conservative rebuy count (1) for {player_name} instead of detected {rebuy_count}")
                rebuy_count = 1
                total_rebuy = initial_buyin + (rebuy_count * initial_buyin)
        
        # Add detailed logging for debugging 
        logger.info(f"===== DEBUG INFO FOR {player_name} =====")
        logger.info(f"Initial buy-in: {initial_buyin}")
        logger.info(f"Tracked rebuy count: {rebuy_count}")
        logger.info(f"Total rebuy amount: {total_rebuy}")
        logger.info(f"Traditional rebuy count calculation: {(total_rebuy - initial_buyin) / initial_buyin:.2f}")
        logger.info(f"Detailed activity history:")
        for i, (timestamp, amount, action_type) in enumerate(rebuy_details):
            logger.info(f"  #{i+1}: {action_type} - {amount} at {timestamp}")
        logger.info(f"Stack history:")
        for i, (timestamp, stack, event) in enumerate(stack_history):
            logger.info(f"  #{i+1}: {event} - {stack} at {timestamp}")
        logger.info("=====================================")
        
        # Return the adjusted total rebuy amount
        return total_rebuy
    
    def _get_out_time(self, player_name: str, 
                     chip_history: Dict[str, List[Tuple[datetime, int]]]) -> Optional[datetime]:
        """
        Get the time when a player went out (if they did).
        
        Args:
            player_name: The name of the player
            chip_history: Dictionary mapping player names to lists of (timestamp, chip count) tuples
        
        Returns:
            The timestamp when the player went out, or None if they didn't go out
        """
        # If the player has chip history and their last recorded chip count is 0, they went out
        history = chip_history.get(player_name, [])
        if history and history[-1][1] == 0:
            return history[-1][0]
            
        # Otherwise, look for the last action from the player
        last_action_time = None
        if player_name in self.player_ids:
            player_id = self.player_ids[player_name]
            action_pattern = rf'{re.escape(player_name)} @ {re.escape(player_id)}"'
            
            for entry in self.sorted_game_data:
                if re.search(action_pattern, entry['entry']):
                    last_action_time = entry.get('datetime')
                
        return last_action_time
    
    def _calculate_rankings(self) -> None:
        """Calculate the rankings for all players based on the specified rules."""
        logger.info("Calculating player rankings")
        # First, identify players who went out during the game (their final chips are 0)
        eliminated_players = [p for p in self.player_names 
                             if self.player_stats[p]['total_chip'] == 0]
        
        # Players who still had chips at the end
        active_players = [p for p in self.player_names 
                         if p not in eliminated_players and self.player_stats[p]['total_chip'] > 0]
        
        # Sort eliminated players by out_time (earliest out gets lowest rank)
        eliminated_players.sort(key=lambda p: self.player_stats[p]['out_time'] or datetime.max)
        
        # Sort active players by income (highest income gets highest rank)
        # Changed from total_chip to total_income for sorting active players
        active_players.sort(key=lambda p: self.player_stats[p]['total_income'], reverse=True)
        
        # Assign ranks (1 is the highest rank)
        rank = 1
        
        # First assign ranks to active players (highest ranks)
        for player in active_players:
            self.player_stats[player]['rank'] = rank
            logger.info(f"Rank {rank}: {player} (active with {self.player_stats[player]['total_chip']} chips, "
                       f"income: {self.player_stats[player]['total_income']})")
            rank += 1
            
        # Then assign ranks to eliminated players (lowest ranks)
        for player in eliminated_players:
            self.player_stats[player]['rank'] = rank
            logger.info(f"Rank {rank}: {player} (eliminated)")
            rank += 1
    
    def _format_results(self) -> Dict[str, Any]:
        """Format the final results."""
        results = {
            'game_period': {
                'start': self.game_start_time,
                'end': self.game_end_time
            },
            'total_hands': self.total_hands,
            'players': []
        }
        
        for player_name in self.player_names:
            player_data = {
                'user_name': player_name,
                'rank': self.player_stats[player_name]['rank'],
                'total_rebuy_amt': self.player_stats[player_name]['total_rebuy_amt'],
                'total_win_cnt': self.player_stats[player_name]['total_win_cnt'],
                'total_hand_cnt': self.player_stats[player_name]['total_hand_cnt'],
                'total_chip': self.player_stats[player_name]['total_chip'],
                'total_income': self.player_stats[player_name]['total_income']
            }
            results['players'].append(player_data)
            
        # Sort players by rank for easier reading
        results['players'].sort(key=lambda p: p['rank'])
            
        return results


def parse_log_file(file_path: str) -> Dict[str, Any]:
    """Parse a PokerNow log file and return the extracted data."""
    parser = PokerNowLogParser(file_path)
    return parser.parse() 