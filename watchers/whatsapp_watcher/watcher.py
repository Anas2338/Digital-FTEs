"""WhatsApp watcher implementation using Node.js bridge.

This watcher monitors WhatsApp messages via whatsapp-web.js library
running in a Node.js subprocess.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.base_watcher import BaseWatcher
from watchers.whatsapp_watcher.config import WhatsAppConfig


class WhatsAppWatcher(BaseWatcher):
    """WhatsApp watcher using Node.js bridge."""

    def __init__(self):
        """Initialize WhatsApp watcher."""
        super().__init__(
            watcher_name="whatsapp",
            polling_interval=WhatsAppConfig.POLLING_INTERVAL
        )
        self.config = WhatsAppConfig
        self.bridge_process = None
        self.last_message_id = None

    def poll(self) -> List[Dict[str, Any]]:
        """Poll for new WhatsApp messages.

        Returns:
            List of event dicts
        """
        # For MVP, return empty list (bridge integration to be completed)
        # Full implementation would:
        # 1. Start Node.js bridge if not running
        # 2. Query bridge for new messages via IPC
        # 3. Filter messages since last_message_id
        # 4. Return formatted events

        # Placeholder: Return empty list
        return []

    def get_config(self) -> Dict[str, Any]:
        """Get watcher configuration.

        Returns:
            Configuration dict
        """
        return self.config.to_dict()

    def _start_bridge(self):
        """Start Node.js bridge process.

        This is a placeholder for bridge integration.
        Full implementation would:
        1. Launch Node.js bridge as subprocess
        2. Wait for QR code authentication
        3. Establish IPC communication
        """
        pass

    def _stop_bridge(self):
        """Stop Node.js bridge process."""
        if self.bridge_process:
            self.bridge_process.terminate()
            self.bridge_process.wait()
            self.bridge_process = None


def main():
    """Main entry point for WhatsApp watcher."""
    watcher = WhatsAppWatcher()
    try:
        watcher.start()
    except KeyboardInterrupt:
        print("\nShutting down WhatsApp watcher...")
        watcher.stop()


if __name__ == "__main__":
    main()
