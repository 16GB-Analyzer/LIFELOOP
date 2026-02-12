import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()


class AIScheduler:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Missing GOOGLE_API_KEY in environment.")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.7,
            api_key=api_key
        )

    # ----------------------------------------------------------
    # Analyze user pattern
    # ----------------------------------------------------------
    def analyze_user_pattern(self):
        now_hour = datetime.now().hour
        if 6 <= now_hour < 11:
            return "Morning: high focus, analytical energy peak."
        elif 11 <= now_hour < 16:
            return "Afternoon: balanced productivity and creativity."
        elif 16 <= now_hour < 21:
            return "Evening: moderate focus, good for light or follow-up work."
        else:
            return "Night: low focus, avoid heavy cognitive tasks."

    # ----------------------------------------------------------
    # Convert "HH:MM AM - HH:MM PM" → datetime pairs
    # ----------------------------------------------------------
    def _parse_slot(self, slot_str):
        try:
            start_str, end_str = [s.strip() for s in slot_str.replace("(AI)", "").split("-")]
            start = datetime.strptime(start_str, "%I:%M %p")
            end = datetime.strptime(end_str, "%I:%M %p")
            return start, end
        except Exception:
            return None, None

    # ----------------------------------------------------------
    # Find nearest available non-overlapping slot
    # ----------------------------------------------------------
    def _find_free_slot(self, existing_slots, user_start, user_end, duration_minutes=30):
        """
        Finds the next available gap that doesn’t overlap any existing slots.
        """
        # Convert to datetime objects
        user_start_dt = datetime.strptime(user_start, "%I:%M %p")
        user_end_dt = datetime.strptime(user_end, "%I:%M %p")

        # Parse and sort existing slots
        booked = []
        for slot in existing_slots:
            s, e = self._parse_slot(slot)
            if s and e:
                booked.append((s, e))
        booked.sort(key=lambda x: x[0])

        # Start scanning for gaps
        candidate_start = user_start_dt
        while candidate_start + timedelta(minutes=duration_minutes) <= user_end_dt:
            candidate_end = candidate_start + timedelta(minutes=duration_minutes)
            overlap = False

            for s, e in booked:
                if not (candidate_end <= s or candidate_start >= e):
                    overlap = True
                    break

            if not overlap:
                return f"{candidate_start.strftime('%I:%M %p')} - {candidate_end.strftime('%I:%M %p')}"

            candidate_start = candidate_start + timedelta(minutes=15)

        # If no gap found, push to end of day (still safe)
        fallback_start = user_end_dt - timedelta(minutes=duration_minutes)
        fallback_end = user_end_dt
        return f"{fallback_start.strftime('%I:%M %p')} - {fallback_end.strftime('%I:%M %p')}"

    # ----------------------------------------------------------
    # Validate slot within user range
    # ----------------------------------------------------------
    def _validate_time_slot(self, time_slot, user_start, user_end):
        try:
            start_str, end_str = [t.strip() for t in time_slot.split("-")]
            start_dt = datetime.strptime(start_str, "%I:%M %p")
            end_dt = datetime.strptime(end_str, "%I:%M %p")
        except Exception:
            return None

        user_start_dt = datetime.strptime(user_start, "%I:%M %p")
        user_end_dt = datetime.strptime(user_end, "%I:%M %p")

        if start_dt < user_start_dt:
            start_dt = user_start_dt
            end_dt = start_dt + timedelta(minutes=30)
        if end_dt > user_end_dt:
            end_dt = user_end_dt
            start_dt = end_dt - timedelta(minutes=30)

        return f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"

    # ----------------------------------------------------------
    # Main Rescheduler (The corrected function name)
    # ----------------------------------------------------------
    def suggest_reschedule(
        self,
        task_name,
        pattern_summary,
        user_start="08:00 AM",
        user_end="09:00 PM",
        existing_slots=None
    ):
        """
        Uses Gemini to suggest reschedule time and avoids overlaps.
        """
        if existing_slots is None:
            existing_slots = []

        prompt = ChatPromptTemplate.from_template(
            """You are a smart scheduling assistant.
Given a skipped task and user focus pattern, suggest a valid new time slot 
within the user's working hours.

Task: {task_name}
Focus pattern: {pattern_summary}
Working hours: {user_start} - {user_end}

Respond only in JSON:
{{
  "time_slot": "HH:MM AM/PM - HH:MM AM/PM",
  "reason": "short justification"
}}"""
        )

        chain = prompt | self.llm | JsonOutputParser()

        try:
            result = chain.invoke({
                "task_name": task_name,
                "pattern_summary": pattern_summary,
                "user_start": user_start,
                "user_end": user_end
            })
        except Exception:
            result = {}

        if isinstance(result, dict) and "time_slot" in result:
            validated = self._validate_time_slot(result["time_slot"], user_start, user_end)
        else:
            validated = None

        if not validated:
            validated = self._find_free_slot(existing_slots, user_start, user_end)

        return {
            "time_slot": validated,
            "reason": result.get("reason", "AI-selected free non-overlapping slot.")
        }