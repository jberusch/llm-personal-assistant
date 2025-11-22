"""Interactive REPL-style interface for Focus Assistant."""

import json

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from anthropic import Anthropic

from assistant import Assistant
from tasks import task_manager
from routines import morning_routine, evening_routine
from storage import storage
from config import config

console = Console()
AI_TRIAGE_MODEL = "claude-3-5-haiku-latest"

# Try to import Google integrations (may not be configured)
try:
    from google_integration import google_integration
    GOOGLE_AVAILABLE = google_integration is not None
except ImportError:
    GOOGLE_AVAILABLE = False
    google_integration = None


class InteractiveSession:
    """Main interactive REPL-style session for Focus Assistant."""
    
    def __init__(self):
        self.assistant = None
        self.running = False
        self.commands = {
            '/morning': self.cmd_morning,
            '/morning-legacy': self.cmd_morning_legacy,
            '/intention': self.cmd_intention,
            '/evening': self.cmd_evening,
            '/tasks': self.cmd_tasks,
            '/today': self.cmd_today,
            '/add': self.cmd_add,
            '/done': self.cmd_done,
            '/note': self.cmd_quick_note,
            '/write': self.cmd_write_note,
            '/log': self.cmd_log,
            '/calendar': self.cmd_calendar,
            '/schedule': self.cmd_schedule,
            '/email': self.cmd_email,
            # Legacy shortcuts (still supported)
            '/inbox': self._email_inbox,
            '/reply': self._email_reply,
            '/cleanup': self._email_cleanup,
            '/archive': self._email_archive,
            '/search': self.cmd_search_router,
            '/places': self.cmd_places,
            '/projects': self.cmd_projects,
            '/tracker': self.cmd_tracker,
            '/stats': self.cmd_stats,
            '/config': self.cmd_config,
            '/help': self.cmd_help,
            '/quit': self.cmd_quit,
            '/exit': self.cmd_quit,
        }

        # Command metadata for autocomplete with descriptions
        self.command_metadata = {
            '/morning': 'Complete morning flow (sleep, daily pages, intention)',
            '/morning-legacy': 'Run legacy morning routine with questions',
            '/intention': "View today's intention and priorities",
            '/evening': 'Reflect on your day with evening routine',
            '/today': "Show today's plan and main goal",
            '/tasks': 'View your task board (today, upcoming, inbox)',
            '/add': 'Add a new task',
            '/done': 'Mark a task as complete',
            '/note': 'Create a quick inline note',
            '/write': 'Write a markdown note with preview (opens in browser)',
            '/log': 'View your daily log (intention, pages, tasks, notes)',
            '/calendar': 'View calendar events',
            '/schedule': 'Create a calendar event',
            '/email': 'Email utilities (/email inbox/read/reply/cleanup)',
            '/inbox': 'Legacy alias: view unread Gmail messages',
            '/reply': 'Legacy alias: draft and send a reply',
            '/archive': 'Legacy alias: archive emails',
            '/cleanup': 'Legacy alias: bulk clean unwanted emails',
            '/search': 'Search the web or your history (/search web <query> or /search history <query>)',
            '/places': 'Find nearby places (cafes, restaurants, etc.)',
            '/projects': 'View all your projects',
            '/tracker': 'View tracker history (e.g., /tracker sleep)',
            '/stats': 'Show productivity statistics',
            '/config': 'Configure API key and settings',
            '/help': 'Show help message',
            '/quit': 'Exit the assistant',
            '/exit': 'Exit the assistant',
        }

        # Set up command completer
        self.completer = WordCompleter(
            list(self.command_metadata.keys()),
            meta_dict=self.command_metadata,
            ignore_case=True,
            sentence=True,  # Allow completion mid-sentence
        )

        # Set up custom key bindings
        self.kb = KeyBindings()

        # Option+Delete (Alt+Backspace) - delete word backward
        @self.kb.add('escape', 'backspace')  # Alt+Backspace
        def _(event):
            """Delete the word before the cursor."""
            buff = event.current_buffer
            buff.delete_before_cursor(count=buff.document.find_start_of_previous_word())

        # Option+Delete for forward delete (on Mac, this might be Alt+Delete or Alt+D)
        @self.kb.add('escape', 'd')  # Alt+D
        def _(event):
            """Delete the word after the cursor."""
            buff = event.current_buffer
            buff.delete(count=buff.document.find_next_word_ending())

        # Set up prompt session with history, completer, and key bindings
        self.history = InMemoryHistory()
        self.prompt_style = PromptStyle.from_dict({
            'prompt': '#00ff00 bold',  # Green prompt like terminal
        })
        self.inbox_cache: List[Dict[str, Any]] = []
        self.session = PromptSession(
            history=self.history,
            style=self.prompt_style,
            completer=self.completer,
            complete_while_typing=True,  # Show completions as you type
            key_bindings=self.kb,
        )

    def _show_welcome_screen(self):
        """Display retro ASCII art welcome screen."""
        welcome_art = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗ ██████╗  ██████╗██╗   ██╗███████╗                ║
║   ██╔════╝██╔═══██╗██╔════╝██║   ██║██╔════╝                ║
║   █████╗  ██║   ██║██║     ██║   ██║███████╗                ║
║   ██╔══╝  ██║   ██║██║     ██║   ██║╚════██║                ║
║   ██║     ╚██████╔╝╚██████╗╚██████╔╝███████║                ║
║   ╚═╝      ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝                ║
║                                                               ║
║              Your Personal Productivity Coach                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        console.print(f"[bold cyan]{welcome_art}[/bold cyan]")
        console.print("[dim]  Type /help for commands  •  Just chat naturally for AI assistance[/dim]\n")
    
    def start(self):
        """Start the interactive session."""
        # Retro welcome screen
        self._show_welcome_screen()
        
        # Check for API key
        if not config.get_api_key():
            console.print("[yellow]⚠ No API key found.[/yellow]")
            console.print("[dim]Get your key from: https://console.anthropic.com/[/dim]\n")
            api_key = self.session.prompt("Enter your Anthropic API key (or type /quit to exit): ")
            if api_key.lower() in ['/quit', '/exit', 'quit', 'exit']:
                return
            config.set_api_key(api_key)
            console.print("[green]✓ API key saved![/green]\n")
        
        # Initialize assistant
        try:
            self.assistant = Assistant()
            self.assistant.load_history_from_today()
        except ValueError as e:
            console.print(f"[red]Error initializing assistant: {e}[/red]")
            return
        
        # Check if morning flow needs to be completed
        from routines import morning_routine
        if not morning_routine.is_completed():
            console.print("[yellow]Let's start your day with the morning flow...[/yellow]\n")
            morning_routine.run()
        
        # Show context
        morning_entry = storage.get_morning_entry()
        if morning_entry:
            console.print("[dim]💡 I remember your morning reflection and current tasks.[/dim]\n")
        
        self.running = True
        
        # Main REPL loop
        while self.running:
            try:
                # Print separator line above input
                terminal_width = console.width
                console.print(f"[dim]{'─' * terminal_width}[/dim]")

                # Get user input with history support (up arrow works!)
                user_input = self.session.prompt("> ")
                
                if not user_input.strip():
                    continue
                
                # Print separator line below input
                console.print(f"[dim]{'─' * terminal_width}[/dim]\n")
                
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
        """Run morning flow (3-phase: sleep, daily pages, intention)."""
        console.print()
        morning_routine.run()
        console.print()
    
    def cmd_morning_legacy(self, args: str):
        """Run legacy morning routine."""
        console.print()
        from routines import legacy_morning_routine
        legacy_morning_routine.run()
        console.print()
    
    def cmd_intention(self, args: str):
        """Display today's intention."""
        console.print()
        
        journal = storage.load_journal()
        intention = journal.get("intention")
        
        if not intention:
            console.print("[yellow]No intention set yet for today.[/yellow]")
            console.print("[dim]Run /morning to set your intention.[/dim]\n")
            return
        
        from rich.panel import Panel
        from rich.markdown import Markdown
        
        summary = ""
        if intention.get("intention"):
            summary += f"**Intention:** {intention['intention']}\n\n"
        if intention.get("priorities"):
            summary += f"**Key Priorities:** {intention['priorities']}\n\n"
        if intention.get("joy"):
            summary += f"**Bring Joy:** {intention['joy']}\n\n"
        
        if not summary:
            # Fallback if keys don't match - show whatever is in the intention dict
            for key, value in intention.items():
                if value:
                    summary += f"**{key.title()}:** {value}\n\n"
        
        console.print(Panel(
            Markdown(summary.strip()),
            title="[bold cyan]Today's Intention[/bold cyan]",
            border_style="cyan"
        ))
        console.print()
    
    def cmd_evening(self, args: str):
        """Run evening routine."""
        console.print()
        evening_routine.run()
        console.print()
    
    def cmd_tasks(self, args: str):
        """Show task board."""
        # Check if GUI mode is requested
        if args.strip().lower() == 'gui':
            self._open_tasks_gui()
            return
        
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
    
    def _open_tasks_gui(self):
        """Open the tasks GUI in a web browser."""
        import webbrowser
        
        console.print()
        console.print("[cyan]Opening tasks in browser...[/cyan]")
        console.print("[dim]Make sure the web app is running: cd web && npm run dev[/dim]\n")
        
        webbrowser.open('http://localhost:5173/tasks')
        console.print("[green]✓ Opened tasks view[/green]\n")
    
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
    
    def _prompt_for_project_assignment(self) -> str:
        """Prompt user to assign note/task to a project. Returns project_id or None."""
        from projects import project_manager
        
        projects = project_manager.get_all_projects()
        
        if not projects:
            return None
        
        # Ask if they want to assign to a project
        assign = Prompt.ask("\nAssign to a project?", choices=["y", "n"], default="n")
        
        if assign == "n":
            return None
        
        # Show projects
        console.print("\n[bold]Available Projects:[/bold]")
        for i, project in enumerate(projects, 1):
            console.print(f"  {i}. {project.name}")
        console.print(f"  {len(projects) + 1}. Skip")
        
        # Get selection
        choice = Prompt.ask("\nSelect project number")
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                return projects[idx].id
        except ValueError:
            pass
        
        return None
    
    def cmd_quick_note(self, args: str):
        """Create a quick inline note (no LLM response)."""
        console.print()
        console.print("[bold cyan]📝 Quick Note[/bold cyan]\n")
        
        note_text = Prompt.ask("Note")
        
        if note_text.strip():
            # Prompt for project assignment
            project_id = self._prompt_for_project_assignment()
            
            # Save note
            storage.add_note_to_journal(note_text, project_id=project_id)
            
            if project_id:
                from projects import project_manager
                project = project_manager.get_project(project_id)
                console.print(f"\n[green]✓ Note saved and assigned to project: {project.name}[/green]\n")
            else:
                console.print("\n[green]✓ Note saved![/green]\n")
        else:
            console.print("[dim]Note cancelled.[/dim]\n")
    
    def cmd_write_note(self, args: str):
        """Create a rich markdown note in the web editor."""
        import webbrowser
        
        console.print()
        console.print("[bold cyan]📝 Opening note editor...[/bold cyan]")
        console.print("[dim]Make sure the web app is running: cd web && npm run dev[/dim]\n")
        
        webbrowser.open('http://localhost:5173/write')
        console.print("[green]✓ Opened note editor[/green]\n")
    
    def cmd_log(self, args: str):
        """Open daily log in browser."""
        import webbrowser
        
        # Parse the date argument
        if args and args.strip() and args.lower() != 'today':
            try:
                target_date = datetime.strptime(args.strip(), "%Y-%m-%d")
                date_str = target_date.strftime("%Y-%m-%d")
                url = f'http://localhost:5173/log/{date_str}'
            except ValueError:
                console.print()
                console.print(f"[red]Invalid date format. Use YYYY-MM-DD (e.g., 2025-11-20)[/red]\n")
                return
        else:
            url = 'http://localhost:5173/log'
        
        console.print()
        console.print("[cyan]Opening daily log in browser...[/cyan]")
        console.print("[dim]Make sure the web app is running: cd web && npm run dev[/dim]\n")
        
        webbrowser.open(url)
        console.print("[green]✓ Opened daily log[/green]\n")
    
    def cmd_calendar(self, args: str):
        """View calendar events."""
        if (not GOOGLE_AVAILABLE) or (not google_integration.is_configured()):
            console.print()
            console.print("[yellow]⚠️  Google Calendar not configured yet[/yellow]")
            console.print("[dim]See GOOGLE_CALENDAR_SETUP.md for setup instructions[/dim]\n")
            return
        
        console.print()
        
        # Parse arguments
        args = args.strip().lower()
        
        if not args or args == 'today':
            events = google_integration.get_events_today()
            title = "📅 Today's Calendar"
        elif args == 'tomorrow':
            events = google_integration.get_events_tomorrow()
            title = "📅 Tomorrow's Calendar"
        elif args in ['weekend', 'this weekend']:
            events = google_integration.get_weekend_events()
            title = "📅 This Weekend"
        elif args in ['week', 'this week']:
            events = google_integration.get_events_this_week()
            title = "📅 This Week"
        else:
            console.print("[yellow]Usage: /calendar [today|tomorrow|weekend|week][/yellow]\n")
            return
        
        formatted = google_integration.format_events_for_display(events)
        console.print(Panel(formatted, title=title, border_style="cyan"))
        console.print()
    
    def cmd_schedule(self, args: str):
        """Create a calendar event using natural language."""
        if (not GOOGLE_AVAILABLE) or (not google_integration.is_configured()):
            console.print()
            console.print("[yellow]⚠️  Google Calendar not configured yet[/yellow]")
            console.print("[dim]See GOOGLE_CALENDAR_SETUP.md for setup instructions[/dim]\n")
            return
        
        if not args.strip():
            console.print()
            console.print("[yellow]Usage: /schedule <event description>[/yellow]")
            console.print("[dim]Example: /schedule Team meeting tomorrow at 2pm[/dim]\n")
            return
        
        console.print()
        console.print("[cyan]Creating calendar event...[/cyan]")
        
        # Use the assistant to parse the event details
        prompt = f"""The user wants to create a calendar event. Parse this into structured data:
        
"{args}"

Return ONLY a JSON object with these fields:
{{
    "summary": "event title",
    "start_time": "YYYY-MM-DD HH:MM",
    "duration_hours": 1.0,
    "description": "optional description"
}}

Use 24-hour format. If no time is specified, use 09:00. If no date, use tomorrow."""
        
        try:
            import json
            response = self.assistant.ask_question(prompt)
            
            # Extract JSON from response
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0].strip()
            else:
                json_str = response.strip()
            
            event_data = json.loads(json_str)
            
            # Parse start time
            from dateutil.parser import parse as parse_date
            start_time = parse_date(event_data['start_time'])
            duration_hours = event_data.get('duration_hours', 1.0)
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Create the event
            created_event = google_integration.create_event(
                summary=event_data['summary'],
                start_time=start_time,
                end_time=end_time,
                description=event_data.get('description', '')
            )

            if created_event:
                console.print(f"[green]✓ Created event: {created_event['summary']}[/green]")
                console.print(f"[dim]  {start_time.strftime('%A, %B %d at %I:%M %p')}[/dim]")
                if created_event.get('htmlLink'):
                    console.print(f"[dim]  {created_event['htmlLink']}[/dim]")
            else:
                console.print("[red]Failed to create event[/red]")

        except Exception as e:
            console.print(f"[red]Error creating event: {e}[/red]")
        
        console.print()

    def cmd_email(self, args: str):
        """Group command for email actions."""
        args = args.strip()
        if not args or args.lower() in {'help', '-h', '--help'}:
            self._show_email_help()
            return
        
        parts = args.split(None, 1)
        subcommand = parts[0].lower()
        remainder = parts[1] if len(parts) > 1 else ""
        
        dispatch = {
            'inbox': self._email_inbox,
            'list': self._email_inbox,
            'read': self._email_read,
            'open': self._email_read,
            'reply': self._email_reply,
            'cleanup': self._email_cleanup,
            'stage': self._email_cleanup,
            'archive': self._email_archive,
        }
        
        handler = dispatch.get(subcommand)
        if not handler:
            console.print(f"[yellow]Unknown email subcommand: {subcommand}[/yellow]\n")
            self._show_email_help()
            return
        
        handler(remainder)

    def _email_inbox(self, args: str):
        """List unread Gmail messages."""
        if not self._check_google_ready():
            return
        
        count = 10
        arg = args.strip()
        if arg:
            try:
                count = max(1, min(50, int(arg)))
            except ValueError:
                console.print("[red]Please provide a number for how many emails to show.[/red]\n")
                return
        
        console.print()
        try:
            emails = google_integration.list_unread_emails(max_results=count)
        except Exception as e:
            console.print(f"[red]Error loading inbox: {e}[/red]\n")
            return
        
        self.inbox_cache = emails
        if not emails:
            console.print("[dim]Inbox is clear! 🎉[/dim]\n")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("From", style="cyan")
        table.add_column("Subject", style="white")
        table.add_column("Received", style="dim", width=24)
        
        for idx, email in enumerate(emails, 1):
            table.add_row(
                str(idx),
                email.get('from_name', 'Unknown'),
                email.get('subject', '(No subject)'),
                email.get('date', ''),
            )
        
        console.print(table)
        console.print("[dim]Use /email 1 or /reply 1 to read or respond.[/dim]\n")

    def _email_read(self, args: str):
        """Read a specific email."""
        ref = args.strip()
        if not ref:
            console.print("[yellow]Usage: /email <index_or_id>[/yellow]\n")
            return
        
        if not self._check_google_ready():
            return
        
        summary = self._resolve_email_reference(ref)
        if not summary:
            console.print(f"[red]Email '{ref}' not found.[/red]\n")
            return
        
        message = google_integration.get_email(summary['id'])
        if not message:
            console.print("[red]Unable to load email content.[/red]\n")
            return
        
        console.print()
        console.print(Panel(
            f"[bold]{message['subject']}[/bold]\n"
            f"[cyan]{message['from_name']}[/cyan] <{message['from_email']}>\n"
            f"[dim]{message['date']}[/dim]\n\n"
            f"{message['body'] or '[dim](No body)'}",
            title="📧 Email",
            border_style="blue"
        ))
        console.print()

    def _email_reply(self, args: str):
        """Draft and send a reply."""
        ref = args.strip()
        if not ref:
            console.print("[yellow]Usage: /reply <index_or_id>[/yellow]\n")
            return
        
        if not self._check_google_ready():
            return
        
        summary = self._resolve_email_reference(ref)
        if not summary:
            console.print(f"[red]Email '{ref}' not found.[/red]\n")
            return
        
        message = google_integration.get_email(summary['id'])
        if not message:
            console.print("[red]Unable to load email content.[/red]\n")
            return
        
        if self.assistant is None:
            self.assistant = Assistant()
        
        console.print("[cyan]Drafting reply with AI...[/cyan]")
        prompt = (
            "Draft a concise, thoughtful reply in natural first-person voice.\n\n"
            f"Subject: {message['subject']}\n"
            f"From: {message['from_name']} <{message['from_email']}>\n"
            f"Body:\n{message['body'] or message['snippet']}"
        )
        
        try:
            draft = self.assistant.ask_question(prompt)
        except Exception as e:
            console.print(f"[red]Error drafting reply: {e}[/red]\n")
            return
        
        console.print()
        console.print(Panel(draft.strip(), title="✉️ Draft Reply", border_style="green"))
        console.print()
        
        send = Prompt.ask("Send this reply?", choices=["y", "n"], default="y")
        if send.lower() != 'y':
            console.print("[yellow]Draft not sent.[/yellow]\n")
            return
        
        subject = message['subject'] or "(No subject)"
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
        
        sent_id = google_integration.send_email(
            to=message['from_email'],
            subject=subject,
            body=draft.strip(),
            thread_id=message.get('threadId')
        )
        
        if sent_id:
            google_integration.mark_as_read(message['id'])
            console.print(f"[green]✓ Reply sent![/green] [dim](message id: {sent_id})[/dim]\n")
        else:
            console.print("[red]Failed to send email.[/red]\n")

    def _email_archive(self, args: str):
        """Archive or delete one or more emails."""
        tokens = args.strip().split()
        delete_mode = False
        refs: List[str] = []
        for token in tokens:
            if token in {'--delete', '-d'}:
                delete_mode = True
            else:
                refs.append(token)
        if not refs:
            console.print("[yellow]Usage: /email archive <index_or_id> [more...] [--delete][/yellow]\n")
            return
        
        if not self._check_google_ready():
            return
        
        processed = 0
        for ref in refs:
            summary = self._resolve_email_reference(ref)
            if not summary:
                console.print(f"[red]Email '{ref}' not found, skipping.[/red]")
                continue
            if delete_mode:
                google_integration.delete_email(summary['id'])
            else:
                google_integration.archive_email(summary['id'])
            processed += 1
        
        verb = "Deleted" if delete_mode else "Archived"
        console.print(f"[green]{verb} {processed} email(s).[/green]\n")

    def _email_cleanup(self, args: str):
        """Cleanup newsletters or staged query results."""
        if not self._check_google_ready():
            return
        
        args = args.strip()
        action = 'archive'
        source_desc = ''
        
        if args:
            console.print(f"\n[cyan]Staging cleanup query:[/cyan] {args}")
            stage = self._stage_query_cleanup(args)
            if not stage:
                return
            newsletters = stage['emails']
            action = stage['action']
            source_desc = stage.get('summary', '')
        else:
            console.print("\n[cyan]Scanning inbox for newsletters...[/cyan]")
            try:
                newsletters = self._detect_newsletter_candidates()
            except Exception as e:
                console.print(f"[red]Error scanning inbox: {e}[/red]\n")
                return
            if not newsletters:
                console.print("[green]Inbox looks good! No obvious newsletters detected.[/green]\n")
                return
        
        for idx, email in enumerate(newsletters, 1):
            email['_list_index'] = idx
        
        ai_keep_indices: Set[int] = set()
        if config.is_ai_triage_enabled():
            triage_map = self._ai_triage_emails(newsletters)
            if triage_map:
                for email in newsletters:
                    decision = triage_map.get(email['id'])
                    if decision:
                        email['_ai_decision'] = decision.get('decision')
                        email['_ai_reason'] = decision.get('reason', '')
                ai_keep_indices = {
                    email['_list_index']
                    for email in newsletters
                    if email.get('_ai_decision') == 'keep'
                }
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3)
        table.add_column("From", style="cyan")
        table.add_column("Subject", style="white")
        table.add_column("Reason", style="dim")
        
        for email in newsletters:
            table.add_row(
                str(email['_list_index']),
                email['from_name'],
                email['subject'],
                self._format_cleanup_reason(email)
            )
        
        console.print(table)
        if source_desc:
            console.print(f"[dim]Query: {source_desc}[/dim]")
        if ai_keep_indices:
            listed = ", ".join(str(i) for i in sorted(ai_keep_indices))
            console.print(f"[dim]AI suggests keeping: {listed}[/dim]")
        
        index_map = {email['_list_index']: email for email in newsletters}
        
        auto_keep_indices: Set[int] = set()
        if ai_keep_indices:
            auto_keep_confirm = Prompt.ask(
                "Keep the AI-suggested emails?",
                choices=['y', 'n'],
                default='y'
            )
            if auto_keep_confirm.lower() == 'y':
                auto_keep_indices = set(ai_keep_indices)
                for idx in auto_keep_indices:
                    if idx in index_map:
                        google_integration.remember_sender(index_map[idx].get('from_email', ''))
                console.print("[dim]Saved those senders so they won't show up again.[/dim]")
        
        skip_input = Prompt.ask(
            "Enter numbers to keep (e.g., 1,3) or press Enter to continue",
            default=""
        ).strip()
        manual_skip_indices: Set[int] = set()
        if skip_input:
            manual_skip_indices = self._parse_index_list(skip_input, len(newsletters))
            for idx in manual_skip_indices:
                email = index_map.get(idx)
                if email:
                    google_integration.remember_sender(email.get('from_email', ''))
            if manual_skip_indices:
                console.print("[dim]Thanks! I'll remember those senders for next time.[/dim]")
        
        skip_indices = auto_keep_indices | manual_skip_indices
        if skip_indices:
            newsletters = [
                email for email in newsletters
                if email['_list_index'] not in skip_indices
            ]
        
        if not newsletters:
            console.print("[yellow]No emails selected for cleanup.[/yellow]\n")
            return
        
        verb = "Delete" if action == 'delete' else "Archive"
        confirm = Prompt.ask(
            f"{verb} {len(newsletters)} email(s)?",
            choices=['y', 'n'],
            default='y'
        )
        if confirm.lower() != 'y':
            console.print("[yellow]No changes made.[/yellow]\n")
            return
        
        ids = [email['id'] for email in newsletters]
        if action == 'delete':
            deleted = google_integration.bulk_delete(ids)
            console.print(f"[green]✓ Deleted {deleted} email(s).[/green]\n")
        else:
            archived = google_integration.bulk_archive(ids)
            console.print(f"[green]✓ Archived {archived} email(s).[/green]\n")

    # ------------------------------------------------------------------
    # Google helpers
    # ------------------------------------------------------------------
    def _check_google_ready(self) -> bool:
        if not GOOGLE_AVAILABLE or google_integration is None:
            console.print("\n[yellow]Google integrations are not available in this environment.[/yellow]\n")
            return False
        if not google_integration.is_configured():
            console.print("\n[yellow]Google integration not configured yet[/yellow]")
            console.print("[dim]See GOOGLE_CALENDAR_SETUP.md for setup instructions[/dim]\n")
            return False
        if not google_integration.has_token():
            console.print("\n[yellow]Google authentication required[/yellow]")
            console.print("[dim]Run `focus calendar` once to connect your account.[/dim]\n")
            return False
        return True

    def _show_email_help(self):
        console.print("""
[bold]Email Commands:[/bold]
- `/email inbox [count]` – Show unread Gmail messages
- `/email read <index|id>` – Read a specific email
- `/email reply <index|id>` – Draft & send a reply with AI
- `/email cleanup` – Run smart newsletter cleanup
- `/email cleanup <natural query>` – Stage a Gmail search (max 25) for cleanup
- `/email archive <index|id...>` – Archive specific emails
""")
        console.print("[dim]Examples: /email cleanup all emails from wefunder this week[/dim]\n")

    def _resolve_email_reference(self, ref: str) -> Optional[Dict[str, Any]]:
        ref = ref.strip()
        if not ref:
            return None

        if ref.isdigit() and self.inbox_cache:
            idx = int(ref) - 1
            if 0 <= idx < len(self.inbox_cache):
                return self.inbox_cache[idx]

        if self.inbox_cache:
            for email in self.inbox_cache:
                if email['id'].startswith(ref) or ref.lower() in email.get('subject', '').lower():
                    return email

        try:
            message = google_integration.get_email(ref)
            return message
        except Exception:
            return None

    def _looks_like_newsletter(self, email_summary: Dict[str, Any]) -> bool:
        return self._newsletter_reason(email_summary) is not None

    def _parse_index_list(self, raw: str, max_index: int) -> Set[int]:
        indices: Set[int] = set()
        for part in raw.replace(' ', '').split(','):
            if not part:
                continue
            if not part.isdigit():
                console.print(f"[red]'{part}' is not a valid number.[/red]")
                continue
            idx = int(part)
            if 1 <= idx <= max_index:
                indices.add(idx)
            else:
                console.print(f"[red]{idx} is out of range (1-{max_index}).[/red]")
        return indices

    def _newsletter_reason(self, email_summary: Dict[str, Any]) -> Optional[str]:
        if not GOOGLE_AVAILABLE or google_integration is None:
            return None
        sender = (email_summary.get('from_email') or '').lower()
        if google_integration.should_keep_sender(sender):
            return None
        subject = (email_summary.get('subject') or '').lower()
        snippet = (email_summary.get('snippet') or '').lower()
        newsletter_keywords = ['newsletter', 'digest', 'update', 'sale', 'offer', 'unsubscribe']
        sender_keywords = ['noreply', 'no-reply', 'notifications', 'mailer']

        for word in newsletter_keywords:
            if word in subject:
                return f"subject contains '{word}'"
        for word in newsletter_keywords:
            if word in snippet:
                return f"snippet mentions '{word}'"
        for keyword in sender_keywords:
            if keyword in sender:
                return f"sender looks automated ('{keyword}')"
        if sender.endswith('@mailchimp.com') or sender.endswith('@sendgrid.net'):
            return "sent via bulk mailer"
        return None

    def _detect_newsletter_candidates(self) -> List[Dict[str, Any]]:
        emails = google_integration.list_unread_emails(max_results=50)
        candidates: List[Dict[str, Any]] = []
        for email in emails:
            reason = self._newsletter_reason(email)
            if reason:
                entry = dict(email)
                entry['_cleanup_reason'] = reason
                candidates.append(entry)
        return candidates

    def _stage_query_cleanup(self, request: str) -> Optional[Dict[str, Any]]:
        parsed = self._build_email_query(request)
        if not parsed:
            console.print("[red]Could not understand that cleanup request.[/red]\n")
            return None
        gmail_query = parsed.get('gmail_query', '').strip()
        if not gmail_query:
            console.print("[red]Cleanup query cannot be empty.[/red]\n")
            return None
        max_results = min(25, max(1, int(parsed.get('max_results', 25))))
        action = parsed.get('action', 'archive').lower()
        if action not in {'archive', 'delete'}:
            action = 'archive'
        emails = google_integration.search_emails(gmail_query, max_results=max_results)
        if not emails:
            console.print("[yellow]No emails matched that query.[/yellow]\n")
            return None
        for email in emails:
            email['_cleanup_reason'] = f"query: {gmail_query}"
        return {'emails': emails, 'action': action, 'summary': gmail_query}

    def _build_email_query(self, request: str) -> Optional[Dict[str, Any]]:
        request = request.strip()
        if not request:
            return None
        if self.assistant is None:
            self.assistant = Assistant()
        prompt = f"""
You convert natural language cleanup requests into Gmail search instructions.
Return ONLY JSON with these fields:
{{
  "gmail_query": "<Gmail search syntax>",
  "max_results": 25,
  "action": "archive"
}}

Rules:
- Use Gmail query operators (from:, subject:, label:, newer_than:, older_than:, etc.).
- Default max_results to 25 and never exceed 25.
- Default action to "archive" unless the user clearly says delete/trash/remove.
- Always focus on inbox messages unless the user explicitly says otherwise.

Request: "{request}"
"""
        response = self.assistant.ask_question(prompt)
        data = self._extract_json_object(response) or {}
        gmail_query = (data.get('gmail_query') or request).strip()
        max_results = int(data.get('max_results', 25))
        action = (data.get('action') or 'archive').lower()
        if action not in {'archive', 'delete'}:
            action = 'archive'
        return {
            'gmail_query': gmail_query,
            'max_results': max_results,
            'action': action,
        }

    def _format_cleanup_reason(self, email: Dict[str, Any]) -> str:
        ai_decision = email.get('_ai_decision')
        ai_reason = email.get('_ai_reason')
        rule_reason = email.get('_cleanup_reason', 'newsletter detected')
        if ai_decision == 'keep':
            return f"AI keep: {ai_reason or 'looks important'}"
        if ai_decision == 'archive':
            return f"AI archive: {ai_reason or rule_reason}"
        return f"Rule: {rule_reason}"

    def _ai_triage_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        if not emails or not config.is_ai_triage_enabled():
            return {}
        api_key = config.get_api_key()
        if not api_key:
            return {}
        client = Anthropic(api_key=api_key)
        decisions: Dict[str, Dict[str, str]] = {}
        batch_size = 5
        for start in range(0, len(emails), batch_size):
            batch = emails[start:start + batch_size]
            payload = []
            for email in batch:
                payload.append({
                    "id": email['id'],
                    "subject": email.get('subject', '(No subject)'),
                    "from": f"{email.get('from_name', '')} <{email.get('from_email', '')}>",
                    "snippet": email.get('snippet', ''),
                    "reason": email.get('_cleanup_reason', '')
                })
            prompt = (
                "You triage emails for a busy professional. For each email decide whether it should be "
                "'archive' (low priority like newsletters/promotions) or 'keep' (may contain useful info). "
                "If unsure, choose keep. Respond ONLY with JSON array like:\n"
                '[{"id": "...", "decision": "keep", "reason": "..."}, ...]\n\n'
                "Emails:\n"
                f"{json.dumps(payload, ensure_ascii=False)}"
            )
            try:
                response = client.messages.create(
                    model=AI_TRIAGE_MODEL,
                    max_tokens=600,
                    system="You are an email triage assistant. Prefer keeping important messages and be explicit about why.",
                    messages=[{"role": "user", "content": prompt}]
                )
            except Exception:
                continue
            if not response.content:
                continue
            text = response.content[0].text.strip()
            parsed = self._extract_json_array(text)
            if not parsed:
                continue
            for item in parsed:
                email_id = item.get("id")
                decision = item.get("decision", "").lower()
                reason = item.get("reason", "")
                if email_id and decision in {"keep", "archive"}:
                    decisions[email_id] = {
                        "decision": decision,
                        "reason": reason
                    }
        return decisions

    def _extract_json_array(self, text: str) -> Optional[List[Dict[str, Any]]]:
        candidates = []
        if text.startswith("```"):
            parts = text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("{") or part.startswith("["):
                    candidates.append(part)
        candidates.append(text)
        for candidate in candidates:
            try:
                data = json.loads(candidate)
                if isinstance(data, list):
                    return data  # type: ignore[arg-type]
            except json.JSONDecodeError:
                continue
        return None

    def _extract_json_object(self, text: str) -> Optional[Dict[str, Any]]:
        candidates = []
        if text.startswith("```"):
            parts = text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("{"):
                    candidates.append(part)
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                candidates.append(text[start:end])
        for candidate in candidates:
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
        return None
    
    def cmd_search_router(self, args: str):
        """Route search commands to web or history search."""
        args = args.strip()
        if not args:
            console.print("[yellow]Usage:[/yellow]")
            console.print("  /search web <query> [results:N] - Search DuckDuckGo (default 10 results)")
            console.print("  /search history <query> - Search your notes, tasks, and projects")
            console.print("\n[dim]Examples:[/dim]")
            console.print("  /search web python tutorials results:5")
            console.print("  /search history things to read\n")
            return
        
        parts = args.split(None, 1)
        subcommand = parts[0].lower()
        remainder = parts[1] if len(parts) > 1 else ""
        
        if subcommand == 'web':
            self.cmd_search_web(remainder)
        elif subcommand == 'history':
            self.cmd_search_history(remainder)
        else:
            # Default to history search for backward compatibility
            self.cmd_search_history(args)
    
    def cmd_search_history(self, args: str):
        """Perform semantic search across journals, tasks, and projects."""
        if not args.strip():
            console.print("[yellow]Usage: /search history <query>[/yellow]")
            console.print("[dim]Example: /search history things to read[/dim]\n")
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
                results, stats = embeddings_mgr.search(
                    args,
                    top_k=15,
                    distance_threshold=0.65,
                    return_stats=True
                )
            
            fallback_used = stats.get("used_fallback")
            best_distance = stats.get("best_distance")
            fallback_threshold = stats.get("fallback_threshold")
            
            if not results:
                console.print(f"[yellow]No results found for '{args}'[/yellow]")
                if best_distance is not None:
                    console.print(
                        f"[dim]Closest match distance was {best_distance:.3f} "
                        f"(threshold {fallback_threshold:.2f}). Try a broader query.[/dim]\n"
                    )
                console.print()
                return
            
            if fallback_used:
                console.print(
                    f"[dim]Showing lower-confidence matches (distance ≤ {fallback_threshold:.2f}).[/dim]\n"
                )
            
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
    
    def cmd_search_web(self, args: str):
        """Search DuckDuckGo and display results with arrow key navigation."""
        if not args.strip():
            console.print("[yellow]Usage: /search web <query> [results:N][/yellow]")
            console.print("[dim]Example: /search web python tutorials results:5[/dim]\n")
            return
        
        # Parse arguments - look for results:N parameter
        max_results = 10  # default
        query = args.strip()
        
        # Check if results parameter is present
        import re
        results_match = re.search(r'\bresults:(\d+)\b', query, re.IGNORECASE)
        if results_match:
            max_results = min(int(results_match.group(1)), 25)  # cap at 25
            # Remove the results parameter from query
            query = re.sub(r'\s*\bresults:\d+\b\s*', ' ', query, flags=re.IGNORECASE).strip()
        
        if not query:
            console.print("[red]Please provide a search query.[/red]\n")
            return
        
        console.print()
        
        # Check if Google Search is configured (preferred)
        google_search_key = config.get_google_search_key()
        google_search_cx = config.get_google_search_cx()
        
        if google_search_key and google_search_cx:
            # Use Google Custom Search API (more reliable)
            self._search_with_google(query, max_results)
            return
        
        # Fall back to DuckDuckGo
        console.print("[dim]Tip: Configure Google Search for better results: /config[/dim]\n")
        
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            console.print("[red]duckduckgo_search library not installed.[/red]")
            console.print("[dim]Install it with: pip install duckduckgo_search[/dim]\n")
            return
        
        # Try search with automatic retry on rate limit
        results = []
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    with console.status(f"[cyan]Retrying search (attempt {attempt + 1}/{max_retries})...[/cyan]"):
                        import time
                        time.sleep(retry_delay * attempt)  # Exponential backoff
                        ddgs = DDGS()
                        results = list(ddgs.text(query, max_results=max_results))
                else:
                    with console.status(f"[cyan]Searching DuckDuckGo for: {query}...[/cyan]"):
                        ddgs = DDGS()
                        results = list(ddgs.text(query, max_results=max_results))
                
                # If we got here, search succeeded
                break
                
            except Exception as e:
                error_msg = str(e).lower()
                
                if "ratelimit" in error_msg or "rate limit" in error_msg:
                    if attempt < max_retries - 1:
                        # Try again after delay
                        continue
                    else:
                        # Final attempt failed
                        console.print(f"[yellow]⚠️  DuckDuckGo rate limit reached[/yellow]")
                        console.print(f"[dim]DuckDuckGo limits automated searches. Try again in 1-2 minutes.[/dim]")
                        console.print(f"[dim]Tip: Use /search history to search your local notes instead.[/dim]\n")
                        return
                elif "timeout" in error_msg:
                    console.print(f"[yellow]Search timed out.[/yellow]")
                    console.print(f"[dim]Please check your internet connection and try again.[/dim]\n")
                    return
                else:
                    console.print(f"[red]Error during web search: {e}[/red]\n")
                    return
        
        if not results:
            console.print(f"[yellow]No results found for '{query}'[/yellow]\n")
            return
        
        console.print(f"[bold cyan]🌐 Web Search Results for: {query}[/bold cyan]\n")

        # Prepare options for pick library
        options = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            # Truncate title if too long
            if len(title) > 80:
                title = title[:77] + "..."
            options.append(f"{title}")

        # Use pick library for arrow key navigation
        try:
            from pick import pick

            title = "Use ↑/↓ arrows to navigate, Enter to open in browser, Esc to cancel"
            try:
                selected_option, selected_index = pick(options, title, indicator="→")
                
                if selected_index is not None:
                    selected_result = results[selected_index]
                    url = selected_result.get('href', selected_result.get('link', ''))

                    if url:
                        import webbrowser
                        console.print()
                        console.print(f"[cyan]Opening: {selected_result.get('title', 'result')}[/cyan]")
                        console.print(f"[dim]{url}[/dim]\n")
                        webbrowser.open(url)
                    else:
                        console.print("[red]No URL found for this result.[/red]\n")
            except (KeyboardInterrupt, EOFError):
                # User pressed Esc or Ctrl+C to cancel
                console.print("\n[dim]Cancelled.[/dim]\n")
                return

        except ImportError:
            # Fallback: numbered list
            console.print("[yellow]Install 'pick' for arrow key navigation: pip install pick[/yellow]")
            console.print("[dim]Using numbered selection instead...[/dim]\n")

            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                snippet = result.get('body', result.get('snippet', ''))
                url = result.get('href', result.get('link', ''))

                console.print(f"[bold cyan]{i}. {title}[/bold cyan]")
                console.print(f"[dim]{url}[/dim]")
                if snippet:
                    # Truncate snippet
                    if len(snippet) > 150:
                        snippet = snippet[:147] + "..."
                    console.print(f"{snippet}")
                console.print()

            choice = Prompt.ask("Select result number to open (or press Enter to cancel)", default="")

            if choice.strip():
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(results):
                        url = results[idx].get('href', results[idx].get('link', ''))
                        if url:
                            import webbrowser
                            console.print()
                            console.print(f"[cyan]Opening: {results[idx].get('title', 'result')}[/cyan]\n")
                            webbrowser.open(url)
                        else:
                            console.print("[red]No URL found for this result.[/red]\n")
                    else:
                        console.print("[red]Invalid selection[/red]\n")
                except ValueError:
                    console.print("[red]Invalid selection[/red]\n")
    
    def _search_with_google(self, query: str, max_results: int):
        """Search using Google Custom Search API."""
        try:
            from google_search import get_google_search_client
            
            # Get configured client
            google_client = get_google_search_client(
                config.get_google_search_key(),
                config.get_google_search_cx()
            )
            
            if not google_client:
                console.print("[red]Google Search not properly configured.[/red]\n")
                return
            
            with console.status(f"[cyan]Searching Google for: {query}...[/cyan]"):
                # Google CSE API limits to 10 results per request
                results = google_client.search(query, min(max_results, 10))
            
            if not results:
                console.print(f"[yellow]No results found for '{query}'[/yellow]\n")
                return
            
            console.print(f"[bold cyan]🌐 Web Search Results for: {query}[/bold cyan]")
            console.print(f"[dim]Powered by Google Custom Search[/dim]\n")
            
            # Prepare options for pick library
            options = []
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                # Truncate title if too long
                if len(title) > 80:
                    title = title[:77] + "..."
                options.append(f"{title}")
            
            # Use pick library for arrow key navigation
            try:
                from pick import pick
                
                title = "Use ↑/↓ arrows to navigate, Enter to open in browser, Esc to cancel"
                try:
                    selected_option, selected_index = pick(options, title, indicator="→")
                    
                    if selected_index is not None:
                        selected_result = results[selected_index]
                        url = selected_result.get('href', selected_result.get('link', ''))
                        
                        if url:
                            import webbrowser
                            console.print()
                            console.print(f"[cyan]Opening: {selected_result.get('title', 'result')}[/cyan]")
                            console.print(f"[dim]{url}[/dim]\n")
                            webbrowser.open(url)
                        else:
                            console.print("[red]No URL found for this result.[/red]\n")
                except (KeyboardInterrupt, EOFError):
                    # User pressed Esc or Ctrl+C to cancel
                    console.print("\n[dim]Cancelled.[/dim]\n")
                    return
            
            except ImportError:
                # Fallback: numbered list
                console.print("[yellow]Install 'pick' for arrow key navigation: pip install pick[/yellow]")
                console.print("[dim]Using numbered selection instead...[/dim]\n")
                
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'No title')
                    snippet = result.get('body', result.get('snippet', ''))
                    url = result.get('href', result.get('link', ''))
                    
                    console.print(f"[bold cyan]{i}. {title}[/bold cyan]")
                    console.print(f"[dim]{url}[/dim]")
                    if snippet:
                        # Truncate snippet
                        if len(snippet) > 150:
                            snippet = snippet[:147] + "..."
                        console.print(f"{snippet}")
                    console.print()
                
                choice = Prompt.ask("Select result number to open (or press Enter to cancel)", default="")
                
                if choice.strip():
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(results):
                            url = results[idx].get('href', results[idx].get('link', ''))
                            if url:
                                import webbrowser
                                console.print()
                                console.print(f"[cyan]Opening: {results[idx].get('title', 'result')}[/cyan]\n")
                                webbrowser.open(url)
                            else:
                                console.print("[red]No URL found for this result.[/red]\n")
                        else:
                            console.print("[red]Invalid selection[/red]\n")
                    except ValueError:
                        console.print("[red]Invalid selection[/red]\n")
        
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg:
                console.print(f"[yellow]Google Search API quota exceeded.[/yellow]")
                console.print(f"[dim]You've used your 100 free searches today. Try again tomorrow.[/dim]")
                console.print(f"[dim]Or use DuckDuckGo: remove Google keys with /config[/dim]\n")
            elif "authentication" in error_msg or "403" in error_msg:
                console.print(f"[red]Google Search authentication failed.[/red]")
                console.print(f"[dim]Check your API key and CX ID with /config[/dim]\n")
            else:
                console.print(f"[red]Google Search error: {e}[/red]\n")
    
    def cmd_places(self, args: str):
        """Find nearby places using Google Places API."""
        if not args.strip():
            console.print("[yellow]Usage: /places <query>[/yellow]")
            console.print("[dim]Examples:[/dim]")
            console.print("[dim]  /places cafe nearby[/dim]")
            console.print("[dim]  /places pizza in hayes valley[/dim]")
            console.print("[dim]  /places bars on fillmore[/dim]\n")
            return
        
        console.print()
        
        # Check if Google API key is configured
        google_api_key = config.get_google_search_key()
        
        if not google_api_key:
            console.print("[yellow]⚠️  Google Places requires a Google API key[/yellow]")
            console.print("[dim]You can use the same API key from Google Custom Search.[/dim]")
            console.print("[dim]Run /config to set up your Google API key.[/dim]\n")
            return
        
        try:
            from google_places import get_google_places_client, Place
            
            # Get or create client
            places_client = get_google_places_client(google_api_key)
            
            if not places_client:
                console.print("[red]Failed to initialize Places client.[/red]\n")
                return
            
            # Search for places
            with console.status(f"[cyan]Searching for: {args}...[/cyan]"):
                places = places_client.text_search(args, max_results=10)
            
            if not places:
                console.print(f"[yellow]No places found for '{args}'[/yellow]\n")
                return
            
            console.print(f"[bold cyan]📍 Places Near You[/bold cyan]\n")
            
            # Prepare options for pick library
            options = []
            for i, place in enumerate(places, 1):
                display_parts = [place.name]
                
                # Rating summary
                if place.rating:
                    stars = "⭐" * int(round(place.rating))
                    rating_text = f"{stars} {place.rating}"
                    if place.user_ratings_total:
                        rating_text += f" ({place.user_ratings_total} reviews)"
                    display_parts.append(rating_text)
                
                # Open/closed status
                if place.opening_hours:
                    status = "🟢 Open now" if place.opening_hours.get('open_now') else "🔴 Closed"
                    display_parts.append(status)
                
                # Address or vicinity
                address = place.address or place.vicinity
                if address:
                    display_parts.append(address)
                
                # Price level
                if place.price_level is not None:
                    display_parts.append(place.get_price_string())
                
                # Build main line
                display = " • ".join(display_parts)
                
                # Add editorial summary if available
                if place.editorial_summary:
                    summary = place.editorial_summary.strip()
                    if len(summary) > 80:
                        summary = summary[:77] + "..."
                    display += f" — {summary}"
                
                options.append(display)
            
            # Use pick library for arrow key navigation
            try:
                from pick import pick
                
                title = "Use ↑/↓ arrows to navigate, Enter for details, Esc to cancel"
                try:
                    selected_option, selected_index = pick(options, title, indicator="→")
                    
                    if selected_index is not None:
                        selected_place = places[selected_index]
                        self._show_place_details(selected_place, places_client)
                except (KeyboardInterrupt, EOFError):
                    # User pressed Esc or Ctrl+C to cancel
                    console.print("\n[dim]Cancelled.[/dim]\n")
                    return
            
            except ImportError:
                # Fallback: numbered list
                console.print("[yellow]Install 'pick' for arrow key navigation: pip install pick[/yellow]")
                console.print("[dim]Using numbered selection instead...[/dim]\n")
                
                for i, place in enumerate(places, 1):
                    # Show name and rating
                    console.print(f"[bold cyan]{i}. {place.name}[/bold cyan]")
                    
                    if place.rating:
                        stars = "⭐" * int(round(place.rating))
                        review_text = f" ({place.user_ratings_total} reviews)" if place.user_ratings_total else ""
                        console.print(f"   {stars} {place.rating}{review_text}")
                    
                    # Show open/closed status prominently
                    if place.opening_hours:
                        if place.opening_hours.get('open_now'):
                            console.print(f"   [green]🕐 Open now[/green]")
                        else:
                            console.print(f"   [red]🕐 Closed[/red]")
                    
                    # Show address
                    address = place.address or place.vicinity or "Address unknown"
                    console.print(f"   [dim]📍 {address}[/dim]")
                    
                    # Show price if available
                    if place.price_level is not None:
                        console.print(f"   [dim]💰 {place.get_price_string()}[/dim]")
                    
                    # Show editorial summary if available
                    if place.editorial_summary:
                        # Truncate if too long
                        summary = place.editorial_summary
                        if len(summary) > 100:
                            summary = summary[:97] + "..."
                        console.print(f"   [dim italic]{summary}[/dim italic]")
                    
                    console.print()
                
                choice = Prompt.ask("Select place number for details (or press Enter to cancel)", default="")
                
                if choice.strip():
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(places):
                            selected_place = places[idx]
                            self._show_place_details(selected_place, places_client)
                        else:
                            console.print("[red]Invalid selection[/red]\n")
                    except ValueError:
                        console.print("[red]Invalid selection[/red]\n")
        
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg:
                console.print(f"[yellow]Google Places API quota exceeded.[/yellow]")
                console.print(f"[dim]Free tier is $200/month (~5,000-10,000 searches). Try again tomorrow.[/dim]\n")
            elif "authentication" in error_msg or "api" in error_msg or "key" in error_msg:
                console.print(f"[red]Google Places API error.[/red]")
                console.print(f"[dim]Make sure Places API is enabled in Google Cloud Console.[/dim]")
                console.print(f"[dim]See GOOGLE_PLACES_SETUP.md for instructions.[/dim]\n")
            else:
                console.print(f"[red]Error searching places: {e}[/red]\n")
    
    def _show_place_details(self, place: 'Place', places_client):
        """Show detailed information about a place."""
        console.print()
        
        # Get full details
        with console.status(f"[cyan]Loading details for {place.name}...[/cyan]"):
            try:
                full_place = places_client.get_place_details(place.place_id)
            except:
                full_place = place  # Fallback to basic info
        
        # Display details
        from rich.panel import Panel
        
        details = f"[bold cyan]{full_place.name}[/bold cyan]\n\n"
        
        # Rating
        if full_place.rating:
            stars = "⭐" * int(round(full_place.rating))
            review_text = f" ({full_place.user_ratings_total} reviews)" if full_place.user_ratings_total else ""
            details += f"{stars} [bold]{full_place.rating}[/bold] stars{review_text}\n"
        
        # Address
        if full_place.address:
            details += f"📍 {full_place.address}\n"
        
        # Phone
        if full_place.phone_number:
            details += f"📞 {full_place.phone_number}\n"
        
        # Hours
        if full_place.opening_hours:
            status = "[green]Open now[/green]" if full_place.opening_hours.get('open_now') else "[red]Closed[/red]"
            details += f"🕐 {status}\n"
            
            # Show hours if available
            if 'weekday_text' in full_place.opening_hours:
                details += "\n[bold]Hours:[/bold]\n"
                for day_hours in full_place.opening_hours['weekday_text']:
                    details += f"  {day_hours}\n"
        
        # Price level
        if full_place.price_level is not None:
            details += f"💰 {full_place.get_price_string()}\n"
        
        # Website
        if full_place.website:
            details += f"🌐 {full_place.website}\n"
        
        console.print(Panel(details, border_style="cyan"))
        
        # Action menu
        console.print("\n[bold]Actions:[/bold]")
        console.print("  1. Open in Google Maps")
        console.print("  2. Save to notes")
        console.print("  3. Back to results")
        
        choice = Prompt.ask("Select action", choices=["1", "2", "3"], default="3")
        
        if choice == "1":
            import webbrowser
            maps_url = full_place.get_google_maps_url()
            console.print(f"\n[cyan]Opening in Google Maps...[/cyan]\n")
            webbrowser.open(maps_url)
        
        elif choice == "2":
            # Save to notes
            note_text = f"**{full_place.name}**\n"
            if full_place.rating:
                note_text += f"Rating: {full_place.rating} ⭐\n"
            if full_place.address:
                note_text += f"Address: {full_place.address}\n"
            if full_place.phone_number:
                note_text += f"Phone: {full_place.phone_number}\n"
            if full_place.website:
                note_text += f"Website: {full_place.website}\n"
            note_text += f"Maps: {full_place.get_google_maps_url()}\n"
            
            storage.add_note_to_journal(note_text)
            console.print(f"\n[green]✓ Saved to notes![/green]\n")
        
        else:
            console.print()
    
    def _get_project_last_activity(self, project_id: str) -> datetime:
        """Get the timestamp of the most recent activity for a project."""
        from projects import project_manager
        
        latest = datetime.min
        
        # Check tasks
        tasks = storage.load_tasks()
        project_tasks = [t for t in tasks if t.project_id == project_id]
        if project_tasks:
            task_dates = [t.updated_at for t in project_tasks if t.updated_at]
            if task_dates:
                latest = max(latest, max(task_dates))
        
        # Check notes
        project_notes = project_manager.get_project_notes(project_id)
        if project_notes:
            # Notes have date strings, convert them
            for note in project_notes:
                try:
                    note_date = datetime.strptime(note['date'], "%Y-%m-%d")
                    latest = max(latest, note_date)
                except:
                    pass
        
        return latest
    
    def cmd_projects(self, args: str):
        """Display all projects with interactive selection."""
        from projects import project_manager
        
        console.print()
        
        projects = storage.load_projects()
        
        if not projects:
            console.print("[dim]No projects yet. Projects will be suggested when you add tasks.[/dim]")
            console.print("[dim]Try adding a task with: /add <task description>[/dim]\n")
            return
        
        # Sort projects by most recent activity
        projects_with_activity = []
        for project in projects:
            last_activity = self._get_project_last_activity(project.id)
            projects_with_activity.append((project, last_activity))
        
        # Sort by activity (most recent first)
        projects_with_activity.sort(key=lambda x: x[1], reverse=True)
        projects = [p[0] for p in projects_with_activity]
        
        console.print("[bold blue]📁 Select a Project[/bold blue]")
        console.print("[dim]Use ↑/↓ arrows to navigate, Enter to open, Esc to cancel[/dim]\n")
        
        # Create options list with task counts
        options = []
        for project in projects:
            project_tasks = [t for t in storage.load_tasks() if t.project_id == project.id and not t.completed]
            task_count = len(project_tasks)
            
            # Get note count
            project_notes = project_manager.get_project_notes(project.id)
            note_count = len(project_notes)
            
            option_text = f"{project.name}"
            if task_count > 0 or note_count > 0:
                counts = []
                if task_count > 0:
                    counts.append(f"{task_count} task{'s' if task_count != 1 else ''}")
                if note_count > 0:
                    counts.append(f"{note_count} note{'s' if note_count != 1 else ''}")
                option_text += f" ({', '.join(counts)})"
            
            options.append(option_text)
        
        # Use pick library for arrow key navigation
        try:
            from pick import pick
            
            title = ""
            try:
                selected_option, selected_index = pick(options, title, indicator="→")
                
                if selected_index is not None:
                    selected_project = projects[selected_index]
                    self._open_project_view(selected_project)
            except (KeyboardInterrupt, EOFError):
                # User pressed Esc or Ctrl+C to cancel
                console.print("\n[dim]Cancelled.[/dim]\n")
                return
        except ImportError:
            # Fallback: numbered list
            console.print("[yellow]Install 'pick' for arrow key navigation: pip install pick[/yellow]")
            console.print("[dim]Using numbered selection instead...[/dim]\n")
            
            for i, (project, option_text) in enumerate(zip(projects, options), 1):
                console.print(f"  {i}. {option_text}")
            
            console.print()
            choice = Prompt.ask("Select project number (or press Enter to cancel)")
            
            if choice.strip():
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(projects):
                        self._open_project_view(projects[idx])
                except ValueError:
                    console.print("[red]Invalid selection[/red]\n")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]\n")
    
    def _open_project_view(self, project):
        """Open the project view in browser."""
        import webbrowser
        
        console.print()
        console.print(f"[cyan]Opening project: {project.name}...[/cyan]")
        console.print("[dim]Make sure the web app is running: cd web && npm run dev[/dim]\n")
        
        webbrowser.open(f'http://localhost:5173/projects/{project.id}')
        console.print(f"[green]✓ Opened {project.name}[/green]\n")
    
    def cmd_tracker(self, args: str):
        """View tracker history."""
        from trackers import sleep_tracker
        
        console.print()
        
        tracker_name = args.strip().lower() if args.strip() else "sleep"
        
        if tracker_name == "sleep":
            sleep_tracker.display_history(days=14)
        else:
            console.print(f"[red]Unknown tracker: {tracker_name}[/red]")
            console.print("[dim]Available trackers: sleep[/dim]\n")
    
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
        
        # Show current configuration
        current_anthropic = config.get_api_key()
        current_google_key = config.get_google_search_key()
        current_google_cx = config.get_google_search_cx()
        
        console.print("[bold]Current Configuration:[/bold]")
        if current_anthropic:
            masked = current_anthropic[:8] + "..." + current_anthropic[-4:]
            console.print(f"  Anthropic API: {masked}")
        else:
            console.print(f"  Anthropic API: [yellow]Not configured[/yellow]")
        
        if current_google_key and current_google_cx:
            masked_key = current_google_key[:8] + "..." + current_google_key[-4:]
            console.print(f"  Google Search: {masked_key} [green]✓[/green]")
        else:
            console.print(f"  Google Search: [yellow]Not configured[/yellow] (recommended)")
        
        console.print("\n[bold]What would you like to configure?[/bold]")
        console.print("  1. Anthropic API key (required)")
        console.print("  2. Google Search (for /search web - 100 free searches/day)")
        console.print("  3. Exit")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="3")
        
        if choice == "1":
            console.print("\n[dim]Get your API key from: https://console.anthropic.com/[/dim]")
            new_key = Prompt.ask("Enter your Anthropic API key")
            if new_key:
                config.set_api_key(new_key)
                console.print("\n[green]✓ Anthropic API key saved![/green]\n")
        
        elif choice == "2":
            console.print("\n[dim]See GOOGLE_SEARCH_SETUP.md for setup instructions[/dim]")
            console.print("[dim]Get API key from: https://console.cloud.google.com/[/dim]")
            console.print("[dim]Create search engine at: https://programmablesearchengine.google.com/[/dim]\n")
            
            new_key = Prompt.ask("Enter your Google Search API key (or press Enter to skip)", default="")
            if new_key:
                new_cx = Prompt.ask("Enter your Google Search CX ID")
                if new_cx:
                    config.set_google_search_key(new_key)
                    config.set_google_search_cx(new_cx)
                    console.print("\n[green]✓ Google Search configured![/green]")
                    console.print("[dim]Now /search web will use Google instead of DuckDuckGo[/dim]\n")
        
        else:
            console.print()
    
    def cmd_help(self, args: str):
        """Show help information."""
        console.print()
        help_text = """
# Focus Assistant Commands

## Daily Routines
- `/morning` - Complete morning flow (sleep tracking, 750-word daily pages, intention)
- `/intention` - View today's intention and priorities
- `/evening` - Reflect on your day with evening routine
- `/today` - Show today's plan and main goal

## Task Management
- `/tasks` - View your task board (today, upcoming, inbox)
- `/tasks gui` - Open tasks in a web GUI with checkboxes
- `/add <task>` - Add a new task
- `/done` - Mark a task as complete
- `/stats` - Show productivity statistics

## Tracking & Logs
- `/tracker <name>` - View tracker history (e.g., `/tracker sleep`)
- `/log [date]` - View your daily log (intention, pages, tasks, notes)

## Calendar (if configured)
- `/calendar [today|tomorrow|weekend|week]` - View calendar events (interactive mode)
- `/schedule <description>` - Create a calendar event (e.g., "team meeting tomorrow at 2pm")
- `focus calendar [range]` / `focus schedule "<event>"` - Same commands from the CLI

## Email & Inbox (if configured)
- `/email inbox [count]` - View unread Gmail messages
- `/email read <index|id>` - Read a specific email
- `/email reply <index|id>` - Draft & send a reply with AI
- `/email cleanup [query]` - Newsletter cleanup or stage a Gmail search (max 25)
- `/email archive <index|id...>` - Archive specific emails (add --delete to trash)

## Search & Projects
- `/search web <query> [results:N]` - Search DuckDuckGo (default 10 results, max 25)
- `/search history <query>` - Search your notes, tasks, and projects semantically
- `/places <query>` - Find nearby places (cafes, restaurants, bars, etc.)
- `/projects` - View all your projects (use arrows to navigate)

## Notes & Writing
- `/note` - Create a quick inline note (no LLM response)
- `/write` - Write a markdown note with live preview (opens in browser)

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
- "/search web python tutorials results:5" → search the web
- "/search history things to read" → find all reading-related notes
- "/places cafe nearby" → find nearby cafes with ratings and hours
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
