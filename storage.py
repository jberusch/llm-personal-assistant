"""Data storage layer for the focus assistant."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from config import config


class Task(BaseModel):
    """Task model with future-proof schema for Supabase migration."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    status: str = "inbox"  # inbox, today, someday, completed
    project_hints: List[str] = Field(default_factory=list)  # For future auto-detection
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class JournalEntry(BaseModel):
    """Journal entry model with metadata for future embedding."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    date: str  # YYYY-MM-DD
    entry_type: str  # morning, evening, chat
    timestamp: datetime = Field(default_factory=datetime.now)
    question: Optional[str] = None
    response: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Storage:
    """Handles all data persistence."""
    
    def __init__(self):
        self.tasks_file = config.tasks_file
        self.journal_dir = config.journal_dir
    
    # Task operations
    
    def load_tasks(self) -> List[Task]:
        """Load all tasks from storage."""
        if not self.tasks_file.exists():
            return []
        
        with open(self.tasks_file, 'r') as f:
            data = json.load(f)
            return [Task(**task) for task in data]
    
    def save_tasks(self, tasks: List[Task]):
        """Save all tasks to storage."""
        with open(self.tasks_file, 'w') as f:
            json.dump(
                [task.model_dump(mode='json') for task in tasks],
                f,
                indent=2,
                default=str
            )
    
    def add_task(self, task: Task) -> Task:
        """Add a new task."""
        tasks = self.load_tasks()
        tasks.append(task)
        self.save_tasks(tasks)
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        tasks = self.load_tasks()
        for task in tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task(self, task: Task):
        """Update an existing task."""
        tasks = self.load_tasks()
        task.updated_at = datetime.now()
        for i, t in enumerate(tasks):
            if t.id == task.id:
                tasks[i] = task
                break
        self.save_tasks(tasks)
    
    def complete_task(self, task_id: str):
        """Mark a task as completed."""
        task = self.get_task(task_id)
        if task:
            task.completed = True
            task.completed_at = datetime.now()
            task.status = "completed"
            self.update_task(task)
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get all tasks with a specific status."""
        tasks = self.load_tasks()
        return [t for t in tasks if t.status == status]
    
    def get_tasks_for_date(self, date: datetime) -> List[Task]:
        """Get all tasks due on a specific date."""
        tasks = self.load_tasks()
        return [
            t for t in tasks 
            if t.due_date and t.due_date.date() == date.date()
        ]
    
    def get_incomplete_tasks(self) -> List[Task]:
        """Get all incomplete tasks."""
        tasks = self.load_tasks()
        return [t for t in tasks if not t.completed]
    
    # Journal operations
    
    def get_journal_file(self, date: Optional[datetime] = None) -> Path:
        """Get the journal file path for a specific date."""
        if date is None:
            date = datetime.now()
        filename = date.strftime("%Y-%m-%d.json")
        return self.journal_dir / filename
    
    def load_journal(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Load journal entries for a specific date."""
        journal_file = self.get_journal_file(date)
        if not journal_file.exists():
            return {
                "date": (date or datetime.now()).strftime("%Y-%m-%d"),
                "morning": None,
                "evening": None,
                "chat_history": []
            }
        
        with open(journal_file, 'r') as f:
            return json.load(f)
    
    def save_journal(self, data: Dict[str, Any], date: Optional[datetime] = None):
        """Save journal data for a specific date."""
        journal_file = self.get_journal_file(date)
        with open(journal_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_journal_entry(self, entry: JournalEntry, date: Optional[datetime] = None):
        """Add an entry to today's journal."""
        journal = self.load_journal(date)
        
        if entry.entry_type == "morning":
            journal["morning"] = entry.model_dump(mode='json')
        elif entry.entry_type == "evening":
            journal["evening"] = entry.model_dump(mode='json')
        elif entry.entry_type == "chat":
            journal["chat_history"].append(entry.model_dump(mode='json'))
        
        self.save_journal(journal, date)
    
    def get_morning_entry(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Get the morning entry for a specific date."""
        journal = self.load_journal(date)
        return journal.get("morning")
    
    def get_chat_history(self, date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get chat history for a specific date."""
        journal = self.load_journal(date)
        return journal.get("chat_history", [])


# Global storage instance
storage = Storage()

