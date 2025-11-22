"""Google Custom Search API integration for web search."""

from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSearchClient:
    """Client for Google Custom Search API."""
    
    def __init__(self, api_key: str, cx_id: str):
        """
        Initialize Google Search client.
        
        Args:
            api_key: Google API key (from Google Cloud Console)
            cx_id: Custom Search Engine ID (from programmablesearchengine.google.com)
        """
        self.api_key = api_key
        self.cx_id = cx_id
        self._service = None
    
    def _get_service(self):
        """Lazy load the Google Custom Search service."""
        if self._service is None:
            self._service = build("customsearch", "v1", developerKey=self.api_key)
        return self._service
    
    def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using Google Custom Search API.
        
        Args:
            query: Search query
            num_results: Number of results to return (max 10 per request)
        
        Returns:
            List of search results with 'title', 'link', 'snippet' keys
        
        Raises:
            HttpError: If API request fails
        """
        try:
            service = self._get_service()
            
            # Google CSE limits to 10 results per request
            num_results = min(num_results, 10)
            
            # Execute search
            result = service.cse().list(
                q=query,
                cx=self.cx_id,
                num=num_results
            ).execute()
            
            # Parse results
            items = result.get('items', [])
            
            # Format results to match DuckDuckGo format
            formatted_results = []
            for item in items:
                formatted_results.append({
                    'title': item.get('title', 'No title'),
                    'href': item.get('link', ''),
                    'link': item.get('link', ''),
                    'body': item.get('snippet', ''),
                    'snippet': item.get('snippet', ''),
                })
            
            return formatted_results
            
        except HttpError as e:
            # Re-raise with more context
            error_details = e.error_details if hasattr(e, 'error_details') else []
            if e.resp.status == 429:
                raise Exception("Google Search API quota exceeded. You've used your 100 free searches today.")
            elif e.resp.status == 403:
                raise Exception("Google Search API authentication failed. Check your API key and CX ID.")
            else:
                raise Exception(f"Google Search API error: {e}")
    
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return bool(self.api_key and self.cx_id)


# Singleton instance
_google_search_client: Optional[GoogleSearchClient] = None


def get_google_search_client(api_key: Optional[str] = None, cx_id: Optional[str] = None) -> Optional[GoogleSearchClient]:
    """
    Get or create Google Search client.
    
    Args:
        api_key: Google API key (optional, will use existing if not provided)
        cx_id: Custom Search Engine ID (optional, will use existing if not provided)
    
    Returns:
        GoogleSearchClient instance or None if not configured
    """
    global _google_search_client
    
    if api_key and cx_id:
        _google_search_client = GoogleSearchClient(api_key, cx_id)
    
    return _google_search_client


def is_google_search_configured() -> bool:
    """Check if Google Search is configured and ready to use."""
    return _google_search_client is not None and _google_search_client.is_configured()

