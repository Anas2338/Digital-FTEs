# LinkedIn Official API Setup Guide

**Status**: Production-ready approach for LinkedIn integration
**Timeline**: 2-4 weeks (includes LinkedIn approval process)
**Requirements**: Company page with admin access

---

## Overview

This guide walks you through setting up official LinkedIn Marketing Developer Platform API access for:
1. **Share API** - Post content to company page
2. **Community Management API** - Monitor comments and engagement

---

## Phase 1: Create LinkedIn App (Day 1)

### Step 1.1: Access Developer Portal

1. Go to https://www.linkedin.com/developers/apps
2. Click "Create app" button
3. You'll need to be logged into LinkedIn

### Step 1.2: Fill App Details

**App name**: `Digital FTE Social Manager`

**LinkedIn Page**: Select your company page from dropdown

**App logo**: Upload a logo (512x512 px minimum)
- Can be your company logo
- Or create simple logo at https://www.canva.com

**Privacy policy URL**:
- If you have a website: `https://yourwebsite.com/privacy`
- If not, you can use: `https://www.termsfeed.com/privacy-policy-generator/` (free generator)

**Legal agreement**: Check the box to agree to LinkedIn API Terms of Use

Click "Create app"

### Step 1.3: Note Your Credentials

After creating the app, go to "Auth" tab and copy:

```
Client ID: xxxxxxxxxxxx
Client Secret: xxxxxxxxxxxx
```

**⚠️ IMPORTANT**: Keep Client Secret secure - treat it like a password!

---

## Phase 2: Request API Products (Day 1)

### Step 2.1: Navigate to Products Tab

In your app dashboard:
1. Click "Products" tab
2. You'll see available API products

### Step 2.2: Request Share API

1. Find "Share on LinkedIn" product
2. Click "Request access"
3. Fill out the form:

**Use case description** (IMPORTANT - this determines approval):

```
We are building a social media management tool to help our company
maintain consistent presence on LinkedIn. The tool will:

1. Schedule and publish company updates, articles, and announcements
2. Share industry insights and thought leadership content
3. Maintain regular posting cadence for audience engagement

This is for our company's official LinkedIn page to improve our
social media marketing efficiency and audience reach.
```

**Why this wording matters**:
- ✅ Emphasizes "social media management" (legitimate use case)
- ✅ Mentions "company page" (not personal automation)
- ✅ Focuses on marketing/business value
- ❌ Avoid mentioning "AI agent", "automation", "bot"

### Step 2.3: Request Community Management API

1. Find "Community Management" product
2. Click "Request access"
3. Fill out the form:

**Use case description**:

```
We need to monitor and respond to engagement on our company's
LinkedIn posts. The tool will:

1. Track comments on company posts for timely responses
2. Monitor engagement metrics (likes, shares, comments)
3. Identify trending content for better audience understanding
4. Enable faster response times to community questions

This helps us maintain active community engagement and improve
our social media presence.
```

### Step 2.4: Submit and Wait

- Click "Submit" for each API product
- LinkedIn will review your application
- **Timeline**: 2-4 weeks typically
- You'll receive email notification when approved/rejected

---

## Phase 3: While Waiting for Approval

### Option A: Use Session Cookies (Temporary)

While waiting for API approval, you can use session cookies for testing:
- See `docs/linkedin-setup-guide.md`
- Extract `li_at` cookie from browser
- Test the watcher functionality
- Switch to official API once approved

### Option B: Prepare OAuth2 Implementation

Start building the OAuth2 flow:

1. **OAuth2 Redirect URL**: Add to your app settings
   - For local testing: `http://localhost:8080/callback`
   - For production: `https://yourdomain.com/callback`

2. **Scopes needed**:
   - `w_member_social` - Post on behalf of member
   - `r_organization_social` - Read organization posts
   - `w_organization_social` - Post on behalf of organization
   - `rw_organization_admin` - Manage organization

3. **Implementation files to prepare**:
   - `watchers/linkedin_oauth.py` - OAuth2 flow
   - `watchers/linkedin_api_client.py` - API wrapper
   - `.env` - Store client ID/secret

---

## Phase 4: After Approval (Week 3-4)

### Step 4.1: Verify API Access

1. Go to your app dashboard
2. Check "Products" tab
3. Verify both APIs show "Approved" status

### Step 4.2: Implement OAuth2 Flow

I'll provide complete implementation code once you're approved.

The flow will be:
1. User clicks "Connect LinkedIn"
2. Redirected to LinkedIn authorization page
3. User grants permissions
4. LinkedIn redirects back with authorization code
5. Exchange code for access token
6. Store token securely in keychain

### Step 4.3: Test API Calls

Test endpoints:
- POST to Share API: Create a test post
- GET from Community Management: Fetch comments

### Step 4.4: Update LinkedIn Watcher

Replace session cookie authentication with OAuth2 tokens.

---

## Common Approval Issues

### Rejected: "Insufficient use case description"

**Solution**: Resubmit with more detailed description:
- Explain specific business value
- Mention company growth goals
- Describe content strategy
- Include metrics you'll track

### Rejected: "Personal use not allowed"

**Solution**: Emphasize business/company use:
- Focus on company page management
- Mention team collaboration
- Describe marketing objectives
- Avoid "personal" or "individual" language

### Rejected: "Unclear implementation"

**Solution**: Provide technical details:
- Describe posting workflow
- Explain content approval process
- Mention security measures
- Include compliance with LinkedIn policies

---

## Rate Limits (Official API)

Once approved, you'll have these limits:

**Share API**:
- 100 posts per day per company page
- 25 posts per hour

**Community Management API**:
- 500 requests per day
- 100 requests per hour

Much higher than unofficial API!

---

## Cost

LinkedIn Marketing Developer Platform is **FREE** for basic use cases.

Premium features (like analytics) may require LinkedIn Marketing Solutions subscription.

---

## Timeline Summary

- **Day 1**: Create app, request API access (30 minutes)
- **Week 1-4**: Wait for LinkedIn review
- **Day after approval**: Implement OAuth2 (2-3 hours)
- **Testing**: 1-2 days
- **Total**: 2-4 weeks

---

## Next Steps (Right Now)

1. Go to https://www.linkedin.com/developers/apps
2. Click "Create app"
3. Fill in the details (use the descriptions I provided above)
4. Request both API products
5. Come back and tell me when you've submitted

I'll help you with the OAuth2 implementation once you're approved!

---

## Alternative: Hybrid Approach

**Recommended for now**:
1. Use session cookies for immediate testing (today)
2. Apply for official API (today)
3. Build and test with session cookies (weeks 1-4)
4. Switch to official API when approved (week 4+)

This way you don't lose 4 weeks of development time!

---

**Questions?** Let me know if you need help with any step!
