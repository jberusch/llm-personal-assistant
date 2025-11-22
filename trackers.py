"""Generic tracker system for habits and metrics."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table

console = Console()


class Tracker(ABC):
    """Base class for tracking habits and metrics."""
    
    def __init__(self, name: str, data_dir: Path = None):
        """Initialize tracker.
        
        Args:
            name: Name of the tracker (e.g., 'sleep', 'reading')
            data_dir: Directory to store tracker data
        """
        self.name = name
        self.data_dir = data_dir or Path("data/trackers")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.data_dir / f"{name}.json"
    
    @abstractmethod
    def prompt_entries(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Prompt user for tracker entries.
        
        Returns:
            Dictionary of responses
        """
        pass
    
    def save_data(self, data: Dict[str, Any], date: Optional[datetime] = None) -> None:
        """Save tracker data for a specific date.
        
        Args:
            data: Data to save
            date: Date for the entry (defaults to today)
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        
        # Load existing data
        entries = self._load_all()
        
        # Add or update entry for this date
        entry = {
            "date": date_str,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Remove any existing entry for this date
        entries = [e for e in entries if e["date"] != date_str]
        entries.append(entry)
        
        # Sort by date
        entries.sort(key=lambda e: e["date"], reverse=True)
        
        # Save
        with open(self.file_path, 'w') as f:
            json.dump(entries, f, indent=2)
    
    def get_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get tracker history for the last N days.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of entries
        """
        entries = self._load_all()
        return entries[:days]
    
    def get_entry(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Get entry for a specific date.
        
        Args:
            date: Date to retrieve (defaults to today)
            
        Returns:
            Entry data or None if not found
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        entries = self._load_all()
        
        for entry in entries:
            if entry["date"] == date_str:
                return entry["data"]
        
        return None
    
    def _load_all(self) -> List[Dict[str, Any]]:
        """Load all entries from file."""
        if not self.file_path.exists():
            return []
        
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def display_history(self, days: int = 7) -> None:
        """Display tracker history in a table."""
        entries = self.get_history(days)
        
        if not entries:
            console.print(f"[yellow]No {self.name} data recorded yet.[/yellow]\n")
            return
        
        self._render_table(entries)
    
    @abstractmethod
    def _render_table(self, entries: List[Dict[str, Any]]) -> None:
        """Render entries as a table."""
        pass


class SleepTracker(Tracker):
    """Track sleep quality and patterns."""
    
    def __init__(self, data_dir: Path = None):
        super().__init__("sleep", data_dir)
    
    def prompt_entries(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Prompt user for sleep data.
        
        Returns:
            Dictionary with sleep data
        """
        console.print("\n[bold cyan]😴 Sleep Tracking[/bold cyan]\n")
        
        # Rested level
        while True:
            rested = IntPrompt.ask("How rested do you feel this morning? (1-10)")
            if 1 <= rested <= 10:
                break
            console.print("[red]Please enter a number between 1 and 10[/red]")
        
        # Bedtime
        bedtime = Prompt.ask("Around when did you go to bed?", default="10:00pm")
        
        # Wake time
        wake_time = Prompt.ask("Around when did you wake up?", default="7:00am")
        
        # Notes
        notes = Prompt.ask("Any other notes on your sleep?", default="")
        
        console.print()
        
        return {
            "rested_level": rested,
            "bedtime": bedtime,
            "wake_time": wake_time,
            "notes": notes if notes else None
        }
    
    def _render_table(self, entries: List[Dict[str, Any]]) -> None:
        """Render sleep entries as a table."""
        table = Table(title=f"[bold]Sleep History (Last {len(entries)} days)[/bold]")
        
        table.add_column("Date", style="cyan")
        table.add_column("Rested", style="green")
        table.add_column("Bedtime", style="yellow")
        table.add_column("Wake Time", style="yellow")
        table.add_column("Notes", style="dim")
        
        for entry in entries:
            data = entry["data"]
            date_obj = datetime.strptime(entry["date"], "%Y-%m-%d")
            date_display = date_obj.strftime("%a, %b %d")
            
            rested = f"{data.get('rested_level', '?')}/10"
            bedtime = data.get('bedtime', '-')
            wake_time = data.get('wake_time', '-')
            notes = data.get('notes', '') or ''
            
            # Truncate notes if too long
            if len(notes) > 30:
                notes = notes[:27] + "..."
            
            table.add_row(date_display, rested, bedtime, wake_time, notes)
        
        console.print(table)
        console.print()


# Global instances
sleep_tracker = SleepTracker()

