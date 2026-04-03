"""
Odoo Connection Test Script

Tests the connection to Odoo Community Edition 19+ and validates credentials.
Run this script to verify Odoo integration is properly configured.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.odoo_watcher.client import OdooClient
from watchers.odoo_watcher.config import OdooConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_odoo_connection():
    """Test Odoo connection and display server information."""
    print("=" * 60)
    print("Odoo Connection Test")
    print("=" * 60)
    print()

    # Create client
    client = OdooClient()

    # Test connection
    print("Attempting to connect to Odoo...")
    connected = client.connect()

    if not connected:
        print("❌ Connection failed!")
        print()
        print("Please check:")
        print("1. Odoo credentials are stored in OS keychain")
        print("2. Run: python watchers/setup_credentials.py")
        print("3. Verify Odoo server is running and accessible")
        return False

    print("✓ Connected successfully!")
    print()

    # Get server info
    print("Retrieving server information...")
    info = client.test_connection()

    if info.get("connected"):
        print("✓ Connection test passed!")
        print()
        print("Server Information:")
        print(f"  - Version: {info.get('version')}")
        print(f"  - Database: {info.get('database')}")
        if info.get('user'):
            print(f"  - User: {info['user'].get('name')} ({info['user'].get('login')})")
        print()

        # Test fetching transactions
        print("Testing transaction fetch...")
        try:
            transactions = client.fetch_transactions(limit=5)
            print(f"✓ Successfully fetched {len(transactions)} transactions")
            print()

            if transactions:
                print("Sample transactions:")
                for i, txn in enumerate(transactions[:3], 1):
                    print(f"  {i}. {txn['date']}: {txn['description']} - ${txn['amount']:.2f}")
                print()

        except Exception as e:
            print(f"❌ Failed to fetch transactions: {e}")
            print()

    else:
        print(f"❌ Connection test failed: {info.get('error')}")
        print()

    # Disconnect
    client.disconnect()
    print("Disconnected from Odoo")
    print()

    # Display configuration
    print("Configuration:")
    print(f"  - Poll Interval: {OdooConfig.POLL_INTERVAL_SECONDS}s")
    print(f"  - Initial Sync: {OdooConfig.INITIAL_SYNC_DAYS} days")
    print(f"  - Max Transactions per Poll: {OdooConfig.MAX_TRANSACTIONS_PER_POLL}")
    print(f"  - Circuit Breaker Threshold: {OdooConfig.CIRCUIT_BREAKER_FAILURE_THRESHOLD * 100}%")
    print()

    print("=" * 60)
    print("Test Complete")
    print("=" * 60)

    return info.get("connected", False)


if __name__ == "__main__":
    try:
        success = test_odoo_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
