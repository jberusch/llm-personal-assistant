"""Daily Pages editor with word count enforcement."""

import os
import tempfile
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt

console = Console()


class DailyPagesEditor:
    """Manages the daily pages writing experience."""
    
    MIN_WORD_COUNT = 750
    SKIP_LOG_FILE = Path("data/daily_pages_skips.json")
    
    def __init__(self):
        self.SKIP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    def open_neovim(self, initial_content: str = "") -> Optional[str]:
        """Open neovim for writing daily pages.
        
        Args:
            initial_content: Existing content to prepopulate
            
        Returns:
            Content if saved and valid, None if cancelled or skipped
        """
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            if initial_content:
                f.write(initial_content)
            temp_path = f.name
        
        try:
            console.print("\n[bold cyan]📝 Opening neovim for Daily Pages[/bold cyan]")
            console.print(f"[dim]Need at least {self.MIN_WORD_COUNT} words[/dim]\n")
            
            # Open in neovim
            subprocess.run(['nvim', temp_path])
            
            # Read content
            with open(temp_path, 'r') as f:
                content = f.read().strip()
            
            # Validate word count
            word_count = self.count_words(content)
            
            if word_count >= self.MIN_WORD_COUNT:
                console.print(f"\n[green]✓ Daily pages saved ({word_count} words)[/green]\n")
                return content
            else:
                needed = self.MIN_WORD_COUNT - word_count
                console.print(f"\n[yellow]⚠ Only {word_count} words written (need {needed} more)[/yellow]\n")
                
                choice = Prompt.ask(
                    "What would you like to do?",
                    choices=["continue", "skip", "cancel"],
                    default="continue"
                )
                
                if choice == "continue":
                    return self.open_neovim(content)  # Reopen with existing content
                elif choice == "skip":
                    reason = self.prompt_skip_reason()
                    if reason:
                        self.log_skip(reason, word_count)
                        return None
                else:
                    console.print("[dim]Cancelled.[/dim]\n")
                    return None
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def open_web(self) -> Optional[str]:
        """Open web-based editor for daily pages.
        
        Opens the React app in browser and waits for completion.
        
        Returns:
            Content if saved and valid, None if cancelled or skipped
        """
        import webbrowser
        
        console.print("\n[bold cyan]📝 Opening web editor for Daily Pages[/bold cyan]")
        console.print("[dim]Make sure the web app is running: cd web && npm run dev[/dim]\n")
        
        webbrowser.open('http://localhost:5173/daily-pages')
        
        console.print("[yellow]Complete your daily pages in the browser.[/yellow]")
        console.print("[dim]This command will wait here. Press Enter when done...[/dim]\n")
        
        Prompt.ask("Press Enter when you've saved your daily pages")
        
        # Check if daily pages were saved
        from storage import storage
        journal = storage.load_journal()
        daily_pages = journal.get("daily_pages")
        
        if daily_pages:
            word_count = self.count_words(daily_pages)
            console.print(f"\n[green]✓ Daily pages found ({word_count} words)[/green]\n")
            return daily_pages
        else:
            console.print("\n[yellow]No daily pages found.[/yellow]\n")
            return None
    
    def count_words(self, text: str) -> int:
        """Count words in text.
        
        Args:
            text: Text to count
            
        Returns:
            Word count
        """
        if not text:
            return 0
        return len(text.split())
    
    def validate_word_count(self, content: str) -> bool:
        """Check if content meets minimum word count.
        
        Args:
            content: Text to validate
            
        Returns:
            True if meets minimum
        """
        return self.count_words(content) >= self.MIN_WORD_COUNT
    
    def prompt_skip_reason(self) -> Optional[str]:
        """Prompt user for reason for skipping.
        
        Returns:
            Reason if provided, None if cancelled
        """
        console.print()
        reason = Prompt.ask("Why are you skipping daily pages today?")
        
        if reason.strip():
            return reason.strip()
        return None
    
    def log_skip(self, reason: str, word_count: int = 0) -> None:
        """Log a skip event with reason.
        
        Args:
            reason: Reason for skipping
            word_count: Words written before skipping
        """
        # Load existing skips
        skips = []
        if self.SKIP_LOG_FILE.exists():
            try:
                with open(self.SKIP_LOG_FILE, 'r') as f:
                    skips = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                skips = []
        
        # Add new skip
        skip_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "word_count": word_count
        }
        skips.append(skip_entry)
        
        # Save
        with open(self.SKIP_LOG_FILE, 'w') as f:
            json.dump(skips, f, indent=2)
        
        console.print(f"\n[dim]Skip logged: {reason}[/dim]\n")
    
    def get_skip_history(self, days: int = 30) -> list:
        """Get skip history.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of skip entries
        """
        if not self.SKIP_LOG_FILE.exists():
            return []
        
        try:
            with open(self.SKIP_LOG_FILE, 'r') as f:
                skips = json.load(f)
            
            # Return most recent
            return sorted(skips, key=lambda s: s["date"], reverse=True)[:days]
        except (json.JSONDecodeError, FileNotFoundError):
            return []


# Global instance
daily_pages_editor = DailyPagesEditor()

