import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import HTTPException, status
from app.core.calendar_auth import get_google_credentials
from app.models.event_models import (
    CalendarIDsResponse, ListEventsResponse, EventItem, 
    DefaultReminder, CalendarListItem, EventCreate, EventResponse
)
from app.utils.error_handler import APIErrorHandler, create_success_response
from app.core.exceptions import InternalServerError, ResourceNotFoundError
from app.core.status_codes import ErrorMessages, GoogleCalendarAPIMessages

def get_calendar_service():
    creds = get_google_credentials()
    try:
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        raise InternalServerError(
            detail=GoogleCalendarAPIMessages.SERVICE_CREATION_FAILED.format(str(e)),
            error_message="Failed to initialize Google Calendar service"
        )

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
        raise InternalServerError(
            detail=GoogleCalendarAPIMessages.EVENT_CREATION_FAILED.format(str(e)),
            error_message="Failed to create calendar event"
        )

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
            raise ResourceNotFoundError(ErrorMessages.EVENT_NOT_FOUND.format(event_id))
        raise HTTPException(status_code=e.resp.status, detail=f"Failed to update event: {e}")
    except Exception as e:
        raise InternalServerError(
            detail=GoogleCalendarAPIMessages.EVENT_UPDATE_FAILED.format(str(e)),
            error_message="Failed to update calendar event"
        )


def get_calendar_ids_service(token: str) -> CalendarIDsResponse:
    """
    Get list of all accessible calendar IDs using REST API
    
    Args:
        token (str): Google OAuth access token
    
    Returns:
        CalendarIDsResponse: Structured response with calendar list
    """
    try:
        # Build the URL and headers
        url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        # Make API request with centralized error handling
        response = APIErrorHandler.make_google_api_request(
            url=url,
            headers=headers,
            method="GET",
            timeout=30,
            operation_context="Get calendar IDs"
        )
        
        data = response.json()
        
        # Transform the response to match our model
        transformed_response = CalendarIDsResponse(
            kind=data.get("kind", "calendar#calendarList"),
            etag=data.get("etag"),
            nextPageToken=data.get("nextPageToken"),
            nextSyncToken=data.get("nextSyncToken"),
            items=[
                CalendarListItem(
                    id=item.get("id"),
                    summary=item.get("summary"),
                    description=item.get("description"),
                    timeZone=item.get("timeZone"),
                    colorId=item.get("colorId"),
                    backgroundColor=item.get("backgroundColor"),
                    foregroundColor=item.get("foregroundColor"),
                    accessRole=item.get("accessRole"),
                    primary=item.get("primary"),
                    selected=item.get("selected")
                )
                for item in data.get("items", [])
            ],
            count=len(data.get("items", [])),
            message=ErrorMessages.CALENDAR_IDS_SUCCESS
        )
        
        return transformed_response
        
    except HTTPException:
        # Re-raise HTTPExceptions as they are already properly formatted
        raise
    except Exception as e:
        raise InternalServerError(
            detail=f"Failed to get calendar IDs: {str(e)}",
            error_message="Failed to retrieve calendar list"
        )


def list_events_service(token: str) -> ListEventsResponse:
    """
    List events from primary calendar using REST API
    
    Args:
        token (str): Google OAuth access token
    
    Returns:
        ListEventsResponse: Structured response with events list
    """
    try:
        # Build the URL and headers
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        # Make API request with centralized error handling
        response = APIErrorHandler.make_google_api_request(
            url=url,
            headers=headers,
            method="GET",
            timeout=30,
            operation_context="List events"
        )
        
        data = response.json()
        
        # Transform the response to match our model
        transformed_response = ListEventsResponse(
            kind=data.get("kind", "calendar#events"),
            etag=data.get("etag"),
            summary=data.get("summary"),
            description=data.get("description"),
            updated=data.get("updated"),
            timeZone=data.get("timeZone"),
            accessRole=data.get("accessRole"),
            defaultReminders=[
                DefaultReminder(method=reminder["method"], minutes=reminder["minutes"])
                for reminder in data.get("defaultReminders", [])
            ],
            nextPageToken=data.get("nextPageToken"),
            nextSyncToken=data.get("nextSyncToken"),
            items=[
                EventItem(
                    id=item.get("id"),
                    summary=item.get("summary"),
                    description=item.get("description"),
                    location=item.get("location"),
                    start=item.get("start"),
                    end=item.get("end"),
                    htmlLink=item.get("htmlLink"),
                    created=item.get("created"),
                    updated=item.get("updated"),
                    status=item.get("status"),
                    organizer=item.get("organizer"),
                    attendees=item.get("attendees"),
                    recurrence=item.get("recurrence"),
                    reminders=item.get("reminders")
                )
                for item in data.get("items", [])
            ],
            count=len(data.get("items", [])),
            message=ErrorMessages.EVENTS_SUCCESS
        )
        
        return transformed_response
        
    except HTTPException:
        # Re-raise HTTPExceptions as they are already properly formatted
        raise
    except Exception as e:
        raise InternalServerError(
            detail=f"Failed to list events: {str(e)}",
            error_message="Failed to retrieve calendar events"
        )


def create_event_service(token: str, event_data: EventCreate) -> EventResponse:
    """
    Create a new event in Google Calendar using REST API
    
    Args:
        token (str): Google OAuth access token
        event_data (EventCreate): Event data to create
    
    Returns:
        EventResponse: Created event data
    """
    try:
        # Build the URL and headers
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Convert Pydantic model to dict for API request
        event_body = {
            "summary": event_data.summary,
            "start": event_data.start.dict(exclude_none=True),
            "end": event_data.end.dict(exclude_none=True)
        }
        
        # Add optional fields if provided
        if event_data.description:
            event_body["description"] = event_data.description
        if event_data.location:
            event_body["location"] = event_data.location
        
        # Make API request with centralized error handling
        response = APIErrorHandler.make_google_api_request(
            url=url,
            headers=headers,
            method="POST",
            json_data=event_body,
            timeout=30,
            operation_context="Create event"
        )
        
        data = response.json()
        
        # Transform the response to match our model
        event_response = EventResponse(
            id=data.get("id"),
            summary=data.get("summary"),
            description=data.get("description"),
            location=data.get("location"),
            start=data.get("start"),
            end=data.get("end"),
            htmlLink=data.get("htmlLink"),
            created=data.get("created"),
            updated=data.get("updated"),
            status=data.get("status")
        )
        
        return event_response
        
    except HTTPException:
        # Re-raise HTTPExceptions as they are already properly formatted
        raise
    except Exception as e:
        raise InternalServerError(
            detail=GoogleCalendarAPIMessages.EVENT_CREATION_FAILED.format(str(e)),
            error_message="Failed to create calendar event"
        )