from fastapi import APIRouter, Depends
from app.core.calendar_auth import get_google_credentials
from app.services.google_calendar import (
    get_calendar_ids_service, list_events_service, create_event_service
)
from app.models.event_models import (
    CalendarIDsResponse, ListEventsResponse, EventCreate, EventResponse
)


router = APIRouter()

# @router.post("/ai/calendar", response_model=dict)
# async def ai_calendar_assistant(request: LLMPromptRequest):
#     """
#     AI-powered calendar assistant that processes natural language requests
    
#     This endpoint uses Google Gemini AI to understand user prompts and automatically:
#     - Determine the appropriate calendar action (create, update, get events)
#     - Parse event details from natural language
#     - Execute the corresponding calendar operation
    
#     Args:
#         request (LLMPromptRequest): User's natural language prompt
    
#     Returns:
#         dict: Response with AI analysis and executed action results
    
#     Examples:
#         - "Create event for 10-11AM I'm in 11th class"
#         - "Show my upcoming events"
#         - "Schedule a meeting tomorrow at 2PM"
#         - "Book appointment for next Tuesday at 3PM"
#     """
#     try:
#         # Parse the user prompt using LLM
#         llm_response = await llm_service.parse_user_prompt(request.prompt)
        
#         # Execute the calendar action if confidence is high enough
#         api_response = None
#         success = False
#         message = ""
        
#         if llm_response.confidence >= 0.5:  # Minimum confidence threshold
#             try:
#                 api_response = await llm_service.execute_calendar_action(llm_response)
#                 success = True
                
#                 # Generate user-friendly message based on action
#                 if llm_response.action.value == "get_events":
#                     event_count = api_response.get("count", 0)
#                     message = f"Found {event_count} upcoming events in your calendar."
#                 elif llm_response.action.value == "create_event":
#                     event_name = llm_response.parsed_data.summary if llm_response.parsed_data else "event"
#                     message = f"Successfully created '{event_name}' in your calendar."
#                 elif llm_response.action.value == "update_event":
#                     message = api_response.get("message", "Event update information provided.")
#                 else:
#                     message = api_response.get("message", "Action processed successfully.")
                    
#             except HTTPException as e:
#                 success = False
#                 message = f"Failed to execute calendar action: {e.detail}"
#                 api_response = {"error": e.detail}
#         else:
#             success = False
#             message = f"I'm not confident enough (confidence: {llm_response.confidence:.2f}) about what you want to do. Please be more specific."
        
#         # Build final response
#         final_response = LLMFinalResponse(
#             success=success,
#             message=message,
#             llm_analysis=llm_response,
#             api_response=api_response
#         )
        
#         return JSONResponse(
#             status_code=200 if success else 400,
#             content=final_response.dict()
#         )
        
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"AI calendar assistant failed: {str(e)}"
#         )

@router.get("/calendar/ids", response_model=CalendarIDsResponse)
def get_calendar_ids(token: str = Depends(get_google_credentials)):
    """Get list of all accessible calendar IDs"""
    return get_calendar_ids_service(token)

@router.get("/listevents", response_model=ListEventsResponse)
def list_events(
    token: str = Depends(get_google_credentials)
):
    """List events from a specific calendar"""
    return list_events_service(token)


@router.post("/create-event", response_model=EventResponse)
def create_event_endpoint(
    event_data: EventCreate,
    token: str = Depends(get_google_credentials)
):
    """Create a new event in Google Calendar"""
    return create_event_service(token, event_data)
