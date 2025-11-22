"""Claude API integration and conversation management."""

from datetime import datetime
from typing import List, Dict, Optional
import anthropic

from config import config
from storage import storage, JournalEntry

# Try to import calendar integration (may not be configured)
try:
    from calendar_integration import calendar_integration
    CALENDAR_AVAILABLE = calendar_integration is not None
except ImportError:
    CALENDAR_AVAILABLE = False
    calendar_integration = None


class Assistant:
    """Manages conversations with Claude API."""
    
    def __init__(self):
        self.api_key = config.get_api_key()
        if not self.api_key:
            raise ValueError(
                "No API key found. Set it with 'focus config' or "
                "set the ANTHROPIC_API_KEY environment variable."
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with context from today's morning routine."""
        base_prompt = config.get_personality()
        
        # Add current date/time context
        now = datetime.now()
        date_context = f"\n\nCurrent date and time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"
        date_context += f"\nToday is: {now.strftime('%Y-%m-%d')}"
        date_context += f"\nDay of week: {now.strftime('%A')}"
        base_prompt += date_context
        
        # Add morning context if available
        morning_entry = storage.get_morning_entry()
        if morning_entry:
            context = "\n\nToday's morning reflection:\n"
            if morning_entry.get("responses"):
                for q, a in morning_entry["responses"].items():
                    context += f"- {q}: {a}\n"
            base_prompt += context
        
        # Add task context
        tasks = storage.get_incomplete_tasks()
        if tasks:
            context = "\n\nCurrent incomplete tasks:\n"
            for task in tasks[:10]:  # Limit to 10 most recent
                context += f"- {task.text}"
                if task.due_date:
                    context += f" (due: {task.due_date.strftime('%Y-%m-%d')})"
                context += "\n"
            base_prompt += context
        
        # Add calendar context if available
        if CALENDAR_AVAILABLE and calendar_integration.is_configured() and calendar_integration.has_token():
            try:
                # Get upcoming calendar events (next 7 days)
                events = calendar_integration.get_events()
                if events:
                    context = "\n\nUpcoming calendar events:\n"
                    context += calendar_integration.format_events_for_llm(events)
                    base_prompt += context
            except Exception:
                # Silently fail if calendar isn't accessible
                pass
        
        return base_prompt
    
    def refresh_context(self):
        """Refresh the system prompt with latest context."""
        self.system_prompt = self._build_system_prompt()
    
    def send_message(self, user_message: str, save_to_journal: bool = True) -> str:
        """Send a message to Claude and get a response."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Get response from Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=self.system_prompt,
            messages=self.conversation_history
        )
        
        # Extract assistant's response
        assistant_message = response.content[0].text
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Save to journal if requested
        if save_to_journal:
            self._save_to_journal(user_message, assistant_message)
        
        return assistant_message
    
    def _save_to_journal(self, user_message: str, assistant_message: str):
        """Save conversation to today's journal."""
        # Save user message
        user_entry = JournalEntry(
            date=datetime.now().strftime("%Y-%m-%d"),
            entry_type="chat",
            response=user_message,
            metadata={"role": "user"}
        )
        storage.add_journal_entry(user_entry)
        
        # Save assistant message
        assistant_entry = JournalEntry(
            date=datetime.now().strftime("%Y-%m-%d"),
            entry_type="chat",
            response=assistant_message,
            metadata={"role": "assistant"}
        )
        storage.add_journal_entry(assistant_entry)
    
    def ask_question(self, question: str) -> str:
        """Ask a single question without full conversation context."""
        response = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": question}]
        )
        return response.content[0].text
    
    def parse_task_intent(self, text: str) -> Optional[Dict[str, str]]:
        """
        Parse natural language text to detect task creation intent.
        Returns dict with 'task' and 'date' if a task is detected, None otherwise.
        """
        prompt = f"""
            Analyze this text and determine if the user wants to create a task or reminder.
            If yes, extract:
            1. The task description (what to do)
            2. When it's due (if mentioned, otherwise null)

            Text: "{text}"

            Respond in JSON format:
            {{"has_task": true/false, "task": "task description", "due": "date string or null"}}

            Only set has_task to true if the user clearly wants to be reminded of something or add a task.
            For the due date, extract phrases like "tomorrow", "next week", "monday", "in 3 days", etc.
            If no specific date is mentioned, set due to null.
        """
        
        response = self.ask_question(prompt)
        
        # Try to parse JSON from response
        import json
        try:
            # Find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
                if result.get("has_task"):
                    return {
                        "task": result.get("task", ""),
                        "due": result.get("due")
                    }
        except (json.JSONDecodeError, ValueError):
            pass
        
        return None
    
    def clear_history(self):
        """Clear conversation history (for new sessions)."""
        self.conversation_history = []
    
    def load_history_from_today(self):
        """Load today's chat history into conversation context."""
        chat_history = storage.get_chat_history()
        self.conversation_history = []
        
        for entry in chat_history:
            role = entry.get("metadata", {}).get("role", "user")
            self.conversation_history.append({
                "role": role,
                "content": entry["response"]
            })

