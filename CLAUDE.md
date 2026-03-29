# Digital FTE Agent Rules

You are building a **Digital FTE (Full-Time Equivalent)** - an autonomous AI agent that proactively manages personal and business affairs 24/7.

## Project Identity

**What We're Building**: A local-first AI employee that monitors Gmail, WhatsApp, banking, and social media to autonomously handle tasks, with a "Monday Morning CEO Briefing" feature.

**Architecture**: Brain (Claude/Gemini) + Memory (Obsidian) + Senses (Python Watchers) + Hands (MCP Servers)

**Constitution**: See `.specify/memory/constitution.md` for all principles, security requirements, and technology constraints.

## Core Principles (from Constitution)

1. **Local-First, Privacy-First** (NON-NEGOTIABLE): All sensitive data stays in Obsidian vault. No cloud storage without explicit consent.
2. **Autonomous Agent Pattern**: Watchers run 24/7, agent iterates until task complete ("Ralph Wiggum Stop Hook").
3. **Separation of Concerns**: Brain/Memory/Senses/Hands - each component independently testable.
4. **Event-Driven**: Watchers emit events → agent processes asynchronously → actions via MCP.
5. **4-Level Action Safety**: Auto-Execute (read) → Notify (draft) → Confirm (send) → Explicit Approval (financial).
6. **Dual-Tier LLM**: Claude (paid) OR Gemini (free) - user choice at setup, MCP adapter for Gemini.

## Technology Stack

- **Python 3.11+** with **uv package manager** (mandatory)
- **Obsidian** (Markdown vault for memory/dashboard)
- **MCP Servers** (actions) + **Gemini Adapter** (function calling translation)
- **APIs**: Gmail, WhatsApp, Plaid (banking), Stripe/PayPal
- **Secrets**: OS keychain only (Windows Credential Manager, macOS Keychain, Linux Secret Service)

## Development Workflow

**Success Criteria**:
- All outputs follow constitution principles
- PHRs created for every interaction
- ADRs suggested for significant decisions
- Changes are small, testable, privacy-preserving

## Workflow Rules

### PHR (Prompt History Record) - Mandatory
Create PHR after every interaction (constitution, spec, plan, tasks, implementation, debugging).

**Quick Process**:
1. Detect stage: `constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general`
2. Route: `history/prompts/constitution/` OR `history/prompts/<feature-name>/` OR `history/prompts/general/`
3. Use template: `.specify/templates/phr-template.prompt.md`
4. Fill all placeholders (ID, TITLE, STAGE, DATE, PROMPT_TEXT, RESPONSE_TEXT)
5. Validate: no placeholders left, file exists at correct path

### ADR (Architecture Decision Record) - Suggest Only
When significant decisions are made (framework choice, data model, security approach):
- Test: Impact? Alternatives? Cross-cutting?
- If ALL true: `📋 Architectural decision detected: <brief>. Document? Run /sp.adr <title>`
- Wait for user consent; never auto-create

### Human-in-the-Loop Triggers
1. **Ambiguous Requirements**: Ask 2-3 targeted questions
2. **Unforeseen Dependencies**: Surface and ask for prioritization
3. **Architectural Uncertainty**: Present options with tradeoffs
4. **High-Risk Actions**: Always confirm (financial, external comms, delete operations)

## Security & Privacy (Critical)

**Never**:
- Hardcode secrets (use OS keychain)
- Store PII in logs (redact)
- Auto-execute Level 2+ actions without confirmation
- Send data to cloud without explicit consent

**Always**:
- Encrypt sensitive data at rest (AES-256)
- Log all agent actions in Obsidian vault
- Use OAuth2 for external APIs
- Respect rate limits (100 emails/day, 10 social posts/day, $500 transaction limit)

## Development Standards

**Code Quality**:
- 80%+ test coverage for watchers and MCP servers
- Use `uv` for Python package management
- Document: trigger conditions, event schemas, error handling
- No direct commits to main; all PRs need tests + security review

**Execution Contract**:
1. Confirm success criteria (one sentence)
2. List constraints and non-goals
3. Produce artifact with acceptance checks
4. Create PHR
5. Suggest ADR if significant decision made

**Minimum Acceptance**:
- Clear, testable acceptance criteria
- Explicit error paths and constraints
- Smallest viable change; no unrelated edits
- Privacy and security compliance verified

## Project Structure

```
digital-fte/
├── .specify/memory/constitution.md    # Project principles (v1.0.1)
├── specs/<feature>/                   # Feature specs, plans, tasks
├── history/prompts/                   # PHRs (constitution, feature, general)
├── history/adr/                       # Architecture Decision Records
├── agents/                            # Claude/Gemini agent definitions
├── watchers/                          # Python event watchers (uv managed)
├── mcp-servers/                       # MCP server implementations
├── mcp-adapter/                       # Gemini function calling adapter
├── obsidian-vault/                    # Obsidian knowledge base
└── tests/                             # Test suites (unit, integration, safety)
```

## Quick Reference

**Start Feature**: `/sp.specify "feature description"`
**Plan Architecture**: `/sp.plan`
**Generate Tasks**: `/sp.tasks`
**Implement**: `/sp.implement`
**Document Decision**: `/sp.adr "decision title"`
**Record Interaction**: `/sp.phr` (auto-created, manual if needed)

**Constitution**: `.specify/memory/constitution.md` - authoritative source for all principles, constraints, and standards.
