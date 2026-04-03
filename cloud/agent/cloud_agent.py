"""
Cloud Agent Main Entry Point for Platinum Tier

Runs continuously on cloud VM, orchestrating watchers and draft generation.
Operates with read-only credentials only (no write access).

Based on spec.md User Story 1: Cloud agent runs 24/7 monitoring email/social
media and generating drafts even when local machine is offline.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from cloud.agent.config import CloudAgentConfig
from cloud.agent.credential_manager import CredentialManager
from cloud.agent.draft_generator import DraftGenerator
from cloud.watchers.gmail_watcher_cloud import GmailWatcherCloud
from cloud.watchers.social_watcher_cloud import SocialWatcherCloud
from cloud.watchers.odoo_watcher_cloud import OdooWatcherCloud


class CloudAgent:
    """
    Main cloud agent orchestrator.

    Responsibilities:
    - Run watchers on schedule (every 5 minutes per FR-003)
    - Generate drafts for detected events
    - Write drafts to vault using atomic write pattern
    - Maintain health status
    """

    def __init__(self, config_path: Path):
        """
        Initialize cloud agent.

        Args:
            config_path: Path to agent-config.json
        """
        self.config = CloudAgentConfig.load(config_path)
        self.credential_manager = CredentialManager(self.config)
        self.draft_generator = DraftGenerator(self.config)

        # Initialize watchers (T049, T015, T016)
        self.gmail_watcher = GmailWatcherCloud(self.credential_manager)
        self.social_watcher = SocialWatcherCloud(self.credential_manager)
        self.odoo_watcher = OdooWatcherCloud(self.credential_manager)

        self.running = False
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for cloud agent."""
        logger = logging.getLogger("cloud_agent")
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
        Start cloud agent main loop.

        Runs continuously until stopped by signal or error.
        Implements Ralph Wiggum loop pattern from constitution.
        """
        self.running = True
        self.logger.info("Cloud agent starting...")
        self.logger.info(f"Agent ID: {self.config.agent_id}")
        self.logger.info(f"Credential scope: {self.config.credential_scope}")
        self.logger.info(f"Vault path: {self.config.vault_path}")

        # Verify read-only credentials (FR-005)
        if self.config.credential_scope != "read_only":
            self.logger.error("Cloud agent MUST have read_only credential scope")
            sys.exit(1)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        try:
            while self.running:
                await self._run_cycle()
                await asyncio.sleep(300)  # 5 minutes per FR-003

        except Exception as e:
            self.logger.error(f"Cloud agent error: {e}", exc_info=True)
            raise

        finally:
            self.logger.info("Cloud agent stopped")

    async def _run_cycle(self) -> None:
        """
        Run one cycle of watcher orchestration.

        Process:
        1. Run all watchers (email, social media, Odoo)
        2. Collect detected events
        3. Generate drafts for events
        4. Write drafts to vault
        5. Check Odoo health (every cycle per FR-028)
        """
        self.logger.info(f"Starting watcher cycle at {datetime.now()}")

        try:
            # Run watchers
            events = await self._run_watchers()

            # Generate drafts for events
            if events:
                self.logger.info(f"Processing {len(events)} events")
                await self._process_events(events)
            else:
                self.logger.debug("No events detected")

            # Check Odoo health (T052: FR-028 requirement)
            await self._check_odoo_health()

        except Exception as e:
            self.logger.error(f"Cycle error: {e}", exc_info=True)

    async def _run_watchers(self) -> list:
        """
        Run all configured watchers.

        Returns:
            List of detected events
        """
        all_events = []

        try:
            # Run Gmail watcher (T015)
            email_events = await self.gmail_watcher.check_for_new_emails()
            all_events.extend(email_events)

            # Run social media watcher (T016)
            social_events = await self.social_watcher.check_for_new_posts()
            all_events.extend(social_events)

            # Run Odoo watcher (T049)
            odoo_events = await self.odoo_watcher.check_for_new_transactions()
            all_events.extend(odoo_events)

            self.logger.debug(f"Watchers found {len(all_events)} total events")

        except Exception as e:
            self.logger.error(f"Error running watchers: {e}", exc_info=True)

        return all_events

    async def _check_odoo_health(self) -> None:
        """
        Check Odoo health status and log results.

        Implements T052: FR-028 requirement for health monitoring.
        Runs every 5 minutes as part of the watcher cycle.
        """
        try:
            health_status = await self.odoo_watcher.check_odoo_health()

            if health_status["status"] == "unhealthy":
                self.logger.warning(
                    f"Odoo health check failed: {health_status.get('error')}"
                )
                # Could write alert to vault here for local agent notification
            else:
                response_time = health_status.get("response_time_seconds", 0)
                self.logger.debug(
                    f"Odoo health check passed (response time: {response_time:.2f}s)"
                )

        except Exception as e:
            self.logger.error(f"Odoo health check error: {e}", exc_info=True)

    async def _process_events(self, events: list) -> None:
        """
        Process events and generate drafts.

        Args:
            events: List of events from watchers
        """
        for event in events:
            try:
                await self.draft_generator.generate_draft(event)
            except Exception as e:
                self.logger.error(f"Failed to process event {event}: {e}")

    def _handle_shutdown(self, signum, frame) -> None:
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False


def main():
    """Main entry point for cloud agent."""
    if len(sys.argv) < 2:
        print("Usage: python cloud_agent.py <config_path>")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    agent = CloudAgent(config_path)
    asyncio.run(agent.start())


if __name__ == "__main__":
    main()
