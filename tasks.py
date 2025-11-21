"""Task management with natural language date parsing."""

from datetime import datetime, timedelta
from typing import Optional, List
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import re

from storage import storage, Task


class TaskManager:
    """Handles task creation, parsing, and management."""
    
    def __init__(self):
        self.storage = storage
    
    def parse_natural_language_task(self, text: str) -> tuple[str, Optional[datetime]]:
        """
        Parse a natural language task string and extract task text and due date.
        
        Examples:
        - "remind me tomorrow to pay rent" -> ("pay rent", tomorrow's date)
        - "call mom next week" -> ("call mom", next Monday)
        - "buy groceries" -> ("buy groceries", None)
        """
        # Common date patterns
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        due_date = None
        task_text = text
        
        # Pattern: "remind me [when] to [task]"
        remind_match = re.search(r'remind me (.*?) to (.+)', text, re.IGNORECASE)
        if remind_match:
            when_text = remind_match.group(1).strip()
            task_text = remind_match.group(2).strip()
            due_date = self._parse_when(when_text, today)
            return task_text, due_date
        
        # Pattern: "[task] [when]" or "[when] [task]"
        # Try to extract date phrases
        date_patterns = [
            (r'\btomorrow\b', lambda: today + timedelta(days=1)),
            (r'\btoday\b', lambda: today),
            (r'\bnext week\b', lambda: today + timedelta(days=7)),
            (r'\bnext month\b', lambda: today + relativedelta(months=1)),
            (r'\bin (\d+) days?\b', lambda m: today + timedelta(days=int(m.group(1)))),
            (r'\bin (\d+) weeks?\b', lambda m: today + timedelta(weeks=int(m.group(1)))),
            (r'\bnext (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', 
             lambda m: self._next_weekday(today, m.group(1))),
            (r'\bon (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
             lambda m: self._next_weekday(today, m.group(1))),
        ]
        
        for pattern, date_func in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if callable(date_func):
                        # Check if date_func expects a match object
                        import inspect
                        sig = inspect.signature(date_func)
                        if len(sig.parameters) > 0:
                            due_date = date_func(match)
                        else:
                            due_date = date_func()
                except Exception:
                    pass
                
                # Remove the date phrase from task text
                task_text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                task_text = re.sub(r'\s+', ' ', task_text)  # Clean up extra spaces
                break
        
        # Clean up common prefixes
        task_text = re.sub(r'^(remind me to|remember to|need to|have to)\s+', '', task_text, flags=re.IGNORECASE)
        task_text = task_text.strip()
        
        return task_text, due_date
    
    def _parse_when(self, when_text: str, base_date: datetime) -> Optional[datetime]:
        """Parse a 'when' phrase into a datetime."""
        when_lower = when_text.lower().strip()
        
        if when_lower == "tomorrow":
            return base_date + timedelta(days=1)
        elif when_lower == "today":
            return base_date
        elif when_lower == "next week":
            return base_date + timedelta(days=7)
        elif when_lower == "next month":
            return base_date + relativedelta(months=1)
        elif "day" in when_lower:
            match = re.search(r'(\d+)', when_lower)
            if match:
                days = int(match.group(1))
                return base_date + timedelta(days=days)
        elif "week" in when_lower:
            match = re.search(r'(\d+)', when_lower)
            if match:
                weeks = int(match.group(1))
                return base_date + timedelta(weeks=weeks)
        
        # Try parsing as weekday
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in weekdays:
            if day in when_lower:
                return self._next_weekday(base_date, day)
        
        return None
    
    def _next_weekday(self, base_date: datetime, weekday: str) -> datetime:
        """Get the next occurrence of a weekday."""
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        target_day = weekdays.get(weekday.lower())
        if target_day is None:
            return base_date
        
        days_ahead = target_day - base_date.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        return base_date + timedelta(days=days_ahead)
    
    def add_task(self, text: str, due_date: Optional[datetime] = None, status: str = "inbox") -> Task:
        """Add a new task."""
        # Parse natural language if no explicit due date provided
        if due_date is None:
            task_text, parsed_date = self.parse_natural_language_task(text)
            text = task_text
            due_date = parsed_date
        
        # Determine status based on due date
        if due_date:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if due_date.date() == today.date():
                status = "today"
            elif due_date > today:
                status = "someday"
        
        task = Task(
            text=text,
            due_date=due_date,
            status=status
        )
        
        return self.storage.add_task(task)
    
    def get_today_tasks(self) -> List[Task]:
        """Get all tasks for today."""
        today = datetime.now()
        tasks = self.storage.get_incomplete_tasks()
        
        return [
            t for t in tasks
            if t.status == "today" or 
            (t.due_date and t.due_date.date() == today.date())
        ]
    
    def get_upcoming_tasks(self) -> List[Task]:
        """Get upcoming tasks (future but not today)."""
        today = datetime.now()
        tasks = self.storage.get_incomplete_tasks()
        
        return [
            t for t in tasks
            if t.due_date and t.due_date.date() > today.date()
        ]
    
    def get_inbox_tasks(self) -> List[Task]:
        """Get tasks without a due date."""
        tasks = self.storage.get_incomplete_tasks()
        return [t for t in tasks if t.due_date is None]
    
    def complete_task(self, task_id: str):
        """Mark a task as complete."""
        self.storage.complete_task(task_id)
    
    def get_task_stats(self) -> dict:
        """Get statistics about tasks."""
        all_tasks = self.storage.load_tasks()
        completed_today = [
            t for t in all_tasks
            if t.completed and t.completed_at and
            t.completed_at.date() == datetime.now().date()
        ]
        
        return {
            "total": len(all_tasks),
            "completed_today": len(completed_today),
            "incomplete": len([t for t in all_tasks if not t.completed]),
            "today": len(self.get_today_tasks()),
            "upcoming": len(self.get_upcoming_tasks()),
            "inbox": len(self.get_inbox_tasks())
        }


# Global task manager instance
task_manager = TaskManager()

