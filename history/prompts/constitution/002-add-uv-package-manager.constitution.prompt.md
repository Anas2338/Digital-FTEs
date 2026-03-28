---
id: 002
title: Add uv Package Manager Requirement
stage: constitution
date: 2026-03-29
surface: agent
model: claude-haiku-4-5-20251001
feature: none
branch: master
user: HP
command: /sp.constitution (amendment)
labels: ["constitution", "amendment", "technology-stack", "python", "package-manager"]
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

User identified missing requirement: "one thing is missing is that use uv package manager"

Context: The constitution defined Python 3.11+ as the required runtime for watchers but did not specify the package manager. The user requested adding `uv` as the standard package manager.

## Response snapshot

Amended Digital FTE Constitution from v1.0.0 to v1.0.1 (PATCH level):

**Change Type**: Technology constraint clarification (PATCH - no breaking changes)

**Modified Section**: Technology Stack → Required Components

**Addition**:
- **Package Manager**: `uv` (fast Python package installer and resolver)
- **Rationale for uv**: Modern, fast package management with reliable dependency resolution. Replaces pip/pip-tools for faster installs and better reproducibility.

**Version Increment Rationale**: PATCH (1.0.0 → 1.0.1) because this is a clarification of existing technology constraints, not a new principle or breaking change. The Python requirement already existed; we're just specifying which package manager to use.

**Sync Impact Report Updated**:
- Version: 1.0.0 → 1.0.1
- Type: PATCH - Technology constraint clarification
- Modified Sections: Technology Stack only
- No template updates required

## Outcome

- ✅ Impact: Constitution now mandates `uv` as the standard Python package manager for all watchers and Python components
- 🧪 Tests: N/A (constitution amendment)
- 📁 Files: Updated .specify/memory/constitution.md (v1.0.1)
- 🔁 Next prompts: Constitution is complete and ready for feature development
- 🧠 Reflection: `uv` is a modern choice that aligns with the project's emphasis on reliability and speed. It provides faster dependency resolution than pip and better reproducibility than traditional requirements.txt workflows.

## Evaluation notes (flywheel)

- Failure modes observed: None - amendment applied cleanly
- Graders run and results (PASS/FAIL): Manual review - amendment is backward compatible and clarifies existing constraints
- Prompt variant (if applicable): User-initiated amendment (not full constitution recreation)
- Next experiment (smallest change to try): Validate `uv` usage during first Python watcher implementation to ensure it meets project needs
