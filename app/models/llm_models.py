from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List
from enum import Enum

class ActionType(str, Enum):
    """Enum for different action types the LLM can identify"""
    CREATE_EVENT = "create_event"
    UPDATE_EVENT = "update_event"
    DELETE_EVENT = "delete_event"
    GET_EVENTS = "get_events"
    UNKNOWN = "unknown"

class AttendeeData(BaseModel):
    """Model for attendee information"""
    name: str = Field(..., description="Attendee name")
    email: str = Field(..., description="Attendee email address")

class LLMPromptRequest(BaseModel):
    """Model for incoming user prompt requests"""
    prompt: str = Field(
        ..., 
        description="Natural language prompt from user", 
        max_length=2048,
        examples=[
            "Schedule an interview with Jagadish (tamaranajagadeesh555@gmail.com) tomorrow from 10 AM to 11 AM in Hyderabad",
            "Create an event for 10-11AM I'm in 11th class",
            "Show me my events for today",
            "Book a meeting with John from 2-3PM on Friday in Conference Room A",
            "Update my interview tomorrow to 2PM",
            "Delete my team meeting on July 28",
            "Cancel the testing integration today",
            "Reschedule my appointment to next week"
        ]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Schedule an interview with Jagadish (tamaranajagadeesh555@gmail.com) tomorrow from 10 AM to 11 AM in Hyderabad"
            }
        }

class ParsedEventData(BaseModel):
    """Model for parsed event data from LLM"""
    summary: Optional[str] = Field(None, description="Event title/summary")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    start_time: Optional[str] = Field(None, description="Start time in ISO format")
    end_time: Optional[str] = Field(None, description="End time in ISO format")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format for all-day events")
    timezone: Optional[str] = Field(None, description="Timezone")
    event_id: Optional[str] = Field(None, description="Event ID for updates")
    attendees: Optional[List[AttendeeData]] = Field(None, description="List of event attendees")

class LLMResponse(BaseModel):
    """Model for LLM parsing response"""
    action: ActionType = Field(..., description="Identified action type")
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0, le=1)
    parsed_data: Optional[ParsedEventData] = Field(None, description="Parsed event data if applicable")
    reasoning: str = Field(..., description="LLM reasoning for the decision")
    endpoint: Optional[str] = Field(None, description="Suggested API endpoint")
    method: Optional[Literal["GET", "POST", "PUT"]] = Field(None, description="HTTP method")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "create_event",
                "confidence": 0.95,
                "parsed_data": {
                    "summary": "11th Class",
                    "description": "Class session",
                    "start_time": "2025-07-24T10:00:00Z",
                    "end_time": "2025-07-24T11:00:00Z",
                    "timezone": "UTC"
                },
                "reasoning": "User wants to create an event for a class session from 10-11AM",
                "endpoint": "/events",
                "method": "POST"
            }
        }

class LLMFinalResponse(BaseModel):
    """Model for the final response to user"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable response message")
    llm_analysis: LLMResponse = Field(..., description="LLM analysis details")
    api_response: Optional[Dict[Any, Any]] = Field(None, description="API response if action was executed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully created your 11th class event for 10-11AM today",
                "llm_analysis": {
                    "action": "create_event",
                    "confidence": 0.95,
                    "reasoning": "User wants to create an event for a class session"
                },
                "api_response": {
                    "event": {
                        "id": "event123",
                        "summary": "11th Class",
                        "start": {"dateTime": "2025-07-24T10:00:00Z"}
                    }
                }
            }
        }

class ChatResponse(BaseModel):
    """Model for chat endpoint response matching other endpoint formats"""
    kind: str = Field(default="calendar#chat", description="Resource type")
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable response message")
    action_performed: str = Field(..., description="Action that was performed")
    confidence: float = Field(..., description="LLM confidence score", ge=0, le=1)
    reasoning: str = Field(..., description="LLM reasoning for the decision")
    data: Optional[Dict[Any, Any]] = Field(None, description="Response data from executed operation")
    timestamp: str = Field(..., description="Response timestamp in ISO format")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "kind": "calendar#chat",
                    "success": True,
                    "message": "Successfully created event: Interview with Jagadish with attendees: Jagadish",
                    "action_performed": "create_event",
                    "confidence": 0.95,
                    "reasoning": "User wants to schedule a new interview event with specific time, location, and attendee",
                    "data": {
                        "id": "abc123def456ghi789",
                        "summary": "Interview with Jagadish",
                        "description": "Interview session with Jagadish",
                        "location": "Hyderabad",
                        "start": {
                            "dateTime": "2025-07-28T10:00:00",
                            "timeZone": "Asia/Kolkata"
                        },
                        "end": {
                            "dateTime": "2025-07-28T11:00:00", 
                            "timeZone": "Asia/Kolkata"
                        },
                        "attendees": [
                            {
                                "email": "tamaranajagadeesh555@gmail.com",
                                "displayName": "Jagadish",
                                "responseStatus": "needsAction"
                            }
                        ],
                        "htmlLink": "https://www.google.com/calendar/event?eid=abc123def456ghi789",
                        "created": "2025-07-27T12:30:00Z",
                        "updated": "2025-07-27T12:30:00Z",
                        "status": "confirmed"
                    },
                    "timestamp": "2025-07-27T12:30:00Z"
                },
                {
                    "kind": "calendar#chat",
                    "success": True,
                    "message": "Here are your upcoming events",
                    "action_performed": "get_events",
                    "confidence": 0.98,
                    "reasoning": "User wants to view their calendar events",
                    "data": {
                        "kind": "calendar#events",
                        "items": [
                            {
                                "id": "event123",
                                "summary": "Team Meeting",
                                "start": {"dateTime": "2025-07-28T14:00:00Z"},
                                "end": {"dateTime": "2025-07-28T15:00:00Z"}
                            }
                        ],
                        "count": 1,
                        "message": "Events retrieved successfully"
                    },
                    "timestamp": "2025-07-27T12:30:00Z"
                }
            ]
        }
