#!/usr/bin/env python3
"""
Focus Assistant - Your personal productivity coach.

A CLI tool to help you plan your day, manage tasks, and stay focused.
"""

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

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Focus Assistant - Your personal productivity coach."""
    pass


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
        console.print()
    except Exception as e:
        console.print(f"[red]Error adding task: {e}[/red]")


@cli.command()
def tasks():
    """View your task board."""
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
@click.option('--key', help='Your Anthropic API key')
def config_cmd(key):
    """Configure the assistant (API key, etc.)."""
    if key:
        config.set_api_key(key)
        console.print("[green]✓ API key saved![/green]")
        return
    
    # Interactive configuration
    console.print("\n[bold cyan]Configuration[/bold cyan]\n")
    
    current_key = config.get_api_key()
    if current_key:
        masked_key = current_key[:8] + "..." + current_key[-4:]
        console.print(f"Current API key: {masked_key}")
        change = Prompt.ask("Change API key?", choices=["y", "n"], default="n")
        if change == "n":
            return
    
    console.print("\n[dim]Get your API key from: https://console.anthropic.com/[/dim]")
    new_key = Prompt.ask("Enter your Anthropic API key")
    
    if new_key:
        config.set_api_key(new_key)
        console.print("\n[green]✓ API key saved![/green]\n")
    else:
        console.print("[yellow]No changes made.[/yellow]")


cli.add_command(config_cmd, name='config')


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


if __name__ == '__main__':
    cli()

