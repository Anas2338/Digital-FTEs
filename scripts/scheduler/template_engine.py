"""Template engine for LinkedIn post variable substitution.

Supports template variables like {{company_name}}, {{date}}, {{milestone}}
that are automatically replaced with values from vault metadata or context.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import yaml


class TemplateEngine:
    """Engine for processing LinkedIn post templates with variable substitution."""

    def __init__(self, vault_path: str = "obsidian-vault"):
        """Initialize template engine.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.metadata = self._load_vault_metadata()

    def _load_vault_metadata(self) -> Dict[str, Any]:
        """Load metadata from vault configuration.

        Returns:
            Metadata dict with company info, defaults, etc.
        """
        metadata_file = self.vault_path / ".metadata.yaml"

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass

        # Default metadata if file doesn't exist
        return {
            "company_name": "Your Company",
            "author_name": "Your Name",
            "author_title": "Your Title"
        }

    def substitute(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Substitute template variables in content.

        Args:
            content: Content with template variables
            context: Optional context dict with additional variables

        Returns:
            Content with variables replaced
        """
        # Merge metadata with context
        variables = {**self.metadata}
        if context:
            variables.update(context)

        # Add dynamic variables
        variables["date"] = self._format_date()
        variables["year"] = str(datetime.now().year)
        variables["month"] = datetime.now().strftime("%B")

        # Find all template variables in content
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, content)

        # Replace each variable
        result = content
        for var_name in matches:
            if var_name in variables:
                value = str(variables[var_name])
                result = result.replace(f"{{{{{var_name}}}}}", value)
            else:
                # Leave unmatched variables as-is (user can fill manually)
                pass

        return result

    def _format_date(self) -> str:
        """Format current date for posts.

        Returns:
            Formatted date string (e.g., "March 30, 2026")
        """
        return datetime.now().strftime("%B %d, %Y")

    def validate_template(self, content: str) -> Dict[str, Any]:
        """Validate template and identify missing variables.

        Args:
            content: Template content

        Returns:
            Validation result dict with missing variables
        """
        pattern = r'\{\{(\w+)\}\}'
        variables = re.findall(pattern, content)

        # Check which variables are available
        available = set(self.metadata.keys()) | {"date", "year", "month"}
        missing = [v for v in variables if v not in available]

        return {
            "valid": len(missing) == 0,
            "total_variables": len(variables),
            "missing_variables": missing,
            "available_variables": list(available)
        }

    def get_available_variables(self) -> Dict[str, str]:
        """Get all available template variables with descriptions.

        Returns:
            Dict mapping variable names to descriptions
        """
        return {
            "company_name": "Company name from vault metadata",
            "author_name": "Post author name",
            "author_title": "Post author title/role",
            "date": "Current date (formatted: March 30, 2026)",
            "year": "Current year",
            "month": "Current month name",
            "milestone": "Milestone value (provide in context)",
            "product_name": "Product name (provide in context)",
            "metric_value": "Metric value (provide in context)",
            "metric_name": "Metric name (provide in context)"
        }

    def enforce_character_limit(self, content: str, limit: int = 3000,
                               truncate: bool = True) -> Dict[str, Any]:
        """Enforce LinkedIn character limit on content.

        Args:
            content: Post content
            limit: Character limit (default: 3000 for LinkedIn)
            truncate: Whether to truncate if over limit

        Returns:
            Result dict with content, length, truncated flag
        """
        char_count = len(content)

        result = {
            "content": content,
            "char_count": char_count,
            "limit": limit,
            "within_limit": char_count <= limit,
            "truncated": False,
            "warning": None
        }

        # Warning if approaching limit
        if 2500 <= char_count < limit:
            result["warning"] = f"Approaching character limit ({char_count}/{limit})"

        # Truncate if over limit
        if char_count > limit:
            if truncate:
                # Truncate at word boundary
                truncated = content[:limit-15]  # Leave room for suffix
                last_space = truncated.rfind(' ')
                if last_space > 0:
                    truncated = truncated[:last_space]

                truncated += "... [Read more]"

                result["content"] = truncated
                result["char_count"] = len(truncated)
                result["truncated"] = True
                result["warning"] = f"Content truncated from {char_count} to {len(truncated)} characters"
            else:
                result["warning"] = f"Content exceeds limit ({char_count}/{limit})"

        return result

    def optimize_for_engagement(self, content: str) -> Dict[str, Any]:
        """Analyze content and suggest optimizations for LinkedIn engagement.

        Args:
            content: Post content

        Returns:
            Analysis dict with suggestions
        """
        lines = content.split('\n')
        char_count = len(content)

        # Check hook (first 2 lines)
        hook_lines = lines[:2] if len(lines) >= 2 else lines
        hook_text = '\n'.join(hook_lines)
        hook_length = len(hook_text)

        # Check for CTA
        cta_keywords = ['comment', 'share', 'click', 'learn more', 'visit',
                       'check out', 'let me know', 'thoughts?', 'link in']
        has_cta = any(keyword in content.lower() for keyword in cta_keywords)

        # Check hashtags
        hashtags = re.findall(r'#\w+', content)
        hashtag_count = len(hashtags)

        # Check emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+",
            flags=re.UNICODE
        )
        emoji_count = len(emoji_pattern.findall(content))

        # Generate suggestions
        suggestions = []

        if hook_length > 150:
            suggestions.append("Hook is too long - aim for 100-150 chars in first 2 lines")

        if not has_cta:
            suggestions.append("Add a call-to-action (ask for comments, shares, or clicks)")

        if hashtag_count == 0:
            suggestions.append("Add 3-5 relevant hashtags for discoverability")
        elif hashtag_count > 5:
            suggestions.append(f"Too many hashtags ({hashtag_count}) - reduce to 3-5 for best results")

        if emoji_count == 0:
            suggestions.append("Consider adding 1-3 emojis for personality")
        elif emoji_count > 5:
            suggestions.append(f"Too many emojis ({emoji_count}) - use sparingly (1-3)")

        if char_count < 500:
            suggestions.append("Post is short - consider expanding for more engagement (target: 1300-2000 chars)")
        elif char_count > 2500:
            suggestions.append("Post is long - consider splitting into multiple posts or carousel")

        # Check line breaks (paragraphs should be 2-3 lines max)
        long_paragraphs = [p for p in content.split('\n\n') if p.count('\n') > 3]
        if long_paragraphs:
            suggestions.append("Break up long paragraphs - use line breaks for readability")

        return {
            "char_count": char_count,
            "optimal_range": (1300, 2000),
            "hook_length": hook_length,
            "has_cta": has_cta,
            "hashtag_count": hashtag_count,
            "emoji_count": emoji_count,
            "suggestions": suggestions,
            "engagement_score": self._calculate_engagement_score(
                char_count, has_cta, hashtag_count, emoji_count, hook_length
            )
        }

    def _calculate_engagement_score(self, char_count: int, has_cta: bool,
                                    hashtag_count: int, emoji_count: int,
                                    hook_length: int) -> int:
        """Calculate engagement score (0-100).

        Args:
            char_count: Character count
            has_cta: Has call-to-action
            hashtag_count: Number of hashtags
            emoji_count: Number of emojis
            hook_length: Hook length in characters

        Returns:
            Score from 0-100
        """
        score = 0

        # Character count (30 points)
        if 1300 <= char_count <= 2000:
            score += 30
        elif 500 <= char_count < 1300 or 2000 < char_count <= 2500:
            score += 20
        elif char_count < 500 or char_count > 2500:
            score += 10

        # Hook (20 points)
        if 80 <= hook_length <= 150:
            score += 20
        elif hook_length < 80 or hook_length > 150:
            score += 10

        # CTA (20 points)
        if has_cta:
            score += 20

        # Hashtags (15 points)
        if 3 <= hashtag_count <= 5:
            score += 15
        elif 1 <= hashtag_count < 3 or 5 < hashtag_count <= 7:
            score += 10
        elif hashtag_count > 7:
            score += 5

        # Emojis (15 points)
        if 1 <= emoji_count <= 3:
            score += 15
        elif emoji_count == 0 or emoji_count > 3:
            score += 5

        return score


if __name__ == "__main__":
    # Example usage
    engine = TemplateEngine()

    template = """🚀 Excited to announce that {{company_name}} has reached {{milestone}}!

This milestone represents months of hard work by our amazing team.

Thank you to everyone who's been part of this journey.

What's your biggest milestone this {{month}}? Let me know in the comments!

#Milestone #Growth #{{company_name}}"""

    # Substitute variables
    result = engine.substitute(template, context={"milestone": "10,000 users"})
    print("Substituted content:")
    print(result)
    print()

    # Enforce character limit
    limit_result = engine.enforce_character_limit(result)
    print(f"Character count: {limit_result['char_count']}/{limit_result['limit']}")
    print(f"Within limit: {limit_result['within_limit']}")
    print()

    # Optimize for engagement
    optimization = engine.optimize_for_engagement(result)
    print(f"Engagement score: {optimization['engagement_score']}/100")
    print("Suggestions:")
    for suggestion in optimization['suggestions']:
        print(f"  - {suggestion}")
