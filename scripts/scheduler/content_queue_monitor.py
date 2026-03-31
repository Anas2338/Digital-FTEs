"""Content Queue Monitor for LinkedIn Auto-Posting.

Scans obsidian-vault/Content_Queue/ for scheduled LinkedIn posts and triggers
posting at the scheduled time via the approval workflow.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from watchers.shared.database import Database
from watchers.shared.vault_writer import VaultWriter


class ContentQueueMonitor:
    """Monitor for scheduled LinkedIn posts in Content Queue."""

    def __init__(self, vault_path: str = "obsidian-vault", poll_interval: int = 60):
        """Initialize content queue monitor.

        Args:
            vault_path: Path to Obsidian vault
            poll_interval: Polling interval in seconds (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.content_queue_dir = self.vault_path / "Content_Queue"
        self.poll_interval = poll_interval
        self.db = Database()
        self.vault_writer = VaultWriter(str(vault_path))

        # Ensure Content_Queue directory exists
        self.content_queue_dir.mkdir(parents=True, exist_ok=True)

    def scan_queue(self) -> List[Dict[str, Any]]:
        """Scan Content Queue for scheduled posts.

        Returns:
            List of post metadata dicts with file path, schedule, content
        """
        scheduled_posts = []

        for note_file in self.content_queue_dir.glob("*.md"):
            try:
                content = note_file.read_text(encoding="utf-8")

                # Parse frontmatter
                frontmatter = self._parse_frontmatter(content)

                if not frontmatter:
                    continue

                # Check if this is a LinkedIn post
                if frontmatter.get("type") != "linkedin-post":
                    continue

                # Check status
                status = frontmatter.get("status", "draft")
                if status not in ["scheduled", "pending"]:
                    continue

                # Extract schedule time
                scheduled_time = frontmatter.get("scheduled_time")
                if not scheduled_time:
                    continue

                # Extract post content (everything after frontmatter)
                post_content = self._extract_content(content)

                scheduled_posts.append({
                    "file_path": str(note_file),
                    "scheduled_time": scheduled_time,
                    "status": status,
                    "content": post_content,
                    "frontmatter": frontmatter
                })

            except Exception as e:
                print(f"Error processing {note_file}: {e}")
                continue

        return scheduled_posts

    def check_due_posts(self) -> List[Dict[str, Any]]:
        """Check for posts that are due to be published.

        Returns:
            List of posts that should be published now
        """
        scheduled_posts = self.scan_queue()
        due_posts = []
        now = datetime.utcnow()

        for post in scheduled_posts:
            try:
                scheduled_time = datetime.fromisoformat(
                    post["scheduled_time"].replace("Z", "")
                )

                # Check if post is due (within 2-minute window)
                time_diff = (now - scheduled_time).total_seconds()
                if 0 <= time_diff <= 120:  # Due now or up to 2 minutes late
                    due_posts.append(post)

            except Exception as e:
                print(f"Error parsing scheduled time: {e}")
                continue

        return due_posts

    def queue_post_for_approval(self, post: Dict[str, Any]) -> str:
        """Queue a post for approval via MCP server.

        Args:
            post: Post metadata dict

        Returns:
            Action ID for the queued post
        """
        from mcp_servers.digital_fte_server.approval.queue import ApprovalQueueManager
        from mcp_servers.digital_fte_server.approval.classifier import ActionClassifier

        # Generate action ID
        action_id = f"action-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

        # Prepare parameters
        parameters = {
            "content": post["content"],
            "source_file": post["file_path"]
        }

        # Classify and queue
        classifier = ActionClassifier()
        safety_level = classifier.classify("linkedin-post", parameters)

        queue_manager = ApprovalQueueManager()
        vault_path = queue_manager.queue_for_approval(
            action_id=action_id,
            action_type="linkedin-post",
            parameters=parameters,
            safety_level=safety_level
        )

        # Update source file status
        self._update_post_status(post["file_path"], "pending_approval", action_id)

        return action_id

    def _parse_frontmatter(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content with frontmatter

        Returns:
            Frontmatter dict or None if not found
        """
        # Match frontmatter between --- delimiters
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return None

        try:
            frontmatter = yaml.safe_load(match.group(1))
            return frontmatter
        except yaml.YAMLError:
            return None

    def _extract_content(self, content: str) -> str:
        """Extract post content (everything after frontmatter).

        Args:
            content: Full markdown content

        Returns:
            Post content without frontmatter
        """
        # Remove frontmatter
        content_without_fm = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content,
                                    count=1, flags=re.DOTALL)
        return content_without_fm.strip()

    def _update_post_status(self, file_path: str, status: str,
                           action_id: Optional[str] = None):
        """Update post status in frontmatter.

        Args:
            file_path: Path to post file
            status: New status
            action_id: Optional action ID to record
        """
        try:
            content = Path(file_path).read_text(encoding="utf-8")

            # Parse frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return

            frontmatter = yaml.safe_load(match.group(1))
            post_content = match.group(2)

            # Update status
            frontmatter["status"] = status
            if action_id:
                frontmatter["action_id"] = action_id
            frontmatter["last_updated"] = datetime.utcnow().isoformat() + "Z"

            # Write back
            new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{post_content}"
            Path(file_path).write_text(new_content, encoding="utf-8")

        except Exception as e:
            print(f"Error updating post status: {e}")

    def run(self):
        """Run the content queue monitor loop."""
        print(f"Content Queue Monitor started (polling every {self.poll_interval}s)")

        while True:
            try:
                # Check for due posts
                due_posts = self.check_due_posts()

                if due_posts:
                    print(f"Found {len(due_posts)} due post(s)")

                for post in due_posts:
                    try:
                        action_id = self.queue_post_for_approval(post)
                        print(f"Queued post for approval: {action_id}")
                    except Exception as e:
                        print(f"Error queuing post: {e}")

                # Sleep until next check
                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                print("\nContent Queue Monitor stopped")
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(self.poll_interval)


if __name__ == "__main__":
    monitor = ContentQueueMonitor()
    monitor.run()
