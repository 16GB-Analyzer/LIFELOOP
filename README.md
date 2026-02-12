# ♾️ LIFELOOP | SmartTodo – Your AI-Powered Day Planner

> “Don’t just plan your day — let AI design it intelligently.”

---

## Overview(Iteration-1 Summary)

**LIFELOOP** is an AI-driven productivity companion that learns *how you work* — not just *what you plan*.  
It creates smart, adaptive daily schedules using intelligent agents that plan, schedule, reschedule, visualize, and reflect on your day automatically.

It’s not just a task list — it’s your **AI productivity ecosystem**.

---

## Features

| Category | Description |
|-----------|--------------|
| **Planner Agent** | Generates goal-based task breakdowns using Gemini AI |
| **AI Scheduler** | Allocates smart time slots and reschedules tasks dynamically |
| **Progress Visualizer** | Tracks completion % and displays insights with interactive charts |
| **Reflection Agent** | Summarizes daily productivity and patterns for personal growth |
| **Context Memory** | Learns your behavior and adapts future plans automatically |

---
## Features by User Story (Iteration 1)

### **User Story 1: Enter Goal and Generate AI Plan**
- User enters a high-level daily goal.
- Planner Agent breaks it into **4–6 actionable subtasks**.
- Each task includes time and priority fields.
- Plan is displayed in an editable table.

### **User Story 2: Interactive Task Table**
- The task table appears with full edit capabilities:
  - Edit task description
  - Edit priority
  - Edit estimated duration
- Clicking **Confirm Plan** saves the edited plan to state.
- Uses `st.data_editor` for clean in-place editing.

### **User Story 3: Mark Task Complete**
- Each task includes a **Done** button/checkbox.
- When the task is marked complete:
  - Task status updates immediately
  - Progress bar updates
  - Completion % recalculated

### **User Story 4: Auto-Reschedule Skipped Tasks**
- When user selects **Skip**, the Context Agent:
  - Reschedules the task to a later time slot
  - Uses heuristics (<30% time shift)
  - Displays a justification message explaining the change

### **User Story 5: Daily Reflection Summary**
- At the end of the day, the user clicks **Reflect**.
- Reflection Agent generates:
  - Completion %
  - Skipped task summary
  - Total focus time
  - Text summary of productivity patterns
- Bar/pie chart visualizations are shown in Streamlit.

### **User Story 6: Visualize Progress**
- Visual charts show:
  - Completed vs pending tasks
  - Distribution by category or priority
- Charts support tooltips on hover.
- Implemented using **Matplotlib / Plotly**.

### **User Story 8: Select Interaction Mode**
- Before generating the plan, user chooses:
  - **AI Mode** → AI generates & locks the plan
  - **Together Mode** → AI generates editable plan
  - **Manual Mode** → User starts with an empty list
- Selected mode is stored in LangGraph state.
- UI changes dynamically based on mode.

---
## Iteration 1: Working Prototype

### Goal
Deliver a functioning AI day planner that interprets a goal, generates tasks, allows edits, tracks progress, and provides an end-of-day reflection.

### Completed in Iteration 1
- Goal input connected to Planner Agent
- Editable interactive task table using `st.data_editor`
- Progress tracking with completion percentage
- Skip logic with automatic rescheduling via Context Agent
- Reflection Agent generating daily summaries & visualizations
- Mode selection: **AI / Together / Manual**
- Local JSON-based storage (`user_data.json`, `history.json`, `daily_reflections.json`)

### **Deferred or unfinished items after Iteration 1**
- No mood-based personalization.
- No weekly summaries or long-term insights.
- No post-generation edit tools beyond the task table.
- No advanced metrics for productivity analysis.
- No cross-day learning or historical analysis.

### **Technical and coordination notes**
- Work focused on stabilizing agents (Planner, Context, Reflection) and UI integration.
- Initial app used direct function calls without multi-agent orchestration.
- JSON schema and consistent storage structure required coordination.
- Team members contributed across Planner Agent, Context Agent, Reflection Agent, and Streamlit UI.

---
## Iteration 2 Overview

- Added mood‑aware adaptive planning and weekly summaries on top of the Iteration‑1 planner.
- Improved interaction design with clearer modes (AI / Together / Manual), editing after generation, and more visible plan changes.
- Extended reasoning to reorganize tasks based on mood and save reflections across days for trend analysis.
- Prepared for HAI evaluation by making AI decisions easier to inspect and override.

---
## Features by User Story (Iteration 2)
### **User Story 9: Manually Add a Task**
- Users in **Manual** or **Together** mode can add custom tasks that the AI did not generate.
- An **Add Task** button inserts a new blank row into the task table, allowing the user to enter:
  - Task name  
  - Duration  
  - Priority  
- Once saved, the new task is added to the plan and included in progress tracking.
- Supports both fully manual planning and collaborative planning with AI.

### **User Story 10: Dropdown for Mode & Priority**
- Users can choose **AI**, **Together**, or **Manual** mode from a dropdown.
- Each task includes a *priority dropdown* (High / Medium / Low).
- Selections update the plan state and influence how tasks are handled by the system.

### **User Story 11: Mood-Aware Adaptive Planning**
- Before generating the plan, the user selects their mood or focus level (Energized,Neutral, Tired, High Focus).
- The system adapts the plan by reordering or adjusting task difficulty:
  - High focus → harder tasks earlier  
  - Low energy/tired → lighter and shorter tasks first  
- Planner and Context Agents reorganize the schedule based on this mood input.

### **User Story 12: Daily & Weekly Summaries**
- The system generates daily metrics including completion %, skipped tasks, and estimated focus time.
- Weekly reflections show broader patterns such as productivity trends, best/worst days, and category distribution.
- Clear charts (bar, line, pie) help users understand daily and weekly performance.
- Weekly insights are saved in weekly_reflections.json.

### **User Story 13: Connecting to External Applications**
- After generating the schedule, the user is given the option to export the schedule to an external calendar application.
- An .ics file is generated and downloaded to the local machine with all of the schedule's information.
- The .ics file is able to be imported to an external calender applciations. 

### **User Story 14: Edit Plan After Generation**
- Users can adjust the generated plan at any time:
  - Add or remove tasks  
  - Edit names, durations, and priorities  
- Edits update the internal state instantly and enhance collaboration in Together Mode.

---
## Iteration 2: Adaptive Planning, Mood Integration & Weekly Intelligence

### Goal
Enhance LifeLoop with adaptive intelligence by integrating mood-based planning, multi-day summaries, richer visual metrics, and the ability to edit plans after they are generated.

### Completed in Iteration 2
- Added **mood/focus pop-up** allowing users to select: Energized, Neutral, Tired, or High Focus.
- Planner + Context Agents **adapt and reorder tasks** based on selected mood.
- Introduced **daily and weekly summaries** with clearer metrics and trends.
- Added visual charts (bar, pie, line) for daily and weekly task insights.
- Implemented **Edit Plan** feature allowing users to modify tasks after generation:
  - Add / remove tasks  
  - Edit name, priority, duration  
- Weekly reflection agent logs insights to `weekly_reflections.json`.
- Expanded visualization engine to support weekly trends and comparisons.
- Added the ability to export the generated schedule to external calendar applications.

### **Deferred or unfinished items after Iteration 2**
- No long-term habit modeling or predictive energy-level estimation.
- No personalized productivity time-window recommendations.
- No automatic multi-day carryover logic.
- No deep AI suggestions for improving weak areas (planned for Iteration 3).
- No integration with external calendars or notification systems.

### **Technical and coordination notes**
- Mood state integrated into existing Planner and Context logic without breaking Iteration 1 workflows.
- Weekly analytics required schema updates and consistent handling across agents.
- Editing after generation required additional UI state management in Streamlit.
- Coordinating multiple agents (Planner, Context, Reflection, Weekly Reflection) increased complexity.
- Team collaborated on consistent visualization style and data flow across days and weeks.

---
## Tech Stack

| Area | Tools / Libraries |
|------|--------------------|
| Frontend | **Streamlit** |
| AI & LLM | **LangChain**, **Google Gemini 2.5**, **LangGraph** |
| Visualization | **Matplotlib**, **Pandas** |
| Memory & State | **Session State**, **JSON context logs** |
| Environment | **Python-dotenv** |

---
## Trust, Transparency, and Control

- Users choose how much AI help they want (AI / Together / Manual).
- All task changes (add, edit, skip, reschedule) are shown directly in the UI.
- Mood selection clearly explains how the plan is adjusted.
- Users can override any AI-generated task at any time.
- Daily and weekly summaries keep the system’s behavior visible and predictable.

---

## Explanation and Confidence

- The system explains why tasks were reordered, rescheduled, or modified.
- Mood-based reasoning is shown (e.g., lighter tasks prioritized when tired).
- Daily and weekly metrics show how conclusions were formed.
- Visual charts make productivity trends clear and confidence easy to interpret.

---

## Explainability

- Short text summaries describe what happened and why.
- Task actions (complete, skip, reschedule) include simple explanations.
- Visualizations (bar/pie/line charts) make patterns easy to understand.
- Editable plans reinforce that AI suggestions are flexible, not forced.

---
## Trust, Predictability, and Autonomy Boundaries

- **Trust:** Users see all task changes (add, edit, skip, reschedule) directly in the table, with mood‑based behavior explained in text so they understand why the plan changed.
- **Predictability:** Fixed modes (AI / Together / Manual), consistent rescheduling rules, and daily/weekly summaries make system behavior repeatable and easier to anticipate.
- **Autonomy Boundaries:** AI can suggest and reorder tasks, but users always confirm plans, can edit any task, and can choose Manual mode for full human control.

---
## Think‑Aloud User Study (Iteration 2)

We conducted a small think‑aloud evaluation with two participants:

- **Neha(Student):** Planned a day around writing a report and doing household chores.
- **Priyanka(Software Engineer):** Planned work tasks and exercise while using the mood and weekly summary features.

Both participants were asked to talk aloud while using LifeLoop to:

- Enter a goal and generate a plan.
- Edit tasks, mark completion or skip tasks.
- Explore reflection and weekly summary views.

### Positive Quotes (What Worked Well)

- Neha: “Oh wow, it actually broke it down nicely… yeah that’s basically my life.”
- Neha: “I’ll mark one as done just to see what happens… Ahh the progress bar moves. That’s satisfying — like checking something off on paper.”
- Priyanka: “Ooooh okay, the plan changed. The hard stuff moved down. That’s actually… really thoughtful? Like it knows me.”
- Priyanka: “Weekly view… ooh charts! It says Tuesday is my best day… I like seeing the trend; makes me kinda want to beat my own stats.”

These comments suggest that users liked:

- The quality of the AI task breakdown.
- The feeling of progress from marking tasks complete.
- Mood‑aware reordering that matches their expectations.
- Weekly trends that create a “gamified” sense of improvement.

### Negative Quotes (Pain Points and Confusions)

- Neha: “Umm… I’ll put ‘Finish my report and do some chores’. Alright. Oh, there’s this mode thing… AI, Together, Manual… hmm…”  
- Neha: “Now lemme try reflection… Hmm, okay, it says something like ‘You completed 25%’… Yeah, I like seeing that” (but she had to explore to find it).  
- Priyanka: “Overall, pretty smooth. Sometimes I forget where things are, but I figured it out.”

From these quotes we observed:

- Mode choices (AI / Together / Manual) are not fully self‑explanatory at first glance.
- Reflection is useful once discovered, but not very “discoverable”.
- Navigation between daily view, mood selection, and weekly summary can be a bit hard to remember.

---
## Planned Improvements from Feedback

Based on Neha and Priyanka’s feedback, we identified several improvements:

- **Clarify interaction modes:** Add one‑line descriptions under AI / Together / Manual so users immediately know how much control the AI will take.
- **Make reflection more discoverable:** Add a small end‑of‑day banner or button (“View today’s reflection”) once the user completes or skips a few tasks.
- **Improve navigation cues:** Add persistent tabs or breadcrumbs for “Today”, “Mood & Plan”, and “Weekly Summary” so users can more easily remember where features live.
- **Onboarding hints:** Show a brief one‑time tooltip the first time a user opens the app, pointing to key elements: goal input, mode selector, mood selector, and reflection button.

---
## Test Cases (Iteration 2)

| ID  | Related User Story | Scenario | Steps | Expected Result | Actual Result |
|-----|--------------------|----------|-------|-----------------|---------------|
| T1  | US9 – Manually Add a Task | Add a custom task in Together mode | 1. Open app  2. Select **Together** mode  3. Generate a plan from any goal  4. Click **Add Task**  5. Enter task name, duration, and priority  6. Confirm/save | New task row appears in the table with the entered values, is included in completion tracking, and appears in daily reflection. | Pass |
| T2  | US10 – Mode & Priority Dropdown | Switch modes and change task priority | 1. Select **AI** mode and generate a plan  2. Switch to **Manual** or **Together** mode  3. For a task, change priority via the dropdown (e.g., Medium → High) | Mode selection updates behavior (e.g., in Manual no new AI tasks are added). Priority change is reflected in the table and influences later scheduling/reflection. | Pass |
| T3  | US11 – Mood‑Aware Adaptive Planning | Plan adapts to different mood levels | 1. Select mood **Energized**  2. Enter a goal with both heavy and light tasks  3. Generate plan and note ordering  4. Change mood to **Tired**  5. Regenerate plan | Under **Energized**, heavier/longer tasks appear earlier; under **Tired**, lighter/shorter tasks are scheduled earlier and heavy tasks later, with explanation text mentioning mood. | Pass |
| T4  | US12 – Daily & Weekly Summaries | Daily metrics and weekly trends update | 1. Complete some tasks, skip others  2. Click **Reflect** at end of day  3. Open weekly summary view | Daily reflection shows completion %, skipped tasks, and text summary; weekly view aggregates multiple days with bar/line/pie charts; new data is written to `weekly_reflections.json`. | Pass |
| T5  | US13 – Export to External Calendar | Export schedule as `.ics` file | 1. Generate a schedule for the day  2. Click **Export to Calendar** (or equivalent button)  3. Download `.ics` file  4. Import it into a calendar app (e.g., Google Calendar, Outlook) | `.ics` file downloads successfully and contains all tasks as events with correct time slots; events appear correctly when imported into an external calendar. | Pass |
| T6  | US14 – Edit Plan After Generation | Edit tasks in an existing plan | 1. Generate a plan in **Together** mode  2. Edit a task name, duration, and priority directly in the table  3. Delete one task  4. Add a new task  5. Confirm/save plan | All edits are reflected immediately in the table; deleted task is removed from tracking; new task is tracked; reflection and weekly summaries use the updated plan. | Pass |

---

## Setup Instructions

### Clone the Repository
bash
git clone https://github.com/vcu-cmsc-damevski/project-smarttodo.git
cd project-smarttodo/whole_code

### Create environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

### Install dependencies
pip install -r requirements.txt

### Run the app
streamlit run main.py


Example Output
Input	Generated Plan
“Finish my research draft and gym after lunch”	AI generates tasks like Write literature review (1h), Format references (30m), Gym workout (1h) with smart time slots and adaptive rescheduling.

Visual dashboards show your daily progress, completion rate, and smart reflection text summarizing your productivity patterns.

**Future Vision**
Integration with Google Calendar & Notion

Natural language chat interface

Long-term habit analysis using reinforcement learning

Cloud deployment (Azure / Render)


Show Some Love
If you found LIFELOOP inspiring —
 Star this repo to support and follow its evolution!

Productivity is not about doing more — it’s about doing what matters intelligently.


---
## Architecture Overview

LIFELOOP consists of multiple intelligent modules working together:

```plaintext
LifeLoop/
project-smarttodo/
│
├── whole_code/
│   ├── main.py                     → Main Streamlit UI
│   ├── agents/
│   │   ├── planner_agent.py        → Goal → subtasks
│   │   ├── ai_scheduler.py         → Time slot management
│   │   ├── context_agent.py        → Completion & skip logic
│   │   ├── history_agent.py        → Logs user interactions
│   │   ├── reflection_agent.py     → Daily reflection generator
│   │   ├── weekly_reflection_agent.py → Week-level summary
│   │   ├── visualization.py        → Generates charts
│   │  
│   ├── daily_reflections.json
│   ├── history.json
│   ├── user_data.json
│   └── weekly_reflections.json
│
└── demo/                           → Demo video


yaml
Copy code

Each “agent” communicates with the main Streamlit app — enabling a seamless interactive workflow between planning, doing, and reflecting.

