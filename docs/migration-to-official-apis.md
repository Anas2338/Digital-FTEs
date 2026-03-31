# Migration to Official APIs

This document provides guidance for migrating from unofficial/placeholder APIs to official production APIs for WhatsApp and LinkedIn integrations.

---

## Overview

The Silver Tier implementation uses placeholder/unofficial APIs for rapid prototyping:

- **WhatsApp**: Custom Node.js bridge using `whatsapp-web.js` (unofficial)
- **LinkedIn**: Unofficial API with session cookies
- **Gmail**: Placeholder (ready for official Gmail API)

This document outlines the migration path to official APIs for production use.

---

## WhatsApp Migration

### Current Implementation (Unofficial)

**Technology**: `whatsapp-web.js` library
- Connects via WhatsApp Web protocol
- Requires QR code scanning
- Session-based authentication
- Not officially supported by Meta

**Limitations**:
- Account can be banned for violating ToS
- No official support or SLA
- Session expires frequently
- Limited to personal accounts

### Target Implementation (Official)

**Technology**: WhatsApp Business API
- Official Meta API
- Webhook-based message delivery
- OAuth2 authentication
- Production-ready with SLA

**Migration Steps**:

1. **Create WhatsApp Business Account**
   - Sign up at https://business.whatsapp.com/
   - Verify business information
   - Get API access credentials

2. **Update Watcher Implementation**

   Replace `watchers/whatsapp_watcher/bridge.js` with official API client:

   ```python
   # watchers/whatsapp_watcher/watcher.py
   from whatsapp_business_api import WhatsAppClient

   class WhatsAppWatcher(BaseWatcher):
       def __init__(self):
           super().__init__("whatsapp_watcher", poll_interval=30)
           self.client = WhatsAppClient(
               phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
               access_token=os.getenv("WHATSAPP_ACCESS_TOKEN")
           )

       def fetch_new_events(self):
           # Use webhook-based delivery instead of polling
           # Messages delivered to webhook endpoint
           pass
   ```

3. **Set Up Webhook Endpoint**

   ```python
   # mcp-servers/digital-fte-server/webhooks/whatsapp.py
   from fastapi import APIRouter, Request

   router = APIRouter()

   @router.post("/webhooks/whatsapp")
   async def whatsapp_webhook(request: Request):
       data = await request.json()
       # Process incoming message
       # Create event in database
       # Write to Obsidian vault
       return {"status": "received"}
   ```

4. **Update MCP Tool**

   ```python
   # mcp-servers/digital-fte-server/tools/whatsapp_send.py
   from whatsapp_business_api import WhatsAppClient

   def execute(self, recipient: str, message: str):
       client = WhatsAppClient(...)
       response = client.send_message(
           to=recipient,
           message=message
       )
       return {
           "success": True,
           "message_id": response["messages"][0]["id"]
       }
   ```

5. **Update Credentials Storage**

   ```bash
   # Store WhatsApp Business API credentials
   python -c "
   from watchers.shared.keychain import KeychainManager
   km = KeychainManager()
   km.set_credential('whatsapp', {
       'phone_number_id': 'YOUR_PHONE_NUMBER_ID',
       'access_token': 'YOUR_ACCESS_TOKEN'
   })
   "
   ```

**Cost Considerations**:
- WhatsApp Business API has per-message pricing
- Free tier: 1,000 conversations/month
- Paid tier: $0.005-0.09 per conversation (varies by country)

**Timeline**: 2-3 days for migration

---

## LinkedIn Migration

### Current Implementation (Unofficial)

**Technology**: `linkedin-api` library with session cookies
- Scrapes LinkedIn web interface
- Session-based authentication
- Not officially supported

**Limitations**:
- Account can be banned for violating ToS
- No official support
- Session expires frequently
- Rate limiting unpredictable

### Target Implementation (Official)

**Technology**: LinkedIn Marketing Developer Platform
- Official LinkedIn API
- OAuth2 authentication
- Production-ready with SLA

**Migration Steps**:

1. **Create LinkedIn App**
   - Go to https://www.linkedin.com/developers/
   - Create new app
   - Request API access (requires company page)
   - Get Client ID and Client Secret

2. **Implement OAuth2 Flow**

   ```python
   # watchers/linkedin_watcher/auth.py
   from linkedin_v2 import linkedin

   def authenticate():
       authentication = linkedin.LinkedInAuthentication(
           client_id=os.getenv("LINKEDIN_CLIENT_ID"),
           client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
           redirect_uri=os.getenv("LINKEDIN_REDIRECT_URI"),
           permissions=['r_liteprofile', 'r_emailaddress', 'w_member_social']
       )

       # Get authorization URL
       print(f"Visit: {authentication.authorization_url}")

       # After user authorizes, exchange code for token
       code = input("Enter authorization code: ")
       authentication.get_access_token(code)

       return authentication.token
   ```

3. **Update Watcher Implementation**

   ```python
   # watchers/linkedin_watcher/watcher.py
   from linkedin_v2 import linkedin

   class LinkedInWatcher(BaseWatcher):
       def __init__(self):
           super().__init__("linkedin_watcher", poll_interval=120)
           token = self.keychain.get_credential("linkedin")["access_token"]
           self.client = linkedin.LinkedInApplication(token=token)

       def fetch_new_events(self):
           # Fetch notifications
           notifications = self.client.get_notifications()

           # Fetch messages
           messages = self.client.get_messages()

           return self._convert_to_events(notifications + messages)
   ```

4. **Update MCP Tool**

   ```python
   # mcp-servers/digital-fte-server/tools/linkedin_post.py
   from linkedin_v2 import linkedin

   def execute(self, content: str):
       token = self.keychain.get_credential("linkedin")["access_token"]
       client = linkedin.LinkedInApplication(token=token)

       response = client.submit_share(
           comment=content,
           visibility_code='anyone'
       )

       return {
           "success": True,
           "post_id": response["updateKey"],
           "post_url": response["updateUrl"]
       }
   ```

5. **Update Credentials Storage**

   ```bash
   # Store LinkedIn OAuth2 credentials
   python -c "
   from watchers.shared.keychain import KeychainManager
   km = KeychainManager()
   km.set_credential('linkedin', {
       'client_id': 'YOUR_CLIENT_ID',
       'client_secret': 'YOUR_CLIENT_SECRET',
       'access_token': 'YOUR_ACCESS_TOKEN',
       'refresh_token': 'YOUR_REFRESH_TOKEN'
   })
   "
   ```

**API Access Requirements**:
- LinkedIn app must be associated with a company page
- API access requires approval from LinkedIn
- Some endpoints require Marketing Developer Platform access

**Cost Considerations**:
- LinkedIn API is free for basic usage
- Marketing Developer Platform may have costs for advanced features

**Timeline**: 3-5 days for migration (including approval wait time)

---

## Gmail Migration

### Current Implementation (Placeholder)

**Technology**: Placeholder implementation
- Returns mock data
- No real API integration

**Limitations**:
- Not functional
- No real email sending

### Target Implementation (Official)

**Technology**: Gmail API
- Official Google API
- OAuth2 authentication
- Production-ready

**Migration Steps**:

1. **Enable Gmail API**
   - Go to https://console.cloud.google.com/
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials.json

2. **Implement OAuth2 Flow**

   ```python
   # watchers/gmail_watcher/auth.py
   from google.oauth2.credentials import Credentials
   from google_auth_oauthlib.flow import InstalledAppFlow
   from google.auth.transport.requests import Request

   SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
             'https://www.googleapis.com/auth/gmail.send']

   def authenticate():
       creds = None
       token_path = 'watchers/.auth/gmail_token.json'

       if os.path.exists(token_path):
           creds = Credentials.from_authorized_user_file(token_path, SCOPES)

       if not creds or not creds.valid:
           if creds and creds.expired and creds.refresh_token:
               creds.refresh(Request())
           else:
               flow = InstalledAppFlow.from_client_secrets_file(
                   'credentials.json', SCOPES)
               creds = flow.run_local_server(port=0)

           with open(token_path, 'w') as token:
               token.write(creds.to_json())

       return creds
   ```

3. **Update MCP Tool**

   ```python
   # mcp-servers/digital-fte-server/tools/send_email.py
   from googleapiclient.discovery import build
   from email.mime.text import MIMEText
   import base64

   def execute(self, recipient: str, subject: str, body: str):
       creds = self._get_credentials()
       service = build('gmail', 'v1', credentials=creds)

       message = MIMEText(body)
       message['to'] = recipient
       message['subject'] = subject

       raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

       result = service.users().messages().send(
           userId='me',
           body={'raw': raw}
       ).execute()

       return {
           "success": True,
           "message_id": result['id'],
           "thread_id": result['threadId']
       }
   ```

**Cost Considerations**:
- Gmail API is free for personal use
- Workspace accounts may have quotas

**Timeline**: 1-2 days for migration

---

## Migration Checklist

### Pre-Migration

- [ ] Create accounts for official APIs (WhatsApp Business, LinkedIn Developer, Google Cloud)
- [ ] Request API access and wait for approval
- [ ] Review API documentation and rate limits
- [ ] Estimate costs for production usage
- [ ] Back up current implementation

### During Migration

- [ ] Implement OAuth2 flows for each service
- [ ] Update watcher implementations
- [ ] Update MCP tool implementations
- [ ] Update credential storage
- [ ] Test authentication flows
- [ ] Test message sending/receiving
- [ ] Verify rate limiting works correctly

### Post-Migration

- [ ] Monitor API usage and costs
- [ ] Set up alerts for API errors
- [ ] Update documentation
- [ ] Remove unofficial API dependencies
- [ ] Archive old implementation code

---

## Testing Strategy

### Unit Tests

```python
# tests/test_whatsapp_official.py
def test_send_message():
    tool = WhatsAppSendTool()
    result = tool.execute("+1234567890", "Test message")
    assert result["success"] == True
    assert "message_id" in result

# tests/test_linkedin_official.py
def test_create_post():
    tool = LinkedInPostTool()
    result = tool.execute("Test post content")
    assert result["success"] == True
    assert "post_id" in result
```

### Integration Tests

```python
# tests/integration/test_end_to_end.py
def test_email_approval_workflow():
    # 1. Invoke send-email tool
    # 2. Verify action queued for approval
    # 3. Approve action
    # 4. Verify email sent via Gmail API
    pass
```

---

## Rollback Plan

If migration fails or issues arise:

1. **Revert to unofficial APIs**
   ```bash
   git checkout main
   git revert <migration-commit>
   ```

2. **Restore credentials**
   ```bash
   # Restore old session cookies/tokens
   ```

3. **Restart services**
   ```bash
   # Restart watchers with old implementation
   python watchers/whatsapp_watcher/watcher.py
   ```

---

## Support Resources

- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp
- **LinkedIn API**: https://docs.microsoft.com/en-us/linkedin/
- **Gmail API**: https://developers.google.com/gmail/api

---

## Timeline Summary

| Service | Migration Time | Approval Wait | Total |
|---------|---------------|---------------|-------|
| Gmail | 1-2 days | None | 1-2 days |
| WhatsApp | 2-3 days | 1-2 days | 3-5 days |
| LinkedIn | 3-5 days | 3-7 days | 6-12 days |

**Total Estimated Time**: 2-3 weeks (including approval wait times)

---

**Last Updated**: 2026-03-31
