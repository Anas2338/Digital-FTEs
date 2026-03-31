"""CLI for approval workflow management.

Provides commands to list, approve, and reject pending actions.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from approval.queue import ApprovalQueueManager
from approval.executor import ActionExecutor


def list_pending(queue_manager: ApprovalQueueManager):
    """List all pending approval requests."""
    pending = queue_manager.list_pending()

    if not pending:
        print("No pending approvals.")
        return

    print(f"\n{'='*80}")
    print(f"PENDING APPROVALS ({len(pending)} total)")
    print(f"{'='*80}\n")

    for action in pending:
        print(f"Action ID: {action['action_id']}")
        print(f"Type: {action['action_type']}")
        print(f"Safety Level: {action['safety_level']}")
        print(f"Created: {action['created_timestamp']}")
        print(f"Parameters:")
        for key, value in action['parameters'].items():
            # Sanitize sensitive data
            if key in ['body', 'content', 'message']:
                display_value = value[:100] + "..." if len(value) > 100 else value
            else:
                display_value = value
            print(f"  {key}: {display_value}")
        print(f"{'-'*80}\n")


def approve_action(queue_manager: ApprovalQueueManager, executor: ActionExecutor,
                  action_id: str, tools_registry: dict):
    """Approve and execute an action."""
    # First approve in queue
    success = queue_manager.approve(action_id)

    if not success:
        print(f"[FAIL] Failed to approve action {action_id}")
        return False

    print(f"[PASS] Action {action_id} approved")

    # Execute the action
    result = executor.execute(action_id, tools_registry)

    if result.get("success"):
        print(f"[PASS] Action {action_id} executed successfully")
        if result.get("message"):
            print(f"Result: {result['message']}")
        return True
    else:
        print(f"[FAIL] Action {action_id} execution failed")
        print(f"Error: {result.get('error', 'Unknown error')}")
        return False


def reject_action(queue_manager: ApprovalQueueManager, action_id: str, reason: str):
    """Reject an action with a reason."""
    success = queue_manager.reject(action_id, reason)

    if success:
        print(f"[PASS] Action {action_id} rejected")
        print(f"Reason: {reason}")
        return True
    else:
        print(f"[FAIL] Failed to reject action {action_id}")
        return False


def approve_all(queue_manager: ApprovalQueueManager, executor: ActionExecutor,
               tools_registry: dict):
    """Approve and execute all pending actions."""
    pending = queue_manager.list_pending()

    if not pending:
        print("No pending approvals.")
        return

    print(f"\n[WARN] Approving ALL {len(pending)} pending actions...")
    print("This will execute all queued actions without individual review.\n")

    confirm = input("Type 'yes' to confirm: ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    success_count = 0
    fail_count = 0

    for action in pending:
        action_id = action['action_id']
        print(f"\nProcessing {action_id}...")

        if approve_action(queue_manager, executor, action_id, tools_registry):
            success_count += 1
        else:
            fail_count += 1

    print(f"\n{'='*80}")
    print(f"SUMMARY: {success_count} succeeded, {fail_count} failed")
    print(f"{'='*80}\n")


def expire_old(queue_manager: ApprovalQueueManager):
    """Expire pending approvals older than 24 hours."""
    expired_count = queue_manager.expire_old_approvals()

    if expired_count > 0:
        print(f"[PASS] Expired {expired_count} old approval(s)")
    else:
        print("No approvals to expire.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Digital FTE Approval Workflow CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List pending approvals
  python -m mcp_servers.digital_fte_server.approval.cli list

  # Approve an action
  python -m mcp_servers.digital_fte_server.approval.cli approve action-20260330120000

  # Reject an action
  python -m mcp_servers.digital_fte_server.approval.cli reject action-20260330120000 "Incorrect recipient"

  # Approve all pending actions
  python -m mcp_servers.digital_fte_server.approval.cli approve-all

  # Expire old approvals
  python -m mcp_servers.digital_fte_server.approval.cli expire
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    subparsers.add_parser('list', help='List all pending approval requests')

    # Approve command
    approve_parser = subparsers.add_parser('approve', help='Approve an action')
    approve_parser.add_argument('action_id', help='Action ID to approve')

    # Reject command
    reject_parser = subparsers.add_parser('reject', help='Reject an action')
    reject_parser.add_argument('action_id', help='Action ID to reject')
    reject_parser.add_argument('reason', help='Rejection reason')

    # Approve-all command
    subparsers.add_parser('approve-all', help='Approve all pending actions (use with caution)')

    # Expire command
    subparsers.add_parser('expire', help='Expire old approvals (24+ hours)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize components
    queue_manager = ApprovalQueueManager()
    executor = ActionExecutor()

    # Import tools registry (needed for execution)
    from tools.send_email import SendEmailTool
    from tools.linkedin_post import LinkedInPostTool
    from tools.whatsapp_send import WhatsAppSendTool

    tools_registry = {
        "send-email": SendEmailTool(),
        "linkedin-post": LinkedInPostTool(),
        "whatsapp-send": WhatsAppSendTool()
    }

    # Execute command
    try:
        if args.command == 'list':
            list_pending(queue_manager)

        elif args.command == 'approve':
            approve_action(queue_manager, executor, args.action_id, tools_registry)

        elif args.command == 'reject':
            reject_action(queue_manager, args.action_id, args.reason)

        elif args.command == 'approve-all':
            approve_all(queue_manager, executor, tools_registry)

        elif args.command == 'expire':
            expire_old(queue_manager)

    except Exception as e:
        print(f"\n[ERROR] Command failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
