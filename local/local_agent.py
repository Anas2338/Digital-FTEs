"""
Local Agent Stub for Platinum Tier

Monitors /Pending_Approval/ and processes user approvals.
Executes approved actions via MCP.

Based on spec.md FR-008, FR-010, FR-029, FR-030 and User Story 2.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from coordination.approval_processor import ApprovalProcessor
from coordination.dashboard_merger import DashboardMerger
from coordination.logical_clock import LamportClock
from sync.sync_monitor import SyncMonitor


class LocalAgent:
    """
    Local agent for approval and execution.

    Responsibilities:
    - Monitor /Pending_Approval/ directories
    - Update Dashboard.md with pending approvals
    - Process user approval decisions
    - Execute approved actions via MCP
    - Maintain exclusive write access to Dashboard.md
    """

    def __init__(self, vault_path: Path):
        """
        Initialize local agent.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.approval_processor = ApprovalProcessor(vault_path, agent_id="local")
        self.dashboard_merger = DashboardMerger(vault_path)
        self.clock = LamportClock(agent_id="local")
        self.sync_monitor = SyncMonitor(vault_path, agent_id="local")
        self.logger = self._setup_logging()
        self.running = False

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for local agent."""
        logger = logging.getLogger("local_agent")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        logger.addHandler(handler)

        return logger

    async def start(self) -> None:
        """
        Start local agent main loop.

        Runs approval processing cycle every 2 minutes (FR-005).
        """
        self.running = True
        self.logger.info("Local agent starting...")
        self.logger.info(f"Vault path: {self.vault_path}")

        try:
            while self.running:
                await self._run_cycle()
                await asyncio.sleep(120)  # 2 minutes

        except Exception as e:
            self.logger.error(f"Local agent error: {e}", exc_info=True)
            raise

        finally:
            self.logger.info("Local agent stopped")

    async def _run_cycle(self) -> None:
        """
        Run one cycle of approval processing.

        Process:
        1. Check vault sync health
        2. Merge cloud agent updates from /Updates/
        3. Scan /Pending_Approval/ for new drafts
        4. Update Dashboard.md with pending approvals
        5. Process approval decisions from Dashboard.md
        6. Execute approved actions via MCP
        """
        self.logger.info("Starting approval processing cycle")

        try:
            # Step 0: Check vault sync health (T065)
            sync_status = self.sync_monitor.get_status_summary()
            if sync_status["should_alert"]:
                self.logger.warning(
                    f"Vault sync degraded: lag {sync_status['sync_lag_seconds']}s"
                )
            if sync_status["should_halt"]:
                self.logger.error(
                    f"Vault sync failed: lag {sync_status['sync_lag_seconds']}s - "
                    f"halting coordination"
                )
                return

            # Step 1: Merge cloud updates (T027)
            updates_merged = self.dashboard_merger.merge_updates()
            if updates_merged > 0:
                self.logger.info(f"Merged {updates_merged} cloud updates")

            # Step 2: Scan for pending approvals (T029)
            pending_approvals = self.approval_processor.scan_pending_approvals()

            # Step 3: Update Dashboard.md (T029)
            if pending_approvals:
                self.approval_processor.update_dashboard_with_approvals(pending_approvals)
                self.logger.info(f"Updated Dashboard with {len(pending_approvals)} pending approvals")

            # Step 4: Process approval decisions (T030)
            processed = self.approval_processor.process_approvals_from_dashboard()
            if processed > 0:
                self.logger.info(f"Processed {processed} approvals")

                # Step 5: Execute approved actions (T030)
                await self._execute_approved_actions(processed)

            # Log approval rate metric (SC-011)
            approval_rate = self.approval_processor.get_approval_rate()
            if approval_rate > 0:
                self.logger.info(f"Current approval rate: {approval_rate:.1f}%")

        except Exception as e:
            self.logger.error(f"Cycle error: {e}", exc_info=True)

    async def _execute_approved_actions(self, count: int) -> None:
        """
        Execute approved actions via MCP.

        Args:
            count: Number of approved actions to execute

        Note: Placeholder - would integrate with MCP servers for actual execution
        """
        self.logger.info(f"Executing {count} approved actions via MCP...")

        # Get approved actions from approval processor
        approved_actions = self.approval_processor.get_approved_actions()

        for action in approved_actions:
            try:
                action_type = action.get("draft_type")

                if action_type == "email_reply":
                    await self._execute_email_action(action)
                elif action_type == "social_post":
                    await self._execute_social_action(action)
                elif action_type == "accounting_entry":
                    await self._execute_accounting_action(action)
                else:
                    self.logger.warning(f"Unknown action type: {action_type}")

            except Exception as e:
                self.logger.error(f"Failed to execute action {action.get('draft_id')}: {e}", exc_info=True)

        self.logger.info("Action execution complete")

    async def _execute_email_action(self, action: dict) -> None:
        """
        Execute approved email action via MCP.

        Args:
            action: Approved email action dict
        """
        self.logger.info(f"Executing email action: {action.get('draft_id')}")

        # Placeholder: Would call MCP server
        # from mcp_servers.digital_fte_server.tools.send_email import send_email
        # await send_email(
        #     to=action['original_email']['from'],
        #     subject=f"Re: {action['original_email']['subject']}",
        #     body=action['draft_content']
        # )

        # Log to audit trail
        self._log_to_audit_trail("email_sent", action)

    async def _execute_social_action(self, action: dict) -> None:
        """
        Execute approved social media action via MCP.

        Args:
            action: Approved social action dict
        """
        self.logger.info(f"Executing social action: {action.get('draft_id')}")

        # Placeholder: Would call MCP server
        # platform = action['platform']
        # if platform == "linkedin":
        #     from mcp_servers.digital_fte_server.tools.linkedin_post import post_to_linkedin
        #     await post_to_linkedin(content=action['draft_content'])

        # Log to audit trail
        self._log_to_audit_trail("social_posted", action)

    async def _execute_accounting_action(self, action: dict) -> None:
        """
        Execute approved accounting action via MCP (post to Odoo).

        Args:
            action: Approved accounting action dict

        Note: This implements FR-029 (local agent posts accounting entries)
        and FR-030 (audit trail for accounting actions).
        """
        self.logger.info(f"Executing accounting action: {action.get('draft_id')}")

        transaction = action.get("transaction", {})
        transaction_id = transaction.get("transaction_id")
        transaction_type = transaction.get("transaction_type")

        try:
            # Placeholder: Would call MCP server to post to Odoo
            # from mcp_servers.digital_fte_server.tools.odoo_record_transaction import record_transaction
            # result = await record_transaction(
            #     transaction_id=transaction_id,
            #     transaction_type=transaction_type,
            #     partner_name=transaction['partner_name'],
            #     amount=transaction['amount'],
            #     currency=transaction['currency'],
            #     date=transaction['date'],
            #     description=transaction['description'],
            #     journal_entry=action['draft_content']
            # )

            # Log to audit trail (FR-030: accounting actions require audit trail)
            self._log_to_audit_trail("accounting_posted", action, {
                "transaction_id": transaction_id,
                "transaction_type": transaction_type,
                "amount": transaction.get("amount"),
                "currency": transaction.get("currency"),
                "posted_at": self.clock.tick().to_dict()
            })

            self.logger.info(f"Posted accounting entry for {transaction_type} {transaction_id}")

        except Exception as e:
            self.logger.error(f"Failed to post accounting entry: {e}", exc_info=True)
            # Log failure to audit trail
            self._log_to_audit_trail("accounting_failed", action, {
                "error": str(e),
                "transaction_id": transaction_id
            })
            raise

    def _log_to_audit_trail(self, event_type: str, action: dict, extra_data: dict = None) -> None:
        """
        Log action to audit trail in vault.

        Args:
            event_type: Type of event (email_sent, social_posted, accounting_posted, etc)
            action: Action dict
            extra_data: Additional data to log
        """
        try:
            timestamp = self.clock.tick()
            audit_entry = {
                "event_type": event_type,
                "draft_id": action.get("draft_id"),
                "draft_type": action.get("draft_type"),
                "executed_by": "local",
                "executed_at": timestamp.to_dict(),
                "action_details": action,
                "extra_data": extra_data or {}
            }

            # Write to audit trail file (append mode)
            audit_file = self.vault_path / "audit_trail.jsonl"
            import json
            with open(audit_file, "a") as f:
                f.write(json.dumps(audit_entry) + "\n")

            self.logger.debug(f"Logged {event_type} to audit trail")

        except Exception as e:
            self.logger.error(f"Failed to log to audit trail: {e}", exc_info=True)

    def stop(self) -> None:
        """Stop local agent gracefully."""
        self.logger.info("Stopping local agent...")
        self.running = False


def main():
    """Main entry point for local agent."""
    if len(sys.argv) < 2:
        print("Usage: python local_agent.py <vault_path>")
        sys.exit(1)

    vault_path = Path(sys.argv[1])
    if not vault_path.exists():
        print(f"Vault path not found: {vault_path}")
        sys.exit(1)

    agent = LocalAgent(vault_path)
    asyncio.run(agent.start())


if __name__ == "__main__":
    main()
