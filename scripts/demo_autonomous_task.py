#!/usr/bin/env python3
"""
Autonomous Task Execution Demo

Demonstrates Ralph Loop executing a multi-step task autonomously.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.shared.ralph_integration import RalphIntegration
import logging


def main():
    """Run autonomous task execution demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*70)
    print("Gold Tier Digital FTE - Autonomous Task Execution Demo")
    print("="*70)
    
    integration = RalphIntegration()
    
    print("\nScenario: Generate and send monthly financial report")
    print("-" * 70)
    
    print("\nStep 1: Creating multi-step task...")
    task_id = integration.create_financial_report_task()
    print(f"✓ Task created with ID: {task_id}")
    
    print("\nStep 2: Executing task autonomously (Ralph Loop)...")
    print("  The agent will:")
    print("  1. Query financial data from Odoo")
    print("  2. Generate financial summary report")
    print("  3. Send report via email to CEO")
    print("\n  Starting execution...")
    
    result = integration.execute_autonomous_task(task_id)
    
    print("\n" + "-" * 70)
    print("Execution Result:")
    print("-" * 70)
    
    if result["success"]:
        print(f"✓ Status: {result.get('status', 'completed').upper()}")
        print(f"✓ Task ID: {result['task_id']}")
        if result.get('summary_path'):
            print(f"✓ Summary saved to: {result['summary_path']}")
        
        print("\n" + "="*70)
        print("SUCCESS: Task completed autonomously!")
        print("="*70)
        print("\nThe agent successfully:")
        print("  ✓ Queried financial data from Odoo")
        print("  ✓ Generated financial summary report")
        print("  ✓ Sent report via email")
        print("\nAll steps completed without human intervention.")
        
        return 0
    else:
        print(f"✗ Status: {result.get('status', 'failed').upper()}")
        print(f"✗ Error: {result.get('error', 'Unknown error')}")
        
        if result.get('escalated'):
            print("\n" + "="*70)
            print("ESCALATED: Task requires user intervention")
            print("="*70)
            print(f"\nFailed at step: {result.get('step_number', 'unknown')}")
            print("\nThe agent encountered an issue it cannot resolve autonomously.")
            print("User intervention is required to proceed.")
        else:
            print("\n" + "="*70)
            print("FAILED: Task execution failed")
            print("="*70)
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
