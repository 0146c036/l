import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import GOOGLE_TOKEN_JSON, logger

def get_calendar_service():
    """
    Authenticate and build the Google Calendar service.
    First checks the environment variable GOOGLE_TOKEN_JSON, then looks for token.json on disk.
    """
    creds = None
    
    # 1. Try to load from GOOGLE_TOKEN_JSON environment variable (cloud-friendly)
    if GOOGLE_TOKEN_JSON:
        try:
            logger.info("Attempting to load Google credentials from environment variable...")
            creds_data = json.loads(GOOGLE_TOKEN_JSON)
            creds = Credentials.from_authorized_user_info(creds_data)
        except Exception as e:
            logger.error(f"Failed to load credentials from GOOGLE_TOKEN_JSON environment variable: {e}")
            
    # 2. Try to load from local token.json file (local testing)
    if not creds and os.path.exists("token.json"):
        try:
            logger.info("Attempting to load Google credentials from local token.json file...")
            creds = Credentials.from_authorized_user_file("token.json")
        except Exception as e:
            logger.error(f"Failed to load credentials from token.json file: {e}")
            
    # Validate credentials and refresh if expired
    if creds:
        try:
            if creds.expired and creds.refresh_token:
                logger.info("Google credentials expired, attempting to refresh...")
                creds.refresh(Request())
        except Exception as e:
            logger.error(f"Failed to refresh Google credentials: {e}")
            creds = None
            
    if not creds:
        logger.warning("No valid Google Calendar credentials found. Skipping Google Calendar integration.")
        return None
        
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to build Google Calendar service client: {e}")
        return None

def create_calendar_event(title, date_str, time_str, location):
    """
    Create a new event on the user's primary Google Calendar.
    Default duration is set to 1 hour.
    """
    service = get_calendar_service()
    if not service:
        logger.warning("Google Calendar service is unavailable. Skipping event creation.")
        return None
        
    try:
        # Parse start time
        start_time_str = f"{date_str}T{time_str}:00"
        start_dt = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S")
        
        # Default duration is 1 hour
        end_dt = start_dt + timedelta(hours=1)
        end_time_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
        
        event = {
            "summary": title,
            "location": location if location else "未設定地點",
            "description": "此行程由互動式 LINE 自動提醒機器人建立。",
            "start": {
                "dateTime": start_time_str,
                "timeZone": "Asia/Taipei",
            },
            "end": {
                "dateTime": end_time_str,
                "timeZone": "Asia/Taipei",
            },
            "reminders": {
                "useDefault": True,
            },
        }
        
        created_event = service.events().insert(calendarId="primary", body=event).execute()
        event_id = created_event.get("id")
        html_link = created_event.get("htmlLink")
        logger.info(f"Google Calendar event created successfully! ID: {event_id}. Link: {html_link}")
        return event_id
        
    except Exception as e:
        logger.error(f"Error creating Google Calendar event: {e}", exc_info=True)
        return None
