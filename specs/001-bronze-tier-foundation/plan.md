# Implementation Plan: Bronze Tier Foundation

**Branch**: `001-bronze-tier-foundation` | **Date**: 2026-03-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bronze-tier-foundation/spec.md`

## Summary

Implement foundational Digital FTE system with Obsidian vault integration, Gmail watcher, and Claude Code agent skills. Primary requirement: Create local-first knowledge management system that captures emails into structured markdown notes with automated dashboard updates.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: google-api-python-client, google-auth-oauthlib, pyyaml, python-dotenv
**Package Manager**: uv (Astral's fast Python package manager using pyproject.toml)
**Storage**: Local filesystem - Obsidian vault with markdown files and YAML frontmatter
**Testing**: pytest for unit and integration tests
**Target Platform**: Windows 10+ (cross-platform Python code)
**Project Type**: Single project with watchers, scripts, and agent skills
**Performance Goals**: Process 100 emails/day, 3-minute polling interval, <1s note creation
**Constraints**: Local-first (no cloud dependencies), privacy-first (no data transmission), <200ms dashboard updates
**Scale/Scope**: Single user, ~1000 notes/month, 3 folders, 1 watcher, 5 agent operations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Simplicity First ✅ PASS
- Single watcher (Gmail only for Bronze Tier)
- Minimal Obsidian configuration (no plugins)
- Flat folder structure (3 folders: Inbox, Needs_Action, Done)
- No database, no complex state management

### Principle II: Testability ✅ PASS
- Unit tests for utilities (sanitization, frontmatter generation)
- Integration tests for Gmail API and vault operations
- Contract tests for agent skills
- Manual acceptance tests for end-to-end workflow

### Principle III: Performance ✅ PASS
- 3-minute polling interval (well within Gmail API quotas)
- Timestamp-based filenames (O(1) creation, no collision checks)
- Dashboard regeneration from filesystem (no caching needed)
- Exponential backoff for error handling (1s, 2s, 4s)

### Principle IV: Security ✅ PASS
- OAuth2 for Gmail authentication (no password storage)
- Token stored in gitignored `.auth/` directory
- Credentials.json excluded from version control
- No sensitive data in logs

### Principle V: Maintainability ✅ PASS
- Standard Python project structure
- Clear separation: watchers/, scripts/, skills/
- Comprehensive documentation in research.md
- Agent skills for reusable operations

### Principle VI: AI-First Architecture ✅ PASS
- All vault operations exposed as agent skills
- Claude Code can read/write vault directly
- Dashboard updates via Python script (callable by agent)
- Note: Gemini integration deferred to Silver Tier (intentional for MVP)

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-tier-foundation/
├── spec.md              # Feature specification
├── plan.md              # This file - implementation plan
├── research.md          # Phase 0 research findings
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 setup guide
├── contracts/           # Phase 1 API contracts
│   └── vault-operations.md
└── tasks.md             # Phase 2 task breakdown
```

### Source Code (repository root)

```text
watchers/
├── pyproject.toml       # uv project configuration with dependencies
├── .env.example         # Environment template
├── .auth/               # OAuth tokens (gitignored)
├── logs/                # Watcher activity logs
├── utils.py             # Filename sanitization, timestamp formatting
├── vault_utils.py       # YAML frontmatter helpers
└── gmail_watcher.py     # Main watcher implementation

scripts/
├── setup_vault.py       # Vault initialization script
└── update_dashboard.py  # Dashboard regeneration script

.claude/skills/vault-operations/
├── SKILL.md             # Agent skill definition
└── references/          # Supporting documentation

obsidian-vault/
├── .obsidian/           # Minimal Obsidian configuration
│   └── workspace.json
├── Inbox/               # New items
├── Needs_Action/        # Items requiring attention
├── Done/                # Completed items
├── Dashboard.md         # Dynamic summary
└── Company_Handbook.md  # Static template

tests/
├── unit/                # Unit tests for utilities
└── integration/         # Integration tests for watcher and vault
```

**Structure Decision**: Single project structure chosen because all components are tightly coupled (watcher → vault → agent skills). No need for separate backend/frontend or microservices. Python scripts and watchers share common utilities.

## Complexity Tracking

> No constitution violations - all principles satisfied.

## Package Management with uv

**Why uv over pip/poetry**:
- 10-100x faster dependency resolution
- Uses standard pyproject.toml (PEP 621)
- Single tool for project management and package installation
- Built-in virtual environment management
- Lockfile for reproducible builds

**Project Configuration** (`watchers/pyproject.toml`):
```toml
[project]
name = "digital-fte-watchers"
version = "0.1.0"
description = "Gmail watcher for Digital FTE Obsidian vault integration"
requires-python = ">=3.11"
dependencies = [
    "google-api-python-client>=2.108.0",
    "google-auth-httplib2>=0.2.0",
    "google-auth-oauthlib>=1.2.0",
    "pyyaml>=6.0.1",
    "python-dotenv>=1.0.0",
]
```

**Common Commands**:
- `uv sync` - Install dependencies from pyproject.toml
- `uv add <package>` - Add new dependency
- `uv run <script>` - Run script in project environment
- `uv pip list` - List installed packages

**Lockfile**: `uv.lock` (gitignored) ensures reproducible builds across environments.

## Implementation Phases

### Phase 0: Research ✅ COMPLETE
- Gmail API OAuth2 flow documented
- Obsidian vault structure defined
- Agent skills patterns researched
- Idempotency strategies determined
- Output: research.md

### Phase 1: Design ✅ COMPLETE
- Data model with 5 entities defined
- Vault operations contract specified
- Quickstart guide created
- Output: data-model.md, contracts/vault-operations.md, quickstart.md

### Phase 2: Task Breakdown ✅ COMPLETE
- 68 tasks across 7 phases
- Dependencies mapped
- Acceptance criteria defined
- Output: tasks.md

### Phase 3: Implementation 🔄 IN PROGRESS
- Phase 1 (Setup): ✅ COMPLETE - Project structure, pyproject.toml, .gitignore, .env.example
- Phase 2 (Foundational): ✅ COMPLETE - utils.py, vault_utils.py with core utilities
- Phase 3 (User Story 1): ✅ COMPLETE - Vault initialization script with all templates
- Phase 4 (User Story 2): ⏳ PENDING - Claude Code integration
- Phase 5 (User Story 3): ⏳ PENDING - Agent skills implementation
- Phase 6 (User Story 4): ⏳ PENDING - Gmail watcher implementation
- Phase 7 (Polish): ⏳ PENDING - Documentation, validation, cleanup

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gmail API quota exceeded | HIGH | 3-minute polling uses <0.001% of daily quota |
| OAuth token expiration | MEDIUM | Library auto-refreshes tokens, user re-auth if needed |
| Filename collisions | LOW | Timestamp-based names prevent collisions |
| Unicode encoding errors | MEDIUM | Use ASCII-safe characters in console output, UTF-8 for files |
| Obsidian vault corruption | LOW | Atomic writes, no concurrent modifications |

## Success Criteria

1. ✅ Vault initialization creates all folders and templates
2. ⏳ Claude Code can create notes with proper frontmatter
3. ⏳ Claude Code can read and parse existing notes
4. ⏳ Dashboard updates reflect current vault state
5. ⏳ Gmail watcher captures labeled emails as notes
6. ⏳ Agent skills expose all vault operations
7. ⏳ All tests pass (unit + integration)
8. ⏳ Documentation complete and accurate

---

**Plan Status**: ✅ COMPLETE
**Implementation Status**: 🔄 IN PROGRESS (Phase 3 of 7)
**Next Steps**: Fix Unicode encoding in setup_vault.py, test vault initialization, proceed to User Story 2
