"""
Swagger/OpenAPI configuration for Calendar Integration API endpoints
"""

from fastapi import status
from app.models.event_models import (
    CalendarIDsResponse, ListEventsResponse, EventResponse,
    ErrorResponse, ValidationErrorResponse, EventDeleteResponse, EventDeleteRequest,
    EventAlreadyDeletedResponse
)
from app.models.llm_models import LLMFinalResponse, ChatResponse

# Common tag for all endpoints
CALENDAR_TAG = "Calendar API"

# Common error responses for all endpoints
COMMON_ERROR_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "description": "Bad Request"
    },
    401: {
        "model": ErrorResponse,
        "description": "Unauthorized"
    },
    403: {
        "model": ErrorResponse,
        "description": "Forbidden"
    },
    408: {
        "model": ErrorResponse,
        "description": "Request Timeout"
    },
    429: {
        "model": ErrorResponse,
        "description": "Too Many Requests"
    },
    500: {
        "model": ErrorResponse,
        "description": "Internal Server Error"
    },
    503: {
        "model": ErrorResponse,
        "description": "Service Unavailable"
    }
}

# GET /calendar/ids configuration
GET_CALENDAR_IDS_CONFIG = {
    "response_model": CalendarIDsResponse,
    "status_code": status.HTTP_200_OK,
    "responses": {
        200: {
            "model": CalendarIDsResponse,
            "description": "Successfully retrieved calendar IDs"
        },
        **COMMON_ERROR_RESPONSES
    },
    "summary": "Get Calendar IDs",
    "tags": [CALENDAR_TAG]
}

# GET /listevents configuration
LIST_EVENTS_CONFIG = {
    "response_model": ListEventsResponse,
    "status_code": status.HTTP_200_OK,
    "responses": {
        200: {
            "model": ListEventsResponse,
            "description": "Successfully retrieved events"
        },
        404: {
            "model": ErrorResponse,
            "description": "Calendar not found"
        },
        **COMMON_ERROR_RESPONSES
    },
    "summary": "List Calendar Events",
    "tags": [CALENDAR_TAG]
}

# POST /create-event configuration
CREATE_EVENT_CONFIG = {
    "response_model": EventResponse,
    "status_code": status.HTTP_201_CREATED,
    "responses": {
        201: {
            "model": EventResponse,
            "description": "Successfully created calendar event"
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error"
        },
        **COMMON_ERROR_RESPONSES
    },
    "summary": "Create Calendar Event",
    "tags": [CALENDAR_TAG]
}

# DELETE /delete-event/{event_id} configuration
DELETE_EVENT_CONFIG = {
    "response_model": EventDeleteResponse,
    "status_code": status.HTTP_200_OK,
    "responses": {
        200: {
            "model": EventDeleteResponse,
            "description": "Successfully deleted calendar event"
        },
        404: {
            "model": ErrorResponse,
            "description": "Event not found"
        },
        410: {
            "model": EventAlreadyDeletedResponse,
            "description": "Event has already been deleted"
        },
        **COMMON_ERROR_RESPONSES
    },
    "summary": "Delete Calendar Event",
    "tags": [CALENDAR_TAG]
}

# POST /delete-event configuration (alternative with request body)
DELETE_EVENT_BODY_CONFIG = {
    "response_model": EventDeleteResponse,
    "status_code": status.HTTP_200_OK,
    "responses": {
        200: {
            "model": EventDeleteResponse,
            "description": "Successfully deleted calendar event"
        },
        404: {
            "model": ErrorResponse,
            "description": "Event not found"
        },
        410: {
            "model": EventAlreadyDeletedResponse,
            "description": "Event has already been deleted"
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error"
        },
        **COMMON_ERROR_RESPONSES
    },
    "summary": "Delete Calendar Event (Request Body)",
    "tags": [CALENDAR_TAG]
}

# POST /chat configuration
CHAT_CONFIG = {
    "response_model": ChatResponse,
    "status_code": status.HTTP_200_OK,
    "responses": {
        200: {
            "model": ChatResponse,
            "description": "Successful chat response with executed calendar operation",
            "content": {
                "application/json": {
                    "examples": {
                        "create_event_with_attendees": {
                            "summary": "Create event with attendees",
                            "value": {
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
                            }
                        },
                        "get_events": {
                            "summary": "Get calendar events",
                            "value": {
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
                                            "end": {"dateTime": "2025-07-28T15:00:00Z"},
                                            "location": "Conference Room A"
                                        }
                                    ],
                                    "count": 1,
                                    "message": "Events retrieved successfully"
                                },
                                "timestamp": "2025-07-27T12:30:00Z"
                            }
                        }
                    }
                }
            }
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error"
        },
        **COMMON_ERROR_RESPONSES
    },
    
    "tags": [CALENDAR_TAG]
}
