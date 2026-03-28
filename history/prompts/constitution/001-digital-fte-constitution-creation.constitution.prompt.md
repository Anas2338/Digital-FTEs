---
id: 001
title: Digital FTE Constitution Creation
stage: constitution
date: 2026-03-29
surface: agent
model: claude-haiku-4-5-20251001
feature: none
branch: master
user: HP
command: /sp.constitution
labels: ["constitution", "architecture", "security", "privacy", "dual-llm", "local-first", "autonomous-agent"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution document)
---

## Prompt

User requested to build a Digital FTE (Full-Time Equivalent) project with the following requirements:

**Project Vision**: A futuristic, local-first AI agent that proactively manages personal and business affairs 24/7. The agent acts as a "Smart Consultant" or "Personal AI Employee" that doesn't just wait for input but autonomously handles:
- Personal Affairs: Gmail, WhatsApp, Bank transactions
- Business Operations: Social Media, Payments, Project Tasks

**Key Architectural Components**:
- Brain: Claude Code (paid) OR Google Gemini (free) - user choice at setup
- Memory/GUI: Obsidian (local Markdown) as dashboard
- Senses: Python watchers monitoring Gmail, WhatsApp, filesystems
- Hands: MCP (Model Context Protocol) servers for external actions

**Standout Feature**: "Monday Morning CEO Briefing" - AI autonomously audits bank transactions and tasks to report revenue and bottlenecks

**User Decisions** (from clarification questions):
1. LLM Architecture: User chooses once at setup (Claude OR Gemini for everything)
2. MCP Strategy: Build MCP adapter for Gemini (translate MCP to Gemini function calling)
3. Target Audience: Both tiers (students learn with Gemini, professionals use Claude)
4. Timeline: 1-2 weeks minimal MVP (single watcher + single LLM)

**Constitution Requirements**: Must include Architecture principles, Technology constraints, Code quality standards, Security requirements, Workflow rules

## Response snapshot

Created comprehensive Digital FTE Constitution v1.0.0 with the following structure:

**Core Principles (6)**:
1. Local-First, Privacy-First (NON-NEGOTIABLE) - All sensitive data stored locally in Obsidian
2. Autonomous Agent Pattern - Continuous operation via watchers with "Ralph Wiggum Stop Hook"
3. Separation of Concerns - Clear boundaries: Brain/Memory/Senses/Hands
4. Event-Driven Architecture - Watchers emit events, agent processes asynchronously
5. Idempotency and Reliability - All actions safe to retry, atomic state transitions
6. Dual-Tier LLM Support - Claude (paid) OR Gemini (free), user choice at setup

**Technology Stack**:
- Agent Runtime: Claude Code OR Google Gemini
- Knowledge Base: Obsidian (Markdown, local)
- Watchers: Python 3.11+
- Action Layer: MCP servers + Gemini adapter
- APIs: Gmail, WhatsApp, Banking (Plaid), Social Media, Payments (Stripe/PayPal)
- Storage: Obsidian vault (primary), SQLite (structured logs), OS keychain (secrets)

**Security & Privacy**:
- 4-level action safety system (Auto-Execute → Notify → Confirm → Explicit Approval)
- OAuth2 for external APIs, credentials in OS keychain only
- AES-256 encryption for sensitive data
- Rate limiting (100 emails/day, 10 social posts/day, $500 transaction limit)
- Complete audit trail in Obsidian vault

**Development Workflow**:
- 80%+ test coverage requirement
- Code organization: agents/, watchers/, mcp-servers/, mcp-adapter/, obsidian-vault/
- Documentation requirements for every component
- No direct commits to main, high-risk changes need two approvals

**MVP Scope (1-2 weeks)**:
- Single watcher (Gmail only)
- Single MCP server (email send/reply)
- Basic agent workflow (read → reason → draft → confirm → send)
- Obsidian dashboard with email inbox view

**Governance**:
- Constitution supersedes all practices
- Semantic versioning for amendments (MAJOR.MINOR.PATCH)
- All PRs must verify constitution compliance
- Priority order: Privacy > Security > Reliability > Features

## Outcome

- ✅ Impact: Established foundational governance document for Digital FTE project with 6 core principles, comprehensive security model, and dual-LLM architecture
- 🧪 Tests: N/A (constitution is a governance document)
- 📁 Files: Created .specify/memory/constitution.md (v1.0.0)
- 🔁 Next prompts: /sp.specify for first feature (e.g., "Gmail Watcher"), /sp.plan for architecture design, /sp.adr for significant decisions
- 🧠 Reflection: Constitution successfully balances educational accessibility (Gemini free tier) with production capability (Claude paid tier). Local-first architecture ensures privacy compliance. Event-driven design with watchers enables true autonomous operation.

## Evaluation notes (flywheel)

- Failure modes observed: None - constitution creation completed successfully
- Graders run and results (PASS/FAIL): Manual review pending - constitution aligns with user requirements and SDD-RI framework
- Prompt variant (if applicable): Standard /sp.constitution workflow with interactive clarification questions
- Next experiment (smallest change to try): Validate constitution compliance during first feature specification (/sp.specify) to ensure principles are actionable
