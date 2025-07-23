import google.generativeai as genai
import json
import re
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.models.llm_models import LLMResponse, ParsedEventData, ActionType
from app.models.event_models import EventCreate, EventUpdate, EventDateTime
from app.services.google_calendar import create_event, update_event, list_upcoming_events

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)

class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for LLM with endpoint descriptions"""
        return """
You are a smart calendar assistant that parses natural language requests and determines the appropriate calendar action.

Available endpoints and their purposes:
1. GET /events - Retrieve upcoming calendar events
   - Use when: user wants to see, list, check, view, or get their events/schedule
   - Examples: "show my events", "what's on my calendar", "list my meetings"
   - No parsed_data needed for this action

2. POST /events - Create a new calendar event  
   - Use when: user wants to create, add, schedule, book, or make a new event
   - Examples: "create meeting", "schedule appointment", "add event", "book time"
   - Required in parsed_data: summary (title), start_time, end_time
   - Optional in parsed_data: description, location, timezone
   - DO NOT include event_id for create operations

3. PUT /events/{{event_id}} - Update an existing event
   - Use when: user wants to modify, change, update, edit, or reschedule an existing event
   - Examples: "change my meeting time", "update event", "reschedule appointment"
   - Required: event_id (you'll need to mention this needs to be provided)
   - Optional in parsed_data: summary, description, location, start_time, end_time, timezone

Current date and time context: {current_time}

INTELLIGENT EVENT PARSING GUIDELINES:
1. Extract meaningful event titles from the context:
   - "going to Hyderabad" → "Trip to Hyderabad"
   - "meeting with John" → "Meeting with John"
   - "doctor appointment" → "Doctor Appointment"
   - "lunch with team" → "Lunch with Team"

2. Generate descriptive details when possible:
   - Include purpose, participants, or additional context from the prompt
   - For travel: "Travel to [destination]" or "Trip to [location]"
   - For meetings: Include participants if mentioned
   - For appointments: Include type/purpose if mentioned

3. Location extraction:
   - Extract specific places, addresses, or destinations mentioned
   - For travel events, the destination becomes the location

4. Timezone handling:
   - Default to "Asia/Kolkata" (Indian Standard Time) unless user specifies otherwise
   - Support IST, UTC, and other common timezone abbreviations

5. Time parsing:
   - Support 12-hour format (12PM to 3PM)
   - Support 24-hour format (14:00 to 15:00)
   - If only time given, assume today's date
   - Support relative times like "tomorrow", "next week"

Parse the user's request and return a JSON response with:
- action: one of "create_event", "update_event", "get_events", or "unknown"
- confidence: float between 0 and 1
- parsed_data: extracted event information (only if action is create_event or update_event, null for get_events)
- reasoning: explanation of your decision
- endpoint: the API endpoint to use
- method: HTTP method (GET, POST, PUT)

For CREATE event (POST /events), include in parsed_data:
- summary: meaningful event title extracted from context
- description: descriptive details about the event (optional but encouraged)
- location: if mentioned (optional)
- start_time: ISO format datetime
- end_time: ISO format datetime  
- timezone: default to "Asia/Kolkata" unless specified otherwise
- DO NOT include event_id

For UPDATE event (PUT /events), include in parsed_data only the fields being updated:
- summary: if changing title (optional)
- description: if changing description (optional)  
- location: if changing location (optional)
- start_time: if changing start time (optional)
- end_time: if changing end time (optional)
- timezone: if specified (optional)
- event_id: REQUIRED for updates

For get_events action, set parsed_data to null.

Return ONLY valid JSON, no additional text.

Example for get events:
{
  "action": "get_events",
  "confidence": 0.95,
  "parsed_data": null,
  "reasoning": "User wants to view their calendar events",
  "endpoint": "/events",
  "method": "GET"
}

Example for create event:
{
  "action": "create_event",
  "confidence": 0.95,
  "parsed_data": {
    "summary": "Trip to Hyderabad",
    "description": "Travel to Hyderabad for business/personal trip",
    "location": "Hyderabad",
    "start_time": "2025-07-24T12:00:00",
    "end_time": "2025-07-24T15:00:00",
    "timezone": "Asia/Kolkata"
  },
  "reasoning": "User wants to create a travel event to Hyderabad",
  "endpoint": "/events",
  "method": "POST"
}

Example prompts and expected parsing:
- "create an event that i am going to Hyderabad 12PM to 3PM" → 
  summary: "Trip to Hyderabad", description: "Travel to Hyderabad", location: "Hyderabad"
- "meeting with John tomorrow 2-3PM" → 
  summary: "Meeting with John", description: "Meeting scheduled with John"
- "doctor appointment at 10AM" → 
  summary: "Doctor Appointment", description: "Medical appointment"
        """

    def _parse_time_expression(self, time_expr: str, base_date: Optional[datetime] = None) -> tuple[Optional[str], Optional[str]]:
        """Parse time expressions like '10-11AM', 'tomorrow 2PM', etc."""
        if base_date is None:
            base_date = datetime.now()
            
        time_expr = time_expr.lower().strip()
        
        # Handle date expressions
        target_date = base_date.date()
        if 'tomorrow' in time_expr:
            target_date = (base_date + timedelta(days=1)).date()
        elif 'next week' in time_expr:
            target_date = (base_date + timedelta(days=7)).date()
        elif re.search(r'\d{4}-\d{2}-\d{2}', time_expr):
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', time_expr)
            if date_match:
                target_date = datetime.fromisoformat(date_match.group(1)).date()
        
        # Parse time ranges like "12PM to 3PM", "9 AM to 12 PM", "10-11AM"
        time_range_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?\s*(?:to|-)?\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)'
        match = re.search(time_range_pattern, time_expr)
        
        if match:
            start_hour = int(match.group(1))
            start_min = int(match.group(2)) if match.group(2) else 0
            start_period = match.group(3).lower() if match.group(3) else None
            end_hour = int(match.group(4))
            end_min = int(match.group(5)) if match.group(5) else 0
            end_period = match.group(6).lower() if match.group(6) else None
            
            # Handle AM/PM for start time
            if start_period:
                if start_period == 'pm' and start_hour != 12:
                    start_hour += 12
                elif start_period == 'am' and start_hour == 12:
                    start_hour = 0
            
            # Handle AM/PM for end time
            if end_period:
                if end_period == 'pm' and end_hour != 12:
                    end_hour += 12
                elif end_period == 'am' and end_hour == 12:
                    end_hour = 0
            
            # If start time has no period but end time does, infer start period
            if not start_period and end_period:
                # If end is PM and start hour is less than end hour, start is likely AM
                # If end is AM and start hour is greater than end hour, start is likely PM (next day)
                if end_period == 'pm' and start_hour < end_hour:
                    # Start is likely AM, no conversion needed
                    pass
                elif end_period == 'am' and start_hour > end_hour:
                    # Start is likely PM previous day
                    if start_hour != 12:
                        start_hour += 12
            
            start_time = datetime.combine(target_date, datetime.min.time().replace(hour=start_hour, minute=start_min))
            end_time = datetime.combine(target_date, datetime.min.time().replace(hour=end_hour, minute=end_min))
            
            # If end time is before start time, assume end time is next day
            if end_time <= start_time:
                end_time = end_time + timedelta(days=1)
            
            # Return in ISO format compatible with Google Calendar API
            return start_time.strftime('%Y-%m-%dT%H:%M:%S'), end_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Single time like "2PM", "14:30"
        single_time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?'
        match = re.search(single_time_pattern, time_expr)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3).lower() if match.group(3) else None
            
            if period:
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
            
            start_time = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
            # Default 1 hour duration
            end_time = start_time + timedelta(hours=1)
            
            # Return in ISO format compatible with Google Calendar API
            return start_time.strftime('%Y-%m-%dT%H:%M:%S'), end_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        return None, None

    async def parse_user_prompt(self, prompt: str) -> LLMResponse:
        """Parse user prompt using Gemini LLM"""
        try:
            current_time = datetime.now().isoformat()
            system_prompt = self._get_system_prompt().format(current_time=current_time)
            
            full_prompt = f"{system_prompt}\n\nUser request: {prompt}"
            
            response = self.model.generate_content(full_prompt)
            
            # Clean and parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                return self._fallback_parse(prompt)
            
            # Enhanced time parsing
            if parsed_response.get('parsed_data'):
                data = parsed_response['parsed_data']
                
                # Set default timezone to Indian Standard Time if not specified
                if not data.get('timezone'):
                    data['timezone'] = 'Asia/Kolkata'
                
                if data.get('start_time') and data.get('end_time'):
                    # Times already parsed by LLM
                    pass
                else:
                    # Try to extract time from original prompt
                    start_time, end_time = self._parse_time_expression(prompt)
                    if start_time and end_time:
                        if not data.get('start_time'):
                            data['start_time'] = start_time
                        if not data.get('end_time'):
                            data['end_time'] = end_time
            
            # Handle cases where parsed_data might have extra fields
            try:
                # Clean parsed_data based on action type
                if 'parsed_data' in parsed_response and parsed_response['parsed_data']:
                    action_type = parsed_response.get('action')
                    data = parsed_response['parsed_data']
                    
                    # For create operations, remove event_id if it was incorrectly included
                    if action_type == 'create_event' and 'event_id' in data:
                        del data['event_id']
                        print("Removed event_id from create_event operation")
                    
                    # For get_events operations, parsed_data should be null
                    if action_type == 'get_events':
                        parsed_response['parsed_data'] = None
                        print("Set parsed_data to null for get_events operation")
                
                return LLMResponse(**parsed_response)
            except Exception as validation_error:
                print(f"Validation error: {validation_error}")
                # Try to clean the parsed_data if it exists
                if 'parsed_data' in parsed_response and parsed_response['parsed_data']:
                    # Only keep valid fields for ParsedEventData
                    valid_fields = ['summary', 'description', 'location', 'start_time', 'end_time', 'date', 'timezone', 'event_id']
                    cleaned_data = {k: v for k, v in parsed_response['parsed_data'].items() if k in valid_fields}
                    
                    # Remove event_id for create operations
                    action_type = parsed_response.get('action')
                    if action_type == 'create_event' and 'event_id' in cleaned_data:
                        del cleaned_data['event_id']
                    
                    parsed_response['parsed_data'] = cleaned_data
                
                return LLMResponse(**parsed_response)
            
        except Exception as e:
            print(f"LLM parsing error: {e}")
            # Return fallback response instead of raising exception
            return self._fallback_parse(prompt)

    def _fallback_parse(self, prompt: str) -> LLMResponse:
        """Fallback parsing when LLM response is invalid"""
        prompt_lower = prompt.lower()
        
        # Simple keyword-based parsing
        if any(word in prompt_lower for word in ['create', 'add', 'schedule', 'book', 'make']):
            action = ActionType.CREATE_EVENT
            endpoint = "/events"
            method = "POST"
            # Try to extract basic info for creation (NO event_id for create)
            start_time, end_time = self._parse_time_expression(prompt)
            parsed_data = ParsedEventData(
                summary=self._extract_summary(prompt),
                description=self._extract_description(prompt),
                location=self._extract_location(prompt),
                start_time=start_time,
                end_time=end_time,
                timezone="Asia/Kolkata"  # Default to Indian timezone
                # event_id is intentionally omitted for create operations
            )
        elif any(word in prompt_lower for word in ['update', 'change', 'modify', 'edit', 'reschedule']):
            action = ActionType.UPDATE_EVENT
            endpoint = "/events/{event_id}"
            method = "PUT"
            parsed_data = None  # Updates need event_id which we don't have in fallback
        elif any(word in prompt_lower for word in ['show', 'list', 'get', 'view', 'see', 'check', 'all', 'upcoming']):
            action = ActionType.GET_EVENTS
            endpoint = "/events"
            method = "GET"
            parsed_data = None  # No data needed for getting events
        else:
            action = ActionType.UNKNOWN
            endpoint = None
            method = None
            parsed_data = None
        
        return LLMResponse(
            action=action,
            confidence=0.7,
            parsed_data=parsed_data,
            reasoning=f"Fallback parsing detected keywords for {action.value}",
            endpoint=endpoint,
            method=method
        )

    def _extract_summary(self, prompt: str) -> str:
        """Extract event summary from prompt"""
        prompt_lower = prompt.lower()
        
        # Travel/trip related
        if any(phrase in prompt_lower for phrase in ['going to', 'trip to', 'travel to', 'visiting']):
            # Extract destination
            destinations = re.findall(r'(?:going to|trip to|travel to|visiting)\s+([a-zA-Z\s]+?)(?:\s+(?:at|from|on|\d)|\s*$)', prompt_lower)
            if destinations:
                destination = destinations[0].strip().title()
                return f"Trip to {destination}"
        
        # Meeting related
        if any(word in prompt_lower for word in ['meeting', 'meet']):
            # Extract who with
            with_match = re.search(r'(?:meeting|meet)\s+(?:with\s+)?([a-zA-Z\s]+?)(?:\s+(?:at|from|on|\d)|\s*$)', prompt_lower)
            if with_match:
                person = with_match.group(1).strip().title()
                return f"Meeting with {person}"
            return "Meeting"
        
        # Appointment related
        if 'appointment' in prompt_lower:
            # Extract type of appointment
            type_match = re.search(r'(\w+)\s+appointment', prompt_lower)
            if type_match:
                apt_type = type_match.group(1).title()
                return f"{apt_type} Appointment"
            return "Appointment"
        
        # Class/lesson related
        if any(word in prompt_lower for word in ['class', 'lesson', 'training']):
            # Extract subject
            subject_match = re.search(r'(\w+)\s+(?:class|lesson|training)', prompt_lower)
            if subject_match:
                subject = subject_match.group(1).title()
                return f"{subject} Class"
            return "Class Session"
        
        # Lunch/dinner/meal related
        if any(word in prompt_lower for word in ['lunch', 'dinner', 'breakfast', 'meal']):
            meal_type = None
            for meal in ['breakfast', 'lunch', 'dinner']:
                if meal in prompt_lower:
                    meal_type = meal.title()
                    break
            
            # Extract who with
            with_match = re.search(rf'{meal_type.lower() if meal_type else "meal"}\s+(?:with\s+)?([a-zA-Z\s]+?)(?:\s+(?:at|from|on|\d)|\s*$)', prompt_lower)
            if with_match:
                person = with_match.group(1).strip().title()
                return f"{meal_type or 'Meal'} with {person}"
            return meal_type or "Meal"
        
        # Default: Use meaningful words from the prompt, skip common words
        words = prompt.split()
        skip_words = {'create', 'an', 'event', 'that', 'i', 'am', 'at', 'to', 'from', 'on', 'in', 'the', 'a', 'and', 'or', 'but', 'for'}
        meaningful_words = []
        
        for word in words:
            # Skip common words and time patterns
            if (word.lower() not in skip_words and 
                not re.match(r'\d+(?:pm|am|:\d+)', word.lower()) and
                word.lower() not in ['exam', 'hall']):  # Skip location words that will be in location field
                meaningful_words.append(word)
        
        if meaningful_words:
            # Join meaningful words and clean up
            summary = ' '.join(meaningful_words[:6]).replace('&', 'and').title()
            
            # Handle specific cases
            if 'semester' in summary.lower():
                # For semester exam, create better title
                subject_words = []
                for word in meaningful_words:
                    if word.lower() not in ['semester', 'exam']:
                        subject_words.append(word)
                if subject_words:
                    return f"{' '.join(subject_words[:3]).replace('&', 'and').title()} Semester Exam"
                return "Semester Exam"
            
            return summary
        else:
            return "Event"

    def _extract_description(self, prompt: str) -> Optional[str]:
        """Extract event description from prompt"""
        prompt_lower = prompt.lower()
        
        # Exam related
        if 'exam' in prompt_lower:
            if 'semester' in prompt_lower:
                # Extract subject from prompt
                words = prompt.split()
                subject_words = []
                for word in words:
                    if (word.lower() not in ['create', 'event', 'for', 'my', 'semester', 'exam', 'from', 'to', 'in', 'am', 'pm', 'hall'] and
                        not re.match(r'\d+', word) and
                        not re.match(r'\d+(?:pm|am|:\d+)', word.lower())):
                        subject_words.append(word)
                
                if subject_words:
                    subject = ' '.join(subject_words[:3]).replace('&', 'and').title()
                    return f"Semester examination for {subject}"
                return "Semester examination"
            return "Examination scheduled"
        
        # Travel/trip related
        if any(phrase in prompt_lower for phrase in ['going to', 'trip to', 'travel to', 'visiting']):
            destinations = re.findall(r'(?:going to|trip to|travel to|visiting)\s+([a-zA-Z\s]+?)(?:\s+(?:at|from|on|\d)|\s*$)', prompt_lower)
            if destinations:
                destination = destinations[0].strip().title()
                return f"Travel to {destination}"
        
        # Meeting related
        if any(word in prompt_lower for word in ['meeting', 'meet']):
            with_match = re.search(r'(?:meeting|meet)\s+(?:with\s+)?([a-zA-Z\s]+?)(?:\s+(?:at|from|on|\d)|\s*$)', prompt_lower)
            if with_match:
                person = with_match.group(1).strip().title()
                return f"Meeting scheduled with {person}"
            return "Meeting scheduled"
        
        # Appointment related
        if 'appointment' in prompt_lower:
            type_match = re.search(r'(\w+)\s+appointment', prompt_lower)
            if type_match:
                apt_type = type_match.group(1).title()
                return f"{apt_type} appointment scheduled"
            return "Appointment scheduled"
        
        # Default description based on the event type
        summary = self._extract_summary(prompt)
        if summary and summary != "Event":
            return f"{summary} scheduled"
        
        return None

    def _extract_location(self, prompt: str) -> Optional[str]:
        """Extract location from prompt"""
        prompt_lower = prompt.lower()
        
        # Extract destinations for travel
        if any(phrase in prompt_lower for phrase in ['going to', 'trip to', 'travel to', 'visiting']):
            destinations = re.findall(r'(?:going to|trip to|travel to|visiting)\s+([a-zA-Z\s]+?)(?:\s+(?:at|from|on|\d)|\s*$)', prompt_lower)
            if destinations:
                return destinations[0].strip().title()
        
        # Look for specific location patterns for exams, meetings, etc.
        location_patterns = [
            r'in\s+((?:exam\s+hall|conference\s+room|room|hall|auditorium|classroom|lab|laboratory)\s*\d*)', # Exam Hall 3, Room 101
            r'at\s+([a-zA-Z\s]+?)(?:\s+(?:from|on|\d+\s*(?:am|pm))|\s*$)',  # General "at" pattern
            r'in\s+([a-zA-Z\s]+?)(?:\s+(?:from|on|\d+\s*(?:am|pm))|\s*$)',  # General "in" pattern
            r'(?:office|building|center|restaurant|cafe|hotel)\s+([a-zA-Z\s\d]+?)(?:\s+(?:at|from|on|\d)|\s*$)'  # Specific building types
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                location = match.group(1).strip().title()
                # Filter out time-related words
                if not re.match(r'\d+(?:pm|am|:\d+)', location.lower()):
                    return location
        
        return None

    async def execute_calendar_action(self, llm_response: LLMResponse) -> Dict[Any, Any]:
        """Execute the calendar action based on LLM response"""
        try:
            if llm_response.action == ActionType.GET_EVENTS:
                events = list_upcoming_events()
                return {
                    "events": events,
                    "count": len(events),
                    "message": f"Found {len(events)} upcoming events"
                }
            
            elif llm_response.action == ActionType.CREATE_EVENT:
                if not llm_response.parsed_data:
                    raise HTTPException(status_code=400, detail="No event data found in prompt")
                
                data = llm_response.parsed_data
                
                # Validate required fields
                if not data.summary:
                    data.summary = "Event"
                if not data.start_time or not data.end_time:
                    raise HTTPException(status_code=400, detail="Start and end times are required")
                
                # Create EventCreate model
                event_create = EventCreate(
                    summary=data.summary,
                    description=data.description or "",
                    location=data.location or "",
                    start=EventDateTime(
                        dateTime=data.start_time,
                        timeZone=data.timezone or "Asia/Kolkata"  # Default to Indian timezone
                    ),
                    end=EventDateTime(
                        dateTime=data.end_time,
                        timeZone=data.timezone or "Asia/Kolkata"  # Default to Indian timezone
                    )
                )
                
                # Convert to dict for Google Calendar API
                event_dict = {
                    "summary": event_create.summary,
                    "start": event_create.start.dict(exclude_none=True),
                    "end": event_create.end.dict(exclude_none=True),
                }
                
                if event_create.description:
                    event_dict["description"] = event_create.description
                if event_create.location:
                    event_dict["location"] = event_create.location
                
                created_event = create_event(event_dict)
                return {
                    "event": created_event,
                    "message": f"Successfully created event: {event_create.summary}"
                }
            
            elif llm_response.action == ActionType.UPDATE_EVENT:
                return {
                    "message": "Event updates require an event ID. Please specify which event you want to update.",
                    "action_needed": "Please provide the event ID or be more specific about which event to update"
                }
            
            else:
                return {
                    "message": "I couldn't understand your request. Please try rephrasing it.",
                    "suggestions": [
                        "Try: 'Create meeting for 2-3PM tomorrow'",
                        "Try: 'Show my upcoming events'",
                        "Try: 'Schedule appointment at 10AM'"
                    ]
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to execute calendar action: {str(e)}")

# Global instance
llm_service = LLMService()
