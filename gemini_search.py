"""Gemini API integration for web search."""

import google.generativeai as genai
import re
from typing import Optional
from config import config


class GeminiSearch:
    """Handles Gemini API calls for web-style Q&A."""
    
    def __init__(self, api_key: str):
        """Initialize Gemini client with API key."""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Use a fast, modern Gemini model
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    def search(self, query: str) -> dict:
        """
        Ask Gemini a web-style question and get an answer with sources.
        
        Args:
            query: The search query
            
        Returns:
            dict with 'answer' and 'sources' keys
        """
        try:
            # Ask Gemini to answer and include sources/links directly
            prompt = f"""You are an AI search assistant.

            The user asked: "{query}"

            Answer as if you just searched the live web:
            - Provide a clear, concise answer.
            - When you state specific facts, include inline citations like [1], [2] where helpful.
            - At the end, include a **Sources** section with a numbered list of titles and URLs, e.g.:

            **Sources**
            [1] Title - https://example.com
            [2] Another Title - https://example.org

            If you are not fully sure about something, say so explicitly."""

            response = self.model.generate_content(prompt)
            answer_text = response.text
            
            # Parse sources from the answer
            sources = self._parse_sources(answer_text)
            
            result = {
                'answer': answer_text,
                'sources': sources
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Gemini search error: {e}")
    
    def _parse_sources(self, text: str) -> list:
        """
        Parse sources from markdown answer text.
        
        Looks for patterns like:
        [1] Title - URL
        [2] Another Title - URL
        
        Returns list of dicts with 'title' and 'url' keys.
        """
        sources = []
        
        # Pattern to match: [number] Title - URL
        # More permissive so it handles extra \" - Provider - URL\" patterns too.
        # Examples it should match:
        # [1] Title - https://example.com
        # [1] Title - Provider - https://example.com
        pattern = r'\[(\d+)\]\s*(.+?)\s*-\s*(https?://[^\s\n)]+)'
        
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            number, title, url = match
            sources.append({
                'title': title.strip(),
                'url': url.strip()
            })
        
        return sources


def get_gemini_client(api_key: Optional[str] = None) -> Optional[GeminiSearch]:
    """
    Get or create a Gemini client.
    
    Args:
        api_key: Optional API key. If not provided, will try to get from config.
        
    Returns:
        GeminiSearch instance or None if no API key available
    """
    if not api_key:
        # Try to get from config (uses same Google API key)
        api_key = config.get_google_search_key()
    
    if not api_key:
        return None
    
    try:
        return GeminiSearch(api_key)
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
        return None

