import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import HTTPException, status
from app.core.calendar_auth import get_google_credentials

def get_calendar_service():
    creds = get_google_credentials()
    try:
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service creation failed: {str(e)}")

def list_upcoming_events(max_results=10):
    service = get_calendar_service()
    now = datetime.datetime.utcnow().isoformat() + "Z"

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        return events_result.get("items", [])
    except HttpError as e:
        raise HTTPException(status_code=e.resp.status, detail=f"Google API error: {e}")

def create_event(event_data):
    """
    Create a new event in Google Calendar
    
    Args:
        event_data (dict): Event data containing summary, start, end, description, location, etc.
    
    Returns:
        dict: Created event data from Google Calendar API
    """
    service = get_calendar_service()
    
    try:
        # Create the event
        event = service.events().insert(
            calendarId="primary",
            body=event_data
        ).execute()
        
        return event
    except HttpError as e:
        raise HTTPException(status_code=e.resp.status, detail=f"Failed to create event: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event creation failed: {str(e)}")

def update_event(event_id, event_data):
    """
    Update an existing event in Google Calendar
    
    Args:
        event_id (str): The ID of the event to update
        event_data (dict): Updated event data containing summary, start, end, description, location, etc.
    
    Returns:
        dict: Updated event data from Google Calendar API
    """
    service = get_calendar_service()
    
    try:
        # First, get the existing event to ensure it exists
        existing_event = service.events().get(
            calendarId="primary",
            eventId=event_id
        ).execute()
        
        # Update the event with new data
        updated_event = service.events().update(
            calendarId="primary",
            eventId=event_id,
            body=event_data
        ).execute()
        
        return updated_event
    except HttpError as e:
        if e.resp.status == 404:
            raise HTTPException(status_code=404, detail=f"Event with ID '{event_id}' not found")
        raise HTTPException(status_code=e.resp.status, detail=f"Failed to update event: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event update failed: {str(e)}")
