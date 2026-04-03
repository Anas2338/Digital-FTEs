"""
Test Odoo Connection

Quick script to verify Odoo credentials and connection.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.odoo_watcher.client import OdooClient
from watchers.shared.env_loader import get_loader
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_odoo_connection():
    """Test Odoo connection and display results."""
    print("\n" + "="*60)
    print("ODOO CONNECTION TEST")
    print("="*60 + "\n")

    # Step 1: Load credentials
    print("Step 1: Loading credentials from .env...")
    try:
        loader = get_loader()
        credentials = loader.get_odoo_credentials()
        print(f"[OK] URL: {credentials['url']}")
        print(f"[OK] Database: {credentials['database']}")
        print(f"[OK] Username: {credentials['username']}")
        print(f"[OK] Password: {'*' * len(credentials['password'])}")
    except Exception as e:
        print(f"[FAIL] Failed to load credentials: {e}")
        return False

    # Step 2: Connect to Odoo
    print("\nStep 2: Connecting to Odoo...")
    client = OdooClient()

    try:
        if client.connect():
            print("[OK] Successfully connected to Odoo!")
        else:
            print("[FAIL] Failed to connect to Odoo")
            return False
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        return False

    # Step 3: Test connection and get server info
    print("\nStep 3: Testing connection and retrieving server info...")
    try:
        info = client.test_connection()

        if info.get('connected'):
            print("[OK] Connection test successful!")
            print(f"\nServer Information:")
            print(f"  - Version: {info.get('version', 'Unknown')}")
            print(f"  - Database: {info.get('database', 'Unknown')}")
            if info.get('user'):
                print(f"  - User: {info['user'].get('name', 'Unknown')} ({info['user'].get('login', 'Unknown')})")
        else:
            print(f"[FAIL] Connection test failed: {info.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"[FAIL] Test connection error: {e}")
        return False

    # Step 4: Try fetching a sample transaction
    print("\nStep 4: Fetching sample transactions (last 7 days)...")
    try:
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        transactions = client.fetch_transactions(
            start_date=start_date,
            end_date=end_date,
            limit=5
        )

        print(f"[OK] Successfully fetched {len(transactions)} transactions")

        if transactions:
            print("\nSample transactions:")
            for i, txn in enumerate(transactions[:3], 1):
                print(f"\n  Transaction {i}:")
                print(f"    - ID: {txn.get('external_id')}")
                print(f"    - Date: {txn.get('date')}")
                print(f"    - Amount: {txn.get('currency', 'USD')} {txn.get('amount', 0):.2f}")
                print(f"    - Description: {txn.get('description', 'N/A')}")
                print(f"    - Partner: {txn.get('partner_name', 'N/A')}")
        else:
            print("  (No transactions found in the last 7 days)")

    except Exception as e:
        print(f"[FAIL] Failed to fetch transactions: {e}")
        return False

    # Step 5: Disconnect
    print("\nStep 5: Disconnecting...")
    client.disconnect()
    print("[OK] Disconnected successfully")

    print("\n" + "="*60)
    print("[SUCCESS] ALL TESTS PASSED - Odoo integration is working!")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = test_odoo_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
