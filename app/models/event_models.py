from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict

# Error Response Models
class ErrorResponse(BaseModel):
    """Standard error response model"""
    statusCode: int = Field(..., description="HTTP status code", example=400)
    errorMessage: str = Field(..., description="Human-readable error message", example="Invalid request data provided")
    statusMessage: str = Field(..., description="HTTP status message", example="Bad Request")
    detail: str = Field(..., description="Detailed error information", example="Create event: Bad Request: Invalid event data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "statusCode": 400,
                "errorMessage": "Invalid request data provided",
                "statusMessage": "Bad Request",
                "detail": "Create event: Bad Request: Invalid event data"
            }
        }

class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    statusCode: int = Field(422, description="HTTP status code")
    errorMessage: str = Field("Validation failed", description="Error message")
    statusMessage: str = Field("Unprocessable Entity", description="HTTP status message")
    detail: List[Dict] = Field(..., description="Validation error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "statusCode": 422,
                "errorMessage": "Validation failed",
                "statusMessage": "Unprocessable Entity",
                "detail": [
                    {
                        "loc": ["body", "start", "dateTime"],
                        "msg": "field required",
                        "type": "value_error.missing"
                    }
                ]
            }
        }

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
        json_schema_extra = {
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
        json_schema_extra = {
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
        json_schema_extra = {
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
        json_schema_extra = {
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
        json_schema_extra = {
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
    
    @model_validator(mode='after')
    def validate_datetime_or_date(self):
        """Validate that either dateTime or date is provided"""
        if not self.dateTime and not self.date:
            raise ValueError("Either 'dateTime' or 'date' must be provided")
        # Google Calendar API requires either dateTime OR date, not both
        if self.dateTime and self.date:
            raise ValueError("Cannot specify both 'dateTime' and 'date'")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "dateTime": "2025-07-24T10:00:00Z",
                "timeZone": "UTC"
            }
        }


class Attendee(BaseModel):
    """Model for event attendee"""
    email: str = Field(..., description="Attendee email address", example="attendee@example.com")
    displayName: Optional[str] = Field(None, description="Attendee display name", example="John Doe")
    responseStatus: Optional[str] = Field("needsAction", description="Response status", example="needsAction")
    comment: Optional[str] = Field(None, description="Attendee comment", example="Looking forward to the meeting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "attendee@example.com",
                "displayName": "John Doe",
                "responseStatus": "needsAction"
            }
        }


class EventCreate(BaseModel):
    """Model for creating a new calendar event"""
    summary: str = Field(..., description="Event title", max_length=1024, example="Team Meeting")
    description: Optional[str] = Field(None, description="Event description", max_length=8192, example="Weekly team sync meeting")
    location: Optional[str] = Field(None, description="Event location", max_length=1024, example="Conference Room A")
    start: EventDateTime = Field(..., description="Event start date/time")
    end: EventDateTime = Field(..., description="Event end date/time")
    attendees: Optional[List[Attendee]] = Field(
        None, 
        description="Event attendees - Optional field. If provided, invitations will be sent to all attendees.", 
        example=[],
        title="Attendees (Optional)"
    )
    
    class Config:
        json_schema_extra = {
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
                },
                "attendees": [
                    {
                        "email": "john.doe@example.com",
                        "displayName": "John Doe"
                    },
                    {
                        "email": "jane.smith@example.com",
                        "displayName": "Jane Smith"
                    }
                ]
            },
            "description": "Create a new calendar event. The 'attendees' field is optional - omit it to create an event without attendees."
        }


class EventResponse(BaseModel):
    """Model for event response"""
    id: str = Field(..., description="Event ID", example="abc123def456ghi789")
    summary: str = Field(..., description="Event title", example="Team Meeting")
    description: Optional[str] = Field(None, description="Event description", example="Weekly team sync meeting")
    location: Optional[str] = Field(None, description="Event location", example="Conference Room A")
    start: Dict = Field(..., description="Event start time", example={"dateTime": "2025-07-24T10:00:00Z", "timeZone": "UTC"})
    end: Dict = Field(..., description="Event end time", example={"dateTime": "2025-07-24T11:00:00Z", "timeZone": "UTC"})
    attendees: Optional[List[Dict]] = Field(None, description="List of event attendees")
    htmlLink: str = Field(..., description="Event HTML link", example="https://www.google.com/calendar/event?eid=abc123def456ghi789")
    created: str = Field(..., description="Creation time", example="2025-07-23T08:30:00Z")
    updated: str = Field(..., description="Last update time", example="2025-07-23T08:30:00Z")
    status: str = Field(..., description="Event status", example="confirmed")
    
    class Config:
        json_schema_extra = {
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
                "attendees": [
                    {
                        "email": "john.doe@example.com",
                        "displayName": "John Doe",
                        "responseStatus": "accepted"
                    },
                    {
                        "email": "jane.smith@example.com", 
                        "displayName": "Jane Smith",
                        "responseStatus": "needsAction"
                    }
                ],
                "htmlLink": "https://www.google.com/calendar/event?eid=abc123def456ghi789",
                "created": "2025-07-23T08:30:00Z",
                "updated": "2025-07-23T08:30:00Z",
                "status": "confirmed"
            }
        }


class EventDeleteResponse(BaseModel):
    """Model for event deletion response"""
    message: str = Field(..., description="Success message", example="Event deleted successfully")
    eventId: str = Field(..., description="ID of the deleted event", example="abc123def456ghi789")
    deleted: bool = Field(True, description="Deletion confirmation", example=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Event deleted successfully",
                "eventId": "abc123def456ghi789",
                "deleted": True
            }
        }


class EventAlreadyDeletedResponse(BaseModel):
    """Model for event already deleted response"""
    statusCode: int = Field(410, description="HTTP status code")
    errorMessage: str = Field("Event has already been deleted", description="Error message")
    statusMessage: str = Field("Gone", description="HTTP status message")
    detail: str = Field(..., description="Detailed error information")
    eventId: str = Field(..., description="ID of the already deleted event")
    
    class Config:
        json_schema_extra = {
            "example": {
                "statusCode": 410,
                "errorMessage": "Event has already been deleted",
                "statusMessage": "Gone", 
                "detail": "Delete event: Event has already been deleted",
                "eventId": "abc123def456ghi789"
            }
        }


class EventDeleteRequest(BaseModel):
    """Model for event deletion request"""
    event_id: str = Field(..., description="ID of the event to delete", example="abc123def456ghi789")
    send_updates: str = Field(
        default="all",
        description="Notification setting for guests",
        pattern="^(all|externalOnly|none)$",
        example="all"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "abc123def456ghi789",
                "send_updates": "all"
            }
        }
