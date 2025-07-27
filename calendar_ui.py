import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
import pandas as pd
import json
import os
from typing import Optional, Dict, Any, List

# Import backend functionality
import google.generativeai as genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIG ---
# Configure Gemini API with better error handling
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except Exception:
    # Fallback to environment variable if secrets not available
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("⚠️ GEMINI_API_KEY not found! Please configure it in .streamlit/secrets.toml or environment variables.")
    st.info("Add this to `.streamlit/secrets.toml`: GEMINI_API_KEY = \"your_api_key_here\"")

# Google Calendar Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# --- BACKEND FUNCTIONS ---
def authenticate_google_calendar():
    """Authenticate with Google Calendar and store credentials"""
    if not os.path.exists(CREDENTIALS_FILE):
        return False, "credentials.json file not found. Please download it from Google Cloud Console."
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        # Use run_local_server for authentication
        creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        # Also store in session state
        st.session_state.google_credentials = creds
        
        return True, "Successfully authenticated with Google Calendar!"
    except Exception as e:
        return False, f"Authentication failed: {str(e)}"

def check_google_auth_status():
    """Check if user is authenticated with Google Calendar"""
    # Check session state first
    if 'google_credentials' in st.session_state:
        creds = st.session_state.google_credentials
        if creds and creds.valid:
            return True
    
    # Check token file
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds and creds.valid:
                st.session_state.google_credentials = creds
                return True
            elif creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Update token file
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    st.session_state.google_credentials = creds
                    return True
                except Exception:
                    return False
        except Exception:
            return False
    
    return False

@st.cache_resource
def get_google_credentials():
    """Get Google Calendar credentials"""
    # Check session state first
    if 'google_credentials' in st.session_state:
        return st.session_state.google_credentials
    
    # Check if we have stored credentials in Streamlit secrets
    if "google_credentials" in st.secrets:
        try:
            creds_info = dict(st.secrets["google_credentials"])
            creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
            if creds and creds.valid:
                return creds
        except Exception as e:
            st.error(f"Error loading credentials from secrets: {e}")
    
    # Check local token file
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds and creds.valid:
                return creds
            elif creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Update token file
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    return creds
                except Exception:
                    return None
        except Exception:
            return None
    
    return None

def get_calendar_service():
    """Get Google Calendar service"""
    creds = get_google_credentials()
    if not creds:
        return None
    
    try:
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        st.error(f"Failed to create Google Calendar service: {e}")
        return None

def parse_user_prompt(prompt: str) -> Dict[str, Any]:
    """Parse user prompt using Gemini AI"""
    if not GEMINI_API_KEY:
        return {
            "success": False,
            "message": "Gemini AI not configured. Please add GEMINI_API_KEY to secrets.",
            "action": "error"
        }
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        system_prompt = f"""
You are a smart calendar assistant. Analyze the user prompt and return a JSON response with the action and extracted data.

Current date/time: {current_time}
Today: {today}
Tomorrow: {tomorrow}

Actions:
- "create_event": Create/schedule/add new event
- "get_events": List/show/view events
- "delete_event": Delete/cancel/remove event
- "update_event": Modify/change existing event

For create_event, extract:
- summary (title)
- start_datetime (YYYY-MM-DD HH:MM format)
- end_datetime (YYYY-MM-DD HH:MM format)
- location
- attendees (list of emails)
- description

For get_events, extract:
- time_range (today, tomorrow, this_week, next_week, or specific date)
- search_query (keywords to filter events)

For delete_event, extract:
- event_title (keywords from the event title)
- event_date (specific date if mentioned)

Return JSON only:
{{
    "action": "action_type",
    "data": {{...extracted_data...}},
    "success": true,
    "message": "Brief confirmation message"
}}

User prompt: {prompt}
"""
        
        response = model.generate_content(system_prompt)
        result_text = response.text.strip()
        
        # Extract JSON from response
        if result_text.startswith('```json'):
            result_text = result_text[7:-3]
        elif result_text.startswith('```'):
            result_text = result_text[3:-3]
        
        return json.loads(result_text)
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error parsing prompt: {str(e)}",
            "action": "error"
        }

def create_calendar_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create event in Google Calendar"""
    service = get_calendar_service()
    if not service:
        return {"success": False, "message": "Calendar service not available"}
    
    try:
        # Format the event data for Google Calendar API
        event = {
            'summary': event_data.get('summary', 'New Event'),
            'description': event_data.get('description', ''),
            'location': event_data.get('location', ''),
            'start': {
                'dateTime': event_data.get('start_datetime'),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': event_data.get('end_datetime'),
                'timeZone': 'Asia/Kolkata',
            },
        }
        
        # Add attendees if provided
        if event_data.get('attendees'):
            event['attendees'] = [{'email': email} for email in event_data['attendees']]
        
        # Create the event
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        
        return {
            "success": True,
            "message": "Event created successfully!",
            "data": created_event,
            "action_performed": "create_event"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create event: {str(e)}",
            "action_performed": "create_event"
        }

def get_calendar_events(filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get events from Google Calendar"""
    service = get_calendar_service()
    if not service:
        return {"success": False, "message": "Calendar service not available"}
    
    try:
        # Set time range
        now = datetime.now().isoformat() + 'Z'
        
        if filters and filters.get('time_range') == 'tomorrow':
            start_time = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'
            end_time = (datetime.now() + timedelta(days=2)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        else:
            start_time = now
            end_time = (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Filter by search query if provided
        if filters and filters.get('search_query'):
            search_terms = filters['search_query'].lower()
            events = [e for e in events if search_terms in e.get('summary', '').lower()]
        
        return {
            "success": True,
            "message": f"Found {len(events)} events",
            "data": {"items": events},
            "action_performed": "get_events"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get events: {str(e)}",
            "action_performed": "get_events"
        }

def delete_calendar_event(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Delete event from Google Calendar"""
    service = get_calendar_service()
    if not service:
        return {"success": False, "message": "Calendar service not available"}
    
    try:
        # First, find matching events
        events_response = get_calendar_events(filters)
        if not events_response["success"]:
            return events_response
        
        events = events_response["data"]["items"]
        
        # Filter by title if provided
        if filters.get('event_title'):
            title_keywords = filters['event_title'].lower()
            matching_events = [e for e in events if title_keywords in e.get('summary', '').lower()]
        else:
            matching_events = events
        
        if len(matching_events) == 0:
            return {
                "success": False,
                "message": "No matching events found to delete",
                "action_performed": "delete_event"
            }
        elif len(matching_events) > 1:
            return {
                "success": False,
                "message": "Found multiple matching events. Please be more specific:",
                "data": matching_events,
                "action_performed": "delete_event"
            }
        else:
            # Delete the event
            event_to_delete = matching_events[0]
            service.events().delete(calendarId='primary', eventId=event_to_delete['id']).execute()
            
            return {
                "success": True,
                "message": f"Successfully deleted event: {event_to_delete.get('summary')}",
                "action_performed": "delete_event"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to delete event: {str(e)}",
            "action_performed": "delete_event"
        }

def process_chat_request(prompt: str) -> Dict[str, Any]:
    """Main function to process chat requests"""
    # Parse the user prompt
    parsed_result = parse_user_prompt(prompt)
    
    if not parsed_result.get("success"):
        return parsed_result
    
    action = parsed_result.get("action")
    data = parsed_result.get("data", {})
    
    # Execute the appropriate action
    if action == "create_event":
        return create_calendar_event(data)
    elif action == "get_events":
        return get_calendar_events(data)
    elif action == "delete_event":
        return delete_calendar_event(data)
    elif action == "update_event":
        return {
            "success": False,
            "message": "Update functionality not implemented yet",
            "action_performed": "update_event"
        }
    else:
        return {
            "success": False,
            "message": "I didn't understand what you want to do. Please try rephrasing your request.",
            "action_performed": "unknown"
        }

# --- SIDEBAR: Project Info & Quick Help ---
st.sidebar.title("📅 Calendar Integration AI")
st.sidebar.markdown("""
**Features:**
- 🤖 AI-powered natural language calendar assistant
- 📅 Google Calendar integration (read/write)
- 🗣️ Create, view, delete events with plain English
- 🔐 Secure Google OAuth2 authentication
- ☁️ Fully deployed on Streamlit Cloud

**Tech Stack:**
- Streamlit (UI + Backend)
- Google Gemini AI
- Google Calendar API v3
- Python

**How to Use:**
1. Ensure Google credentials are configured
2. Enter natural language commands below
3. AI will understand and execute your requests

**Authentication:**
- Credentials should be configured in Streamlit secrets
- For local development, place `credentials.json` in project root

**Troubleshooting:**
- Missing credentials? Check Streamlit secrets configuration
- Auth errors? Verify Google Calendar API permissions
- AI not working? Check GEMINI_API_KEY in secrets

**Examples:**
- "Schedule meeting tomorrow 2 PM"
- "Show my events for tomorrow"
- "Delete interview with John"
""")

# --- PAGE SETUP ---
st.set_page_config(
    page_title="AI Calendar Assistant",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("📅 AI Calendar Assistant")
st.markdown("""
Effortlessly manage your Google Calendar using natural language!<br>

**What can you do?**
- Schedule meetings, classes, or reminders
- List your upcoming events
- Cancel or update events
- All with simple English commands!

_Requires Google authentication on first use._
""", unsafe_allow_html=True)

# --- EXAMPLE PROMPTS ---
with st.expander("💡 Example prompts", expanded=False):
    st.markdown("""
    **Full-featured examples:**
    1. Schedule an interview with Jagadish (tamaranajagadeesh555@gmail.com) tomorrow from 10 AM to 11 AM in Hyderabad
    2. Book a doctor's appointment with Dr. Smith (dr.smith@hospital.com) next Monday at 4 PM at Apollo Clinic, Hyderabad
    3. Create a team lunch with John (john@company.com), Priya (priya@company.com), and Alex (alex@company.com) next Friday at 1 PM at Barbeque Nation

    **Type commands like:**
    - Schedule a call with Ramesh (ramesh@client.com) tomorrow at 3 PM in my office
    - Add a reminder to submit my expense report this Friday at 5 PM
    - Show all my meetings with Priya next week
    - Delete my Yoga class on August 1 at 6 AM

    _Tip: Be as specific as possible for best results!_
    """)

# --- SESSION STATE FOR CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # List of (user, assistant) tuples

# --- DISPLAY FUNCTIONS ---
def display_event_details(event):
    """Display a single event's important details in a clean format."""
    st.markdown(f"**Title:** {event.get('summary', '(No title)')}")
    start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
    end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date', ''))
    if start:
        st.markdown(f"**Start:** {start}")
    if end:
        st.markdown(f"**End:** {end}")
    location = event.get('location', None)
    if location:
        st.markdown(f"**Location:** {location}")
    attendees = event.get('attendees', [])
    if attendees:
        names = [a.get('displayName', a.get('email', '')) for a in attendees]
        st.markdown(f"**Attendees:** {', '.join(names)}")
    link = event.get('htmlLink', None)
    if link:
        st.markdown(f"[View in Google Calendar]({link})")

def display_events_table(events):
    """Display multiple events in a table format."""
    if not events:
        st.info("No events found.")
        return
    
    # Prepare data for the table
    table_data = []
    for event in events:
        # Get start and end times
        start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
        end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date', ''))
        
        # Format dates for better readability
        start_formatted = start.split('T')[0] + ' ' + start.split('T')[1][:5] if 'T' in start else start
        end_formatted = end.split('T')[0] + ' ' + end.split('T')[1][:5] if 'T' in end else end
        
        # Get attendees
        attendees = event.get('attendees', [])
        attendees_str = ', '.join([a.get('displayName', a.get('email', '')) for a in attendees]) if attendees else 'None'
        
        # Truncate long attendee lists for table display
        if len(attendees_str) > 50:
            attendees_str = attendees_str[:47] + '...'
        
        table_data.append({
            'Title': event.get('summary', '(No title)'),
            'Start': start_formatted,
            'End': end_formatted,
            'Location': event.get('location', 'Not specified'),
            'Attendees': attendees_str
        })
    
    # Create and display the dataframe
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Add a note about viewing individual events
    st.caption(f"📋 Showing {len(events)} event(s). Click on any row to expand details if needed.")

def display_response(resp):
    """Display the assistant's response in a structured, minimal way."""
    st.markdown(f"**Assistant:** {resp.get('message', '')}")
    data = resp.get("data")
    action = resp.get("action_performed", "")
    
    if action == "get_events" and data and "items" in data:
        items = data["items"]
        if items:
            st.markdown("#### Events:")
            if len(items) > 1:
                # Display multiple events in table format
                display_events_table(items)
            else:
                # Display single event in detailed format
                display_event_details(items[0])
        else:
            st.info("No events found.")
    
    elif action == "delete_event":
        if resp.get("success"):
            st.success("Event deleted successfully!")
        else:
            # Handle case where multiple events are found for deletion
            if data and isinstance(data, list) and len(data) > 1:
                st.warning("Multiple matching events found. Please be more specific:")
                display_events_table(data)
            elif data and isinstance(data, list) and len(data) == 1:
                st.warning("Found this matching event:")
                display_event_details(data[0])
            elif data and "items" in data and len(data["items"]) > 1:
                st.warning("Multiple matching events found. Please be more specific:")
                display_events_table(data["items"])
            elif data and "items" in data and len(data["items"]) == 1:
                st.warning("Found this matching event:")
                display_event_details(data["items"][0])
    
    elif action == "create_event" and data:
        st.success("Event created successfully!")
        display_event_details(data)
    
    elif action == "update_event" and resp.get("success"):
        st.success("Event updated successfully!")
    
    elif not resp.get("success"):
        st.error(resp.get("message", "Something went wrong."))
        if data and "suggestions" in data:
            st.markdown("**Suggestions:**")
            for sug in data["suggestions"]:
                st.markdown(f"- {sug}")
        # Handle any other case where data contains events to display
        elif data and isinstance(data, list) and len(data) > 0:
            if len(data) > 1:
                display_events_table(data)
            else:
                display_event_details(data[0])
        elif data and "items" in data and len(data["items"]) > 0:
            if len(data["items"]) > 1:
                display_events_table(data["items"])
            else:
                display_event_details(data["items"][0])

# --- GOOGLE CALENDAR AUTHENTICATION ---
st.markdown("---")
st.markdown("### 🔐 Google Calendar Authentication")

# Check authentication status
is_authenticated = check_google_auth_status()

if is_authenticated:
    st.success("✅ Connected to Google Calendar")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("You can now use calendar commands!")
    with col2:
        if st.button("🔄 Re-authenticate", help="Click to re-authenticate with Google Calendar"):
            # Clear existing credentials
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            if 'google_credentials' in st.session_state:
                del st.session_state.google_credentials
            st.rerun()
else:
    st.warning("⚠️ Google Calendar not connected")
    
    # Check if credentials.json exists
    if not os.path.exists(CREDENTIALS_FILE):
        st.error("📄 `credentials.json` file not found!")
        st.markdown("""
        **To set up Google Calendar authentication:**
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a project and enable Google Calendar API
        3. Create OAuth 2.0 credentials (Desktop application)
        4. Download the credentials as `credentials.json`
        5. Place the file in your project root directory
        """)
    else:
        st.info("📄 `credentials.json` found! Click below to authenticate:")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            auth_button = st.button("🔑 Authenticate Google Calendar", type="primary")
        with col2:
            st.caption("This will open a browser window for Google authentication")
        
        if auth_button:
            with st.spinner("Starting authentication process..."):
                success, message = authenticate_google_calendar()
                if success:
                    st.success(message)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)

# Only show chat interface if authenticated
if is_authenticated:
    # --- CHAT INPUT ---
    st.markdown("---")
    st.markdown("#### Enter your calendar command:")
    user_input = st.text_input("", "", key="user_input")
    send_btn = st.button("Send", type="primary")
    
    # --- MAIN CHAT LOGIC ---
    if send_btn and user_input.strip():
        with st.spinner("Processing..."):
            try:
                # Use integrated backend instead of API call
                resp = process_chat_request(user_input.strip())
                st.session_state.chat_history.append((user_input, resp))
            except Exception as e:
                st.session_state.chat_history.append((user_input, {"success": False, "message": f"Request failed: {e}"}))
        st.rerun()
    
    # --- DISPLAY CHAT HISTORY ---
    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### Conversation History")
        # Show only the last 2 exchanges
        for user, resp in reversed(st.session_state.chat_history[-2:]):
            st.markdown(f"**You:** {user}")
            display_response(resp)
            st.markdown("---")

else:
    # Show message when not authenticated
    st.markdown("---")
    st.info("🔒 Please authenticate with Google Calendar first to use the chat interface.")
    st.markdown("""
    **Once authenticated, you can:**
    - 📅 Create events: "Schedule meeting tomorrow 2 PM"
    - 👀 View events: "Show my tomorrow events"  
    - 🗑️ Delete events: "Delete interview with John"
    - ✏️ Update events: "Change meeting time to 3 PM"
    """) 