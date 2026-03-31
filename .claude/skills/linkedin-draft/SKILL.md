# LinkedIn Draft Agent Skill

**Purpose**: AI-assisted LinkedIn post drafting with business context awareness

**Version**: 1.0.0

**Category**: Content Creation

---

## Description

This skill helps users draft professional LinkedIn posts for business development, announcements, and thought leadership. The agent analyzes business context from the Obsidian vault and suggests post content optimized for LinkedIn engagement.

---

## Commands

### draft-post

Draft a LinkedIn post based on a topic or business update.

**Usage:**
```
claude-code "Draft a LinkedIn post about [topic]"
```

**Parameters:**
- `topic`: The subject matter for the post (product launch, milestone, insight, etc.)
- `tone`: Optional tone (professional, casual, thought-leadership) - defaults to professional
- `length`: Optional length (short: 500 chars, medium: 1500 chars, long: 2500 chars) - defaults to medium

**Example:**
```
claude-code "Draft a LinkedIn post about our Q1 revenue milestone in a professional tone"
```

**Output:**
- Post content (optimized for LinkedIn)
- Character count
- Suggested hashtags
- Best posting time recommendation
- Engagement optimization tips

---

### schedule-post

Schedule a drafted post for future publication.

**Usage:**
```
claude-code "Schedule this LinkedIn post for [date/time]"
```

**Parameters:**
- `content`: Post content (from draft or user-provided)
- `scheduled_time`: ISO 8601 timestamp or natural language ("tomorrow 9am", "next Monday 2pm")

**Example:**
```
claude-code "Schedule this LinkedIn post for tomorrow at 9am EST"
```

**Result:**
- Creates note in `obsidian-vault/Content_Queue/` with frontmatter:
  ```yaml
  ---
  type: linkedin-post
  status: scheduled
  scheduled_time: 2026-03-31T13:00:00Z
  created: 2026-03-30T10:00:00Z
  ---
  ```
- Post will be queued for approval at scheduled time
- User will receive approval request before publication

---

### optimize-post

Analyze and optimize an existing post draft for LinkedIn engagement.

**Usage:**
```
claude-code "Optimize this LinkedIn post for engagement"
```

**Analysis includes:**
- Character count (target: 1300-2000 for optimal engagement)
- Readability score
- Hook strength (first 2 lines)
- Call-to-action presence
- Hashtag recommendations (3-5 relevant tags)
- Emoji usage suggestions (1-3 for personality)
- Line break optimization (improve scannability)

**Example:**
```
claude-code "Optimize this LinkedIn post: [paste content]"
```

---

## Post Templates

The agent has access to these LinkedIn post templates:

### Product Launch
```
🚀 Excited to announce [product_name]!

[Problem statement - what pain point does this solve?]

[Solution overview - how does your product help?]

Key features:
• [Feature 1]
• [Feature 2]
• [Feature 3]

[Call to action - link, demo request, etc.]

#ProductLaunch #[Industry] #Innovation
```

### Milestone Celebration
```
🎉 [Milestone achievement]!

[Context - why this matters]

This wouldn't be possible without:
• [Team/partner acknowledgment]
• [Customer acknowledgment]
• [Community acknowledgment]

[Forward-looking statement - what's next?]

Thank you to everyone who's been part of this journey.

#Milestone #Growth #[Industry]
```

### Thought Leadership
```
[Hook - controversial or thought-provoking statement]

Here's what I've learned about [topic]:

[Insight 1 with brief explanation]

[Insight 2 with brief explanation]

[Insight 3 with brief explanation]

[Conclusion - actionable takeaway]

What's your experience with [topic]? Let me know in the comments.

#ThoughtLeadership #[Industry] #[Topic]
```

---

## Variable Substitution

Posts support template variables that are automatically replaced:

- `{{company_name}}` - Company name from vault metadata
- `{{date}}` - Current date (formatted: March 30, 2026)
- `{{milestone}}` - Milestone value (e.g., "1M users", "$10M ARR")
- `{{product_name}}` - Product name from context
- `{{author_name}}` - Post author name
- `{{author_title}}` - Post author title/role

**Example:**
```
We're thrilled to announce that {{company_name}} has reached {{milestone}}!

This milestone represents {{date}} of hard work...
```

---

## Character Limit Enforcement

LinkedIn posts have a 3000 character limit. The agent will:

1. **Warn** if post exceeds 2500 characters (approaching limit)
2. **Truncate** if post exceeds 3000 characters with "... [Read more]" suffix
3. **Suggest** splitting long posts into carousel or thread format
4. **Optimize** for engagement sweet spot (1300-2000 characters)

---

## Best Practices

The agent follows these LinkedIn posting best practices:

1. **Hook in first 2 lines** - Capture attention before "see more" fold
2. **Use line breaks** - Improve readability (max 2-3 lines per paragraph)
3. **Include CTA** - Clear call-to-action (comment, share, visit link)
4. **3-5 hashtags** - Relevant, not spammy
5. **Tag people/companies** - Increase reach (when appropriate)
6. **Post timing** - Weekdays 8-10am or 12-2pm for B2B
7. **Visual content** - Suggest adding image/video when relevant
8. **Authenticity** - Personal voice over corporate speak

---

## Integration with Approval Workflow

All scheduled posts go through the approval workflow:

1. **Draft created** - Saved to Content_Queue with status: "draft"
2. **Scheduled** - Status updated to "scheduled" with timestamp
3. **Queued for approval** - At scheduled time, moved to Approvals folder
4. **User approves** - Post published to LinkedIn via MCP server
5. **Performance tracked** - Views, likes, comments recorded in note

---

## Performance Tracking

After publication, the agent tracks:

- **Views** - Total impressions
- **Likes** - Engagement count
- **Comments** - Discussion count
- **Shares** - Viral reach
- **Click-through rate** - Link clicks (if applicable)

Metrics are updated in post frontmatter:
```yaml
performance:
  views: 1250
  likes: 87
  comments: 12
  shares: 5
  ctr: 3.2%
  last_updated: 2026-03-31T15:00:00Z
```

---

## Error Handling

- **Rate limit exceeded**: Post rescheduled to next available slot
- **Authentication failure**: User notified to reconnect LinkedIn
- **Content policy violation**: Post flagged for manual review
- **Network error**: Retry with exponential backoff (3 attempts)

---

## Examples

### Example 1: Draft and Schedule Product Launch

```bash
# Draft the post
claude-code "Draft a LinkedIn post announcing our new AI-powered analytics dashboard"

# Agent generates optimized post with hashtags and CTA

# Schedule for publication
claude-code "Schedule this post for Monday at 9am EST"

# Post saved to Content_Queue, will be queued for approval Monday morning
```

### Example 2: Optimize Existing Draft

```bash
# User has draft in Content_Queue/product-launch-draft.md

claude-code "Optimize the product launch draft for engagement"

# Agent analyzes and suggests improvements:
# - Stronger hook
# - Better line breaks
# - More specific hashtags
# - Add emoji for personality
```

### Example 3: Template-Based Post

```bash
claude-code "Create a milestone post using the template: We hit 10,000 users!"

# Agent uses Milestone template, substitutes variables:
# {{company_name}} → "Digital FTE"
# {{milestone}} → "10,000 users"
# {{date}} → "March 2026"
```

---

## Notes

- All posts require approval before publication (Safety Level 2)
- Draft posts can be edited manually in Content_Queue folder
- Performance metrics updated every 24 hours after publication
- Posts older than 90 days archived to Content_Queue/Archive/
