import os
from fastapi import HTTPException, status
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from app.config.settings import SCOPES

def get_google_credentials():
    if not os.path.exists("credentials.json"):
        raise HTTPException(status_code=500, detail="Missing credentials.json")

    creds = None

    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Invalid token.json: {str(e)}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"OAuth flow failed: {str(e)}")

        try:
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"Warning: Failed to save token: {str(e)}")

    return creds