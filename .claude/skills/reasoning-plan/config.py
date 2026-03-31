"""Configuration for reasoning-plan skill.

Customize complexity thresholds, execution settings, and validation parameters.
"""

# Complexity threshold (default: 25)
# Tasks scoring >= this value will trigger automatic plan generation
COMPLEXITY_THRESHOLD = 25

# Auto-execute plans (default: False - requires user approval)
# Set to True to automatically execute plans without user confirmation
AUTO_EXECUTE = False

# Max execution time per step (minutes)
# Steps exceeding this time will be marked as timeout
MAX_STEP_TIME = 60

# Max re-evaluation attempts
# Plans failing more than this many times will be marked as failed
MAX_REEVALUATIONS = 3

# Validation timeout (seconds)
# Validation checks exceeding this time will be marked as needs_manual_check
VALIDATION_TIMEOUT = 30

# Polling interval for /Needs_Action monitoring (seconds)
MONITOR_INTERVAL = 60

# Minimum time between plan updates (seconds)
# Prevents excessive plan re-generation
MIN_UPDATE_INTERVAL = 300

# Enable automatic /Needs_Action monitoring
AUTO_MONITOR = True

# Complexity level thresholds
COMPLEXITY_LEVELS = {
    "trivial": (0, 9),
    "simple": (10, 24),
    "moderate": (25, 49),
    "complex": (50, 74),
    "very_complex": (75, float('inf'))
}

# Step status values
STEP_STATUS = {
    "PENDING": "pending",
    "IN_PROGRESS": "in_progress",
    "COMPLETED": "completed",
    "FAILED": "failed",
    "SKIPPED": "skipped",
    "VALIDATED": "validated"
}

# Plan status values
PLAN_STATUS = {
    "DRAFT": "draft",
    "IN_PROGRESS": "in_progress",
    "BLOCKED": "blocked",
    "COMPLETED": "completed",
    "FAILED": "failed",
    "ABANDONED": "abandoned"
}

# Vault directories
VAULT_DIRS = {
    "needs_action": "Needs_Action",
    "done": "Done",
    "dashboard": "Dashboard.md"
}
