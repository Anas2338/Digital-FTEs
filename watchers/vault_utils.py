"""Vault-specific utility functions for Obsidian integration."""

import yaml
from typing import Dict, Any, Optional
from datetime import datetime


def generate_frontmatter(
    title: str,
    created: str,
    source: str,
    sender: Optional[str] = None,
    email_date: Optional[str] = None,
    status: str = "inbox",
    tags: Optional[list] = None
) -> str:
    """
    Generate YAML frontmatter for an Obsidian note.

    Args:
        title: Note title
        created: Creation timestamp (ISO 8601 format)
        source: Source of the note (e.g., "gmail", "manual")
        sender: Email sender (optional)
        email_date: Original email date (optional)
        status: Note status (default: "inbox")
        tags: List of tags (optional)

    Returns:
        YAML frontmatter string with --- delimiters

    Examples:
        >>> generate_frontmatter("Test Note", "2026-03-29T14:30:00Z", "gmail")
        '---\\ntitle: Test Note\\ncreated: 2026-03-29T14:30:00Z\\nsource: gmail\\nstatus: inbox\\n---\\n'
    """
    frontmatter_dict = {
        'title': title,
        'created': created,
        'source': source,
        'status': status
    }

    if sender:
        frontmatter_dict['sender'] = sender

    if email_date:
        frontmatter_dict['email_date'] = email_date

    if tags:
        frontmatter_dict['tags'] = tags

    # Generate YAML with proper formatting
    yaml_content = yaml.dump(
        frontmatter_dict,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False
    )

    return f"---\n{yaml_content}---\n"


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown content with frontmatter

    Returns:
        Tuple of (frontmatter_dict, body_content)
        If no frontmatter found, returns (empty dict, original content)

    Examples:
        >>> parse_frontmatter("---\\ntitle: Test\\n---\\nBody text")
        ({'title': 'Test'}, 'Body text')
    """
    # Check if content starts with frontmatter delimiter
    if not content.startswith('---'):
        return {}, content

    # Find the closing delimiter
    try:
        # Split on first occurrence of closing ---
        parts = content.split('---', 2)

        if len(parts) < 3:
            return {}, content

        # parts[0] is empty, parts[1] is frontmatter, parts[2] is body
        frontmatter_text = parts[1].strip()
        body = parts[2].strip()

        # Parse YAML
        frontmatter_dict = yaml.safe_load(frontmatter_text)

        if frontmatter_dict is None:
            frontmatter_dict = {}

        return frontmatter_dict, body

    except yaml.YAMLError:
        # If YAML parsing fails, return empty dict and original content
        return {}, content
