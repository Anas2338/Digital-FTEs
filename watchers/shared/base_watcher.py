"""Base watcher class for Digital FTE watchers.

Provides common functionality for all watchers including polling loop,
health checks, error handling, and event logging.
"""

import time
import signal
import sys
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from .database import Database
from .event_logger import EventLogger
from .vault_writer import VaultWriter
from .keychain import KeychainManager


class BaseWatcher(ABC):
    """Abstract base class for all watchers."""

    def __init__(self, watcher_name: str, polling_interval: int = 300):
        """Initialize base watcher.

        Args:
            watcher_name: Name of the watcher (gmail, whatsapp, linkedin)
            polling_interval: Polling interval in seconds (default: 5 minutes)
        """
        self.watcher_name = watcher_name
        self.polling_interval = polling_interval
        self.running = False
        self.error_count = 0

        # Initialize shared components
        self.db = Database()
        self.event_logger = EventLogger()
        self.vault_writer = VaultWriter()
        self.keychain = KeychainManager()

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def start(self):
        """Start the watcher polling loop."""
        self.running = True
        print(f"[{self.watcher_name}] Starting watcher (polling every {self.polling_interval}s)")

        # Update health status
        self._update_health("healthy")

        while self.running:
            try:
                # Poll for new events
                events = self.poll()

                # Process each event
                for event in events:
                    self._process_event(event)

                # Reset error count on successful poll
                if self.error_count > 0:
                    self.error_count = 0
                    self._update_health("healthy")

            except Exception as e:
                self._handle_error(e)

            # Update health check timestamp
            self._update_health("healthy" if self.error_count == 0 else "degraded")

            # Sleep until next poll
            if self.running:
                time.sleep(self.polling_interval)

        print(f"[{self.watcher_name}] Watcher stopped")

    def stop(self):
        """Stop the watcher polling loop."""
        self.running = False

    @abstractmethod
    def poll(self) -> List[Dict[str, Any]]:
        """Poll for new events.

        This method must be implemented by subclasses to fetch new events
        from their respective channels (Gmail, WhatsApp, LinkedIn).

        Returns:
            List of event dicts
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get watcher configuration.

        Returns:
            Configuration dict
        """
        pass

    def _process_event(self, event: Dict[str, Any]):
        """Process a single event.

        Args:
            event: Event dict with keys: event_type, content
        """
        try:
            # Generate event ID
            event_id = str(uuid.uuid4())

            # Log event
            self.event_logger.log_event(
                source_channel=self.watcher_name,
                event_type=event["event_type"],
                content=event["content"],
                event_id=event_id
            )

            # Store in database
            self.db.log_event(
                event_id=event_id,
                source_channel=self.watcher_name,
                event_type=event["event_type"],
                content=event["content"],
                processing_status="pending"
            )

            # Create vault note
            vault_path = self.vault_writer.create_event_note(
                source_channel=self.watcher_name,
                event_type=event["event_type"],
                event_data=event["content"]
            )

            # Update event status
            self.db.update_event_status(
                event_id=event_id,
                processing_status="processed",
                vault_note_path=vault_path
            )

            print(f"[{self.watcher_name}] Processed event {event_id} -> {vault_path}")

        except Exception as e:
            # Log error
            self.event_logger.log_error(
                source_channel=self.watcher_name,
                error_message=f"Failed to process event: {str(e)}",
                error_details={"event": event}
            )

            # Update event status if we have an event_id
            if 'event_id' in locals():
                self.db.update_event_status(
                    event_id=event_id,
                    processing_status="failed",
                    error_message=str(e)
                )

            print(f"[{self.watcher_name}] Error processing event: {e}")

    def _handle_error(self, error: Exception):
        """Handle polling error.

        Args:
            error: Exception that occurred
        """
        self.error_count += 1

        # Log error
        self.event_logger.log_error(
            source_channel=self.watcher_name,
            error_message=str(error),
            error_details={"error_count": self.error_count}
        )

        # Update health status
        if self.error_count >= 3:
            health_status = "unhealthy"
        else:
            health_status = "degraded"

        self._update_health(health_status)

        print(f"[{self.watcher_name}] Error (count: {self.error_count}): {error}")

        # Exponential backoff for retries
        if self.error_count <= 3:
            backoff_time = min(2 ** self.error_count, 60)  # Max 60 seconds
            print(f"[{self.watcher_name}] Retrying in {backoff_time}s...")
            time.sleep(backoff_time)

    def _update_health(self, health_status: str):
        """Update watcher health status in database.

        Args:
            health_status: Health status (healthy, degraded, unhealthy)
        """
        config = self.get_config()
        self.db.update_watcher_health(
            watcher_name=self.watcher_name,
            health_status=health_status,
            error_count=self.error_count,
            config=config
        )

        self.event_logger.log_health_check(
            watcher_name=self.watcher_name,
            health_status=health_status,
            error_count=self.error_count
        )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print(f"\n[{self.watcher_name}] Received signal {signum}, shutting down...")
        self.stop()
