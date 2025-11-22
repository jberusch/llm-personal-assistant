"""
Google Calendar integration for Focus Assistant.

Provides read/write access to Google Calendar events.
"""

from __future__ import annotations

import pickle
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from compat import ensure_importlib_metadata_support

ensure_importlib_metadata_support()

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import config

# If modifying these scopes, delete the token file
SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarIntegration:
    """Handles Google Calendar API integration."""
    
    def __init__(self):
        self.data_dir = Path(config.config_dir)
        self.credentials_file = self.data_dir / 'google_credentials.json'
        self.token_file = self.data_dir / 'google_token.pickle'
        self.service = None
        self._creds: Optional[Credentials] = None
    
    def _ensure_service(self) -> None:
        """Initialize Google Calendar service with authentication if needed."""
        if self.service:
            return

        if not self.credentials_file.exists():
            raise FileNotFoundError(
                f"Google credentials file not found at {self.credentials_file}\n"
                "Please follow the setup instructions in GOOGLE_CALENDAR_SETUP.md"
            )

        creds: Optional[Credentials] = None

        # Load existing token
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        self._creds = creds
        self.service = build('calendar', 'v3', credentials=creds)
    
    def is_configured(self) -> bool:
        """Check if Google Calendar is configured."""
        return self.credentials_file.exists()
    
    def has_token(self) -> bool:
        """Return True if OAuth token has been generated."""
        return self.token_file.exists()
    
    def _to_utc_rfc3339(self, dt: datetime) -> str:
        """Convert a datetime to UTC RFC3339 format for Google Calendar API."""
        # If datetime is naive (no timezone), assume it's in local time
        if dt.tzinfo is None:
            dt = dt.astimezone()  # Convert to local timezone-aware datetime
        
        # Convert to UTC
        dt_utc = dt.astimezone(timezone.utc)
        
        # Return ISO format with 'Z' suffix
        return dt_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events within a date range.
        
        Args:
            start_date: Start of date range (default: now)
            end_date: End of date range (default: 7 days from now)
            max_results: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        try:
            self._ensure_service()
        except FileNotFoundError:
            raise
        except Exception as error:
            print(f"An error occurred: {error}")
            return []

        try:
            if start_date is None:
                start_date = datetime.now()
            if end_date is None:
                end_date = start_date + timedelta(days=7)
            
            # Convert to RFC3339 timestamp in UTC
            time_min = self._to_utc_rfc3339(start_date)
            time_max = self._to_utc_rfc3339(end_date)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events for easier use
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start': start,
                    'end': end,
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'all_day': 'date' in event['start']
                })
            
            return formatted_events
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_events_for_date(self, target_date: datetime) -> List[Dict[str, Any]]:
        """Get all events for a specific date."""
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return self.get_events(start, end, max_results=50)
    
    def get_events_today(self) -> List[Dict[str, Any]]:
        """Get today's events."""
        return self.get_events_for_date(datetime.now())
    
    def get_events_tomorrow(self) -> List[Dict[str, Any]]:
        """Get tomorrow's events."""
        return self.get_events_for_date(datetime.now() + timedelta(days=1))
    
    def get_events_this_week(self) -> List[Dict[str, Any]]:
        """Get this week's events."""
        today = datetime.now()
        # Get to next Sunday
        days_until_sunday = 6 - today.weekday()
        if days_until_sunday < 0:
            days_until_sunday += 7
        
        end_of_week = today + timedelta(days=days_until_sunday)
        end_of_week = end_of_week.replace(hour=23, minute=59, second=59)
        
        return self.get_events(today, end_of_week, max_results=50)
    
    def get_weekend_events(self) -> List[Dict[str, Any]]:
        """Get this weekend's events (Saturday and Sunday)."""
        today = datetime.now()
        
        # Find next Saturday
        days_until_saturday = 5 - today.weekday()
        if days_until_saturday <= 0:
            days_until_saturday += 7
        
        saturday = today + timedelta(days=days_until_saturday)
        saturday = saturday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Sunday end of day
        sunday = saturday + timedelta(days=1)
        sunday_end = sunday.replace(hour=23, minute=59, second=59)
        
        return self.get_events(saturday, sunday_end, max_results=50)
    
    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: str = "",
        location: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new calendar event.
        
        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time (default: 1 hour after start)
            description: Event description
            location: Event location
            
        Returns:
            Created event dictionary or None on failure
        """
        try:
            self._ensure_service()
        except FileNotFoundError:
            raise
        except Exception as error:
            print(f"An error occurred: {error}")
            return None

        try:
            if end_time is None:
                end_time = start_time + timedelta(hours=1)
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Los_Angeles',  # TODO: Make configurable
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Los_Angeles',
                },
            }
            
            if location:
                event['location'] = location
            
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {
                'id': created_event['id'],
                'summary': created_event['summary'],
                'start': created_event['start']['dateTime'],
                'end': created_event['end']['dateTime'],
                'htmlLink': created_event.get('htmlLink', '')
            }
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def format_events_for_display(self, events: List[Dict[str, Any]]) -> str:
        """Format events for rich console display."""
        if not events:
            return "No events scheduled"
        
        lines = []
        for event in events:
            start = event['start']
            
            # Parse the datetime
            if event['all_day']:
                # All-day event
                date_str = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%a, %b %d')
                time_str = "All day"
            else:
                dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                date_str = dt.strftime('%a, %b %d')
                time_str = dt.strftime('%I:%M %p')
            
            summary = event['summary']
            location = f" @ {event['location']}" if event['location'] else ""
            
            lines.append(f"  • {time_str}: {summary}{location}")
        
        return "\n".join(lines)
    
    def format_events_for_llm(self, events: List[Dict[str, Any]]) -> str:
        """Format events for LLM context."""
        if not events:
            return "No events scheduled"
        
        lines = []
        for event in events:
            start = event['start']
            
            if event['all_day']:
                dt_str = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%A, %B %d')
                time_str = "all day"
            else:
                dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                dt_str = dt.strftime('%A, %B %d')
                time_str = dt.strftime('%I:%M %p')
            
            summary = event['summary']
            location = f" at {event['location']}" if event['location'] else ""
            
            lines.append(f"- {dt_str}, {time_str}: {summary}{location}")
        
        return "\n".join(lines)


# Global instance (lazy auth happens on first use)
calendar_integration = CalendarIntegration()

