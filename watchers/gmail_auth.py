"""
Gmail Authentication Module

Handles OAuth2 authentication for Gmail API access.
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def authenticate_gmail(
    credentials_path: str = 'credentials.json',
    token_path: str = 'watchers/.auth/token.json'
) -> any:
    """
    Authenticate with Gmail API using OAuth2.

    Args:
        credentials_path: Path to credentials.json from Google Cloud Console
        token_path: Path to store/load token.json

    Returns:
        Authenticated Gmail API service object

    Raises:
        FileNotFoundError: If credentials.json not found
        Exception: If authentication fails
    """
    creds = None
    token_file = Path(token_path)

    # Ensure token directory exists
    token_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing token if available
    if token_file.exists():
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            print("[INFO] Refreshing expired token...")
            creds.refresh(Request())
        else:
            # Run OAuth2 flow
            if not Path(credentials_path).exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {credentials_path}\n"
                    "Download credentials.json from Google Cloud Console:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Enable Gmail API\n"
                    "3. Create OAuth 2.0 credentials (Desktop app)\n"
                    "4. Download and save as credentials.json"
                )

            print("[INFO] Starting OAuth2 authentication flow...")
            print("[INFO] A browser window will open for authorization")

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future use
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        print(f"[OK] Token saved to {token_path}")

    # Build and return Gmail service
    service = build('gmail', 'v1', credentials=creds)
    print("[OK] Gmail API authenticated successfully")
    return service
