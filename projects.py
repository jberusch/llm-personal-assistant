"""Project management and suggestion system."""

from typing import List, Optional, Tuple
from datetime import datetime

from storage import storage, Project
from embeddings import get_embeddings_manager


class ProjectManager:
    """Manages projects and provides intelligent project suggestions."""
    
    def __init__(self):
        self.storage = storage
    
    def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        return self.storage.load_projects()
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self.storage.get_project(project_id)
    
    def create_project(self, name: str, description: str = "", color: str = "#3b82f6") -> Project:
        """Create a new project."""
        project = Project(
            name=name,
            description=description,
            color=color
        )
        
        # Save to storage
        self.storage.add_project(project)
        
        # Generate embedding
        try:
            embeddings_mgr = get_embeddings_manager()
            if embeddings_mgr:
                embeddings_mgr.embed_project(project)
        except Exception:
            pass  # Embeddings are optional
        
        return project
    
    def suggest_projects_for_text(self, text: str, top_k: int = 3) -> List[Tuple[Project, float]]:
        """
        Suggest projects for a given text using embeddings.
        
        Returns a list of (project, similarity_score) tuples.
        Higher score = better match (lower distance).
        """
        embeddings_mgr = get_embeddings_manager()
        if not embeddings_mgr:
            # No embeddings available, return empty list
            return []
        
        projects = self.get_all_projects()
        if not projects:
            return []
        
        try:
            # Search for similar projects
            results = embeddings_mgr.search(text, top_k=top_k * 2)  # Get more results to filter
            
            # Filter for project results only
            project_results = [r for r in results if r.result_type == 'project'][:top_k]
            
            # Map back to Project objects with scores
            suggestions = []
            for result in project_results:
                project_id = result.metadata.get('project_id')
                if project_id:
                    project = self.get_project(project_id)
                    if project:
                        # Convert distance to similarity (inverse)
                        # Lower distance = higher similarity
                        similarity = 1.0 / (1.0 + result.distance)
                        suggestions.append((project, similarity))
            
            return suggestions
            
        except Exception:
            # If embeddings fail, return empty list
            return []
    
    def assign_task_to_project(self, task_id: str, project_id: str):
        """Assign a task to a project."""
        task = self.storage.get_task(task_id)
        if task:
            task.project_id = project_id
            task.updated_at = datetime.now()
            self.storage.update_task(task)
            
            # Re-embed the task with updated project info
            try:
                embeddings_mgr = get_embeddings_manager()
                if embeddings_mgr:
                    embeddings_mgr.embed_task(task)
            except Exception:
                pass  # Embeddings are optional
    
    def get_project_tasks(self, project_id: str, include_completed: bool = False):
        """Get all tasks for a project."""
        tasks = self.storage.load_tasks()
        project_tasks = [t for t in tasks if t.project_id == project_id]
        
        if not include_completed:
            project_tasks = [t for t in project_tasks if not t.completed]
        
        return project_tasks
    
    def delete_project(self, project_id: str, unassign_tasks: bool = True):
        """Delete a project and optionally unassign its tasks."""
        if unassign_tasks:
            # Unassign all tasks from this project
            tasks = self.get_project_tasks(project_id, include_completed=True)
            for task in tasks:
                task.project_id = None
                self.storage.update_task(task)
        
        # Remove embedding
        try:
            embeddings_mgr = get_embeddings_manager()
            if embeddings_mgr:
                embeddings_mgr.remove_project_embedding(project_id)
        except Exception:
            pass
        
        # Delete from storage
        self.storage.delete_project(project_id)


# Global project manager instance
project_manager = ProjectManager()

