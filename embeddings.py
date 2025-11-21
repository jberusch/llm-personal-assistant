"""Embeddings and semantic search using OpenAI and ChromaDB."""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import config
from storage import storage, Task, Project

console = Console()


@dataclass
class SearchResult:
    """Result from semantic search."""
    content: str
    metadata: Dict[str, Any]
    distance: float
    result_type: str  # 'journal', 'task', 'project'


class EmbeddingsManager:
    """Manages embeddings generation and semantic search."""
    
    def __init__(self):
        """Initialize OpenAI client and ChromaDB."""
        self.openai_key = config.get_openai_key()
        if not self.openai_key:
            raise ValueError(
                "OpenAI API key not found. Please set it using:\n"
                "  ./focus config --openai-key YOUR_KEY\n"
                "Or set the OPENAI_API_KEY environment variable."
            )
        
        self.client = OpenAI(api_key=self.openai_key)
        self.embedding_model = "text-embedding-3-small"
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(config.embeddings_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collections
        self.journal_collection = self.chroma_client.get_or_create_collection(
            name="journal_entries",
            metadata={"description": "Journal entries with embeddings"}
        )
        
        self.task_collection = self.chroma_client.get_or_create_collection(
            name="tasks",
            metadata={"description": "Task embeddings"}
        )
        
        self.project_collection = self.chroma_client.get_or_create_collection(
            name="projects",
            metadata={"description": "Project embeddings"}
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API."""
        if not text.strip():
            # Return zero vector for empty text
            return [0.0] * 1536
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            console.print(f"[red]Error generating embedding: {e}[/red]")
            raise
    
    def embed_journal_entry(self, date: str, section: str, content: str, entry_type: str = "journal"):
        """Embed a journal entry section."""
        if not content or not content.strip():
            return
        
        # Generate unique ID
        doc_id = f"{date}_{section}"
        
        # Generate embedding
        embedding = self.generate_embedding(content)
        
        # Store in ChromaDB
        self.journal_collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "date": date,
                "section": section,
                "type": entry_type,
                "indexed_at": datetime.now().isoformat()
            }]
        )
    
    def embed_task(self, task: Task):
        """Embed a task with its text and metadata."""
        if not task.text or not task.text.strip():
            return
        
        # Create rich text representation
        task_text = task.text
        if task.due_date:
            task_text += f" (due: {task.due_date.strftime('%Y-%m-%d')})"
        
        # Generate embedding
        embedding = self.generate_embedding(task_text)
        
        # Prepare metadata
        metadata = {
            "task_id": task.id,
            "status": task.status,
            "completed": task.completed,
            "created_at": task.created_at.isoformat(),
            "indexed_at": datetime.now().isoformat()
        }
        
        if task.due_date:
            metadata["due_date"] = task.due_date.isoformat()
        
        if task.project_id:
            metadata["project_id"] = task.project_id
        
        # Store in ChromaDB
        self.task_collection.upsert(
            ids=[task.id],
            embeddings=[embedding],
            documents=[task_text],
            metadatas=[metadata]
        )
    
    def embed_project(self, project: Project):
        """Embed a project with name and description."""
        # Create rich text representation
        project_text = f"{project.name}: {project.description}"
        
        # Generate embedding
        embedding = self.generate_embedding(project_text)
        
        # Store in ChromaDB
        self.project_collection.upsert(
            ids=[project.id],
            embeddings=[embedding],
            documents=[project_text],
            metadatas=[{
                "project_id": project.id,
                "name": project.name,
                "created_at": project.created_at.isoformat(),
                "indexed_at": datetime.now().isoformat()
            }]
        )
    
    def search(self, query: str, top_k: int = 10, distance_threshold: float = 0.7) -> List[SearchResult]:
        """
        Perform semantic search across all collections.
        
        Args:
            query: Search query text
            top_k: Maximum number of results to return
            distance_threshold: Maximum distance to consider (lower = more strict)
                               0.0 = perfect match, 1.0 = completely different
                               Recommended: 0.6-0.8 for good quality results
        """
        if not query.strip():
            return []
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search across all collections
        results = []
        
        # Search journals
        try:
            journal_count = self.journal_collection.count()
            if journal_count > 0:
                journal_results = self.journal_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, journal_count)
                )
                
                if journal_results['documents'] and journal_results['documents'][0]:
                    for i, doc in enumerate(journal_results['documents'][0]):
                        results.append(SearchResult(
                            content=doc,
                            metadata=journal_results['metadatas'][0][i],
                            distance=journal_results['distances'][0][i] if 'distances' in journal_results else 0.0,
                            result_type='journal'
                        ))
        except Exception as e:
            console.print(f"[dim]Note: Error searching journals: {e}[/dim]")
        
        # Search tasks
        try:
            task_count = self.task_collection.count()
            if task_count > 0:
                task_results = self.task_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, task_count)
                )
                
                if task_results['documents'] and task_results['documents'][0]:
                    for i, doc in enumerate(task_results['documents'][0]):
                        results.append(SearchResult(
                            content=doc,
                            metadata=task_results['metadatas'][0][i],
                            distance=task_results['distances'][0][i] if 'distances' in task_results else 0.0,
                            result_type='task'
                        ))
        except Exception as e:
            console.print(f"[dim]Note: Error searching tasks: {e}[/dim]")
        
        # Search projects
        try:
            project_count = self.project_collection.count()
            if project_count > 0:
                project_results = self.project_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, project_count)
                )
                
                if project_results['documents'] and project_results['documents'][0]:
                    for i, doc in enumerate(project_results['documents'][0]):
                        results.append(SearchResult(
                            content=doc,
                            metadata=project_results['metadatas'][0][i],
                            distance=project_results['distances'][0][i] if 'distances' in project_results else 0.0,
                            result_type='project'
                        ))
        except Exception as e:
            # Silently skip projects if there's an error
            pass
        
        # Filter by distance threshold (remove poor matches)
        results = [r for r in results if r.distance <= distance_threshold]
        
        # Sort by distance (lower is better)
        results.sort(key=lambda x: x.distance)
        
        # Return top_k results
        return results[:top_k]
    
    def index_all_existing_data(self):
        """Index all existing journals and tasks (one-time migration)."""
        console.print("\n[bold cyan]🔄 Indexing existing data...[/bold cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Index journals
            journal_task = progress.add_task("Indexing journal entries...", total=None)
            journal_count = 0
            
            # Get all journal files
            journal_files = sorted(config.journal_dir.glob("*.md"))
            
            for journal_file in journal_files:
                try:
                    date_str = journal_file.stem  # YYYY-MM-DD
                    
                    # Parse the journal file
                    with open(journal_file, 'r') as f:
                        content = f.read()
                    
                    # Parse journal data
                    journal_data = storage._parse_markdown_journal(content)
                    
                    # Index morning reflection
                    if journal_data.get("morning"):
                        morning_meta = journal_data["morning"].get("metadata", {})
                        responses = morning_meta.get("responses", {})
                        if responses:
                            # Combine all Q&As into one text
                            morning_text = "\n\n".join([
                                f"{q}\n{a}" for q, a in responses.items()
                            ])
                            self.embed_journal_entry(
                                date_str, "morning", morning_text, "morning"
                            )
                            journal_count += 1
                            console.print(f"[dim]  {date_str}: Indexed morning reflection[/dim]")
                    
                    # Index evening reflection
                    if journal_data.get("evening"):
                        evening_meta = journal_data["evening"].get("metadata", {})
                        responses = evening_meta.get("responses", {})
                        if responses:
                            evening_text = "\n\n".join([
                                f"{q}\n{a}" for q, a in responses.items()
                            ])
                            self.embed_journal_entry(
                                date_str, "evening", evening_text, "evening"
                            )
                            journal_count += 1
                            console.print(f"[dim]  {date_str}: Indexed evening reflection[/dim]")
                    
                    # Index chat history
                    chat_history = journal_data.get("chat_history", [])
                    chat_indexed = 0
                    for idx, entry in enumerate(chat_history):
                        role = entry.get("metadata", {}).get("role", "user")
                        message = entry.get("response", "")
                        if message and role == "user":  # Only index user messages
                            self.embed_journal_entry(
                                date_str, f"chat_{idx}", message, "chat"
                            )
                            journal_count += 1
                            chat_indexed += 1
                    if chat_indexed > 0:
                        console.print(f"[dim]  {date_str}: Indexed {chat_indexed} chat messages[/dim]")
                    
                    # Index notes
                    notes = journal_data.get("notes", [])
                    for idx, note in enumerate(notes):
                        content = note.get("content", "")
                        title = note.get("title", "")
                        if content:
                            # Combine title and content for better searchability
                            note_text = f"{title}\n{content}" if title else content
                            self.embed_journal_entry(
                                date_str, f"note_{idx}", note_text, "note"
                            )
                            journal_count += 1
                            truncated_title = title[:50] + "..." if len(title) > 50 else title
                            console.print(f"[dim]  {date_str}: Indexed note '{truncated_title}'[/dim]")
                
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not index {journal_file.name}: {e}[/yellow]")
            
            progress.update(journal_task, completed=True)
            console.print(f"[green]✓ Indexed {journal_count} journal entries[/green]")
            
            # Index tasks
            task_task = progress.add_task("Indexing tasks...", total=None)
            tasks = storage.load_tasks()
            
            for task in tasks:
                try:
                    self.embed_task(task)
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not index task {task.id}: {e}[/yellow]")
            
            progress.update(task_task, completed=True)
            console.print(f"[green]✓ Indexed {len(tasks)} tasks[/green]")
            
            # Index projects
            project_task = progress.add_task("Indexing projects...", total=None)
            projects = storage.load_projects()
            
            for project in projects:
                try:
                    self.embed_project(project)
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not index project {project.id}: {e}[/yellow]")
            
            progress.update(project_task, completed=True)
            console.print(f"[green]✓ Indexed {len(projects)} projects[/green]")
        
        console.print("\n[bold green]✅ Indexing complete![/bold green]\n")
    
    def remove_task_embedding(self, task_id: str):
        """Remove a task's embedding from the collection."""
        try:
            self.task_collection.delete(ids=[task_id])
        except Exception:
            pass  # Ignore if doesn't exist
    
    def remove_project_embedding(self, project_id: str):
        """Remove a project's embedding from the collection."""
        try:
            self.project_collection.delete(ids=[project_id])
        except Exception:
            pass  # Ignore if doesn't exist


# Global embeddings manager instance (lazy initialization)
_embeddings_manager = None

def get_embeddings_manager() -> Optional[EmbeddingsManager]:
    """Get or create the global embeddings manager instance."""
    global _embeddings_manager
    if _embeddings_manager is None:
        try:
            _embeddings_manager = EmbeddingsManager()
        except ValueError as e:
            # API key not configured
            return None
    return _embeddings_manager

