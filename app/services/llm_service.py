import google.generativeai as genai
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from app.models.llm_models import LLMResponse, ParsedEventData, ActionType
import difflib

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)

class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for LLM data extraction"""
        return """
You are a smart calendar assistant. Your task is to analyze user prompts and determine the action they want to perform, then extract relevant event data.

First, determine the action:
- "create_event": User wants to create/add/schedule/book a new event
- "get_events": User wants to see/list/view/check their calendar events  
- "update_event": User wants to modify/change/update an existing event
- "delete_event": User wants to delete/cancel/remove an existing event
- "unknown": Unable to determine the intent

If the action is "create_event", extract the following data from the prompt:
- summary: Event title/name
- description: Event description (optional)
- start_time: Start date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- end_time: End date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- timezone: Timezone (default to "Asia/Kolkata" for Indian Standard Time)
- location: Event location (optional)
- attendees: List of attendees with name and email (optional)

If the action is "update_event" or "delete_event", extract:
- summary: Keywords from event title/name to search for (REQUIRED for identification)
- start_time: Date/time to help identify the event - ALWAYS extract this when date/time keywords are mentioned
- date: Specific date mentioned (YYYY-MM-DD format) - ALWAYS extract when "today", "tomorrow", or specific dates are mentioned
- Any other identifying information from the prompt

IMPORTANT FOR DELETE/UPDATE ACTIONS:
- When user mentions "today", ALWAYS set date to today's date
- When user mentions "tomorrow", ALWAYS set date to tomorrow's date
- When user mentions "yesterday", ALWAYS set date to yesterday's date
- When user mentions specific dates, convert them to YYYY-MM-DD format
- When user mentions times (like "10 AM"), combine with the date to create start_time
- Date filtering is CRITICAL for accurate event identification when multiple events have similar titles

For time parsing:
- Always interpret times in the user's local timezone (Asia/Kolkata) unless explicitly stated otherwise
- If only time is given (like "10 AM"), assume today's date unless "tomorrow" or specific date is mentioned
- If "tomorrow" is mentioned, use tomorrow's date (2025-07-28)
- Support both 12-hour (10 AM, 2 PM) and 24-hour (14:00) formats
- If no end time specified, assume 1 hour duration
- Always format datetime as YYYY-MM-DDTHH:MM:SS (local time, NOT UTC)
- Always set timezone as "Asia/Kolkata" unless user specifies otherwise
- Examples:
  - "10 AM tomorrow" → start_time: "2025-07-28T10:00:00", timezone: "Asia/Kolkata"
  - "2 PM to 3 PM today" → start_time: "2025-07-27T14:00:00", end_time: "2025-07-27T15:00:00"

For get_events actions, set parsed_data to null.
For update_event and delete_event actions, extract event identification data in parsed_data.

Current date and time: {current_time} (Asia/Kolkata timezone)
Today's date: 2025-07-27
Tomorrow's date: 2025-07-28

Return ONLY a valid JSON response in this exact format:
{{
  "action": "create_event|get_events|update_event|delete_event|unknown",
  "confidence": 0.0-1.0,
  "parsed_data": {{
    "summary": "event title",
    "description": "event description", 
    "start_time": "2025-07-27T10:00:00",
    "end_time": "2025-07-27T11:00:00",
    "timezone": "Asia/Kolkata",
    "location": "location",
    "attendees": [
      {{
        "name": "John Doe",
        "email": "john@example.com"
      }}
    ]
  }} OR null,
  "reasoning": "explanation of decision",
  "endpoint": "/create-event|/listevents|/update-event|/delete-event",
  "method": "POST|GET|PUT|POST"
}}

Note: delete_event uses POST method with event_id in request body.

Example:
User: "Schedule an interview with Jagadish (tamaranajagadeesh555@gmail.com) tomorrow from 10 AM to 11 AM in Hyderabad."

Response:
{{
  "action": "create_event",
  "confidence": 0.95,
  "parsed_data": {{
    "summary": "Interview with Jagadish",
    "description": "Interview session with Jagadish",
    "start_time": "2025-07-28T10:00:00",
    "end_time": "2025-07-28T11:00:00",
    "timezone": "Asia/Kolkata",
    "location": "Hyderabad",
    "attendees": [
      {{
        "name": "Jagadish",
        "email": "tamaranajagadeesh555@gmail.com"
      }}
    ]
  }},
  "reasoning": "User wants to schedule a new interview event with specific time, location, and attendee",
  "endpoint": "/create-event",
  "method": "POST"
}}
        """

    def parse_user_prompt(self, prompt: str) -> LLMResponse:
        """Parse user prompt using Gemini LLM"""
        try:
            # Get current time in Asia/Kolkata timezone
            ist_tz = timezone(timedelta(hours=5, minutes=30))
            current_time = datetime.now(ist_tz).isoformat()
            system_prompt = self._get_system_prompt().format(current_time=current_time)
            
            full_prompt = f"{system_prompt}\n\nUser prompt: {prompt}"
            
            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()
            
            # Clean markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            try:
                parsed_response = json.loads(response_text)
                
                # Debug: Print the raw LLM response
                print(f"LLM Response: {parsed_response}")
                
                # Fix missing attendee names
                if parsed_response.get('parsed_data') and parsed_response['parsed_data'].get('attendees'):
                    attendees = parsed_response['parsed_data']['attendees']
                    for attendee in attendees:
                        if not attendee.get('name') and attendee.get('email'):
                            attendee['name'] = attendee['email'].split('@')[0]

                return LLMResponse(**parsed_response)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Raw LLM response: {response_text}")
                return self._fallback_parse(prompt)
            except Exception as e:
                print(f"Validation error: {e}")
                print(f"Raw LLM response: {response_text}")
                return self._fallback_parse(prompt)
                
        except Exception as e:
            print(f"LLM parsing error: {e}")
            return self._fallback_parse(prompt)

    def _fallback_parse(self, prompt: str) -> LLMResponse:
        """Fallback parsing when LLM response is invalid"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['create', 'add', 'schedule', 'book', 'make', 'plan', 'meeting']):
            action = ActionType.CREATE_EVENT
            endpoint = "/create-event"
            method = "POST"
            reasoning = "Detected creation keywords in prompt"
        elif any(word in prompt_lower for word in ['show', 'list', 'get', 'view', 'see', 'check', 'display']):
            action = ActionType.GET_EVENTS  
            endpoint = "/listevents"
            method = "GET"
            reasoning = "Detected viewing keywords in prompt"
        elif any(word in prompt_lower for word in ['update', 'change', 'modify', 'edit', 'reschedule']):
            action = ActionType.UPDATE_EVENT
            endpoint = "/update-event"
            method = "PUT"
            reasoning = "Detected update keywords in prompt"
        elif any(word in prompt_lower for word in ['delete', 'remove', 'cancel', 'cancel']):
            action = ActionType.DELETE_EVENT
            endpoint = "/delete-event"
            method = "POST"  # DELETE endpoint uses POST with request body
            reasoning = "Detected delete keywords in prompt"
        else:
            action = ActionType.UNKNOWN
            endpoint = None
            method = None
            reasoning = "Could not determine intent from prompt"
        
        return LLMResponse(
            action=action,
            confidence=0.6,
            parsed_data=None,
            reasoning=reasoning,
            endpoint=endpoint,
            method=method
        )

    def match_events_for_update_delete(self, user_input: str, events_list: List[Dict]) -> List[Dict]:
        """
        Match events from the calendar list based on user input.
        
        Args:
            user_input: The user's original prompt
            events_list: List of events from the calendar API
            
        Returns:
            List of matching events with match scores
        """
        if not events_list:
            return []
        
        # Parse user input for event identification
        llm_response = self.parse_user_prompt(user_input)
        search_criteria = {}
        
        # Extract search criteria from parsed_data if available
        if llm_response.parsed_data:
            if hasattr(llm_response.parsed_data, 'summary') and llm_response.parsed_data.summary:
                search_criteria['summary'] = str(llm_response.parsed_data.summary)
            if hasattr(llm_response.parsed_data, 'start_time') and llm_response.parsed_data.start_time:
                search_criteria['start_time'] = str(llm_response.parsed_data.start_time)
            if hasattr(llm_response.parsed_data, 'date') and llm_response.parsed_data.date:
                search_criteria['date'] = str(llm_response.parsed_data.date)
        
        matches = []
        user_input_lower = user_input.lower()
        
        for event in events_list:
            # Skip events that are None or malformed
            if not event or not isinstance(event, dict):
                continue
                
            match_score = 0.0
            match_reasons = []
            
            # Get event details
            event_summary = event.get('summary', '') or ''  # Handle None values
            event_summary = event_summary.lower()
            event_start = event.get('start', {}) or {}  # Handle None start
            event_date = None
            
            # Extract date from event
            if 'dateTime' in event_start:
                try:
                    event_datetime_str = event_start['dateTime']
                    if event_datetime_str:  # Check if not None or empty
                        event_datetime = datetime.fromisoformat(event_datetime_str.replace('Z', '+00:00'))
                        event_date = event_datetime.date()
                except (ValueError, TypeError, AttributeError):
                    pass
            elif 'date' in event_start:
                try:
                    event_date_str = event_start['date']
                    if event_date_str:  # Check if not None or empty
                        event_date = datetime.fromisoformat(event_date_str).date()
                except (ValueError, TypeError, AttributeError):
                    pass
            
            # Match on event title/summary
            if search_criteria.get('summary'):
                search_summary = search_criteria['summary'].lower()
                if search_summary in event_summary:
                    match_score += 0.5
                    match_reasons.append(f"Title contains '{search_criteria['summary']}'")
                else:
                    # Use fuzzy matching for partial matches
                    similarity = difflib.SequenceMatcher(None, search_summary, event_summary).ratio()
                    if similarity > 0.6:
                        match_score += similarity * 0.4
                        match_reasons.append(f"Title similarity ({similarity:.2f})")
            
            # Look for keywords in user input that might match event summary
            if event_summary:  # Only if event_summary is not empty
                summary_words = event_summary.split()
                for word in summary_words:
                    if len(word) > 3 and word in user_input_lower:
                        match_score += 0.3
                        match_reasons.append(f"Contains keyword '{word}'")
                        break
                
                # Additional check for names in user input (case insensitive)
                user_words = user_input_lower.split()
                for user_word in user_words:
                    if len(user_word) > 2 and user_word in event_summary:
                        match_score += 0.4
                        match_reasons.append(f"Contains name/word '{user_word}'")
                        break
            
            # Match on date
            if event_date:
                # Check for date mentions in user input
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                
                if 'today' in user_input_lower and event_date == today:
                    match_score += 0.6  # Increased weight for date matching
                    match_reasons.append("Date matches 'today'")
                elif 'tomorrow' in user_input_lower and event_date == tomorrow:
                    match_score += 0.6  # Increased weight for date matching
                    match_reasons.append("Date matches 'tomorrow'")
                elif search_criteria.get('start_time'):
                    try:
                        search_date = datetime.fromisoformat(search_criteria['start_time']).date()
                        if event_date == search_date:
                            match_score += 0.6  # Increased weight for date matching
                            match_reasons.append("Date matches specified date")
                    except:
                        pass
                elif search_criteria.get('date'):
                    try:
                        search_date = datetime.fromisoformat(search_criteria['date']).date()
                        if event_date == search_date:
                            match_score += 0.6  # Increased weight for date matching
                            match_reasons.append("Date matches specified date")
                    except:
                        pass
                
                # Check for date keywords (July 28, etc.)
                if event_date:
                    try:
                        date_str = event_date.strftime("%B %d").lower()
                        if date_str in user_input_lower:
                            match_score += 0.5
                            match_reasons.append(f"Date matches '{date_str}'")
                    except (ValueError, AttributeError):
                        pass
                
                # Penalty for wrong date when date is explicitly mentioned
                if 'today' in user_input_lower and event_date != today:
                    match_score -= 0.2  # Reduced penalty for wrong date
                    match_reasons.append("Date does NOT match 'today' (penalty applied)")
                elif 'tomorrow' in user_input_lower and event_date != tomorrow:
                    match_score -= 0.2  # Reduced penalty for wrong date
                    match_reasons.append("Date does NOT match 'tomorrow' (penalty applied)")
            
            # Match on time if specified
            if search_criteria.get('start_time') and 'dateTime' in event_start:
                try:
                    search_datetime = datetime.fromisoformat(search_criteria['start_time'])
                    event_datetime = datetime.fromisoformat(event_start['dateTime'].replace('Z', '+00:00'))
                    
                    # Check if times are close (within 30 minutes)
                    time_diff = abs((event_datetime - search_datetime).total_seconds())
                    if time_diff <= 1800:  # 30 minutes
                        match_score += 0.3
                        match_reasons.append("Time matches closely")
                except:
                    pass
            
            # Bonus for events that match both title keywords AND correct date
            has_title_match = any("keyword" in reason or "similarity" in reason or "name/word" in reason or "Title contains" in reason for reason in match_reasons)
            has_date_match = any("Date matches" in reason and "penalty" not in reason for reason in match_reasons)
            
            if has_title_match and has_date_match:
                match_score += 0.3  # Bonus for matching both title and date
                match_reasons.append("Bonus: matches both title and date")
            
            # Only include events with reasonable match scores
            # Lowered threshold to be less strict
            if match_score > 0.2:
                matches.append({
                    'event': event,
                    'match_score': match_score,
                    'match_reasons': match_reasons
                })
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Post-processing: If we have multiple matches and date is explicitly mentioned,
        # filter to only include events that match the specified date
        if len(matches) > 1:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            # Check if user mentioned specific date keywords
            date_filtered_matches = []
            
            if 'tomorrow' in user_input_lower:
                # Filter for events on tomorrow's date
                for match in matches:
                    event = match['event']
                    event_start = event.get('start', {}) or {}
                    event_date = None
                    
                    # Extract date from event
                    if 'dateTime' in event_start:
                        try:
                            event_datetime_str = event_start['dateTime']
                            if event_datetime_str:
                                event_datetime = datetime.fromisoformat(event_datetime_str.replace('Z', '+00:00'))
                                event_date = event_datetime.date()
                        except (ValueError, TypeError, AttributeError):
                            pass
                    elif 'date' in event_start:
                        try:
                            event_date_str = event_start['date']
                            if event_date_str:
                                event_date = datetime.fromisoformat(event_date_str).date()
                        except (ValueError, TypeError, AttributeError):
                            pass
                    
                    # Only include events that match tomorrow's date
                    if event_date == tomorrow:
                        date_filtered_matches.append(match)
                        
            elif 'today' in user_input_lower:
                # Filter for events on today's date
                for match in matches:
                    event = match['event']
                    event_start = event.get('start', {}) or {}
                    event_date = None
                    
                    # Extract date from event
                    if 'dateTime' in event_start:
                        try:
                            event_datetime_str = event_start['dateTime']
                            if event_datetime_str:
                                event_datetime = datetime.fromisoformat(event_datetime_str.replace('Z', '+00:00'))
                                event_date = event_datetime.date()
                        except (ValueError, TypeError, AttributeError):
                            pass
                    elif 'date' in event_start:
                        try:
                            event_date_str = event_start['date']
                            if event_date_str:
                                event_date = datetime.fromisoformat(event_date_str).date()
                        except (ValueError, TypeError, AttributeError):
                            pass
                    
                    # Only include events that match today's date
                    if event_date == today:
                        date_filtered_matches.append(match)
                        
            elif search_criteria.get('start_time') or search_criteria.get('date'):
                # Filter based on parsed date from LLM
                target_date = None
                if search_criteria.get('start_time'):
                    try:
                        target_date = datetime.fromisoformat(search_criteria['start_time']).date()
                    except:
                        pass
                elif search_criteria.get('date'):
                    try:
                        target_date = datetime.fromisoformat(search_criteria['date']).date()
                    except:
                        pass
                
                if target_date:
                    for match in matches:
                        event = match['event']
                        event_start = event.get('start', {}) or {}
                        event_date = None
                        
                        # Extract date from event
                        if 'dateTime' in event_start:
                            try:
                                event_datetime_str = event_start['dateTime']
                                if event_datetime_str:
                                    event_datetime = datetime.fromisoformat(event_datetime_str.replace('Z', '+00:00'))
                                    event_date = event_datetime.date()
                            except (ValueError, TypeError, AttributeError):
                                pass
                        elif 'date' in event_start:
                            try:
                                event_date_str = event_start['date']
                                if event_date_str:
                                    event_date = datetime.fromisoformat(event_date_str).date()
                            except (ValueError, TypeError, AttributeError):
                                pass
                        
                        # Only include events that match the target date
                        if event_date == target_date:
                            date_filtered_matches.append(match)
            
            # If we found date-filtered matches, use them instead of all matches
            # This significantly reduces ambiguity when date is mentioned
            if date_filtered_matches:
                matches = date_filtered_matches
                # Re-sort the filtered matches by score
                matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches

# Global instance
llm_service = LLMService()