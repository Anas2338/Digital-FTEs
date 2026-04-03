# Research & Technology Decisions: Gold Tier

**Feature**: 001-gold-tier-autonomous  
**Date**: 2026-03-31  
**Status**: Complete

## Overview

This document captures research findings and technology decisions for Gold Tier implementation. All decisions align with the Digital FTE constitution (local-first, privacy-first, Python 3.11+, uv package manager) and build upon Bronze/Silver tier patterns.

---

## 1. Odoo JSON-RPC Integration

### Research Question
How to integrate with Odoo Community Edition (self-hosted) for transaction tracking?

### Options Evaluated

| Library | Pros | Cons | Verdict |
|---------|------|------|---------|
| **OdooRPC** | Clean API, well-maintained, supports Odoo 8-17+, JSON-RPC and XML-RPC | Requires manual version compatibility checks | ✅ **SELECTED** |
| erppeek | Simpler API, good for scripting | Less actively maintained, limited Odoo 19 support | ❌ Rejected |
| Direct XML-RPC | No dependencies, full control | Verbose, error-prone, requires manual protocol handling | ❌ Rejected |

### Decision: OdooRPC

**Rationale**:
- Active maintenance with Odoo 19 support
- Clean Pythonic API: `odoo.env['account.move'].search_read([('state', '=', 'posted')])`
- Built-in session management and authentication
- Supports both JSON-RPC (faster) and XML-RPC (fallback)
- Aligns with constitution's preference for well-maintained libraries

**Installation**: `uv add odoorpc`

**Authentication Pattern**:
```python
import odoorpc

# Connect to Odoo instance
odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('database_name', 'username', 'password')

# Query transactions
moves = odoo.env['account.move'].search_read(
    [('create_date', '>=', last_check_time)],
    ['name', 'date', 'amount_total', 'partner_id', 'move_type']
)
```

**Error Handling**:
- Connection errors: Retry with exponential backoff (1s, 2s, 4s per constitution)
- Authentication errors: Notify user, don't retry (credentials issue)
- API errors: Log and escalate to circuit breaker

---

## 2. Social Media APIs

### 2.1 Facebook Graph API

**Decision**: Use official Facebook Graph API v19.0 with `facebook-sdk` library

**Rationale**:
- Official API ensures stability and compliance with platform terms
- `facebook-sdk` is the most popular Python wrapper (10k+ stars)
- Supports posting, engagement metrics, page management

**Installation**: `uv add facebook-sdk`

**Required Permissions**:
- `pages_manage_posts` - Post to Facebook pages
- `pages_read_engagement` - Read engagement metrics
- `pages_read_user_content` - Read page content

**API Pattern**:
```python
import facebook

graph = facebook.GraphAPI(access_token=token)
# Post to page
graph.put_object(parent_object='page_id', connection_name='feed', message='content')
# Get engagement
insights = graph.get_object(id='post_id', fields='likes.summary(true),comments.summary(true),shares')
```

**Rate Limits**: 200 calls/hour per user (well above our 10 posts/day limit)

### 2.2 Instagram Graph API

**Decision**: Use official Instagram Graph API (requires Business Account) with `facebook-sdk`

**Rationale**:
- Instagram Graph API is part of Facebook Graph API (same library)
- Requires Instagram Business Account (documented in quickstart)
- Stable, compliant with platform terms
- Unofficial APIs (instagrapi) risk account bans

**Required Setup**:
1. Convert Instagram account to Business Account
2. Link to Facebook Page
3. Use Facebook Graph API with Instagram endpoints

**API Pattern**:
```python
# Post to Instagram (requires media upload first)
media = graph.post(f'{instagram_account_id}/media', 
                   image_url=image_url, caption=caption)
graph.post(f'{instagram_account_id}/media_publish', creation_id=media['id'])

# Get engagement
insights = graph.get_object(id='media_id', 
                           fields='like_count,comments_count,engagement')
```

**Limitation**: Cannot post videos >60 seconds (documented in constraints)

### 2.3 Twitter/X API v2

**Decision**: Use `tweepy` v4.14+ for Twitter API v2 access

**Rationale**:
- Official Twitter-recommended library
- Full API v2 support (posting, metrics, media upload)
- Active maintenance, 10k+ stars
- Handles OAuth 2.0 authentication

**Installation**: `uv add tweepy`

**Required Access**: Twitter API v2 with "Read and Write" permissions

**API Pattern**:
```python
import tweepy

client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret
)

# Post tweet
response = client.create_tweet(text='content', media_ids=[media_id])

# Get engagement
tweet = client.get_tweet(id=tweet_id, tweet_fields=['public_metrics'])
metrics = tweet.data.public_metrics  # likes, retweets, replies, impressions
```

**Rate Limits**: 
- Posting: 300 tweets/3 hours (well above our 10/day limit)
- Reading: 900 requests/15 minutes

---

## 3. Circuit Breaker Pattern

### Research Question
How to implement circuit breaker for graceful degradation?

### Options Evaluated

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Custom Implementation** | Full control, no dependencies, tailored to our needs | More code to maintain | ✅ **SELECTED** |
| pybreaker library | Battle-tested, feature-rich | Adds dependency, may be overkill | ❌ Rejected |
| tenacity library | Good for retries, has circuit breaker | Primarily retry-focused, complex config | ❌ Rejected |

### Decision: Custom Circuit Breaker

**Rationale**:
- Simple requirements: track error rate, disable at 20%, recover with exponential backoff
- Constitution emphasizes simplicity and minimal dependencies
- ~100 lines of code vs external dependency
- Full control over recovery schedule (5min, 10min, 20min, hourly)

**Implementation Pattern**:
```python
class CircuitBreaker:
    def __init__(self, error_threshold=0.20, window_size=10):
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.error_count = 0
        self.success_count = 0
        self.window_size = window_size
        self.last_failure_time = None
        self.recovery_schedule = [300, 600, 1200, 3600]  # 5m, 10m, 20m, 1h
        self.recovery_attempt = 0
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if self._should_attempt_recovery():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_failure(self):
        self.error_count += 1
        if self.error_count / (self.error_count + self.success_count) >= 0.20:
            self.state = 'OPEN'
            self.last_failure_time = time.time()
    
    def _should_attempt_recovery(self):
        if not self.last_failure_time:
            return False
        elapsed = time.time() - self.last_failure_time
        delay = self.recovery_schedule[min(self.recovery_attempt, len(self.recovery_schedule)-1)]
        return elapsed >= delay
```

**State Transitions**:
- CLOSED → OPEN: When error rate exceeds 20%
- OPEN → HALF_OPEN: After recovery delay (exponential backoff)
- HALF_OPEN → CLOSED: On successful call
- HALF_OPEN → OPEN: On failed call (increment recovery attempt)

---

## 4. Duplicate Transaction Detection

### Research Question
How to detect duplicate transactions in accounting system?

### Decision: Multi-Factor Matching Algorithm

**Algorithm** (from spec clarification):
- Match by amount (exact)
- Match by date (within 24-hour window)
- Match by description similarity (>80% using Levenshtein distance)

**Rationale**:
- Handles timing variations (transactions may arrive with slight delays)
- Description similarity catches typos and minor variations
- 24-hour window prevents false positives from recurring transactions

**Implementation**:
```python
from difflib import SequenceMatcher

def is_duplicate(new_txn, existing_txns):
    for existing in existing_txns:
        # Check amount match
        if new_txn.amount != existing.amount:
            continue
        
        # Check date within 24-hour window
        time_diff = abs((new_txn.date - existing.date).total_seconds())
        if time_diff > 86400:  # 24 hours
            continue
        
        # Check description similarity
        similarity = SequenceMatcher(None, new_txn.description, existing.description).ratio()
        if similarity > 0.80:
            return True
    
    return False
```

**Storage**: SQLite table with indexed columns (amount, date) for fast lookups

---

## 5. CEO Briefing Generation

### Research Question
How to generate formatted briefings with charts?

### Options Evaluated

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Markdown + ASCII Charts** | Simple, readable in Obsidian, no dependencies | Limited visual appeal | ✅ **SELECTED** |
| matplotlib | Professional charts, PNG export | Requires display backend, heavy dependency | ❌ Rejected |
| plotly | Interactive charts, HTML export | Not readable in Obsidian, requires browser | ❌ Rejected |

### Decision: Markdown with ASCII Charts

**Rationale**:
- Obsidian renders Markdown natively
- ASCII charts readable in any text editor
- No external dependencies (use built-in string formatting)
- Aligns with local-first principle (no image files to manage)

**Chart Library**: Use simple ASCII bar charts with Unicode box-drawing characters

**Example Output**:
```markdown
# Weekly CEO Briefing: Week 14, 2026

**Period**: March 31 - April 6, 2026  
**Generated**: 2026-04-07 08:00 AM

## 📊 Financial Summary

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Revenue | $12,450 | $10,200 | +22% ↑ |
| Expenses | $3,200 | $3,500 | -9% ↓ |
| Profit | $9,250 | $6,700 | +38% ↑ |

### Revenue Trend (Last 4 Weeks)
```
Week 11: ████████░░ $8,500
Week 12: ██████████ $10,200
Week 13: ████████░░ $9,100
Week 14: ████████████ $12,450
```

## 📱 Social Media Performance

| Platform | Posts | Engagement | Top Post |
|----------|-------|------------|----------|
| Facebook | 3 | 245 reactions | "Product Launch" (120 likes) |
| Instagram | 5 | 380 likes | "Behind the Scenes" (95 likes) |
| Twitter | 7 | 156 interactions | "Industry News" (45 retweets) |

## ✅ Tasks Completed: 12
## ⚠️ Requires Attention: 2

1. **High Priority**: Invoice #1234 overdue by 5 days
2. **Medium Priority**: Social media engagement down 15% on Twitter
```

**Generation Frequency**: Every Monday at 8:00 AM local time

---

## 6. Scheduling for Weekly Tasks

### Research Question
How to schedule weekly CEO briefing generation?

### Options Evaluated

| Library | Pros | Cons | Verdict |
|---------|------|------|---------|
| **schedule** | Simple, Pythonic, lightweight | Requires running loop | ✅ **SELECTED** |
| APScheduler | Feature-rich, persistent jobs | Overkill for single weekly task | ❌ Rejected |
| cron | Native OS scheduling | Platform-specific, harder to test | ❌ Rejected |

### Decision: `schedule` Library

**Rationale**:
- Simple API: `schedule.every().monday.at("08:00").do(generate_briefing)`
- Integrates with existing watcher pattern (runs in watcher loop)
- Lightweight (no dependencies)
- Easy to test (can trigger manually)

**Installation**: `uv add schedule`

**Implementation Pattern**:
```python
import schedule
import time

def briefing_watcher_loop():
    schedule.every().monday.at("08:00").do(generate_ceo_briefing)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

**Timezone Handling**: Use local system time (per spec assumption: "User's business operates primarily in a single timezone")

---

## 7. Exponential Backoff Implementation

### Decision: Built-in Implementation

**Pattern** (from constitution and spec):
- Initial retry: 1 second
- Second retry: 2 seconds
- Third retry: 4 seconds
- Circuit breaker: 5min, 10min, 20min, then hourly

**Implementation**:
```python
def retry_with_backoff(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(delay)
```

**Rationale**: Simple, no dependencies, matches constitution requirements exactly

---

## 8. Audit Logging

### Research Question
How to implement tamper-evident audit logging with PII redaction?

### Decision: Structured Markdown Logs with Hash Chains

**Log Format**: Daily Markdown files in `obsidian-vault/Audit_Logs/YYYY-MM-DD.md`

**Structure**:
```markdown
# Audit Log: 2026-03-31

## Entry 001 - 08:15:23
- **Action**: odoo_record_transaction
- **Parameters**: amount=150.00, category=Revenue, description=[REDACTED]
- **Result**: SUCCESS
- **Reasoning**: New invoice detected in Odoo, categorized as Revenue based on account code
- **User Approval**: N/A (Level 0 action)
- **Hash**: sha256:abc123...

## Entry 002 - 08:20:45
- **Action**: social_post
- **Parameters**: platforms=[facebook, instagram], content=[REDACTED]
- **Result**: SUCCESS
- **Reasoning**: Scheduled post approved by user on 2026-03-30
- **User Approval**: 2026-03-30 14:30:00 (Level 2 action)
- **Hash**: sha256:def456...
```

**PII Redaction Rules**:
- Transaction descriptions: Show first 20 chars only
- Email addresses: Mask domain (user@****)
- Phone numbers: Mask middle digits (555-***-1234)
- API keys: Never log (show "***" only)

**Tamper Evidence**: Each entry includes SHA-256 hash of previous entry + current entry content

**Storage**: SQLite database for queryable logs + Markdown for human readability

---

## 9. Transaction Categorization

### Decision: Rule-Based Categorization with ML Fallback (Future)

**Phase 1 (Gold Tier)**: Rule-based categorization using Odoo account codes

**Categorization Logic**:
```python
CATEGORY_MAPPING = {
    'Revenue': ['400', '401', '402'],  # Odoo account codes
    'COGS': ['500', '501'],
    'Operating Expenses': ['600', '601', '602', '603'],
    'Assets': ['100', '101', '102'],
    'Liabilities': ['200', '201'],
    'Equity': ['300', '301']
}

def categorize_transaction(transaction):
    account_code = transaction.account_id.code[:3]
    for category, codes in CATEGORY_MAPPING.items():
        if account_code in codes:
            return category
    return 'Uncategorized'  # Requires user clarification
```

**User Clarification**: When category is 'Uncategorized', create task in Obsidian vault for user review

**Phase 2 (Future)**: Train ML model on user-categorized transactions for automatic categorization

---

## 10. Cross-Platform Keychain Access

### Decision: Use Existing `keychain.py` from Bronze/Silver Tier

**Rationale**:
- Already implemented and tested across Windows/macOS/Linux
- Uses `keyring` library (Python standard for OS keychain access)
- Handles platform differences transparently

**New Credentials to Store**:
- Odoo: `odoo_url`, `odoo_database`, `odoo_username`, `odoo_password`
- Facebook: `facebook_access_token`, `facebook_page_id`
- Instagram: `instagram_account_id`, `instagram_access_token`
- Twitter: `twitter_api_key`, `twitter_api_secret`, `twitter_access_token`, `twitter_access_secret`

**Storage Pattern**:
```python
from watchers.shared.keychain import store_credential, get_credential

# Store
store_credential('digital-fte', 'odoo_password', password)

# Retrieve
password = get_credential('digital-fte', 'odoo_password')
```

---

## Summary of Technology Decisions

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Odoo Integration | OdooRPC | Clean API, Odoo 19 support, JSON-RPC |
| Facebook API | facebook-sdk | Official, stable, well-maintained |
| Instagram API | Instagram Graph API (via facebook-sdk) | Official, requires Business Account |
| Twitter API | tweepy v4.14+ | Official, API v2 support |
| Circuit Breaker | Custom implementation | Simple, no dependencies, tailored |
| Duplicate Detection | Multi-factor matching (amount + date + description) | Handles timing variations, robust |
| CEO Briefing | Markdown + ASCII charts | Obsidian-native, no dependencies |
| Scheduling | schedule library | Simple, Pythonic, lightweight |
| Audit Logging | Markdown + SQLite + hash chains | Human-readable, queryable, tamper-evident |
| Keychain | Existing keyring library | Already implemented, cross-platform |

**All decisions align with constitution principles**: local-first, privacy-first, Python 3.11+, uv package manager, minimal dependencies, separation of concerns.

---

## Next Steps

1. ✅ Research complete
2. ⏭️ Phase 1: Generate data-model.md
3. ⏭️ Phase 1: Generate API contracts (contracts/*.yaml)
4. ⏭️ Phase 1: Generate quickstart.md
5. ⏭️ Phase 2: Run /sp.tasks to generate implementation tasks
