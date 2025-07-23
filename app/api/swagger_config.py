"""
Swagger/OpenAPI configuration for Calendar Integration API endpoints
"""

from fastapi import status
from app.models.event_models import (
    CalendarIDsResponse, ListEventsResponse, EventResponse,
    ErrorResponse, ValidationErrorResponse
)

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
