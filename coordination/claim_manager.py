"""
Claim Manager for Platinum Tier

Implements claim-by-move pattern for dual-agent coordination.
First agent to move file from /Needs_Action/ to /In_Progress/ owns the task.

Based on spec.md FR-020, FR-021, FR-024 and User Story 3.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from coordination.logical_clock import LamportClock, LamportTimestamp
from coordination.work_queue import WorkQueueDomain, WorkQueuePathHelper
from sync.atomic_writer import AtomicWriter


class ClaimManager:
    """
    Manages task claiming using claim-by-move pattern.

    Claim-by-move rule (FR-020):
    - First agent to move file from /Needs_Action/ to /In_Progress/<agent>/ owns it
    - Other agents must respect claimed tasks (FR-024)
    - Race conditions detected via Git push failures (FR-023)
    """

    def __init__(self, vault_path: Path, agent_id: str):
        """
        Initialize claim manager.

        Args:
            vault_path: Path to Obsidian vault
            agent_id: Agent identifier (cloud or local)
        """
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.clock = LamportClock(agent_id=agent_id)
        self.path_helper = WorkQueuePathHelper(vault_path)
        self.logger = logging.getLogger(f"claim_manager_{agent_id}")

    def claim_task(self, task_file: Path, domain: WorkQueueDomain) -> Tuple[bool, Optional[str]]:
        """
        Attempt to claim a task by moving it to /In_Progress/<agent>/.

        Args:
            task_file: Path to task file in /Needs_Action/
            domain: Work domain

        Returns:
            Tuple of (success, error_message)
            - (True, None) if claim successful
            - (False, error_message) if claim failed
        """
        try:
            # Check if task is in /Needs_Action/
            if "/Needs_Action/" not in str(task_file):
                return False, "Task is not in /Needs_Action/ directory"

            # Check if task still exists (another agent may have claimed it)
            if not task_file.exists():
                return False, "Task no longer exists (already claimed)"

            # Generate claim timestamp
            claim_timestamp = self.clock.tick()

            # Destination: /In_Progress/<agent>/
            in_progress_dir = self.path_helper.in_progress_dir(self.agent_id)
            in_progress_dir.mkdir(parents=True, exist_ok=True)

            dest_file = in_progress_dir / task_file.name

            # Add claim metadata to file
            self._add_claim_metadata(task_file, claim_timestamp)

            # Atomic move operation
            shutil.move(str(task_file), str(dest_file))

            self.logger.info(f"Claimed task {task_file.name} at {claim_timestamp.wall_clock_time}")
            return True, None

        except FileNotFoundError:
            # Race condition: another agent claimed it first
            self.logger.warning(f"Race condition: task {task_file.name} already claimed")
            return False, "Race condition: task already claimed by another agent"

        except Exception as e:
            self.logger.error(f"Error claiming task {task_file.name}: {e}", exc_info=True)
            return False, str(e)

    def _add_claim_metadata(self, task_file: Path, timestamp: LamportTimestamp) -> None:
        """
        Add claim metadata to task file.

        Args:
            task_file: Path to task file
            timestamp: Claim timestamp
        """
        try:
            content = task_file.read_text(encoding='utf-8')

            # Add claim metadata to frontmatter
            claim_metadata = f"""
claimed_by: {self.agent_id}
claimed_at: {timestamp.wall_clock_time.isoformat()}
claim_counter: {timestamp.counter}
"""

            # Insert after frontmatter header
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = f"---{parts[1]}{claim_metadata}---{parts[2]}"

            AtomicWriter.write(task_file, content)

        except Exception as e:
            self.logger.error(f"Error adding claim metadata: {e}")

    def release_task(self, task_file: Path, completed: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Release a claimed task (move to /Done/ or back to /Needs_Action/).

        Args:
            task_file: Path to task file in /In_Progress/<agent>/
            completed: If True, move to /Done/; if False, return to /Needs_Action/

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Verify task is in our /In_Progress/ directory
            if f"/In_Progress/{self.agent_id}/" not in str(task_file):
                return False, f"Task is not in /In_Progress/{self.agent_id}/"

            if not task_file.exists():
                return False, "Task file not found"

            if completed:
                # Move to /Done/
                done_dir = self.path_helper.done_dir()
                done_dir.mkdir(parents=True, exist_ok=True)

                # Add completion timestamp
                completion_timestamp = self.clock.tick()
                self._add_completion_metadata(task_file, completion_timestamp)

                dest_file = done_dir / task_file.name
                shutil.move(str(task_file), str(dest_file))

                self.logger.info(f"Completed task {task_file.name}")
            else:
                # Return to /Needs_Action/ (task failed or cancelled)
                # Extract domain from filename or metadata
                domain = self._extract_domain(task_file)
                if not domain:
                    return False, "Cannot determine task domain"

                needs_action_dir = self.path_helper.needs_action_dir(domain)
                dest_file = needs_action_dir / task_file.name

                # Remove claim metadata
                self._remove_claim_metadata(task_file)

                shutil.move(str(task_file), str(dest_file))

                self.logger.info(f"Released task {task_file.name} back to /Needs_Action/")

            return True, None

        except Exception as e:
            self.logger.error(f"Error releasing task {task_file.name}: {e}", exc_info=True)
            return False, str(e)

    def _add_completion_metadata(self, task_file: Path, timestamp: LamportTimestamp) -> None:
        """
        Add completion metadata to task file.

        Args:
            task_file: Path to task file
            timestamp: Completion timestamp
        """
        try:
            content = task_file.read_text(encoding='utf-8')

            completion_metadata = f"""
completed_by: {self.agent_id}
completed_at: {timestamp.wall_clock_time.isoformat()}
completion_counter: {timestamp.counter}
"""

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = f"---{parts[1]}{completion_metadata}---{parts[2]}"

            AtomicWriter.write(task_file, content)

        except Exception as e:
            self.logger.error(f"Error adding completion metadata: {e}")

    def _remove_claim_metadata(self, task_file: Path) -> None:
        """
        Remove claim metadata from task file.

        Args:
            task_file: Path to task file
        """
        try:
            content = task_file.read_text(encoding='utf-8')

            # Remove claim-related lines from frontmatter
            lines = content.split('\n')
            filtered_lines = [
                line for line in lines
                if not any(key in line for key in ['claimed_by:', 'claimed_at:', 'claim_counter:'])
            ]

            AtomicWriter.write(task_file, '\n'.join(filtered_lines))

        except Exception as e:
            self.logger.error(f"Error removing claim metadata: {e}")

    def _extract_domain(self, task_file: Path) -> Optional[WorkQueueDomain]:
        """
        Extract domain from task file.

        Args:
            task_file: Path to task file

        Returns:
            WorkQueueDomain or None
        """
        try:
            # Try to extract from filename pattern: {id}_{domain}_{type}.md
            parts = task_file.stem.split('_')
            if len(parts) >= 2:
                domain_str = parts[1]
                try:
                    return WorkQueueDomain(domain_str)
                except ValueError:
                    pass

            # Try to extract from file content
            content = task_file.read_text(encoding='utf-8')
            if "domain:" in content:
                for line in content.split('\n'):
                    if line.strip().startswith('domain:'):
                        domain_str = line.split(':', 1)[1].strip()
                        try:
                            return WorkQueueDomain(domain_str)
                        except ValueError:
                            pass

            return None

        except Exception as e:
            self.logger.error(f"Error extracting domain: {e}")
            return None

    def is_task_claimed(self, task_file: Path) -> bool:
        """
        Check if a task is already claimed by any agent.

        Args:
            task_file: Path to task file

        Returns:
            True if task is claimed (in any /In_Progress/ directory)
        """
        # Check if file is in any /In_Progress/ directory
        return "/In_Progress/" in str(task_file)

    def get_claimed_tasks(self) -> list[Path]:
        """
        Get list of tasks claimed by this agent.

        Returns:
            List of task file paths in /In_Progress/<agent>/
        """
        in_progress_dir = self.path_helper.in_progress_dir(self.agent_id)
        if not in_progress_dir.exists():
            return []

        return list(in_progress_dir.glob("*.md"))

    def check_for_abandoned_claims(self, max_age_hours: int = 24) -> list[Path]:
        """
        Find tasks claimed by this agent that are older than max_age.

        Args:
            max_age_hours: Maximum age in hours before considering abandoned

        Returns:
            List of potentially abandoned task files
        """
        abandoned = []
        claimed_tasks = self.get_claimed_tasks()

        for task_file in claimed_tasks:
            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(task_file.stat().st_mtime)
                age_hours = (datetime.now() - mtime).total_seconds() / 3600

                if age_hours > max_age_hours:
                    abandoned.append(task_file)
                    self.logger.warning(f"Found abandoned task: {task_file.name} (age: {age_hours:.1f}h)")

            except Exception as e:
                self.logger.error(f"Error checking task age: {e}")

        return abandoned
