"""
Race Detector for Platinum Tier

Detects and resolves race conditions when both agents claim same task.
Uses Git push failures and logical timestamps for resolution.

Based on spec.md FR-023 and User Story 3.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from coordination.logical_clock import LamportTimestamp
from sync.git_sync import GitSyncManager


class RaceDetector:
    """
    Detects race conditions during claim-by-move operations.

    Race detection strategy (FR-023):
    1. Agent attempts to claim task (move file)
    2. Agent commits and pushes to Git
    3. If push fails → race condition detected
    4. Resolve using logical timestamps (first-write-wins)
    """

    def __init__(self, vault_path: Path, agent_id: str):
        """
        Initialize race detector.

        Args:
            vault_path: Path to Obsidian vault
            agent_id: Agent identifier (cloud or local)
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"race_detector_{agent_id}")
        self.git_sync = GitSyncManager(vault_path, agent_id)

    def detect_race_after_claim(self) -> Tuple[bool, Optional[str]]:
        """
        Detect race condition after claiming a task.

        Process:
        1. Attempt to sync (commit + push)
        2. If push fails → race detected
        3. Pull to get other agent's changes
        4. Check if our claim still exists

        Returns:
            Tuple of (race_detected, winner_agent_id)
            - (False, None) if no race
            - (True, agent_id) if race detected, with winner
        """
        try:
            # Attempt to sync (this will push our claim)
            success, error = self.git_sync.sync()

            if success:
                # No race - our push succeeded
                self.logger.debug("No race condition detected")
                return False, None

            # Push failed - possible race condition
            if "race condition" in (error or "").lower() or "rejected" in (error or "").lower():
                self.logger.warning("Race condition detected during claim")

                # Pull to get other agent's changes
                pull_success, _ = self.git_sync._pull()
                if not pull_success:
                    self.logger.error("Failed to pull after race detection")
                    return True, None

                # Determine winner using logical timestamps
                winner = self._determine_race_winner()
                self.logger.info(f"Race resolved: winner is {winner}")

                return True, winner

            # Other error (not a race)
            self.logger.error(f"Sync failed (not a race): {error}")
            return False, None

        except Exception as e:
            self.logger.error(f"Error detecting race: {e}", exc_info=True)
            return False, None

    def _determine_race_winner(self) -> Optional[str]:
        """
        Determine race winner using logical timestamps.

        Checks /In_Progress/ directories to see which agent's claim
        has the earlier timestamp (first-write-wins).

        Returns:
            Winner agent ID or None if cannot determine
        """
        try:
            # Check both /In_Progress/ directories
            cloud_claims = self._get_claims_with_timestamps("cloud")
            local_claims = self._get_claims_with_timestamps("local")

            # Find overlapping claims (same task ID)
            for cloud_task_id, cloud_timestamp in cloud_claims.items():
                if cloud_task_id in local_claims:
                    local_timestamp = local_claims[cloud_task_id]

                    # Compare timestamps - earlier wins
                    if cloud_timestamp < local_timestamp:
                        return "cloud"
                    else:
                        return "local"

            # No overlapping claims found
            return None

        except Exception as e:
            self.logger.error(f"Error determining race winner: {e}")
            return None

    def _get_claims_with_timestamps(self, agent_id: str) -> dict:
        """
        Get all claims for an agent with their timestamps.

        Args:
            agent_id: Agent identifier

        Returns:
            Dict mapping task_id to LamportTimestamp
        """
        claims = {}
        in_progress_dir = self.vault_path / "In_Progress" / agent_id

        if not in_progress_dir.exists():
            return claims

        for task_file in in_progress_dir.glob("*.md"):
            try:
                # Extract task ID from filename
                task_id = task_file.stem.split('_')[0]

                # Extract timestamp from file content
                timestamp = self._extract_claim_timestamp(task_file)
                if timestamp:
                    claims[task_id] = timestamp

            except Exception as e:
                self.logger.error(f"Error processing {task_file}: {e}")

        return claims

    def _extract_claim_timestamp(self, task_file: Path) -> Optional[LamportTimestamp]:
        """
        Extract claim timestamp from task file.

        Args:
            task_file: Path to task file

        Returns:
            LamportTimestamp or None
        """
        try:
            content = task_file.read_text(encoding='utf-8')

            # Extract claim metadata from frontmatter
            claimed_by = None
            claim_counter = None

            for line in content.split('\n'):
                if line.strip().startswith('claimed_by:'):
                    claimed_by = line.split(':', 1)[1].strip()
                elif line.strip().startswith('claim_counter:'):
                    claim_counter = int(line.split(':', 1)[1].strip())

            if claimed_by and claim_counter is not None:
                return LamportTimestamp(
                    agent_id=claimed_by,
                    counter=claim_counter,
                    wall_clock_time=task_file.stat().st_mtime
                )

            return None

        except Exception as e:
            self.logger.error(f"Error extracting timestamp: {e}")
            return None

    def resolve_race_as_loser(self, task_id: str) -> bool:
        """
        Resolve race condition as the losing agent.

        Removes our claim and lets the winner proceed.

        Args:
            task_id: Task identifier

        Returns:
            True if resolved successfully
        """
        try:
            self.logger.info(f"Resolving race as loser for task {task_id}")

            # Find our claim in /In_Progress/<agent>/
            in_progress_dir = self.vault_path / "In_Progress" / self.agent_id

            for task_file in in_progress_dir.glob(f"{task_id}*.md"):
                # Move back to /Needs_Action/ or delete
                # (winner will handle the task)
                task_file.unlink()
                self.logger.info(f"Removed losing claim: {task_file.name}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error resolving race as loser: {e}")
            return False

    def check_for_stale_races(self, max_age_minutes: int = 10) -> list[str]:
        """
        Check for unresolved race conditions (stale claims).

        Args:
            max_age_minutes: Maximum age before considering stale

        Returns:
            List of task IDs with potential stale races
        """
        stale_races = []

        try:
            # Get claims from both agents
            cloud_claims = self._get_claims_with_timestamps("cloud")
            local_claims = self._get_claims_with_timestamps("local")

            # Find overlapping claims
            for task_id in cloud_claims:
                if task_id in local_claims:
                    # Both agents have claims - potential unresolved race
                    stale_races.append(task_id)
                    self.logger.warning(f"Found potential stale race: {task_id}")

        except Exception as e:
            self.logger.error(f"Error checking for stale races: {e}")

        return stale_races
