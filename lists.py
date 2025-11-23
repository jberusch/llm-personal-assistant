"""Persistent lists with rich metadata for tracking places, books, recommendations, etc."""

import json
from pathlib import Path
from typing import List as ListType, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field


class ListItem(BaseModel):
    """An item in a list with rich metadata."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    list_id: str
    title: str
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PersistentList(BaseModel):
    """A persistent list for organizing items."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    category: str = "general"  # places, books, restaurants, etc.
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ListManager:
    """Manages persistent lists and their items."""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.lists_file = self.data_dir / "lists.json"
    
    def _load_data(self) -> Dict[str, Any]:
        """Load lists and items from storage."""
        if not self.lists_file.exists():
            return {"lists": [], "items": []}
        
        try:
            with open(self.lists_file, 'r') as f:
                data = json.load(f)
                # Ensure both keys exist
                if "lists" not in data:
                    data["lists"] = []
                if "items" not in data:
                    data["items"] = []
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            return {"lists": [], "items": []}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save lists and items to storage."""
        with open(self.lists_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def create_list(self, name: str, description: str = "", category: str = "general") -> PersistentList:
        """Create a new list."""
        # Check if list with this name already exists
        existing = self.get_list_by_name(name)
        if existing:
            return existing
        
        new_list = PersistentList(
            name=name,
            description=description,
            category=category
        )
        
        data = self._load_data()
        data["lists"].append(new_list.model_dump(mode='json'))
        self._save_data(data)
        
        return new_list
    
    def get_all_lists(self) -> ListType[PersistentList]:
        """Get all lists."""
        data = self._load_data()
        return [PersistentList(**lst) for lst in data["lists"]]
    
    def get_list_by_name(self, name: str) -> Optional[PersistentList]:
        """Get a list by name (case-insensitive)."""
        data = self._load_data()
        name_lower = name.lower()
        
        for lst in data["lists"]:
            if lst["name"].lower() == name_lower:
                return PersistentList(**lst)
        
        return None
    
    def get_list_by_id(self, list_id: str) -> Optional[PersistentList]:
        """Get a list by ID."""
        data = self._load_data()
        
        for lst in data["lists"]:
            if lst["id"] == list_id:
                return PersistentList(**lst)
        
        return None
    
    def add_item(
        self,
        list_name: str,
        title: str,
        description: str = "",
        metadata: Dict[str, Any] = None,
        auto_create_list: bool = True
    ) -> ListItem:
        """Add an item to a list.
        
        Args:
            list_name: Name of the list
            title: Item title
            description: Item description
            metadata: Additional metadata (tags, notes, etc.)
            auto_create_list: Create list if it doesn't exist
        
        Returns:
            The created list item
        """
        # Get or create list
        lst = self.get_list_by_name(list_name)
        if not lst:
            if auto_create_list:
                lst = self.create_list(list_name)
            else:
                raise ValueError(f"List '{list_name}' not found")
        
        # Create item
        item = ListItem(
            list_id=lst.id,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        
        data = self._load_data()
        data["items"].append(item.model_dump(mode='json'))
        self._save_data(data)
        
        # Auto-embed for search
        self._embed_item(item)
        
        return item
    
    def get_list_items(self, list_name: str) -> ListType[ListItem]:
        """Get all items in a list."""
        lst = self.get_list_by_name(list_name)
        if not lst:
            return []
        
        data = self._load_data()
        items = []
        
        for item_data in data["items"]:
            if item_data["list_id"] == lst.id:
                items.append(ListItem(**item_data))
        
        # Sort by created date (newest first)
        items.sort(key=lambda x: x.created_at, reverse=True)
        
        return items
    
    def update_item(self, item_id: str, **updates) -> Optional[ListItem]:
        """Update a list item."""
        data = self._load_data()
        
        for i, item_data in enumerate(data["items"]):
            if item_data["id"] == item_id:
                # Apply updates
                item_data.update(updates)
                item_data["updated_at"] = datetime.now().isoformat()
                
                data["items"][i] = item_data
                self._save_data(data)
                
                item = ListItem(**item_data)
                
                # Re-embed
                self._embed_item(item)
                
                return item
        
        return None
    
    def delete_item(self, item_id: str) -> bool:
        """Delete a list item."""
        data = self._load_data()
        
        for i, item_data in enumerate(data["items"]):
            if item_data["id"] == item_id:
                data["items"].pop(i)
                self._save_data(data)
                return True
        
        return False
    
    def search_items(self, query: str) -> ListType[ListItem]:
        """Search items by title or description (basic text search)."""
        data = self._load_data()
        query_lower = query.lower()
        results = []
        
        for item_data in data["items"]:
            title = item_data.get("title", "").lower()
            description = item_data.get("description", "").lower()
            
            # Check metadata tags and notes
            metadata = item_data.get("metadata", {})
            tags = " ".join(metadata.get("tags", [])).lower()
            notes = metadata.get("notes", "").lower()
            
            if (query_lower in title or 
                query_lower in description or 
                query_lower in tags or 
                query_lower in notes):
                results.append(ListItem(**item_data))
        
        return results
    
    def _embed_item(self, item: ListItem):
        """Embed a list item for semantic search."""
        try:
            from embeddings import get_embeddings_manager
            
            embeddings_mgr = get_embeddings_manager()
            if not embeddings_mgr:
                return
            
            # Build searchable text from item
            text_parts = [item.title]
            
            if item.description:
                text_parts.append(item.description)
            
            # Add metadata
            if item.metadata:
                if "tags" in item.metadata:
                    text_parts.append(" ".join(item.metadata["tags"]))
                if "notes" in item.metadata:
                    text_parts.append(item.metadata["notes"])
                if "address" in item.metadata:
                    text_parts.append(item.metadata["address"])
            
            text = " | ".join(text_parts)
            
            # Embed with list item context
            embeddings_mgr.embed_list_item(
                item_id=item.id,
                text=text,
                category="list_item"
            )
        
        except Exception:
            # Embeddings are optional
            pass


# Global instance
list_manager = ListManager()

