"""
CEO Briefing Generator

Generates comprehensive weekly executive briefings by aggregating data from
financial transactions, social media posts, tasks, and critical issues.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from watchers.briefing_watcher.config import BriefingConfig
from watchers.briefing_watcher.financial_aggregator import FinancialAggregator
from watchers.briefing_watcher.social_aggregator import SocialAggregator
from watchers.briefing_watcher.task_aggregator import TaskAggregator
from watchers.briefing_watcher.issue_detector import IssueDetector
from watchers.briefing_watcher.chart_generator import ChartGenerator

logger = logging.getLogger(__name__)


class BriefingGenerator:
    """
    Generates weekly CEO briefings in Markdown format.
    """

    def __init__(self, config: Optional[BriefingConfig] = None):
        """
        Initialize briefing generator.

        Args:
            config: Briefing configuration (uses default if not provided)
        """
        self.config = config or BriefingConfig()
        self.financial_aggregator = FinancialAggregator()
        self.social_aggregator = SocialAggregator()
        self.task_aggregator = TaskAggregator()
        self.issue_detector = IssueDetector()
        self.chart_generator = ChartGenerator()

    def generate_briefing(
        self,
        week_number: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate weekly CEO briefing.

        Args:
            week_number: ISO week number (default: current week)
            year: Year (default: current year)

        Returns:
            Dictionary with briefing data and file path
        """
        # Determine week and year
        now = datetime.now()
        if week_number is None:
            week_number = now.isocalendar()[1]
        if year is None:
            year = now.year

        logger.info(f"Generating CEO briefing for week {week_number}, {year}")

        # Calculate date range for the week
        start_date, end_date = self._get_week_date_range(week_number, year)

        # Gather data from all aggregators
        briefing_data = {
            "week_number": week_number,
            "year": year,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "generated_at": now.isoformat(),
        }

        # Financial summary
        if self.config.include_financial_summary:
            try:
                financial_data = self.financial_aggregator.aggregate(
                    start_date=start_date,
                    end_date=end_date
                )
                briefing_data["financial"] = financial_data
            except Exception as e:
                logger.error(f"Failed to aggregate financial data: {e}")
                briefing_data["financial"] = {"error": str(e)}

        # Social media summary
        if self.config.include_social_media_summary:
            try:
                social_data = self.social_aggregator.aggregate(
                    start_date=start_date,
                    end_date=end_date,
                    platforms=self.config.social_media_platforms
                )
                briefing_data["social_media"] = social_data
            except Exception as e:
                logger.error(f"Failed to aggregate social media data: {e}")
                briefing_data["social_media"] = {"error": str(e)}

        # Task summary
        if self.config.include_task_summary:
            try:
                task_data = self.task_aggregator.aggregate(
                    start_date=start_date,
                    end_date=end_date
                )
                briefing_data["tasks"] = task_data
            except Exception as e:
                logger.error(f"Failed to aggregate task data: {e}")
                briefing_data["tasks"] = {"error": str(e)}

        # Critical issues
        if self.config.include_critical_issues:
            try:
                issues = self.issue_detector.detect_issues(
                    financial_data=briefing_data.get("financial", {}),
                    social_data=briefing_data.get("social_media", {}),
                    task_data=briefing_data.get("tasks", {})
                )
                briefing_data["critical_issues"] = issues
            except Exception as e:
                logger.error(f"Failed to detect critical issues: {e}")
                briefing_data["critical_issues"] = []

        # Generate Markdown content
        markdown_content = self._generate_markdown(briefing_data)

        # Write to file
        output_path = self._write_briefing_file(
            markdown_content,
            week_number,
            year
        )

        logger.info(f"CEO briefing generated successfully: {output_path}")

        return {
            "success": True,
            "file_path": str(output_path),
            "week_number": week_number,
            "year": year,
            "data": briefing_data
        }

    def _get_week_date_range(self, week_number: int, year: int) -> tuple:
        """
        Get start and end dates for a given ISO week.

        Args:
            week_number: ISO week number
            year: Year

        Returns:
            Tuple of (start_date, end_date)
        """
        # Get first day of the year
        jan_1 = datetime(year, 1, 1)

        # Find the first Monday of the year
        days_to_monday = (7 - jan_1.weekday()) % 7
        if days_to_monday == 0 and jan_1.weekday() != 0:
            days_to_monday = 7
        first_monday = jan_1 + timedelta(days=days_to_monday)

        # Calculate start of target week
        start_date = first_monday + timedelta(weeks=week_number - 1)
        end_date = start_date + timedelta(days=6)

        return start_date, end_date

    def _generate_markdown(self, data: Dict[str, Any]) -> str:
        """
        Generate Markdown content from briefing data.

        Args:
            data: Briefing data dictionary

        Returns:
            Markdown string
        """
        lines = []

        # Header
        lines.append(f"# CEO Briefing - Week {data['week_number']}, {data['year']}")
        lines.append("")
        lines.append(f"**Period**: {data['start_date'][:10]} to {data['end_date'][:10]}")
        lines.append(f"**Generated**: {data['generated_at'][:19]}")
        lines.append("")

        # Critical Issues (at top for visibility)
        if data.get("critical_issues"):
            lines.append("## ⚠️ Requires Attention")
            lines.append("")
            for issue in data["critical_issues"]:
                lines.append(f"- **{issue['severity'].upper()}**: {issue['title']}")
                lines.append(f"  - {issue['description']}")
            lines.append("")

        # Financial Summary
        if data.get("financial"):
            lines.append("## 💰 Financial Summary")
            lines.append("")
            financial = data["financial"]

            if "error" in financial:
                lines.append(f"*Error: {financial['error']}*")
            else:
                lines.append(f"- **Revenue**: ${financial.get('revenue', 0):,.2f}")
                lines.append(f"- **Expenses**: ${financial.get('expenses', 0):,.2f}")
                lines.append(f"- **Profit/Loss**: ${financial.get('profit_loss', 0):,.2f}")
                lines.append("")

                # Week-over-week comparison
                if financial.get("previous_week"):
                    prev = financial["previous_week"]
                    revenue_change = financial.get('revenue', 0) - prev.get('revenue', 0)
                    lines.append(f"**Week-over-Week**: Revenue {revenue_change:+,.2f}")
                    lines.append("")

                # ASCII chart
                if self.config.financial_chart_type == "ascii" and financial.get("daily_revenue"):
                    chart = self.chart_generator.generate_revenue_chart(
                        financial["daily_revenue"]
                    )
                    lines.append("```")
                    lines.append(chart)
                    lines.append("```")
                    lines.append("")

        # Social Media Summary
        if data.get("social_media"):
            lines.append("## 📱 Social Media Performance")
            lines.append("")
            social = data["social_media"]

            if "error" in social:
                lines.append(f"*Error: {social['error']}*")
            else:
                lines.append(f"- **Posts Published**: {social.get('total_posts', 0)}")
                lines.append(f"- **Total Engagement**: {social.get('total_engagement', 0):,}")
                lines.append(f"- **Average Engagement**: {social.get('avg_engagement', 0):.1f} per post")
                lines.append("")

                # Platform breakdown
                if social.get("by_platform"):
                    lines.append("**By Platform**:")
                    for platform, metrics in social["by_platform"].items():
                        lines.append(f"- {platform.title()}: {metrics.get('posts', 0)} posts, {metrics.get('engagement', 0):,} engagement")
                    lines.append("")

        # Task Summary
        if data.get("tasks"):
            lines.append("## ✅ Tasks & Action Items")
            lines.append("")
            tasks = data["tasks"]

            if "error" in tasks:
                lines.append(f"*Error: {tasks['error']}*")
            else:
                lines.append(f"- **Completed**: {tasks.get('completed_count', 0)}")
                lines.append(f"- **In Progress**: {tasks.get('in_progress_count', 0)}")
                lines.append(f"- **Pending**: {tasks.get('pending_count', 0)}")
                lines.append("")

                # Top completed tasks
                if tasks.get("top_completed"):
                    lines.append("**Key Accomplishments**:")
                    for task in tasks["top_completed"][:5]:
                        lines.append(f"- {task['title']}")
                    lines.append("")

                # Pending action items
                if tasks.get("pending_high_priority"):
                    lines.append("**Pending Action Items**:")
                    for task in tasks["pending_high_priority"][:5]:
                        lines.append(f"- {task['title']}")
                    lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated automatically by Digital FTE Agent*")

        return "\n".join(lines)

    def _write_briefing_file(
        self,
        content: str,
        week_number: int,
        year: int
    ) -> Path:
        """
        Write briefing content to file.

        Args:
            content: Markdown content
            week_number: ISO week number
            year: Year

        Returns:
            Path to written file
        """
        # Create output directory if it doesn't exist
        output_dir = Path(self.config.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = self.config.get_briefing_filename(week_number, year)
        file_path = output_dir / filename

        # Write content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path
