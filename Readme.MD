# Calendar Integration API with AI Assistant

A FastAPI-based REST API for integrating with Google Calendar, featuring an AI-powered natural language interface for effortless calendar management.

## ✨ Features

- **🤖 AI-Powered Calendar Assistant**: Natural language calendar management using Google Gemini AI
- **📅 Google Calendar Integration**: Full read/write access to Google Calendar
- **🗣️ Natural Language Processing**: Create events with phrases like "Schedule meeting tomorrow 2-3PM"
- **🔐 OAuth2 Authentication**: Secure Google authentication flow
- **📊 RESTful API**: Clean REST endpoints for programmatic access
- **🌐 CORS Support**: Cross-origin resource sharing enabled
- **💾 Database Ready**: SQLAlchemy integration for future data persistence

## 🚀 New AI Features

### Natural Language Calendar Operations
- **Create Events**: "Create event for 10-11AM I'm in 11th class"
- **View Events**: "Show my upcoming events"
- **Smart Parsing**: Automatically extracts dates, times, and event details
- **Context Aware**: Understands relative dates like "tomorrow", "next week"

## Tech Stack

- **Backend**: FastAPI (Python)
- **AI**: Google Gemini Flash 1.5 (Free tier)
- **Authentication**: Google OAuth2
- **Calendar API**: Google Calendar API v3
- **Database**: SQLAlchemy with MySQL support
- **Server**: Uvicorn ASGI server

## Project Structure

```
calender_Integration/
├── app/
│   ├── api/
│   │   └── routes.py          # API route definitions
│   ├── config/
│   │   └── settings.py        # Configuration and environment variables
│   ├── core/
│   │   └── calendar_auth.py   # Google OAuth2 authentication logic
│   ├── db/
│   │   ├── database.py        # Database configuration
│   │   └── fetch_tables.py    # Database table operations
│   ├── models/                # Data models (future use)
│   ├── services/
│   │   └── google_calendar.py # Google Calendar service integration
│   └── utils/
│       └── database.py        # Database utilities
├── credentials.json           # Google API credentials (not in repo)
├── token.json                 # OAuth2 token storage (not in repo)
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Prerequisites

- Python 3.7+
- Google Cloud Platform account
- Google Calendar API enabled
- Google OAuth2 credentials

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd calender_Integration
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Google Calendar API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the credentials as `credentials.json`
5. Place the `credentials.json` file in the project root directory

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
GOOGLE_CALENDAR_ID=primary
```

### 5. Run the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Get Upcoming Events

**GET** `/events`

Retrieves upcoming events from your primary Google Calendar.

**Response:**
```json
{
  "message": "Events retrieved.",
  "events": [
    {
      "id": "event_id",
      "summary": "Event Title",
      "start": "2025-07-23T10:00:00Z",
      "description": "Event description",
      "location": "Event location"
    }
  ],
  "count": 1,
  "timestamp": "2025-07-23T12:00:00.000000"
}
```

### Create New Event

**POST** `/events`

Creates a new event in your primary Google Calendar.

**Request Body:**
```json
{
  "summary": "Team Meeting",
  "description": "Weekly team sync meeting",
  "location": "Conference Room A",
  "start": {
    "dateTime": "2025-07-24T10:00:00Z",
    "timeZone": "UTC"
  },
  "end": {
    "dateTime": "2025-07-24T11:00:00Z",
    "timeZone": "UTC"
  }
}
```

**Response:**
```json
{
  "message": "Event created successfully.",
  "event": {
    "id": "event_id",
    "summary": "Team Meeting",
    "description": "Weekly team sync meeting",
    "location": "Conference Room A",
    "start": {
      "dateTime": "2025-07-24T10:00:00Z",
      "timeZone": "UTC"
    },
    "end": {
      "dateTime": "2025-07-24T11:00:00Z",
      "timeZone": "UTC"
    },
    "htmlLink": "https://calendar.google.com/event?eid=...",
    "created": "2025-07-23T12:00:00.000Z",
    "updated": "2025-07-23T12:00:00.000Z",
    "status": "confirmed"
  },
  "timestamp": "2025-07-23T12:00:00.000000"
}
```

**Notes:**
- `summary` is required
- For all-day events, use `date` instead of `dateTime` in start/end
- `timeZone` is optional but recommended for timed events
- `description` and `location` are optional

### Update Existing Event

**PUT** `/events/{event_id}`

Updates an existing event in your primary Google Calendar.

**Path Parameters:**
- `event_id` (string): The ID of the event to update

**Request Body:**
```json
{
  "summary": "Updated Team Meeting",
  "description": "Updated weekly team sync meeting",
  "location": "Conference Room B",
  "start": {
    "dateTime": "2025-07-24T14:00:00Z",
    "timeZone": "UTC"
  },
  "end": {
    "dateTime": "2025-07-24T15:00:00Z",
    "timeZone": "UTC"
  }
}
```

**Response:**
```json
{
  "message": "Event updated successfully.",
  "event": {
    "id": "event_id",
    "summary": "Updated Team Meeting",
    "description": "Updated weekly team sync meeting",
    "location": "Conference Room B",
    "start": {
      "dateTime": "2025-07-24T14:00:00Z",
      "timeZone": "UTC"
    },
    "end": {
      "dateTime": "2025-07-24T15:00:00Z",
      "timeZone": "UTC"
    },
    "htmlLink": "https://calendar.google.com/event?eid=...",
    "created": "2025-07-23T12:00:00.000Z",
    "updated": "2025-07-23T12:05:00.000Z",
    "status": "confirmed"
  },
  "timestamp": "2025-07-23T12:05:00.000000"
}
```

**Notes:**
- All fields are optional - only provided fields will be updated
- At least one field must be provided for update
- Event ID in the path must be valid
- Returns 404 if event is not found

## Authentication Flow

1. On first run, the application will open a browser window for Google OAuth2 authentication
2. Grant the necessary calendar permissions
3. The application will save an authentication token (`token.json`) for future use
4. Subsequent requests will use the saved token (auto-refreshed when needed)

## Development

### Project Structure Overview

- **`main.py`**: FastAPI application setup and configuration
- **`app/api/routes.py`**: API endpoint definitions
- **`app/services/google_calendar.py`**: Google Calendar API integration
- **`app/core/calendar_auth.py`**: OAuth2 authentication handling
- **`app/config/settings.py`**: Application configuration

### Adding New Features

1. Add new routes in `app/api/routes.py`
2. Implement business logic in appropriate service files
3. Update models if database changes are needed
4. Test thoroughly with different calendar scenarios

## Security Notes

- Never commit `credentials.json` or `token.json` to version control
- Configure CORS origins properly for production use
- Consider implementing rate limiting for production deployment
- Ensure proper error handling for API failures

## API Documentation

When the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Troubleshooting

### Common Issues

1. **Missing credentials.json**: Ensure you've downloaded OAuth2 credentials from Google Cloud Console
2. **Authentication errors**: Delete `token.json` and re-authenticate
3. **API quota exceeded**: Check your Google Cloud Console for API usage limits
4. **Permission errors**: Ensure the OAuth2 scope includes calendar access

### Error Responses

The API returns structured error responses:
```json
{
  "detail": "Error description"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Future Enhancements

- [x] Create calendar events
- [x] Update existing events
- [ ] Delete events
- [ ] Support for multiple calendars
- [ ] Event filtering and search
- [ ] Webhook support for real-time updates
- [ ] User management and multi-tenant support
- [ ] Event analytics and reporting