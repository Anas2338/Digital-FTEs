---
id: 003
title: Plan Bronze Tier Foundation Implementation
stage: plan
date: 2026-03-29
surface: agent
model: claude-haiku-4-5-20251001
feature: 001-bronze-tier-foundation
branch: 001-bronze-tier-foundation
user: Anas2338
command: /sp.plan
labels: ["planning", "architecture", "bronze-tier", "gmail-watcher", "obsidian", "agent-skills"]
links:
  spec: specs/001-bronze-tier-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-tier-foundation/plan.md
  - specs/001-bronze-tier-foundation/research.md
  - specs/001-bronze-tier-foundation/data-model.md
  - specs/001-bronze-tier-foundation/contracts/vault-operations.md
  - specs/001-bronze-tier-foundation/quickstart.md
  - CLAUDE.md (updated with Python 3.11+ and local file system context)
tests:
  - Constitution Check validation (all principles passed)
  - Technical context validation (all dependencies identified)
  - Design validation (data model, contracts, quickstart complete)
---

## Prompt

/sp.plan (no additional user input - standard planning workflow)

## Response snapshot

Created comprehensive implementation plan for Bronze Tier Foundation through Phase 0 (Research) and Phase 1 (Design):

**Phase 0: Research & Unknowns (COMPLETE)**

Dispatched 3 parallel research agents to resolve technical unknowns:

1. **Gmail API Integration**: Researched OAuth2 desktop flow, label-based filtering, message content extraction, rate limiting, and error handling patterns. Key findings: OAuth2 tokens in `watchers/.auth/token.json`, label-based filtering with "ToVault" default, plain text body extraction, 3-minute polling well within API quotas (4,800 units/day vs 1B limit), exponential backoff (1s, 2s, 4s) for transient errors.

2. **Obsidian Vault Structure**: Researched minimal configuration requirements, YAML frontmatter standards, dashboard dynamic content patterns, filename sanitization, and markdown linking. Key findings: Minimal `.obsidian/workspace.json` sufficient (Obsidian auto-generates rest), YAML frontmatter schema for email notes, timestamp-based filename format `YYYYMMDD-HHMMSS-sanitized-subject.md`, dashboard regeneration via Python script (no plugin dependencies).

3. **Agent Skills Patterns**: Researched existing `.claude/skills/` patterns, SKILL.md format, tool integration, and skill invocation mechanisms. Key findings: Single `vault-operations` skill consolidating all operations, frontmatter description is primary trigger, tool usage patterns (Read/Write/Grep/Glob/Bash), progressive disclosure architecture.

Consolidated findings into `research.md` with 5 key decision areas: Gmail auth, email filtering, content extraction, vault config, dashboard updates, filename format, agent skills, idempotency, watcher architecture, error handling.

**Phase 1: Design & Contracts (COMPLETE)**

Generated comprehensive design artifacts:

1. **data-model.md**: Defined 5 core entities (Note, Dashboard, Company Handbook, Email Event, Watcher State) with complete schemas, validation rules, state transitions, relationships, and performance considerations. Note entity uses YAML frontmatter with 7 fields (title, created, source, sender, email_date, status, tags). Dashboard dynamically aggregates folder counts and last 10 notes.

2. **contracts/vault-operations.md**: Specified 5 agent skill operations with complete contracts:
   - Create Note: Parameters (folder, title, content, sender, email_date, tags), returns file path
   - Read Note: Parameters (path), returns frontmatter + body
   - Move Note: Parameters (source_path, target_folder), updates status field
   - Update Dashboard: No parameters, regenerates from vault state
   - Search Vault: Parameters (query, case_sensitive, max_results), returns matches

   Each operation includes parameter specs, behavior description, return format, error cases, and example usage.

3. **quickstart.md**: Created 10-step setup guide (30-45 min estimated):
   - Install Python dependencies via uv
   - Configure Gmail API credentials (OAuth2)
   - Initialize Obsidian vault structure
   - Configure Gmail label
   - Set environment variables
   - Authenticate Gmail (first run)
   - Test email capture
   - Open vault in Obsidian
   - Test Claude Code integration
   - Verify dashboard updates

   Includes troubleshooting section, verification checklist, and daily usage patterns.

**Agent Context Update**:
- Updated `CLAUDE.md` with Python 3.11+ and local file system context
- Preserved existing manual additions between markers

**Constitution Check Re-Evaluation**:
- All 6 principles validated post-design (Local-First, Autonomous Agent, Separation of Concerns, Event-Driven, Idempotency, Dual-Tier LLM)
- All security & privacy requirements satisfied
- No violations requiring complexity justification
- Final gate: ✅ PASS - Ready for /sp.tasks

**Project Structure Defined**:
- Single project structure selected (no frontend/backend split)
- Clear component boundaries: watchers/, obsidian-vault/, .claude/skills/vault-operations/, tests/, scripts/
- Follows constitution's separation of concerns

**Technical Context Finalized**:
- Language: Python 3.11+
- Dependencies: google-api-python-client, google-auth-oauthlib, pyyaml, python-dotenv
- Storage: Local file system (Obsidian vault)
- Testing: pytest with pytest-mock
- Performance: 3-min polling, <2s note creation, <5s dashboard update
- Constraints: 8-12 hour implementation, Bronze Tier scope only

## Outcome

- ✅ Impact: Complete implementation plan with research, data model, contracts, and quickstart guide ready for task breakdown
- 🧪 Tests: Constitution Check passed (all principles satisfied), design validation complete
- 📁 Files: Generated 5 planning artifacts (plan.md, research.md, data-model.md, contracts/vault-operations.md, quickstart.md) + updated CLAUDE.md
- 🔁 Next prompts: /sp.tasks to generate actionable task breakdown with test cases
- 🧠 Reflection: Parallel research agents efficiently resolved all technical unknowns. Design maintains constitution compliance while delivering Bronze Tier scope within 8-12 hour estimate. Clear separation between planning (this phase) and task generation (next phase) ensures focused deliverables.

## Evaluation notes (flywheel)

- Failure modes observed: None - all research agents completed successfully, all design artifacts generated without issues
- Graders run and results (PASS/FAIL): Constitution Check - PASS (all 6 principles + security requirements satisfied)
- Prompt variant (if applicable): Standard /sp.plan workflow with parallel research agents (3 agents dispatched simultaneously)
- Next experiment (smallest change to try): Consider caching research findings across similar features to reduce redundant research time
