from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class CalendarListItem(BaseModel):
    """Model for individual calendar item"""
    id: str = Field(..., description="Calendar ID", example="primary")
    summary: Optional[str] = Field(None, description="Calendar title", example="My Calendar")
    description: Optional[str] = Field(None, description="Calendar description", example="Personal calendar for events")
    timeZone: Optional[str] = Field(None, description="Calendar timezone", example="UTC")
    colorId: Optional[str] = Field(None, description="Calendar color ID", example="1")
    backgroundColor: Optional[str] = Field(None, description="Background color", example="#3174F1")
    foregroundColor: Optional[str] = Field(None, description="Foreground color", example="#FFFFFF")
    accessRole: Optional[str] = Field(None, description="User's access role", example="owner")
    primary: Optional[bool] = Field(None, description="Whether this is the primary calendar", example=True)
    selected: Optional[bool] = Field(None, description="Whether calendar is selected", example=True)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "primary",
                "summary": "My Calendar",
                "description": "Personal calendar for events",
                "timeZone": "UTC",
                "colorId": "1",
                "backgroundColor": "#3174F1",
                "foregroundColor": "#FFFFFF",
                "accessRole": "owner",
                "primary": True,
                "selected": True
            }
        }

class CalendarIDsResponse(BaseModel):
    """Model for calendar list response"""
    kind: str = Field("calendar#calendarList", description="Resource type", example="calendar#calendarList")
    etag: Optional[str] = Field(None, description="ETag of the collection", example="\"p33g-uP7XcQh6v_cztmGnhV2_lk/abc123\"")
    nextPageToken: Optional[str] = Field(None, description="Next page token", example="abc123nextpage")
    nextSyncToken: Optional[str] = Field(None, description="Next sync token", example="xyz789sync")
    items: List[CalendarListItem] = Field([], description="List of calendars")
    count: int = Field(0, description="Number of calendars returned", example=3)
    message: str = Field("Calendar IDs retrieved successfully", description="Response message", example="Calendar IDs retrieved successfully")
    
    class Config:
        schema_extra = {
            "example": {
                "kind": "calendar#calendarList",
                "etag": "\"p33g-uP7XcQh6v_cztmGnhV2_lk/abc123\"",
                "nextPageToken": "abc123nextpage",
                "nextSyncToken": "xyz789sync",
                "items": [
                    {
                        "id": "primary",
                        "summary": "My Calendar",
                        "description": "Personal calendar for events",
                        "timeZone": "UTC",
                        "accessRole": "owner",
                        "primary": True,
                        "selected": True
                    }
                ],
                "count": 1,
                "message": "Calendar IDs retrieved successfully"
            }
        }

class DefaultReminder(BaseModel):
    """Model for default reminder"""
    method: str = Field(..., description="Reminder method", example="popup")
    minutes: int = Field(..., description="Minutes before event", ge=0, le=40320, example=15)
    
    class Config:
        schema_extra = {
            "example": {
                "method": "popup",
                "minutes": 15
            }
        }

class EventItem(BaseModel):
    """Model for individual event item"""
    id: Optional[str] = Field(None, description="Event ID", example="abc123def456ghi789")
    summary: Optional[str] = Field(None, description="Event title", example="Weekly Stand-up")
    description: Optional[str] = Field(None, description="Event description", example="Weekly team stand-up meeting")
    location: Optional[str] = Field(None, description="Event location", example="Meeting Room B")
    start: Optional[Dict] = Field(None, description="Event start time", example={"dateTime": "2025-07-25T09:00:00Z", "timeZone": "UTC"})
    end: Optional[Dict] = Field(None, description="Event end time", example={"dateTime": "2025-07-25T09:30:00Z", "timeZone": "UTC"})
    created: Optional[str] = Field(None, description="Creation time", example="2025-07-23T08:00:00Z")
    updated: Optional[str] = Field(None, description="Last update time", example="2025-07-23T08:00:00Z")
    status: Optional[str] = Field(None, description="Event status", example="confirmed")
    organizer: Optional[Dict] = Field(None, description="Event organizer", example={"email": "organizer@example.com", "displayName": "John Doe"})
    attendees: Optional[List[Dict]] = Field(None, description="Event attendees", example=[{"email": "attendee@example.com", "displayName": "Jane Smith", "responseStatus": "accepted"}])
    recurrence: Optional[List[str]] = Field(None, description="Recurrence rules", example=["RRULE:FREQ=WEEKLY;BYDAY=MO"])
    reminders: Optional[Dict] = Field(None, description="Event reminders", example={"useDefault": True})
    
    class Config:
        schema_extra = {
            "example": {
                "id": "abc123def456ghi789",
                "summary": "Weekly Stand-up",
                "description": "Weekly team stand-up meeting",
                "location": "Meeting Room B",
                "start": {
                    "dateTime": "2025-07-25T09:00:00Z",
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": "2025-07-25T09:30:00Z",
                    "timeZone": "UTC"
                },
                "created": "2025-07-23T08:00:00Z",
                "updated": "2025-07-23T08:00:00Z",
                "status": "confirmed",
                "organizer": {
                    "email": "organizer@example.com",
                    "displayName": "John Doe"
                },
                "attendees": [
                    {
                        "email": "attendee@example.com",
                        "displayName": "Jane Smith",
                        "responseStatus": "accepted"
                    }
                ],
                "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO"],
                "reminders": {
                    "useDefault": True
                }
            }
        }

class ListEventsResponse(BaseModel):
    """Model for list events response"""
    kind: str = Field("calendar#events", description="Resource type", example="calendar#events")
    summary: Optional[str] = Field(None, description="Calendar title", example="My Calendar")
    description: Optional[str] = Field(None, description="Calendar description", example="Personal calendar for events")
    updated: Optional[str] = Field(None, description="Last modification time", example="2025-07-23T10:30:00Z")
    timeZone: Optional[str] = Field(None, description="Calendar time zone", example="UTC")
    accessRole: Optional[str] = Field(None, description="User's access role", example="owner")
    defaultReminders: Optional[List[DefaultReminder]] = Field(None, description="Default reminders")
    nextPageToken: Optional[str] = Field(None, description="Next page token", example="abc123nextpage")
    nextSyncToken: Optional[str] = Field(None, description="Next sync token", example="xyz789sync")
    items: List[EventItem] = Field([], description="List of events")
    count: int = Field(0, description="Number of events returned", example=5)
    message: str = Field("Events retrieved successfully", description="Response message", example="Events retrieved successfully")
    
    class Config:
        schema_extra = {
            "example": {
                "kind": "calendar#events",
                "summary": "My Calendar",
                "description": "Personal calendar for events",
                "updated": "2025-07-23T10:30:00Z",
                "timeZone": "UTC",
                "accessRole": "owner",
                "defaultReminders": [
                    {
                        "method": "popup",
                        "minutes": 15
                    }
                ],
                "nextPageToken": "abc123nextpage",
                "nextSyncToken": "xyz789sync",
                "items": [
                    {
                        "id": "abc123def456ghi789",
                        "summary": "Weekly Stand-up",
                        "description": "Weekly team stand-up meeting",
                        "location": "Meeting Room B",
                        "start": {
                            "dateTime": "2025-07-25T09:00:00Z",
                            "timeZone": "UTC"
                        },
                        "end": {
                            "dateTime": "2025-07-25T09:30:00Z",
                            "timeZone": "UTC"
                        },
                        "created": "2025-07-23T08:00:00Z",
                        "updated": "2025-07-23T08:00:00Z",
                        "status": "confirmed"
                    }
                ],
                "count": 1,
                "message": "Events retrieved successfully"
            }
        }


class EventDateTime(BaseModel):
    """Event date/time model for Google Calendar events"""
    dateTime: Optional[str] = Field(None, description="RFC3339 timestamp for timed events", example="2025-07-24T10:00:00Z")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format for all-day events", example="2025-07-24")
    timeZone: Optional[str] = Field(None, description="Time zone (e.g., 'America/New_York')", example="UTC")
    
    class Config:
        schema_extra = {
            "example": {
                "dateTime": "2025-07-24T10:00:00Z",
                "timeZone": "UTC"
            }
        }


class EventCreate(BaseModel):
    """Model for creating a new calendar event"""
    summary: str = Field(..., description="Event title", max_length=1024, example="Team Meeting")
    description: Optional[str] = Field(None, description="Event description", max_length=8192, example="Weekly team sync meeting")
    location: Optional[str] = Field(None, description="Event location", max_length=1024, example="Conference Room A")
    start: EventDateTime = Field(..., description="Event start date/time")
    end: EventDateTime = Field(..., description="Event end date/time")
    
    class Config:
        schema_extra = {
            "example": {
                "summary": "Team Meeting",
                "description": "Weekly team sync meeting",
                "location": "Conference Room A",
                "start": {
                    "dateTime": "2025-07-24T10:00:00Z",
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": "2025-07-24T11:00:00Z",
                    "timeZone": "UTC"
                }
            }
        }


class EventResponse(BaseModel):
    """Model for event response"""
    id: str = Field(..., description="Event ID", example="abc123def456ghi789")
    summary: str = Field(..., description="Event title", example="Team Meeting")
    description: Optional[str] = Field(None, description="Event description", example="Weekly team sync meeting")
    location: Optional[str] = Field(None, description="Event location", example="Conference Room A")
    start: Dict = Field(..., description="Event start time", example={"dateTime": "2025-07-24T10:00:00Z", "timeZone": "UTC"})
    end: Dict = Field(..., description="Event end time", example={"dateTime": "2025-07-24T11:00:00Z", "timeZone": "UTC"})
    htmlLink: str = Field(..., description="Event HTML link", example="https://www.google.com/calendar/event?eid=abc123def456ghi789")
    created: str = Field(..., description="Creation time", example="2025-07-23T08:30:00Z")
    updated: str = Field(..., description="Last update time", example="2025-07-23T08:30:00Z")
    status: str = Field(..., description="Event status", example="confirmed")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "abc123def456ghi789",
                "summary": "Team Meeting",
                "description": "Weekly team sync meeting",
                "location": "Conference Room A",
                "start": {
                    "dateTime": "2025-07-24T10:00:00Z",
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": "2025-07-24T11:00:00Z",
                    "timeZone": "UTC"
                },
                "htmlLink": "https://www.google.com/calendar/event?eid=abc123def456ghi789",
                "created": "2025-07-23T08:30:00Z",
                "updated": "2025-07-23T08:30:00Z",
                "status": "confirmed"
            }
        }
