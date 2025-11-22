"""
Unified Google integrations (Calendar + Gmail) for Focus Assistant.
"""

from __future__ import annotations

import base64
import pickle
from email.mime.text import MIMEText
from email.utils import parseaddr, parsedate_to_datetime
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from compat import ensure_importlib_metadata_support

ensure_importlib_metadata_support()

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import config

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send',
]


class GoogleIntegration:
    """Handles Google Calendar + Gmail API access."""

    def __init__(self):
        self.data_dir = Path(config.config_dir)
        self.credentials_file = self.data_dir / 'google_credentials.json'
        self.token_file = self.data_dir / 'google_token.pickle'
        self._creds: Optional[Credentials] = None
        self.calendar_service = None
        self.gmail_service = None
        self.email_prefs_file = self.data_dir / 'email_preferences.json'
        self.email_prefs = self._load_email_preferences()

    # ------------------------------------------------------------------ #
    # Shared helpers
    # ------------------------------------------------------------------ #
    def _ensure_creds(self) -> None:
        """Ensure Google OAuth credentials are loaded and valid."""
        if self._creds and self._creds.valid:
            return

        creds: Optional[Credentials] = None
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        elif not creds or not creds.valid:
            if not self.credentials_file.exists():
                raise FileNotFoundError(
                    f"Google credentials file not found at {self.credentials_file}\n"
                    "Please follow the setup instructions in GOOGLE_CALENDAR_SETUP.md"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), SCOPES)
            creds = flow.run_local_server(port=0)

            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        self._creds = creds

    def _ensure_calendar_service(self) -> None:
        self._ensure_creds()
        if self.calendar_service is None:
            self.calendar_service = build('calendar', 'v3', credentials=self._creds)

    def _ensure_gmail_service(self) -> None:
        self._ensure_creds()
        if self.gmail_service is None:
            self.gmail_service = build('gmail', 'v1', credentials=self._creds)

    def is_configured(self) -> bool:
        return self.credentials_file.exists()

    def has_token(self) -> bool:
        return self.token_file.exists()

    # ------------------------------------------------------------------ #
    # Email preference helpers
    # ------------------------------------------------------------------ #
    def _load_email_preferences(self) -> Dict[str, Any]:
        if self.email_prefs_file.exists():
            try:
                with open(self.email_prefs_file, 'r') as f:
                    data = json.load(f)
                    return {
                        'keep_senders': set(data.get('keep_senders', [])),
                        'keep_domains': set(data.get('keep_domains', [])),
                    }
            except Exception:
                pass
        return {'keep_senders': set(), 'keep_domains': set()}

    def _save_email_preferences(self) -> None:
        data = {
            'keep_senders': sorted(self.email_prefs['keep_senders']),
            'keep_domains': sorted(self.email_prefs['keep_domains']),
        }
        with open(self.email_prefs_file, 'w') as f:
            json.dump(data, f, indent=2)

    def should_keep_sender(self, email: str) -> bool:
        if not email:
            return False
        email = email.lower()
        domain = email.split('@')[-1]
        prefs = self.email_prefs
        return (
            email in prefs['keep_senders']
            or domain in prefs['keep_domains']
        )

    def remember_sender(self, email: str) -> None:
        if not email:
            return
        email = email.lower()
        domain = email.split('@')[-1]
        prefs = self.email_prefs
        added = False
        if email not in prefs['keep_senders']:
            prefs['keep_senders'].add(email)
            added = True
        if domain and domain not in prefs['keep_domains']:
            prefs['keep_domains'].add(domain)
            added = True
        if added:
            self._save_email_preferences()

    # ------------------------------------------------------------------ #
    # Calendar helpers
    # ------------------------------------------------------------------ #
    def _to_utc_rfc3339(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.astimezone()
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        try:
            self._ensure_calendar_service()
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

            time_min = self._to_utc_rfc3339(start_date)
            time_max = self._to_utc_rfc3339(end_date)

            events_result = (
                self.calendar_service.events()
                .list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime',
                )
                .execute()
            )

            events = events_result.get('items', [])
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                formatted_events.append(
                    {
                        'id': event['id'],
                        'summary': event.get('summary', 'No Title'),
                        'start': start,
                        'end': end,
                        'description': event.get('description', ''),
                        'location': event.get('location', ''),
                        'all_day': 'date' in event['start'],
                    }
                )
            return formatted_events
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_events_for_date(self, target_date: datetime) -> List[Dict[str, Any]]:
        start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return self.get_events(start, end, max_results=50)

    def get_events_today(self) -> List[Dict[str, Any]]:
        return self.get_events_for_date(datetime.now())

    def get_events_tomorrow(self) -> List[Dict[str, Any]]:
        return self.get_events_for_date(datetime.now() + timedelta(days=1))

    def get_events_this_week(self) -> List[Dict[str, Any]]:
        today = datetime.now()
        days_until_sunday = 6 - today.weekday()
        if days_until_sunday < 0:
            days_until_sunday += 7
        end_of_week = today + timedelta(days=days_until_sunday)
        end_of_week = end_of_week.replace(hour=23, minute=59, second=59)
        return self.get_events(today, end_of_week, max_results=50)

    def get_weekend_events(self) -> List[Dict[str, Any]]:
        today = datetime.now()
        days_until_saturday = 5 - today.weekday()
        if days_until_saturday <= 0:
            days_until_saturday += 7
        saturday = today + timedelta(days=days_until_saturday)
        saturday = saturday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday_end = (saturday + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        return self.get_events(saturday, sunday_end, max_results=50)

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: str = "",
        location: str = "",
    ) -> Optional[Dict[str, Any]]:
        try:
            self._ensure_calendar_service()
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
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Los_Angeles',
                },
            }
            if location:
                event['location'] = location

            created_event = (
                self.calendar_service.events().insert(calendarId='primary', body=event).execute()
            )

            return {
                'id': created_event['id'],
                'summary': created_event['summary'],
                'start': created_event['start']['dateTime'],
                'end': created_event['end']['dateTime'],
                'htmlLink': created_event.get('htmlLink', ''),
            }
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def format_events_for_display(self, events: List[Dict[str, Any]]) -> str:
        if not events:
            return "No events scheduled"

        lines = []
        for event in events:
            start = event['start']
            if event['all_day']:
                date_str = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%a, %b %d')
                time_str = "All day"
            else:
                dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                date_str = dt.strftime('%a, %b %d')
                time_str = dt.strftime('%I:%M %p')
            location = f" @ {event['location']}" if event['location'] else ""
            lines.append(f"  • {time_str}: {event['summary']}{location}")
        return "\n".join(lines)

    def format_events_for_llm(self, events: List[Dict[str, Any]]) -> str:
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
            location = f" at {event['location']}" if event['location'] else ""
            lines.append(f"- {dt_str}, {time_str}: {event['summary']}{location}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Gmail helpers
    # ------------------------------------------------------------------ #
    def list_unread_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        try:
            self._ensure_gmail_service()
        except FileNotFoundError:
            raise
        except Exception as error:
            print(f"An error occurred: {error}")
            return []

        try:
            response = (
                self.gmail_service.users()
                .messages()
                .list(
                    userId='me',
                    labelIds=['UNREAD'],
                    q='in:inbox',
                    maxResults=max(1, min(max_results, 50)),
                )
                .execute()
            )
            messages = response.get('messages', [])
            summaries: List[Dict[str, Any]] = []

            for msg_meta in messages:
                full = (
                    self.gmail_service.users()
                    .messages()
                    .get(
                        userId='me',
                        id=msg_meta['id'],
                        format='metadata',
                        metadataHeaders=['Subject', 'From', 'Date'],
                    )
                    .execute()
                )
                summaries.append(self._build_message_summary(full))
            return summaries
        except HttpError as error:
            print(f"Gmail error: {error}")
            return []

    def search_emails(self, query: str, max_results: int = 25) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return []
        try:
            self._ensure_gmail_service()
        except FileNotFoundError:
            raise
        except Exception as error:
            print(f"An error occurred: {error}")
            return []

        try:
            response = (
                self.gmail_service.users()
                .messages()
                .list(
                    userId='me',
                    q=query,
                    labelIds=['INBOX'],
                    maxResults=max(1, min(max_results, 50)),
                )
                .execute()
            )
            messages = response.get('messages', [])
            summaries: List[Dict[str, Any]] = []
            for msg_meta in messages:
                full = (
                    self.gmail_service.users()
                    .messages()
                    .get(
                        userId='me',
                        id=msg_meta['id'],
                        format='metadata',
                        metadataHeaders=['Subject', 'From', 'Date'],
                    )
                    .execute()
                )
                summaries.append(self._build_message_summary(full))
            return summaries
        except HttpError as error:
            print(f"Gmail search error: {error}")
            return []

    def get_email(self, message_id: str) -> Optional[Dict[str, Any]]:
        try:
            self._ensure_gmail_service()
        except FileNotFoundError:
            raise
        except Exception as error:
            print(f"An error occurred: {error}")
            return None

        try:
            message = (
                self.gmail_service.users()
                .messages()
                .get(userId='me', id=message_id, format='full')
                .execute()
            )
            payload = message.get('payload', {})
            headers = self._headers_to_dict(payload.get('headers', []))
            from_name, from_email = parseaddr(headers.get('from', ''))
            body = self._extract_plain_body(payload)
            labels = message.get('labelIds', [])
            date_header = headers.get('date')
            date_str = ""
            if date_header:
                try:
                    parsed = parsedate_to_datetime(date_header)
                    date_str = parsed.strftime('%a, %b %d at %I:%M %p')
                except Exception:
                    date_str = date_header

            return {
                'id': message['id'],
                'threadId': message.get('threadId'),
                'subject': headers.get('subject', '(No subject)'),
                'from_name': from_name or from_email or "Unknown sender",
                'from_email': from_email,
                'date': date_str,
                'snippet': message.get('snippet', ''),
                'body': body,
                'labels': labels,
                'is_unread': 'UNREAD' in labels,
            }
        except HttpError as error:
            print(f"Gmail error: {error}")
            return None

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
    ) -> Optional[str]:
        try:
            self._ensure_gmail_service()
        except FileNotFoundError:
            raise
        except Exception as error:
            print(f"An error occurred: {error}")
            return None

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        payload: Dict[str, Any] = {'raw': encoded_message}
        if thread_id:
            payload['threadId'] = thread_id

        try:
            sent = (
                self.gmail_service.users()
                .messages()
                .send(userId='me', body=payload)
                .execute()
            )
            return sent.get('id')
        except HttpError as error:
            print(f"Gmail send error: {error}")
            return None

    def mark_as_read(self, message_id: str) -> None:
        self._modify_labels(message_id, remove_labels=['UNREAD'])

    def archive_email(self, message_id: str) -> None:
        self._modify_labels(message_id, remove_labels=['INBOX', 'UNREAD'])

    def delete_email(self, message_id: str) -> None:
        try:
            self._ensure_gmail_service()
            self.gmail_service.users().messages().trash(userId='me', id=message_id).execute()
        except HttpError as error:
            print(f"Gmail delete error: {error}")

    def bulk_archive(self, message_ids: Sequence[str]) -> int:
        if not message_ids:
            return 0
        try:
            self._ensure_gmail_service()
            chunk = list(message_ids)
            self.gmail_service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': chunk,
                    'removeLabelIds': ['INBOX', 'UNREAD'],
                },
            ).execute()
            return len(chunk)
        except HttpError as error:
            print(f"Gmail batch error: {error}")
            return 0

    def _modify_labels(
        self,
        message_id: str,
        add_labels: Optional[Sequence[str]] = None,
        remove_labels: Optional[Sequence[str]] = None,
    ) -> None:
        try:
            self._ensure_gmail_service()
            body: Dict[str, Any] = {}
            if add_labels:
                body['addLabelIds'] = list(add_labels)
            if remove_labels:
                body['removeLabelIds'] = list(remove_labels)
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body,
            ).execute()
        except HttpError as error:
            print(f"Gmail label error: {error}")

    # ------------------------------------------------------------------ #
    # Parsing helpers
    # ------------------------------------------------------------------ #
    def bulk_delete(self, message_ids: Sequence[str]) -> int:
        if not message_ids:
            return 0
        try:
            self._ensure_gmail_service()
        except FileNotFoundError:
            raise
        except Exception as error:
            print(f"An error occurred: {error}")
            return 0

        deleted = 0
        for msg_id in message_ids:
            try:
                self.gmail_service.users().messages().trash(userId='me', id=msg_id).execute()
                deleted += 1
            except HttpError as error:
                print(f"Gmail delete error: {error}")
        return deleted

    def _build_message_summary(self, full: Dict[str, Any]) -> Dict[str, Any]:
        payload = full.get('payload', {})
        headers = self._headers_to_dict(payload.get('headers', []))
        from_name, from_email = parseaddr(headers.get('from', ''))
        return {
            'id': full['id'],
            'threadId': full.get('threadId'),
            'subject': headers.get('subject', '(No subject)'),
            'from_name': from_name or from_email or "Unknown sender",
            'from_email': from_email,
            'date': headers.get('date', ''),
            'snippet': full.get('snippet', '').strip(),
        }

    def _headers_to_dict(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
        return {h['name'].lower(): h['value'] for h in headers if 'name' in h and 'value' in h}

    def _extract_plain_body(self, payload: Dict[str, Any]) -> str:
        if not payload:
            return ""

        def _decode(data: str) -> str:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

        mime_type = payload.get('mimeType')
        body = payload.get('body', {})
        data = body.get('data')

        if data and mime_type == 'text/plain':
            return _decode(data).strip()

        parts = payload.get('parts', [])
        for part in parts:
            if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                return _decode(part['body']['data']).strip()
            elif part.get('parts'):
                inner = self._extract_plain_body(part)
                if inner:
                    return inner

        if data:
            return _decode(data).strip()
        return ""


google_integration = GoogleIntegration()

