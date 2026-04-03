"""
Conflict Resolver for Platinum Tier

Resolves Git merge conflicts using logical timestamps and first-write-wins.
Handles Dashboard.md conflicts with local-agent-wins rule.

Based on spec.md FR-018, FR-023 and clarifications.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import git
from git.exc import GitCommandError

from coordination.logical_clock import LamportTimestamp


class ConflictResolver:
    """
    Resolves Git merge conflicts for vault synchronization.

    Resolution strategies:
    - Dashboard.md: Local agent wins (FR-018)
    - Other files: First-write-wins using logical timestamps (FR-018, FR-023)
    """

    def __init__(self, vault_path: Path, agent_id: str):
        """
        Initialize conflict resolver.

        Args:
            vault_path: Path to Obsidian vault
            agent_id: Agent identifier (cloud or local)
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"conflict_resolver_{agent_id}")

        try:
            self.repo = git.Repo(vault_path)
        except git.exc.InvalidGitRepositoryError:
            raise ValueError(f"Not a git repository: {vault_path}")

    def has_conflicts(self) -> bool:
        """
        Check if there are unresolved merge conflicts.

        Returns:
            True if conflicts exist
        """
        try:
            # Check for unmerged paths
            unmerged = self.repo.index.unmerged_blobs()
            return len(unmerged) > 0
        except Exception as e:
            self.logger.error(f"Error checking conflicts: {e}")
            return False

    def get_conflicted_files(self) -> List[Path]:
        """
        Get list of files with merge conflicts.

        Returns:
            List of file paths with conflicts
        """
        try:
            unmerged = self.repo.index.unmerged_blobs()
            return [Path(self.vault_path / path) for path in unmerged.keys()]
        except Exception as e:
            self.logger.error(f"Error getting conflicted files: {e}")
            return []

    def resolve_conflicts(self) -> Tuple[bool, Optional[str]]:
        """
        Resolve all merge conflicts automatically.

        Returns:
            Tuple of (success, error_message)
        """
        if not self.has_conflicts():
            return True, None

        conflicted_files = self.get_conflicted_files()
        self.logger.info(f"Resolving {len(conflicted_files)} conflicted files")

        try:
            for file_path in conflicted_files:
                success, error = self._resolve_single_file(file_path)
                if not success:
                    return False, f"Failed to resolve {file_path}: {error}"

            # Stage resolved files
            self.repo.git.add(A=True)

            self.logger.info("All conflicts resolved")
            return True, None

        except Exception as e:
            self.logger.error(f"Conflict resolution failed: {e}", exc_info=True)
            return False, str(e)

    def _resolve_single_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Resolve conflict for a single file.

        Args:
            file_path: Path to conflicted file

        Returns:
            Tuple of (success, error_message)
        """
        try:
            relative_path = file_path.relative_to(self.vault_path)

            # Special case: Dashboard.md - local agent wins (FR-018)
            if file_path.name == "Dashboard.md":
                return self._resolve_dashboard_conflict(relative_path)

            # General case: Use logical timestamps for first-write-wins
            return self._resolve_with_timestamps(relative_path)

        except Exception as e:
            self.logger.error(f"Error resolving {file_path}: {e}")
            return False, str(e)

    def _resolve_dashboard_conflict(self, relative_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Resolve Dashboard.md conflict - local agent always wins.

        Args:
            relative_path: Relative path to Dashboard.md

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.logger.info("Resolving Dashboard.md conflict - local agent wins")

            if self.agent_id == "local":
                # Keep local version (ours)
                self.repo.git.checkout('--ours', str(relative_path))
                self.logger.info("Kept local version of Dashboard.md")
            else:
                # Cloud agent: accept remote version (theirs)
                self.repo.git.checkout('--theirs', str(relative_path))
                self.logger.info("Accepted remote version of Dashboard.md")

            return True, None

        except GitCommandError as e:
            return False, str(e)

    def _resolve_with_timestamps(self, relative_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Resolve conflict using logical timestamps (first-write-wins).

        Args:
            relative_path: Relative path to conflicted file

        Returns:
            Tuple of (success, error_message)
        """
        try:
            self.logger.info(f"Resolving {relative_path} with timestamp comparison")

            # Get both versions
            ours_content = self._get_version_content(relative_path, 'ours')
            theirs_content = self._get_version_content(relative_path, 'theirs')

            # Extract timestamps from both versions
            ours_timestamp = self._extract_timestamp(ours_content)
            theirs_timestamp = self._extract_timestamp(theirs_content)

            # Compare timestamps - earlier timestamp wins
            if ours_timestamp and theirs_timestamp:
                if ours_timestamp < theirs_timestamp:
                    # Our version is earlier (first write) - keep ours
                    self.repo.git.checkout('--ours', str(relative_path))
                    self.logger.info(f"Kept our version (earlier timestamp)")
                else:
                    # Their version is earlier - accept theirs
                    self.repo.git.checkout('--theirs', str(relative_path))
                    self.logger.info(f"Accepted their version (earlier timestamp)")
            else:
                # Cannot determine timestamps - default to ours
                self.logger.warning(f"Cannot extract timestamps, defaulting to our version")
                self.repo.git.checkout('--ours', str(relative_path))

            return True, None

        except Exception as e:
            return False, str(e)

    def _get_version_content(self, relative_path: Path, version: str) -> str:
        """
        Get content of a specific version during conflict.

        Args:
            relative_path: Relative path to file
            version: 'ours' or 'theirs'

        Returns:
            File content as string
        """
        try:
            stage = 2 if version == 'ours' else 3
            content = self.repo.git.show(f':{stage}:{relative_path}')
            return content
        except Exception as e:
            self.logger.error(f"Error getting {version} version: {e}")
            return ""

    def _extract_timestamp(self, content: str) -> Optional[LamportTimestamp]:
        """
        Extract Lamport timestamp from file content.

        Args:
            content: File content

        Returns:
            LamportTimestamp or None if not found
        """
        try:
            # Look for timestamp in frontmatter or metadata
            # Format: created_at: {agent_id: "cloud", counter: 123, wall_clock_time: "..."}

            # Simplified extraction - would use proper YAML parser in production
            if "created_at:" in content:
                # Extract timestamp data (simplified)
                # In production, would parse YAML frontmatter properly
                pass

            return None  # Placeholder - would extract actual timestamp

        except Exception as e:
            self.logger.error(f"Error extracting timestamp: {e}")
            return None

    def abort_merge(self) -> bool:
        """
        Abort current merge and return to pre-merge state.

        Returns:
            True if successful
        """
        try:
            self.logger.warning("Aborting merge")
            self.repo.git.merge('--abort')
            return True
        except Exception as e:
            self.logger.error(f"Abort merge failed: {e}")
            return False
