from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from app.services.google_calendar import list_upcoming_events, create_event, update_event
from app.models.event_models import EventCreate, EventResponse, EventUpdate
from app.models.llm_models import LLMPromptRequest, LLMFinalResponse
from app.services.llm_service import llm_service
import datetime

router = APIRouter()

@router.get("/events", response_model=dict)
def get_events():
    events = list_upcoming_events()

    if not events:
        return JSONResponse(
            status_code=200,
            content={"message": "No events found.", "events": [], "count": 0}
        )

    formatted = [{
        "id": e.get("id"),
        "summary": e.get("summary", "No title"),
        "start": e["start"].get("dateTime", e["start"].get("date")),
        "description": e.get("description", ""),
        "location": e.get("location", ""),
        "invites": e.get("attendees", []),
        "htmlLink": e.get("htmlLink"),
        "created": e.get("created"),
        "updated": e.get("updated"),
        "status": e.get("status", "confirmed")
        
    } for e in events]

    return JSONResponse(
        status_code=200,
        content={
            "message": "Events retrieved.",
            "events": formatted,
            "count": len(formatted),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    )

@router.post("/create-event", response_model=dict)
def create_calendar_event(event_data: EventCreate):
    """
    Create a new event in Google Calendar
    
    Args:
        event_data (EventCreate): Event data including summary, start, end, description, location
    
    Returns:
        dict: Response with created event details
    """
    try:
        # Convert Pydantic model to dict for Google Calendar API
        event_dict = {
            "summary": event_data.summary,
            "start": event_data.start.dict(exclude_none=True),
            "end": event_data.end.dict(exclude_none=True),
        }
        
        # Add optional fields if provided
        if event_data.description:
            event_dict["description"] = event_data.description
        if event_data.location:
            event_dict["location"] = event_data.location
            
        # Create the event using Google Calendar service
        created_event = create_event(event_dict)
        
        # Format the response
        formatted_event = {
            "id": created_event.get("id"),
            "summary": created_event.get("summary"),
            "description": created_event.get("description", ""),
            "location": created_event.get("location", ""),
            "start": created_event.get("start", {}),
            "end": created_event.get("end", {}),
            "htmlLink": created_event.get("htmlLink"),
            "created": created_event.get("created"),
            "updated": created_event.get("updated"),
            "status": created_event.get("status")
        }
        
        return JSONResponse(
            status_code=201,
            content={
                "message": "Event created successfully.",
                "event": formatted_event,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException as e:
        # Re-raise HTTPExceptions from the service layer
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create event: {str(e)}"
        )

@router.put("/update-events/{event_id}", response_model=dict)
def update_calendar_event(event_id: str, event_data: EventUpdate):
    """
    Update an existing event in Google Calendar
    
    Args:
        event_id (str): The ID of the event to update
        event_data (EventUpdate): Updated event data (only provided fields will be updated)
    
    Returns:
        dict: Response with updated event details
    """
    try:
        # Convert Pydantic model to dict for Google Calendar API
        # Only include fields that are provided (not None)
        event_dict = {}
        
        if event_data.summary is not None:
            event_dict["summary"] = event_data.summary
        if event_data.description is not None:
            event_dict["description"] = event_data.description
        if event_data.location is not None:
            event_dict["location"] = event_data.location
        if event_data.start is not None:
            event_dict["start"] = event_data.start.dict(exclude_none=True)
        if event_data.end is not None:
            event_dict["end"] = event_data.end.dict(exclude_none=True)
            
        # Check if any fields are provided for update
        if not event_dict:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided for update"
            )
            
        # Update the event using Google Calendar service
        updated_event = update_event(event_id, event_dict)
        
        # Format the response
        formatted_event = {
            "id": updated_event.get("id"),
            "summary": updated_event.get("summary"),
            "description": updated_event.get("description", ""),
            "location": updated_event.get("location", ""),
            "start": updated_event.get("start", {}),
            "end": updated_event.get("end", {}),
            "htmlLink": updated_event.get("htmlLink"),
            "created": updated_event.get("created"),
            "updated": updated_event.get("updated"),
            "status": updated_event.get("status")
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Event updated successfully.",
                "event": formatted_event,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException as e:
        # Re-raise HTTPExceptions from the service layer
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update event: {str(e)}"
        )

@router.post("/ai/calendar", response_model=dict)
async def ai_calendar_assistant(request: LLMPromptRequest):
    """
    AI-powered calendar assistant that processes natural language requests
    
    This endpoint uses Google Gemini AI to understand user prompts and automatically:
    - Determine the appropriate calendar action (create, update, get events)
    - Parse event details from natural language
    - Execute the corresponding calendar operation
    
    Args:
        request (LLMPromptRequest): User's natural language prompt
    
    Returns:
        dict: Response with AI analysis and executed action results
    
    Examples:
        - "Create event for 10-11AM I'm in 11th class"
        - "Show my upcoming events"
        - "Schedule a meeting tomorrow at 2PM"
        - "Book appointment for next Tuesday at 3PM"
    """
    try:
        # Parse the user prompt using LLM
        llm_response = await llm_service.parse_user_prompt(request.prompt)
        
        # Execute the calendar action if confidence is high enough
        api_response = None
        success = False
        message = ""
        
        if llm_response.confidence >= 0.5:  # Minimum confidence threshold
            try:
                api_response = await llm_service.execute_calendar_action(llm_response)
                success = True
                
                # Generate user-friendly message based on action
                if llm_response.action.value == "get_events":
                    event_count = api_response.get("count", 0)
                    message = f"Found {event_count} upcoming events in your calendar."
                elif llm_response.action.value == "create_event":
                    event_name = llm_response.parsed_data.summary if llm_response.parsed_data else "event"
                    message = f"Successfully created '{event_name}' in your calendar."
                elif llm_response.action.value == "update_event":
                    message = api_response.get("message", "Event update information provided.")
                else:
                    message = api_response.get("message", "Action processed successfully.")
                    
            except HTTPException as e:
                success = False
                message = f"Failed to execute calendar action: {e.detail}"
                api_response = {"error": e.detail}
        else:
            success = False
            message = f"I'm not confident enough (confidence: {llm_response.confidence:.2f}) about what you want to do. Please be more specific."
        
        # Build final response
        final_response = LLMFinalResponse(
            success=success,
            message=message,
            llm_analysis=llm_response,
            api_response=api_response
        )
        
        return JSONResponse(
            status_code=200 if success else 400,
            content=final_response.dict()
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI calendar assistant failed: {str(e)}"
        )
