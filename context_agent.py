import pandas as pd
from datetime import datetime, timedelta

class ContextAgent:
    """Tracks task completion, rescheduling, and computes progress."""
    def __init__(self):
        # Initial columns now include Time Slot for consistency
        self.df = pd.DataFrame(columns=["Task", "Priority", "Time", "Completed", "Time Slot"])

    def load_tasks(self, plan):
        # Assuming plan structure is available or passed correctly
        self.df = pd.DataFrame([{
            "Task": t.description,
            "Priority": t.priority,
            "Time": t.time_estimate,
            "Completed": False
        } for t in plan.tasks])
        # Ensure 'Time Slot' column exists after load, even if empty initially
        if "Time Slot" not in self.df.columns:
            self.df["Time Slot"] = ""
        return self.df

    def update_completion(self, idx, done):
        """Mark task as complete."""
        self.df.at[idx, "Completed"] = done

    # ------------------------------------------------------------------
    # NEW: Chronological Sort Helper
    # ------------------------------------------------------------------
    def _chronological_sort(self):
        """Sorts the DataFrame based on the start time in the 'Time Slot' column."""
        
        def sort_key(slot):
            """Helper function to extract datetime object for sorting."""
            if pd.isna(slot) or 'N/A' in str(slot):
                return datetime.max
            try:
                # Extract the start time string (e.g., '08:00 AM')
                start_str = str(slot).split(' - ')[0].strip()
                return datetime.strptime(start_str, '%I:%M %p')
            except Exception:
                # Put invalid time slots at the end
                return datetime.max

        self.df = self.df.sort_values(
            by="Time Slot", 
            key=lambda x: x.apply(sort_key), 
            ignore_index=True
        )

    # ------------------------------------------------------------------
    # FIX: Reschedule Task with Auto-Sort
    # ------------------------------------------------------------------
    def reschedule_task(self, idx):
        """Shift a task’s time slot later (~30%) and show justification."""
        if self.df.empty or "Time Slot" not in self.df.columns:
            return "The plan is empty or has no time slots to reschedule."
        
        # Ensure idx is valid (convert to integer index if needed for robustness)
        if idx >= len(self.df) or idx < 0:
             return f"Task index {idx} is invalid."
        
        # If the DF index is not integer-based, we need to use .iloc
        try:
             time_slot = self.df.iloc[idx].loc["Time Slot"]
             task_name = self.df.iloc[idx].loc["Task"]
        except IndexError:
             return f"Task index {idx} is out of bounds."

        if 'N/A' in time_slot:
            return f"Task '{task_name}' is already marked as N/A and cannot be rescheduled."

        try:
            start_str, end_str = time_slot.split(" - ")
            start = datetime.strptime(start_str.strip(), "%I:%M %p")
            end = datetime.strptime(end_str.strip(), "%I:%M %p")
            duration = end - start
            
            # Calculate 30% shift
            shift = timedelta(minutes=duration.total_seconds() / 60 * 0.3)
            
            new_start = start + shift
            new_end = end + shift
            new_slot = f"{new_start.strftime('%I:%M %p')} - {new_end.strftime('%I:%M %p')}"
            
            # Update the time slot using .iloc for row safety
            self.df.iloc[idx, self.df.columns.get_loc("Time Slot")] = new_slot
            
            # Perform the chronological sort
            self._chronological_sort() # <-- ADDED: Sorting the DataFrame after update
            
            return f"Task '{task_name}' rescheduled by ~30% to **{new_slot}**. List sorted."
        
        except ValueError:
            return f"Error parsing time slot '{time_slot}'. Task cannot be manually shifted."
        except Exception as e:
            return f"An unexpected error occurred during manual shift: {e}"

    def progress(self):
        """Calculate completion percentage."""
        if self.df.empty:
            return 0.0
        completed = self.df["Completed"].sum()
        total = len(self.df)
        return (completed / total) * 100