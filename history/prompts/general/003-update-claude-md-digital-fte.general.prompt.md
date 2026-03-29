---
id: 003
title: Update CLAUDE.md for Digital FTE
stage: general
date: 2026-03-29
surface: agent
model: claude-haiku-4-5-20251001
feature: none
branch: master
user: HP
command: manual update
labels: ["documentation", "agent-guidance", "constitution-alignment", "performance-optimization"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - CLAUDE.md
tests:
  - N/A (documentation update)
---

## Prompt

User requested: "update CLAUDE.md file according to project constitution keep CLAUDE.md concise and short for better performance"

Context: The existing CLAUDE.md was a generic SDD template with extensive PHR creation instructions and architect guidelines. It needed to be:
1. Aligned with Digital FTE constitution principles
2. Made concise for better agent performance
3. Project-specific rather than generic

## Response snapshot

Streamlined CLAUDE.md from 211 lines to ~120 lines while maintaining all critical information:

**Changes Made**:

1. **Project Identity Section** (NEW):
   - Clear statement: "Building a Digital FTE - autonomous AI agent for personal/business affairs"
   - Architecture overview: Brain/Memory/Senses/Hands
   - Reference to constitution as authoritative source

2. **Core Principles** (CONDENSED):
   - Extracted 6 key principles from constitution
   - Added specific constraints: Local-first, 4-level action safety, dual-tier LLM
   - Emphasized privacy and security as non-negotiable

3. **Technology Stack** (NEW):
   - Python 3.11+ with uv package manager (mandatory)
   - Obsidian, MCP servers, Gemini adapter
   - Specific APIs: Gmail, WhatsApp, Plaid, Stripe/PayPal
   - Secrets management: OS keychain only

4. **Workflow Rules** (STREAMLINED):
   - PHR creation: condensed from 8-step detailed process to 5-step quick process
   - ADR suggestions: kept 3-part test, removed verbose examples
   - Human-in-the-loop: kept 4 triggers, removed redundant explanations

5. **Security & Privacy** (NEW CRITICAL SECTION):
   - "Never" list: hardcode secrets, store PII in logs, auto-execute high-risk actions
   - "Always" list: encrypt data, log actions, use OAuth2, respect rate limits
   - Specific limits: 100 emails/day, 10 social posts/day, $500 transactions

6. **Development Standards** (CONDENSED):
   - 80%+ test coverage requirement
   - uv package manager mandate
   - Execution contract: 5 steps instead of verbose explanations
   - Minimum acceptance criteria: 4 bullets

7. **Project Structure** (VISUAL):
   - Added directory tree showing actual Digital FTE structure
   - Included new directories: agents/, watchers/, mcp-servers/, mcp-adapter/, obsidian-vault/

8. **Quick Reference** (NEW):
   - One-line commands for common workflows
   - Direct pointer to constitution as authoritative source

**Removed**:
- Generic SDD boilerplate
- Verbose PHR step-by-step instructions (kept essentials)
- Lengthy architect guidelines (referenced constitution instead)
- Redundant explanations and examples

**Performance Impact**:
- Reduced token count by ~40%
- Faster agent context loading
- Clearer decision-making with project-specific guidance
- Constitution reference prevents duplication

## Outcome

- ✅ Impact: CLAUDE.md now provides concise, Digital FTE-specific guidance aligned with constitution principles
- 🧪 Tests: N/A (documentation)
- 📁 Files: Updated CLAUDE.md (211 lines → ~120 lines, ~40% reduction)
- 🔁 Next prompts: Ready to start feature development with /sp.specify
- 🧠 Reflection: Concise agent guidance improves performance by reducing context overhead while maintaining all critical information. Constitution serves as single source of truth, preventing duplication.

## Evaluation notes (flywheel)

- Failure modes observed: None - update completed successfully
- Graders run and results (PASS/FAIL): Manual review - CLAUDE.md is now project-specific and constitution-aligned
- Prompt variant (if applicable): Standard documentation update
- Next experiment (smallest change to try): Monitor agent performance during first feature specification to validate that concise guidance is sufficient
