#!/usr/bin/env python3
"""
Focus Assistant - Your personal productivity coach.

A CLI tool to help you plan your day, manage tasks, and stay focused.
"""

import sys
import warnings

# Suppress urllib3 OpenSSL warning (doesn't affect functionality)
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')
warnings.filterwarnings(
    'ignore',
    category=FutureWarning,
    module='google\\.api_core\\._python_version_support'
)

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from config import config
from tasks import task_manager
from routines import morning_routine, evening_routine
from chat import chat
from storage import storage
from interactive import interactive_session

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0")
def cli(ctx):
    """Focus Assistant - Your personal productivity coach.
    
    Run without any command to start the interactive session.
    """
    # If no subcommand is provided, start interactive mode
    if ctx.invoked_subcommand is None:
        interactive_session.start()


@cli.command()
def morning():
    """Start your morning routine and plan the day."""
    try:
        morning_routine.run()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
def evening():
    """Reflect on your day with the evening routine."""
    try:
        evening_routine.run()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('task_text', required=False)
def add(task_text):
    """Add a new task with natural language.
    
    Examples:
        focus add "remind me tomorrow to pay rent"
        focus add "call mom next week"
        focus add "buy groceries"
    """
    if not task_text:
        task_text = Prompt.ask("What task would you like to add?")
    
    try:
        task = task_manager.add_task(task_text)
        console.print(f"\n[green]✓ Task added:[/green] {task.text}")
        if task.due_date:
            console.print(f"[green]  Due:[/green] {task.due_date.strftime('%A, %B %d, %Y')}")
        
        # Suggest projects
        _suggest_project_for_task(task)
        
        console.print()
    except Exception as e:
        console.print(f"[red]Error adding task: {e}[/red]")


def _suggest_project_for_task(task):
    """Suggest projects for a newly created task (used by CLI)."""
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


@cli.command()
@click.argument('mode', required=False)
def tasks(mode):
    """View your task board.
    
    Examples:
        focus tasks        # Show tasks in terminal
        focus tasks gui    # Open tasks in web GUI
    """
    # Check if GUI mode is requested
    if mode and mode.lower() == 'gui':
        import webbrowser
        import threading
        
        try:
            from note_editor import start_tasks_gui
            
            console.print("\n[cyan]Opening tasks GUI...[/cyan]")
            console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")
            
            # Start GUI in a thread and open browser
            def open_browser():
                import time
                time.sleep(1)  # Wait for server to start
                webbrowser.open('http://localhost:5557')
            
            threading.Thread(target=open_browser, daemon=True).start()
            start_tasks_gui()
            
        except KeyboardInterrupt:
            console.print("\n[cyan]Tasks GUI closed.[/cyan]\n")
        except Exception as e:
            console.print(f"[red]Error starting tasks GUI: {e}[/red]")
        return
    
    console.print()
    
    # Create task board
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
        for task in upcoming_tasks[:10]:  # Show first 10
            due_str = task.due_date.strftime("%a, %b %d") if task.due_date else ""
            console.print(f"  • {task.text} [dim]({due_str})[/dim]")
        if len(upcoming_tasks) > 10:
            console.print(f"  [dim]... and {len(upcoming_tasks) - 10} more[/dim]")
        console.print()
    
    # Inbox
    if inbox_tasks:
        console.print("[bold cyan]📥 INBOX[/bold cyan]")
        for task in inbox_tasks[:5]:  # Show first 5
            console.print(f"  • {task.text}")
        if len(inbox_tasks) > 5:
            console.print(f"  [dim]... and {len(inbox_tasks) - 5} more[/dim]")
        console.print()
    
    if not (today_tasks or upcoming_tasks or inbox_tasks):
        console.print("[dim]No tasks yet. Add one with:[/dim]")
        console.print("[dim]  focus add \"your task\"[/dim]\n")
    
    # Show stats
    stats = task_manager.get_task_stats()
    console.print(f"[dim]Total: {stats['incomplete']} incomplete • {stats['completed_today']} completed today[/dim]\n")


@cli.command()
@click.argument('task_id', required=False)
def done(task_id):
    """Mark a task as complete."""
    if not task_id:
        # Show today's tasks and let user select
        today_tasks = task_manager.get_today_tasks()
        if not today_tasks:
            console.print("[yellow]No tasks for today![/yellow]")
            return
        
        console.print("\n[bold]Today's tasks:[/bold]")
        for i, task in enumerate(today_tasks, 1):
            console.print(f"  {i}. {task.text}")
        
        choice = Prompt.ask("\nWhich task did you complete? (number)")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(today_tasks):
                task_id = today_tasks[idx].id
            else:
                console.print("[red]Invalid choice[/red]")
                return
        except ValueError:
            console.print("[red]Invalid choice[/red]")
            return
    
    try:
        task = storage.get_task(task_id)
        if task:
            task_manager.complete_task(task_id)
            console.print(f"\n[green]✓ Completed:[/green] {task.text}\n")
        else:
            console.print("[red]Task not found[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('timeframe', default='today')
def calendar(timeframe):
    """View calendar events.
    
    Examples:
        focus calendar            # Show today's events
        focus calendar today      # Show today's events
        focus calendar tomorrow   # Show tomorrow's events
        focus calendar weekend    # Show this weekend
        focus calendar week       # Show this week
    """
    try:
        from google_integration import google_integration
        
        if (not google_integration) or (not google_integration.is_configured()):
            console.print("\n[yellow]⚠️  Google Calendar not configured yet[/yellow]")
            console.print("[dim]See GOOGLE_CALENDAR_SETUP.md for setup instructions[/dim]\n")
            return
        
        timeframe = timeframe.lower().strip()
        
        if timeframe in ['today', '']:
            events = google_integration.get_events_today()
            title = "📅 Today's Calendar"
        elif timeframe == 'tomorrow':
            events = google_integration.get_events_tomorrow()
            title = "📅 Tomorrow's Calendar"
        elif timeframe in ['weekend', 'this_weekend']:
            events = google_integration.get_weekend_events()
            title = "📅 This Weekend"
        elif timeframe in ['week', 'this_week']:
            events = google_integration.get_events_this_week()
            title = "📅 This Week"
        else:
            console.print("[yellow]Usage: focus calendar [today|tomorrow|weekend|week][/yellow]\n")
            return
        
        formatted = google_integration.format_events_for_display(events)
        console.print()
        console.print(Panel(formatted, title=title, border_style="cyan"))
        console.print()
        
    except ImportError:
        console.print("\n[yellow]⚠️  Google Calendar not configured yet[/yellow]")
        console.print("[dim]See GOOGLE_CALENDAR_SETUP.md for setup instructions[/dim]\n")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]\n")


@cli.command()
@click.argument('event_description', nargs=-1)
def schedule(event_description):
    """Create a calendar event using natural language.
    
    Examples:
        focus schedule "Team meeting tomorrow at 2pm"
        focus schedule "Dentist appointment Friday at 10am"
        focus schedule "Lunch with Sarah next Tuesday at noon"
    """
    if not event_description:
        console.print("\n[yellow]Usage: focus schedule \"<event description>\"[/yellow]")
        console.print("[dim]Example: focus schedule \"Team meeting tomorrow at 2pm\"[/dim]\n")
        return
    
    try:
        from google_integration import google_integration
        from assistant import Assistant
        from datetime import timedelta
        from dateutil.parser import parse as parse_date
        import json
        
        if (not google_integration) or (not google_integration.is_configured()):
            console.print("\n[yellow]⚠️  Google Calendar not configured yet[/yellow]")
            console.print("[dim]See GOOGLE_CALENDAR_SETUP.md for setup instructions[/dim]\n")
            return
        
        event_text = ' '.join(event_description)
        console.print(f"\n[cyan]Creating calendar event...[/cyan]")
        
        # Use the assistant to parse the event details
        assistant = Assistant()
        prompt = f"""The user wants to create a calendar event. Parse this into structured data:

"{event_text}"

Return ONLY a JSON object with these fields:
{{
    "summary": "event title",
    "start_time": "YYYY-MM-DD HH:MM",
    "duration_hours": 1.0,
    "description": "optional description"
}}

Use 24-hour format. If no time is specified, use 09:00. If no date, use tomorrow."""
        
        response = assistant.ask_question(prompt)
        
        # Extract JSON from response
        if '```json' in response:
            json_str = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            json_str = response.split('```')[1].split('```')[0].strip()
        else:
            json_str = response.strip()
        
        event_data = json.loads(json_str)
        
        # Parse start time
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
            console.print()
        else:
            console.print("[red]Failed to create event[/red]\n")
    
    except ImportError:
        console.print("\n[yellow]⚠️  Google Calendar not configured yet[/yellow]")
        console.print("[dim]See GOOGLE_CALENDAR_SETUP.md for setup instructions[/dim]\n")
    except Exception as e:
        console.print(f"[red]Error creating event: {e}[/red]\n")


@cli.command()
def chat_cmd():
    """Start an interactive chat session."""
    try:
        chat.start()
    except KeyboardInterrupt:
        console.print("\n[cyan]Chat ended.[/cyan]\n")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# Alias 'chat' command since 'chat' is a reserved name in click
cli.add_command(chat_cmd, name='chat')


@cli.command()
@click.option('--key', '--anthropic-key', help='Your Anthropic API key')
@click.option('--openai-key', help='Your OpenAI API key (for embeddings)')
@click.option('--google-search-key', help='Your Google Search API key')
@click.option('--google-search-cx', help='Your Google Custom Search Engine ID')
def config_cmd(key, openai_key, google_search_key, google_search_cx):
    """Configure the assistant (API keys, etc.)."""
    if key:
        config.set_api_key(key)
        console.print("[green]✓ Anthropic API key saved![/green]")
    
    if openai_key:
        config.set_openai_key(openai_key)
        console.print("[green]✓ OpenAI API key saved![/green]")
    
    if google_search_key:
        config.set_google_search_key(google_search_key)
        console.print("[green]✓ Google Search API key saved![/green]")
    
    if google_search_cx:
        config.set_google_search_cx(google_search_cx)
        console.print("[green]✓ Google Search CX ID saved![/green]")
    
    if key or openai_key or google_search_key or google_search_cx:
        return
    
    # Interactive configuration
    console.print("\n[bold cyan]Configuration[/bold cyan]\n")
    
    # Anthropic API Key
    current_anthropic = config.get_api_key()
    if current_anthropic:
        masked_key = current_anthropic[:8] + "..." + current_anthropic[-4:]
        console.print(f"Anthropic API key: {masked_key}")
        change = Prompt.ask("Change Anthropic API key?", choices=["y", "n"], default="n")
        if change == "y":
            console.print("\n[dim]Get your API key from: https://console.anthropic.com/[/dim]")
            new_key = Prompt.ask("Enter your Anthropic API key")
            if new_key:
                config.set_api_key(new_key)
                console.print("[green]✓ Anthropic API key saved![/green]")
    else:
        console.print("[yellow]No Anthropic API key configured[/yellow]")
        console.print("\n[dim]Get your API key from: https://console.anthropic.com/[/dim]")
        new_key = Prompt.ask("Enter your Anthropic API key", default="")
        if new_key:
            config.set_api_key(new_key)
            console.print("[green]✓ Anthropic API key saved![/green]")
    
    console.print()
    
    # OpenAI API Key
    current_openai = config.get_openai_key()
    if current_openai:
        masked_key = current_openai[:8] + "..." + current_openai[-4:]
        console.print(f"OpenAI API key: {masked_key}")
        change = Prompt.ask("Change OpenAI API key?", choices=["y", "n"], default="n")
        if change == "y":
            console.print("\n[dim]Get your API key from: https://platform.openai.com/api-keys[/dim]")
            new_key = Prompt.ask("Enter your OpenAI API key")
            if new_key:
                config.set_openai_key(new_key)
                console.print("[green]✓ OpenAI API key saved![/green]")
    else:
        console.print("[yellow]No OpenAI API key configured (needed for semantic search)[/yellow]")
        console.print("\n[dim]Get your API key from: https://platform.openai.com/api-keys[/dim]")
        new_key = Prompt.ask("Enter your OpenAI API key (or press Enter to skip)", default="")
        if new_key:
            config.set_openai_key(new_key)
            console.print("[green]✓ OpenAI API key saved![/green]")
    
    console.print()
    
    # Google Search API Key
    current_google = config.get_google_search_key()
    current_google_cx = config.get_google_search_cx()
    
    if current_google and current_google_cx:
        masked_key = current_google[:8] + "..." + current_google[-4:]
        masked_cx = current_google_cx[:8] + "..." if len(current_google_cx) > 12 else current_google_cx
        console.print(f"Google Search API key: {masked_key}")
        console.print(f"Google Search CX ID: {masked_cx}")
        change = Prompt.ask("Change Google Search credentials?", choices=["y", "n"], default="n")
        if change == "y":
            console.print("\n[dim]See GOOGLE_SEARCH_SETUP.md for instructions[/dim]")
            new_key = Prompt.ask("Enter your Google Search API key")
            new_cx = Prompt.ask("Enter your Google Search CX ID")
            if new_key and new_cx:
                config.set_google_search_key(new_key)
                config.set_google_search_cx(new_cx)
                console.print("[green]✓ Google Search credentials saved![/green]")
    else:
        console.print("[yellow]No Google Search configured (recommended for /search web)[/yellow]")
        console.print("[dim]Google Search has 100 free searches/day (much better than DuckDuckGo)[/dim]")
        setup = Prompt.ask("Set up Google Search now?", choices=["y", "n"], default="n")
        if setup == "y":
            console.print("\n[dim]See GOOGLE_SEARCH_SETUP.md for detailed setup instructions[/dim]")
            new_key = Prompt.ask("Enter your Google Search API key (or press Enter to skip)", default="")
            if new_key:
                new_cx = Prompt.ask("Enter your Google Search CX ID")
                if new_cx:
                    config.set_google_search_key(new_key)
                    config.set_google_search_cx(new_cx)
                    console.print("[green]✓ Google Search credentials saved![/green]")
    
    console.print()


cli.add_command(config_cmd, name='config')


@cli.command()
@click.argument('target', type=click.Choice(['obsidian']), required=False, default='obsidian')
@click.option(
    '--include-completed',
    is_flag=True,
    help='Include a recently-completed section in the export.',
)
def export(target, include_completed):
    """Export data for use in other tools (currently Obsidian tasks)."""
    if target == 'obsidian':
        from obsidian_export import export_tasks_to_markdown

        output_path = export_tasks_to_markdown(include_completed=include_completed)
        console.print(
            f"\n[green]✓ Exported tasks to Obsidian markdown:[/green] {output_path}\n"
        )


@cli.command()
def stats():
    """Show statistics about your tasks and productivity."""
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


@cli.command()
def index():
    """Index all existing data for semantic search.
    
    This command generates embeddings for all your journals and tasks,
    enabling semantic search with the /search command.
    
    Run this once after setting up your OpenAI API key.
    """
    try:
        from embeddings import EmbeddingsManager
        
        # Check for OpenAI API key
        if not config.get_openai_key():
            console.print("\n[red]Error: OpenAI API key not configured.[/red]")
            console.print("\nTo set your OpenAI API key, run:")
            console.print("  [cyan]./focus config --openai-key YOUR_KEY[/cyan]")
            console.print("\nOr set the OPENAI_API_KEY environment variable.")
            console.print("\n[dim]Get your API key from: https://platform.openai.com/api-keys[/dim]\n")
            return
        
        # Initialize embeddings manager and index data
        embeddings_mgr = EmbeddingsManager()
        embeddings_mgr.index_all_existing_data()
        
    except Exception as e:
        console.print(f"\n[red]Error during indexing: {e}[/red]\n")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


@cli.command(name='log')
@click.argument('date', required=False)
def log(date):
    """Open today's journal in a web editor.
    
    Examples:
        focus log              # Open today's journal
        focus log today        # Open today's journal
        focus log 2025-11-20   # Open specific date
    """
    from datetime import datetime
    import webbrowser
    import threading
    
    # Parse the date argument
    target_date = None
    if not date or date.lower() == 'today':
        target_date = datetime.now()
    else:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]Invalid date format. Use YYYY-MM-DD (e.g., 2025-11-20)[/red]")
            return
    
    # Import and start the editor
    try:
        from note_editor import start_editor
        
        console.print(f"\n[cyan]Opening journal editor for {target_date.strftime('%Y-%m-%d')}...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")
        
        # Start editor in a thread and open browser
        def open_browser():
            import time
            time.sleep(1)  # Wait for server to start
            webbrowser.open('http://localhost:5555')
        
        threading.Thread(target=open_browser, daemon=True).start()
        start_editor(target_date)
        
    except KeyboardInterrupt:
        console.print("\n[cyan]Editor closed.[/cyan]\n")
    except Exception as e:
        console.print(f"[red]Error starting editor: {e}[/red]")


if __name__ == '__main__':
    cli()

