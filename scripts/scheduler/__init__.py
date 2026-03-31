"""Platform detection and scheduler initialization.

Detects the operating system and initializes the appropriate scheduler:
- Unix/Linux: crontab
- Windows: Task Scheduler
- macOS: launchd (future)
"""

import sys
import platform
from typing import Optional

# Lazy imports to avoid loading platform-specific modules
_cron_manager = None
_taskscheduler_manager = None


def get_platform() -> str:
    """Detect the current platform.

    Returns:
        Platform identifier: 'linux', 'windows', 'darwin', 'unknown'
    """
    system = platform.system().lower()

    if system == 'linux':
        return 'linux'
    elif system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'darwin'
    else:
        return 'unknown'


def get_scheduler():
    """Get the appropriate scheduler for the current platform.

    Returns:
        Scheduler instance (CronManager or TaskSchedulerManager)

    Raises:
        NotImplementedError: If platform is not supported
    """
    global _cron_manager, _taskscheduler_manager

    current_platform = get_platform()

    if current_platform in ['linux', 'darwin']:
        # Use cron for Unix-like systems
        if _cron_manager is None:
            from scripts.scheduler.cron_manager import CronManager
            _cron_manager = CronManager()
        return _cron_manager

    elif current_platform == 'windows':
        # Use Task Scheduler for Windows
        if _taskscheduler_manager is None:
            from scripts.scheduler.taskscheduler_manager import TaskSchedulerManager
            _taskscheduler_manager = TaskSchedulerManager()
        return _taskscheduler_manager

    else:
        raise NotImplementedError(f"Scheduler not implemented for platform: {current_platform}")


def is_scheduler_available() -> bool:
    """Check if a scheduler is available on this platform.

    Returns:
        True if scheduler is available
    """
    try:
        get_scheduler()
        return True
    except NotImplementedError:
        return False


__all__ = ['get_platform', 'get_scheduler', 'is_scheduler_available']
