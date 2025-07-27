"""
Custom exceptions for the calendar integration application.
"""

from fastapi import HTTPException
from typing import Optional, Dict, Any


class CalendarAPIException(HTTPException):
    """Base exception for Google Calendar API related errors"""
    
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        error_message: str = None,
        status_message: str = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        # Create detailed response body
        error_response = {
            "statusCode": status_code,
            "errorMessage": error_message or detail,
            "statusMessage": status_message or self._get_status_message(status_code),
            "detail": detail  # Keep original detail for backward compatibility
        }
        super().__init__(status_code=status_code, detail=error_response, headers=headers)
    
    def _get_status_message(self, status_code: int) -> str:
        """Get standard HTTP status message"""
        status_messages = {
            400: "Bad Request",
            401: "Unauthorized", 
            403: "Forbidden",
            404: "Not Found",
            408: "Request Timeout",
            410: "Gone",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return status_messages.get(status_code, "Unknown Error")


class AuthenticationError(CalendarAPIException):
    """Exception raised for authentication errors"""
    
    def __init__(self, detail: str = "Authentication failed", error_message: str = None):
        super().__init__(
            status_code=401, 
            detail=detail,
            error_message=error_message or "Invalid or expired authentication token",
            status_message="Unauthorized"
        )


class AuthorizationError(CalendarAPIException):
    """Exception raised for authorization/permission errors"""
    
    def __init__(self, detail: str = "Insufficient permissions", error_message: str = None):
        super().__init__(
            status_code=403, 
            detail=detail,
            error_message=error_message or "Access denied - insufficient permissions",
            status_message="Forbidden"
        )


class ResourceNotFoundError(CalendarAPIException):
    """Exception raised when a resource is not found"""
    
    def __init__(self, detail: str = "Resource not found", error_message: str = None):
        super().__init__(
            status_code=404, 
            detail=detail,
            error_message=error_message or "The requested resource was not found",
            status_message="Not Found"
        )


class RateLimitError(CalendarAPIException):
    """Exception raised when API rate limit is exceeded"""
    
    def __init__(self, detail: str = "Rate limit exceeded. Please try again later", error_message: str = None):
        super().__init__(
            status_code=429, 
            detail=detail,
            error_message=error_message or "API rate limit exceeded",
            status_message="Too Many Requests"
        )


class RequestTimeoutError(CalendarAPIException):
    """Exception raised when request times out"""
    
    def __init__(self, detail: str = "Request timeout: Service took too long to respond", error_message: str = None):
        super().__init__(
            status_code=408, 
            detail=detail,
            error_message=error_message or "Request timed out",
            status_message="Request Timeout"
        )


class ServiceUnavailableError(CalendarAPIException):
    """Exception raised when external service is unavailable"""
    
    def __init__(self, detail: str = "Service unavailable: Unable to connect to external service", error_message: str = None):
        super().__init__(
            status_code=503, 
            detail=detail,
            error_message=error_message or "External service is currently unavailable",
            status_message="Service Unavailable"
        )


class BadRequestError(CalendarAPIException):
    """Exception raised for bad request data"""
    
    def __init__(self, detail: str = "Bad Request: Invalid data provided", error_message: str = None):
        super().__init__(
            status_code=400, 
            detail=detail,
            error_message=error_message or "Invalid request data",
            status_message="Bad Request"
        )


class InternalServerError(CalendarAPIException):
    """Exception raised for internal server errors"""
    
    def __init__(self, detail: str = "Internal server error occurred", error_message: str = None):
        super().__init__(
            status_code=500, 
            detail=detail,
            error_message=error_message or "An internal server error occurred",
            status_message="Internal Server Error"
        )


class ResourceGoneError(CalendarAPIException):
    """Exception raised when a resource has been deleted (410 Gone)"""
    
    def __init__(self, detail: str = "Resource has been deleted", error_message: str = None):
        super().__init__(
            status_code=410, 
            detail=detail,
            error_message=error_message or "The requested resource has been deleted",
            status_message="Gone"
        )


class ValidationError(CalendarAPIException):
    """Exception raised for data validation errors"""
    
    def __init__(self, detail: str = "Data validation failed", error_message: str = None):
        super().__init__(
            status_code=422, 
            detail=detail,
            error_message=error_message or "Data validation failed",
            status_message="Unprocessable Entity"
        )
