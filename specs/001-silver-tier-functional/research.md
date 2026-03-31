# Research: Silver Tier Functional Assistant

**Feature**: 001-silver-tier-functional
**Date**: 2026-03-30
**Purpose**: Resolve technical unknowns and document architectural decisions before implementation

## Research Topics

### 1. Gemini Compatibility for Agent Skills

**Decision**: All new agent skills will be compatible with both Claude Code and Gemini via MCP adapter layer

**Rationale**:
- Agent skills are prompt-based definitions in `.claude/skills/*/SKILL.md` format
- Skills invoke tools via MCP protocol, which is LLM-agnostic
- MCP adapter layer (from constitution) translates MCP protocol to Gemini's function calling API
- No skill-specific code changes needed for dual-tier support

**Implementation Notes**:
- Skills use standard MCP tool invocation syntax
- MCP adapter handles protocol translation transparently
- Test both Claude and Gemini execution paths in integration tests
- Document any Gemini-specific limitations (e.g., context window, function calling depth)

**Alternatives Considered**:
- Separate skill definitions for Claude vs Gemini: Rejected due to maintenance overhead
- Claude-only implementation: Rejected as it violates constitution Principle VI (Dual-Tier LLM Support)

---

### 2. WhatsApp Web API (whatsapp-web.js) Integration

**Decision**: Use whatsapp-web.js library with Python subprocess bridge for Silver Tier MVP

**Rationale**:
- whatsapp-web.js is the most mature unofficial WhatsApp Web client (50k+ GitHub stars)
- Supports message monitoring, sending, and media handling
- No WhatsApp Business API approval required (weeks-long process)
- Python-Node.js bridge pattern is well-established for cross-language integration

**Best Practices**:
- Use headless Chromium via puppeteer for WhatsApp Web session
- Persist session data to avoid repeated QR code scans
- Implement exponential backoff for reconnection (1s, 2s, 4s per constitution)
- Monitor for session expiration and alert user for re-authentication
- Rate limit: 1000 messages/day (conservative, unofficial API has no documented limit)

**Limitations & Risks**:
- Violates WhatsApp ToS (unofficial API)
- Account ban risk if detected (mitigated by conservative rate limiting)
- Session requires QR code scan on first setup
- No official support or SLA guarantees

**Migration Path to Official API**:
1. Document current event schema and tool signatures
2. Create abstraction layer (WhatsAppClient interface)
3. Implement official WhatsApp Business API client as alternative implementation
4. Switch via configuration flag when official API credentials available
5. Estimated migration effort: 4-6 hours

**Alternatives Considered**:
- Official WhatsApp Business API: Rejected for MVP due to 2-3 week approval process
- Twilio WhatsApp API: Rejected due to cost ($0.005/message) and setup complexity
- Manual WhatsApp monitoring: Rejected as it defeats automation purpose

---

### 3. LinkedIn Unofficial API (linkedin-api) Integration

**Decision**: Use linkedin-api Python library with documented migration path to official API

**Rationale**:
- linkedin-api library provides Python-native interface (no Node.js bridge needed)
- Supports profile access, messaging, post creation, and notification monitoring
- No LinkedIn partnership approval required (4-6 week process)
- Active maintenance (last update within 6 months)

**Best Practices**:
- Use session-based authentication (cookies) to avoid repeated logins
- Implement rate limiting: 100 posts/day, 50 profile views/day (conservative)
- Monitor for CAPTCHA challenges and alert user
- Rotate user agents to reduce detection risk
- Cache profile data to minimize API calls

**Limitations & Risks**:
- Violates LinkedIn ToS (unofficial scraping)
- Account restriction risk if detected (temporary or permanent)
- No access to LinkedIn Analytics API (post performance metrics limited)
- Breaking changes possible if LinkedIn updates their web interface

**Migration Path to Official API**:
1. Apply for LinkedIn Marketing Developer Platform partnership
2. Obtain OAuth2 credentials and API access
3. Implement official LinkedIn API client (REST-based)
4. Map unofficial API methods to official API endpoints
5. Update MCP server tool signatures if needed
6. Estimated migration effort: 8-12 hours (includes partnership approval wait time)

**Alternatives Considered**:
- Official LinkedIn API: Rejected for MVP due to partnership approval delay
- Puppeteer-based automation: Rejected due to higher resource usage and fragility
- Manual LinkedIn posting: Rejected as it defeats automation purpose

---

### 4. MCP Server Implementation Framework

**Decision**: Use FastAPI for MCP server implementation

**Rationale**:
- FastAPI provides async/await support for concurrent tool execution
- Built-in request validation via Pydantic (satisfies FR-008)
- OpenAPI schema generation for contract documentation
- High performance (comparable to Node.js/Go for I/O-bound tasks)
- Python-native (matches watcher implementation language)

**Architecture Pattern**:
```python
# MCP Server Structure
- server.py: FastAPI app with MCP protocol endpoints
- tools/: Individual tool implementations (send_email, linkedin_post, whatsapp_send)
- approval/: Approval workflow middleware (intercepts Level 2+ actions)
- rate_limiter.py: Token bucket algorithm for rate limiting
- validator.py: Pydantic models for input validation
```

**MCP Protocol Compliance**:
- Tool registration: POST /tools/register
- Tool invocation: POST /tools/invoke
- Tool discovery: GET /tools/list
- Health check: GET /health

**Alternatives Considered**:
- Flask: Rejected due to lack of native async support
- Node.js (Express): Rejected to maintain Python consistency across codebase
- gRPC: Rejected due to MCP specification using JSON-RPC over HTTP

---

### 5. Task Scheduling Cross-Platform Strategy

**Decision**: Implement dual scheduler with platform detection

**Rationale**:
- Unix/Linux: Use cron via crontab manipulation (FR-031)
- Windows: Use Task Scheduler via XML import (FR-031)
- Python schedule library for in-process scheduling (fallback)

**Implementation Approach**:
```python
# Platform detection
if platform.system() == "Windows":
    use TaskSchedulerManager
elif platform.system() in ["Linux", "Darwin"]:
    use CronManager
else:
    use InProcessScheduler (fallback)
```

**Cron Integration (Unix/Linux)**:
- Read existing crontab: `crontab -l`
- Append new task: `crontab -l | { cat; echo "0 9 * * 1 /path/to/task"; } | crontab -`
- Remove task: Filter out matching line and rewrite crontab
- Validate cron expression before adding

**Task Scheduler Integration (Windows)**:
- Generate XML definition from template
- Import via: `schtasks /create /xml task.xml /tn "DigitalFTE-Task"`
- List tasks: `schtasks /query /fo csv`
- Delete task: `schtasks /delete /tn "DigitalFTE-Task"`

**Missed Schedule Handling (FR-034)**:
- Store last run timestamp in obsidian-vault/Schedules/
- On startup, check if current_time - last_run > schedule_interval
- If within 24-hour window, execute immediately
- Update last_run timestamp after execution

**Alternatives Considered**:
- Python schedule library only: Rejected as it requires process to stay running (not persistent across restarts)
- Celery: Rejected due to complexity overhead (requires Redis/RabbitMQ)
- APScheduler: Rejected due to similar limitations as schedule library

---

### 6. Reasoning Loop Complexity Detection Algorithm

**Decision**: Multi-factor heuristic scoring system with configurable threshold

**Rationale**:
- Simple rule-based approach suitable for MVP (FR-026)
- Configurable threshold allows tuning to reduce false positives
- Transparent decision-making (user can understand why plan was generated)

**Complexity Scoring Algorithm**:
```python
def calculate_complexity_score(note_content: str) -> int:
    score = 0

    # Factor 1: Length (>100 words = +10 points)
    word_count = len(note_content.split())
    if word_count > 100:
        score += 10

    # Factor 2: Action verbs (each = +5 points, max 30)
    action_verbs = ["launch", "implement", "design", "build", "create",
                    "develop", "integrate", "deploy", "migrate", "refactor"]
    verb_count = sum(1 for verb in action_verbs if verb in note_content.lower())
    score += min(verb_count * 5, 30)

    # Factor 3: Multiple steps/phases (each = +5 points)
    step_indicators = ["step 1", "phase 1", "first,", "then,", "finally,"]
    step_count = sum(1 for indicator in step_indicators if indicator in note_content.lower())
    score += step_count * 5

    # Factor 4: Dependencies mentioned (each = +5 points)
    dependency_keywords = ["depends on", "requires", "needs", "after", "before"]
    dep_count = sum(1 for keyword in dependency_keywords if keyword in note_content.lower())
    score += dep_count * 5

    # Factor 5: Time estimates (presence = +10 points)
    time_patterns = ["hours", "days", "weeks", "months"]
    if any(pattern in note_content.lower() for pattern in time_patterns):
        score += 10

    return score

# Threshold: score >= 25 triggers Plan.md generation
COMPLEXITY_THRESHOLD = 25
```

**Tuning Strategy**:
- Start with threshold = 25 (generates plans for ~30% of tasks)
- Monitor false positive rate (plans generated for simple tasks)
- Adjust threshold based on user feedback
- Store threshold in config file for easy modification

**Alternatives Considered**:
- ML-based classifier: Rejected due to training data requirements and complexity
- Manual trigger only: Rejected as it violates clarification decision (automatic trigger)
- Keyword-only detection: Rejected as it produces too many false positives

---

### 7. Test Strategy for 80%+ Coverage

**Decision**: Layered testing approach with mocked external APIs

**Test Pyramid**:
```
Integration Tests (10%)
├── End-to-end watcher → vault → MCP → approval flow
└── Cross-component interaction tests

Unit Tests (70%)
├── Watcher logic (event detection, note creation)
├── MCP server tools (email send, LinkedIn post)
├── Approval workflow (queue, classifier, executor)
├── Rate limiter (token bucket algorithm)
└── Scheduler (cron/Task Scheduler integration)

Contract Tests (20%)
├── MCP server tool signatures
├── Watcher event schemas
└── Agent skill invocation patterns
```

**Mocking Strategy**:
- Gmail API: Use pytest-mock with recorded responses
- WhatsApp Web: Mock Node.js bridge subprocess calls
- LinkedIn API: Mock HTTP requests with responses library
- Obsidian vault: Use temporary directory with test fixtures
- OS keychain: Mock credential storage/retrieval

**Coverage Targets by Component**:
- Watchers: 85% (critical for reliability)
- MCP server: 90% (handles external actions)
- Approval workflow: 95% (security-critical)
- Scheduler: 80% (platform-specific code harder to test)
- Agent skills: 70% (prompt-based, harder to unit test)

**CI/CD Integration**:
- Run pytest with coverage report on every commit
- Fail build if coverage drops below 80%
- Generate HTML coverage report for review
- Track coverage trends over time

**Alternatives Considered**:
- Manual testing only: Rejected due to constitution requirement (80%+ coverage)
- 100% coverage target: Rejected as unrealistic for 20-30 hour implementation window
- Integration tests only: Rejected as they're slower and harder to debug

---

## Summary of Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Gemini Compatibility | MCP adapter layer handles translation | LLM-agnostic protocol, no skill changes needed |
| WhatsApp API | whatsapp-web.js with Python bridge | Fastest MVP path, documented migration to official API |
| LinkedIn API | linkedin-api library | Python-native, no Node.js dependency |
| MCP Server | FastAPI with async support | Performance, validation, OpenAPI generation |
| Task Scheduling | Dual scheduler (cron + Task Scheduler) | Cross-platform support with persistent scheduling |
| Complexity Detection | Multi-factor heuristic scoring | Transparent, configurable, suitable for MVP |
| Test Strategy | Layered pyramid with mocked APIs | 80%+ coverage achievable in 20-30 hour window |

## Next Steps

1. Generate data-model.md with entity schemas
2. Generate contracts/ with MCP tool definitions and watcher event schemas
3. Generate quickstart.md with setup instructions
4. Update agent context with new technologies
5. Re-evaluate Constitution Check post-design
