import json
import os
from datetime import datetime

# The file where all daily progress will be saved.
HISTORY_FILE = "history.json"

class HistoryAgent:
    """Manages persistence for daily task data and handles history retrieval."""
    
    def __init__(self):
        pass

    def _load_all_history(self):
        """Loads all existing history from the JSON file."""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                try:
                    # Load the history structure: {username: {date: {task_data}}}
                    return json.load(f)
                except json.JSONDecodeError:
                    # Return empty dict if file is corrupt or empty
                    return {}
        return {}
    
    def _save_all_history(self, data):
        """Saves all history to the JSON file."""
        with open(HISTORY_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def save_date(self, username, date, df):
        """Saves a DataFrame (daily progress) for a specific user and date."""
        data = self._load_all_history()
        
        # Convert DataFrame to a serializable dictionary format for storage
        daily_data = df.to_dict(orient='list')

        if username not in data:
            data[username] = {}
            
        data[username][date] = daily_data
        self._save_all_history(data)

    # -------------------------------------------------------------
    # FIX: load_last_n_days method
    # -------------------------------------------------------------
    def load_last_n_days(self, username, n=7):
        """Loads the last N days of history data for a specific user."""
        all_data = self._load_all_history()
        
        if username not in all_data:
            return {}
        
        user_history = all_data[username]
        
        # Sort dates chronologically (most recent first)
        # Dates must be sorted as strings, assuming YYYY-MM-DD format
        sorted_dates = sorted(user_history.keys(), reverse=True)
        
        # Select the last N days
        last_n_history = {}
        for date_str in sorted_dates[:n]:
            last_n_history[date_str] = user_history[date_str]
            
        return last_n_history

    def is_end_of_week(self):
        """Helper to determine if a weekly reflection should be triggered (e.g., on Sunday)."""
        # Monday is 0, Sunday is 6
        return datetime.now().weekday() == 6