# Feature Specification: Bronze Tier Foundation

**Feature Branch**: `001-bronze-tier-foundation`
**Created**: 2026-03-29
**Status**: Draft
**Input**: User description: "Bronze Tier: Foundation (Minimum Viable Deliverable) - Obsidian vault with Dashboard.md and Company_Handbook.md, one working Watcher script (Gmail OR file system monitoring), Claude Code reading/writing to vault, basic folder structure"

## Clarifications

### Session 2026-03-29

- Q: Which watcher should be implemented first for the Bronze Tier MVP? → A: Gmail watcher - Monitor inbox for new emails and create notes automatically
- Q: Which emails should the Gmail watcher capture and convert to notes? → A: Emails with specific Gmail label (e.g., "ToVault") - User manually labels emails to capture
- Q: What email content should be extracted and stored in the vault note? → A: Subject, sender, timestamp, plain text body (no attachments)
- Q: What specific content and format should Dashboard.md display? → A: Dynamic counts with links - Auto-updated counts (Inbox: 5, Needs Action: 3) plus last 10 created notes with timestamps
- Q: What filename convention should be used for notes created from emails? → A: Timestamp + sanitized subject - Format: "YYYYMMDD-HHMMSS-subject.md" (unique and readable)

## Reference Architecture Analysis

### Industry Standards for Knowledge Management Systems

**Obsidian Vault Patterns**:
- Local-first markdown storage with `.obsidian/` configuration directory
- Flat or hierarchical folder structures for organizing notes
- Frontmatter metadata (YAML) for note properties and relationships
- Dataview queries for dynamic content aggregation
- Daily notes and templates for consistent structure

**Email Monitoring Patterns**:
- Gmail API with OAuth2 authentication for secure access
- Polling intervals (1-5 minutes) or webhook-based push notifications
- Label-based filtering and organization
- Read/unread state tracking
- Thread and conversation grouping

**File System Monitoring Patterns**:
- Event-driven watchers (create, modify, delete, rename)
- Debouncing to prevent duplicate processing
- Recursive directory watching
- File type filtering and pattern matching

**AI Agent Integration Patterns**:
- Skill-based architecture with modular capabilities
- Tool-based execution (read, write, search, transform)
- Context-aware prompting with memory systems
- Audit logging for all agent actions

## Current Architecture Analysis

### Existing Project Structure

**Present Components**:
- `.specify/` - Spec-Driven Development framework with templates and scripts
- `.claude/` - Claude Code configuration with 13 commands and 22 skills
- `CLAUDE.md` - Agent development rules and SDD guidelines
- `history/prompts/` - Prompt History Records system
- `.specify/memory/constitution.md` - Project constitution (v1.0.1)

**Missing Components** (per Bronze Tier requirements):
- No `obsidian-vault/` directory or Obsidian configuration
- No watcher scripts in `watchers/` directory
- No agent skills for vault operations
- No Dashboard.md or Company_Handbook.md files
- No /Inbox, /Needs_Action, /Done folder structure

**Existing Patterns to Leverage**:
- Agent Skills framework (`.claude/skills/*/SKILL.md` pattern)
- File operations via Read, Write, Grep, Glob tools
- Markdown-based documentation and templates
- YAML frontmatter for metadata

### Gap Analysis

**Infrastructure Gaps**:
1. Obsidian vault structure and configuration
2. Watcher script implementation (Gmail or file system)
3. Vault-specific agent skills
4. Integration between Claude Code and vault

**Capability Gaps**:
1. Email monitoring and processing
2. Automated note creation from external sources
3. Dashboard aggregation and reporting
4. Handbook content management

## User Scenarios & Testing

### User Story 1 - Obsidian Vault Initialization (Priority: P1)

As a business owner, I need a structured knowledge base where all business information is stored in markdown format, so I can access and organize information locally without depending on cloud services.

**Why this priority**: The vault is the foundational data layer. Without it, no other features can function. This delivers immediate value by providing a structured location for business information.

**Independent Test**: Can be fully tested by verifying the vault directory exists with proper structure, opening it in Obsidian, and confirming Dashboard.md and Company_Handbook.md are accessible and editable.

**Acceptance Scenarios**:

1. **Given** no obsidian-vault directory exists, **When** the vault is initialized, **Then** the directory structure includes /Inbox, /Needs_Action, /Done folders and .obsidian configuration
2. **Given** the vault is initialized, **When** I open Dashboard.md, **Then** I see a formatted dashboard with sections for inbox items, action items, and recent activity
3. **Given** the vault is initialized, **When** I open Company_Handbook.md, **Then** I see a template structure for documenting business processes, contacts, and guidelines
4. **Given** the vault exists, **When** I open it in Obsidian application, **Then** the vault loads successfully with all folders visible

---

### User Story 2 - Claude Code Vault Integration (Priority: P2)

As a business owner, I need Claude Code to read from and write to my Obsidian vault, so the AI assistant can help me manage and organize business information automatically.

**Why this priority**: This enables AI-powered automation of vault operations. Without this, the vault is just a static file structure. This is P2 because the vault must exist first (P1).

**Independent Test**: Can be fully tested by having Claude Code create a new note in /Inbox, read an existing note from the vault, and update Dashboard.md with new content.

**Acceptance Scenarios**:

1. **Given** the vault exists, **When** Claude Code is asked to create a note in /Inbox, **Then** a new markdown file appears in obsidian-vault/Inbox/ with proper frontmatter
2. **Given** notes exist in the vault, **When** Claude Code is asked to read a specific note, **Then** the full content including frontmatter is retrieved and displayed
3. **Given** Dashboard.md exists, **When** Claude Code is asked to update the dashboard, **Then** the file is modified with new content while preserving existing structure
4. **Given** a note exists in /Inbox, **When** Claude Code is asked to move it to /Needs_Action, **Then** the file is relocated and Dashboard.md reflects the change

---

### User Story 3 - Agent Skills for Vault Operations (Priority: P3)

As a business owner, I need specialized agent skills for common vault operations, so I can efficiently manage notes, tasks, and information without manual file manipulation.

**Why this priority**: Agent skills provide reusable, standardized workflows for vault operations. This is P3 because basic read/write works without skills (P2), but skills make operations more efficient and consistent.

**Independent Test**: Can be fully tested by invoking each agent skill and verifying the expected vault changes occur (e.g., /vault-create-note creates a note, /vault-move-note relocates a file).

**Acceptance Scenarios**:

1. **Given** the vault exists, **When** I invoke the vault-create-note skill with title and content, **Then** a new note is created in the specified folder with proper metadata
2. **Given** a note exists in /Inbox, **When** I invoke the vault-move-note skill, **Then** the note is moved to the target folder and all references are updated
3. **Given** multiple notes exist, **When** I invoke the vault-search skill with a query, **Then** all matching notes are returned with relevant excerpts
4. **Given** Dashboard.md exists, **When** I invoke the vault-update-dashboard skill, **Then** the dashboard is refreshed with current inbox count, action items, and recent activity

---

### User Story 4 - Watcher Script Implementation (Priority: P4)

As a business owner, I need an automated watcher that monitors either my Gmail inbox or a file system directory, so new information is automatically captured in my Obsidian vault without manual intervention.

**Why this priority**: Automation reduces manual work but the vault is functional without it. This is P4 because it depends on vault structure (P1), Claude Code integration (P2), and benefits from agent skills (P3).

**Independent Test**: Can be fully tested by either sending a test email (Gmail watcher) or creating a test file (file system watcher) and verifying a new note appears in obsidian-vault/Inbox/ within the polling interval.

**Acceptance Scenarios**:

1. **Given** the Gmail watcher is running, **When** a new email with the configured label arrives in the monitored inbox, **Then** a note is created in /Inbox with email subject, sender email address, plain text body, and timestamp (attachments not included)
2. **Given** the file system watcher is running, **When** a new file is created in the monitored directory, **Then** a note is created in /Inbox with file name, path, and creation timestamp
3. **Given** the watcher is running, **When** an error occurs (API failure, network issue), **Then** the error is logged and the watcher continues monitoring without crashing
4. **Given** the watcher has created notes, **When** I check Dashboard.md, **Then** the new inbox items are reflected in the inbox count and recent activity section

---

### Edge Cases

- What happens when the obsidian-vault directory already exists with conflicting structure?
- How does the system handle duplicate note titles in the same folder?
- What happens when Claude Code attempts to write to a note that's currently open in Obsidian?
- How does the watcher handle rate limits from Gmail API?
- What happens when the watcher encounters a file it cannot read or process?
- How does the system handle markdown files with malformed frontmatter?
- What happens when Dashboard.md is deleted or corrupted?
- How does the system handle very large email attachments or file system files?

## Requirements

### Functional Requirements

- **FR-001**: System MUST create an obsidian-vault directory with subdirectories /Inbox, /Needs_Action, /Done
- **FR-002**: System MUST create a .obsidian configuration directory with valid workspace settings
- **FR-003**: System MUST create Dashboard.md with auto-updated sections showing: folder counts with links (Inbox, Needs_Action, Done), and recent activity list displaying the last 10 created notes with titles and timestamps
- **FR-004**: System MUST create Company_Handbook.md with template sections for business processes, contacts, and guidelines
- **FR-005**: Claude Code MUST be able to read any markdown file from the vault including frontmatter
- **FR-006**: Claude Code MUST be able to write new markdown files to any vault folder with proper frontmatter
- **FR-007**: Claude Code MUST be able to update existing markdown files while preserving structure
- **FR-008**: System MUST implement Gmail watcher for monitoring inbox emails
- **FR-009**: Gmail watcher MUST run continuously and check for new emails at regular intervals (every 3 minutes)
- **FR-009a**: Gmail watcher MUST only capture emails with a specific Gmail label (configurable, default: "ToVault")
- **FR-010**: Gmail watcher MUST create notes in /Inbox folder when labeled emails are detected, extracting subject, sender email address, timestamp, and plain text body content (attachments excluded). Note filenames MUST follow format: "YYYYMMDD-HHMMSS-sanitized-subject.md" where subject is sanitized to remove special characters and truncated to 50 characters maximum
- **FR-011**: System MUST implement agent skills as separate skill definitions following .claude/skills/*/SKILL.md pattern
- **FR-012**: Agent skills MUST include: vault-create-note, vault-read-note, vault-move-note, vault-update-dashboard
- **FR-013**: All notes created by the system MUST include YAML frontmatter with at minimum: title, created date, modified date, source
- **FR-014**: Dashboard.md MUST be automatically updated with current folder counts and recent activity (last 10 notes) when notes are added to or removed from tracked folders
- **FR-015**: System MUST log all watcher activity and errors to a dedicated log file

### Key Entities

- **Obsidian Vault**: Root directory containing all markdown notes, organized into folders, with .obsidian configuration for Obsidian application compatibility
- **Note**: Individual markdown file with YAML frontmatter (title, created, modified, source, tags) and markdown body content
- **Dashboard**: Special note (Dashboard.md) that dynamically aggregates and displays folder counts (Inbox, Needs_Action, Done) with navigation links and recent activity showing the last 10 created notes with timestamps
- **Handbook**: Special note (Company_Handbook.md) that serves as the central reference for business processes and information
- **Watcher**: Background process that monitors external source (Gmail or file system) and creates notes in vault when new items detected
- **Agent Skill**: Reusable workflow definition that encapsulates common vault operations for Claude Code

## Success Criteria

### Measurable Outcomes

- **SC-001**: Obsidian vault can be opened in Obsidian application and all folders are visible and navigable
- **SC-002**: Claude Code can create a new note in any vault folder in under 2 seconds
- **SC-003**: Claude Code can read and display the full content of any vault note in under 1 second
- **SC-004**: Watcher detects and processes new items within one polling interval (3 minutes for Gmail)
- **SC-005**: Dashboard.md accurately reflects current state of vault (inbox count, action items) within 5 seconds of any change
- **SC-006**: All agent skills execute successfully without errors for valid inputs
- **SC-007**: System handles at least 100 notes in the vault without performance degradation
- **SC-008**: Watcher runs continuously for at least 24 hours without crashing or requiring restart

## Constraints

### Technical Constraints

- Must use local file system storage (no cloud dependencies for vault storage)
- Must use markdown format for all notes (Obsidian compatibility requirement)
- Must follow existing .claude/skills/ pattern for agent skill implementation
- Must use Claude Code's existing Read, Write, Grep, Glob tools for file operations
- Watcher must be implemented as standalone script (Python or Node.js) that can run independently

### Business Constraints

- Estimated implementation time: 8-12 hours
- Must deliver minimum viable functionality (Bronze Tier scope only)
- Must not include features beyond Bronze Tier requirements (no Silver/Gold tier features)

### Security Constraints

- Gmail watcher (if implemented) must use OAuth2 authentication (no password storage)
- All credentials must be stored in .env file (not committed to git)
- Watcher must not expose sensitive email content in logs
- File system watcher must respect file permissions and not attempt to read restricted files

### Operational Constraints

- Vault must be compatible with Obsidian desktop application (Windows, Mac, Linux)
- Watcher must be startable/stoppable via simple command (no complex deployment)
- System must work offline (except for Gmail watcher which requires internet)
- All components must run on user's local machine (no server deployment required)

## Assumptions

- User has Obsidian application installed or will install it to view the vault
- User has Python 3.11+ runtime available for watcher script
- User will manually configure Gmail API credentials if Gmail watcher is chosen
- User will manually start the watcher script (no automatic startup on boot)
- User has basic familiarity with markdown syntax
- Vault will contain fewer than 1000 notes initially (Bronze Tier scope)
- User will manually organize notes from /Inbox to /Needs_Action or /Done (no automatic categorization in Bronze Tier)

## Out of Scope

The following are explicitly excluded from Bronze Tier:

- Automatic email replies or sending emails from vault
- Advanced search with natural language queries
- Automatic categorization or tagging of notes
- Integration with calendar or task management systems
- Mobile app or web interface for vault access
- Real-time sync between multiple devices
- Backup and restore functionality
- Version control for notes (beyond git)
- Rich media embedding (images, videos, PDFs)
- Multiple watcher scripts running simultaneously
- MCP server implementation (deferred to Silver Tier)
- AI-powered summarization or analysis of notes
- Custom Obsidian plugins or themes
