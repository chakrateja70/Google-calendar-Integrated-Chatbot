import os
from dotenv import load_dotenv
from app.core.exceptions import InternalServerError

load_dotenv()

# Google Calendar Configuration

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
if not CALENDAR_ID:
    raise InternalServerError("GOOGLE_CALENDAR_ID environment variable is not set.")

# Scopes for Google Calendar API (create, update, delete)
SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]

# Validate SCOPES configuration
if not SCOPES or not isinstance(SCOPES, list) or len(SCOPES) == 0:
    raise InternalServerError("Google Calendar SCOPES are not properly configured.")

# Google Gemini AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable is not set. LLM features will not work.")
    print("Get your free API key from: https://makersuite.google.com/app/apikey")
