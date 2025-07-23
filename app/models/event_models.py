from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class EventDateTime(BaseModel):
    """Event date/time model for Google Calendar events"""
    dateTime: Optional[str] = Field(None, description="RFC3339 timestamp for timed events")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format for all-day events")
    timeZone: Optional[str] = Field(None, description="Time zone (e.g., 'America/New_York')")

class EventCreate(BaseModel):
    """Model for creating a new calendar event"""
    summary: str = Field(..., description="Event title", max_length=1024)
    description: Optional[str] = Field(None, description="Event description", max_length=8192)
    location: Optional[str] = Field(None, description="Event location", max_length=1024)
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

class EventUpdate(BaseModel):
    """Model for updating an existing calendar event"""
    summary: Optional[str] = Field(None, description="Event title", max_length=1024)
    description: Optional[str] = Field(None, description="Event description", max_length=8192)
    location: Optional[str] = Field(None, description="Event location", max_length=1024)
    start: Optional[EventDateTime] = Field(None, description="Event start date/time")
    end: Optional[EventDateTime] = Field(None, description="Event end date/time")
    
    class Config:
        schema_extra = {
            "example": {
                "summary": "Updated Team Meeting",
                "description": "Updated weekly team sync meeting",
                "location": "Conference Room B",
                "start": {
                    "dateTime": "2025-07-24T14:00:00Z",
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": "2025-07-24T15:00:00Z",
                    "timeZone": "UTC"
                }
            }
        }

class EventResponse(BaseModel):
    """Model for event response"""
    id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start: dict
    end: dict
    htmlLink: str
    created: str
    updated: str
    status: str
