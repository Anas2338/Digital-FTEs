#!/bin/bash
# Vault Sync Script for Cloud Agent
# Runs every 30 seconds via systemd timer
#
# Based on quickstart.md Phase 2 and spec.md FR-015

set -e

VAULT_PATH="/opt/cloud-agent/obsidian-vault"
LOG_FILE="/opt/cloud-agent/logs/vault-sync.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Change to vault directory
cd "$VAULT_PATH" || {
    log "ERROR: Vault directory not found: $VAULT_PATH"
    exit 1
}

# Check if this is a git repository
if [ ! -d ".git" ]; then
    log "ERROR: Not a git repository: $VAULT_PATH"
    exit 1
fi

# Step 1: Pull changes with rebase and autostash
log "Pulling changes from remote..."
if ! git pull --rebase --autostash 2>&1 | tee -a "$LOG_FILE"; then
    log "ERROR: Pull failed"
    exit 1
fi

# Step 2: Check for changes to commit
if git diff --quiet && git diff --cached --quiet; then
    log "No changes to commit"
    exit 0
fi

# Step 3: Stage all changes
log "Staging changes..."
git add -A

# Step 4: Commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
git commit -m "Cloud agent sync - $TIMESTAMP" 2>&1 | tee -a "$LOG_FILE"

# Step 5: Push to remote
log "Pushing to remote..."
if ! git push 2>&1 | tee -a "$LOG_FILE"; then
    log "WARNING: Push failed (possible race condition)"
    # Reset last commit to retry on next sync
    git reset HEAD~1
    exit 1
fi

log "Sync completed successfully"
exit 0
