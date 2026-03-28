<!--
Sync Impact Report:
- Version: 1.0.0 → 1.0.1
- Type: PATCH - Technology constraint clarification
- Modified Principles: None
- Modified Sections: Technology Stack - Added uv package manager requirement
- Templates Status:
  ✅ constitution.md - updated
  ⚠ plan-template.md - review for constitution alignment
  ⚠ spec-template.md - review for constitution alignment
  ⚠ tasks-template.md - review for constitution alignment
- Follow-up TODOs: None
-->

# Digital FTE (Full-Time Equivalent) Constitution

## Core Principles

### I. Local-First, Privacy-First (NON-NEGOTIABLE)
All sensitive data (emails, messages, financial records, personal information) MUST be stored locally in the Obsidian vault. External API calls MUST be logged and auditable. No data leaves the local environment unless explicitly required for action execution (e.g., sending an email). Users MUST have full control over what data the agent can access.

**Rationale**: Privacy is paramount for a system handling personal and business affairs. Local storage ensures data sovereignty and compliance with privacy regulations.

### II. Autonomous Agent Pattern
The agent operates continuously via watchers, not just on-demand. The "Ralph Wiggum Stop Hook" pattern ensures the agent iterates until task completion criteria are met. The agent MUST self-validate work before marking tasks complete. Human-in-the-loop is required ONLY for high-risk actions (financial transactions, external communications).

**Rationale**: True automation requires proactive operation. The agent should work like a trusted employee who doesn't need constant supervision.

### III. Separation of Concerns
The system architecture MUST maintain clear boundaries:
- **Brain (Claude Code / Gemini)**: Reasoning, decision-making, task orchestration
- **Memory (Obsidian)**: State management, dashboard, audit trail
- **Senses (Watchers)**: Event detection and agent triggering
- **Hands (MCP Servers)**: Action execution on external systems

Each component MUST be independently testable and replaceable. No component may bypass another's responsibilities.

**Rationale**: Modular architecture enables incremental development, easier debugging, and component upgrades without system-wide rewrites.

### IV. Event-Driven Architecture
Watchers emit events (new email, bank transaction, task deadline). Events trigger agent workflows with context. The agent processes events asynchronously. Failed events MUST be retryable with exponential backoff (3 attempts: 1s, 2s, 4s).

**Rationale**: Event-driven design enables reactive automation and graceful handling of transient failures.

### V. Idempotency and Reliability
All agent actions MUST be idempotent (safe to retry). State transitions MUST be atomic and logged. The system MUST recover gracefully from crashes. The "Monday Morning CEO Briefing" MUST always be generatable from historical data.

**Rationale**: Reliability is critical for a system managing important personal and business affairs. Idempotency prevents duplicate actions (e.g., sending the same email twice).

### VI. Dual-Tier LLM Support
The system MUST support both Claude Code (paid tier) and Google Gemini (free tier). Users choose their LLM provider once at setup. The MCP adapter layer MUST translate MCP protocol to Gemini's function calling API, ensuring feature parity. Students learn with Gemini; professionals deploy with Claude.

**Rationale**: Accessibility for educational use (free tier) while supporting production deployments (paid tier). Single-choice architecture simplifies implementation for MVP.

## Technology Stack

### Required Components
- **Agent Runtime**: Claude Code (Anthropic) OR Google Gemini (user choice at setup)
- **Knowledge Base**: Obsidian (Markdown-based, local storage)
- **Watchers**: Python 3.11+ (lightweight, cross-platform)
- **Package Manager**: `uv` (fast Python package installer and resolver)
- **Action Layer**: MCP (Model Context Protocol) servers with Gemini adapter

**Rationale for uv**: Modern, fast package management with reliable dependency resolution. Replaces pip/pip-tools for faster installs and better reproducibility.

### Integration APIs
- **Email**: Gmail API (OAuth2, read/send permissions)
- **Messaging**: WhatsApp Business API or unofficial API (with user consent)
- **Banking**: Plaid API or bank-specific APIs (read-only initially)
- **Social Media**: Platform-specific APIs (Twitter, LinkedIn, etc.)
- **Payments**: Stripe/PayPal APIs (with transaction limits)

### Data Storage
- **Primary**: Obsidian vault (Markdown files)
- **Structured Data**: SQLite for queryable logs and metrics
- **Secrets**: OS keychain (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **No Cloud Databases**: Unless explicitly opted-in by user

### Deployment Model
- **Local-First**: Runs on user's machine (Windows/macOS/Linux)
- **Optional**: Docker container for isolated execution
- **No Server-Side Components**: Required for core functionality
- **Cloud Deployment**: Optional for advanced users

## Security & Privacy

### Authentication & Authorization
- All external API credentials stored in OS keychain, NEVER in code or config files
- OAuth2 for Gmail, social media APIs
- API keys rotated every 90 days
- Agent MUST request user approval for new API scopes

### Action Safety Levels
```
Level 0 (Auto-Execute): Read-only operations (fetch emails, check balances)
Level 1 (Notify): Low-risk writes (draft emails, create tasks)
Level 2 (Confirm): Medium-risk (send emails, post to social media)
Level 3 (Explicit Approval): High-risk (financial transactions, delete operations)
```

### Data Protection
- Sensitive data (bank info, passwords) encrypted at rest (AES-256)
- PII (Personally Identifiable Information) redacted in logs
- Obsidian vault can be encrypted with user passphrase
- No telemetry or analytics without explicit opt-in

### Rate Limiting & Abuse Prevention
- Max 100 emails sent per day (configurable)
- Max 10 social media posts per day
- Financial transaction limits (e.g., max $500 per transaction)
- Circuit breaker: stop agent if error rate > 20%

### Audit Trail
- Every agent action logged with: timestamp, action type, parameters, result
- Logs stored in Obsidian vault for user review
- "Monday Morning CEO Briefing" includes security audit section
- User can replay any day's agent activity

## Development Workflow

### Code Quality Standards
- **Unit Tests**: 80%+ coverage for watcher logic and MCP servers
- **Integration Tests**: End-to-end tests for each agent workflow
- **Simulation Tests**: Mock external APIs to test agent decision-making
- **Safety Tests**: Verify agent doesn't take unauthorized actions

### Code Organization
```
digital-fte/
├── agents/           # Claude Code / Gemini agent definitions
├── watchers/         # Python event watchers
├── mcp-servers/      # MCP server implementations
├── mcp-adapter/      # Gemini function calling adapter
├── obsidian-vault/   # Obsidian knowledge base
├── tests/            # Test suites
├── docs/             # Documentation
└── scripts/          # Automation scripts
```

### Documentation Requirements
- Every watcher MUST document: trigger conditions, event schema, error handling
- Every MCP server MUST document: actions, parameters, rate limits, error codes
- Every agent workflow MUST have: decision tree, success criteria, rollback procedure
- README MUST include: setup guide, security considerations, troubleshooting

### Code Review Gates
- No direct commits to main branch
- All PRs require: tests passing, documentation updated, security review
- High-risk changes (financial, external comms) require two approvals

### Workflow Rules
- **Agent Activation**: Watchers run 24/7, check every 5 minutes; agent wakes on events
- **Task Prioritization**: P0 (Critical) → P1 (High) → P2 (Medium) → P3 (Low)
- **Decision-Making**: Agent explains reasoning in Obsidian; escalates uncertainty to user
- **Error Handling**: Retry transient errors 3x; notify user on permanent errors; never fail silently
- **Continuous Improvement**: Create PHR for every interaction; weekly retrospective

### MVP Scope (1-2 Weeks)
- Single watcher (Gmail only)
- Single MCP server (email send/reply)
- Basic agent workflow (read → reason → draft → confirm → send)
- Obsidian dashboard with email inbox view
- Support for either Claude OR Gemini (user choice)

## Governance

This constitution supersedes all other development practices and guidelines. All code changes, architectural decisions, and feature implementations MUST comply with these principles.

### Amendment Process
- Amendments require: documented rationale, impact analysis, team approval
- Version increments follow semantic versioning:
  - **MAJOR**: Backward incompatible principle changes
  - **MINOR**: New principles or sections added
  - **PATCH**: Clarifications, wording fixes
- All dependent templates (spec, plan, tasks) MUST be updated to reflect amendments

### Compliance Review
- All PRs MUST verify constitution compliance before merge
- Complexity MUST be justified against simplicity principles
- Security violations result in immediate PR rejection
- Privacy violations are non-negotiable blockers

### Runtime Guidance
- Use `CLAUDE.md` for agent-specific development guidance
- Constitution principles take precedence over agent suggestions
- When in doubt, prioritize: Privacy > Security > Reliability > Features

**Version**: 1.0.1 | **Ratified**: 2026-03-29 | **Last Amended**: 2026-03-29
