"""Interactive REPL-style interface for Focus Assistant."""

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from datetime import datetime

from assistant import Assistant
from tasks import task_manager
from routines import morning_routine, evening_routine
from storage import storage
from config import config

console = Console()


class InteractiveSession:
    """Main interactive REPL-style session for Focus Assistant."""
    
    def __init__(self):
        self.assistant = None
        self.running = False
        self.commands = {
            '/morning': self.cmd_morning,
            '/evening': self.cmd_evening,
            '/tasks': self.cmd_tasks,
            '/today': self.cmd_today,
            '/add': self.cmd_add,
            '/done': self.cmd_done,
            '/note': self.cmd_quick_note,
            '/write': self.cmd_write_note,
            '/log': self.cmd_log,
            '/search': self.cmd_search,
            '/projects': self.cmd_projects,
            '/stats': self.cmd_stats,
            '/config': self.cmd_config,
            '/help': self.cmd_help,
            '/quit': self.cmd_quit,
            '/exit': self.cmd_quit,
        }
    
    def start(self):
        """Start the interactive session."""
        # Welcome message
        console.print("\n[bold cyan]✨ Focus Assistant[/bold cyan]")
        console.print("[dim]Your personal productivity coach[/dim]\n")
        
        # Check for API key
        if not config.get_api_key():
            console.print("[yellow]⚠ No API key found.[/yellow]")
            console.print("[dim]Get your key from: https://console.anthropic.com/[/dim]\n")
            api_key = Prompt.ask("Enter your Anthropic API key (or type /quit to exit)")
            if api_key.lower() in ['/quit', '/exit', 'quit', 'exit']:
                return
            config.set_api_key(api_key)
            console.print("[green]✓ API key saved![/green]\n")
        
        # Show quick help
        console.print("[dim]Type /help for available commands, or just chat naturally.[/dim]")
        console.print("[dim]Example commands: /morning, /tasks, /note, /search, /add, /done[/dim]\n")
        
        # Initialize assistant
        try:
            self.assistant = Assistant()
            self.assistant.load_history_from_today()
        except ValueError as e:
            console.print(f"[red]Error initializing assistant: {e}[/red]")
            return
        
        # Show context
        morning_entry = storage.get_morning_entry()
        if morning_entry:
            console.print("[dim]💡 I remember your morning reflection and current tasks.[/dim]\n")
        
        self.running = True
        
        # Main REPL loop
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("[bold green]>[/bold green]")
                
                if not user_input.strip():
                    continue
                
                # Check if it's a command
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                else:
                    # Default: chat with assistant
                    self._handle_chat(user_input)
                
            except KeyboardInterrupt:
                console.print("\n")
                self.cmd_quit()
                break
            except EOFError:
                console.print("\n")
                self.cmd_quit()
                break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]\n")
    
    def _handle_command(self, user_input: str):
        """Route command to appropriate handler."""
        # Split command and arguments
        parts = user_input.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Find and execute command
        if command in self.commands:
            self.commands[command](args)
        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            console.print("[dim]Type /help to see available commands.[/dim]\n")
    
    def _handle_chat(self, user_input: str):
        """Handle natural language chat."""
        # Check for task creation intent
        task_intent = self.assistant.parse_task_intent(user_input)
        if task_intent:
            self._handle_task_creation(task_intent)
            return
        
        # Send to Claude
        console.print()
        with console.status("[cyan]Thinking...[/cyan]"):
            response = self.assistant.send_message(user_input)
        
        # Display response
        console.print("[bold blue]Assistant[/bold blue]")
        console.print(Markdown(response))
        console.print()
    
    def _handle_task_creation(self, task_intent: dict):
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
            task = task_manager.add_task(task_text)
            console.print(f"[green]✓ Task added: {task.text}[/green]")
            if task.due_date:
                console.print(f"[green]  Due: {task.due_date.strftime('%A, %B %d, %Y')}[/green]")
            self.assistant.refresh_context()
        else:
            console.print("[dim]Task not added.[/dim]")
        
        console.print()
    
    # Command handlers
    
    def cmd_morning(self, args: str):
        """Run morning routine."""
        console.print()
        morning_routine.run()
        console.print()
    
    def cmd_evening(self, args: str):
        """Run evening routine."""
        console.print()
        evening_routine.run()
        console.print()
    
    def cmd_tasks(self, args: str):
        """Show task board."""
        console.print()
        
        today_tasks = task_manager.get_today_tasks()
        upcoming_tasks = task_manager.get_upcoming_tasks()
        inbox_tasks = task_manager.get_inbox_tasks()
        
        # Today's tasks
        if today_tasks:
            console.print("[bold yellow]📌 TODAY[/bold yellow]")
            for i, task in enumerate(today_tasks, 1):
                console.print(f"  {i}. {task.text}")
            console.print()
        
        # Upcoming tasks
        if upcoming_tasks:
            console.print("[bold blue]📅 UPCOMING[/bold blue]")
            for task in upcoming_tasks[:10]:
                due_str = task.due_date.strftime("%a, %b %d") if task.due_date else ""
                console.print(f"  • {task.text} [dim]({due_str})[/dim]")
            if len(upcoming_tasks) > 10:
                console.print(f"  [dim]... and {len(upcoming_tasks) - 10} more[/dim]")
            console.print()
        
        # Inbox
        if inbox_tasks:
            console.print("[bold cyan]📥 INBOX[/bold cyan]")
            for task in inbox_tasks[:5]:
                console.print(f"  • {task.text}")
            if len(inbox_tasks) > 5:
                console.print(f"  [dim]... and {len(inbox_tasks) - 5} more[/dim]")
            console.print()
        
        if not (today_tasks or upcoming_tasks or inbox_tasks):
            console.print("[dim]No tasks yet. Add one with:[/dim]")
            console.print("[dim]  /add your task description[/dim]")
            console.print("[dim]  Or just say: \"remind me tomorrow to call mom\"[/dim]\n")
        
        # Show stats
        stats = task_manager.get_task_stats()
        console.print(f"[dim]Total: {stats['incomplete']} incomplete • {stats['completed_today']} completed today[/dim]\n")
    
    def cmd_today(self, args: str):
        """Show today's plan based on morning reflection."""
        console.print()
        
        morning_entry = storage.get_morning_entry()
        if not morning_entry:
            console.print("[yellow]You haven't done your morning routine yet today.[/yellow]")
            console.print("[dim]Run /morning to create your daily plan.[/dim]\n")
            return
        
        # Show morning reflection summary
        console.print("[bold cyan]📋 Today's Plan[/bold cyan]\n")
        
        responses = morning_entry.get("metadata", {}).get("responses", {})
        
        # Show the key success metric
        success_question = "What's THE one thing that would make today a success?"
        if success_question in responses:
            console.print("[bold]🎯 Today's Main Goal:[/bold]")
            console.print(f"  {responses[success_question]}\n")
        
        # Show tasks
        today_tasks = task_manager.get_today_tasks()
        if today_tasks:
            console.print("[bold]📌 Tasks for Today:[/bold]")
            for i, task in enumerate(today_tasks, 1):
                console.print(f"  {i}. {task.text}")
            console.print()
        
        # Show what they're avoiding
        avoid_question = "What are you avoiding that needs attention?"
        if avoid_question in responses:
            console.print("[bold]⚠️  Don't Forget:[/bold]")
            console.print(f"  {responses[avoid_question]}\n")
        
        console.print("[dim]Type /morning to see your full morning reflection.[/dim]\n")
    
    def cmd_add(self, args: str):
        """Add a new task."""
        if not args.strip():
            args = Prompt.ask("What task would you like to add?")
        
        console.print()
        try:
            task = task_manager.add_task(args)
            console.print(f"[green]✓ Task added:[/green] {task.text}")
            if task.due_date:
                console.print(f"[green]  Due:[/green] {task.due_date.strftime('%A, %B %d, %Y')}")
            
            # Suggest projects
            self._suggest_project_for_task(task)
            
            console.print()
            
            # Refresh assistant context
            if self.assistant:
                self.assistant.refresh_context()
        except Exception as e:
            console.print(f"[red]Error adding task: {e}[/red]\n")
    
    def _suggest_project_for_task(self, task):
        """Suggest projects for a newly created task."""
        try:
            from projects import project_manager
            
            # Get all projects
            all_projects = storage.load_projects()
            
            if not all_projects:
                # No projects yet, ask if user wants to create one
                console.print("\n[dim]No projects yet. Would you like to create one for this task?[/dim]")
                create = Prompt.ask("Create a project?", choices=["y", "n"], default="n")
                if create == "y":
                    project_name = Prompt.ask("Project name")
                    project_desc = Prompt.ask("Project description (optional)", default="")
                    
                    project = project_manager.create_project(project_name, project_desc)
                    project_manager.assign_task_to_project(task.id, project.id)
                    console.print(f"[green]✓ Created project '{project_name}' and assigned task[/green]")
                return
            
            # Get project suggestions using embeddings
            suggestions = project_manager.suggest_projects_for_text(task.text, top_k=3)
            
            if suggestions:
                console.print("\n[cyan]📁 Suggested projects:[/cyan]")
                for i, (project, score) in enumerate(suggestions, 1):
                    desc = f" - {project.description}" if project.description else ""
                    console.print(f"  {i}. {project.name}{desc}")
                
                console.print(f"  {len(suggestions) + 1}. Create new project")
                console.print(f"  n. No project")
                
                choice = Prompt.ask(
                    "Assign to project?",
                    default="n"
                )
                
                if choice.lower() != 'n':
                    try:
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(suggestions):
                            # Assign to suggested project
                            selected_project = suggestions[choice_num - 1][0]
                            project_manager.assign_task_to_project(task.id, selected_project.id)
                            console.print(f"[green]✓ Assigned to '{selected_project.name}'[/green]")
                        elif choice_num == len(suggestions) + 1:
                            # Create new project
                            project_name = Prompt.ask("Project name")
                            project_desc = Prompt.ask("Project description (optional)", default="")
                            
                            project = project_manager.create_project(project_name, project_desc)
                            project_manager.assign_task_to_project(task.id, project.id)
                            console.print(f"[green]✓ Created project '{project_name}' and assigned task[/green]")
                    except ValueError:
                        pass  # Invalid input, skip
            else:
                # No good suggestions, offer to create new project
                console.print("\n[dim]No similar projects found.[/dim]")
                create = Prompt.ask("Create a new project for this task?", choices=["y", "n"], default="n")
                if create == "y":
                    project_name = Prompt.ask("Project name")
                    project_desc = Prompt.ask("Project description (optional)", default="")
                    
                    project = project_manager.create_project(project_name, project_desc)
                    project_manager.assign_task_to_project(task.id, project.id)
                    console.print(f"[green]✓ Created project '{project_name}' and assigned task[/green]")
        
        except Exception as e:
            # Project suggestions are optional, don't break the flow
            console.print(f"[dim]Note: Could not suggest projects: {e}[/dim]")
    
    def cmd_done(self, args: str):
        """Mark a task as complete."""
        console.print()
        
        today_tasks = task_manager.get_today_tasks()
        if not today_tasks:
            console.print("[yellow]No tasks for today![/yellow]\n")
            return
        
        console.print("[bold]Today's tasks:[/bold]")
        for i, task in enumerate(today_tasks, 1):
            console.print(f"  {i}. {task.text}")
        
        choice = Prompt.ask("\nWhich task did you complete? (number)")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(today_tasks):
                task = today_tasks[idx]
                task_manager.complete_task(task.id)
                console.print(f"\n[green]✓ Completed:[/green] {task.text}\n")
                
                # Refresh assistant context
                if self.assistant:
                    self.assistant.refresh_context()
            else:
                console.print("[red]Invalid choice[/red]\n")
        except ValueError:
            console.print("[red]Invalid choice[/red]\n")
    
    def cmd_quick_note(self, args: str):
        """Create a quick inline note (no LLM response)."""
        console.print()
        console.print("[bold cyan]📝 Quick Note[/bold cyan]\n")
        
        note_text = Prompt.ask("Note")
        
        if note_text.strip():
            # Save as a note entry
            title = note_text[:50] + "..." if len(note_text) > 50 else note_text
            storage.add_note_to_journal(title, note_text)
            console.print("\n[green]✓ Note saved![/green]\n")
        else:
            console.print("[dim]Note cancelled.[/dim]\n")
    
    def cmd_write_note(self, args: str):
        """Create a rich markdown note in the web editor."""
        console.print()
        console.print("[bold cyan]📝 Opening note editor...[/bold cyan]")
        console.print("[dim]A new browser window will open.[/dim]\n")
        
        try:
            from note_editor import open_note_editor
            result = open_note_editor()
            
            if result:
                console.print(f"\n[green]✓ Note saved: {result['title']}[/green]\n")
            else:
                console.print("\n[dim]Note editor closed without saving.[/dim]\n")
        except Exception as e:
            console.print(f"\n[red]Error opening note editor: {e}[/red]\n")
    
    def cmd_log(self, args: str):
        """Open daily journal in web editor."""
        import webbrowser
        import threading
        
        # Parse the date argument
        target_date = None
        if not args or args.lower() == 'today':
            target_date = datetime.now()
        else:
            try:
                target_date = datetime.strptime(args.strip(), "%Y-%m-%d")
            except ValueError:
                console.print()
                console.print(f"[red]Invalid date format. Use YYYY-MM-DD (e.g., 2025-11-20)[/red]\n")
                return
        
        # Import and start the journal editor
        try:
            from note_editor import start_journal_editor
            
            console.print()
            console.print(f"[cyan]Opening journal editor for {target_date.strftime('%Y-%m-%d')}...[/cyan]")
            console.print("[dim]The editor will open in your browser[/dim]")
            console.print("[dim]Press Ctrl+C here to stop the server[/dim]\n")
            
            # Start editor in a thread and open browser
            def open_browser():
                import time
                time.sleep(1)  # Wait for server to start
                webbrowser.open('http://localhost:5556')
            
            threading.Thread(target=open_browser, daemon=True).start()
            start_journal_editor(target_date)
            
        except KeyboardInterrupt:
            console.print("\n[cyan]Editor closed.[/cyan]\n")
        except Exception as e:
            console.print()
            console.print(f"[red]Error starting editor: {e}[/red]\n")
    
    def cmd_search(self, args: str):
        """Perform semantic search across journals, tasks, and projects."""
        if not args.strip():
            console.print("[yellow]Usage: /search <query>[/yellow]")
            console.print("[dim]Example: /search things to read[/dim]\n")
            return
        
        console.print()
        try:
            from embeddings import get_embeddings_manager
            
            with console.status(f"[cyan]Searching for: {args}...[/cyan]"):
                embeddings_mgr = get_embeddings_manager()
                
                if not embeddings_mgr:
                    console.print("[yellow]Semantic search not available. Please configure your OpenAI API key:[/yellow]")
                    console.print("  [cyan]./focus config --openai-key YOUR_KEY[/cyan]")
                    console.print("\n[dim]Or run: /config to set it up[/dim]\n")
                    return
                
                # Search with a relevance threshold of 0.65 (fairly strict)
                results = embeddings_mgr.search(args, top_k=15, distance_threshold=0.65)
            
            if not results:
                console.print(f"[yellow]No results found for '{args}'[/yellow]\n")
                return
            
            # Group results by type
            journals = [r for r in results if r.result_type == 'journal']
            tasks = [r for r in results if r.result_type == 'task']
            projects = [r for r in results if r.result_type == 'project']
            
            console.print(f"[bold cyan]🔍 Search Results for: {args}[/bold cyan]\n")
            
            # Display journal entries
            if journals:
                console.print("[bold yellow]📔 Journal Entries[/bold yellow]")
                for result in journals[:8]:  # Limit to top 8 journals
                    date = result.metadata.get('date', 'Unknown')
                    section = result.metadata.get('section', 'Unknown')
                    entry_type = result.metadata.get('type', 'journal')
                    
                    # Calculate similarity percentage (inverse of distance)
                    similarity = int((1 - result.distance) * 100)
                    
                    # Truncate content if too long
                    content = result.content
                    if len(content) > 200:
                        content = content[:200] + "..."
                    
                    console.print(f"\n[cyan]{date}[/cyan] • [dim]{section} ({entry_type}) • {similarity}% match[/dim]")
                    console.print(f"[white]{content}[/white]")
                
                console.print()
            
            # Display tasks
            if tasks:
                console.print("[bold green]✓ Tasks[/bold green]")
                for result in tasks[:5]:  # Limit to top 5 tasks
                    status = result.metadata.get('status', 'unknown')
                    completed = result.metadata.get('completed', False)
                    similarity = int((1 - result.distance) * 100)
                    
                    status_icon = "✓" if completed else "○"
                    status_color = "dim" if completed else "white"
                    
                    console.print(f"\n{status_icon} [{status_color}]{result.content}[/{status_color}] [dim]({similarity}% match)[/dim]")
                    console.print(f"[dim]  Status: {status}[/dim]")
                
                console.print()
            
            # Display projects
            if projects:
                console.print("[bold blue]📁 Projects[/bold blue]")
                for result in projects:
                    name = result.metadata.get('name', 'Unknown')
                    similarity = int((1 - result.distance) * 100)
                    console.print(f"\n[blue]• {name}[/blue] [dim]({similarity}% match)[/dim]")
                    console.print(f"[white]{result.content}[/white]")
                
                console.print()
            
            console.print(f"[dim]Found {len(results)} total results[/dim]\n")
            
        except Exception as e:
            console.print(f"[red]Error during search: {e}[/red]")
            console.print(f"[dim]Make sure you've run: ./focus index[/dim]\n")
    
    def cmd_projects(self, args: str):
        """Display all projects."""
        console.print()
        
        projects = storage.load_projects()
        
        if not projects:
            console.print("[dim]No projects yet. Projects will be suggested when you add tasks.[/dim]")
            console.print("[dim]Try adding a task with: /add <task description>[/dim]\n")
            return
        
        console.print("[bold blue]📁 Your Projects[/bold blue]\n")
        
        for project in projects:
            console.print(f"[bold cyan]{project.name}[/bold cyan]")
            if project.description:
                console.print(f"[dim]{project.description}[/dim]")
            
            # Count tasks in this project
            tasks = storage.load_tasks()
            project_tasks = [t for t in tasks if t.project_id == project.id and not t.completed]
            if project_tasks:
                console.print(f"[yellow]{len(project_tasks)} active task(s)[/yellow]")
            
            console.print()
        
        console.print()
    
    def cmd_stats(self, args: str):
        """Show productivity statistics."""
        console.print()
        
        stats = task_manager.get_task_stats()
        
        table = Table(title="📊 Your Stats", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="bold")
        
        table.add_row("✓ Completed today", str(stats['completed_today']))
        table.add_row("📌 Tasks for today", str(stats['today']))
        table.add_row("📅 Upcoming tasks", str(stats['upcoming']))
        table.add_row("📥 Inbox tasks", str(stats['inbox']))
        table.add_row("• Total incomplete", str(stats['incomplete']))
        
        console.print(table)
        console.print()
    
    def cmd_config(self, args: str):
        """Configure settings."""
        console.print()
        console.print("[bold cyan]⚙️  Configuration[/bold cyan]\n")
        
        current_key = config.get_api_key()
        if current_key:
            masked_key = current_key[:8] + "..." + current_key[-4:]
            console.print(f"Current API key: {masked_key}")
            change = Prompt.ask("Change API key?", choices=["y", "n"], default="n")
            if change == "n":
                console.print()
                return
        
        console.print("\n[dim]Get your API key from: https://console.anthropic.com/[/dim]")
        new_key = Prompt.ask("Enter your Anthropic API key")
        
        if new_key:
            config.set_api_key(new_key)
            console.print("\n[green]✓ API key saved![/green]\n")
        else:
            console.print("[yellow]No changes made.[/yellow]\n")
    
    def cmd_help(self, args: str):
        """Show help information."""
        console.print()
        help_text = """
# Focus Assistant Commands

## Daily Routines
- `/morning` - Start your morning routine and plan the day
- `/evening` - Reflect on your day with evening routine
- `/today` - Show today's plan and main goal

## Task Management
- `/tasks` - View your task board (today, upcoming, inbox)
- `/add <task>` - Add a new task
- `/done` - Mark a task as complete
- `/stats` - Show productivity statistics

## Search & Projects
- `/search <query>` - Search your notes, tasks, and projects semantically
- `/projects` - View all your projects

## Notes & Writing
- `/note` - Create a quick inline note (no LLM response)
- `/write` - Create a rich markdown note (opens in browser)
- `/log [date]` - Open your daily journal in web editor (today, or YYYY-MM-DD)

## Settings
- `/config` - Configure API key and settings
- `/help` - Show this help message
- `/quit` or `/exit` - Exit the assistant

## Natural Conversation
Just type naturally without a slash command to chat with the assistant!

**Examples:**
- "remind me tomorrow to call mom" → creates a task
- "what should I focus on today?" → get advice
- "I'm feeling overwhelmed" → get support
- "/search things to read" → find all reading-related notes
"""
        console.print(Panel(Markdown(help_text), title="Help", border_style="cyan"))
        console.print()
    
    def cmd_quit(self, args: str = ""):
        """Exit the interactive session."""
        console.print("\n[cyan]Thanks for using Focus Assistant![/cyan]")
        console.print("[dim]Your progress has been saved. See you next time![/dim]\n")
        self.running = False


# Global session instance
interactive_session = InteractiveSession()
