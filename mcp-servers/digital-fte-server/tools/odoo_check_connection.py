"""
MCP Tool: Check Odoo Connection

Tests the connection to Odoo and returns server information.
Safety Level: 0 (Auto-Execute) - Read-only health check operation.
"""

from typing import Dict, Any
import logging

from watchers.odoo_watcher.client import OdooClient

logger = logging.getLogger(__name__)


def odoo_check_connection() -> Dict[str, Any]:
    """
    Check Odoo connection status and retrieve server information.

    Returns:
        Result dictionary with connection status and server info
    """
    try:
        client = OdooClient()

        # Attempt connection
        connected = client.connect()

        if not connected:
            return {
                "success": False,
                "connected": False,
                "message": "Failed to connect to Odoo. Check credentials in keychain."
            }

        # Test connection and get server info
        connection_info = client.test_connection()

        # Disconnect
        client.disconnect()

        if connection_info.get("connected"):
            logger.info("Odoo connection test successful")
            return {
                "success": True,
                "connected": True,
                "version": connection_info.get("version"),
                "database": connection_info.get("database"),
                "user": connection_info.get("user"),
                "message": f"Connected to Odoo {connection_info.get('version')} successfully"
            }
        else:
            logger.warning(f"Odoo connection test failed: {connection_info.get('error')}")
            return {
                "success": False,
                "connected": False,
                "error": connection_info.get("error"),
                "message": f"Connection test failed: {connection_info.get('error')}"
            }

    except Exception as e:
        logger.error(f"Error checking Odoo connection: {e}", exc_info=True)
        return {
            "success": False,
            "connected": False,
            "error": str(e),
            "message": f"Error checking connection: {str(e)}"
        }
