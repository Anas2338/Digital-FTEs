# LinkedIn Integration Setup Guide

## Overview

LinkedIn integration uses the unofficial `linkedin-api` library which requires your browser session cookies. This is simpler than OAuth2 but requires manual cookie extraction.

**⚠️ Security Note**: Your LinkedIn cookies provide full access to your account. Store them securely and never commit them to git.

---

## Step 1: Extract LinkedIn Session Cookies

### Method 1: Chrome/Edge (Recommended)

1. **Open LinkedIn in Chrome/Edge**
   - Go to https://www.linkedin.com
   - Make sure you're logged in

2. **Open Developer Tools**
   - Press `F12` or `Ctrl+Shift+I`
   - Go to "Application" tab (or "Storage" in Firefox)

3. **Find Cookies**
   - In left sidebar: Storage → Cookies → https://www.linkedin.com
   - Look for these cookies:
     - `li_at` (required) - Your authentication token
     - `JSESSIONID` (optional) - Session ID

4. **Copy Cookie Values**
   - Click on `li_at` cookie
   - Copy the entire "Value" field (starts with "AQ...")
   - It should be ~200-300 characters long

### Method 2: Firefox

1. Open LinkedIn and log in
2. Press `F12` → Storage tab
3. Cookies → https://www.linkedin.com
4. Find and copy `li_at` value

### Method 3: Using Browser Extension

Install "Cookie Editor" extension:
- Chrome: https://chrome.google.com/webstore (search "Cookie Editor")
- Firefox: https://addons.mozilla.org/firefox/ (search "Cookie Editor")

1. Click extension icon while on LinkedIn
2. Find `li_at` cookie
3. Copy value

---

## Step 2: Store Cookies Securely

### Option A: Environment Variable (Quick Test)

Create `.env` file in `watchers/` directory:

```bash
# watchers/.env
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_LI_AT=AQEDARxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**⚠️ Important**: Add `.env` to `.gitignore` (already done)

### Option B: OS Keychain (Production - Recommended)

Store in Windows Credential Manager / macOS Keychain:

```python
# Run this once to store credentials
python -c "
from watchers.shared.keychain import KeychainManager
km = KeychainManager()
km.set_credential('linkedin', {
    'email': 'your-email@example.com',
    'li_at': 'AQEDARxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
})
print('LinkedIn credentials stored in keychain')
"
```

---

## Step 3: Test LinkedIn Connection

Create test script:

```python
# watchers/test_linkedin.py
from linkedin_api import Linkedin

# Replace with your credentials
email = "your-email@example.com"
li_at_cookie = "AQEDARxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

try:
    # Initialize LinkedIn client
    api = Linkedin(email, authenticate=False)
    api.client.cookies.set('li_at', li_at_cookie, domain='.linkedin.com')

    # Test: Get your profile
    profile = api.get_profile()
    print(f"✓ Connected as: {profile['firstName']} {profile['lastName']}")

    # Test: Get notifications
    notifications = api.get_notifications()
    print(f"✓ Found {len(notifications)} notifications")

except Exception as e:
    print(f"✗ Connection failed: {e}")
```

Run test:
```bash
cd watchers
uv run python test_linkedin.py
```

---

## Step 4: Configure LinkedIn Watcher

Edit `watchers/linkedin_watcher/config.py`:

```python
LINKEDIN_EMAIL = "your-email@example.com"  # Or load from env/keychain
POLLING_INTERVAL = 300  # 5 minutes
```

---

## Step 5: Start LinkedIn Watcher

```bash
cd watchers
uv run python -m linkedin_watcher.watcher
```

Expected output:
```
[linkedin] Starting watcher (polling every 300s)
[linkedin] LinkedIn authentication successful
[linkedin] Monitoring notifications...
```

---

## What LinkedIn Watcher Monitors

1. **Messages** - New LinkedIn messages
2. **Connection Requests** - New connection requests
3. **Post Mentions** - When someone mentions you in a post
4. **Comments** - Comments on your posts
5. **Reactions** - Reactions to your posts

All events are saved to `obsidian-vault/Inbox/` as notes.

---

## Troubleshooting

### "Invalid session" error

**Cause**: Cookie expired or invalid

**Solution**:
1. Log out of LinkedIn
2. Log back in
3. Extract fresh `li_at` cookie
4. Update stored credentials

### "Rate limit exceeded" error

**Cause**: Too many API requests

**Solution**:
1. Increase polling interval to 600s (10 minutes)
2. Wait 1 hour before retrying
3. LinkedIn has strict rate limits on unofficial API

### "Account restricted" warning

**Cause**: LinkedIn detected unusual activity

**Solution**:
1. Stop the watcher immediately
2. Log into LinkedIn manually
3. Complete any security challenges
4. Consider using official LinkedIn API (see migration guide)

---

## Cookie Expiration

LinkedIn cookies typically expire after:
- **30 days** of inactivity
- **Logout** from any device
- **Password change**

When cookies expire:
1. Extract fresh cookies from browser
2. Update stored credentials
3. Restart watcher

---

## Security Best Practices

1. **Never commit cookies to git** - Already in .gitignore
2. **Use OS keychain** - More secure than .env files
3. **Rotate cookies regularly** - Extract fresh cookies monthly
4. **Monitor for suspicious activity** - Check LinkedIn security settings
5. **Use dedicated account** - Consider using a separate LinkedIn account for automation

---

## Migration to Official API

For production use, migrate to LinkedIn Marketing Developer Platform:
- See `docs/migration-to-official-apis.md`
- Requires company page and API approval
- More stable and secure
- Higher rate limits

---

## Rate Limits (Unofficial API)

- **Notifications**: ~100 requests/hour
- **Messages**: ~50 requests/hour
- **Profile views**: ~200 requests/hour

The watcher is configured to stay well below these limits with 5-minute polling.

---

## Next Steps

1. Extract `li_at` cookie from browser
2. Store in keychain or .env file
3. Run test script to verify connection
4. Start LinkedIn watcher
5. Send yourself a test LinkedIn message
6. Verify note appears in `obsidian-vault/Inbox/`

---

**Estimated Setup Time**: 10-15 minutes
**Difficulty**: Easy (just cookie extraction)
**Status**: Ready to implement
