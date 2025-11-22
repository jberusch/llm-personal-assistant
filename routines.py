"""Morning and evening routine flows."""

from datetime import datetime
from typing import Dict
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.markdown import Markdown

from storage import storage, JournalEntry
from assistant import Assistant
from tasks import task_manager

console = Console()

# Try to import Google integrations (may not be configured)
try:
    from google_integration import google_integration
    GOOGLE_AVAILABLE = google_integration is not None
except ImportError:
    GOOGLE_AVAILABLE = False
    google_integration = None


class MorningRoutine:
    """New structured morning flow with sleep, daily pages, and intention setting."""
    
    def run(self):
        """Run the complete morning flow."""
        console.print("\n[bold cyan]🌅 Good Morning Flow[/bold cyan]\n")
        
        # Check if already completed today
        if self.is_completed():
            console.print("[yellow]You've already completed your morning flow today.[/yellow]")
            response = Prompt.ask("Would you like to do it again?", choices=["y", "n"], default="n")
            if response == "n":
                self._show_current_intention()
                return
            console.print()
        
        # Phase 1: Sleep Tracking
        console.print("[bold]Phase 1/3: Sleep Tracking[/bold]\n")
        from trackers import sleep_tracker
        sleep_data = sleep_tracker.prompt_entries()
        sleep_tracker.save_data(sleep_data)
        console.print("[green]✓ Sleep data logged[/green]\n")
        
        # Phase 2: Daily Pages
        console.print("[bold]Phase 2/3: Daily Pages[/bold]")
        console.print("[dim]Write 750 words to clear your mind and start fresh[/dim]\n")
        
        editor_choice = Prompt.ask(
            "Which editor would you like to use?",
            choices=["neovim", "web"],
            default="neovim"
        )
        
        from daily_pages import daily_pages_editor
        
        if editor_choice == "neovim":
            daily_pages_content = daily_pages_editor.open_neovim()
        else:
            daily_pages_content = daily_pages_editor.open_web()
        
        if daily_pages_content:
            # Save to journal
            journal = storage.load_journal()
            journal["daily_pages"] = daily_pages_content
            storage.save_journal(journal)
            console.print("[green]✓ Daily pages saved to journal[/green]\n")
        else:
            console.print("[yellow]Continuing without daily pages...[/yellow]\n")
        
        # Phase 3: Intention Setting
        console.print("[bold]Phase 3/3: Set Your Intention[/bold]\n")
        
        intention_data = {}
        
        console.print("[bold]What is your intention for today?[/bold]")
        intention_data["intention"] = Prompt.ask("  ")
        console.print()
        
        console.print("[bold]What are your key priorities today?[/bold]")
        console.print("[dim](comma-separated)[/dim]")
        intention_data["priorities"] = Prompt.ask("  ")
        console.print()
        
        console.print("[bold]What's one thing that would bring you joy today?[/bold]")
        intention_data["joy"] = Prompt.ask("  ")
        console.print()
        
        # Save intention to journal
        journal = storage.load_journal()
        journal["intention"] = intention_data
        journal["morning_flow_completed"] = True
        storage.save_journal(journal)
        
        console.print("[bold green]✓ Morning flow complete![/bold green]\n")
        
        # Show summary
        self._show_summary(intention_data)
    
    def is_completed(self) -> bool:
        """Check if morning flow is completed for today (PST)."""
        try:
            journal = storage.load_journal()
            return journal.get("morning_flow_completed", False)
        except:
            return False
    
    def _show_current_intention(self):
        """Show today's intention if set."""
        try:
            journal = storage.load_journal()
            intention = journal.get("intention")
            
            if intention:
                console.print("\n[bold]Today's Intention:[/bold]\n")
                if "intention" in intention:
                    console.print(f"[cyan]Intention:[/cyan] {intention['intention']}")
                if "priorities" in intention:
                    console.print(f"[cyan]Priorities:[/cyan] {intention['priorities']}")
                if "joy" in intention:
                    console.print(f"[cyan]Bring Joy:[/cyan] {intention['joy']}")
                console.print()
        except:
            pass
    
    def _show_summary(self, intention_data: Dict[str, str]):
        """Show summary of morning flow."""
        from rich.panel import Panel
        from rich.markdown import Markdown
        
        summary = f"""## Your Day

        **Intention:** {intention_data.get('intention', '')}

        **Priorities:** {intention_data.get('priorities', '')}

        **Bring Joy:** {intention_data.get('joy', '')}
        """
        
        console.print(Panel(
            Markdown(summary),
            title="[bold cyan]Ready to Start Your Day[/bold cyan]",
            border_style="cyan"
        ))
        console.print()


class LegacyMorningRoutine:
    """Original morning check-in routine (kept for reference)."""
    
    QUESTIONS = [
        "How did you sleep? What's your energy level (1-10)?",
        "How are you feeling going into today?",
        "What's THE one thing that would make today a success?",
        "What are you avoiding that needs attention?",
        "What would bring joy or meaning to your day?"
    ]
    
    def run(self):
        """Run the legacy morning routine."""
        console.print("\n[bold cyan]🌅 Good morning! Let's plan your day.[/bold cyan]\n")
        
        # Check if morning routine already done today
        morning_entry = storage.get_morning_entry()
        if morning_entry:
            console.print("[yellow]You've already completed your morning routine today.[/yellow]")
            response = Prompt.ask("Would you like to do it again?", choices=["y", "n"], default="n")
            if response == "n":
                self._show_existing_plan(morning_entry)
                return
            console.print()
        
        # Ask morning questions
        responses = {}
        for i, question in enumerate(self.QUESTIONS, 1):
            console.print(f"[bold]{i}. {question}[/bold]")
            answer = Prompt.ask("  ")
            responses[question] = answer
            console.print()
        
        # Save morning entry
        entry_data = {
            "questions": self.QUESTIONS,
            "responses": responses,
            "timestamp": datetime.now().isoformat()
        }
        
        entry = JournalEntry(
            date=datetime.now().strftime("%Y-%m-%d"),
            entry_type="morning",
            response="",  # Full responses stored in metadata
            metadata=entry_data
        )
        storage.add_journal_entry(entry)
        
        console.print("[bold green]✓ Morning reflection saved![/bold green]\n")
        
        # Show existing tasks
        self._show_tasks()
        
        # Ask Claude to help synthesize the day
        console.print("[bold cyan]Let me help you plan your day...[/bold cyan]\n")
        self._generate_day_plan(responses)
    
    def _show_existing_plan(self, morning_entry: Dict):
        """Show the existing morning plan."""
        console.print("\n[bold]Today's Morning Reflection:[/bold]\n")
        
        responses = morning_entry.get("metadata", {}).get("responses", {})
        for question, answer in responses.items():
            console.print(f"[cyan]{question}[/cyan]")
            console.print(f"  {answer}\n")
    
    def _show_tasks(self):
        """Display current tasks and calendar events."""
        # Show calendar events if available
        if GOOGLE_AVAILABLE and google_integration.is_configured() and google_integration.has_token():
            try:
                today_events = google_integration.get_events_today()
                if today_events:
                    console.print("[bold magenta]📅 Today's Calendar:[/bold magenta]")
                    formatted = google_integration.format_events_for_display(today_events)
                    console.print(formatted)
                    console.print()
            except Exception:
                # Silently skip if calendar unavailable
                pass
        
        today_tasks = task_manager.get_today_tasks()
        upcoming_tasks = task_manager.get_upcoming_tasks()
        inbox_tasks = task_manager.get_inbox_tasks()
        
        if today_tasks:
            console.print("[bold yellow]📋 Today's Tasks:[/bold yellow]")
            for task in today_tasks:
                console.print(f"  • {task.text}")
            console.print()
        
        if upcoming_tasks:
            console.print("[bold blue]📅 Upcoming Tasks:[/bold blue]")
            for task in upcoming_tasks[:5]:  # Show first 5
                due_str = task.due_date.strftime("%a, %b %d") if task.due_date else ""
                console.print(f"  • {task.text} ({due_str})")
            console.print()
        
        if inbox_tasks:
            console.print(f"[dim]📥 {len(inbox_tasks)} tasks in inbox[/dim]\n")
    
    def _generate_day_plan(self, responses: Dict[str, str]):
        """Use Claude to generate a day plan based on responses."""
        try:
            assistant = Assistant()
            
            # Build a prompt for Claude
            prompt = f"""Based on my morning reflection, help me create a focused plan for today.

My responses:
"""
            for question, answer in responses.items():
                prompt += f"\n{question}\n→ {answer}\n"
            
            # Add task context
            today_tasks = task_manager.get_today_tasks()
            if today_tasks:
                prompt += "\n\nToday's scheduled tasks:\n"
                for task in today_tasks:
                    prompt += f"- {task.text}\n"
            
            prompt += """

            Please help me:
            1. Identify the top 2-3 priorities for today
            2. Suggest how to structure my day
            3. Offer any insights about what I'm avoiding or what might bring meaning

            Keep it concise and actionable."""
            
            response = assistant.ask_question(prompt)
            
            # Display the plan
            console.print(Panel(
                Markdown(response),
                title="[bold cyan]Your Day Plan[/bold cyan]",
                border_style="cyan"
            ))
            console.print()
            
        except Exception as e:
            console.print(f"[red]Couldn't generate plan: {e}[/red]")
            console.print("[yellow]Continuing without AI planning.[/yellow]\n")


class EveningRoutine:
    """Manages the evening reflection routine."""
    
    QUESTIONS = [
        "What did you accomplish today?",
        "What got in your way or distracted you?",
        "How do you feel about the day overall?",
        "What's one thing you want to focus on tomorrow?"
    ]
    
    def run(self):
        """Run the evening routine."""
        console.print("\n[bold magenta]🌙 Evening Reflection[/bold magenta]\n")
        
        # Check if evening routine already done today
        journal = storage.load_journal()
        if journal.get("evening"):
            console.print("[yellow]You've already completed your evening reflection today.[/yellow]")
            response = Prompt.ask("Would you like to do it again?", choices=["y", "n"], default="n")
            if response == "n":
                return
            console.print()
        
        # Show task completion stats
        self._show_task_stats()
        
        # Ask evening questions
        responses = {}
        for i, question in enumerate(self.QUESTIONS, 1):
            console.print(f"[bold]{i}. {question}[/bold]")
            answer = Prompt.ask("  ")
            responses[question] = answer
            console.print()
        
        # Save evening entry
        entry_data = {
            "questions": self.QUESTIONS,
            "responses": responses,
            "timestamp": datetime.now().isoformat(),
            "task_stats": task_manager.get_task_stats()
        }
        
        entry = JournalEntry(
            date=datetime.now().strftime("%Y-%m-%d"),
            entry_type="evening",
            response="",
            metadata=entry_data
        )
        storage.add_journal_entry(entry)
        
        console.print("[bold green]✓ Evening reflection saved![/bold green]")
        console.print("[dim]Sleep well! See you tomorrow morning.[/dim]\n")
    
    def _show_task_stats(self):
        """Show task completion statistics."""
        stats = task_manager.get_task_stats()
        
        console.print("[bold]Today's Progress:[/bold]")
        console.print(f"  ✓ Completed: {stats['completed_today']} tasks")
        console.print(f"  • Remaining: {stats['today']} tasks for today")
        console.print(f"  • Total incomplete: {stats['incomplete']} tasks\n")


# Global instances
morning_routine = MorningRoutine()
legacy_morning_routine = LegacyMorningRoutine()
evening_routine = EveningRoutine()

