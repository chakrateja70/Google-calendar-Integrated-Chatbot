import os
from fastapi import HTTPException, status
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from app.config.settings import SCOPES
from app.core.exceptions import InternalServerError, AuthenticationError
from app.core.status_codes import GoogleCalendarAPIMessages

def get_google_credentials():
    if not os.path.exists("credentials.json"):
        raise InternalServerError(
            detail=GoogleCalendarAPIMessages.MISSING_CREDENTIALS,
            error_message="Google Calendar credentials file is missing"
        )

    creds = None

    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception as e:
            raise InternalServerError(
                detail=GoogleCalendarAPIMessages.INVALID_TOKEN.format(str(e)),
                error_message="Authentication token file is corrupted or invalid"
            )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise AuthenticationError(
                    detail=GoogleCalendarAPIMessages.TOKEN_REFRESH_FAILED.format(str(e)),
                    error_message="Failed to refresh the authentication token"
                )
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise InternalServerError(
                    detail=GoogleCalendarAPIMessages.OAUTH_FLOW_FAILED.format(str(e)),
                    error_message="OAuth authentication flow failed"
                )

        try:
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"Warning: Failed to save token: {str(e)}")

    return creds.token