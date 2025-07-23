"""
Centralized error handling utilities for HTTP requests and API responses.
"""

import requests
from typing import Dict, Any, Optional, Callable
from fastapi import HTTPException

from app.core.exceptions import (
    AuthenticationError, AuthorizationError, ResourceNotFoundError,
    RateLimitError, RequestTimeoutError, ServiceUnavailableError,
    BadRequestError, InternalServerError
)
from app.core.status_codes import HTTPStatus, ErrorMessages, GoogleCalendarAPIMessages


class HTTPErrorHandler:
    """Centralized HTTP error handling for API requests"""
    
    @staticmethod
    def handle_google_calendar_response(response: requests.Response, operation_context: str = "Google Calendar API") -> None:
        """
        Handle Google Calendar API HTTP response and raise appropriate exceptions
        
        Args:
            response (requests.Response): The HTTP response object
            operation_context (str): Context about the operation being performed
            
        Raises:
            Various CalendarAPIException subclasses based on status code
        """
        if response.status_code == HTTPStatus.OK.value:
            return  # Success, no error handling needed
            
        # Create error detail with context
        error_detail = f"{operation_context}: "
        
        if response.status_code == HTTPStatus.BAD_REQUEST.value:
            error_detail += ErrorMessages.BAD_REQUEST
            raise BadRequestError(
                detail=error_detail,
                error_message="Invalid request data provided"
            )
            
        elif response.status_code == HTTPStatus.UNAUTHORIZED.value:
            error_detail += ErrorMessages.UNAUTHORIZED
            raise AuthenticationError(
                detail=error_detail,
                error_message="Authentication token is invalid or has expired"
            )
            
        elif response.status_code == HTTPStatus.FORBIDDEN.value:
            # Determine specific forbidden context
            if "calendar" in operation_context.lower():
                if "list" in operation_context.lower():
                    error_detail += ErrorMessages.FORBIDDEN_CALENDAR_LIST
                    error_message = "Insufficient permissions to access calendar list"
                elif "create" in operation_context.lower():
                    error_detail += ErrorMessages.FORBIDDEN_CREATE_EVENTS
                    error_message = "Insufficient permissions to create calendar events"
                elif "update" in operation_context.lower():
                    error_detail += ErrorMessages.FORBIDDEN_UPDATE_EVENTS
                    error_message = "Insufficient permissions to update calendar events"
                else:
                    error_detail += ErrorMessages.FORBIDDEN_CALENDAR
                    error_message = "Insufficient permissions to access calendar"
            else:
                error_detail += ErrorMessages.FORBIDDEN_CALENDAR
                error_message = "Access denied - insufficient permissions"
            
            raise AuthorizationError(
                detail=error_detail,
                error_message=error_message
            )
            
        elif response.status_code == HTTPStatus.NOT_FOUND.value:
            if "event" in operation_context.lower():
                error_detail += "Event not found"
                error_message = "The requested event could not be found"
            elif "calendar" in operation_context.lower():
                error_detail += ErrorMessages.CALENDAR_NOT_FOUND
                error_message = "The requested calendar could not be found"
            else:
                error_detail += "Resource not found"
                error_message = "The requested resource could not be found"
            
            raise ResourceNotFoundError(
                detail=error_detail,
                error_message=error_message
            )
            
        elif response.status_code == HTTPStatus.TOO_MANY_REQUESTS.value:
            error_detail += ErrorMessages.RATE_LIMIT_EXCEEDED
            raise RateLimitError(
                detail=error_detail,
                error_message="API rate limit exceeded, please retry after some time"
            )
            
        else:
            # Generic error with response details
            error_detail += GoogleCalendarAPIMessages.GOOGLE_API_ERROR.format(response.text)
            raise InternalServerError(
                detail=error_detail,
                error_message=f"Google Calendar API returned status {response.status_code}"
            )
    
    @staticmethod
    def handle_requests_exceptions(operation_context: str = "API request") -> Callable:
        """
        Decorator to handle common requests exceptions
        
        Args:
            operation_context (str): Context about the operation being performed
            
        Returns:
            Callable: Decorator function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.Timeout:
                    raise RequestTimeoutError(
                        detail=f"{operation_context}: {ErrorMessages.REQUEST_TIMEOUT_CALENDAR}",
                        error_message="The request timed out while waiting for a response"
                    )
                except requests.exceptions.ConnectionError:
                    raise ServiceUnavailableError(
                        detail=f"{operation_context}: {ErrorMessages.CONNECTION_ERROR_CALENDAR}",
                        error_message="Unable to establish connection to the service"
                    )
                except requests.exceptions.RequestException as e:
                    raise InternalServerError(
                        detail=f"{operation_context}: {GoogleCalendarAPIMessages.REQUEST_ERROR.format(str(e))}",
                        error_message="An error occurred while making the request"
                    )
            return wrapper
        return decorator


class APIErrorHandler:
    """High-level API error handling utilities"""
    
    @staticmethod
    def make_google_api_request(
        url: str,
        headers: Dict[str, str],
        method: str = "GET",
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        operation_context: str = "Google Calendar API request"
    ) -> requests.Response:
        """
        Make a Google Calendar API request with centralized error handling
        
        Args:
            url (str): API endpoint URL
            headers (Dict[str, str]): Request headers
            method (str): HTTP method (GET, POST, PUT, DELETE)
            json_data (Optional[Dict[str, Any]]): JSON data for POST/PUT requests
            timeout (int): Request timeout in seconds
            operation_context (str): Context about the operation
            
        Returns:
            requests.Response: The response object if successful
            
        Raises:
            Various CalendarAPIException subclasses based on errors
        """
        try:
            # Make the HTTP request
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=json_data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise InternalServerError(
                    detail=f"Unsupported HTTP method: {method}",
                    error_message=f"HTTP method '{method}' is not supported"
                )
            
            # Handle the response
            HTTPErrorHandler.handle_google_calendar_response(response, operation_context)
            
            return response
            
        except requests.exceptions.Timeout:
            raise RequestTimeoutError(
                detail=f"{operation_context}: {ErrorMessages.REQUEST_TIMEOUT_CALENDAR}",
                error_message="The request timed out while waiting for a response"
            )
        except requests.exceptions.ConnectionError:
            raise ServiceUnavailableError(
                detail=f"{operation_context}: {ErrorMessages.CONNECTION_ERROR_CALENDAR}",
                error_message="Unable to establish connection to the Google Calendar service"
            )
        except requests.exceptions.RequestException as e:
            raise InternalServerError(
                detail=f"{operation_context}: {GoogleCalendarAPIMessages.REQUEST_ERROR.format(str(e))}",
                error_message="An error occurred while making the HTTP request"
            )
    
    @staticmethod
    def handle_generic_exception(
        exception: Exception, 
        operation_context: str = "Operation",
        fallback_status_code: int = 500
    ) -> HTTPException:
        """
        Convert generic exceptions to appropriate HTTP exceptions
        
        Args:
            exception (Exception): The exception to handle
            operation_context (str): Context about the operation
            fallback_status_code (int): Status code to use if not already an HTTPException
            
        Returns:
            HTTPException: The converted HTTP exception
        """
        if isinstance(exception, HTTPException):
            return exception
        
        # Create error message with context
        error_detail = f"{operation_context} failed: {str(exception)}"
        
        return HTTPException(
            status_code=fallback_status_code,
            detail=error_detail
        )


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present in data
    
    Args:
        data (Dict[str, Any]): Data to validate
        required_fields (list): List of required field names
        
    Raises:
        BadRequestError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise BadRequestError(ErrorMessages.MISSING_REQUIRED_FIELDS.format(", ".join(missing_fields)))


def create_success_response(
    data: Any,
    message: str = None,
    operation: str = None,
    resource: str = None,
    count: int = None
) -> Dict[str, Any]:
    """
    Create a standardized success response
    
    Args:
        data (Any): The response data
        message (str): Custom success message
        operation (str): The operation performed
        resource (str): The resource type
        count (int): Count of items (for list operations)
        
    Returns:
        Dict[str, Any]: Standardized response dictionary
    """
    from app.core.status_codes import get_success_message
    
    response = {}
    
    if message:
        response["message"] = message
    elif operation and resource:
        response["message"] = get_success_message(operation, resource)
    else:
        response["message"] = "Operation completed successfully"
    
    if isinstance(data, list):
        response["items"] = data
        response["count"] = count if count is not None else len(data)
    elif isinstance(data, dict):
        response.update(data)
    else:
        response["data"] = data
    
    return response
