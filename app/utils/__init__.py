"""
Common imports and utilities for error handling throughout the application.
This module provides convenient imports to reduce boilerplate code.
"""

# Exception classes
from app.core.exceptions import (
    CalendarAPIException,
    AuthenticationError,
    AuthorizationError, 
    ResourceNotFoundError,
    RateLimitError,
    RequestTimeoutError,
    ServiceUnavailableError,
    BadRequestError,
    InternalServerError,
    ValidationError
)

# Status codes and messages
from app.core.status_codes import (
    HTTPStatus,
    ErrorMessages,
    GoogleCalendarAPIMessages,
    get_error_message,
    get_success_message
)

# Error handling utilities
from app.utils.error_handler import (
    HTTPErrorHandler,
    APIErrorHandler,
    validate_required_fields,
    create_success_response
)

# Commonly used FastAPI imports
from fastapi import HTTPException, status

__all__ = [
    # Exceptions
    'CalendarAPIException',
    'AuthenticationError', 
    'AuthorizationError',
    'ResourceNotFoundError',
    'RateLimitError',
    'RequestTimeoutError', 
    'ServiceUnavailableError',
    'BadRequestError',
    'InternalServerError',
    'ValidationError',
    
    # Status and Messages
    'HTTPStatus',
    'ErrorMessages',
    'GoogleCalendarAPIMessages', 
    'get_error_message',
    'get_success_message',
    
    # Utilities
    'HTTPErrorHandler',
    'APIErrorHandler',
    'validate_required_fields',
    'create_success_response',
    
    # FastAPI
    'HTTPException',
    'status'
]
