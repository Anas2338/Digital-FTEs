"""WhatsApp watcher configuration."""

from typing import Dict, Any


class WhatsAppConfig:
    """Configuration for WhatsApp watcher."""

    # Polling interval in seconds (5 minutes)
    POLLING_INTERVAL = 300

    # Session storage path
    SESSION_PATH = "watchers/whatsapp_watcher/.wwebjs_auth/"

    # QR code timeout in seconds (60 seconds)
    QR_TIMEOUT = 60

    # Node.js bridge script path
    BRIDGE_SCRIPT = "watchers/whatsapp_watcher/bridge.js"

    # Maximum message length to store
    MAX_MESSAGE_LENGTH = 5000

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dict.

        Returns:
            Configuration dict
        """
        return {
            "polling_interval": cls.POLLING_INTERVAL,
            "session_path": cls.SESSION_PATH,
            "qr_timeout": cls.QR_TIMEOUT,
            "bridge_script": cls.BRIDGE_SCRIPT,
            "max_message_length": cls.MAX_MESSAGE_LENGTH
        }
