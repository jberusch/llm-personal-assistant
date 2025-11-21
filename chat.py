"""Interactive chat interface with task integration."""

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text

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
        console.print("[dim]Type '/search [query]' for semantic search, 'tasks' to view your task board, 'quit' or 'exit' to end.[/dim]\n")
        
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
                
                # Check for search command
                if user_input.lower().startswith('/search'):
                    query = user_input[7:].strip()  # Remove '/search' prefix
                    if query:
                        self._handle_search(query)
                    else:
                        console.print("[yellow]Usage: /search [your query][/yellow]")
                        console.print("[dim]Example: /search things I should read[/dim]\n")
                    continue
                
                # Check for projects command
                if user_input.lower() in ['/projects']:
                    self._show_projects()
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
            
            # Suggest projects
            self._suggest_project_for_task(task)
            
            # Refresh assistant context
            self.assistant.refresh_context()
        else:
            console.print("[dim]Task not added. Continuing conversation...[/dim]")
        
        console.print()
    
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
- `/search [query]` - Search your notes and tasks semantically
- `/projects` - View all your projects
- `tasks` - View your task board
- `quit` or `exit` - End the chat session
- `help` - Show this help message

**Tips:**
- Just chat naturally - I'll help you think through priorities
- Say things like "remind me tomorrow to..." to create tasks
- Use `/search` to find everything you've written about a topic
- Ask "what should I focus on?" for suggestions based on your morning goals
- I remember your morning reflection and current context
"""
        console.print(Panel(Markdown(help_text), title="Help", border_style="cyan"))
        console.print()
    
    def _handle_search(self, query: str):
        """Handle semantic search command."""
        try:
            from embeddings import get_embeddings_manager
            
            console.print()
            with console.status(f"[cyan]Searching for: {query}...[/cyan]"):
                embeddings_mgr = get_embeddings_manager()
                
                if not embeddings_mgr:
                    console.print("[yellow]Semantic search not available. Please configure your OpenAI API key:[/yellow]")
                    console.print("  [cyan]./focus config --openai-key YOUR_KEY[/cyan]\n")
                    return
                
                # Search with a relevance threshold of 0.65 (fairly strict)
                results, stats = embeddings_mgr.search(
                    query,
                    top_k=15,
                    distance_threshold=0.65,
                    return_stats=True
                )
            
            fallback_used = stats.get("used_fallback")
            best_distance = stats.get("best_distance")
            fallback_threshold = stats.get("fallback_threshold")
            
            if not results:
                console.print(f"[yellow]No results found for '{query}'[/yellow]")
                if best_distance is not None:
                    console.print(
                        f"[dim]Closest match distance was {best_distance:.3f} "
                        f"(threshold {fallback_threshold:.2f}). Try a broader query.[/dim]\n"
                    )
                else:
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
            
            console.print(f"[bold cyan]🔍 Search Results for: {query}[/bold cyan]\n")
            
            # Display journal entries
            if journals:
                console.print("[bold yellow]📔 Journal Entries[/bold yellow]")
                for result in journals[:8]:  # Limit to top 8 journals
                    date = result.metadata.get('date', 'Unknown')
                    section = result.metadata.get('section', 'Unknown')
                    entry_type = result.metadata.get('type', 'journal')
                    
                    # Truncate content if too long
                    content = result.content
                    if len(content) > 200:
                        content = content[:200] + "..."
                    
                    console.print(f"\n[cyan]{date}[/cyan] • [dim]{section} ({entry_type})[/dim]")
                    console.print(f"[white]{content}[/white]")
                
                console.print()
            
            # Display tasks
            if tasks:
                console.print("[bold green]✓ Tasks[/bold green]")
                for result in tasks[:5]:  # Limit to top 5 tasks
                    status = result.metadata.get('status', 'unknown')
                    completed = result.metadata.get('completed', False)
                    
                    status_icon = "✓" if completed else "○"
                    status_color = "dim" if completed else "white"
                    
                    console.print(f"\n{status_icon} [{status_color}]{result.content}[/{status_color}]")
                    console.print(f"[dim]  Status: {status}[/dim]")
                
                console.print()
            
            # Display projects
            if projects:
                console.print("[bold blue]📁 Projects[/bold blue]")
                for result in projects:
                    name = result.metadata.get('name', 'Unknown')
                    console.print(f"\n[blue]• {name}[/blue]")
                    console.print(f"[white]{result.content}[/white]")
                
                console.print()
            
            console.print(f"[dim]Found {len(results)} total results[/dim]\n")
            
        except Exception as e:
            console.print(f"[red]Error during search: {e}[/red]\n")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    def _show_projects(self):
        """Display all projects."""
        console.print()
        
        projects = storage.load_projects()
        
        if not projects:
            console.print("[dim]No projects yet. Projects will be suggested when you add tasks.[/dim]\n")
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
    
    def _exit_chat(self):
        """Exit the chat session."""
        console.print("\n[cyan]Chat session ended. Your conversation has been saved.[/cyan]")
        console.print("[dim]Use 'focus chat' to continue later.[/dim]\n")
        self.running = False


# Global chat instance
chat = ChatInterface()

