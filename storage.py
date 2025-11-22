"""Data storage layer for the focus assistant."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from config import config


class Project(BaseModel):
    """Project model for organizing tasks and notes."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    color: str = "#3b82f6"  # Default blue color
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


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
    project_id: Optional[str] = None  # Link to project
    
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
        self.projects_file = config.config_dir / "projects.json"
    
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
        
        # Auto-generate embedding
        try:
            from embeddings import get_embeddings_manager
            embeddings_mgr = get_embeddings_manager()
            if embeddings_mgr:
                embeddings_mgr.embed_task(task)
        except Exception:
            pass  # Embeddings are optional
        
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
        
        # Re-generate embedding
        try:
            from embeddings import get_embeddings_manager
            embeddings_mgr = get_embeddings_manager()
            if embeddings_mgr:
                embeddings_mgr.embed_task(task)
        except Exception:
            pass  # Embeddings are optional
    
    def complete_task(self, task_id: str):
        """Mark a task as completed."""
        task = self.get_task(task_id)
        if task:
            task.completed = True
            task.completed_at = datetime.now()
            task.status = "completed"
            self.update_task(task)
            
            # Update embedding to reflect completion
            try:
                from embeddings import get_embeddings_manager
                embeddings_mgr = get_embeddings_manager()
                if embeddings_mgr:
                    embeddings_mgr.embed_task(task)
            except Exception:
                pass  # Embeddings are optional
    
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
        """Get the journal file path for a specific date (markdown format)."""
        if date is None:
            date = datetime.now()
        filename = date.strftime("%Y-%m-%d.md")
        return self.journal_dir / filename
    
    def _parse_markdown_journal(self, content: str) -> Dict[str, Any]:
        """Parse markdown journal into structured data."""
        # Extract YAML frontmatter
        frontmatter = {}
        main_content = content
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                main_content = parts[2].strip()
                
                # Simple YAML parsing (key: value)
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        frontmatter[key] = value
        
        # Parse sections
        journal_data = {
            "date": frontmatter.get("date", ""),
            "morning": None,
            "evening": None,
            "chat_history": [],
            "notes": []
        }
        
        # Extract morning reflection
        morning_match = re.search(r'## Morning Reflection\n\n(.*?)(?=\n## |\Z)', main_content, re.DOTALL)
        if morning_match:
            morning_text = morning_match.group(1).strip()
            responses = {}
            
            # Parse Q&A pairs
            qa_pattern = r'\*\*(.*?)\*\*\s*\n(.*?)(?=\n\n\*\*|\Z)'
            for match in re.finditer(qa_pattern, morning_text, re.DOTALL):
                question = match.group(1).strip()
                answer = match.group(2).strip()
                responses[question] = answer
            
            journal_data["morning"] = {
                "metadata": {
                    "responses": responses,
                    "energy_level": frontmatter.get("energy", "")
                }
            }
        
        # Extract chat history
        chat_match = re.search(r'## Chat History\n\n(.*?)(?=\n## |\Z)', main_content, re.DOTALL)
        if chat_match:
            chat_text = chat_match.group(1).strip()
            
            # Parse individual chat messages
            message_pattern = r'### ([\d:]+\s*[AP]M)\n\*\*(You|Assistant):\*\* (.*?)(?=\n### |\Z)'
            for match in re.finditer(message_pattern, chat_text, re.DOTALL):
                timestamp = match.group(1).strip()
                role = "user" if match.group(2) == "You" else "assistant"
                message = match.group(3).strip()
                
                journal_data["chat_history"].append({
                    "response": message,
                    "metadata": {"role": role, "timestamp": timestamp}
                })
        
        # Extract evening reflection
        evening_match = re.search(r'## Evening Reflection\n\n(.*?)(?=\n## |\Z)', main_content, re.DOTALL)
        if evening_match:
            evening_text = evening_match.group(1).strip()
            responses = {}
            
            # Parse Q&A pairs
            qa_pattern = r'\*\*(.*?)\*\*\s*\n(.*?)(?=\n\n\*\*|\Z)'
            for match in re.finditer(qa_pattern, evening_text, re.DOTALL):
                question = match.group(1).strip()
                answer = match.group(2).strip()
                responses[question] = answer
            
            journal_data["evening"] = {
                "metadata": {"responses": responses}
            }
        
        # Extract notes
        notes_match = re.search(r'## Notes\n\n(.*?)(?=\n\n---|\Z)', main_content, re.DOTALL)
        if notes_match:
            notes_text = notes_match.group(1).strip()
            
            # Parse individual notes (format: ### HH:MM AM/PM `#ProjectName`\nContent...)
            # Content goes until the next ### heading or end of notes section
            note_pattern = r'### ([\d:]+\s*[AP]M)\s*(?:`#([^`]+)`)?\n(.*?)(?=\n###|\Z)'
            for match in re.finditer(note_pattern, notes_text, re.DOTALL):
                timestamp = match.group(1).strip()
                project_name = match.group(2)  # Captured project name from `#ProjectName`
                content = match.group(3).strip()
                
                # Find project by name if present
                project_id = None
                if project_name:
                    projects = self.load_projects()
                    project = next((p for p in projects if p.name == project_name), None)
                    if project:
                        project_id = project.id
                
                journal_data["notes"].append({
                    "timestamp": timestamp,
                    "content": content,
                    "project_id": project_id
                })
        
        return journal_data
    
    def _load_json_journal(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Load journal from legacy JSON format."""
        if date is None:
            date = datetime.now()
        json_file = self.journal_dir / date.strftime("%Y-%m-%d.json")
        
        if json_file.exists():
            with open(json_file, 'r') as f:
                return json.load(f)
        return None
    
    def load_journal(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Load journal entries for a specific date (supports both markdown and JSON)."""
        if date is None:
            date = datetime.now()
        
        # Try markdown first
        md_file = self.get_journal_file(date)
        if md_file.exists():
            with open(md_file, 'r') as f:
                content = f.read()
            return self._parse_markdown_journal(content)
        
        # Fall back to JSON
        json_data = self._load_json_journal(date)
        if json_data:
            return json_data
        
        # Return empty structure
        return {
            "date": date.strftime("%Y-%m-%d"),
            "morning": None,
            "evening": None,
            "chat_history": []
        }
    
    def _format_markdown_journal(self, data: Dict[str, Any], date: datetime) -> str:
        """Format journal data as markdown."""
        date_str = date.strftime("%Y-%m-%d")
        day_name = date.strftime("%A")
        full_date = date.strftime("%A, %B %d, %Y")
        
        # Build YAML frontmatter
        frontmatter = f"""---
date: {date_str}
day: {day_name}
"""
        
        # Add morning metadata to frontmatter
        if data.get("morning") and data["morning"].get("metadata"):
            morning_meta = data["morning"]["metadata"]
            if "responses" in morning_meta:
                responses = morning_meta["responses"]
                energy = responses.get("How did you sleep? What's your energy level (1-10)?", "")
                if energy:
                    frontmatter += f"energy: {energy}\n"
        
        frontmatter += "tags: [daily, journal]\n---\n\n"
        
        # Build content
        content = f"# {full_date}\n\n"
        
        # Morning Reflection
        if data.get("morning") and data["morning"].get("metadata", {}).get("responses"):
            content += "## Morning Reflection\n\n"
            responses = data["morning"]["metadata"]["responses"]
            
            for question, answer in responses.items():
                content += f"**{question}**\n{answer}\n\n"
            
            content += "---\n\n"
        
        # Chat History
        if data.get("chat_history"):
            content += "## Chat History\n\n"
            
            for entry in data["chat_history"]:
                role = entry.get("metadata", {}).get("role", "user")
                message = entry.get("response", "")
                timestamp_str = entry.get("metadata", {}).get("timestamp", "")
                
                if not timestamp_str:
                    # Generate timestamp from entry if available
                    if "timestamp" in entry:
                        try:
                            ts = datetime.fromisoformat(entry["timestamp"])
                            timestamp_str = ts.strftime("%I:%M %p")
                        except:
                            timestamp_str = datetime.now().strftime("%I:%M %p")
                    else:
                        timestamp_str = datetime.now().strftime("%I:%M %p")
                
                role_label = "You" if role == "user" else "Assistant"
                content += f"### {timestamp_str}\n**{role_label}:** {message}\n\n"
            
            content += "---\n\n"
        
        # Notes
        if data.get("notes"):
            content += "## Notes\n\n"
            
            for note in data["notes"]:
                timestamp = note.get("timestamp", "")
                note_content = note.get("content", "")
                project_id = note.get("project_id")
                
                # Add project tag if assigned
                if project_id:
                    # Get project name for display
                    projects = self.load_projects()
                    project_name = next((p.name for p in projects if p.id == project_id), None)
                    if project_name:
                        content += f"### {timestamp} `#{project_name}`\n{note_content}\n\n"
                    else:
                        content += f"### {timestamp}\n{note_content}\n\n"
                else:
                    content += f"### {timestamp}\n{note_content}\n\n"
            
            content += "---\n\n"
        
        # Evening Reflection
        if data.get("evening") and data["evening"].get("metadata", {}).get("responses"):
            content += "## Evening Reflection\n\n"
            responses = data["evening"]["metadata"]["responses"]
            
            for question, answer in responses.items():
                content += f"**{question}**\n{answer}\n\n"
        
        return frontmatter + content
    
    def save_journal(self, data: Dict[str, Any], date: Optional[datetime] = None):
        """Save journal data for a specific date (as markdown)."""
        if date is None:
            date = datetime.now()
        
        journal_file = self.get_journal_file(date)
        markdown_content = self._format_markdown_journal(data, date)
        
        with open(journal_file, 'w') as f:
            f.write(markdown_content)
        
        # Auto-generate embeddings for new content
        self._auto_embed_journal(data, date)
    
    def add_journal_entry(self, entry: JournalEntry, date: Optional[datetime] = None):
        """Add an entry to today's journal."""
        journal = self.load_journal(date)
        
        if entry.entry_type == "morning":
            journal["morning"] = entry.model_dump(mode='json')
        elif entry.entry_type == "evening":
            journal["evening"] = entry.model_dump(mode='json')
        elif entry.entry_type == "chat":
            # Add timestamp to metadata
            if "timestamp" not in entry.metadata:
                entry.metadata["timestamp"] = entry.timestamp.strftime("%I:%M %p")
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
    
    def _auto_embed_journal(self, data: Dict[str, Any], date: datetime):
        """Auto-generate embeddings for journal content."""
        try:
            from embeddings import get_embeddings_manager
            embeddings_mgr = get_embeddings_manager()
            if not embeddings_mgr:
                return
            
            date_str = date.strftime("%Y-%m-%d")
            
            # Embed morning reflection
            if data.get("morning"):
                morning_meta = data["morning"].get("metadata", {})
                responses = morning_meta.get("responses", {})
                if responses:
                    morning_text = "\n\n".join([
                        f"{q}\n{a}" for q, a in responses.items()
                    ])
                    embeddings_mgr.embed_journal_entry(
                        date_str, "morning", morning_text, "morning"
                    )
            
            # Embed evening reflection
            if data.get("evening"):
                evening_meta = data["evening"].get("metadata", {})
                responses = evening_meta.get("responses", {})
                if responses:
                    evening_text = "\n\n".join([
                        f"{q}\n{a}" for q, a in responses.items()
                    ])
                    embeddings_mgr.embed_journal_entry(
                        date_str, "evening", evening_text, "evening"
                    )
            
            # Embed chat history (only user messages)
            chat_history = data.get("chat_history", [])
            for idx, entry in enumerate(chat_history):
                role = entry.get("metadata", {}).get("role", "user")
                message = entry.get("response", "")
                if message and role == "user":
                    embeddings_mgr.embed_journal_entry(
                        date_str, f"chat_{idx}", message, "chat"
                    )
            
            # Embed notes
            notes = data.get("notes", [])
            for idx, note in enumerate(notes):
                content = note.get("content", "")
                title = note.get("title", "")
                if content:
                    # Combine title and content for better searchability
                    note_text = f"{title}\n{content}" if title else content
                    embeddings_mgr.embed_journal_entry(
                        date_str, f"note_{idx}", note_text, "note"
                    )
        
        except Exception:
            pass  # Embeddings are optional
    
    def add_note_to_journal(self, content: str, project_id: Optional[str] = None, date: Optional[datetime] = None):
        """Add a note to today's journal."""
        journal = self.load_journal(date)
        
        # Initialize notes list if it doesn't exist
        if "notes" not in journal:
            journal["notes"] = []
        
        # Create note entry with timestamp
        now = datetime.now()
        note_entry = {
            "timestamp": now.strftime("%I:%M %p"),
            "content": content,
            "project_id": project_id
        }
        
        journal["notes"].append(note_entry)
        self.save_journal(journal, date)
        return note_entry
    
    # Project operations
    
    def load_projects(self) -> List[Project]:
        """Load all projects from storage."""
        if not self.projects_file.exists():
            return []
        
        with open(self.projects_file, 'r') as f:
            data = json.load(f)
            return [Project(**project) for project in data]
    
    def save_projects(self, projects: List[Project]):
        """Save all projects to storage."""
        with open(self.projects_file, 'w') as f:
            json.dump(
                [project.model_dump(mode='json') for project in projects],
                f,
                indent=2,
                default=str
            )
    
    def add_project(self, project: Project) -> Project:
        """Add a new project."""
        projects = self.load_projects()
        projects.append(project)
        self.save_projects(projects)
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        projects = self.load_projects()
        for project in projects:
            if project.id == project_id:
                return project
        return None
    
    def update_project(self, project: Project):
        """Update an existing project."""
        projects = self.load_projects()
        project.updated_at = datetime.now()
        for i, p in enumerate(projects):
            if p.id == project.id:
                projects[i] = project
                break
        self.save_projects(projects)
    
    def delete_project(self, project_id: str):
        """Delete a project by ID."""
        projects = self.load_projects()
        projects = [p for p in projects if p.id != project_id]
        self.save_projects(projects)


# Global storage instance
storage = Storage()

