#!/usr/bin/env python3
"""Migrate JSON journals to Markdown format."""

import json
import shutil
from pathlib import Path
from datetime import datetime
from storage import storage
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def migrate_journals():
    """Convert all JSON journals to Markdown format."""
    journal_dir = storage.journal_dir
    json_files = list(journal_dir.glob("*.json"))
    
    if not json_files:
        console.print("[yellow]No JSON journal files found to migrate.[/yellow]")
        return
    
    console.print(f"\n[cyan]Found {len(json_files)} JSON journal file(s) to migrate.[/cyan]\n")
    
    # Create archive directory
    archive_dir = journal_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    migrated = 0
    errors = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Migrating journals...", total=len(json_files))
        
        for json_file in json_files:
            try:
                # Load JSON data
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Extract date from filename
                date_str = json_file.stem  # YYYY-MM-DD
                date = datetime.strptime(date_str, "%Y-%m-%d")
                
                # Save as markdown using storage layer
                storage.save_journal(data, date)
                
                # Move JSON to archive
                archive_file = archive_dir / json_file.name
                shutil.move(str(json_file), str(archive_file))
                
                migrated += 1
                progress.update(task, advance=1, description=f"Migrated {json_file.name}")
                
            except Exception as e:
                errors.append((json_file.name, str(e)))
                progress.update(task, advance=1, description=f"Error with {json_file.name}")
    
    # Print summary
    console.print(f"\n[bold green]✓ Migration complete![/bold green]")
    console.print(f"  Migrated: {migrated} file(s)")
    console.print(f"  Archived: {archive_dir}")
    
    if errors:
        console.print(f"\n[yellow]Errors encountered:[/yellow]")
        for filename, error in errors:
            console.print(f"  • {filename}: {error}")
    
    # Verify markdown files
    md_files = list(journal_dir.glob("*.md"))
    console.print(f"\n[cyan]Markdown journal files: {len(md_files)}[/cyan]")
    
    if md_files:
        console.print("\n[dim]Sample locations:[/dim]")
        for md_file in md_files[:3]:
            console.print(f"  • {md_file}")
        if len(md_files) > 3:
            console.print(f"  • ... and {len(md_files) - 3} more")


def verify_migration():
    """Verify that journals can be read back correctly."""
    console.print("\n[cyan]Verifying migration...[/cyan]")
    
    journal_dir = storage.journal_dir
    md_files = list(journal_dir.glob("*.md"))
    
    if not md_files:
        console.print("[yellow]No markdown files to verify.[/yellow]")
        return
    
    verified = 0
    errors = []
    
    for md_file in md_files:
        try:
            # Try to parse the markdown file
            date_str = md_file.stem
            date = datetime.strptime(date_str, "%Y-%m-%d")
            journal = storage.load_journal(date)
            
            # Basic validation
            assert "date" in journal
            assert "morning" in journal or "evening" in journal or "chat_history" in journal
            
            verified += 1
        except Exception as e:
            errors.append((md_file.name, str(e)))
    
    console.print(f"  Verified: {verified}/{len(md_files)} file(s)")
    
    if errors:
        console.print(f"\n[yellow]Verification errors:[/yellow]")
        for filename, error in errors:
            console.print(f"  • {filename}: {error}")
    else:
        console.print("[green]  All files verified successfully![/green]")


if __name__ == "__main__":
    console.print("[bold cyan]📝 Journal Migration to Markdown[/bold cyan]")
    console.print("[dim]This will convert your JSON journals to Obsidian-ready Markdown format.[/dim]")
    
    migrate_journals()
    verify_migration()
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Your journals are now in Markdown format")
    console.print("  2. Original JSON files are in journal/archive/")
    console.print("  3. You can now use the focus assistant normally")
    console.print("  4. To use with Obsidian: symlink ~/.focus_assistant/journal/ to your vault")
    console.print("\n[green]Migration complete! 🎉[/green]\n")

