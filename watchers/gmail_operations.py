"""
Gmail Operations Module

Functions for interacting with Gmail API to retrieve labels and messages.
"""

import base64
import re
from typing import List, Dict, Any, Optional
from email.utils import parsedate_to_datetime


def get_label_id(service: any, label_name: str = 'ToVault') -> str:
    """
    Get Gmail label ID by name.

    Args:
        service: Authenticated Gmail API service
        label_name: Name of the label to find

    Returns:
        Label ID string

    Raises:
        Exception: If label not found or retrieval fails
    """
    try:
        # List all labels
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        # Search for existing label
        for label in labels:
            if label['name'] == label_name:
                print(f"[OK] Found existing label: {label_name} (ID: {label['id']})")
                return label['id']

        # Label not found - provide helpful error message
        raise Exception(
            f"Label '{label_name}' not found in Gmail.\n"
            f"Please create the label manually:\n"
            f"1. Open Gmail\n"
            f"2. Click 'Create new label' in the sidebar\n"
            f"3. Name it '{label_name}'\n"
            f"4. Apply the label to emails you want to capture"
        )

    except Exception as e:
        if "not found" in str(e):
            raise  # Re-raise our custom error message
        raise Exception(f"Failed to get label '{label_name}': {e}")


def get_messages_with_label(
    service: any,
    label_id: str,
    max_results: int = 100
) -> List[Dict[str, str]]:
    """
    Get list of messages with specific label.

    Args:
        service: Authenticated Gmail API service
        label_id: Gmail label ID
        max_results: Maximum number of messages to retrieve

    Returns:
        List of message dicts with 'id' and 'threadId' keys

    Raises:
        Exception: If message retrieval fails
    """
    try:
        response = service.users().messages().list(
            userId='me',
            labelIds=[label_id],
            maxResults=max_results
        ).execute()

        messages = response.get('messages', [])
        return messages

    except Exception as e:
        raise Exception(f"Failed to retrieve messages: {e}")


def extract_body(payload: Dict[str, Any]) -> str:
    """
    Extract plain text body from Gmail message payload.

    Handles multipart messages, prefers text/plain, falls back to HTML with tag stripping.

    Args:
        payload: Gmail message payload dict

    Returns:
        Plain text body content
    """
    body = ""

    # Check if payload has parts (multipart message)
    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')

            # Prefer text/plain
            if mime_type == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8', errors='ignore')
                    return body

            # Recursively check nested parts
            elif 'parts' in part:
                nested_body = extract_body(part)
                if nested_body:
                    body = nested_body
                    return body

        # Fallback to text/html if no text/plain found
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            if mime_type == 'text/html':
                if 'data' in part['body']:
                    html_body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8', errors='ignore')
                    # Strip HTML tags
                    body = re.sub(r'<[^>]+>', '', html_body)
                    return body

    # Single part message
    elif 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(
            payload['body']['data']
        ).decode('utf-8', errors='ignore')

        # If it's HTML, strip tags
        if payload.get('mimeType') == 'text/html':
            body = re.sub(r'<[^>]+>', '', body)

    return body.strip()


def get_message_details(service: any, message_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific message.

    Args:
        service: Authenticated Gmail API service
        message_id: Gmail message ID

    Returns:
        Dict with keys: subject, sender, date, body, timestamp, message_id

    Raises:
        Exception: If message retrieval fails
    """
    try:
        # Get full message
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        # Extract headers
        headers = message['payload']['headers']
        subject = next(
            (h['value'] for h in headers if h['name'].lower() == 'subject'),
            'No Subject'
        )
        sender = next(
            (h['value'] for h in headers if h['name'].lower() == 'from'),
            'Unknown'
        )
        date_str = next(
            (h['value'] for h in headers if h['name'].lower() == 'date'),
            ''
        )

        # Parse date to ISO 8601
        email_date = None
        if date_str:
            try:
                dt = parsedate_to_datetime(date_str)
                email_date = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            except Exception:
                email_date = None

        # Extract body
        body = extract_body(message['payload'])

        # Internal timestamp (milliseconds since epoch)
        internal_timestamp = message.get('internalDate', '')

        return {
            'message_id': message_id,
            'subject': subject,
            'sender': sender,
            'date': date_str,
            'email_date': email_date,
            'body': body,
            'timestamp': internal_timestamp
        }

    except Exception as e:
        raise Exception(f"Failed to get message details for {message_id}: {e}")
