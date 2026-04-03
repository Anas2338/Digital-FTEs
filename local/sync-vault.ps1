# Local Vault Sync Script (PowerShell)
# Run every 30 seconds via Windows Task Scheduler
#
# Based on quickstart.md Phase 6

$VaultPath = "D:\obsidian-vault"
$LogFile = "C:\Logs\vault-sync.log"

# Ensure log directory exists
$LogDir = Split-Path $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Function to log with timestamp
function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$Timestamp] $Message" | Tee-Object -FilePath $LogFile -Append
}

# Change to vault directory
Set-Location $VaultPath

# Check if this is a git repository
if (-not (Test-Path ".git")) {
    Write-Log "ERROR: Not a git repository: $VaultPath"
    exit 1
}

# Step 1: Pull changes
Write-Log "Pulling changes from remote..."
try {
    git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $LogFile -Append
} catch {
    Write-Log "ERROR: Pull failed - $_"
    exit 1
}

# Step 2: Check for changes
$Status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($Status)) {
    Write-Log "No changes to commit"
    exit 0
}

# Step 3: Stage all changes
Write-Log "Staging changes..."
git add -A

# Step 4: Commit with timestamp
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
git commit -m "Local agent sync - $Timestamp" 2>&1 | Tee-Object -FilePath $LogFile -Append

# Step 5: Push to remote
Write-Log "Pushing to remote..."
try {
    git push 2>&1 | Tee-Object -FilePath $LogFile -Append
    Write-Log "Sync completed successfully"
} catch {
    Write-Log "WARNING: Push failed (possible race condition)"
    # Reset last commit to retry on next sync
    git reset HEAD~1
    exit 1
}

exit 0
