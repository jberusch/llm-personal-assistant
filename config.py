"""Configuration management for the focus assistant."""

import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """Manages configuration for the focus assistant."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".focus_assistant"
        self.config_file = self.config_dir / "config.json"
        self.tasks_file = self.config_dir / "tasks.json"
        self.journal_dir = self.config_dir / "journal"
        
        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.journal_dir.mkdir(exist_ok=True)
        
        # Load or create config
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            "anthropic_api_key": None,
            "assistant_personality": "You are a focused productivity coach. Be firm but kind. Remember the user's daily goals and gently challenge distractions."
        }
    
    def save(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get_api_key(self) -> Optional[str]:
        """Get Claude API key from config or environment."""
        # Try config first, then environment
        api_key = self._config.get("anthropic_api_key")
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        return api_key
    
    def set_api_key(self, api_key: str):
        """Set Claude API key in config."""
        self._config["anthropic_api_key"] = api_key
        self.save()
    
    def get_personality(self) -> str:
        """Get assistant personality prompt."""
        return self._config.get("assistant_personality", "")


# Global config instance
config = Config()

