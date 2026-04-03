"""
Git Sync Manager for Platinum Tier

Implements Git-based vault synchronization with atomic operations.
Handles pull, commit, push cycle with conflict detection.

Based on research.md Decision 1: Git chosen for atomic operations,
10-20MB RAM usage, and explicit conflict detection.
"""

import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import git
from git.exc import GitCommandError


class GitSyncManager:
    """
    Manages Git-based vault synchronization.

    Implements atomic sync pattern:
    1. Pull with rebase and autostash
    2. Commit local changes
    3. Push (failure indicates conflict/race)
    4. Retry on push failure
    """

    def __init__(self, vault_path: Path, agent_id: str):
        """
        Initialize Git sync manager.

        Args:
            vault_path: Path to Obsidian vault (must be git repo)
            agent_id: Agent identifier (cloud or local)
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"git_sync_{agent_id}")

        try:
            self.repo = git.Repo(vault_path)
        except git.exc.InvalidGitRepositoryError:
            raise ValueError(f"Not a git repository: {vault_path}")

    def sync(self) -> Tuple[bool, Optional[str]]:
        """
        Perform full sync cycle: pull, commit, push.

        Returns:
            Tuple of (success, error_message)
            - (True, None) if sync successful
            - (False, error_message) if sync failed
        """
        try:
            # Step 1: Pull with rebase
            pull_success, pull_error = self._pull()
            if not pull_success:
                return False, f"Pull failed: {pull_error}"

            # Step 2: Commit local changes
            commit_success, commit_error = self._commit()
            if not commit_success:
                # No changes to commit is not an error
                if "nothing to commit" in (commit_error or ""):
                    self.logger.debug("No changes to commit")
                else:
                    return False, f"Commit failed: {commit_error}"

            # Step 3: Push
            push_success, push_error = self._push()
            if not push_success:
                return False, f"Push failed: {push_error}"

            self.logger.info("Sync completed successfully")
            return True, None

        except Exception as e:
            self.logger.error(f"Sync error: {e}", exc_info=True)
            return False, str(e)

    def _pull(self) -> Tuple[bool, Optional[str]]:
        """
        Pull changes from remote with rebase and autostash.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.logger.debug("Pulling changes from remote...")

            # git pull --rebase --autostash
            origin = self.repo.remote('origin')
            origin.pull(rebase=True, autostash=True)

            self.logger.debug("Pull successful")
            return True, None

        except GitCommandError as e:
            self.logger.error(f"Pull failed: {e}")
            return False, str(e)

    def _commit(self) -> Tuple[bool, Optional[str]]:
        """
        Commit all local changes.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Check if there are changes to commit
            if not self.repo.is_dirty(untracked_files=True):
                return True, "nothing to commit"

            self.logger.debug("Committing local changes...")

            # Stage all changes
            self.repo.git.add(A=True)

            # Commit with agent-specific message
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            commit_message = f"{self.agent_id} agent sync - {timestamp}"

            self.repo.index.commit(commit_message)

            self.logger.debug(f"Committed changes: {commit_message}")
            return True, None

        except GitCommandError as e:
            self.logger.error(f"Commit failed: {e}")
            return False, str(e)

    def _push(self) -> Tuple[bool, Optional[str]]:
        """
        Push commits to remote.

        Push failure indicates another agent pushed first (race condition).

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.logger.debug("Pushing to remote...")

            origin = self.repo.remote('origin')
            push_info = origin.push()

            # Check push result
            if push_info and push_info[0].flags & git.PushInfo.ERROR:
                error_msg = "Push rejected (another agent pushed first)"
                self.logger.warning(error_msg)
                return False, error_msg

            self.logger.debug("Push successful")
            return True, None

        except GitCommandError as e:
            # Push failure is expected during race conditions
            if "rejected" in str(e).lower() or "non-fast-forward" in str(e).lower():
                self.logger.warning("Push rejected - race condition detected")
                return False, "Race condition: another agent pushed first"

            self.logger.error(f"Push failed: {e}")
            return False, str(e)

    def get_last_sync_time(self) -> Optional[datetime]:
        """
        Get timestamp of last successful sync (last commit).

        Returns:
            Datetime of last commit or None if no commits
        """
        try:
            if self.repo.head.is_valid():
                last_commit = self.repo.head.commit
                return datetime.fromtimestamp(last_commit.committed_date)
            return None
        except Exception as e:
            self.logger.error(f"Error getting last sync time: {e}")
            return None

    def get_sync_lag_seconds(self) -> Optional[int]:
        """
        Calculate sync lag (time since last commit).

        Returns:
            Seconds since last commit or None if unavailable
        """
        last_sync = self.get_last_sync_time()
        if last_sync:
            lag = (datetime.now() - last_sync).total_seconds()
            return int(lag)
        return None

    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes.

        Returns:
            True if there are uncommitted changes
        """
        return self.repo.is_dirty(untracked_files=True)

    def get_current_branch(self) -> str:
        """
        Get current branch name.

        Returns:
            Branch name
        """
        return self.repo.active_branch.name

    def reset_to_remote(self) -> bool:
        """
        Reset local branch to match remote (discard local changes).

        WARNING: This discards all local uncommitted changes.
        Use only for recovery from unresolvable conflicts.

        Returns:
            True if successful
        """
        try:
            self.logger.warning("Resetting to remote - discarding local changes")

            origin = self.repo.remote('origin')
            origin.fetch()

            # Reset to origin/main (or origin/master)
            branch = self.get_current_branch()
            self.repo.git.reset('--hard', f'origin/{branch}')

            self.logger.info("Reset to remote successful")
            return True

        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            return False
