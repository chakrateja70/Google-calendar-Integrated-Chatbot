import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# --- CONFIG ---
API_URL = "http://localhost:8000/chat"  # Adjust if backend runs elsewhere

# --- SIDEBAR: Project Info & Quick Help ---
st.sidebar.title("📅 Calendar Integration AI")
st.sidebar.markdown("""
**Features:**
- 🤖 AI-powered natural language calendar assistant
- 📅 Google Calendar integration (read/write)
- 🗣️ Create, view, delete events with plain English
- 🔐 Secure Google OAuth2 authentication
- 🌐 RESTful API backend (FastAPI)

**Tech Stack:**
- FastAPI (Python)
- Google Gemini AI
- Google Calendar API v3
- Streamlit (UI)

**How to Use:**
1. Start the FastAPI backend (`uvicorn main:app --reload`)
2. Run this UI (`streamlit run calendar_ui.py`)
3. Enter natural language commands below

**Authentication:**
- On first use, a Google login window will open
- Grant calendar permissions
- Token is saved for future use

**Troubleshooting:**
- Missing credentials? Place `credentials.json` in project root
- Auth errors? Delete `token.json` and re-authenticate
- API quota? Check Google Cloud Console

[API Docs](http://localhost:8000/docs)
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

# --- CHAT INPUT ---
st.markdown("---")
st.markdown("#### Enter your calendar command:")
user_input = st.text_input("", "Enter your prompt here...", key="user_input")
send_btn = st.button("Send", type="primary")

# --- HANDLE CHAT SUBMISSION ---
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

# --- MAIN CHAT LOGIC ---
if send_btn and user_input.strip():
    with st.spinner("Processing..."):
        try:
            payload = {"prompt": user_input.strip()}
            r = requests.post(API_URL, json=payload, timeout=30)
            if r.status_code == 200:
                resp = r.json()
                st.session_state.chat_history.append((user_input, resp))
            else:
                st.session_state.chat_history.append((user_input, {"success": False, "message": f"API error: {r.status_code} {r.text}"}))
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