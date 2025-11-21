"""Interactive chat interface with task integration."""

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from assistant import Assistant
from tasks import task_manager
from storage import storage

console = Console()


class ChatInterface:
    """Manages interactive chat sessions with the assistant."""
    
    def __init__(self):
        self.assistant = None
        self.running = False
    
    def start(self):
        """Start an interactive chat session."""
        console.print("\n[bold cyan]💬 Chat Session Started[/bold cyan]")
        console.print("[dim]Type 'tasks' to view your task board, 'quit' or 'exit' to end the session.[/dim]\n")
        
        # Initialize assistant
        try:
            self.assistant = Assistant()
            self.assistant.load_history_from_today()
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            return
        
        # Show context
        morning_entry = storage.get_morning_entry()
        if morning_entry:
            console.print("[dim]I remember your morning reflection and current tasks.[/dim]\n")
        
        self.running = True
        
        # Main chat loop
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("[bold green]You[/bold green]")
                
                if not user_input.strip():
                    continue
                
                # Check for commands
                if user_input.lower() in ['quit', 'exit', '/quit', 'done']:
                    self._exit_chat()
                    break
                
                if user_input.lower() in ['tasks', '/tasks']:
                    self._show_tasks()
                    continue
                
                if user_input.lower() in ['help', '/help']:
                    self._show_help()
                    continue
                
                # Check for task creation intent
                task_intent = self.assistant.parse_task_intent(user_input)
                if task_intent:
                    self._handle_task_creation(task_intent, user_input)
                    continue
                
                # Send to Claude
                console.print()
                with console.status("[cyan]Thinking...[/cyan]"):
                    response = self.assistant.send_message(user_input)
                
                # Display response
                console.print("[bold blue]Assistant[/bold blue]")
                console.print(Markdown(response))
                console.print()
                
            except KeyboardInterrupt:
                console.print("\n")
                self._exit_chat()
                break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]\n")
    
    def _handle_task_creation(self, task_intent: dict, original_text: str):
        """Handle automatic task creation from conversation."""
        task_text = task_intent.get("task", "")
        due_text = task_intent.get("due")
        
        console.print()
        console.print(f"[yellow]📝 I detected a task: \"{task_text}\"[/yellow]")
        
        if due_text:
            console.print(f"[yellow]   Due: {due_text}[/yellow]")
        
        # Ask for confirmation
        confirm = Prompt.ask("Add this task?", choices=["y", "n"], default="y")
        
        if confirm == "y":
            # Add the task
            task = task_manager.add_task(task_text)
            console.print(f"[green]✓ Task added: {task.text}[/green]")
            if task.due_date:
                console.print(f"[green]  Due: {task.due_date.strftime('%A, %B %d, %Y')}[/green]")
            
            # Refresh assistant context
            self.assistant.refresh_context()
        else:
            console.print("[dim]Task not added. Continuing conversation...[/dim]")
        
        console.print()
    
    def _show_tasks(self):
        """Display the task board."""
        console.print()
        
        # Create task board
        table = Table(title="📋 Task Board", show_header=True, header_style="bold cyan")
        table.add_column("Status", style="dim", width=12)
        table.add_column("Task", style="white")
        table.add_column("Due", style="yellow", width=15)
        
        # Today's tasks
        today_tasks = task_manager.get_today_tasks()
        if today_tasks:
            for task in today_tasks:
                due_str = "Today" if task.due_date else ""
                table.add_row("📌 Today", task.text, due_str)
        
        # Upcoming tasks
        upcoming_tasks = task_manager.get_upcoming_tasks()
        if upcoming_tasks:
            for task in upcoming_tasks[:5]:  # Show first 5
                due_str = task.due_date.strftime("%b %d") if task.due_date else ""
                table.add_row("📅 Upcoming", task.text, due_str)
        
        # Inbox tasks
        inbox_tasks = task_manager.get_inbox_tasks()
        if inbox_tasks:
            for task in inbox_tasks[:3]:  # Show first 3
                table.add_row("📥 Inbox", task.text, "")
        
        if not (today_tasks or upcoming_tasks or inbox_tasks):
            console.print("[dim]No tasks yet. You can add one by saying something like:[/dim]")
            console.print("[dim]  'Remind me tomorrow to call mom'[/dim]")
        else:
            console.print(table)
        
        console.print()
    
    def _show_help(self):
        """Show help information."""
        console.print()
        help_text = """
**Chat Commands:**
- `tasks` - View your task board
- `quit` or `exit` - End the chat session
- `help` - Show this help message

**Tips:**
- Just chat naturally - I'll help you think through priorities
- Say things like "remind me tomorrow to..." to create tasks
- Ask "what should I focus on?" for suggestions based on your morning goals
- I remember your morning reflection and current context
"""
        console.print(Panel(Markdown(help_text), title="Help", border_style="cyan"))
        console.print()
    
    def _exit_chat(self):
        """Exit the chat session."""
        console.print("\n[cyan]Chat session ended. Your conversation has been saved.[/cyan]")
        console.print("[dim]Use 'focus chat' to continue later.[/dim]\n")
        self.running = False


# Global chat instance
chat = ChatInterface()

