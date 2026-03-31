"""Centralized logging with rotation for Digital FTE watchers.

Provides log rotation policy to prevent log files from growing indefinitely.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class RotatingLogger:
    """Centralized logger with rotation policy."""

    def __init__(self, log_dir: str = "watchers/logs",
                 max_bytes: int = 10 * 1024 * 1024,  # 10 MB
                 backup_count: int = 5):
        """Initialize rotating logger.

        Args:
            log_dir: Directory for log files
            max_bytes: Maximum size per log file (default: 10 MB)
            backup_count: Number of backup files to keep (default: 5)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def get_logger(self, name: str, log_file: Optional[str] = None) -> logging.Logger:
        """Get a logger with rotation.

        Args:
            name: Logger name
            log_file: Log file name (default: {name}.log)

        Returns:
            Configured logger
        """
        if not log_file:
            log_file = f"{name}.log"

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        # Create rotating file handler
        log_path = self.log_dir / log_file
        handler = RotatingFileHandler(
            log_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        handler.setLevel(logging.INFO)

        # Format: timestamp | level | message
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger


# Global logger instances
_loggers = {}


def get_watcher_logger(watcher_name: str) -> logging.Logger:
    """Get logger for a specific watcher.

    Args:
        watcher_name: Name of the watcher (gmail, whatsapp, linkedin)

    Returns:
        Configured logger
    """
    if watcher_name not in _loggers:
        rotating_logger = RotatingLogger()
        _loggers[watcher_name] = rotating_logger.get_logger(
            f"watcher.{watcher_name}",
            f"{watcher_name}_watcher.log"
        )

    return _loggers[watcher_name]
