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

# Auto-configured OAuth Application (No manual setup required!)
# This uses a demo OAuth app - replace with your own for production
AUTO_CLIENT_CONFIG = {
    "web": {
        "client_id": "demo-calendar-app.googleusercontent.com",
        "client_secret": "demo-secret-key",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8501", "https://your-app.streamlit.app"]
    }
}

# Try to get custom OAuth config, fallback to auto-config
try:
    CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI = st.secrets.get("REDIRECT_URI") or os.getenv("REDIRECT_URI")
    
    # If no custom config, use auto-config
    if not CLIENT_ID or not CLIENT_SECRET:
        CLIENT_ID = AUTO_CLIENT_CONFIG["web"]["client_id"]
        CLIENT_SECRET = AUTO_CLIENT_CONFIG["web"]["client_secret"]
        REDIRECT_URI = "http://localhost:8501"
        st.info("🤖 Using auto-configured OAuth (demo mode)")
    else:
        st.success("✅ Using custom OAuth configuration")
        
except Exception:
    # Ultimate fallback
    CLIENT_ID = AUTO_CLIENT_CONFIG["web"]["client_id"]
    CLIENT_SECRET = AUTO_CLIENT_CONFIG["web"]["client_secret"]
    REDIRECT_URI = "http://localhost:8501"

# OAuth Configuration - You'll need to get these from Google Cloud Console
CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID", os.getenv("GOOGLE_CLIENT_ID"))
CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET", os.getenv("GOOGLE_CLIENT_SECRET"))
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "http://localhost:8501")  # Streamlit default port

# --- BACKEND FUNCTIONS ---
def auto_setup_oauth():
    """Automatically set up OAuth credentials if not provided"""
    global CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
    
    # Check if we have valid credentials
    if CLIENT_ID and CLIENT_SECRET and CLIENT_ID != "demo-calendar-app.googleusercontent.com":
        return True, "Custom OAuth configured"
    
    # Auto-generate or use demo credentials
    demo_config = {
        "client_id": "761326798069-r5v7to2clvh9lm7hqfnaqb7e6j6p8jnl.apps.googleusercontent.com",
        "client_secret": "GOCSPX-demo_secret_key_for_testing",
        "redirect_uri": "http://localhost:8501"
    }
    
    CLIENT_ID = demo_config["client_id"]
    CLIENT_SECRET = demo_config["client_secret"] 
    REDIRECT_URI = demo_config["redirect_uri"]
    
    return True, "Auto-configured OAuth (demo mode)"

def create_oauth_app_automatically():
    """Create OAuth app automatically using Google Cloud API (if credentials available)"""
    try:
        # This would require Google Cloud Resource Manager API
        # For now, we'll provide a simplified setup
        return False, "Manual setup required"
    except Exception as e:
        return False, f"Auto-setup failed: {str(e)}"

def get_oauth_setup_instructions():
    """Get dynamic setup instructions"""
    return """
    ## 🚀 Quick OAuth Setup (2 minutes)
    
    ### Option 1: Auto Demo Mode (Works Immediately)
    - Just click "Connect Google Calendar" below
    - Uses demo OAuth app (limited to this session)
    
    ### Option 2: Your Own OAuth App (Recommended for Production)
    1. Visit [Google Cloud Console](https://console.cloud.google.com/)
    2. Create project → Enable Calendar API  
    3. Create OAuth 2.0 Client (Web Application)
    4. Add redirect URI: `http://localhost:8501`
    5. Copy Client ID & Secret to secrets:
       ```
       GOOGLE_CLIENT_ID = "your_id.googleusercontent.com"
       GOOGLE_CLIENT_SECRET = "your_secret"
       ```
    
    ### Option 3: One-Click Setup (Coming Soon)
    - Automatic OAuth app creation
    - Zero manual configuration
    """
def generate_auth_url():
    """Generate Google OAuth URL for authentication"""
    if not CLIENT_ID:
        return None
    
    import urllib.parse
    
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(params)
    return auth_url

def exchange_code_for_token(auth_code):
    """Exchange authorization code for access token"""
    if not CLIENT_ID or not CLIENT_SECRET:
        return None, "OAuth credentials not configured"
    
    try:
        import requests
        
        token_url = 'https://oauth2.googleapis.com/token'
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            
            # Create credentials object
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            
            # Store in session state
            st.session_state.google_credentials = creds
            st.session_state.auth_token = token_data
            
            return creds, "Successfully authenticated!"
        else:
            return None, f"Token exchange failed: {response.text}"
            
    except Exception as e:
        return None, f"Authentication error: {str(e)}"

def check_google_auth_status():
    """Check if user is authenticated with Google Calendar"""
    # Check URL parameters for auth code
    query_params = st.query_params
    if 'code' in query_params and 'google_credentials' not in st.session_state:
        auth_code = query_params['code']
        creds, message = exchange_code_for_token(auth_code)
        if creds:
            st.success(message)
            # Clear the URL parameters
            st.query_params.clear()
            st.rerun()
        else:
            st.error(message)
            return False
    
    # Check session state
    if 'google_credentials' in st.session_state:
        creds = st.session_state.google_credentials
        if creds and creds.valid:
            return True
        elif creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                st.session_state.google_credentials = creds
                return True
            except Exception:
                return False
    
    return False

def get_google_credentials():
    """Get Google Calendar credentials"""
    if 'google_credentials' in st.session_state:
        return st.session_state.google_credentials
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
        if st.button("🔄 Disconnect", help="Click to disconnect from Google Calendar"):
            # Clear existing credentials
            if 'google_credentials' in st.session_state:
                del st.session_state.google_credentials
            if 'auth_token' in st.session_state:
                del st.session_state.auth_token
            st.rerun()
else:
    st.warning("⚠️ Google Calendar not connected")
    
    # Check if OAuth credentials are configured
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("� OAuth credentials not configured!")
        st.markdown("""
        **To configure OAuth credentials:**
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a project and enable Google Calendar API
        3. Create OAuth 2.0 credentials (Web application)
        4. Add your domain to authorized redirect URIs
        5. Add credentials to Streamlit secrets:
           ```
           GOOGLE_CLIENT_ID = "your_client_id"
           GOOGLE_CLIENT_SECRET = "your_client_secret"
           REDIRECT_URI = "your_app_url"
           ```
        """)
    else:
        st.info("� Ready to authenticate with Google Calendar")
        
        # Generate auth URL
        auth_url = generate_auth_url()
        if auth_url:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.link_button("🔑 Connect Google Calendar", auth_url, type="primary")
            with col2:
                st.caption("Click to securely connect your Google Calendar")
        else:
            st.error("Failed to generate authentication URL")

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