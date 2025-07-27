# Calendar Integration API with AI Assistant

A FastAPI-based REST API for integrating with Google Calendar, featuring an AI-powered natural language interface for effortless calendar management.

## ✨ Features

- **🤖 AI-Powered Calendar Assistant**: Natural language calendar management using Google Gemini AI
- **📅 Google Calendar Integration**: Full read/write access to Google Calendar
- **🗣️ Natural Language Processing**: Create, view, and delete events with natural language commands
- **🔐 OAuth2 Authentication**: Secure Google authentication flow
- **📊 RESTful API**: Clean REST endpoints for programmatic access
- **🌐 CORS Support**: Cross-origin resource sharing enabled

## � What This Project Does

- **Chat Interface**: Ask in plain English - "Schedule meeting tomorrow 2-3PM", "Show my events today", "Cancel my 10 AM meeting"
- **Smart Event Management**: Creates, lists, and deletes calendar events based on your natural language requests
- **Google Calendar Integration**: Directly connects to your Google Calendar account
- **AI Understanding**: Uses Google Gemini AI to understand your calendar requests

## Tech Stack

- **Backend**: FastAPI (Python)
- **AI**: Google Gemini Flash 1.5
- **Authentication**: Google OAuth2
- **Calendar API**: Google Calendar API v3
- **Server**: Uvicorn ASGI server


## Prerequisites

- Python 3.7+
- Google Cloud Platform account
- Google Calendar API enabled
- Google OAuth2 credentials
- Gemini API key

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/chakrateja70/Google-calendar-Integrated-Chatbot.git
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
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 5. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## How to Use

1. **Visit** `http://localhost:8000/docs` for API documentation
2. **Chat with AI**: Use the `/chat` endpoint with natural language
   - "Schedule meeting tomorrow 2-3PM"
   - "Show my events today"
   - "Cancel my meeting at 10 AM"
3. **Direct API**: Use specific endpoints like `/listevents`, `/create-event`, `/delete-event`

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
- [x] List calendar events  
- [x] Delete events
- [x] Natural language chat interface
- [x] Google Calendar API integration
- [x] OAuth2 authentication
- [x] AI-powered event parsing
- [ ] Update existing events
- [ ] Support for multiple calendars
- [ ] Event filtering and search
- [ ] Webhook support for real-time updates