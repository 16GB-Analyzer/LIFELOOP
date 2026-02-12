import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys
import os
import json # New import for handling reflections archive
from dotenv import load_dotenv
from ics import Calendar, Event
import io

# ----------------------------------------------------------
# 🧩 Path & Environment Setup
# ----------------------------------------------------------
# Adjust path to import agents from the 'agents' subdirectory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "agents")))
load_dotenv()

# ----------------------------------------------------------
# 🧠 Import Agents
# ----------------------------------------------------------
# Ensure these files exist in your 'agents' directory.
from agents.user_agent import UserAgent
from agents.weekly_reflection_agent import WeeklyReflectionAgent
from agents.history_agent import HistoryAgent 
from agents.planner_agent import PlannerAgent
from agents.ai_scheduler import AIScheduler
from agents.context_agent import ContextAgent
from agents.reflection_agent import ReflectionAgent
from agents.visualization import plot_completion_bar, plot_status_pie 

def generate_ics_file(df, active_date):
    """
    Converts the LifeLoop DataFrame into an .ics calendar file with Timezone support.
    """
    c = Calendar()
    USER_TIMEZONE = 'US/Eastern' 

    if isinstance(active_date, datetime):
        base_date = active_date.date()
    else:
        base_date = active_date 

    for _, row in df.iterrows():
        time_slot = row['Time Slot']
        task_name = row['Task']
        
        # Skip rows without valid time slots
        if pd.isna(time_slot) or "N/A" in str(time_slot) or not time_slot:
            continue

        try:
            # Parse start and end times
            start_str, end_str = time_slot.split(" - ")
            start_time = datetime.strptime(start_str.strip(), "%I:%M %p").time()
            end_time = datetime.strptime(end_str.strip(), "%I:%M %p").time()

            # Combine to make naive datetime (Year-Month-Day Hour:Minute)
            start_dt_naive = datetime.combine(base_date, start_time)
            end_dt_naive = datetime.combine(base_date, end_time)

            # Handle overnight tasks
            if end_dt_naive < start_dt_naive:
                end_dt_naive += timedelta(days=1)

            start_dt = pd.Timestamp(start_dt_naive).tz_localize(USER_TIMEZONE).to_pydatetime()
            end_dt = pd.Timestamp(end_dt_naive).tz_localize(USER_TIMEZONE).to_pydatetime()

            # Create the Event
            e = Event()
            e.name = f"LifeLoop: {task_name}"
            e.begin = start_dt
            e.end = end_dt
            e.description = f"Priority: {row['Priority']}\nStatus: {'Done' if row['Completed'] else 'Pending'}"
            
            c.events.add(e)

        except Exception as e:
            print(f"Skipping row due to error: {e}")
            continue

    return c.serialize()

# ----------------------------------------------------------
# 🎨 Aesthetic Streamlit Page Config & Custom CSS (Dark Theme)
# ----------------------------------------------------------
st.set_page_config(
    page_title="♾️ LifeLoop | Daily AI Planner",
    layout="wide",
    page_icon="♾️", 
    initial_sidebar_state="expanded"
)

# Custom CSS for a clean, professional, dark UI
st.markdown("""
<style>
/* Base Dark Theme Overrides for a clean look */
.main {
    background-color: #0d1117; /* GitHub Dark Theme Background */
    color: #c9d1d9;
}
.stSidebar {
    background-color: #161b22; /* Sidebar is slightly different */
    padding-top: 2rem;
}

/* Headings and Titles - Subtle, professional accent */
h1, h2, h3 {
    color: #58a6ff; /* Soft Blue Accent */
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    border-bottom: 1px solid #21262d; /* Subtle divider under main titles */
    padding-bottom: 5px;
}

/* Primary Button Styling (Gradient for CTA) */
.stButton>button {
    background: linear-gradient(135deg, #2f81f7, #58a6ff);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 600;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #58a6ff, #2f81f7);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Secondary Button Styling (for smaller actions) */
.stDownloadButton > button {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
}

/* Text Area and Input fields */
.stTextArea, .stTextInput {
    background-color: #161b22;
    border-radius: 6px;
    color: #c9d1d9;
}

/* Data Editor/Table (Key for a clean plan view) */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
    background-color: #1e2632; 
    border: 1px solid #30363d;
}
.stDataFrame th, .stDataFrame td {
    color: #c9d1d9 !important;
}

/* Metrics/Progress Boxes - Use primary color for value */
[data-testid="stMetricValue"] {
    color: #58a6ff !important;
    font-size: 1.5rem;
}

/* Custom separator */
.st_divider {
    border-top: 1px solid #21262d;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# 🔁 Session State & Agent Initialization
# ----------------------------------------------------------
# Initialize all agents and session variables
if "user_agent" not in st.session_state:
    st.session_state.user_agent = UserAgent()
if "weekly_agent" not in st.session_state:
    st.session_state.weekly_agent = WeeklyReflectionAgent()
if "history_agent" not in st.session_state:
    st.session_state.history_agent = HistoryAgent()
if "planner" not in st.session_state:
    st.session_state.planner = PlannerAgent()
if "scheduler" not in st.session_state:
    st.session_state.scheduler = AIScheduler()
if "reflector" not in st.session_state:
    st.session_state.reflector = ReflectionAgent()
if "context" not in st.session_state:
    st.session_state.context = ContextAgent()

# Two-Step Planning State
if "df" not in st.session_state:         # Final, Scheduled Plan
    st.session_state.df = pd.DataFrame() 
if "draft_df" not in st.session_state:   # Preliminary Plan (Before Scheduling)
    st.session_state.draft_df = pd.DataFrame()

if "mood_log" not in st.session_state:
    st.session_state.mood_log = []
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'last_processed_mood' not in st.session_state:
    st.session_state.last_processed_mood = "Select Mood" 

# New states for History Backfill
if 'backfill_mode' not in st.session_state:
    st.session_state.backfill_mode = False
if 'backfill_date' not in st.session_state:
    st.session_state.backfill_date = None

# New state for Weekly Insights
if 'weekly_summary' not in st.session_state:
    st.session_state.weekly_summary = None

# Local agent references
context = st.session_state.context
planner = st.session_state.planner
scheduler = st.session_state.scheduler
reflector = st.session_state.reflector
history_agent = st.session_state.history_agent
weekly_agent = st.session_state.weekly_agent


# ----------------------------------------------------------
# 👤 User Login/Switch Logic (Sidebar)
# ----------------------------------------------------------
st.sidebar.title("🔑 User Context")

new_username = st.sidebar.text_input(
    "Enter your Username", 
    value=st.session_state.username if st.session_state.username else "",
    placeholder="e.g., JaneDoe"
)

if st.sidebar.button("Login / Switch User", use_container_width=True):
    if new_username:
        # Clear data if switching users
        if st.session_state.username != new_username and st.session_state.logged_in:
            st.session_state.df = pd.DataFrame() 
            st.session_state.draft_df = pd.DataFrame()
            st.session_state.mood_log = []
            st.session_state.backfill_mode = False # Reset backfill mode
            st.session_state.backfill_date = None
            st.session_state.weekly_summary = None # Reset weekly summary
        
        st.session_state.username = new_username
        st.session_state.logged_in = True
        st.toast(f"Switched user to {new_username}!")
        st.rerun()
    else:
        st.sidebar.error("Please enter a username.")

if st.session_state.logged_in:
    username = st.session_state.username 
    st.sidebar.success(f"Active: **{username}**")
else:
    username = "Guest"
    st.sidebar.warning("Log in to save history.")

# ----------------------------------------------------------
# 📅 Main Content & Goal Input (DYNAMIC DATE LOGIC)
# ----------------------------------------------------------
st.title("♾️ LifeLoop: Your Adaptive Daily AI Planner")

# --- Dynamic Date Determination ---
is_backfilling = st.session_state.get('backfill_mode') and st.session_state.get('backfill_date')

if is_backfilling:
    # Use the selected backfill date if in backfill mode
    DISPLAY_DATE_KEY = st.session_state.backfill_date
    try:
        DISPLAY_DATE = datetime.strptime(DISPLAY_DATE_KEY, "%Y-%m-%d")
        header_title = f"Reviewing/Editing History for {DISPLAY_DATE.strftime('%A, %B %d, %Y')} 📜"
    except ValueError:
        DISPLAY_DATE = datetime.now()
        DISPLAY_DATE_KEY = DISPLAY_DATE.strftime("%Y-%m-%d")
        header_title = f"Let's design your most productive day 💫"
else:
    # Use today's date
    DISPLAY_DATE = datetime.now()
    DISPLAY_DATE_KEY = DISPLAY_DATE.strftime("%Y-%m-%d")
    header_title = f"Let's design your most productive day 💫"
    
st.subheader(f"Hello, {username}! {header_title}")
st.markdown(f"**Date:** {DISPLAY_DATE.strftime('%A, %B %d, %Y')}")

# Set the DATE_KEY used for history saving to the current display context
DATE_KEY = DISPLAY_DATE_KEY 

# ----------------------------------------------------------
# ⚙️ Sidebar Configuration
# ----------------------------------------------------------
st.sidebar.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
st.sidebar.subheader("Planner Settings")

# Scheduling Mode Selection
scheduling_mode = st.sidebar.selectbox(
    "Select Scheduling Mode",
    options=["AI (Full Control)", "Manual (Fixed Slots)", "Together (Prioritized)"],
    index=2, # Default to Together for the most robust immediate scheduling
    help="AI: Uses AI to assign optimal slots (read-only draft).\nManual: User enters tasks and time estimates (fully editable draft).\nTogether: Uses AI to prioritize, then user edits before scheduling (editable draft)."
)

# Time Inputs
st.sidebar.markdown("###### Work Window")
start_time_str = st.sidebar.text_input("Start Time (HH:MM AM/PM)", "09:00 AM")
end_time_str = st.sidebar.text_input("End Time (HH:MM AM/PM)", "07:00 PM")

time_valid = False
try:
    start_dt_time = datetime.strptime(start_time_str, "%I:%M %p").time()
    end_dt_time = datetime.strptime(end_time_str, "%I:%M %p").time()
    
    # Use the display date's date part for combine operation
    date_part = DISPLAY_DATE.date()
    start_dt = datetime.combine(date_part, start_dt_time)
    end_dt = datetime.combine(date_part, end_dt_time)
    
    # Handle end time being on the next day (e.g., 9 PM to 5 AM)
    if start_dt >= end_dt:
        end_dt += timedelta(days=1)
    
    time_valid = True
except ValueError:
    st.sidebar.error("Invalid time format. Use 'HH:MM AM/PM'.")


# Goal Input
with st.container(border=True):
    st.markdown("##### 🎯 Daily Focus")
    goal = st.text_area(
        "Enter your main goal for today:", 
        "Complete critical project deliverables and maintain a healthy work-life balance.",
        height=70,
        label_visibility="collapsed"
    )

# ----------------------------------------------------------
# 1. GENERATE DRAFT PLAN (TASK LIST) 
# ----------------------------------------------------------
# Only allow planning if we are on the current day (not backfilling)
if not is_backfilling:
    is_manual_mode = (scheduling_mode == "Manual (Fixed Slots)")
    button_label = "1. Create Manual Task List" if is_manual_mode else "1. Generate Draft Tasks (via AI)"

    if st.button(button_label, use_container_width=True, key="generate_draft_btn"):
        if not st.session_state.logged_in:
            st.error("Please log in with a username on the sidebar.")
        else:
            # Exit backfill mode when starting a new plan (already handled above, but good safeguard)
            st.session_state.backfill_mode = False
            st.session_state.backfill_date = None

            if is_manual_mode:
                st.toast("📋 Creating template for manual task entry. Please fill out your tasks, priority, and time.")
                # Template for manual entry
                df_draft = pd.DataFrame([
                    {"Task": "Enter your first task here...", "Priority": "High", "Time": "1 hour", "Completed": False, "Duration_min": 60},
                    {"Task": "Enter your second task here...", "Priority": "Medium", "Time": "30 min", "Completed": False, "Duration_min": 30}
                ])
                st.success("✅ Manual task template created. Fill it out below.")
                
            else: # AI (Full Control) or Together (Prioritized)
                with st.spinner("🧠 AI is drafting your task list..."):
                    plan = planner.generate_plan(goal)
                    df_draft = context.load_tasks(plan)
                
                # --- Duration Parsing Logic (Kept from original AI flow) ---
                task_minutes_list = []
                for dur in df_draft["Time"]:
                    mins = 0
                    try:
                        parts = dur.lower().split()
                        for i, part in enumerate(parts):
                            if 'hour' in part and i > 0:
                                try:
                                    num = int(parts[i - 1].replace('min', '').replace('hour', '').strip())
                                    mins += num * 60
                                except ValueError:
                                    if 'hour' in parts[i-1]: mins += 60
                            if 'min' in part and i > 0:
                                try:
                                    num = int(parts[i - 1].replace('min', '').replace('hour', '').strip())
                                    mins += num
                                except ValueError:
                                    if 'min' in parts[i-1]: mins += 30
                        if mins == 0: 
                            try:
                                mins = int(dur.split()[0])
                            except:
                                mins = 30
                    except:
                        mins = 30
                    
                    if mins <= 0: mins = 30 
                    task_minutes_list.append(mins)
                
                df_draft['Duration_min'] = task_minutes_list
                df_draft['Completed'] = False
                st.success("✅ Draft task list generated. Review and confirm below.")
                
            st.session_state.draft_df = df_draft
            st.session_state.df = pd.DataFrame() # Clear final plan
            st.rerun()


# ----------------------------------------------------------
# 2. REVIEW DRAFT PLAN (EDITABLE TABLE) - FIXED LOGIC
# ----------------------------------------------------------
if not st.session_state.draft_df.empty:
    st.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
    st.subheader("📝 Draft Plan Review (Step 2/3)")

    is_ai_full_control = (scheduling_mode == "AI (Full Control)")
    is_manual_mode = (scheduling_mode == "Manual (Fixed Slots)")
    is_together_mode = (scheduling_mode == "Together (Prioritized)")
    
    # --- Define Configuration Based on Mode ---
    if is_ai_full_control:
        st.markdown("🔒 **AI FULL CONTROL MODE:** Review the AI-generated tasks. **No editing** of Task, Priority, or Time is allowed.")
        editor_disabled_cols = ("Task", "Priority", "Time", "Completed") 
        num_rows_mode = "fixed"
        time_column_label = "Duration" 
        
    elif is_manual_mode:
        st.markdown("👀 **MANUAL MODE:** **Edit** the tasks, priority, and duration. You can add or delete rows.")
        editor_disabled_cols = ("Completed", ) # Allows editing Task, Priority, Time
        num_rows_mode = "dynamic"
        time_column_label = "Duration (e.g., '1 hour', '30 min')"
        
    elif is_together_mode: 
        # TOGETHER MODE: AI-generated tasks, but user can edit them before scheduling.
        st.markdown("✍️ **TOGETHER MODE:** **Edit** the AI-generated tasks, priority, and duration before scheduling.")
        editor_disabled_cols = ("Completed", ) # Allows editing Task, Priority, Time
        num_rows_mode = "fixed" 
        time_column_label = "Duration" 
        
    else:
        # Fallback 
        st.markdown("Configuration Error. Defaulting to read-only.")
        editor_disabled_cols = ("Task", "Priority", "Time", "Completed") 
        num_rows_mode = "fixed"
        time_column_label = "Duration" 
        
    # --- Consolidated Column Config Map (used by all modes) ---
    column_config_map = {
        "Completed": st.column_config.CheckboxColumn("Done", default=False, disabled=True),
        "Task": st.column_config.TextColumn("Task Description", required=True),
        "Priority": st.column_config.SelectboxColumn("Priority", options=["High", "Medium", "Low"], required=True),
        "Time": st.column_config.TextColumn(time_column_label, required=True),
    }
        
    # Hide Duration_min column
    df_for_editor = st.session_state.draft_df.drop(columns=['Duration_min'], errors='ignore')

    edited_draft_df = st.data_editor(
        df_for_editor,
        column_order=("Task", "Priority", "Time", "Completed"),
        column_config=column_config_map,
        disabled=editor_disabled_cols, # This is where the editability is globally set per mode
        use_container_width=True,
        num_rows=num_rows_mode,
        key="draft_plan_editor"
    )
    
    # --- Update st.session_state.draft_df based on editor results ---
    if not is_ai_full_control: 
        # This logic is applied whenever editing is allowed (Manual or Together)
        
        # Custom simple time parsing for user-entered time strings
        def simple_time_parse(dur_str):
            dur_str = str(dur_str).lower()
            mins = 0
            try:
                if 'hour' in dur_str:
                    # Look for a number before 'hour', default to 1 if none found
                    num_str = dur_str.split('hour')[0]
                    num = int(''.join(filter(str.isdigit, num_str.strip())) or 1)
                    mins += num * 60
                if 'min' in dur_str or 'minute' in dur_str:
                    # Look for a number before 'min', default to 30 if none found
                    num_str = dur_str.split('min')[0]
                    num = int(''.join(filter(str.isdigit, num_str.strip())) or 30)
                    mins += num
            except ValueError:
                # Fallback if parsing fails (e.g., user just writes "30")
                try:
                    mins = int(''.join(filter(str.isdigit, dur_str.strip())))
                except ValueError:
                    mins = 30
            return mins if mins > 0 else 30

        # Update the hidden Duration_min and the main draft_df
        st.session_state.draft_df = edited_draft_df.copy()
        # Only process Time column if it exists in the edited_draft_df
        if 'Time' in edited_draft_df.columns:
            st.session_state.draft_df['Duration_min'] = edited_draft_df['Time'].apply(simple_time_parse)
        st.session_state.draft_df['Completed'] = False # Ensure we start planning with False
        


    # ----------------------------------------------------------
    # 3. CONFIRM & SCHEDULE PLAN (TIME SLOT GENERATION)
    # ----------------------------------------------------------
    if st.button("2. Confirm & Schedule Plan", use_container_width=True, key="confirm_schedule_btn"):
        if not time_valid:
            st.error("Please fix the time format errors in the sidebar before scheduling.")
        else:
            with st.spinner(f"⏱️ Scheduling plan using {scheduling_mode} mode..."):
                
                df_to_schedule = st.session_state.draft_df.copy()
                total_task_minutes = df_to_schedule['Duration_min'].sum()
                
                # Scheduling Logic
                total_work_minutes = (end_dt - start_dt).total_seconds() / 60
                
                # Distribute breaks evenly across the entire time window
                num_tasks = len(df_to_schedule)
                if num_tasks > 0 and total_work_minutes > total_task_minutes:
                    total_free_time = total_work_minutes - total_task_minutes
                    break_slots = num_tasks 
                    inter_task_break_minutes = max(5, total_free_time / break_slots)
                else:
                    inter_task_break_minutes = 10 

                # Separate and prioritize tasks
                df_to_schedule['Is_Evening'] = df_to_schedule['Task'].str.lower().str.contains('dinner|evening|wind down|relax')
                
                # Use Priority to sort for initial scheduling
                df_to_schedule['Priority_Sort'] = df_to_schedule['Priority'].map({'High': 3, 'Medium': 2, 'Low': 1})
                df_to_schedule = df_to_schedule.sort_values(by=['Is_Evening', 'Priority_Sort'], ascending=[True, False]).reset_index(drop=True)

                tasks_order = df_to_schedule.index.tolist()
                
                final_slots = [""] * len(df_to_schedule)
                current_time = start_dt

                for i, task_idx in enumerate(tasks_order):
                    task_mins = int(df_to_schedule.loc[task_idx, 'Duration_min'])
                    
                    # Heuristic to push evening tasks later
                    if df_to_schedule.loc[task_idx, 'Is_Evening'] and current_time < (end_dt - timedelta(minutes=90)):
                        target_start = end_dt - timedelta(minutes=90) 
                        current_time = max(current_time, target_start)

                    end_time = current_time + timedelta(minutes=task_mins) 
                    
                    if end_time > end_dt:
                        final_slots[task_idx] = "N/A - Too Late"
                        continue
                    
                    final_slots[task_idx] = f"{current_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
                    
                    current_time = end_time + timedelta(minutes=int(inter_task_break_minutes)) 


                df_to_schedule["Time Slot"] = final_slots

                # Finalize the session state
                st.session_state.df = df_to_schedule.drop(columns=['Duration_min', 'Is_Evening', 'Priority_Sort'], errors='ignore')
                st.session_state.draft_df = pd.DataFrame() # Clear draft
                st.session_state.context.df = st.session_state.df # Update ContextAgent's DF
                st.success(f"✅ Final plan generated and scheduled using the '{scheduling_mode}' mode!")
                st.rerun()


# ----------------------------------------------------------
# 📊 Display FINAL Plan, Mood Tracker, and Actions (Step 3/3)
# ----------------------------------------------------------
# Exit backfill mode when viewing today's plan
if not st.session_state.df.empty and st.session_state.get('backfill_mode') and DATE_KEY == datetime.now().strftime("%Y-%m-%d"):
     st.session_state.backfill_mode = False
     st.session_state.backfill_date = None
     st.rerun()

df = st.session_state.df

if not df.empty and st.session_state.logged_in:
    st.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
    
    # Do not show Step 3/3 or mood/rescheduling if backfilling is active
    if not is_backfilling:
        st.subheader("🚀 Final Active Plan (Step 3/3)")
        
        # --- Chronological Sort (Ensure display is always sorted on load) ---
        def sort_key(slot):
            """Helper function to extract datetime object for sorting."""
            if pd.isna(slot) or 'N/A' in str(slot):
                return datetime.max
            try:
                start_str = str(slot).split(' - ')[0].strip()
                return datetime.strptime(start_str, '%I:%M %p')
            except Exception:
                return datetime.max
                
        df = df.sort_values(
            by="Time Slot", 
            key=lambda x: x.apply(sort_key), 
            ignore_index=True
        )
        st.session_state.df = df # Update session state with the sorted DF
        st.session_state.context.df = st.session_state.df # Ensure context agent is also updated with the sort
        # ---------------------------------------------------
        
        col_mood, col_table = st.columns([1, 4])

        with col_mood:
            st.markdown("##### 🧘 Mood Adjuster")
            mood = st.selectbox(
                "Current Focus/Mood", 
                ["Select Mood", "Low 😴", "Great 😊", "Neutral 😌"],
                label_visibility="collapsed"
            )
            
            # Adaptive sorting logic based on mood
            if mood != "Select Mood":
                if mood != st.session_state.last_processed_mood:
                    
                    df_copy = st.session_state.df.copy()
                    
                    if mood == "Low 😴":
                        # Re-sort to put low priority/breaks first
                        df_copy['Priority_Sort'] = df_copy['Priority'].map({'High': 3, 'Medium': 2, 'Low': 1})
                        df_copy['Is_Break'] = df_copy['Task'].str.lower().str.contains('break|relax')
                        
                        df_easy = df_copy[df_copy['Is_Break'] | (df_copy['Priority_Sort'] == 1)]
                        df_hard = df_copy[~(df_copy['Is_Break'] | (df_copy['Priority_Sort'] == 1))]
                        
                        df_new = pd.concat([df_easy, df_hard]).drop(columns=['Priority_Sort', 'Is_Break'], errors='ignore').reset_index(drop=True)
                        st.session_state.df = df_new
                        st.session_state.mood_log.append({"time": datetime.now().strftime("%I:%M %p"), "mood": mood, "action": "Prioritized easy tasks."})
                        st.toast("Low focus detected: Moved breaks/low priority tasks up.")
                        
                    elif mood == "Great 😊":
                        # Re-sort to put high priority first
                        df_high = df_copy[df_copy['Priority'].str.lower() == 'high']
                        df_other = df_copy[~(df_copy['Priority'].str.lower() == 'high')]
                        df_new = pd.concat([df_high, df_other]).reset_index(drop=True)
                        st.session_state.df = df_new
                        st.session_state.mood_log.append({"time": datetime.now().strftime("%I:%M %p"), "mood": mood, "action": "Prioritized high-priority tasks."})
                        st.toast("Great focus detected: Moved high priority tasks up.")
                        
                    elif mood == "Neutral 😌":
                        st.session_state.mood_log.append({"time": datetime.now().strftime("%I:%M %p"), "mood": mood, "action": "Schedule unchanged."})
                        st.toast("Schedule unchanged.")
                    
                    st.session_state.last_processed_mood = mood
                    st.rerun()

            
            # Display Mood Log
            if st.session_state.mood_log:
                st.markdown("###### Mood Log")
                log_df = pd.DataFrame(st.session_state.mood_log).tail(5)
                st.dataframe(log_df, use_container_width=True, hide_index=True)


        with col_table:
            st.markdown("##### Task Timeline")
            # The data editor modifies st.session_state.df when interaction stops
            edited_df = st.data_editor(
                df,
                column_order=("Time Slot", "Completed", "Priority", "Time", "Task"),
                column_config={
                    "Completed": st.column_config.CheckboxColumn("Done", default=False),
                    "Task": st.column_config.TextColumn("Task Description"),
                    "Priority": st.column_config.SelectboxColumn("Priority", options=["High", "Medium", "Low"], required=True, disabled=True),
                    "Time": st.column_config.TextColumn("Duration", disabled=True),
                    "Time Slot": st.column_config.TextColumn("Time Slot", disabled=True)
                },
                disabled=("Priority", "Time", "Time Slot", "Task"), # Only Completed is editable
                use_container_width=True,
                key="task_data_editor"
            )
            st.session_state.df = edited_df # Ensure st.session_state.df is updated
            st.session_state.context.df = edited_df # Update ContextAgent's DF


        # ----------------------------------------------------------
        # 🔁 Task Action (Skip/Reschedule)
        # ----------------------------------------------------------
        st.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
        st.subheader("Task Rescheduling")
        
        col_idx, col_action_ai, col_action_manual = st.columns([1, 2, 2])
        
        max_idx = len(df) - 1 if not df.empty else 0
        task_idx = col_idx.number_input(
            "Task Index (0-based) to Action",
            min_value=0,
            max_value=max_idx,
            step=1,
            value=0,
            key="action_task_index"
        )
        
        # AI Reschedule Button
        with col_action_ai:
            if st.button("🔄 AI Reschedule (Smart Slot)", use_container_width=True):
                with st.spinner("🧠 AI is finding a better slot..."):
                    # Use the latest DF from context
                    df_current = st.session_state.context.df 
                    current_task_name = df_current.at[task_idx, "Task"]
                    
                    result = scheduler.suggest_reschedule( 
                        task_name=current_task_name,
                        pattern_summary=scheduler.analyze_user_pattern(),
                        user_start=start_time_str,
                        user_end=end_time_str,
                        existing_slots=df_current["Time Slot"].tolist()
                    )
                    
                    if "time_slot" in result:
                        st.session_state.df.at[task_idx, "Time Slot"] = result["time_slot"]
                        st.session_state.df.at[task_idx, "Completed"] = False 
                        
                        # Update context and re-sort after AI reschedule
                        st.session_state.context.df = st.session_state.df 
                        # Manually re-sort the dataframe based on the helper function
                        st.session_state.df = st.session_state.df.sort_values(
                            by="Time Slot", 
                            key=lambda x: x.apply(sort_key), 
                            ignore_index=True
                        )
                        st.session_state.context.df = st.session_state.df # Update context again after sort

                        st.toast(f"✅ AI Rescheduled: {result['reason']}")
                    else:
                        st.error("AI failed. Try Manual Shift.")
                
                st.rerun() 

        # Manual Shift Button (Calls context_agent.reschedule_task which includes sort)
        with col_action_manual:
            if st.button("➡️ Manual Shift (30% Later)", use_container_width=True):
                # context.reschedule_task method updates st.session_state.context.df internally
                # and performs the chronological sort.
                result = context.reschedule_task(task_idx) 
                
                st.session_state.df = st.session_state.context.df
                
                st.toast(result) 
                st.rerun() 


        # ----------------------------------------------------------
        # 📊 Visualization & Reflection (Updated to Professional Look)
        # ----------------------------------------------------------
        st.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
        progress = context.progress()
        st.subheader(f"📈 Daily Review: {progress:.1f}% Complete")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Overall Progress")
            st.pyplot(plot_completion_bar(progress)) 
        with col2:
            st.markdown("##### Status Distribution")
            df_current = st.session_state.context.df 
            task_data = [
                {"task": t, "status": "completed" if c else "pending"}
                for t, c in zip(df_current["Task"], df_current["Completed"])
            ]
            st.pyplot(plot_status_pie(task_data))


        st.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
        
        # Save, Export, and Reflection Actions
        col_save, col_reflect, col_export = st.columns([1, 1, 1])

        with col_save:
            if st.button("💾 Save Today’s Progress", use_container_width=True):
                st.session_state.history_agent.save_date(username, DATE_KEY, st.session_state.context.df)
                st.success("Progress saved!")

        with col_reflect:
            if st.button("🧠 Generate Daily Reflection", use_container_width=True):
                df_current = st.session_state.context.df 
                tasks_summary = [
                    {"task": t, "status": "completed" if c else "skipped"}
                    for t, c in zip(df_current["Task"], df_current["Completed"])
                ]
                reflection = reflector.generate_summary(tasks_summary)
                
                st.markdown("### 📘 Daily Reflection Summary")
                st.info(f"**Summary:** {reflection['summary_text']}")
        
        with col_export:
            ics_content = generate_ics_file(st.session_state.context.df, DISPLAY_DATE)
            
            st.download_button(
                label="📅 Export to Calendar",
                data=ics_content,
                file_name=f"LifeLoop_Plan_{DATE_KEY}.ics",
                mime="text/calendar",
                use_container_width=True,
                help="Download a file to import into Google Calendar, Outlook, or Apple Calendar."
            )

        # --- NEW: Weekly Insights & Patterns Section ---

        def calculate_weekly_metrics(history_data):
            """Calculates key metrics from the last 7 days of history."""
            if not history_data:
                return None, None
            
            total_tasks = 0
            completed_tasks = 0
            daily_progress = {} # Date -> Progress %
            
            all_tasks_df = []

            for date in sorted(history_data.keys()):
                data = history_data[date]
                completed = data.get("Completed", [])
                tasks = data.get("Task", [])
                priority = data.get("Priority", ["Medium"] * len(tasks)) # Default to Medium if missing

                tasks_completed = sum(completed)
                tasks_total = len(tasks)
                
                total_tasks += tasks_total
                completed_tasks += tasks_completed
                
                progress = (tasks_completed / tasks_total) * 100 if tasks_total > 0 else 0
                daily_progress[date] = progress
                
                # Compile all tasks into a single DF for priority breakdown
                temp_df = pd.DataFrame({
                    "Date": [date] * tasks_total,
                    "Priority": priority,
                    "Completed": completed
                })
                all_tasks_df.append(temp_df)

            avg_progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            
            metrics = {
                "Total Tasks": total_tasks,
                "Completed Tasks": completed_tasks,
                "Average Progress": avg_progress
            }
            
            if all_tasks_df:
                priority_df = pd.concat(all_tasks_df).groupby('Priority').agg(
                    Total=('Completed', 'size'),
                    Completed=('Completed', 'sum')
                ).reset_index()
            else:
                priority_df = pd.DataFrame(columns=['Priority', 'Total', 'Completed'])


            return metrics, daily_progress, priority_df

        def plot_daily_progress(daily_progress):
            """Generates a bar chart for daily progress."""
            dates = sorted(daily_progress.keys())
            progress = [daily_progress[date] for date in dates]
            
            # Use only day and month for cleaner x-axis labels
            labels = [datetime.strptime(d, "%Y-%m-%d").strftime("%m/%d") for d in dates]

            fig, ax = plt.subplots(figsize=(6, 3))
            # Set dark theme background and colors for Matplotlib
            fig.patch.set_facecolor('#0d1117')
            ax.set_facecolor('#161b22')
            ax.spines['bottom'].set_color('#c9d1d9')
            ax.spines['top'].set_color('#161b22')
            ax.spines['right'].set_color('#161b22')
            ax.spines['left'].set_color('#c9d1d9')
            ax.tick_params(axis='x', colors='#c9d1d9')
            ax.tick_params(axis='y', colors='#c9d1d9')
            ax.yaxis.label.set_color('#c9d1d9')
            ax.title.set_color('#58a6ff')


            ax.bar(labels, progress, color="#58a6ff")
            ax.set_ylabel("Progress (%)")
            ax.set_title("Task Completion Last 7 Days")
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            return fig

        def plot_priority_breakdown(priority_df):
            """Generates a stacked bar chart for task completion by priority."""
            fig, ax = plt.subplots(figsize=(6, 3))
            
            # Set dark theme background and colors for Matplotlib
            fig.patch.set_facecolor('#0d1117')
            ax.set_facecolor('#161b22')
            ax.spines['bottom'].set_color('#c9d1d9')
            ax.spines['top'].set_color('#161b22')
            ax.spines['right'].set_color('#161b22')
            ax.spines['left'].set_color('#c9d1d9')
            ax.tick_params(axis='x', colors='#c9d1d9')
            ax.tick_params(axis='y', colors='#c9d1d9')
            ax.yaxis.label.set_color('#c9d1d9')
            ax.title.set_color('#58a6ff')

            if priority_df.empty:
                ax.text(0.5, 0.5, "No task data to display.", horizontalalignment='center', verticalalignment='center', color='#c9d1d9', transform=ax.transAxes)
                return fig

            # Calculate Pending tasks
            priority_df['Pending'] = priority_df['Total'] - priority_df['Completed']

            # Sort to ensure consistent order
            priority_order = ['High', 'Medium', 'Low']
            priority_df['SortOrder'] = priority_df['Priority'].apply(lambda x: priority_order.index(x) if x in priority_order else 99)
            priority_df = priority_df.sort_values(by='SortOrder').drop(columns='SortOrder')

            priorities = priority_df['Priority']
            completed = priority_df['Completed']
            pending = priority_df['Pending']

            # Plot stacked bar
            ax.bar(priorities, completed, label='Completed', color='#2f81f7')
            ax.bar(priorities, pending, bottom=completed, label='Pending', color='#30363d')

            ax.set_ylabel("Number of Tasks")
            ax.set_title("Completion by Priority")
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1), facecolor='#161b22', edgecolor='#21262d', labelcolor='#c9d1d9')
            plt.tight_layout()
            return fig


        st.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
        st.subheader("🗓️ Weekly Insights & Patterns")

        # Load history for the last 7 days
        history_7_days = history_agent.load_last_n_days(username, n=7)
        
        metrics, daily_progress, priority_df = calculate_weekly_metrics(history_7_days)

        if metrics and metrics['Total Tasks'] > 0: # Check if we have actual data
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            # 1. Key Metrics
            col_m1.metric("Total Tasks (7 Days)", metrics['Total Tasks'])
            col_m2.metric("Completed Tasks", metrics['Completed Tasks'])
            col_m3.metric("Average Progress", f"{metrics['Average Progress']:.1f}%")
            
            # 2. Pattern Insights (Simple Placeholder)
            # Find the day with the max progress from daily_progress
            valid_daily_progress = {date: prog for date, prog in daily_progress.items() if prog > 0}
            
            if valid_daily_progress:
                highest_day = max(valid_daily_progress, key=valid_daily_progress.get) 
                day_name = datetime.strptime(highest_day, "%Y-%m-%d").strftime("%A")
                col_m4.metric("Most Productive Day", day_name, delta=f"{valid_daily_progress.get(highest_day, 0):.1f}%")
            else:
                col_m4.metric("Most Productive Day", "N/A", delta="0.0%")
            
            
            st.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
            
            # 3. Charts
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown("##### Daily Progress Over Time")
                st.pyplot(plot_daily_progress(daily_progress))
            with col_c2:
                st.markdown("##### Task Status by Priority")
                st.pyplot(plot_priority_breakdown(priority_df))

            st.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)

            # 4. AI Weekly Insights Button (WITH SAVE LOGIC)
            if st.button("🧠 Generate AI Weekly Summary", use_container_width=True, key="generate_weekly_summary_btn"):
                if not history_7_days:
                    st.error("Cannot generate summary: No history found for the last 7 days.")
                else:
                    with st.spinner("Analyzing 7 days of data..."):
                        # Call the generate_summary method
                        summary_result = weekly_agent.generate_summary(history_7_days)
                        
                        st.session_state.weekly_summary = summary_result['summary']
                        
                        # --- ARCHIVE SAVE LOGIC ---
                        try:
                            # 1. Prepare the entry (timestamp + summary/metrics from agent output)
                            new_entry = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "summary": summary_result['summary'],
                                "metrics": summary_result.get('metrics', {}) 
                            }
                            
                            # 2. Use the Agent's save_entry method 
                            st.session_state.weekly_agent.save_entry(username, new_entry)
                                
                            st.toast("Weekly summary generated and **archived successfully**!")
                            
                        except Exception as e:
                            st.error(f"Error saving weekly reflection to archive: {e}")
                        # --- END ARCHIVE SAVE LOGIC ---
                        
            # Display AI Weekly Insights
            if st.session_state.weekly_summary:
                st.markdown("##### 💡 AI Weekly Insights")
                st.info(st.session_state.weekly_summary)
                
        else:
            st.info("Log in and save some daily progress over the past week to view insights. (Minimum 1 day saved.)")

        # --- End NEW Section ---


else:
    # Initial state messages
    if st.session_state.logged_in and not st.session_state.draft_df.empty:
         st.info("You've generated a **Draft Plan**. Review and click **'2. Confirm & Schedule Plan'** to get your time slots.")
    elif st.session_state.logged_in:
         st.info("Enter your goal and configuration, then click the **'1. Generate Draft Tasks'** button to begin your day.")
    elif st.session_state.get('backfill_mode'):
         # If backfill mode is active but user is logged out, this should be handled by login check
         pass 
    else:
         st.error("Please log in on the sidebar to start planning.")


# ----------------------------------------------------------
# 📜 History Backfill & Review (Sidebar)
# ----------------------------------------------------------
st.sidebar.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
st.sidebar.subheader("History & Review")

if st.session_state.logged_in:
    
    # ---------------------------------------------------
    # NEW: Last 7 Days Overview & Clickable Load
    # ---------------------------------------------------
    st.sidebar.markdown("##### 🗓️ Last 7 Days Overview")
    
    # Load the history data
    history_data = history_agent.load_last_n_days(username, n=7)
    
    if history_data:
        history_list = []
        # Sort history data by date chronologically (newest first for display)
        sorted_dates = sorted(history_data.keys(), reverse=True)
        
        # Prepare data for a simple display
        for date in sorted_dates:
            data = history_data[date]
            completed_count = sum(data.get("Completed", []))
            total_count = len(data.get("Completed", []))
            progress = (completed_count / total_count) * 100 if total_count > 0 else 0
            history_list.append({"Date": date, "Progress": f"{progress:.1f}%", "Tasks": total_count})
        
        history_df = pd.DataFrame(history_list)
        
        # Display the history data frame
        st.sidebar.dataframe(history_df, use_container_width=True, hide_index=True)

        # --- Dropdown to Select the Day to Load/Edit ---
        date_options = history_df['Date'].tolist()
        
        # Pre-select the date currently in the backfill mode, or the newest one in the list
        default_index = date_options.index(st.session_state.backfill_date) if st.session_state.backfill_date in date_options else 0
        
        date_to_load = st.sidebar.selectbox(
            "Select a Date to Review/Edit:",
            options=date_options,
            index=default_index,
            key="history_date_selector",
            help="Select a date from your saved history to view or edit the tasks."
        )

        if st.sidebar.button(f"Load Tasks for {date_to_load}", use_container_width=True, key="load_selected_history_btn"):
            st.session_state.backfill_mode = True
            st.session_state.backfill_date = date_to_load
            st.rerun()

    else:
        st.sidebar.info("No saved history found for the last 7 days.")

    # --- Original Calendar Input (Kept for manually choosing older days) ---
    st.sidebar.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
    st.sidebar.markdown("##### 🗓️ Load/Edit Older History")
    
    # Calendar Input for Date Selection
    yesterday = datetime.now().date() - timedelta(days=1)
    selected_date = st.sidebar.date_input(
        "Select Date to Edit/View (older than 7 days):", 
        value=yesterday, 
        max_value=datetime.now().date() - timedelta(days=1), # Max day is yesterday
        key="backfill_date_picker"
    )
    
    selected_date_key = selected_date.strftime("%Y-%m-%d")
    
    if st.sidebar.button(f"Load/Edit Tasks for {selected_date_key}", use_container_width=True, key="load_backfill_btn"):
        st.session_state.backfill_mode = True
        st.session_state.backfill_date = selected_date_key
        st.rerun()

    # --- Backfill Logic Display ---
    if st.session_state.get('backfill_mode') and st.session_state.get('backfill_date'):
        backfill_date_key = st.session_state.backfill_date
        
        # Load existing data for that day
        history_data = history_agent._load_all_history()
        user_history = history_data.get(username, {})
        
        if backfill_date_key in user_history:
            # Data exists, load it into a DataFrame
            data_dict = user_history[backfill_date_key]
            try:
                # Ensure all lists have the same length for DataFrame construction
                lengths = {k: len(v) for k, v in data_dict.items() if isinstance(v, list)}
                max_len = max(lengths.values()) if lengths else 0
                
                # Pad lists to max length if necessary (though they should be consistent)
                padded_data = {}
                for k, v in data_dict.items():
                     if isinstance(v, list):
                        padded_data[k] = v + [None] * (max_len - len(v))
                     else:
                         padded_data[k] = [v] # Handle single values if structure is wrong
                         
                if max_len > 0:
                     backfill_df = pd.DataFrame(padded_data)
                else:
                    backfill_df = pd.DataFrame(columns=["Task", "Completed"])
                    st.warning(f"Data for {backfill_date_key} is empty.")
            
            except Exception:
                st.warning(f"Could not load data for {backfill_date_key}. File structure might be corrupt.")
                backfill_df = pd.DataFrame(columns=["Task", "Completed"])
        else:
            # No data exists, provide a template
            st.warning(f"No plan found for {backfill_date_key}. Enter tasks manually to save progress.")
            # Create a template DF with the required columns for editing
            backfill_df = pd.DataFrame([
                {"Task": "Enter task 1 (e.g., Complete Report)", "Completed": False, "Priority": "Medium", "Time": "30 min", "Time Slot": "N/A"},
                {"Task": "Enter task 2 (e.g., Exercise)", "Completed": False, "Priority": "Low", "Time": "1 hour", "Time Slot": "N/A"}
            ])
        
        st.subheader(f"✏️ Editing History: {backfill_date_key}")
        
        # Data Editor for editing past tasks/completion status
        edited_backfill_df = st.data_editor(
            backfill_df,
            column_order=("Task", "Completed"),
            column_config={
                "Completed": st.column_config.CheckboxColumn("Done", default=False),
                "Task": st.column_config.TextColumn("Task Description", required=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic", # Allow adding/deleting rows for missing days
            disabled=("Priority", "Time", "Time Slot"),
            key="backfill_data_editor"
        )
        
        if st.button(f"💾 Save Progress for {backfill_date_key}", use_container_width=True, key="save_backfill_btn"):
            # Ensure the saved DF has all required columns, even if blank/default
            if "Time" not in edited_backfill_df.columns: edited_backfill_df["Time"] = edited_backfill_df.get("Time", ["30 min"] * len(edited_backfill_df))
            if "Priority" not in edited_backfill_df.columns: edited_backfill_df["Priority"] = edited_backfill_df.get("Priority", ["Medium"] * len(edited_backfill_df))
            if "Time Slot" not in edited_backfill_df.columns: edited_backfill_df["Time Slot"] = edited_backfill_df.get("Time Slot", ["N/A"] * len(edited_backfill_df))
            
            history_agent.save_date(username, backfill_date_key, edited_backfill_df)
            st.success(f"✅ History saved for {backfill_date_key}. Weekly analysis will include this data.")
            st.session_state.backfill_mode = False # Exit backfill mode
            st.rerun() # Rerun to update the main page context

    # --- Weekly Reflections Archive Display ---
    st.sidebar.markdown('<div class="st_divider"></div>', unsafe_allow_html=True)
    if st.sidebar.button("Show Weekly Reflections Archive", use_container_width=True, key="show_weekly_btn"):
        
        try:
            # Assumes 'weekly_reflections.json' is in the root directory (alongside main.py)
            file_path = os.path.join(os.path.dirname(__file__), 'weekly_reflections.json')
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            user_reflections = data.get(username, []) # Load reflections for the active user
            
            if user_reflections:
                st.subheader("📘 Weekly Reflections Archive")
                st.info(f"Found **{len(user_reflections)}** archived reflections for user **{username}**.")
                
                # Display each reflection in an expander (newest first)
                for i, reflection in enumerate(reversed(user_reflections)):
                    timestamp = reflection.get("timestamp", "N/A")
                    summary = reflection.get("summary", "No summary found.")
                    
                    # Display metrics if available
                    metrics = reflection.get("metrics", {})
                    metrics_str = " | ".join([
                        f"{k.capitalize()}: {v.get('completed', 0)}/{v.get('total', 0)}" 
                        for k, v in metrics.items()
                    ])
                    
                    # Use overall metrics for the header if categorized metrics exist
                    overall_metrics = metrics.get('overall', {})
                    if overall_metrics:
                         metrics_str = f"Progress: {overall_metrics.get('completed', 0)}/{overall_metrics.get('total', 0)}"

                    header_text = f"Reflection from: **{timestamp.split()[0]}**"
                    if metrics_str:
                         header_text += f" ({metrics_str})"
                         
                    with st.expander(header_text):
                        st.markdown(summary) # Summary is expected to be formatted with markdown (###, etc.)
                        
                # Reset backfill mode if the archive is displayed
                st.session_state.backfill_mode = False

            else:
                st.error(f"No weekly reflection archive found for user **{username}**.")

        except FileNotFoundError:
            st.error("Weekly reflections file (`weekly_reflections.json`) not found. Ensure it exists in the root directory.")
        except json.JSONDecodeError:
            st.error("Weekly reflections file is empty or corrupted. Delete it to generate a new file.")
        except Exception as e:
            st.error(f"An error occurred while loading reflections: {e}")
        
else:
    st.sidebar.error("Please log in to use history features.")
