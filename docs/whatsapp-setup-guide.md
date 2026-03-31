# WhatsApp Integration Setup Guide

**Status**: Ready to test - Phone authentication required
**Timeline**: 5-10 minutes
**Requirements**: WhatsApp on your phone, Node.js 18+

---

## How It Works

WhatsApp integration uses **whatsapp-web.js** library:
1. Node.js bridge connects to WhatsApp Web
2. You scan QR code with your phone (like WhatsApp Web)
3. Bridge receives messages and stores in JSON file
4. Python watcher polls the JSON file
5. Messages saved to Obsidian vault

**⚠️ Important**: This is the unofficial WhatsApp Web API. For production, migrate to WhatsApp Business API.

---

## Step 1: Install Node.js Dependencies (2 minutes)

```bash
cd watchers/whatsapp_watcher
npm install
```

This installs:
- `whatsapp-web.js` - WhatsApp Web client
- `qrcode-terminal` - QR code display in terminal

---

## Step 2: Start WhatsApp Bridge (1 minute)

```bash
node bridge.js
```

**Expected output**:
```
[WhatsApp Bridge] Starting WhatsApp Web.js client...
[WhatsApp Bridge] QR Code received. Scan with WhatsApp mobile app:
```

A QR code will appear in your terminal.

---

## Step 3: Scan QR Code with Phone (30 seconds)

1. **Open WhatsApp on your phone**
2. **Go to Settings**:
   - Android: Menu (⋮) → Linked Devices
   - iPhone: Settings → Linked Devices
3. **Tap "Link a Device"**
4. **Scan the QR code** displayed in your terminal

**After scanning**:
```
[WhatsApp Bridge] Authentication successful
[WhatsApp Bridge] Client is ready!
[WhatsApp Bridge] Listening for messages...
```

---

## Step 4: Test Message Reception (1 minute)

1. **Send yourself a test message**:
   - From another phone, send a WhatsApp message to yourself
   - Or use WhatsApp Web to send a message

2. **Check bridge output**:
```
[WhatsApp Bridge] Message from John Doe: Hello, this is a test...
```

3. **Verify messages.json created**:
```bash
cat watchers/whatsapp_watcher/messages.json
```

---

## Step 5: Start Python Watcher (2 minutes)

Open a **new terminal** (keep bridge running):

```bash
cd watchers
uv run python -m whatsapp_watcher.watcher
```

**Expected output**:
```
[whatsapp_watcher] Starting watcher (polling every 60s)
[whatsapp_watcher] WhatsApp bridge connected
[whatsapp_watcher] Monitoring messages...
```

---

## Step 6: Verify Vault Notes (1 minute)

Send another test message, then check:

```bash
ls -lt ../obsidian-vault/Inbox/ | head -5
```

You should see a new note like:
```
20260331-123456-whatsapp-message.md
```

---

## Architecture

```
┌─────────────────┐
│  WhatsApp Web   │
│   (Your Phone)  │
└────────┬────────┘
         │ QR Auth
         ↓
┌─────────────────┐
│   bridge.js     │  ← Node.js process
│ (whatsapp-web)  │     Receives messages
└────────┬────────┘
         │ JSON file
         ↓
┌─────────────────┐
│  watcher.py     │  ← Python process
│ (polls JSON)    │     Polls every 60s
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Obsidian Vault  │
│   /Inbox/*.md   │
└─────────────────┘
```

---

## Session Persistence

After first QR scan, session is saved in `.wwebjs_auth/` directory.

**Next time you start bridge.js**:
- No QR code needed
- Automatically reconnects
- Session lasts ~2 weeks

**If session expires**:
- Delete `.wwebjs_auth/` folder
- Restart bridge.js
- Scan QR code again

---

## Troubleshooting

### "npm: command not found"

**Solution**: Install Node.js
- Download from: https://nodejs.org/
- Install LTS version (18.x or 20.x)
- Restart terminal

### QR code not appearing

**Solution**:
1. Check Node.js version: `node --version` (should be 18+)
2. Delete `.wwebjs_auth/` folder
3. Restart bridge.js

### "Authentication failed"

**Solution**:
1. Make sure WhatsApp is active on your phone
2. Check internet connection
3. Delete `.wwebjs_auth/` and try again
4. Update WhatsApp app on phone

### Messages not appearing in vault

**Solution**:
1. Check bridge.js is running (should show "Client is ready!")
2. Check messages.json exists and has content
3. Check Python watcher is running
4. Verify vault path in watcher config

### Bridge crashes or disconnects

**Solution**:
1. WhatsApp Web session expired - scan QR again
2. Phone lost internet connection
3. WhatsApp app closed on phone
4. Restart bridge.js

---

## Rate Limits

WhatsApp has rate limits to prevent spam:
- **100 messages/day** to new contacts
- **1000 messages/day** to existing contacts
- **No limit** on receiving messages

The watcher respects these limits automatically.

---

## Security Notes

- ✅ Session stored locally in `.wwebjs_auth/` (in .gitignore)
- ✅ No credentials needed (uses QR code)
- ✅ Same security as WhatsApp Web
- ⚠️ Keep bridge.js running on trusted machine only
- ⚠️ Anyone with access to `.wwebjs_auth/` can access your WhatsApp

---

## Production Migration

For production use, migrate to **WhatsApp Business API**:
- Official API from Meta
- Higher rate limits
- Webhook-based (no polling)
- Requires business verification
- See `docs/migration-to-official-apis.md`

---

## Next Steps

1. Install dependencies: `npm install`
2. Start bridge: `node bridge.js`
3. Scan QR code with phone
4. Start Python watcher in new terminal
5. Send test message
6. Check Obsidian vault for new note

**Ready to start? Let me know when you're ready to run the commands!**
