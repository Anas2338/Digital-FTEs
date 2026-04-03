#!/usr/bin/env python3
"""
Circuit Breaker Reset Script

Manually resets circuit breakers for recovery after issues are resolved.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database
from watchers.shared.circuit_breaker import CircuitBreaker
from datetime import datetime
import argparse


def list_circuit_breakers(db: Database):
    """List all circuit breakers and their states."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT integration_name, circuit_breaker_state, 
               failure_count, last_failure_time, last_success_time
        FROM integration_status
        ORDER BY integration_name
    """)
    
    breakers = cursor.fetchall()
    
    print("\n" + "="*70)
    print("Circuit Breaker Status")
    print("="*70)
    
    if not breakers:
        print("\nNo circuit breakers found.")
        return
    
    for breaker in breakers:
        state = breaker["circuit_breaker_state"]
        status_symbol = "✗" if state == "OPEN" else "✓"
        
        print(f"\n{status_symbol} {breaker['integration_name']}")
        print(f"  State: {state}")
        print(f"  Failures: {breaker['failure_count']}")
        print(f"  Last Failure: {breaker['last_failure_time'] or 'Never'}")
        print(f"  Last Success: {breaker['last_success_time'] or 'Never'}")


def reset_circuit_breaker(integration_name: str, db: Database):
    """Reset a specific circuit breaker."""
    cb = CircuitBreaker(name=integration_name, db=db)
    
    print(f"\nResetting circuit breaker: {integration_name}")
    
    current_state = cb.get_state()
    print(f"  Current state: {current_state}")
    
    if current_state == "CLOSED":
        print(f"  ⚠ Circuit breaker is already CLOSED")
        return False
    
    cb.reset()
    
    new_state = cb.get_state()
    print(f"  New state: {new_state}")
    print(f"  ✓ Circuit breaker reset successfully")
    
    return True


def reset_all_circuit_breakers(db: Database):
    """Reset all open circuit breakers."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT integration_name
        FROM integration_status
        WHERE circuit_breaker_state = 'OPEN'
    """)
    
    open_breakers = cursor.fetchall()
    
    if not open_breakers:
        print("\n✓ No open circuit breakers to reset")
        return 0
    
    print(f"\nFound {len(open_breakers)} open circuit breaker(s)")
    
    reset_count = 0
    for breaker in open_breakers:
        if reset_circuit_breaker(breaker["integration_name"], db):
            reset_count += 1
    
    print(f"\n✓ Reset {reset_count} circuit breaker(s)")
    return reset_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reset circuit breakers for manual recovery"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all circuit breakers and their states"
    )
    parser.add_argument(
        "--reset",
        metavar="NAME",
        help="Reset a specific circuit breaker by name"
    )
    parser.add_argument(
        "--reset-all",
        action="store_true",
        help="Reset all open circuit breakers"
    )
    
    args = parser.parse_args()
    
    db = Database()
    
    if args.list:
        list_circuit_breakers(db)
        return 0
    
    if args.reset:
        reset_circuit_breaker(args.reset, db)
        return 0
    
    if args.reset_all:
        reset_all_circuit_breakers(db)
        return 0
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
