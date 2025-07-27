from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime, timedelta
from app.core.calendar_auth import get_google_credentials
from app.services.google_calendar import (
    get_calendar_ids_service, list_events_service, create_event_service, delete_event_service
)
from app.services.llm_service import llm_service
from app.models.event_models import EventCreate, EventDeleteRequest, EventDateTime, Attendee
from app.models.llm_models import LLMPromptRequest, LLMFinalResponse, ChatResponse
from app.api.swagger_config import (
    GET_CALENDAR_IDS_CONFIG, LIST_EVENTS_CONFIG, CREATE_EVENT_CONFIG, DELETE_EVENT_CONFIG, DELETE_EVENT_BODY_CONFIG, CHAT_CONFIG
)

router = APIRouter()

@router.get("/calendar/ids", **GET_CALENDAR_IDS_CONFIG)
def get_calendar_ids(token: str = Depends(get_google_credentials)):
    """Get list of all accessible calendar IDs"""
    return get_calendar_ids_service(token)

@router.get("/listevents", **LIST_EVENTS_CONFIG)
def list_events(token: str = Depends(get_google_credentials)):
    """List events from primary calendar"""
    return list_events_service(token)

@router.post("/create-event", **CREATE_EVENT_CONFIG)
def create_event_endpoint(
    event_data: EventCreate,
    token: str = Depends(get_google_credentials)
):
    """Create a new event in Google Calendar"""
    return create_event_service(token, event_data)

@router.post("/delete-event", **DELETE_EVENT_BODY_CONFIG)
def delete_event_body_endpoint(
    delete_data: EventDeleteRequest,
    token: str = Depends(get_google_credentials)
):
    """Delete an event from Google Calendar using request body
    
    Args:
        delete_data (EventDeleteRequest): Delete request data containing event_id and send_updates
    """
    return delete_event_service(token, delete_data.event_id, delete_data.send_updates)

@router.post("/chat", **CHAT_CONFIG)
def chat_endpoint(
    prompt_request: LLMPromptRequest,
    token: str = Depends(get_google_credentials)
):  
    """Process user prompt using LLM and execute calendar actions"""
    try:
        # Parse the user's prompt using LLM
        llm_response = llm_service.parse_user_prompt(prompt_request.prompt)
        
        # Initialize variables for API response and final message
        api_response = None
        success = False
        message = ""
        
        # Execute the appropriate action based on LLM analysis
        if llm_response.action == "create_event":
            if llm_response.parsed_data:
                try:
                    # Prepare attendees if provided by LLM
                    attendees = None
                    if llm_response.parsed_data.attendees:
                        attendees = [
                            Attendee(
                                email=attendee.email,
                                displayName=attendee.name
                            )
                            for attendee in llm_response.parsed_data.attendees
                        ]
                    
                    # Call the existing create event service
                    event_data = EventCreate(
                        summary=llm_response.parsed_data.summary or "Event",
                        description=llm_response.parsed_data.description or "",
                        location=llm_response.parsed_data.location or "",
                        start=EventDateTime(
                            dateTime=llm_response.parsed_data.start_time,
                            timeZone=llm_response.parsed_data.timezone or "Asia/Kolkata"
                        ),
                        end=EventDateTime(
                            dateTime=llm_response.parsed_data.end_time,
                            timeZone=llm_response.parsed_data.timezone or "Asia/Kolkata"
                        ),
                        attendees=attendees
                    )
                    event_response = create_event_service(token, event_data)
                    # Convert Pydantic model to dict
                    api_response = event_response.dict() if hasattr(event_response, 'dict') else event_response.__dict__
                    success = True
                    message = f"Successfully created event: {llm_response.parsed_data.summary}"
                    
                    # Add attendee info to success message if attendees were added
                    if attendees:
                        attendee_names = [att.displayName for att in attendees]
                        message += f" with attendees: {', '.join(attendee_names)}"
                except Exception as e:
                    success = False
                    message = f"Failed to create event: {str(e)}"
                    api_response = {"error": str(e)}
            else:
                success = False
                message = "Could not extract event details from your request. Please provide more specific information."
        
        elif llm_response.action == "get_events":
            try:
                # Call the existing list events service
                events_response = list_events_service(token)
                events = events_response.items
                # Filtering logic for today, tomorrow, or date range
                filtered_events = events
                pd = llm_response.parsed_data
                if pd:
                    # Handle 'today' and 'tomorrow' or specific date
                    if pd.date:
                        try:
                            target_date = datetime.fromisoformat(pd.date).date()
                            filtered_events = [
                                e for e in events
                                if (
                                    (e.start.get("dateTime") and datetime.fromisoformat(e.start["dateTime"].replace("Z", "+00:00")).date() == target_date)
                                    or (e.start.get("date") and datetime.fromisoformat(e.start["date"]).date() == target_date)
                                )
                            ]
                        except Exception:
                            pass
                    # Handle date range if both start_time and end_time are present and are dates
                    elif pd.start_time and pd.end_time:
                        try:
                            start = datetime.fromisoformat(pd.start_time).date()
                            end = datetime.fromisoformat(pd.end_time).date()
                            filtered_events = [
                                e for e in events
                                if (
                                    (e.start.get("dateTime") and start <= datetime.fromisoformat(e.start["dateTime"].replace("Z", "+00:00")).date() <= end)
                                    or (e.start.get("date") and start <= datetime.fromisoformat(e.start["date"]).date() <= end)
                                )
                            ]
                        except Exception:
                            pass
                # If no date or range specified, filtered_events remains as all events
                events_response.items = filtered_events
                events_response.count = len(filtered_events)
                api_response = events_response.dict() if hasattr(events_response, 'dict') else events_response.__dict__
                success = True
                message = "Here are your filtered events" if filtered_events != events else "Here are your upcoming events"
            except Exception as e:
                success = False
                message = f"Failed to retrieve events: {str(e)}"
                api_response = {"error": str(e)}
        
        elif llm_response.action == "update_event":
            try:
                # First, get the list of events to find the target event
                events_response = list_events_service(token)
                events_data = events_response.dict() if hasattr(events_response, 'dict') else events_response.__dict__
                events_list = events_data.get('items', [])
                
                if not events_list:
                    success = False
                    message = "No events found in your calendar to update."
                    api_response = {"error": "No events available"}
                else:
                    # Use LLM service to match events
                    matching_events = llm_service.match_events_for_update_delete(prompt_request.prompt, events_list)
                    
                    if not matching_events:
                        success = False
                        message = "Could not find any events matching your description. Please be more specific about which event to update."
                        api_response = {
                            "error": "No matching events found",
                            "suggestion": "Try including the event title, date, or time in your request"
                        }
                    elif len(matching_events) == 1:
                        # Single match found - proceed with update
                        matched_event = matching_events[0]['event']
                        event_id = matched_event.get('id')
                        success = False  # TODO: Implement actual update logic
                        message = f"Found event to update: '{matched_event.get('summary', 'Untitled')}'. Update functionality will be implemented soon."
                        api_response = {
                            "matched_event": {
                                "id": event_id,
                                "summary": matched_event.get('summary'),
                                "start": matched_event.get('start'),
                                "end": matched_event.get('end')
                            },
                            "match_score": matching_events[0]['match_score'],
                            "match_reasons": matching_events[0]['match_reasons']
                        }
                    else:
                        # Multiple matches - ask user to choose
                        success = False
                        message = f"Found {len(matching_events)} events that might match. Please specify which one you want to update:"
                        api_response = {
                            "multiple_matches": True,
                            "matching_events": [
                                {
                                    "id": match['event'].get('id'),
                                    "summary": match['event'].get('summary', 'Untitled'),
                                    "start": match['event'].get('start'),
                                    "end": match['event'].get('end'),
                                    "match_score": match['match_score'],
                                    "match_reasons": match['match_reasons']
                                }
                                for match in matching_events[:5]  # Limit to top 5 matches
                            ]
                        }
            except Exception as e:
                success = False
                message = f"Failed to find events for update: {str(e)}"
                api_response = {"error": str(e)}
        
        elif llm_response.action == "delete_event":
            try:
                # First, get the list of events to find the target event
                events_response = list_events_service(token)
                events_data = events_response.dict() if hasattr(events_response, 'dict') else events_response.__dict__
                events_list = events_data.get('items', [])
                
                if not events_list:
                    success = False
                    message = "No events found in your calendar to delete."
                    api_response = {"error": "No events available"}
                else:
                    # Use LLM service to match events
                    matching_events = llm_service.match_events_for_update_delete(prompt_request.prompt, events_list)
                    
                    if not matching_events:
                        success = False
                        message = "Could not find any events matching your description. Please be more specific about which event to delete."
                        api_response = {
                            "error": "No matching events found",
                            "suggestion": "Try including the event title, date, or time in your request"
                        }
                    elif len(matching_events) == 1:
                        # Single match found - proceed with deletion
                        matched_event = matching_events[0]['event']
                        event_id = matched_event.get('id')
                        
                        try:
                            # Call the existing delete event service
                            from app.models.event_models import EventDeleteRequest
                            delete_request = EventDeleteRequest(event_id=event_id, send_updates="all")
                            delete_response = delete_event_service(token, event_id, "all")
                            
                            # Handle response conversion safely
                            if hasattr(delete_response, 'dict'):
                                api_response = delete_response.dict()
                            elif hasattr(delete_response, '__dict__'):
                                api_response = delete_response.__dict__
                            else:
                                # If it's already a dict or other type
                                api_response = delete_response
                                
                            success = True
                            message = f"Successfully deleted event: '{matched_event.get('summary', 'Untitled')}'"
                        except Exception as delete_error:
                            success = False
                            message = f"Failed to delete event: {str(delete_error)}"
                            api_response = {"error": str(delete_error)}
                    else:
                        # Multiple matches - ask user to choose
                        success = False
                        message = f"Found {len(matching_events)} events that might match. Please specify which one you want to delete:"
                        api_response = {
                            "multiple_matches": True,
                            "matching_events": [
                                {
                                    "id": match['event'].get('id'),
                                    "summary": match['event'].get('summary', 'Untitled'),
                                    "start": match['event'].get('start'),
                                    "end": match['event'].get('end'),
                                    "match_score": match['match_score'],
                                    "match_reasons": match['match_reasons']
                                }
                                for match in matching_events[:5]  # Limit to top 5 matches
                            ]
                        }
            except Exception as e:
                success = False
                message = f"Failed to find events for deletion: {str(e)}"
                api_response = {"error": str(e)}
        
        else:
            success = False
            message = "I couldn't understand your request. Please try rephrasing it."
            api_response = {
                "suggestions": [
                    "Try: 'Create meeting for 2-3PM tomorrow'",
                    "Try: 'Show my upcoming events'",
                    "Try: 'Update my meeting tomorrow'",
                    "Try: 'Delete my interview on July 28'",
                    "Try: 'Schedule appointment at 10AM'"
                ]
            }
        
        # Return structured response
        return ChatResponse(
            kind="calendar#chat",
            success=success,
            message=message,
            action_performed=llm_response.action.value,
            confidence=llm_response.confidence,
            reasoning=llm_response.reasoning,
            data=api_response,
            timestamp=datetime.now().isoformat() + "Z"
        )
        
    except Exception as e:
        # Handle any unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )
