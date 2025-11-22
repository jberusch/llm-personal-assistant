"""Google Places API integration for finding local businesses."""

import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Place:
    """Represents a place from Google Places API."""
    place_id: str
    name: str
    address: str
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    opening_hours: Optional[Dict[str, Any]] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    types: List[str] = None
    vicinity: Optional[str] = None
    business_status: Optional[str] = None
    editorial_summary: Optional[str] = None
    
    def __post_init__(self):
        if self.types is None:
            self.types = []
    
    def get_price_string(self) -> str:
        """Convert price level (0-4) to dollar signs."""
        if self.price_level is None:
            return "Price unknown"
        return "$" * max(1, self.price_level)
    
    def get_status_string(self) -> str:
        """Get human-readable status."""
        if not self.opening_hours:
            return "Hours unknown"
        if self.opening_hours.get('open_now'):
            return "Open now"
        return "Closed"
    
    def get_google_maps_url(self) -> str:
        """Get Google Maps URL for this place."""
        return f"https://www.google.com/maps/place/?q=place_id:{self.place_id}"


class GooglePlacesClient:
    """Client for Google Places API."""
    
    # Using Places API (new) - more features and better pricing
    BASE_URL = "https://places.googleapis.com/v1/places"
    LEGACY_BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    def __init__(self, api_key: str):
        """
        Initialize Google Places client.
        
        Args:
            api_key: Google API key with Places API enabled
        """
        self.api_key = api_key
    
    def text_search(self, query: str, location: Optional[Tuple[float, float]] = None, 
                   radius: int = 5000, max_results: int = 10) -> List[Place]:
        """
        Search for places using text query.
        
        Args:
            query: Search query (e.g., "coffee near me", "pizza in hayes valley")
            location: Optional (latitude, longitude) tuple for biasing results
            radius: Search radius in meters (default 5000m = 3.1 miles)
            max_results: Maximum number of results (default 10)
        
        Returns:
            List of Place objects
        """
        # Use legacy Text Search API (more reliable for now)
        url = f"{self.LEGACY_BASE_URL}/textsearch/json"
        
        params = {
            'query': query,
            'key': self.api_key,
        }
        
        if location:
            params['location'] = f"{location[0]},{location[1]}"
            params['radius'] = radius
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                if data.get('status') == 'ZERO_RESULTS':
                    return []
                raise Exception(f"Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
            
            results = data.get('results', [])[:max_results]
            
            places = []
            for result in results:
                # Extract editorial summary if available
                editorial_summary = None
                if 'editorial_summary' in result:
                    editorial_summary = result['editorial_summary'].get('overview')
                
                place = Place(
                    place_id=result.get('place_id', ''),
                    name=result.get('name', 'Unknown'),
                    address=result.get('formatted_address', ''),
                    rating=result.get('rating'),
                    user_ratings_total=result.get('user_ratings_total'),
                    price_level=result.get('price_level'),
                    opening_hours=result.get('opening_hours'),
                    vicinity=result.get('vicinity'),
                    types=result.get('types', []),
                    business_status=result.get('business_status'),
                    editorial_summary=editorial_summary,
                )
                places.append(place)
            
            return places
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
    
    def get_place_details(self, place_id: str) -> Place:
        """
        Get detailed information about a specific place.
        
        Args:
            place_id: Google Place ID
        
        Returns:
            Place object with full details
        """
        url = f"{self.LEGACY_BASE_URL}/details/json"
        
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,'
                     'user_ratings_total,price_level,opening_hours,types,business_status,url,editorial_summary'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                raise Exception(f"Places API error: {data.get('status')}")
            
            result = data.get('result', {})
            
            # Extract editorial summary if available
            editorial_summary = None
            if 'editorial_summary' in result:
                editorial_summary = result['editorial_summary'].get('overview')
            
            place = Place(
                place_id=place_id,
                name=result.get('name', 'Unknown'),
                address=result.get('formatted_address', ''),
                rating=result.get('rating'),
                user_ratings_total=result.get('user_ratings_total'),
                price_level=result.get('price_level'),
                opening_hours=result.get('opening_hours'),
                phone_number=result.get('formatted_phone_number'),
                website=result.get('website'),
                types=result.get('types', []),
                business_status=result.get('business_status'),
                editorial_summary=editorial_summary,
            )
            
            return place
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")
    
    def nearby_search(self, location: Tuple[float, float], place_type: Optional[str] = None,
                     keyword: Optional[str] = None, radius: int = 1500, 
                     max_results: int = 10) -> List[Place]:
        """
        Search for places near a location.
        
        Args:
            location: (latitude, longitude) tuple
            place_type: Type of place (e.g., 'restaurant', 'cafe', 'bar')
            keyword: Additional keyword to filter results
            radius: Search radius in meters (default 1500m ~ 1 mile)
            max_results: Maximum number of results
        
        Returns:
            List of Place objects
        """
        url = f"{self.LEGACY_BASE_URL}/nearbysearch/json"
        
        params = {
            'location': f"{location[0]},{location[1]}",
            'radius': radius,
            'key': self.api_key,
        }
        
        if place_type:
            params['type'] = place_type
        if keyword:
            params['keyword'] = keyword
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                if data.get('status') == 'ZERO_RESULTS':
                    return []
                raise Exception(f"Places API error: {data.get('status')}")
            
            results = data.get('results', [])[:max_results]
            
            places = []
            for result in results:
                # Extract editorial summary if available
                editorial_summary = None
                if 'editorial_summary' in result:
                    editorial_summary = result['editorial_summary'].get('overview')
                
                place = Place(
                    place_id=result.get('place_id', ''),
                    name=result.get('name', 'Unknown'),
                    address=result.get('vicinity', ''),
                    rating=result.get('rating'),
                    user_ratings_total=result.get('user_ratings_total'),
                    price_level=result.get('price_level'),
                    opening_hours=result.get('opening_hours'),
                    vicinity=result.get('vicinity'),
                    types=result.get('types', []),
                    business_status=result.get('business_status'),
                    editorial_summary=editorial_summary,
                )
                places.append(place)
            
            return places
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")


# Singleton instance
_google_places_client: Optional[GooglePlacesClient] = None


def get_google_places_client(api_key: Optional[str] = None) -> Optional[GooglePlacesClient]:
    """
    Get or create Google Places client.
    
    Args:
        api_key: Google API key (optional, will use existing if not provided)
    
    Returns:
        GooglePlacesClient instance or None if not configured
    """
    global _google_places_client
    
    if api_key:
        _google_places_client = GooglePlacesClient(api_key)
    
    return _google_places_client


def is_google_places_configured() -> bool:
    """Check if Google Places is configured and ready to use."""
    return _google_places_client is not None

