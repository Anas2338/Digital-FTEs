# Gmail API Setup Guide

## Prerequisites

- Google account with Gmail access
- Google Cloud Console access

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Name it "Digital FTE" or similar

## Step 2: Enable Gmail API

1. In Google Cloud Console, go to **APIs & Services > Library**
2. Search for "Gmail API"
3. Click **Enable**

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (for personal use)
   - App name: "Digital FTE"
   - User support email: your email
   - Developer contact: your email
   - Scopes: Add `gmail.readonly` and `gmail.send`
   - Test users: Add your email
   - Save and continue
4. Back to Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: "Digital FTE Desktop"
   - Click **Create**
5. Download the credentials JSON file
6. Rename it to `credentials.json`
7. Place it in project root: `D:\GIAIC\Agentic-AI\Digital-FTEs\credentials.json`

## Step 4: Test Authentication

```bash
# From project root
python test_gmail_auth.py
```

This will:
1. Open a browser window
2. Ask you to sign in to Google
3. Request permission to read and send emails
4. Save token to `watchers/.auth/gmail_token.json`

## Step 5: Verify Integration

### Test Gmail Watcher

```bash
cd watchers
python -m gmail_watcher.watcher
```

Expected output:
- "Gmail authentication successful"
- "Label ID: <label_id>"
- Polls every 180 seconds for emails with "ToVault" label

### Test Send Email Tool

```bash
cd mcp-servers/digital-fte-server
python -c "
from tools.send_email import SendEmailTool
tool = SendEmailTool()
result = tool.execute(
    recipient='your-email@gmail.com',
    subject='Test from Digital FTE',
    body='This is a test email from the Digital FTE system.'
)
print(result)
"
```

Expected output:
```json
{
  "success": true,
  "message_id": "...",
  "thread_id": "...",
  "recipient": "your-email@gmail.com",
  "subject": "Test from Digital FTE",
  "timestamp": "2026-03-31T..."
}
```

## Troubleshooting

### "credentials.json not found"
- Ensure file is in project root
- Check file name is exactly `credentials.json` (case-sensitive)

### "Access blocked: This app's request is invalid"
- OAuth consent screen not configured
- Go back to Step 3 and configure consent screen

### "Token has been expired or revoked"
- Delete `watchers/.auth/gmail_token.json`
- Run authentication again

### "Insufficient Permission"
- Check OAuth scopes include `gmail.readonly` and `gmail.send`
- Delete token and re-authenticate

## Security Notes

- **Never commit credentials.json to git** (already in .gitignore)
- Token is stored in `watchers/.auth/gmail_token.json` (also in .gitignore)
- Tokens expire after 7 days of inactivity
- Refresh tokens are automatically handled by the authentication module

## Rate Limits

- Gmail API: 250 quota units per user per second
- Sending emails: 100 per day (free tier)
- Reading emails: Unlimited

The MCP server enforces a 100 emails/day limit via rate limiter.
