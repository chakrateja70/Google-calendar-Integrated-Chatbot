from fastapi import APIRouter, Depends
from app.core.calendar_auth import get_google_credentials
from app.services.google_calendar import (
    get_calendar_ids_service, list_events_service, create_event_service
)
from app.models.event_models import EventCreate
from app.api.swagger_config import (
    GET_CALENDAR_IDS_CONFIG, LIST_EVENTS_CONFIG, CREATE_EVENT_CONFIG
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
