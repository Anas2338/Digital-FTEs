"""
Test Odoo MCP Tools

Tests all Odoo-related MCP tools to verify they work with the configured credentials.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers" / "digital-fte-server"))

from tools.odoo_check_connection import odoo_check_connection
from tools.odoo_get_transactions import odoo_get_transactions
from tools.odoo_query_financials import odoo_query_financials

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_odoo_mcp_tools():
    """Test all Odoo MCP tools."""
    print("\n" + "="*60)
    print("ODOO MCP TOOLS TEST")
    print("="*60 + "\n")

    # Test 1: Check Connection
    print("Test 1: odoo_check_connection")
    print("-" * 40)
    try:
        result = odoo_check_connection()
        if result.get("success"):
            print("[OK] Connection check passed")
            print(f"  - Version: {result.get('version')}")
            print(f"  - Database: {result.get('database')}")
            print(f"  - Message: {result.get('message')}")
        else:
            print(f"[FAIL] Connection check failed: {result.get('message')}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

    # Test 2: Get Transactions
    print("\nTest 2: odoo_get_transactions")
    print("-" * 40)
    try:
        from datetime import datetime, timedelta

        # Calculate date range (last 7 days)
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()

        result = odoo_get_transactions(start_date=start_date, end_date=end_date, limit=5)
        if result.get("success"):
            print(f"[OK] Retrieved {result.get('count', 0)} transactions")
            transactions = result.get('transactions', [])
            if transactions:
                print("\nSample transactions:")
                for i, txn in enumerate(transactions[:3], 1):
                    print(f"\n  Transaction {i}:")
                    print(f"    - ID: {txn.get('id')}")
                    print(f"    - Date: {txn.get('date')}")
                    print(f"    - Amount: {txn.get('amount')}")
                    print(f"    - Description: {txn.get('description')}")
            else:
                print("  (No transactions in database yet - run the Odoo watcher to sync)")
        else:
            print(f"[FAIL] Get transactions failed: {result.get('message')}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Query Financials
    print("\nTest 3: odoo_query_financials")
    print("-" * 40)
    try:
        from datetime import datetime, timedelta

        # Calculate date range (last 30 days)
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = datetime.now().isoformat()

        result = odoo_query_financials(start_date=start_date, end_date=end_date)
        if result.get("success"):
            print("[OK] Financial query successful")
            print(f"\n  Financial Summary (last 30 days):")
            print(f"    - Total Transactions: {result.get('total_transactions', 0)}")
            print(f"    - Total Amount: ${result.get('total_amount', 0):,.2f}")

            aggregated = result.get('aggregated_data', {})
            if aggregated:
                print(f"\n  Breakdown by Category:")
                for category, data in aggregated.items():
                    print(f"    - {category}: {data['count']} transactions, ${data['total_amount']:,.2f}")
            else:
                print("    (No transactions in database yet - run the Odoo watcher to sync)")
        else:
            print(f"[FAIL] Financial query failed: {result.get('message')}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*60)
    print("[SUCCESS] ALL MCP TOOLS TESTS PASSED!")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = test_odoo_mcp_tools()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
