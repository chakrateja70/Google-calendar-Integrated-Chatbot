from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from enum import Enum

class ActionType(str, Enum):
    """Enum for different action types the LLM can identify"""
    CREATE_EVENT = "create_event"
    UPDATE_EVENT = "update_event"
    GET_EVENTS = "get_events"
    UNKNOWN = "unknown"

class LLMPromptRequest(BaseModel):
    """Model for incoming user prompt requests"""
    prompt: str = Field(..., description="Natural language prompt from user", max_length=2048)
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "Create an event for 10-11AM I'm in 11th class"
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
