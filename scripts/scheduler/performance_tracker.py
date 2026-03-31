"""Performance tracker for LinkedIn posts.

Fetches engagement metrics (views, likes, comments, shares) from LinkedIn API
and updates post frontmatter in the vault.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import yaml
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class LinkedInPerformanceTracker:
    """Tracker for LinkedIn post performance metrics."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize performance tracker.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.content_queue_dir = self.vault_path / "Content_Queue"
        self.done_dir = self.vault_path / "Done"

    def fetch_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """Fetch metrics for a LinkedIn post.

        Args:
            post_id: LinkedIn post ID

        Returns:
            Metrics dict with views, likes, comments, shares
        """
        # TODO: Implement LinkedIn API integration
        # For now, return placeholder metrics
        # Real implementation would use LinkedIn API:
        # https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/share-api

        return {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "ctr": 0.0,
            "engagement_rate": 0.0,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

    def update_post_performance(self, file_path: str, post_id: str) -> bool:
        """Update post performance metrics in frontmatter.

        Args:
            file_path: Path to post file
            post_id: LinkedIn post ID

        Returns:
            True if updated successfully
        """
        try:
            # Fetch latest metrics
            metrics = self.fetch_post_metrics(post_id)

            # Read post file
            post_file = Path(file_path)
            if not post_file.exists():
                return False

            content = post_file.read_text(encoding="utf-8")

            # Parse frontmatter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
            if not match:
                return False

            frontmatter = yaml.safe_load(match.group(1))
            post_content = match.group(2)

            # Update performance section
            frontmatter["performance"] = metrics

            # Calculate engagement rate
            if metrics["views"] > 0:
                total_engagement = (metrics["likes"] + metrics["comments"] +
                                  metrics["shares"])
                engagement_rate = (total_engagement / metrics["views"]) * 100
                frontmatter["performance"]["engagement_rate"] = round(engagement_rate, 2)

            # Write back
            new_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n{post_content}"
            post_file.write_text(new_content, encoding="utf-8")

            return True

        except Exception as e:
            print(f"Error updating post performance: {e}")
            return False

    def track_all_published_posts(self):
        """Track performance for all published posts."""
        # Check Done directory for published posts
        if not self.done_dir.exists():
            return

        for note_file in self.done_dir.glob("*.md"):
            try:
                content = note_file.read_text(encoding="utf-8")

                # Parse frontmatter
                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if not match:
                    continue

                frontmatter = yaml.safe_load(match.group(1))

                # Check if this is a LinkedIn post
                if frontmatter.get("type") != "linkedin-post":
                    continue

                # Check if post has been published
                if frontmatter.get("status") != "published":
                    continue

                # Get LinkedIn post ID
                post_id = frontmatter.get("linkedin_post_id")
                if not post_id:
                    continue

                # Update performance
                self.update_post_performance(str(note_file), post_id)
                print(f"Updated performance for {note_file.name}")

            except Exception as e:
                print(f"Error tracking {note_file}: {e}")
                continue

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all published posts.

        Returns:
            Summary dict with aggregate metrics
        """
        total_posts = 0
        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0

        if not self.done_dir.exists():
            return {
                "total_posts": 0,
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "total_shares": 0,
                "avg_engagement_rate": 0.0
            }

        for note_file in self.done_dir.glob("*.md"):
            try:
                content = note_file.read_text(encoding="utf-8")
                match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                if not match:
                    continue

                frontmatter = yaml.safe_load(match.group(1))

                if frontmatter.get("type") != "linkedin-post":
                    continue

                if frontmatter.get("status") != "published":
                    continue

                performance = frontmatter.get("performance", {})
                total_posts += 1
                total_views += performance.get("views", 0)
                total_likes += performance.get("likes", 0)
                total_comments += performance.get("comments", 0)
                total_shares += performance.get("shares", 0)

            except Exception:
                continue

        # Calculate averages
        avg_engagement_rate = 0.0
        if total_views > 0:
            total_engagement = total_likes + total_comments + total_shares
            avg_engagement_rate = (total_engagement / total_views) * 100

        return {
            "total_posts": total_posts,
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "avg_engagement_rate": round(avg_engagement_rate, 2),
            "avg_views_per_post": round(total_views / total_posts, 2) if total_posts > 0 else 0,
            "avg_likes_per_post": round(total_likes / total_posts, 2) if total_posts > 0 else 0
        }


if __name__ == "__main__":
    # Example usage
    tracker = LinkedInPerformanceTracker()

    # Track all published posts
    print("Tracking performance for all published posts...")
    tracker.track_all_published_posts()

    # Get summary
    summary = tracker.get_performance_summary()
    print("\nPerformance Summary:")
    print(f"Total Posts: {summary['total_posts']}")
    print(f"Total Views: {summary['total_views']}")
    print(f"Total Likes: {summary['total_likes']}")
    print(f"Total Comments: {summary['total_comments']}")
    print(f"Total Shares: {summary['total_shares']}")
    print(f"Avg Engagement Rate: {summary['avg_engagement_rate']}%")
