"""Personal profile management for the focus assistant."""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from config import config


class ProfileManager:
    """Manages user profile stored in markdown format."""
    
    def __init__(self):
        self.profile_file = config.config_dir / "profile.md"
        self._ensure_profile_exists()
    
    def _ensure_profile_exists(self):
        """Create default profile if it doesn't exist."""
        if not self.profile_file.exists():
            self._create_default_profile()
    
    def _create_default_profile(self):
        """Create a default profile template."""
        template = """# Personal Profile

<!-- This file contains personal context that will be available to your assistant. -->
<!-- Edit this file to add information about yourself, your preferences, and context. -->
<!-- Only include information you're comfortable having in every conversation context. -->

## Location & Context

*Where you live, timezone, general context about your environment*


## Preferences

*Your preferences for work, communication style, tools, etc.*


## Work & Projects

*Current role, projects you're working on, professional context*


## Personal

*Personal interests, hobbies, things that matter to you*


## Goals

*Current goals, aspirations, things you're working toward*


## Communication Style

*How you prefer to receive feedback, coaching style you prefer, etc.*


---
*Last updated: Never*
"""
        with open(self.profile_file, 'w') as f:
            f.write(template)
    
    def load_profile(self) -> str:
        """Load the full profile content."""
        if not self.profile_file.exists():
            self._create_default_profile()
        
        with open(self.profile_file, 'r') as f:
            content = f.read()
        
        # Check if profile is mostly empty (just template)
        # Count non-comment, non-header lines with actual content
        lines = content.split('\n')
        content_lines = [
            line.strip() for line in lines 
            if line.strip() 
            and not line.strip().startswith('#')
            and not line.strip().startswith('<!--')
            and not line.strip().endswith('-->')
            and not line.strip().startswith('*')
            and not line.strip() == '---'
        ]
        
        # If there's minimal content, return empty string
        # Use a lower threshold - if there's at least 1 line of real content, include it
        if len(content_lines) < 1:
            return ""
        
        return content
    
    def save_profile(self, content: str):
        """Save profile content to file."""
        # Add last updated timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d at %I:%M %p")
        
        # Update the timestamp line if it exists
        if "*Last updated:" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('*Last updated:'):
                    lines[i] = f"*Last updated: {timestamp}*"
                    break
            content = '\n'.join(lines)
        else:
            # Add timestamp at the end
            content = content.rstrip() + f"\n\n---\n*Last updated: {timestamp}*\n"
        
        with open(self.profile_file, 'w') as f:
            f.write(content)
    
    def get_profile_path(self) -> Path:
        """Get the path to the profile file."""
        return self.profile_file
    
    def parse_profile_sections(self) -> Dict[str, str]:
        """Parse profile into sections."""
        # Read directly from file to avoid filtering
        if not self.profile_file.exists():
            return {}
        
        with open(self.profile_file, 'r') as f:
            content = f.read()
        
        if not content:
            return {}
        
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        for line in lines:
            # Check for section headers (## Header)
            if line.strip().startswith('## '):
                # Save previous section if exists
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.strip()[3:].strip()
                current_content = []
            elif current_section:
                # Skip template comments, italicized instructions, and separators
                stripped = line.strip()
                if (not stripped.startswith('<!--') 
                    and not stripped.endswith('-->')
                    and not stripped.startswith('*')
                    and stripped != '---'):
                    current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            section_content = '\n'.join(current_content).strip()
            if section_content:
                sections[current_section] = section_content
        
        return sections
    
    def update_section(self, section_name: str, content: str):
        """Update a specific section in the profile."""
        full_content = self.load_profile()
        
        if not full_content:
            # If profile is empty, create from template first
            self._create_default_profile()
            full_content = self.load_profile()
        
        sections = self.parse_profile_sections()
        
        # Update or add the section
        sections[section_name] = content.strip()
        
        # Rebuild the profile
        new_content = "# Personal Profile\n\n"
        new_content += "<!-- This file contains personal context that will be available to your assistant. -->\n\n"
        
        for section, section_content in sections.items():
            if section_content:  # Only include sections with content
                new_content += f"## {section}\n\n{section_content}\n\n"
        
        self.save_profile(new_content)
    
    def append_to_section(self, section_name: str, content: str):
        """Append content to a section."""
        sections = self.parse_profile_sections()
        existing = sections.get(section_name, "")
        
        if existing:
            updated = existing + "\n\n" + content.strip()
        else:
            updated = content.strip()
        
        self.update_section(section_name, updated)
    
    def detect_profile_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detect if the user wants to update their profile.
        Returns dict with 'action' and 'updates' if detected, None otherwise.
        """
        # Simple keyword matching for common profile update patterns
        lower_text = text.lower()
        
        # Profile update keywords
        profile_keywords = [
            'remember that i',
            'remember i',
            'update my profile',
            'add to my profile',
            'i live in',
            'i prefer',
            'i like',
            'i am',
            "i'm a",
            "i'm from",
            'my goal is',
            'my goals are',
            'save this:',
            'note:',
        ]
        
        # Check if any keywords match
        has_keyword = any(keyword in lower_text for keyword in profile_keywords)
        
        if has_keyword:
            return {
                "action": "update_profile",
                "text": text,
                "confidence": "medium"
            }
        
        return None
    
    def format_for_display(self) -> str:
        """Format profile for terminal display."""
        content = self.load_profile()
        
        if not content:
            return "[dim]Profile is empty. Add information via chat or edit directly with:[/dim]\n  [cyan]./focus profile edit[/cyan]"
        
        # Remove HTML comments for display
        lines = content.split('\n')
        display_lines = [
            line for line in lines 
            if not line.strip().startswith('<!--') 
            and not line.strip().endswith('-->')
        ]
        
        return '\n'.join(display_lines)
    
    def reset_profile(self):
        """Reset profile to default template."""
        if self.profile_file.exists():
            self.profile_file.unlink()
        self._create_default_profile()


# Global profile manager instance
profile_manager = ProfileManager()

