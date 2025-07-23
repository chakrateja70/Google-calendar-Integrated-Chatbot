"""
HTTP status codes and messages for consistent API responses.
"""

from enum import Enum
from typing import Dict, Union


class HTTPStatus(Enum):
    """HTTP status codes commonly used in the application"""
    
    # Success codes
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    
    # Client error codes
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Server error codes
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class ErrorMessages:
    """Standard error messages for consistent responses"""
    
    # Authentication and Authorization
    UNAUTHORIZED = "Unauthorized: Invalid or expired token"
    FORBIDDEN_CALENDAR_LIST = "Forbidden: Insufficient permissions to access calendar list"
    FORBIDDEN_CALENDAR = "Forbidden: Insufficient permissions to access calendar"
    FORBIDDEN_CREATE_EVENTS = "Forbidden: Insufficient permissions to create events"
    FORBIDDEN_UPDATE_EVENTS = "Forbidden: Insufficient permissions to update events"
    
    # Resource Not Found
    CALENDAR_NOT_FOUND = "Calendar not found"
    CALENDAR_LIST_NOT_FOUND = "Calendar list not found"
    EVENT_NOT_FOUND = "Event with ID '{}' not found"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again later"
    
    # Request Errors
    BAD_REQUEST = "Bad Request: Invalid event data"
    INVALID_DATA = "Invalid data provided"
    MISSING_REQUIRED_FIELDS = "Missing required fields: {}"
    
    # Timeout and Connection
    REQUEST_TIMEOUT_CALENDAR = "Request timeout: Google Calendar API took too long to respond"
    CONNECTION_ERROR_CALENDAR = "Service unavailable: Unable to connect to Google Calendar API"
    
    # Generic Errors
    INTERNAL_ERROR = "Internal server error occurred"
    SERVICE_UNAVAILABLE = "Service unavailable"
    VALIDATION_ERROR = "Data validation failed"
    
    # Success Messages
    CALENDAR_IDS_SUCCESS = "Calendar IDs retrieved successfully"
    EVENTS_SUCCESS = "Events retrieved successfully"
    EVENT_CREATED_SUCCESS = "Event created successfully"
    EVENT_UPDATED_SUCCESS = "Event updated successfully"
    EVENT_DELETED_SUCCESS = "Event deleted successfully"


class GoogleCalendarAPIMessages:
    """Specific error messages for Google Calendar API responses"""
    
    # Common API error patterns
    GOOGLE_API_ERROR = "Google Calendar API error: {}"
    REQUEST_ERROR = "Request error: {}"
    
    # Service-specific errors
    SERVICE_CREATION_FAILED = "Service creation failed: {}"
    EVENT_CREATION_FAILED = "Event creation failed: {}"
    EVENT_UPDATE_FAILED = "Event update failed: {}"
    EVENT_DELETION_FAILED = "Event deletion failed: {}"
    
    # Authentication-specific
    TOKEN_REFRESH_FAILED = "Token refresh failed: {}"
    OAUTH_FLOW_FAILED = "OAuth flow failed: {}"
    INVALID_TOKEN = "Invalid token.json: {}"
    MISSING_CREDENTIALS = "Missing credentials.json"


def get_error_message(status_code: int, context: str = None) -> str:
    """
    Get appropriate error message based on status code and context
    
    Args:
        status_code (int): HTTP status code
        context (str): Additional context for the error
    
    Returns:
        str: Appropriate error message
    """
    error_map = {
        400: ErrorMessages.BAD_REQUEST,
        401: ErrorMessages.UNAUTHORIZED,
        403: ErrorMessages.FORBIDDEN_CALENDAR,
        404: ErrorMessages.CALENDAR_NOT_FOUND,
        408: ErrorMessages.REQUEST_TIMEOUT_CALENDAR,
        429: ErrorMessages.RATE_LIMIT_EXCEEDED,
        500: ErrorMessages.INTERNAL_ERROR,
        503: ErrorMessages.SERVICE_UNAVAILABLE,
    }
    
    base_message = error_map.get(status_code, ErrorMessages.INTERNAL_ERROR)
    
    if context:
        return f"{base_message} - {context}"
    
    return base_message


def get_success_message(operation: str, resource: str = None) -> str:
    """
    Get appropriate success message based on operation
    
    Args:
        operation (str): The operation performed (create, update, delete, get, list)
        resource (str): The resource type (event, calendar, etc.)
    
    Returns:
        str: Appropriate success message
    """
    success_map = {
        "create": "created successfully",
        "update": "updated successfully", 
        "delete": "deleted successfully",
        "get": "retrieved successfully",
        "list": "retrieved successfully"
    }
    
    action = success_map.get(operation.lower(), "processed successfully")
    
    if resource:
        return f"{resource.title()} {action}"
    
    return f"Operation {action}"
